"""
Fleet记忆本地数据库
使用SQLite存储Fleet API记忆,支持降级和离线使用
"""
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class FleetMemoryDB:
    """Fleet记忆数据库管理器"""
    
    # 存储限制: 500GB
    MAX_STORAGE_BYTES = 500 * 1024 * 1024 * 1024  # 500GB
    
    def __init__(self, db_path: str = "/app/data/fleet_memories.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保数据目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库表
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                source TEXT DEFAULT 'agent6',
                synced_to_fleet INTEGER DEFAULT 0,
                fleet_memory_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON memories(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_synced 
            ON memories(synced_to_fleet)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON memories(timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def add_memory(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """
        添加记忆
        
        Args:
            session_id: 会话ID
            content: 记忆内容
            metadata: 元数据
            memory_id: 记忆ID(可选,不提供则自动生成)
            
        Returns:
            记忆ID
            
        Raises:
            Exception: 存储已满
        """
        # 检查存储限制
        if self.is_storage_full():
            raise Exception(
                f"Fleet记忆库存储已满! "
                f"当前大小: {self.get_storage_size() / 1024 / 1024 / 1024:.2f}GB, "
                f"限制: {self.MAX_STORAGE_BYTES / 1024 / 1024 / 1024:.0f}GB. "
                f"请同步到Fleet API后删除本地数据。"
            )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 生成ID
        if not memory_id:
            memory_id = f"mem_{session_id}_{int(datetime.now().timestamp() * 1000)}"
        
        # 当前时间
        now = datetime.now().isoformat()
        
        # 插入记忆
        cursor.execute("""
            INSERT INTO memories (
                id, session_id, content, metadata, timestamp, 
                source, synced_to_fleet, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            session_id,
            content,
            json.dumps(metadata or {}, ensure_ascii=False),
            now,
            "agent6",
            0,  # 未同步
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆字典,不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM memories WHERE id = ?
        """, (memory_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    def get_session_memories(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取指定会话的所有记忆
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM memories 
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (session_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def list_all_memories(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出所有记忆
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM memories 
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_unsynced_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取未同步到Fleet API的记忆
        
        Args:
            limit: 返回数量限制
            
        Returns:
            未同步记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM memories 
            WHERE synced_to_fleet = 0
            ORDER BY timestamp ASC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def mark_as_synced(self, memory_id: str, fleet_memory_id: str):
        """
        标记记忆已同步到Fleet API
        
        Args:
            memory_id: 本地记忆ID
            fleet_memory_id: Fleet API返回的记忆ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE memories 
            SET synced_to_fleet = 1,
                fleet_memory_id = ?,
                updated_at = ?
            WHERE id = ?
        """, (fleet_memory_id, datetime.now().isoformat(), memory_id))
        
        conn.commit()
        conn.close()
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM memories WHERE id = ?
        """, (memory_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_storage_size(self) -> int:
        """
        获取数据库文件大小(字节)
        
        Returns:
            数据库文件大小
        """
        try:
            return os.path.getsize(self.db_path)
        except:
            return 0
    
    def is_storage_full(self) -> bool:
        """
        检查存储是否已满
        
        Returns:
            是否超过存储限制
        """
        return self.get_storage_size() >= self.MAX_STORAGE_BYTES
    
    def get_storage_usage_percent(self) -> float:
        """
        获取存储使用率
        
        Returns:
            使用率(百分比)
        """
        return (self.get_storage_size() / self.MAX_STORAGE_BYTES) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总记忆数
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_count = cursor.fetchone()[0]
        
        # 已同步数
        cursor.execute("SELECT COUNT(*) FROM memories WHERE synced_to_fleet = 1")
        synced_count = cursor.fetchone()[0]
        
        # 未同步数
        unsynced_count = total_count - synced_count
        
        # 会话数
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM memories")
        session_count = cursor.fetchone()[0]
        
        # 最新记忆时间
        cursor.execute("SELECT MAX(timestamp) FROM memories")
        latest_timestamp = cursor.fetchone()[0]
        
        conn.close()
        
        # 存储大小
        storage_size = self.get_storage_size()
        storage_usage_percent = self.get_storage_usage_percent()
        
        return {
            "total_memories": total_count,
            "synced_memories": synced_count,
            "unsynced_memories": unsynced_count,
            "total_sessions": session_count,
            "latest_memory_timestamp": latest_timestamp,
            "sync_rate": f"{synced_count / total_count * 100:.1f}%" if total_count > 0 else "0%",
            "storage_size_bytes": storage_size,
            "storage_size_mb": round(storage_size / 1024 / 1024, 2),
            "storage_size_gb": round(storage_size / 1024 / 1024 / 1024, 2),
            "storage_limit_gb": 500,
            "storage_usage_percent": round(storage_usage_percent, 2),
            "storage_is_full": self.is_storage_full()
        }
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        将数据库行转换为字典
        
        Args:
            row: 数据库行
            
        Returns:
            字典
        """
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "timestamp": row["timestamp"],
            "source": row["source"],
            "synced_to_fleet": bool(row["synced_to_fleet"]),
            "fleet_memory_id": row["fleet_memory_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }


# 全局单例
fleet_memory_db = FleetMemoryDB()
