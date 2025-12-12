"""
Agent6 主入口文件 - 单进程FastAPI应用
整合了原main.py和admin_app.py的所有功能
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 添加app目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from app.config import (
    AGENT_VERSION, 
    API_PORT, 
    ENABLE_CORS, 
    CORS_ORIGINS,
    TIMEZONE
)
from app.state import state_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("=" * 60)
    print(f"🚀 {AGENT_VERSION} 启动中...")
    print(f"   时区: {TIMEZONE}")
    print(f"   端口: {API_PORT}")
    print("=" * 60)
    
    # Phase 2: 加载工具池和LangGraph
    from app.tools import load_all_tools
    from app.workflow import create_app_graph
    from langchain_openai import ChatOpenAI
    
    # 初始化LLM
    llm = ChatOpenAI(
        base_url="http://localhost:8000/v1",
        model="local-model",
        temperature=0.7,
        api_key="not-needed"
    )
    
    # 加载工具池
    tools, tool_errors = load_all_tools()
    state_manager.loaded_tools = {tool.name: tool for tool in tools}
    state_manager.tool_errors = tool_errors
    state_manager.mark_tool_pool_loaded({tool.name: tool for tool in tools})
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(tools)
    state_manager.app_state["llm_with_tools"] = llm_with_tools
    state_manager.app_state["tools"] = tools
    
    # 创建并编译LangGraph工作流
    app_graph = create_app_graph()
    state_manager.set_app_graph(app_graph)
    
    # Phase 4: 启动后台服务
    from app.services import system_monitor, task_scheduler
    
    # 启动系统监控服务
    await system_monitor.start()
    
    # 启动定时任务调度服务
    await task_scheduler.start()
    
    print(f"✅ {AGENT_VERSION} 启动完成")
    print(f"   管理面板: http://localhost:{API_PORT}/dashboard")
    print(f"   聊天室: http://localhost:{API_PORT}/chatroom")
    print(f"   API文档: http://localhost:{API_PORT}/docs")
    print("=" * 60)
    
    yield  # 应用运行中
    
    # 关闭时执行的清理任务
    print(f"🛑 {AGENT_VERSION} 关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=AGENT_VERSION,
    description="统一的智能座席系统 - 单进程架构",
    version="6.6.0",
    lifespan=lifespan
)

# 配置CORS
if ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": AGENT_VERSION,
        "status": "running",
        "uptime": state_manager.get_uptime(),
        "endpoints": {
            "dashboard": "/dashboard",
            "chatroom": "/chatroom",
            "api_docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": AGENT_VERSION,
        "uptime": state_manager.get_uptime()
    }

@app.get("/status")
async def system_status():
    """系统状态"""
    return state_manager.get_system_status()


# ==================== API路由挂载 ====================
# Phase 3: 挂载聊天室API
from app.api.chat import router as chat_router
app.include_router(chat_router, tags=["Chat"])

# Phase 4: 挂载管理面板API
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router, tags=["Dashboard"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,  # 生产环境关闭热重载
        log_level="info"
    )
