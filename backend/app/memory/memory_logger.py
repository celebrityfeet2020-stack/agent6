"""
Memory Logger Module for Agent System v3.6
提供便捷的记忆记录函数
"""

from typing import Optional, Dict, Any
from app.memory.memory_sync import add_memory


def log_dialogue(
    role: str,
    message: str,
    source: str = "user",
    interface: str = "http_api",
    client_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    记录对话
    
    Args:
        role: 角色 (user/assistant/system)
        message: 消息内容
        source: 消息来源 (user/api/agent)
        interface: 接口类型 (http_api/sse_api/websocket)
        client_id: 客户端ID
        thread_id: 线程ID
        metadata: 额外元数据
    """
    content = f"[{role}] {message}"
    add_memory(
        memory_type="dialogue",
        content=content,
        metadata=metadata,
        source=source,
        interface=interface,
        client_id=client_id,
        thread_id=thread_id
    )


def log_thinking(
    thought: str,
    interface: str = "sse_api",
    client_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    记录思考链
    
    Args:
        thought: 思考内容
        interface: 接口类型
        client_id: 客户端ID
        thread_id: 线程ID
        metadata: 额外元数据
    """
    add_memory(
        memory_type="thinking_chain",
        content=thought,
        metadata=metadata,
        source="agent",
        interface=interface,
        client_id=client_id,
        thread_id=thread_id
    )


def log_tool_operation(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: str,
    success: bool = True,
    interface: str = "http_api",
    client_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    记录工具调用
    
    Args:
        tool_name: 工具名称
        tool_input: 工具输入
        tool_output: 工具输出
        success: 是否成功
        interface: 接口类型
        client_id: 客户端ID
        thread_id: 线程ID
        metadata: 额外元数据
    """
    content = f"Tool: {tool_name}\nInput: {tool_input}\nOutput: {tool_output}\nSuccess: {success}"
    
    enhanced_metadata = metadata.copy() if metadata else {}
    enhanced_metadata.update({
        "tool_name": tool_name,
        "tool_input": tool_input,
        "success": success
    })
    
    add_memory(
        memory_type="operation_log",
        content=content,
        metadata=enhanced_metadata,
        source="agent",
        interface=interface,
        client_id=client_id,
        thread_id=thread_id
    )


def log_system_event(
    event: str,
    level: str = "info",
    interface: str = "http_api",
    client_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    记录系统日志
    
    Args:
        event: 事件描述
        level: 日志级别 (info/warning/error)
        interface: 接口类型
        client_id: 客户端ID
        thread_id: 线程ID
        metadata: 额外元数据
    """
    content = f"[{level.upper()}] {event}"
    
    enhanced_metadata = metadata.copy() if metadata else {}
    enhanced_metadata.update({
        "level": level
    })
    
    add_memory(
        memory_type="system_log",
        content=content,
        metadata=enhanced_metadata,
        source="system",
        interface=interface,
        client_id=client_id,
        thread_id=thread_id
    )
