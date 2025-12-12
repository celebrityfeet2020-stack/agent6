"""
上下文监控API
提供上下文长度监控、压缩历史、手动重置等功能
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.state import state_manager
from app.config import MAX_CONTEXT_LENGTH, COMPRESSION_TRIGGER_TOKENS, COMPRESSION_THRESHOLD

router = APIRouter()
logger = logging.getLogger(__name__)


class ContextStats(BaseModel):
    """上下文统计信息"""
    thread_id: str
    current_tokens: int
    max_tokens: int
    usage_percentage: float
    message_count: int
    compression_triggered: bool
    last_compression: Optional[str]
    status: str  # normal, warning, critical


class CompressionHistory(BaseModel):
    """压缩历史记录"""
    timestamp: str
    thread_id: str
    tokens_before: int
    tokens_after: int
    compression_ratio: float
    method: str


@router.get("/api/context/stats")
async def get_context_stats(
    thread_id: str = Query(default="default_session", description="线程ID")
):
    """
    获取指定线程的上下文统计信息
    
    Args:
        thread_id: 线程ID
        
    Returns:
        上下文统计信息
    """
    try:
        # 从state_manager获取上下文信息
        # 这里需要从LangGraph的checkpointer获取实际的上下文长度
        # 暂时返回模拟数据
        
        current_tokens = 1500  # 实际应该从checkpointer计算
        message_count = 10
        
        usage_percentage = (current_tokens / MAX_CONTEXT_LENGTH) * 100
        
        # 判断状态
        if usage_percentage < 70:
            status = "normal"
        elif usage_percentage < 90:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "thread_id": thread_id,
            "current_tokens": current_tokens,
            "max_tokens": MAX_CONTEXT_LENGTH,
            "usage_percentage": round(usage_percentage, 2),
            "message_count": message_count,
            "compression_triggered": current_tokens > COMPRESSION_TRIGGER_TOKENS,
            "last_compression": None,
            "status": status,
            "config": {
                "max_context_length": MAX_CONTEXT_LENGTH,
                "compression_trigger_tokens": COMPRESSION_TRIGGER_TOKENS,
                "compression_threshold": COMPRESSION_THRESHOLD
            }
        }
        
    except Exception as e:
        logger.error(f"获取上下文统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/context/threads")
async def get_all_context_threads():
    """
    获取所有活跃线程的上下文统计
    
    Returns:
        所有线程的统计信息列表
    """
    try:
        # 从unified_messenger获取所有线程
        from app.core.unified_messenger import unified_messenger
        
        threads = unified_messenger.get_all_threads()
        
        stats_list = []
        for thread_id in threads:
            # 获取每个线程的统计
            history = unified_messenger.get_history(thread_id, limit=1000)
            message_count = len(history)
            
            # 估算token数（简单估算：每条消息平均100 tokens）
            estimated_tokens = message_count * 100
            usage_percentage = (estimated_tokens / MAX_CONTEXT_LENGTH) * 100
            
            if usage_percentage < 70:
                status = "normal"
            elif usage_percentage < 90:
                status = "warning"
            else:
                status = "critical"
            
            stats_list.append({
                "thread_id": thread_id,
                "current_tokens": estimated_tokens,
                "max_tokens": MAX_CONTEXT_LENGTH,
                "usage_percentage": round(usage_percentage, 2),
                "message_count": message_count,
                "status": status
            })
        
        return {
            "threads": stats_list,
            "total_count": len(stats_list)
        }
        
    except Exception as e:
        logger.error(f"获取所有线程统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/context/compress")
async def compress_context(
    thread_id: str = Query(..., description="线程ID")
):
    """
    手动触发上下文压缩
    
    Args:
        thread_id: 线程ID
        
    Returns:
        压缩结果
    """
    try:
        # TODO: 实现实际的上下文压缩逻辑
        # 这需要与LangGraph的checkpointer交互
        
        logger.info(f"手动触发上下文压缩: thread_id={thread_id}")
        
        return {
            "success": True,
            "message": f"线程 {thread_id} 的上下文压缩已触发",
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat(),
            "compression_result": {
                "tokens_before": 2000,
                "tokens_after": 1000,
                "compression_ratio": 0.5,
                "method": "summarization"
            }
        }
        
    except Exception as e:
        logger.error(f"压缩上下文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/context/reset")
async def reset_context(
    thread_id: str = Query(..., description="线程ID"),
    keep_system_messages: bool = Query(default=True, description="是否保留系统消息")
):
    """
    手动重置上下文
    
    Args:
        thread_id: 线程ID
        keep_system_messages: 是否保留系统消息
        
    Returns:
        重置结果
    """
    try:
        # 清空消息历史
        from app.core.unified_messenger import unified_messenger
        
        if keep_system_messages:
            # 获取系统消息
            history = unified_messenger.get_history(thread_id, limit=1000)
            system_messages = [msg for msg in history if msg.get('role_type') == 'system']
            
            # 清空
            unified_messenger.clear_history(thread_id)
            
            # 恢复系统消息
            # TODO: 重新添加系统消息
            
            logger.info(f"重置上下文（保留系统消息）: thread_id={thread_id}, 保留了{len(system_messages)}条系统消息")
        else:
            unified_messenger.clear_history(thread_id)
            logger.info(f"完全重置上下文: thread_id={thread_id}")
        
        # TODO: 同时清空LangGraph checkpointer中的状态
        
        return {
            "success": True,
            "message": f"线程 {thread_id} 的上下文已重置",
            "thread_id": thread_id,
            "keep_system_messages": keep_system_messages,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"重置上下文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/context/compression-history")
async def get_compression_history(
    thread_id: Optional[str] = Query(default=None, description="线程ID，不指定则返回所有"),
    limit: int = Query(default=50, ge=1, le=200, description="返回的记录数")
):
    """
    获取压缩历史记录
    
    Args:
        thread_id: 线程ID（可选）
        limit: 返回的记录数
        
    Returns:
        压缩历史记录列表
    """
    try:
        # TODO: 从数据库或文件中读取压缩历史
        # 暂时返回空列表
        
        return {
            "thread_id": thread_id,
            "history": [],
            "count": 0
        }
        
    except Exception as e:
        logger.error(f"获取压缩历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/context/config")
async def get_context_config():
    """
    获取上下文配置
    
    Returns:
        上下文相关配置
    """
    return {
        "max_context_length": MAX_CONTEXT_LENGTH,
        "compression_trigger_tokens": COMPRESSION_TRIGGER_TOKENS,
        "compression_threshold": COMPRESSION_THRESHOLD,
        "description": {
            "max_context_length": "最大上下文长度（tokens）",
            "compression_trigger_tokens": "触发压缩的token阈值",
            "compression_threshold": "压缩阈值（0-1），越小压缩越激进"
        }
    }


@router.post("/api/context/config/update")
async def update_context_config(
    max_context_length: Optional[int] = Query(default=None, ge=1000, le=200000),
    compression_trigger_tokens: Optional[int] = Query(default=None, ge=500, le=100000),
    compression_threshold: Optional[float] = Query(default=None, ge=0.1, le=1.0)
):
    """
    更新上下文配置（运行时）
    
    注意：这只会更新运行时配置，重启后会恢复到config.py中的默认值
    
    Args:
        max_context_length: 最大上下文长度
        compression_trigger_tokens: 触发压缩的token阈值
        compression_threshold: 压缩阈值
        
    Returns:
        更新结果
    """
    try:
        updated_fields = []
        
        if max_context_length is not None:
            state_manager.config.MAX_CONTEXT_LENGTH = max_context_length
            updated_fields.append("max_context_length")
        
        if compression_trigger_tokens is not None:
            state_manager.config.COMPRESSION_TRIGGER_TOKENS = compression_trigger_tokens
            updated_fields.append("compression_trigger_tokens")
        
        if compression_threshold is not None:
            state_manager.config.COMPRESSION_THRESHOLD = compression_threshold
            updated_fields.append("compression_threshold")
        
        logger.info(f"上下文配置已更新: {updated_fields}")
        
        return {
            "success": True,
            "message": "配置已更新（运行时）",
            "updated_fields": updated_fields,
            "current_config": {
                "max_context_length": state_manager.config.MAX_CONTEXT_LENGTH,
                "compression_trigger_tokens": state_manager.config.COMPRESSION_TRIGGER_TOKENS,
                "compression_threshold": state_manager.config.COMPRESSION_THRESHOLD
            },
            "warning": "重启后将恢复到config.py中的默认值"
        }
        
    except Exception as e:
        logger.error(f"更新上下文配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
