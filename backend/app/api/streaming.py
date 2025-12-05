"""
Enhanced SSE Streaming Module for Agent System v3.6
支持前端要求的 thought / tool / system 事件流推送
"""

import json
import uuid
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from app.memory.memory_logger import log_dialogue, log_thinking, log_tool_operation, log_system_event

logger = logging.getLogger(__name__)


class SSEEventFormatter:
    """SSE事件格式化器"""
    
    @staticmethod
    def format_event(event_type: str, data: Dict[str, Any]) -> str:
        """
        格式化SSE事件
        
        Args:
            event_type: 事件类型 (thought/tool/system/message)
            data: 事件数据
            
        Returns:
            str: 格式化的SSE事件字符串
        """
        try:
            event_data = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "type": event_type,
                **data
            }
            return f"event: {event_type}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Error formatting SSE event: {e}")
            return ""
    
    @staticmethod
    def format_thought(content: str, metadata: Optional[Dict] = None) -> str:
        """
        格式化思考事件
        
        Args:
            content: 思考内容
            metadata: 额外元数据
            
        Returns:
            str: 格式化的SSE事件
        """
        data = {
            "content": content,
            "metadata": metadata or {}
        }
        return SSEEventFormatter.format_event("thought", data)
    
    @staticmethod
    def format_tool_call(tool_name: str, tool_input: Dict, tool_call_id: str) -> str:
        """
        格式化工具调用事件
        
        Args:
            tool_name: 工具名称
            tool_input: 工具输入
            tool_call_id: 工具调用ID
            
        Returns:
            str: 格式化的SSE事件
        """
        data = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_call_id": tool_call_id,
            "status": "calling"
        }
        return SSEEventFormatter.format_event("tool", data)
    
    @staticmethod
    def format_tool_result(tool_name: str, tool_output: str, tool_call_id: str, success: bool = True) -> str:
        """
        格式化工具结果事件
        
        Args:
            tool_name: 工具名称
            tool_output: 工具输出
            tool_call_id: 工具调用ID
            success: 是否成功
            
        Returns:
            str: 格式化的SSE事件
        """
        data = {
            "tool_name": tool_name,
            "tool_output": tool_output,
            "tool_call_id": tool_call_id,
            "status": "success" if success else "error"
        }
        return SSEEventFormatter.format_event("tool", data)
    
    @staticmethod
    def format_system_log(level: str, message: str, source: str = "agent", metadata: Optional[Dict] = None) -> str:
        """
        格式化系统日志事件
        
        Args:
            level: 日志级别 (info/warning/error)
            message: 日志消息
            source: 日志来源
            metadata: 额外元数据
            
        Returns:
            str: 格式化的SSE事件
        """
        data = {
            "level": level,
            "message": message,
            "source": source,
            "metadata": metadata or {}
        }
        return SSEEventFormatter.format_event("system", data)
    
    @staticmethod
    def format_message_delta(content: str, role: str = "assistant") -> str:
        """
        格式化消息增量事件（打字机效果）
        
        Args:
            content: 消息内容增量
            role: 角色 (assistant/user)
            
        Returns:
            str: 格式化的SSE事件
        """
        data = {
            "role": role,
            "content": content,
            "delta": True
        }
        return SSEEventFormatter.format_event("message", data)
    
    @staticmethod
    def format_message_complete(content: str, role: str = "assistant") -> str:
        """
        格式化消息完成事件
        
        Args:
            content: 完整消息内容
            role: 角色
            
        Returns:
            str: 格式化的SSE事件
        """
        data = {
            "role": role,
            "content": content,
            "delta": False,
            "complete": True
        }
        return SSEEventFormatter.format_event("message", data)


async def stream_agent_response_with_enhanced_thought_chain(
    app_graph,
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    thread_id: str,
    client_id: Optional[str] = None,
    enable_enhanced_thought_chain: bool = True
) -> AsyncGenerator[str, None]:
    """
    v5.8增强版：流式执行Agent并生成详细的思维链
    
    新增思维链步骤：
    1. understanding - 理解任务
    2. tool_selection - 选择工具
    3. executing - 执行工具
    4. analyzing - 分析结果
    5. synthesizing - 综合信息
    6. completed - 完成任务
    """
    try:
        # Step 1: 理解任务
        if enable_enhanced_thought_chain:
            messages = input_data.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    user_message = last_msg.get("content", "")
                else:
                    user_message = getattr(last_msg, "content", "")
            else:
                user_message = ""
            yield SSEEventFormatter.format_thought(
                f"正在理解用户需求：{user_message[:50]}...",
                metadata={"step": "understanding", "thread_id": thread_id}
            )
        
        # 发送系统日志：开始处理
        yield SSEEventFormatter.format_system_log(
            "info",
            f"开始处理请求 (thread_id={thread_id})",
            metadata={"thread_id": thread_id, "client_id": client_id}
        )
        
        # 记录到D5记忆航母
        log_system_event(
            f"开始处理请求 (thread_id={thread_id})",
            level="info",
            interface="sse_api",
            client_id=client_id,
            thread_id=thread_id
        )
        
        # 用于累积AI消息内容
        current_ai_message = ""
        tool_selection_sent = False
        
        # 流式执行Agent
        async for chunk in app_graph.astream(input_data, config=config):
            logger.debug(f"Stream chunk: {chunk}")
            
            # 处理不同类型的chunk
            if isinstance(chunk, dict):
                # 检查是否有messages
                if "messages" in chunk:
                    messages = chunk["messages"]
                    if messages and len(messages) > 0:
                        last_message = messages[-1]
                        
                        # 处理AI消息
                        if isinstance(last_message, AIMessage) or (isinstance(last_message, dict) and last_message.get("type") == "ai"):
                            # 安全获取content
                            if isinstance(last_message, dict):
                                content = last_message.get("content", "")
                                tool_calls = last_message.get("tool_calls", [])
                            else:
                                content = getattr(last_message, "content", "")
                                tool_calls = getattr(last_message, "tool_calls", [])
                            
                            if tool_calls:
                                # Step 2: 选择工具
                                if enable_enhanced_thought_chain and not tool_selection_sent:
                                    tool_names = [
                                        tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                                        for tc in tool_calls
                                    ]
                                    yield SSEEventFormatter.format_thought(
                                        f"选择工具: {', '.join(tool_names)}",
                                        metadata={"step": "tool_selection", "tools": tool_names}
                                    )
                                    tool_selection_sent = True
                                
                                # 发送工具调用事件
                                for tool_call in tool_calls:
                                    # 安全获取tool_call属性
                                    if isinstance(tool_call, dict):
                                        tool_name = tool_call.get("name", "unknown")
                                        tool_input = tool_call.get("args", {})
                                        tool_call_id = tool_call.get("id", str(uuid.uuid4()))
                                    else:
                                        tool_name = getattr(tool_call, "name", "unknown")
                                        tool_input = getattr(tool_call, "args", {})
                                        tool_call_id = getattr(tool_call, "id", str(uuid.uuid4()))
                                    
                                    yield SSEEventFormatter.format_tool_call(
                                        tool_name=tool_name,
                                        tool_input=tool_input,
                                        tool_call_id=tool_call_id
                                    )
                                    
                                    # Step 3: 执行工具
                                    if enable_enhanced_thought_chain:
                                        yield SSEEventFormatter.format_thought(
                                            f"正在执行工具: {tool_name}",
                                            metadata={"step": "executing", "tool": tool_name}
                                        )
                                    
                                    # 记录思考链
                                    log_thinking(
                                        f"调用工具: {tool_name}",
                                        interface="sse_api",
                                        client_id=client_id,
                                        thread_id=thread_id,
                                        metadata={"tool_call_id": tool_call_id, "tool_input": tool_input}
                                    )
                            
                            # 如果有文本内容，发送消息增量
                            if content and content != current_ai_message:
                                # 计算增量
                                delta = content[len(current_ai_message):]
                                if delta:
                                    yield SSEEventFormatter.format_message_delta(delta)
                                    current_ai_message = content
                        
                        # 处理工具消息
                        elif isinstance(last_message, ToolMessage) or (isinstance(last_message, dict) and last_message.get("type") == "tool"):
                            # 安全获取tool相关属性
                            if isinstance(last_message, dict):
                                tool_output = last_message.get("content", "")
                                tool_call_id = last_message.get("tool_call_id", "")
                            else:
                                tool_output = getattr(last_message, "content", "")
                                tool_call_id = getattr(last_message, "tool_call_id", "")
                            
                            # 发送工具结果事件
                            yield SSEEventFormatter.format_tool_result(
                                tool_name="unknown",  # 工具名称需要从tool_call中获取
                                tool_output=tool_output,
                                tool_call_id=tool_call_id
                            )
                            
                            # Step 4: 分析结果
                            if enable_enhanced_thought_chain:
                                yield SSEEventFormatter.format_thought(
                                    f"正在分析工具输出...",
                                    metadata={"step": "analyzing"}
                                )
                            
                            # 记录工具调用结果
                            log_tool_operation(
                                tool_name="unknown",
                                tool_input={},
                                tool_output=tool_output,
                                success=True,
                                interface="sse_api",
                                client_id=client_id,
                                thread_id=thread_id,
                                metadata={"tool_call_id": tool_call_id}
                            )
                
                # 检查是否有思考过程（如果LangGraph配置了中间步骤）
                if "__intermediate_steps__" in chunk:
                    steps = chunk["__intermediate_steps__"]
                    for step in steps:
                        if isinstance(step, tuple) and len(step) >= 2:
                            action, observation = step[0], step[1]
                            # 发送思考事件
                            yield SSEEventFormatter.format_thought(
                                f"执行动作: {action}",
                                metadata={"observation": str(observation)[:200]}
                            )
        
        # Step 5: 综合信息
        if enable_enhanced_thought_chain and current_ai_message:
            yield SSEEventFormatter.format_thought(
                "正在综合信息生成回复...",
                metadata={"step": "synthesizing"}
            )
        
        # 发送最终完整消息
        if current_ai_message:
            yield SSEEventFormatter.format_message_complete(current_ai_message)
            
            # 记录对话
            log_dialogue(
                role="assistant",
                message=current_ai_message,
                source="agent",
                interface="sse_api",
                client_id=client_id,
                thread_id=thread_id
            )
        
        # Step 6: 完成任务
        if enable_enhanced_thought_chain:
            yield SSEEventFormatter.format_thought(
                "任务完成",
                metadata={"step": "completed"}
            )
        
        # 发送系统日志：完成处理
        yield SSEEventFormatter.format_system_log(
            "info",
            f"请求处理完成 (thread_id={thread_id})",
            metadata={"thread_id": thread_id, "client_id": client_id}
        )
        
        # 发送结束标记
        yield "event: done\ndata: {\"status\": \"completed\"}\n\n"
        
        logger.info(f"Stream completed for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        # 发送错误事件
        yield SSEEventFormatter.format_system_log(
            "error",
            f"处理请求时发生错误: {str(e)}",
            metadata={"thread_id": thread_id, "error": str(e)}
        )
        yield "event: error\ndata: {\"error\": \"" + str(e).replace('"', '\\"') + "\"}\n\n"


async def stream_agent_response(
    app_graph,
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    thread_id: str,
    client_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    流式执行Agent并生成SSE事件流
    
    Args:
        app_graph: LangGraph应用图
        input_data: 输入数据
        config: 配置
        thread_id: 线程ID
        client_id: 客户端ID
        
    Yields:
        str: SSE事件字符串
    """
    try:
        # 发送系统日志：开始处理
        yield SSEEventFormatter.format_system_log(
            "info",
            f"开始处理请求 (thread_id={thread_id})",
            metadata={"thread_id": thread_id, "client_id": client_id}
        )
        
        # 记录到D5记忆航母
        log_system_event(
            f"开始处理请求 (thread_id={thread_id})",
            level="info",
            interface="sse_api",
            client_id=client_id,
            thread_id=thread_id
        )
        
        # 用于累积AI消息内容
        current_ai_message = ""
        
        # 流式执行Agent
        async for chunk in app_graph.astream(input_data, config=config):
            logger.debug(f"Stream chunk: {chunk}")
            
            # 处理不同类型的chunk
            if isinstance(chunk, dict):
                # 检查是否有messages
                if "messages" in chunk:
                    messages = chunk["messages"]
                    if messages and len(messages) > 0:
                        last_message = messages[-1]
                        
                        # 处理AI消息
                        if isinstance(last_message, AIMessage) or (isinstance(last_message, dict) and last_message.get("type") == "ai"):
                            # 安全获取content
                            if isinstance(last_message, dict):
                                content = last_message.get("content", "")
                                tool_calls = last_message.get("tool_calls", [])
                            else:
                                content = getattr(last_message, "content", "")
                                tool_calls = getattr(last_message, "tool_calls", [])
                            
                            if tool_calls:
                                # 发送工具调用事件
                                for tool_call in tool_calls:
                                    # 安全获取tool_call属性
                                    if isinstance(tool_call, dict):
                                        tool_name = tool_call.get("name", "unknown")
                                        tool_input = tool_call.get("args", {})
                                        tool_call_id = tool_call.get("id", str(uuid.uuid4()))
                                    else:
                                        tool_name = getattr(tool_call, "name", "unknown")
                                        tool_input = getattr(tool_call, "args", {})
                                        tool_call_id = getattr(tool_call, "id", str(uuid.uuid4()))
                                    
                                    yield SSEEventFormatter.format_tool_call(
                                        tool_name=tool_name,
                                        tool_input=tool_input,
                                        tool_call_id=tool_call_id
                                    )
                                    
                                    # 记录思考链
                                    log_thinking(
                                        f"调用工具: {tool_name}",
                                        interface="sse_api",
                                        client_id=client_id,
                                        thread_id=thread_id,
                                        metadata={"tool_call_id": tool_call_id, "tool_input": tool_input}
                                    )
                            
                            # 如果有文本内容，发送消息增量
                            if content and content != current_ai_message:
                                # 计算增量
                                delta = content[len(current_ai_message):]
                                if delta:
                                    yield SSEEventFormatter.format_message_delta(delta)
                                    current_ai_message = content
                        
                        # 处理工具消息
                        elif isinstance(last_message, ToolMessage) or (isinstance(last_message, dict) and last_message.get("type") == "tool"):
                            # 安全获取tool相关属性
                            if isinstance(last_message, dict):
                                tool_output = last_message.get("content", "")
                                tool_call_id = last_message.get("tool_call_id", "")
                            else:
                                tool_output = getattr(last_message, "content", "")
                                tool_call_id = getattr(last_message, "tool_call_id", "")
                            
                            # 发送工具结果事件
                            yield SSEEventFormatter.format_tool_result(
                                tool_name="unknown",  # 工具名称需要从tool_call中获取
                                tool_output=tool_output,
                                tool_call_id=tool_call_id
                            )
                            
                            # 记录工具调用结果
                            log_tool_operation(
                                tool_name="unknown",
                                tool_input={},
                                tool_output=tool_output,
                                success=True,
                                interface="sse_api",
                                client_id=client_id,
                                thread_id=thread_id,
                                metadata={"tool_call_id": tool_call_id}
                            )
                
                # 检查是否有思考过程（如果LangGraph配置了中间步骤）
                if "__intermediate_steps__" in chunk:
                    steps = chunk["__intermediate_steps__"]
                    for step in steps:
                        if isinstance(step, tuple) and len(step) >= 2:
                            action, observation = step[0], step[1]
                            # 发送思考事件
                            yield SSEEventFormatter.format_thought(
                                f"执行动作: {action}",
                                metadata={"observation": str(observation)[:200]}
                            )
        
        # 发送最终完整消息
        if current_ai_message:
            yield SSEEventFormatter.format_message_complete(current_ai_message)
            
            # 记录对话
            log_dialogue(
                role="assistant",
                message=current_ai_message,
                source="agent",
                interface="sse_api",
                client_id=client_id,
                thread_id=thread_id
            )
        
        # 发送系统日志：完成处理
        yield SSEEventFormatter.format_system_log(
            "info",
            f"请求处理完成 (thread_id={thread_id})",
            metadata={"thread_id": thread_id, "client_id": client_id}
        )
        
        # 发送结束标记
        yield "event: done\ndata: {\"status\": \"completed\"}\n\n"
        
        logger.info(f"Stream completed for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        # 发送错误事件
        yield SSEEventFormatter.format_system_log(
            "error",
            f"处理请求时发生错误: {str(e)}",
            metadata={"thread_id": thread_id, "error": str(e)}
        )
        yield "event: error\ndata: {\"error\": \"" + str(e).replace('"', '\\"') + "\"}\n\n"


# ============================================
# v5.8: FastAPI Router for Streaming API
# ============================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["streaming"])


class StreamChatRequest(BaseModel):
    """SSE流式聊天请求"""
    message: str = Field(..., description="用户消息")
    thread_id: Optional[str] = Field(None, description="会话ID")
    source: Optional[str] = Field("user", description="消息来源（user/api/assistant）")
    enable_thought_chain: bool = Field(True, description="是否启用增强版思维链")
    enable_tool_chain: bool = Field(True, description="是否启用工具链")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


@router.post("/chat/stream")
async def stream_chat(request: StreamChatRequest):
    """
    v5.8: SSE流式聊天端点（增强版思维链 + 工具链）
    
    功能：
    - 实时推送Agent推理过程（6步思维链）
    - 实时推送工具调用链路
    - 可视化展示思维链
    
    SSE事件类型：
    - thought: 思维链事件（understanding/tool_selection/executing/analyzing/synthesizing/completed）
    - tool: 工具调用/结果事件
    - message: 消息事件（delta/complete）
    - system: 系统日志事件
    - done: 完成事件
    
    示例：
    ```bash
    curl -N -X POST http://localhost:8888/api/chat/stream \
      -H "Content-Type: application/json" \
      -d '{"message": "帮我搜索今天的新闻", "thread_id": "test-123"}'
    ```
    """
    try:
        # 导入全局变量
        from main import app_graph
        
        # 生成thread_id（如果未提供）
        thread_id = request.thread_id or f"thread-{datetime.now().timestamp()}"
        
        logger.info(f"Starting SSE stream for thread: {thread_id}")
        
        # 准备输入
        input_data = {
            "messages": [HumanMessage(content=request.message)]
        }
        config = {"configurable": {"thread_id": thread_id}}
        
        # 返回SSE流
        return StreamingResponse(
            stream_agent_response_with_enhanced_thought_chain(
                app_graph=app_graph,
                input_data=input_data,
                config=config,
                thread_id=thread_id,
                client_id=request.metadata.get("client_id") if request.metadata else None,
                enable_enhanced_thought_chain=request.enable_thought_chain
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用nginx缓冲
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream_chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# 导出路由
__all__ = ['router', 'SSEEventFormatter', 'stream_agent_response', 'stream_agent_response_with_enhanced_thought_chain']
