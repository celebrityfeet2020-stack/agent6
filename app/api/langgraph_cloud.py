"""
LangGraph Cloud兼容API
实现完整的LangGraph Cloud API端点,支持@assistant-ui/react-langgraph前端
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
from app.state import state_manager

router = APIRouter()

# ==================== 数据模型 ====================

class Message(BaseModel):
    """消息模型"""
    role: str
    content: str
    
class StreamInput(BaseModel):
    """流式输入模型"""
    messages: List[Message]
    config: Optional[Dict[str, Any]] = {}

class ThreadCreate(BaseModel):
    """创建线程模型"""
    metadata: Optional[Dict[str, Any]] = {}

# ==================== 线程管理 ====================

@router.post("/threads")
async def create_thread(data: ThreadCreate):
    """创建新线程"""
    thread_id = f"thread_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 初始化线程状态
    state_manager.chat_sessions[thread_id] = {
        "thread_id": thread_id,
        "created_at": datetime.now().isoformat(),
        "metadata": data.metadata or {},
        "messages": [],
        "state": {}
    }
    
    return {
        "thread_id": thread_id,
        "created_at": state_manager.chat_sessions[thread_id]["created_at"],
        "metadata": data.metadata or {}
    }

@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """获取线程信息"""
    if thread_id not in state_manager.chat_sessions:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread = state_manager.chat_sessions[thread_id]
    return {
        "thread_id": thread_id,
        "created_at": thread["created_at"],
        "metadata": thread["metadata"],
        "values": {
            "messages": thread["messages"]
        }
    }

@router.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """获取线程状态"""
    if thread_id not in state_manager.chat_sessions:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread = state_manager.chat_sessions[thread_id]
    return {
        "values": {
            "messages": thread["messages"]
        },
        "tasks": [],
        "next": []
    }

# ==================== 助手/图执行 ====================

@router.post("/assistants/{assistant_id}/threads/{thread_id}/runs/stream")
async def stream_run(assistant_id: str, thread_id: str, data: StreamInput):
    """流式执行助手(兼容LangGraph Cloud API)"""
    
    # 确保线程存在
    if thread_id not in state_manager.chat_sessions:
        state_manager.chat_sessions[thread_id] = {
            "thread_id": thread_id,
            "created_at": datetime.now().isoformat(),
            "metadata": {},
            "messages": [],
            "state": {}
        }
    
    async def event_stream():
        """生成SSE事件流"""
        try:
             # 1. 发送metadata事件
            run_id = f"run_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            yield f"event: metadata\n"
            yield f"data: {json.dumps({'run_id': run_id, 'thread_id': thread_id})}\n\n"
            
            # 2. 获取LangGraph工作流
            app_graph = state_manager.get_app_graph()
            if not app_graph:
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': 'LangGraph工作流未初始化'})}\n\n"
                return
            
            # 3. 转换消息格式
            from langchain_core.messages import HumanMessage, AIMessage
            messages = []
            for msg in data.messages:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
            
            # 4. 流式执行工作流
            config = {"configurable": {"thread_id": thread_id}}
            
            async for event in app_graph.astream_events(
                {"messages": messages},
                config=config,
                version="v2"
            ):
                event_type = event.get("event")
                
                # 发送消息更新事件
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        yield f"event: messages/partial\n"
                        yield f"data: {json.dumps([{'role': 'assistant', 'content': chunk.content}])}\n\n"
                
                # 发送工具调用事件
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    yield f"event: updates\n"
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"
                
                # 发送工具结果事件
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", "")
                    yield f"event: updates\n"
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'output': str(output)[:200]})}\n\n"
            
            # 5. 发送完成事件
            yield f"event: end\n"
            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
            
        except Exception as e:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ==================== 简化的图执行API(用于直接调用) ====================

@router.post("/runs/stream")
async def simple_stream_run(data: StreamInput):
    """简化的流式执行API(自动创建线程)"""
    # 创建临时线程
    thread_id = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    # 转发到完整的stream_run
    return await stream_run("default", thread_id, data)

