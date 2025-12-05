"""
聊天室SSE流式API
为聊天室前端提供/api/chat/stream端点
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

@router.get("/api/chat/stream")
async def chat_stream(message: str, user_id: str = "anonymous"):
    """
    SSE流式聊天端点
    前端通过EventSource连接此端点
    """
    async def event_generator():
        try:
            # 导入必要的模块
            from app.core.state_manager import StateManager
            
            state_mgr = StateManager()
            app_graph = state_mgr.get("app_graph")
            
            if not app_graph:
                # 如果workflow未初始化,返回错误
                yield f"data: {json.dumps({'error': 'Agent未初始化,请等待5分钟'})}\n\n"
                return
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # 构造输入
            input_data = {
                "messages": [{"role": "user", "content": message}]
            }
            
            # 流式执行workflow
            async for event in app_graph.astream(input_data):
                # 发送中间结果
                if "agent" in event:
                    messages = event["agent"].get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        
                        # 如果是AI消息
                        if hasattr(last_message, "content"):
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
                                yield f"data: {json.dumps({'type': 'tool_result', 'content': msg.content})}\n\n"
                
                # 短暂延迟,避免过快
                await asyncio.sleep(0.01)
            
            # 发送结束事件
            yield f"data: {json.dumps({'type': 'end', 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            # 发送错误事件
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
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
    from app.core.state_manager import StateManager
    
    state_mgr = StateManager()
    tools_loaded = state_mgr.get("tools_loaded", False)
    
    return {
        "status": "healthy",
        "tools_loaded": tools_loaded,
        "timestamp": datetime.now().isoformat()
    }
