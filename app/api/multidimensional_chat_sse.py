"""
多维聊天室API - SSE流式版本
支持任意角色类型的聊天,通过SSE推送消息
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, AsyncGenerator
import json
import asyncio
from datetime import datetime

from app.workflow.graph import create_agent_graph
from app.core.unified_messenger import unified_messenger

router = APIRouter()


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    thread_id: str = Field(default="default_session", description="线程ID")
    source: str = Field(default="user", description="消息来源(已废弃,使用role_type)")
    role_type: str = Field(default="user", description="角色类型(user/admin/n8_workflow/digital_human_guest等)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


@router.post("/api/multidimensional/chat/stream")
async def multidimensional_chat_stream(request: ChatRequest):
    """
    多维聊天室 - SSE流式API
    
    支持任意角色类型,通过SSE推送消息到前端
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """SSE事件生成器"""
        try:
            # 1. 推送用户消息到统一消息总线
            unified_messenger.send_user_message(
                thread_id=request.thread_id,
                content=request.message,
                role_type=request.role_type,
                metadata=request.metadata or {}
            )
            
            # 2. 推送用户消息事件到前端
            yield f"event: message\n"
            user_msg_data = json.dumps({
                'type': 'message',
                'role': 'user',
                'role_type': request.role_type,
                'source': request.role_type,
                'content': request.message,
                'timestamp': datetime.now().isoformat(),
                'metadata': request.metadata
            }, ensure_ascii=False)
            yield f"data: {user_msg_data}\n\n"
            
            # 3. 调用Agent处理
            graph = create_agent_graph()
            config = {
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
            
            # 4. 流式处理Agent响应
            async for event in graph.astream_events(
                {"messages": [("user", request.message)]},
                config=config,
                version="v2"
            ):
                event_type = event.get("event")
                
                # 处理不同类型的事件
                if event_type == "on_chat_model_stream":
                    # AI响应流
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        # 推送AI响应到统一消息总线
                        unified_messenger.send_message(
                            thread_id=request.thread_id,
                            content=chunk.content,
                            role_type="assistant",
                            msg_type="text"
                        )
                        
                        # 推送到前端
                        yield f"event: message\n"
                        ai_msg_data = json.dumps({
                            'type': 'message',
                            'role': 'assistant',
                            'role_type': 'assistant',
                            'source': 'assistant',
                            'content': chunk.content,
                            'timestamp': datetime.now().isoformat()
                        }, ensure_ascii=False)
                        yield f"data: {ai_msg_data}\n\n"
                
                elif event_type == "on_tool_start":
                    # 工具调用开始
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    tool_id = f"tool-{datetime.now().timestamp()}"
                    
                    # 推送工具调用到统一消息总线
                    unified_messenger.send_tool_call_message(
                        thread_id=request.thread_id,
                        tool_name=tool_name,
                        tool_input=tool_input
                    )
                    
                    # 推送到前端
                    yield f"event: tool\n"
                    tool_call_data = json.dumps({
                        'type': 'tool_call',
                        'id': tool_id,
                        'tool_name': tool_name,
                        'status': 'calling',
                        'input': tool_input,
                        'timestamp': datetime.now().isoformat()
                    }, ensure_ascii=False)
                    yield f"data: {tool_call_data}\n\n"
                
                elif event_type == "on_tool_end":
                    # 工具调用结束
                    tool_name = event.get("name", "unknown")
                    tool_output = event.get("data", {}).get("output")
                    tool_id = f"tool-{datetime.now().timestamp()}"
                    
                    # 推送工具结果到统一消息总线
                    unified_messenger.send_tool_result_message(
                        thread_id=request.thread_id,
                        tool_name=tool_name,
                        tool_output=tool_output
                    )
                    
                    # 推送到前端
                    yield f"event: tool\n"
                    tool_result_data = json.dumps({
                        'type': 'tool_result',
                        'id': tool_id,
                        'tool_name': tool_name,
                        'status': 'success',
                        'output': tool_output,
                        'timestamp': datetime.now().isoformat()
                    }, ensure_ascii=False)
                    yield f"data: {tool_result_data}\n\n"
                
                # 避免事件过快
                await asyncio.sleep(0.01)
            
            # 5. 推送完成事件
            yield f"event: done\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            # 推送错误事件
            yield f"event: error\n"
            error_data = json.dumps({
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    # 返回SSE响应
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )
