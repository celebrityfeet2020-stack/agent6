"""
LangGraph API Adapter for M3 Agent System v2.7
提供标准的LangGraph API端点，支持assistant-ui等客户端
"""

import uuid
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/assistants", tags=["LangGraph API"])


# ==================== Pydantic Models ====================

class ThreadCreateRequest(BaseModel):
    """创建线程请求"""
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ThreadResponse(BaseModel):
    """线程响应"""
    thread_id: str
    created_at: str
    metadata: Dict[str, Any]


class RunRequest(BaseModel):
    """运行请求"""
    input: str = Field(..., description="User input message")
    stream: bool = Field(default=True, description="Whether to stream the response")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RunResponse(BaseModel):
    """运行响应"""
    run_id: str
    thread_id: str
    status: str
    output: Optional[str] = None


# ==================== In-Memory Thread Storage ====================
# 简单的内存存储，生产环境应使用数据库
_threads: Dict[str, Dict[str, Any]] = {}


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    """获取线程"""
    return _threads.get(thread_id)


def create_thread(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """创建新线程"""
    thread_id = str(uuid.uuid4())
    thread = {
        "thread_id": thread_id,
        "created_at": datetime.utcnow().isoformat(),
        "metadata": metadata or {},
        "messages": []
    }
    _threads[thread_id] = thread
    return thread


def delete_thread(thread_id: str) -> bool:
    """删除线程"""
    if thread_id in _threads:
        del _threads[thread_id]
        return True
    return False


# ==================== API Endpoints ====================

@router.post("/{assistant_id}/threads", response_model=ThreadResponse)
async def create_thread_endpoint(
    assistant_id: str,
    request: Optional[ThreadCreateRequest] = None
):
    """
    创建新的对话线程
    
    Args:
        assistant_id: Assistant ID (目前未使用，预留)
        request: 线程创建请求
    
    Returns:
        ThreadResponse: 新创建的线程信息
    """
    metadata = request.metadata if request else {}
    thread = create_thread(metadata)
    
    logger.info(f"Created thread {thread['thread_id']} for assistant {assistant_id}")
    
    return ThreadResponse(
        thread_id=thread["thread_id"],
        created_at=thread["created_at"],
        metadata=thread["metadata"]
    )


@router.get("/{assistant_id}/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread_endpoint(assistant_id: str, thread_id: str):
    """
    获取线程信息
    
    Args:
        assistant_id: Assistant ID
        thread_id: Thread ID
    
    Returns:
        ThreadResponse: 线程信息
    """
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    return ThreadResponse(
        thread_id=thread["thread_id"],
        created_at=thread["created_at"],
        metadata=thread["metadata"]
    )


@router.delete("/{assistant_id}/threads/{thread_id}")
async def delete_thread_endpoint(assistant_id: str, thread_id: str):
    """
    删除线程
    
    Args:
        assistant_id: Assistant ID
        thread_id: Thread ID
    
    Returns:
        Dict: 删除结果
    """
    success = delete_thread(thread_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    logger.info(f"Deleted thread {thread_id}")
    return {"status": "deleted", "thread_id": thread_id}


@router.post("/{assistant_id}/threads/{thread_id}/runs/stream")
async def stream_run_endpoint(
    assistant_id: str,
    thread_id: str,
    request: RunRequest
):
    """
    流式运行Agent（核心端点）
    
    Args:
        assistant_id: Assistant ID
        thread_id: Thread ID
        request: 运行请求
    
    Returns:
        StreamingResponse: 流式响应
    """
    # 验证线程存在
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    logger.info(f"Starting stream run for thread {thread_id}, input: {request.input[:50]}...")
    
    # 创建流式响应
    async def generate_stream() -> AsyncGenerator[str, None]:
        """生成流式响应"""
        try:
            # 导入Agent（延迟导入避免循环依赖）
            import main
            app_graph = main.app_graph
            
            # 准备输入
            input_data = {
                "messages": [{"role": "user", "content": request.input}]
            }
            
            # 配置
            run_config = {
                "configurable": {"thread_id": thread_id},
                **request.config
            }
            
            # 流式执行Agent
            async for chunk in app_graph.astream(input_data, config=run_config):
                # 调试日志
                logger.debug(f"Stream chunk: {chunk}")
                
                # 格式化为LangGraph标准格式
                formatted_chunk = format_langgraph_chunk(chunk)
                if formatted_chunk:
                    yield f"data: {formatted_chunk}\n\n"
                else:
                    # 即使没有格式化成功，也输出原始数据供调试
                    import json
                    try:
                        raw_data = json.dumps({"type": "raw", "data": str(chunk)})
                        yield f"data: {raw_data}\n\n"
                    except:
                        pass
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
            
            logger.info(f"Stream run completed for thread {thread_id}")
            
        except Exception as e:
            logger.error(f"Stream run error: {e}", exc_info=True)
            error_chunk = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{assistant_id}/threads/{thread_id}/runs", response_model=RunResponse)
async def run_endpoint(
    assistant_id: str,
    thread_id: str,
    request: RunRequest
):
    """
    非流式运行Agent
    
    Args:
        assistant_id: Assistant ID
        thread_id: Thread ID
        request: 运行请求
    
    Returns:
        RunResponse: 运行结果
    """
    # 验证线程存在
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    logger.info(f"Starting run for thread {thread_id}, input: {request.input[:50]}...")
    
    try:
        # 导入Agent
        import main
        app_graph = main.app_graph
        
        # 准备输入
        input_data = {
            "messages": [{"role": "user", "content": request.input}]
        }
        
        # 配置
        run_config = {
            "configurable": {"thread_id": thread_id},
            **request.config
        }
        
        # 执行Agent
        result = await app_graph.ainvoke(input_data, config=run_config)
        
        # 提取输出
        output = extract_output_from_result(result)
        
        run_id = str(uuid.uuid4())
        
        logger.info(f"Run completed for thread {thread_id}")
        
        return RunResponse(
            run_id=run_id,
            thread_id=thread_id,
            status="completed",
            output=output
        )
        
    except Exception as e:
        logger.error(f"Run error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ====================

def format_langgraph_chunk(chunk: Any) -> Optional[str]:
    """
    格式化LangGraph chunk为标准格式
    
    Args:
        chunk: Agent输出的chunk
    
    Returns:
        str: JSON格式的chunk，如果无需输出则返回None
    """
    import json
    
    try:
        # 提取消息内容
        if isinstance(chunk, dict):
            # 检查是否有messages
            if "messages" in chunk:
                messages = chunk["messages"]
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    
                    # 提取内容
                    if hasattr(last_message, "content"):
                        content = last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        content = last_message["content"]
                    else:
                        return None
                    
                    # 格式化输出
                    output = {
                        "type": "message",
                        "content": content
                    }
                    return json.dumps(output)
        
        return None
        
    except Exception as e:
        logger.warning(f"Error formatting chunk: {e}")
        return None


def extract_output_from_result(result: Any) -> str:
    """
    从Agent结果中提取输出
    
    Args:
        result: Agent执行结果
    
    Returns:
        str: 输出文本
    """
    try:
        if isinstance(result, dict):
            # 检查是否有messages
            if "messages" in result:
                messages = result["messages"]
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    
                    # 提取内容
                    if hasattr(last_message, "content"):
                        return last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        return last_message["content"]
        
        return str(result)
        
    except Exception as e:
        logger.warning(f"Error extracting output: {e}")
        return str(result)


# Export router
__all__ = ['router']
