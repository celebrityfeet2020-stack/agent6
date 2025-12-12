"""
聊天室SSE流式API
为聊天室前端提供/api/chat/stream端点
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
import json
import asyncio
from datetime import datetime
from langchain_core.messages import HumanMessage

from app.state import state_manager
from app.config import MAX_CONTEXT_LENGTH, COMPRESSION_TRIGGER_TOKENS

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_session"
    source: str = "user"
    metadata: Dict[str, Any] = {}


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE流式聊天端点
    前端通过EventSource连接此端点
    """
    async def event_generator():
        try:
            # 从全局状态获取app_graph
            app_graph = state_manager.get_app_graph()
            
            if not app_graph:
                # 如果workflow未初始化,返回错误
                yield f"data: {json.dumps({'type': 'error', 'message': 'Agent未初始化,请等待启动完成'})}\n\n"
                return
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # 构造输入
            input_data = {
                "messages": [HumanMessage(content=request.message)]
            }
            
            # 配置(包含thread_id用于会话管理)
            config = {
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
            
            # 流式执行workflow
            async for event in app_graph.astream(input_data, config=config):
                # 发送中间结果
                if "agent" in event:
                    messages = event["agent"].get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        
                        # 如果是AI消息
                        if hasattr(last_message, "content") and last_message.content:
                            yield f"data: {json.dumps({'type': 'message', 'content': last_message.content})}\n\n"
                        
                        # 如果有工具调用
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_call.get('name'), 'args': tool_call.get('args')})}\n\n"
                
                # 如果有工具结果
                if "tools" in event:
                    messages = event["tools"].get("messages", [])
                    if messages:
                        for msg in messages:
                            if hasattr(msg, "content"):
                                yield f"data: {json.dumps({'type': 'tool_result', 'content': str(msg.content)[:500]})}\n\n"  # 限制长度
                
                # 短暂延迟,避免过快
                await asyncio.sleep(0.01)
            
            # 发送结束事件
            yield f"data: {json.dumps({'type': 'end', 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            # 发送错误事件
            error_msg = f"聊天处理错误: {str(e)}"
            print(f"ERROR: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )


@router.get("/api/chat/health")
async def chat_health():
    """健康检查"""
    return {
        "status": "healthy",
        "tools_loaded": state_manager.tool_pool_loaded,
        "app_graph_loaded": state_manager.app_graph is not None,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/chat/context_stats")
async def get_context_stats():
    """获取上下文统计信息"""
    stats = state_manager.get_context_stats()
    
    # 计算使用率
    current_tokens = stats.get("current_tokens", 0)
    usage_percent = (current_tokens / MAX_CONTEXT_LENGTH * 100) if MAX_CONTEXT_LENGTH > 0 else 0
    
    # 确定记忆状态
    compression_count = stats.get("compression_count", 0)
    if compression_count == 0:
        memory_status = "🟢 完美记忆"
    elif compression_count == 1:
        memory_status = "🟡 轻度失忆"
    elif compression_count == 2:
        memory_status = "🟠 中度失忆(建议重置)"
    else:
        memory_status = "🔴 重度失忆(必须重置)"
    
    return {
        "current_tokens": current_tokens,
        "max_tokens": MAX_CONTEXT_LENGTH,
        "compression_threshold": COMPRESSION_TRIGGER_TOKENS,
        "usage_percent": round(usage_percent, 2),
        "compression_count": compression_count,
        "memory_status": memory_status,
        "last_compression_time": stats.get("last_compression_time")
    }
