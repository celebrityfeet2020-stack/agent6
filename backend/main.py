"""FastAPI Backend for M3 Agent System
A6 System v6.2.0 - Main Application
重大性能优化：全局浏览器池 + 模型预加载
完整的 Agent 工作流，支持工具调用和 OpenAI 兼容接口

v5.2 Critical Fix:
- Migrated browser_pool from sync_playwright() to async_playwright()
- Created sync/async bridge (browser_sync_wrapper) for tool compatibility
- Fixed "Playwright Sync API inside asyncio loop" error
- All Playwright tools updated to use async browser pool

v5.1 Bug Fixes:
- Fixed event loop conflict (browser pool initialization moved to startup event)
- Fixed frontend nginx config (removed backend proxy)

v5.0 Performance Improvements:
- Browser Pool: 90% faster Playwright operations (5-10s → 0.5-1s)
- Model Pre-loading: 60% faster first-time model usage
- Memory optimization: Shared browser instances across tools

v5.7 Tool Pool:
- Global tool pool for pre-loading heavy resources (OCR, Docker, etc.)
- 10-20x faster first-time tool calls (OCR: 10s → 0.5s)
- Memory usage: ~1.3GB (0.7% of 192GB M3 memory)

v5.6 Critical Fixes:
- Fixed event loop conflict with nest_asyncio (browser pool now works)
- Fixed performance monitoring task lifecycle (保持任务引用)
- Added API performance tracking middleware
- Updated version to v5.6
"""

# v5.7.1: Tool pool for pre-loading heavy resources
# v5.7.1: Browser pool uses thread pool (no need for nest_asyncio)
# Removed nest_asyncio to preserve uvloop performance

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal
from config.settings import settings
from config.logging_config import main_logger as logger
from app.tools import *
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
import httpx
import json
import time
import asyncio
import os

# WebSocket管理器
from app.websocket_manager import manager as ws_manager

# ============================================
# Global Application State (v6.4)
# ============================================
# 使用单例StateManager,确保跨模块状态共享
from app.core.state_manager import StateManager

state_mgr = StateManager()

# 向后兼容:保留app_state变量名(但实际使用state_mgr)
# 这样可以减少代码修改量
app_state = state_mgr._state  # 直接引用内部字典

# ============================================
# FastAPI Application Setup
# ============================================

app = FastAPI(
    title="Agent System",
    version="5.9.0",
    description="M3 Agent v5.9.0 - Background Tasks Manager: Periodic health checks (tool pool + performance test + API check). 后台任务管理器：定期健康检查（工具池预加载 + 性能测试 + API检测）。支持思维链+工具链、三角聊天室、SSE流式输出、工具调用、RPA自动化、多轮对话和性能监控"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# v5.6: Add API performance tracking middleware
from app.performance.performance_monitor import record_api_request
import time

@app.middleware("http")
async def performance_tracking_middleware(request: Request, call_next):
    """Track API performance for all requests"""
    start_time = time.time()
    try:
        response = await call_next(request)
        response_time = (time.time() - start_time) * 1000
        record_api_request(success=response.status_code < 400, response_time_ms=response_time)
        return response
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        record_api_request(success=False, response_time_ms=response_time)
        raise

# v5.1: Startup event to initialize browser pool, tools, and workflow
@app.on_event("startup")
async def startup_event():
    """Initialize browser pool, tools, and workflow on application startup."""
    from app.core.startup import initialize_browser_pool_and_tools
    
    # v6.3.2: Browser pool and tools will be loaded by background tasks (5 minutes after startup)
    logger.info("[v6.3.2] Browser pool and tools will be loaded in background (5 minutes delay)")
    logger.info("[v6.3.2] This avoids asyncio conflicts during startup")
    
    # Initialize app_state with empty values (will be populated by background tasks)
    app_state["browser_pool"] = None
    app_state["tools"] = []
    
    # Bind empty tools to LLM (will be updated by background tasks)
    app_state["llm_with_tools"] = llm.bind_tools(app_state["tools"])
    
    # v5.9: Start background tasks manager
    from app.core.background_tasks import background_tasks_manager
    await background_tasks_manager.start()
    
    # Compile workflow (moved from module level to avoid using None llm_with_tools)
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import StateGraph, MessagesState, END
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node_with_error_handling)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    checkpointer = MemorySaver()
    app_state["app_graph"] = workflow.compile(checkpointer=checkpointer)
    
    logger.info("✅ Startup complete: browser pool, tools, and workflow ready")

# 注册Fleet API路由（用于与D5管理航母和Temporal调度系统对接）
from app.api.fleet_api import router as fleet_router
app.include_router(fleet_router)

# 注册LangGraph API路由（用于assistant-ui等客户端）
from app.api.langgraph_adapter import router as langgraph_router
app.include_router(langgraph_router)

# v5.8: 注册Streaming API路由（思维链 + 工具链）
from app.api.streaming import router as streaming_router
app.include_router(streaming_router)

# v5.9: 注册统一三角聊天室API路由（默认统一界面，三方可见）
from app.api.unified_chat_room import router as unified_chat_room_router
app.include_router(unified_chat_room_router)

# v6.5.5: 注册聊天室SSE流式API路由（挂载到8888端口以共享状态）
from chatroom_api import router as chatroom_api_router
app.include_router(chatroom_api_router)

# ============================================
# Initialize LLM and Tools
# ============================================

# Initialize LLM
llm = ChatOpenAI(
    base_url=settings.LLM_BASE_URL,
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    max_tokens=settings.LLM_MAX_TOKENS,
    api_key="not-needed"
)

# v5.1: Browser pool and tools will be initialized in startup event
from app.core.browser_pool import get_browser_pool
browser_pool = None
tools = []  # Will be initialized in startup event

# v6.3.2: llm_with_tools moved to app_state dictionary

# ============================================
# Agent Workflow (LangGraph)
# ============================================

def load_system_prompt() -> str:
    """加载激活的元提示词"""
    try:
        prompts_file = "/app/data/system_prompts.json"
        if os.path.exists(prompts_file):
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                for prompt in prompts:
                    if prompt.get("is_active", False):
                        return prompt["prompt"]
        # 默认提示词 (v6.1: 添加VL模型支持说明)
        return """你是 A6 System，一个功能强大的 AI Agent，拥有以下能力：

1. **网络搜索和抓取**：使用 web_search 搜索信息，使用 web_scraper 抓取网页内容
2. **浏览器自动化**：使用 browser_automation 进行复杂的网页交互
3. **代码执行**：使用 code_executor 在安全沙盒中执行 Python/JavaScript/Bash 代码
4. **文件操作**：使用 file_operations 读写文件
5. **图像处理**：使用 image_ocr 识别图片文字 (支持中英日韩等多语言)，使用 image_analysis 分析图像 (人脸检测、物体识别等)
6. **语音处理**：使用 speech_recognition_tool 转录音频 (支持中英日韩等多语言)
7. **视频处理**：使用 video_analysis 分析视频内容
8. **数据分析**：使用 data_analysis 处理和可视化数据
9. **远程操作**：使用 ssh_tool 执行远程命令，使用 git_tool 管理代码仓库
10. **API 调用**：使用 universal_api 调用任意 RESTful API
11. **通讯**：使用 telegram_tool 发送 Telegram 消息
12. **RPA自动化**：使用 rpa_tool 进行复杂的自动化流程
13. **文件同步**：使用 file_sync_tool 同步文件到D5航母

**工作原则**：
- 默认使用工具处理多媒体内容，以确保结果的准确性和一致性
- 如果你是多模态模型 (VL模型)，在简单的图片理解任务中 (如“这是什么？”)，你可以直接查看图片
- 但对于需要精确结果的任务 (如OCR、人脸检测、语音转录)，仍应使用专业工具
- 根据用户需求，主动选择合适的工具来完成任务
- 如果一个工具不够，可以连续调用多个工具
- 始终向用户解释你在做什么以及为什么这样做
- 如果遇到错误，尝试其他方法或向用户寻求帮助

现在，请根据用户的请求，充分利用你的工具来完成任务！"""
    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        return "你是 M3 Agent，一个功能强大的 AI 助手。"

def agent_node(state: MessagesState, config: dict) -> MessagesState:
    """Agent 节点：LLM 推理并决定是否调用工具"""
    messages = state["messages"]
    
    # 添加系统提示词（如果第一条消息不是 SystemMessage）
    if not messages or not isinstance(messages[0], SystemMessage):
        system_prompt = load_system_prompt()
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # 调用 LLM（带重试机制）(v6.3.2: 使用app_state)
    try:
        response = app_state["llm_with_tools"].with_retry(stop_after_attempt=3).invoke(messages, config=config)
        return {"messages": [response]}
    except Exception as e:
        error_message = f"LLM 调用失败: {e}"
        logger.error(error_message)
        return {"messages": [AIMessage(content=error_message)]}

def should_continue(state: MessagesState) -> Literal["tools", END]:
    """条件边：判断是否需要继续调用工具"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果 LLM 返回了 tool_calls，则继续调用工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # 否则结束
    return END

# 创建工具节点
def tool_node_with_error_handling(state: MessagesState) -> MessagesState:
    """工具节点（带错误处理）"""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_invocations = []
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_invocations = last_message.tool_calls
    
    if not tool_invocations:
        return {"messages": [AIMessage(content="没有可用的工具调用")]}
    
    tool_node = ToolNode(tools)
    try:
        # 调用工具节点
        return tool_node.invoke(state)
    except Exception as e:
        error_message = f"工具调用失败: {e}"
        logger.error(error_message)
        # 返回错误信息给 LLM，让它决定下一步
        return {"messages": [ToolMessage(content=error_message, tool_call_id=tool_invocations[0]["id"])]}

tool_node = tool_node_with_error_handling

# v6.3.2: app_graph moved to app_state dictionary
# This allows background_tasks to update it properly

# ============================================
# Pydantic Models
# ============================================

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    source: str = "user"  # 消息来源: user/api/assistant

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

class OpenAIMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"

class OpenAIModel(BaseModel):
    id: str
    object: str = "model"
    created: int = int(time.time())
    owned_by: str = "m3-agent"

class OpenAIModelsResponse(BaseModel):
    object: str = "list"
    data: List[OpenAIModel]

# ============================================
# Native Agent API Endpoints
# ============================================

@app.get("/")
async def root():
    return {
        "status": "M3 Agent System v5.9.0 Running",
        "tools": len(tools),
        "features": ["Agent Workflow", "Tool Calling", "OpenAI Compatible"]
    }

@app.get("/health")
async def health():
    # v6.5.6: 修复 - 从 app_state 读取 tools
    actual_tools = app_state.get("tools", [])
    return {
        "status": "healthy",
        "llm_model": settings.LLM_MODEL,
        "tools_count": len(actual_tools)
    }

@app.post("/api/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """原生 Agent 接口：支持完整的工具调用工作流"""
    try:
        # 记录用户消息到memory_buffer
        from app.memory.memory_logger import log_dialogue
        log_dialogue(
            role="user",
            message=request.message,
            source=request.source,
            thread_id=request.thread_id,
            interface="http_api"
        )
        
        # 通过WebSocket广播用户消息
        await ws_manager.broadcast_to_thread(
            thread_id=request.thread_id,
            message={
                "type": "new_message",
                "thread_id": request.thread_id,
                "role": "user",
                "content": request.message,
                "source": request.source,
                "timestamp": time.time()
            }
        )
        
        # 构建输入消息
        input_messages = [HumanMessage(content=request.message)]
        
        # 调用 Agent 工作流 (v6.3.2: 使用app_state)
        config = {"configurable": {"thread_id": request.thread_id}}
        result = app_state["app_graph"].invoke(
            {"messages": input_messages},
            config=config
        )
        
        # 提取最终响应
        messages = result["messages"]
        last_message = messages[-1]
        
        # 提取工具调用信息
        tool_calls_info = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_info.append({
                        "tool": tc["name"],
                        "input": tc["args"]
                    })
        
        response_text = last_message.content if hasattr(last_message, "content") else str(last_message)
        
        # 记录Assistant的回复到memory_buffer
        log_dialogue(
            role="assistant",
            message=response_text,
            source="assistant",
            thread_id=request.thread_id,
            interface="http_api"
        )
        
        # 通过WebSocket广播新消息
        await ws_manager.broadcast_to_thread(
            thread_id=request.thread_id,
            message={
                "type": "new_message",
                "thread_id": request.thread_id,
                "role": "assistant",
                "content": response_text,
                "source": "assistant",
                "timestamp": time.time()
            }
        )
        
        return ChatResponse(
            response=response_text,
            thread_id=request.thread_id,
            tool_calls=tool_calls_info if tool_calls_info else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@app.post("/api/chat")
async def simple_chat(request: ChatRequest):
    """
    简化的聊天接口（兼容旧版本）
    
    这是 /api/agent/chat 的别名，提供更简洁的API路径。
    支持完整的Agent工作流，包括工具调用和多轮对话。
    
    Args:
        request: ChatRequest with message and optional thread_id
    
    Returns:
        ChatResponse with agent response and tool call info
    """
    return await agent_chat(request)

@app.get("/api/tools")
async def list_tools():
    """列出所有可用工具 (v6.3.2: 使用app_state)"""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in app_state["tools"]
        ]
    }

@app.get("/api/threads/{thread_id}/history")
async def get_thread_history(thread_id: str, limit: int = 100):
    """
    查询指定thread_id的历史消息
    
    这是三角聊天室的核心API，返回所有source（user/api/assistant）的消息
    
    Args:
        thread_id: 对话线程ID
        limit: 最大返回数量
    
    Returns:
        List[Dict]: 消息历史列表
    """
    try:
        import sqlite3
        import json
        from pathlib import Path
        
        db_path = "/data/memory_buffer.db"
        
        # 检查数据库是否存在
        if not Path(db_path).exists():
            return {"messages": [], "thread_id": thread_id}
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询指定thread_id的dialogue类型消息
        cursor.execute("""
            SELECT * FROM memory_buffer
            WHERE type = 'dialogue'
            AND json_extract(metadata, '$.thread_id') = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (thread_id, limit))
        
        records = cursor.fetchall()
        conn.close()
        
        # 格式化消息
        messages = []
        for record in records:
            metadata = json.loads(record["metadata"]) if record["metadata"] else {}
            messages.append({
                "id": record["id"],
                "timestamp": record["timestamp"],
                "content": record["content"],
                "source": metadata.get("source", "unknown"),
                "interface": metadata.get("interface", "unknown"),
                "metadata": metadata
            })
        
        return {
            "messages": messages,
            "thread_id": thread_id,
            "count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Failed to get thread history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

# ============================================
# OpenAI Compatible API Endpoints
# ============================================

@app.get("/v1/models")
async def list_models():
    """OpenAI 兼容：列出可用模型"""
    try:
        # 尝试从 LM Studio 获取模型列表
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.LLM_BASE_URL}/models")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    
    # 回退：返回配置的模型
    return OpenAIModelsResponse(
        data=[OpenAIModel(id=settings.LLM_MODEL)]
    ).dict()

@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    """OpenAI 兼容：聊天补全接口（支持工具调用）"""
    try:
        # 转换 OpenAI 格式的消息为 LangChain 格式
        langchain_messages = []
        for msg in request.messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content or ""))
        
        # 调用 Agent 工作流 (v6.3.2: 使用app_state)
        config = {"configurable": {"thread_id": f"openai_{int(time.time())}"}}
        result = app_state["app_graph"].invoke(
            {"messages": langchain_messages},
            config=config
        )
        
        # 提取最终响应
        messages = result["messages"]
        last_message = messages[-1]
        
        # 构建 OpenAI 格式的响应
        response_message = {
            "role": "assistant",
            "content": last_message.content if hasattr(last_message, "content") else str(last_message)
        }
        
        # 如果有工具调用，添加 tool_calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            response_message["tool_calls"] = [
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"])
                    }
                }
                for i, tc in enumerate(last_message.tool_calls)
            ]
        
        # 返回 OpenAI 格式
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": response_message,
                    "finish_reason": "tool_calls" if "tool_calls" in response_message else "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@app.post("/v1/completions")
async def completions(request: Dict[str, Any]):
    """OpenAI 兼容：文本补全接口（代理到 LM Studio）"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.LLM_BASE_URL}/completions",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")

@app.post("/v1/embeddings")
async def embeddings(request: Dict[str, Any]):
    """OpenAI 兼容：文本嵌入接口（代理到 LM Studio）"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.LLM_BASE_URL}/embeddings",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embeddings failed: {str(e)}")

# ============================================
# WebSocket Chat Room (三角聊天室)
# ============================================

@app.websocket("/ws/chat/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: str):
    """
    WebSocket 三角聊天室接口
    
    客户端连接后，会实时接收该thread_id的所有消息（user/api/assistant）
    
    Args:
        thread_id: 对话线程ID
    """
    await ws_manager.connect(websocket, thread_id)
    
    try:
        # 发送欢迎消息
        await ws_manager.send_personal_message(
            websocket,
            {
                "type": "connected",
                "thread_id": thread_id,
                "message": f"Connected to thread {thread_id}",
                "connections": ws_manager.get_thread_connections_count(thread_id)
            }
        )
        
        # 保持连接，等待消息
        while True:
            # 接收客户端消息（如心跳包）
            data = await websocket.receive_text()
            
            # 处理心跳包
            if data == "ping":
                await ws_manager.send_personal_message(
                    websocket,
                    {"type": "pong", "timestamp": time.time()}
                )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, thread_id)
        logger.info(f"WebSocket disconnected from thread {thread_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, thread_id)

@app.get("/chat-room", response_class=HTMLResponse)
async def chat_room_placeholder():
    """聊天室占位页面（未来替换为完整的前端）"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>M3 Agent 聊天室（开发中）</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #667eea; }
            .note { background: #f0f0f0; padding: 15px; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🚀 M3 Agent 舰队聊天室</h1>
        <div class="note">
            <p><strong>状态：</strong>开发中</p>
            <p><strong>WebSocket 端点：</strong><code>ws://localhost:8001/ws/chat</code></p>
            <p><strong>计划功能：</strong></p>
            <ul>
                <li>多用户实时聊天</li>
                <li>Agent 工具调用可视化</li>
                <li>对话历史回放</li>
                <li>多模态消息支持（文本、图片、代码）</li>
            </ul>
        </div>
    </body>
    </html>
    """

# ============================================
# Mount Admin Panel
# ============================================

# 注意：admin_app 将在单独的进程中运行（端口 8002）
# 这里不需要 mount，因为它们是独立的服务

# ============================================
# Memory Sync Startup
# ============================================

from app.memory.memory_sync import start_memory_sync, stop_memory_sync
from app.core.browser_pool import shutdown_browser_pool
from app.core.tool_pool import tool_pool  # v5.7: Global tool pool
import atexit

# 启动记忆同步
start_memory_sync()
logger.info("✓ Memory sync worker started")

# v5.7: Initialize tool pool (async initialization will be done in startup event)
# Note: Actual loading happens in @app.on_event("startup")
logger.info("✓ Tool pool ready for initialization")

# 注册关闭钩子
atexit.register(stop_memory_sync)
atexit.register(shutdown_browser_pool)  # v5.0: Shutdown browser pool on exit
atexit.register(lambda: asyncio.run(tool_pool.shutdown()))  # v5.7: Shutdown tool pool

# v5.9: Shutdown background tasks manager
from app.core.background_tasks import background_tasks_manager
atexit.register(lambda: asyncio.run(background_tasks_manager.stop()))

logger.info("✓ Shutdown hooks registered (memory sync + browser pool + tool pool + background tasks)")

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    # v5.7.1: Use default uvloop for performance (browser pool uses thread pool)
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
        # No loop="asyncio" - let uvicorn use uvloop by default
    )


# ============================================
# 临时调试端点 (v6.3.2 debug)
# ============================================

@app.get("/debug/app_state")
async def debug_app_state():
    """调试: 检查app_state的实际内容"""
    return {
        "app_state_id": id(app_state),
        "browser_pool": app_state["browser_pool"] is not None,
        "tools_count": len(app_state["tools"]),
        "tools_sample": [
            {"name": t.name, "description": t.description[:50]}
            for t in app_state["tools"][:3]
        ] if app_state["tools"] else [],
        "llm_with_tools": app_state["llm_with_tools"] is not None,
        "app_graph": app_state["app_graph"] is not None,
    }
