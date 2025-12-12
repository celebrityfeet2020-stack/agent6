"""
多维聊天室API (Multidimensional Chatroom API)
支持任意角色类型的多维对话系统
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio
from langchain_core.messages import HumanMessage

from app.state import state_manager
from app.config import MAX_CONTEXT_LENGTH, COMPRESSION_TRIGGER_TOKENS

router = APIRouter()


class RoleInfo(BaseModel):
    """角色信息 - 支持任意字符串作为角色类型"""
    type: str = Field(..., description="角色类型，可以是任意字符串，如: user, admin, n8_workflow, digital_human_guest, git_committer等")
    id: str = Field(..., description="角色唯一ID")
    name: str = Field(..., description="显示名称")
    weight: float = Field(default=1.0, ge=0.1, le=10.0, description="权重（0.1-10.0），影响响应优先级")
    permissions: List[str] = Field(default=["chat"], description="权限列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class MultidimensionalChatRequest(BaseModel):
    """多维聊天请求"""
    message: str = Field(..., description="用户消息")
    thread_id: Optional[str] = Field(default="default_session", description="会话ID")
    role: RoleInfo = Field(
        default=RoleInfo(type="user", id="anonymous", name="匿名用户"),
        description="角色信息"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息（房间ID、平台来源等）")
    enable_thought_chain: bool = Field(default=True, description="是否启用思维链")
    enable_tool_chain: bool = Field(default=True, description="是否启用工具链")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


@router.post("/api/multidimensional/chat/stream")
async def multidimensional_chat_stream(request: MultidimensionalChatRequest):
    """
    多维聊天室SSE流式端点
    
    支持：
    - 任意角色类型（user/admin/n8_workflow/digital_human_guest等）
    - 权重系统（0.1-10.0）
    - 权限控制
    - 上下文信息
    - 统一消息推送到多维聊天室
    """
    async def event_generator():
        try:
            # 从全局状态获取app_graph
            app_graph = state_manager.get_app_graph()
            
            if not app_graph:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Agent未初始化,请等待启动完成'})}\n\n"
                return
            
            # 权限检查
            if not _check_permissions(request.role, request.message):
                yield f"data: {json.dumps({'type': 'error', 'message': f'角色 {request.role.type} 无权执行此操作'})}\n\n"
                return
            
            # 发送用户消息到统一消息总线
            await unified_messenger.send_user_message(
                content=request.message,
                role_type=request.role.type,
                role_id=request.role.id,
                role_name=request.role.name,
                thread_id=request.thread_id,
                metadata={
                    "weight": request.role.weight,
                    "permissions": request.role.permissions,
                    "context": request.context
                }
            )
            
            # 发送开始事件（包含角色信息）
            start_event = {
                'type': 'start',
                'timestamp': datetime.now().isoformat(),
                'role': request.role.dict(),
                'message': request.message
            }
            yield f"data: {json.dumps(start_event)}\n\n"
            
            # 构造输入（注入角色信息到上下文）
            input_data = {
                "messages": [HumanMessage(content=request.message)],
                "role_info": request.role.dict(),
                "context": request.context or {}
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
                            # 推送到消息总线
                            await unified_messenger.send_user_message(
                                content=last_message.content,
                                role_type="assistant",
                                role_id="agent",
                                role_name="AI助手",
                                thread_id=request.thread_id
                            )
                            
                            msg_event = {
                                'type': 'message',
                                'content': last_message.content,
                                'role': 'assistant'
                            }
                            yield f"data: {json.dumps(msg_event)}\n\n"
                        
                        # 如果有工具调用
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                # 推送到消息总线
                                await unified_messenger.send_tool_call_message(
                                    tool_name=tool_call.get('name'),
                                    tool_args=tool_call.get('args'),
                                    thread_id=request.thread_id
                                )
                                
                                tool_call_event = {
                                    'type': 'tool_call',
                                    'tool': tool_call.get('name'),
                                    'args': tool_call.get('args')
                                }
                                yield f"data: {json.dumps(tool_call_event)}\n\n"
                
                # 如果有工具结果
                if "tools" in event:
                    messages = event["tools"].get("messages", [])
                    if messages:
                        for msg in messages:
                            if hasattr(msg, "content"):
                                # 推送到消息总线
                                tool_name = getattr(msg, 'name', 'unknown_tool')
                                await unified_messenger.send_tool_result_message(
                                    tool_name=tool_name,
                                    result=str(msg.content),
                                    thread_id=request.thread_id
                                )
                                
                                tool_result_event = {
                                    'type': 'tool_result',
                                    'content': str(msg.content)[:500]
                                }
                                yield f"data: {json.dumps(tool_result_event)}\n\n"
                
                # 短暂延迟,避免过快
                await asyncio.sleep(0.01)
            
            # 发送结束事件
            end_event = {
                'type': 'end',
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(end_event)}\n\n"
            
        except Exception as e:
            error_msg = f"多维聊天处理错误: {str(e)}"
            print(f"ERROR: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/api/multidimensional/chat/health")
async def multidimensional_chat_health():
    """健康检查"""
    return {
        "status": "healthy",
        "tools_loaded": state_manager.tool_pool_loaded,
        "app_graph_loaded": state_manager.app_graph is not None,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/multidimensional/chat/context_stats")
async def get_multidimensional_context_stats():
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


def _check_permissions(role: RoleInfo, message: str) -> bool:
    """
    检查权限
    
    示例：检查是否有权限执行危险操作
    可根据实际需求扩展
    """
    # 危险关键词列表
    dangerous_keywords = ["删除系统", "重启服务器", "关闭系统", "rm -rf"]
    
    # 如果消息包含危险关键词，检查权限
    if any(kw in message for kw in dangerous_keywords):
        return "dangerous_operations" in role.permissions or role.type == "admin"
    
    # 默认允许
    return True


def _build_role_aware_prompt(role: RoleInfo, context: Optional[Dict]) -> str:
    """
    构建角色感知的元提示词
    
    这个函数可以在未来用于动态调整Agent的响应策略
    """
    prompt = f"""
# 当前对话角色信息

**角色类型**: {role.type}
**角色名称**: {role.name}
**角色权重**: {role.weight}
**权限列表**: {', '.join(role.permissions)}

## 响应策略

"""
    
    # 根据权重调整响应策略
    if role.weight >= 5.0:
        prompt += "- 提供详细、深入的回答（VIP/管理员）\n"
        prompt += "- 可以使用高级工具\n"
        prompt += "- 优先处理请求\n"
    elif 1.0 <= role.weight < 5.0:
        prompt += "- 提供标准回答（普通用户）\n"
        prompt += "- 使用基础工具\n"
        prompt += "- 正常优先级\n"
    else:
        prompt += "- 提供简洁回答（低优先级用户）\n"
        prompt += "- 限制工具使用\n"
        prompt += "- 低优先级处理\n"
    
    # 添加上下文信息
    if context:
        prompt += f"\n## 当前上下文\n{json.dumps(context, ensure_ascii=False, indent=2)}\n"
    
    return prompt
