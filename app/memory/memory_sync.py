"""
Memory Sync Module for M3 Agent System v2.7
记忆同步模块：将M3的所有数据同步到D5管理航母
"""

import sqlite3
import json
import logging
import threading
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ==================== Configuration ====================

# D5 API地址（从环境变量读取）
import os
D5_API_URL = os.getenv("D5_API_URL", "")

# 同步配置
SYNC_INTERVAL = int(os.getenv("MEMORY_SYNC_INTERVAL", "10"))  # 同步间隔（秒）
SYNC_BATCH_SIZE = int(os.getenv("MEMORY_SYNC_BATCH_SIZE", "100"))  # 每批同步数量
MAX_RETRY_COUNT = int(os.getenv("MEMORY_MAX_RETRY", "3"))  # 最大重试次数

# 数据库路径
DB_PATH = "/data/memory_buffer.db"


# ==================== Database Setup ====================

def init_database():
    """初始化记忆缓冲数据库"""
    # 确保目录存在
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建记忆缓冲表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_buffer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            synced BOOLEAN DEFAULT 0,
            retry_count INTEGER DEFAULT 0,
            last_retry DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_synced 
        ON memory_buffer(synced)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_type 
        ON memory_buffer(type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON memory_buffer(timestamp)
    """)
    
    conn.commit()
    conn.close()
    
    logger.info(f"Memory buffer database initialized at {DB_PATH}")


# ==================== Memory Buffer Operations ====================

def add_memory(
    memory_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    添加记忆到缓冲区
    
    Args:
        memory_type: 记忆类型 (operation_log, thinking_chain, dialogue, system_log)
        content: 记忆内容
        metadata: 元数据
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO memory_buffer (type, content, metadata)
            VALUES (?, ?, ?)
        """, (memory_type, content, metadata_json))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")


def get_unsynced_records(limit: int = SYNC_BATCH_SIZE) -> List[Dict[str, Any]]:
    """
    获取未同步的记录
    
    Args:
        limit: 最大记录数
    
    Returns:
        List[Dict]: 未同步的记录列表
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM memory_buffer
            WHERE synced = 0 AND retry_count < ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (MAX_RETRY_COUNT, limit))
        
        records = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return records
        
    except Exception as e:
        logger.error(f"Failed to get unsynced records: {e}")
        return []


def mark_as_synced(record_ids: List[int]):
    """
    标记记录为已同步
    
    Args:
        record_ids: 记录ID列表
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(record_ids))
        cursor.execute(f"""
            UPDATE memory_buffer
            SET synced = 1
            WHERE id IN ({placeholders})
        """, record_ids)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Marked {len(record_ids)} records as synced")
        
    except Exception as e:
        logger.error(f"Failed to mark records as synced: {e}")


def increment_retry_count(record_ids: List[int]):
    """
    增加重试计数
    
    Args:
        record_ids: 记录ID列表
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(record_ids))
        cursor.execute(f"""
            UPDATE memory_buffer
            SET retry_count = retry_count + 1,
                last_retry = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """, record_ids)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to increment retry count: {e}")


def cleanup_old_records(days: int = 7):
    """
    清理旧的已同步记录
    
    Args:
        days: 保留天数
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM memory_buffer
            WHERE synced = 1
            AND timestamp < datetime('now', '-' || ? || ' days')
        """, (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old synced records")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old records: {e}")


def get_buffer_stats() -> Dict[str, Any]:
    """
    获取缓冲区统计信息
    
    Returns:
        Dict: 统计信息
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM memory_buffer")
        total_count = cursor.fetchone()[0]
        
        # 未同步记录数
        cursor.execute("SELECT COUNT(*) FROM memory_buffer WHERE synced = 0")
        unsynced_count = cursor.fetchone()[0]
        
        # 已同步记录数
        cursor.execute("SELECT COUNT(*) FROM memory_buffer WHERE synced = 1")
        synced_count = cursor.fetchone()[0]
        
        # 失败记录数（重试次数>=MAX_RETRY_COUNT）
        cursor.execute("""
            SELECT COUNT(*) FROM memory_buffer 
            WHERE synced = 0 AND retry_count >= ?
        """, (MAX_RETRY_COUNT,))
        failed_count = cursor.fetchone()[0]
        
        # 各类型记录数
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM memory_buffer
            GROUP BY type
        """)
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_count": total_count,
            "unsynced_count": unsynced_count,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "type_counts": type_counts,
            "d5_url": D5_API_URL or "Not configured"
        }
        
    except Exception as e:
        logger.error(f"Failed to get buffer stats: {e}")
        return {}


# ==================== Sync to D5 ====================

def sync_to_d5(records: List[Dict[str, Any]]) -> bool:
    """
    同步记录到D5
    
    Args:
        records: 记录列表
    
    Returns:
        bool: 是否成功
    """
    if not D5_API_URL:
        logger.debug("D5_API_URL not configured, skipping sync")
        return False
    
    if not records:
        return True
    
    try:
        # 准备数据
        payload = {
            "agent_id": os.getenv("AGENT_ID", "m3-unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "records": [
                {
                    "type": record["type"],
                    "content": record["content"],
                    "metadata": json.loads(record["metadata"]) if record["metadata"] else {},
                    "timestamp": record["timestamp"]
                }
                for record in records
            ]
        }
        
        # 发送到D5
        response = requests.post(
            f"{D5_API_URL}/api/memory/receive",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            # 同步成功
            record_ids = [record["id"] for record in records]
            mark_as_synced(record_ids)
            logger.info(f"Successfully synced {len(records)} records to D5")
            return True
        else:
            # 同步失败
            logger.warning(f"D5 sync failed with status {response.status_code}: {response.text}")
            record_ids = [record["id"] for record in records]
            increment_retry_count(record_ids)
            return False
            
    except requests.exceptions.ConnectionError:
        logger.debug("D5 not available, will retry later")
        record_ids = [record["id"] for record in records]
        increment_retry_count(record_ids)
        return False
        
    except Exception as e:
        logger.error(f"Failed to sync to D5: {e}")
        record_ids = [record["id"] for record in records]
        increment_retry_count(record_ids)
        return False


# ==================== Background Sync Worker ====================

class MemorySyncWorker:
    """后台记忆同步工作器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """启动同步工作器"""
        if self.running:
            logger.warning("Memory sync worker already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        logger.info("Memory sync worker started")
    
    def stop(self):
        """停止同步工作器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Memory sync worker stopped")
    
    def _sync_loop(self):
        """同步循环"""
        while self.running:
            try:
                # 获取未同步的记录
                records = get_unsynced_records()
                
                if records:
                    logger.debug(f"Found {len(records)} unsynced records")
                    sync_to_d5(records)
                
                # 每天清理一次旧记录（在凌晨2点）
                current_hour = datetime.now().hour
                if current_hour == 2:
                    cleanup_old_records()
                
                # 等待下一次同步
                time.sleep(SYNC_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                time.sleep(SYNC_INTERVAL)


# ==================== Global Worker Instance ====================

_sync_worker = None


def start_memory_sync():
    """启动记忆同步"""
    global _sync_worker
    
    # 初始化数据库
    init_database()
    
    # 启动同步工作器
    _sync_worker = MemorySyncWorker()
    _sync_worker.start()


def stop_memory_sync():
    """停止记忆同步"""
    global _sync_worker
    
    if _sync_worker:
        _sync_worker.stop()


# ==================== Helper Functions ====================

def log_operation(operation: str, details: Dict[str, Any]):
    """记录操作日志"""
    add_memory(
        memory_type="operation_log",
        content=operation,
        metadata=details
    )


def log_thinking(thinking: str, context: Dict[str, Any]):
    """记录思考链"""
    add_memory(
        memory_type="thinking_chain",
        content=thinking,
        metadata=context
    )


def log_dialogue(role: str, message: str, metadata: Dict[str, Any]):
    """记录对话"""
    add_memory(
        memory_type="dialogue",
        content=f"{role}: {message}",
        metadata=metadata
    )


def log_system(level: str, message: str, details: Dict[str, Any]):
    """记录系统日志"""
    add_memory(
        memory_type="system_log",
        content=f"[{level}] {message}",
        metadata=details
    )


# Export
__all__ = [
    'start_memory_sync',
    'stop_memory_sync',
    'add_memory',
    'get_buffer_stats',
    'log_operation',
    'log_thinking',
    'log_dialogue',
    'log_system'
]
