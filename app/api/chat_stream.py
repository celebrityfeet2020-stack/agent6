"""
M3 Agent v6.0 - Chat Stream API
支持SSE流式输出、思维链、工具调用可视化
支持三方可见 (用户/API/Admin)
"""

import json
import uuid
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)


class StreamChatRequest(BaseModel):
    """流式聊天请求"""
    message: str
    thread_id: Optional[str] = "default_session"  # 默认共享会话
    source: Optional[str] = "user"  # user/api/admin/livestream/fleet
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据


class SSEFormatter:
    """SSE事件格式化器"""
    
    @staticmethod
    def format_event(event_type: str, data: Dict[str, Any]) -> str:
        """格式化SSE事件"""
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
        """格式化思考事件"""
        return SSEFormatter.format_event("thought", {
            "content": content,
            "metadata": metadata or {}
        })
    
    @staticmethod
    def format_tool_call(tool_name: str, tool_input: Dict, tool_call_id: str) -> str:
        """格式化工具调用事件"""
        return SSEFormatter.format_event("tool", {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_call_id": tool_call_id,
            "status": "calling"
        })
    
    @staticmethod
    def format_tool_result(tool_name: str, tool_output: str, tool_call_id: str, success: bool = True) -> str:
        """格式化工具结果事件"""
        return SSEFormatter.format_event("tool", {
            "tool_name": tool_name,
            "tool_output": tool_output,
            "tool_call_id": tool_call_id,
            "status": "success" if success else "error"
        })
    
    @staticmethod
    def format_message_delta(content: str, role: str = "assistant", source: str = "agent", metadata: Optional[Dict] = None) -> str:
        """格式化消息增量事件（打字机效果）"""
        return SSEFormatter.format_event("message", {
            "role": role,
            "content": content,
            "delta": True,
            "source": source,
            "metadata": metadata or {}
        })
    
    @staticmethod
    def format_message_complete(content: str, role: str = "assistant", source: str = "agent", metadata: Optional[Dict] = None) -> str:
        """格式化消息完成事件"""
        return SSEFormatter.format_event("message", {
            "role": role,
            "content": content,
            "delta": False,
            "complete": True,
            "source": source,
            "metadata": metadata or {}
        })
    
    @staticmethod
    def format_system_log(level: str, message: str, source: str = "agent", metadata: Optional[Dict] = None) -> str:
        """格式化系统日志事件"""
        return SSEFormatter.format_event("system", {
            "level": level,
            "message": message,
            "source": source,
            "metadata": metadata or {}
        })


async def stream_agent_response(
    app_graph,
    message: str,
    thread_id: str,
    source: str = "user",
    metadata: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """
    流式执行Agent并生成SSE事件
    
    Args:
        app_graph: LangGraph编译后的图
        message: 用户消息
        thread_id: 会话ID
        source: 消息来源 (user/api/admin/livestream/fleet)
        metadata: 额外元数据
    
    Yields:
        str: SSE格式的事件字符串
    """
    try:
        # 发送用户消息事件
        yield SSEFormatter.format_message_complete(
            content=message,
            role="user",
            source=source,
            metadata=metadata
        )
        
        # 发送系统日志：开始处理
        yield SSEFormatter.format_system_log(
            "info",
            f"开始处理来自 {source} 的请求",
            metadata={"thread_id": thread_id, "source": source}
        )
        
        # 构建输入
        input_data = {
            "messages": [HumanMessage(content=message)]
        }
        
        # 配置
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # 用于累积AI消息内容
        current_ai_message = ""
        tool_call_map = {}  # 用于跟踪工具调用
        
        # 流式执行Agent
        async for chunk in app_graph.astream(input_data, config=config):
            logger.debug(f"Stream chunk: {chunk}")
            
            # 处理不同类型的chunk
            if isinstance(chunk, dict):
                # 检查是否有agent节点的输出
                if "agent" in chunk:
                    agent_output = chunk["agent"]
                    if "messages" in agent_output:
                        messages = agent_output["messages"]
                        if messages and len(messages) > 0:
                            last_message = messages[-1]
                            
                            # 处理AI消息
                            if isinstance(last_message, AIMessage):
                                content = getattr(last_message, "content", "")
                                tool_calls = getattr(last_message, "tool_calls", [])
                                
                                # 处理工具调用
                                if tool_calls:
                                    yield SSEFormatter.format_thought(
                                        f"正在调用 {len(tool_calls)} 个工具...",
                                        metadata={"step": "tool_selection", "count": len(tool_calls)}
                                    )
                                    
                                    for tool_call in tool_calls:
                                        tool_name = getattr(tool_call, "name", "unknown")
                                        tool_input = getattr(tool_call, "args", {})
                                        tool_call_id = getattr(tool_call, "id", str(uuid.uuid4()))
                                        
                                        # 保存工具调用信息
                                        tool_call_map[tool_call_id] = tool_name
                                        
                                        # 发送工具调用事件
                                        yield SSEFormatter.format_tool_call(
                                            tool_name=tool_name,
                                            tool_input=tool_input,
                                            tool_call_id=tool_call_id
                                        )
                                        
                                        yield SSEFormatter.format_thought(
                                            f"正在执行工具: {tool_name}",
                                            metadata={"step": "executing", "tool": tool_name}
                                        )
                                
                                # 处理文本内容
                                if content and content != current_ai_message:
                                    # 计算增量
                                    delta = content[len(current_ai_message):]
                                    if delta:
                                        yield SSEFormatter.format_message_delta(
                                            delta,
                                            source="agent"
                                        )
                                        current_ai_message = content
                
                # 检查是否有tools节点的输出
                if "tools" in chunk:
                    tools_output = chunk["tools"]
                    if "messages" in tools_output:
                        messages = tools_output["messages"]
                        for message in messages:
                            if isinstance(message, ToolMessage):
                                tool_output = getattr(message, "content", "")
                                tool_call_id = getattr(message, "tool_call_id", "")
                                tool_name = tool_call_map.get(tool_call_id, "unknown")
                                
                                # 发送工具结果事件
                                yield SSEFormatter.format_tool_result(
                                    tool_name=tool_name,
                                    tool_output=tool_output,
                                    tool_call_id=tool_call_id
                                )
                                
                                yield SSEFormatter.format_thought(
                                    f"工具 {tool_name} 执行完成",
                                    metadata={"step": "analyzing", "tool": tool_name}
                                )
        
        # 发送完成消息
        if current_ai_message:
            yield SSEFormatter.format_message_complete(
                content=current_ai_message,
                source="agent"
            )
        
        # 发送系统日志：完成处理
        yield SSEFormatter.format_system_log(
            "info",
            "请求处理完成",
            metadata={"thread_id": thread_id}
        )
    
    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}", exc_info=True)
        yield SSEFormatter.format_system_log(
            "error",
            f"处理请求时发生错误: {str(e)}",
            metadata={"thread_id": thread_id, "error": str(e)}
        )
