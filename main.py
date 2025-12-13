"""
Agent6 主入口文件 - 单进程FastAPI应用
整合了原main.py和admin_app.py的所有功能
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
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
    
    # Phase 2: 初始化LLM和LangGraph(工具池将在5分钟后加载)
    from app.workflow import create_agent_graph
    from langchain_openai import ChatOpenAI
    
    # 初始化LLM
    llm = ChatOpenAI(
        base_url=f"http://{state_manager.config.MODEL_HOST}:{state_manager.config.MODEL_PORT}/v1",
        model="local-model",
        temperature=0.7,
        api_key="not-needed"
    )
    
    # 暂不加载工具,等待定时任务在5分钟后加载
    print("⚠️  工具池将在5分钟后加载...")
    
    # 创建并编译LangGraph工作流(使用空工具列表)
    app_graph = create_agent_graph()
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

# Phase 5: 挂载LangGraph Cloud兼容API
from app.api.langgraph_cloud import router as langgraph_router
app.include_router(langgraph_router, prefix="/api/langgraph", tags=["LangGraph Cloud"])

# Phase 6: 挂载元提示词管理API
from app.api.meta_prompt import router as meta_prompt_router
app.include_router(meta_prompt_router, tags=["Meta Prompt"])

# Phase 7: 挂载多维聊天室API
from app.api.multidimensional_chat import router as multidimensional_chat_router
app.include_router(multidimensional_chat_router, tags=["Multidimensional Chat"])

# Phase 7.1: 挂载多维聊天室WebSocket API
from app.api.multidimensional_ws import router as multidimensional_ws_router
from app.api.multidimensional_chat_sse import router as multidimensional_chat_sse_router
app.include_router(multidimensional_ws_router, tags=["Multidimensional Chat WebSocket"])
app.include_router(multidimensional_chat_sse_router, tags=["Multidimensional Chat SSE"])

# Phase 8: 挂载增强型监控API
from app.api.monitoring import router as monitoring_router
app.include_router(monitoring_router, tags=["Monitoring"])

# Phase 9: 挂载上下文监控API
from app.api.context_monitor import router as context_monitor_router
app.include_router(context_monitor_router, tags=["Context Monitor"])

# Phase 10: 挂载Fleet统计API
from app.api.fleet_stats import router as fleet_stats_router
app.include_router(fleet_stats_router, tags=["Fleet Stats"])


# ==================== 静态文件和UI路由 ====================
# 挂载管理面板静态文件
if os.path.exists("admin_ui/static"):
    app.mount("/dashboard/static", StaticFiles(directory="admin_ui/static"), name="dashboard_static")

# 管理面板HTML路由
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """管理面板"""
    dashboard_html_path = "admin_ui/templates/dashboard.html"
    if os.path.exists(dashboard_html_path):
        with open(dashboard_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Dashboard UI 未找到</h1><p>请确保 admin_ui/templates/dashboard.html 存在</p>", status_code=404)

# 多维聊天室HTML路由
@app.get("/chatroom", response_class=HTMLResponse)
async def chatroom():
    """聊天室 - 返回React应用的index.html"""
    chatroom_html_path = "chatroom_ui/index.html"
    if os.path.exists(chatroom_html_path):
        with open(chatroom_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Chatroom UI 未找到</h1><p>请确保 chatroom_ui/index.html 存在或运行 'cd chatroom_ui && pnpm install && pnpm build'</p>", status_code=404)

# 挂载聊天室静态文件
if os.path.exists("chatroom_ui/dist"):
    app.mount("/chatroom/assets", StaticFiles(directory="chatroom_ui/dist/assets"), name="chatroom_assets")
elif os.path.exists("chatroom_ui/static"):
    app.mount("/chatroom/static", StaticFiles(directory="chatroom_ui/static"), name="chatroom_static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,  # 生产环境关闭热重载
        log_level="info"
    )
