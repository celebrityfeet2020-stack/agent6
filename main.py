"""
M3 Agent System v2.5 - Main Application
完整的 Agent 工作流，支持工具调用和 OpenAI 兼容接口
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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

# ============================================
# FastAPI Application Setup
# ============================================

app = FastAPI(
    title="M3 Agent System",
    version="3.0.0",
    description="完整的 AI Agent 系统，支持工具调用、RPA自动化和多轮对话"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册Fleet API路由（用于与D5管理航母和Temporal调度系统对接）
from app.api.fleet_api import router as fleet_router
app.include_router(fleet_router)

# 注册LangGraph API路由（用于assistant-ui等客户端）
from app.api.langgraph_adapter import router as langgraph_router
app.include_router(langgraph_router)

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

# Initialize all 15 tools (v2.9)
tools = [
    WebSearchTool(),
    WebScraperTool(),
    CodeExecutorTool(),
    FileOperationsTool(),
    ImageOCRTool(),
    ImageAnalysisTool(),
    SSHTool(),
    GitTool(),
    DataAnalysisTool(),
    BrowserAutomationTool(),
    UniversalAPITool(),
    TelegramTool(),
    SpeechRecognitionTool(),
    RPATool(),           # v2.8新增：跨平台RPA自动化
    FileSyncTool(),      # v2.8新增：容器-宿主机文件同步
]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

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
        # 默认提示词
        return """你是 M3 Agent，一个功能强大的 AI 助手，拥有以下能力：

1. **网络搜索和抓取**：使用 web_search 搜索信息，使用 web_scraper 抓取网页内容
2. **浏览器自动化**：使用 browser_automation 进行复杂的网页交互
3. **代码执行**：使用 code_executor 在安全沙盒中执行 Python/JavaScript/Bash 代码
4. **文件操作**：使用 file_operations 读写文件
5. **图像处理**：使用 image_ocr 识别图片文字，使用 image_analysis 分析图像
6. **数据分析**：使用 data_analysis 处理和可视化数据
7. **远程操作**：使用 ssh_tool 执行远程命令，使用 git_tool 管理代码仓库
8. **API 调用**：使用 universal_api 调用任意 RESTful API
9. **通讯**：使用 telegram_tool 发送 Telegram 消息

**工作原则**：
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
    
    # 调用 LLM（带重试机制）
    try:
        response = llm_with_tools.with_retry(stop_after_attempt=3).invoke(messages, config=config)
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

# 构建 LangGraph 工作流
workflow = StateGraph(MessagesState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node_with_error_handling)

# 设置入口点
workflow.set_entry_point("agent")

# 添加条件边
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# 工具执行后，回到 agent 节点
workflow.add_edge("tools", "agent")

# 配置内存持久化（使用 MemorySaver）
# v2.5: 已移除PostgreSQL依赖，使用内存checkpointer
# 未来将通过 D5 记忆航母实现集中式记忆管理
checkpointer = MemorySaver()
app_graph = workflow.compile(checkpointer=checkpointer)
print("✓ LangGraph workflow compiled with MemorySaver (in-memory checkpointer)")

# ============================================
# Pydantic Models
# ============================================

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

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
        "status": "M3 Agent System v2.2.0 Running",
        "tools": len(tools),
        "features": ["Agent Workflow", "Tool Calling", "OpenAI Compatible"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "llm_model": settings.LLM_MODEL,
        "tools_count": len(tools)
    }

@app.post("/api/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """原生 Agent 接口：支持完整的工具调用工作流"""
    try:
        # 构建输入消息
        input_messages = [HumanMessage(content=request.message)]
        
        # 调用 Agent 工作流
        config = {"configurable": {"thread_id": request.thread_id}}
        result = app_graph.invoke(
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
        
        return ChatResponse(
            response=last_message.content if hasattr(last_message, "content") else str(last_message),
            thread_id=request.thread_id,
            tool_calls=tool_calls_info if tool_calls_info else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@app.get("/api/tools")
async def list_tools():
    """列出所有可用工具"""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in tools
        ]
    }

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
        
        # 调用 Agent 工作流
        config = {"configurable": {"thread_id": f"openai_{int(time.time())}"}}
        result = app_graph.invoke(
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
# WebSocket Chat Room (预留接口)
# ============================================

class ConnectionManager:
    """WebSocket 连接管理器（为未来的舰队聊天室预留）"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 聊天接口（预留）"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: 未来在这里集成 Agent 工作流
            # 目前只是简单回显
            await manager.broadcast(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
import atexit

# 启动记忆同步
start_memory_sync()
logger.info("✓ Memory sync worker started")

# 注册关闭钩子
atexit.register(stop_memory_sync)

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
