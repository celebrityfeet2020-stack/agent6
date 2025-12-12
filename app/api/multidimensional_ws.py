"""
多维聊天室WebSocket API
提供实时消息流订阅功能
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging

from app.core.unified_messenger import unified_messenger

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/api/multidimensional/chat/ws")
async def multidimensional_chat_websocket(
    websocket: WebSocket,
    thread_id: str = Query(default="default", description="线程ID")
):
    """
    多维聊天室WebSocket端点
    
    客户端连接后会收到：
    1. 历史消息（最近100条）
    2. 实时新消息
    
    消息格式：
    {
        "type": "message",
        "data": {
            "message_id": "msg_xxx",
            "content": "消息内容",
            "role_type": "user/admin/n8_workflow/...",
            "role_id": "角色ID",
            "role_name": "显示名称",
            "thread_id": "线程ID",
            "message_type": "text/tool_call/tool_result/system",
            "metadata": {},
            "timestamp": "2025-01-01T00:00:00"
        }
    }
    """
    await websocket.accept()
    logger.info(f"📡 新WebSocket连接: thread_id={thread_id}")
    
    try:
        # 注册连接
        unified_messenger.register_connection(thread_id, websocket)
        
        # 发送历史消息
        history = unified_messenger.get_history(thread_id, limit=100)
        if history:
            await websocket.send_json({
                "type": "history",
                "data": {
                    "messages": history,
                    "count": len(history)
                }
            })
        
        # 发送欢迎消息
        await websocket.send_json({
            "type": "system",
            "data": {
                "message": f"✅ 已连接到多维聊天室 (线程: {thread_id})",
                "timestamp": unified_messenger.get_stats()
            }
        })
        
        # 保持连接，等待客户端断开
        while True:
            # 接收客户端消息（如果有的话）
            data = await websocket.receive_text()
            
            # 这里可以处理客户端发送的控制命令
            # 例如：{"command": "clear_history"}
            import json
            try:
                command = json.loads(data)
                if command.get("command") == "clear_history":
                    unified_messenger.clear_history(thread_id)
                    await websocket.send_json({
                        "type": "system",
                        "data": {"message": "✅ 历史消息已清空"}
                    })
                elif command.get("command") == "get_stats":
                    stats = unified_messenger.get_stats()
                    await websocket.send_json({
                        "type": "stats",
                        "data": stats
                    })
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket连接断开: thread_id={thread_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket错误: {e}")
    finally:
        # 注销连接
        unified_messenger.unregister_connection(thread_id, websocket)


@router.get("/api/multidimensional/chat/history")
async def get_chat_history(
    thread_id: str = Query(default="default", description="线程ID"),
    limit: int = Query(default=100, ge=1, le=500, description="返回的消息数量")
):
    """
    获取聊天历史
    
    Args:
        thread_id: 线程ID
        limit: 返回的消息数量（1-500）
        
    Returns:
        消息列表
    """
    history = unified_messenger.get_history(thread_id, limit=limit)
    
    return {
        "thread_id": thread_id,
        "messages": history,
        "count": len(history)
    }


@router.get("/api/multidimensional/chat/threads")
async def get_all_threads():
    """获取所有活跃的线程ID"""
    threads = unified_messenger.get_all_threads()
    
    return {
        "threads": threads,
        "count": len(threads)
    }


@router.get("/api/multidimensional/chat/stats")
async def get_messenger_stats():
    """获取消息总线统计信息"""
    stats = unified_messenger.get_stats()
    
    return stats


@router.post("/api/multidimensional/chat/clear")
async def clear_chat_history(thread_id: str = Query(..., description="线程ID")):
    """清空指定线程的聊天历史"""
    unified_messenger.clear_history(thread_id)
    
    return {
        "success": True,
        "message": f"线程 {thread_id} 的历史消息已清空"
    }
