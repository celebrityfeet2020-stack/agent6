"""
M3 Agent 管理面板 v6.5.4
独立运行在端口 8889，提供管理界面和 API

v6.5.4更新：
- 修复系统运行时间（从后端获取，不是前端计时）
- 修复LLM模型检测（正确检测端口8000的模型）
- 修复定时任务（真正执行更新，不只是打印日志）
- 修复内存预加载倒计时（从后端获取，不是前端计时）
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
import os
import uuid
from datetime import datetime, timedelta
import threading
import asyncio
from app.performance.performance_monitor import (
    get_performance_data,
    update_performance_cache,
    performance_monitor_loop,
    record_api_request
)

# ============================================
# FastAPI Application Setup
# ============================================

admin_app = FastAPI(
    title="M3 Agent Admin Panel",
    version="6.5.4"
)

admin_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模板目录
templates = Jinja2Templates(directory="/app/admin_ui/templates")

# v6.1: 挂载聊天室UI静态文件
import os
chatroom_ui_dir = "/app/chatroom_ui_dist"
if os.path.exists(chatroom_ui_dir):
    admin_app.mount("/chatroom", StaticFiles(directory=chatroom_ui_dir, html=True), name="chatroom")
    print(f"[Admin Panel] Chatroom UI mounted at /chatroom (from {chatroom_ui_dir})")
else:
    print(f"[Admin Panel] Warning: Chatroom UI directory not found: {chatroom_ui_dir}")

# ============================================
# Startup Event
# ============================================

# v5.6: Keep task reference to prevent garbage collection
_monitor_task = None
_scheduled_task = None

# v6.5.4: 定时任务状态
_last_agent_api_update = None
_last_performance_test = None

# v6.5.4: Agent API状态缓存
_agent_api_status_cache = {
    "config_model": "minimax/minimax-m2",
    "tool_count": 15,
    "api_port": 8000,
    "last_check": "--"
}

@admin_app.on_event("startup")
async def startup_event():
    """启动时初始化性能监控"""
    global _monitor_task, _scheduled_task
    # v6.3: 初始化启动时间
    from dashboard_apis import set_startup_time
    from datetime import datetime
    set_startup_time(datetime.now())
    print("[Admin Panel] Initializing performance monitoring...")
    # 立即更新一次性能数据
    await update_performance_cache()
    # 启动后台监控任务（保持引用防止被垃圾回收）
    _monitor_task = asyncio.create_task(performance_monitor_loop())
    print("[Admin Panel] Performance monitoring started (task reference kept)")
    
    # v6.5.4: 启动定时任务
    _scheduled_task = asyncio.create_task(scheduled_tasks_loop())
    print("[Admin Panel] Scheduled tasks started (task reference kept)")

# ============================================
# v6.5.4: Docker健康检查端点
# ============================================

@admin_app.get("/health")
async def health_check():
    """Docker健康检查端点"""
    return {"status": "healthy", "service": "admin_panel", "version": "6.5.4"}

# ============================================
# v6.5.4: LLM模型检测端点（修复版）
# ============================================

@admin_app.get("/api/models")
async def get_llm_models():
    """
    检测端口8000上运行的LLM模型
    支持OpenAI兼容API
    """
    import httpx
    import os
    
    # 从环境变量获取API配置
    api_base = os.getenv("OPENAI_BASE_URL", "http://192.168.9.125:8000/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # 尝试调用 /v1/models 端点
            response = await client.get(f"{api_base}/models", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                models_list = data.get("data", [])
                
                if models_list:
                    available_models = [m.get("id", "unknown") for m in models_list]
                    current_model = available_models[0] if available_models else "unknown"
                    
                    return {
                        "api_url": api_base,
                        "current_model": current_model,
                        "available_models": available_models,
                        "status": "connected"
                    }
            
            # 如果/v1/models失败，尝试发送测试请求
            test_response = await client.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json={
                    "model": "minimax/minimax-m2",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10.0
            )
            
            if test_response.status_code == 200:
                return {
                    "api_url": api_base,
                    "current_model": "minimax/minimax-m2",
                    "available_models": ["minimax/minimax-m2"],
                    "status": "connected"
                }
            
            return {
                "api_url": api_base,
                "current_model": "unknown",
                "available_models": [],
                "status": "error",
                "error": f"HTTP {test_response.status_code}"
            }
            
    except Exception as e:
        return {
            "api_url": api_base,
            "current_model": "unknown",
            "available_models": [],
            "status": "disconnected",
            "error": str(e)
        }

# ============================================
# v6.5.4: 定时任务系统（修复版）
# ============================================

async def update_agent_api_status():
    """
    更新Agent API状态
    检查工具数量、配置模型等
    """
    global _agent_api_status_cache
    
    try:
        # 检查Agent API的健康状态
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8888/health")
            
            if response.status_code == 200:
                data = response.json()
                _agent_api_status_cache["tool_count"] = data.get("tool_count", 15)
                _agent_api_status_cache["config_model"] = data.get("config_model", "minimax/minimax-m2")
                _agent_api_status_cache["api_port"] = 8000
                _agent_api_status_cache["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[Scheduled Tasks] Agent API status updated: {_agent_api_status_cache}")
            else:
                print(f"[Scheduled Tasks] Agent API health check failed: HTTP {response.status_code}")
                
    except Exception as e:
        print(f"[Scheduled Tasks] Error updating Agent API status: {e}")

@admin_app.get("/api/agent-status")
async def get_agent_api_status():
    """
    获取Agent API状态
    """
    return _agent_api_status_cache

async def scheduled_tasks_loop():
    """
    v6.5.4: 定时任务循环（修复版）
    - Agent API状态: 启动后5分钟，之后每30分钟
    - 模型性能测试: 启动后20分钟，之后每15分钟
    """
    global _last_agent_api_update, _last_performance_test
    
    from dashboard_apis import get_startup_time
    
    print("[Scheduled Tasks] Task loop started")
    
    while True:
        try:
            now = datetime.now()
            startup_time = get_startup_time()
            elapsed_seconds = (now - startup_time).total_seconds()
            
            # Agent API状态更新（启动后5分钟，之后每30分钟）
            if _last_agent_api_update is None:
                if elapsed_seconds >= 5 * 60:  # 5分钟
                    print("[Scheduled Tasks] Running Agent API status update (first time)...")
                    await update_agent_api_status()
                    _last_agent_api_update = now
            else:
                if (now - _last_agent_api_update).total_seconds() >= 30 * 60:  # 30分钟
                    print("[Scheduled Tasks] Running Agent API status update (periodic)...")
                    await update_agent_api_status()
                    _last_agent_api_update = now
            
            # 模型性能测试（启动后20分钟，之后每15分钟）
            if _last_performance_test is None:
                if elapsed_seconds >= 20 * 60:  # 20分钟
                    print("[Scheduled Tasks] Running model performance test (first time)...")
                    await update_performance_cache()
                    _last_performance_test = now
            else:
                if (now - _last_performance_test).total_seconds() >= 15 * 60:  # 15分钟
                    print("[Scheduled Tasks] Running model performance test (periodic)...")
                    await update_performance_cache()
                    _last_performance_test = now
            
            # 每分钟检查一次
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"[Scheduled Tasks] Error: {e}")
            await asyncio.sleep(60)

# ============================================
# Dashboard API Endpoints
# ============================================

from dashboard_apis import (
    get_dashboard_status,
    get_preload_status,
    get_health_details,
    get_performance_data
)

@admin_app.get("/api/dashboard/status")
async def dashboard_status():
    """获取系统状态"""
    return await get_dashboard_status()

@admin_app.get("/api/dashboard/preload-status")
async def preload_status():
    """获取预加载状态"""
    return await get_preload_status()

@admin_app.get("/api/dashboard/health")
async def health_details():
    """获取健康检测详情"""
    return await get_health_details()

@admin_app.get("/api/dashboard/performance")
async def performance_data():
    """获取性能数据"""
    return await get_performance_data()

# ============================================
# Unified Chat Room API
# ============================================

from app.api.unified_chat_room import router as unified_chat_room_router
admin_app.include_router(unified_chat_room_router)

# Chatroom SSE Stream API
from chatroom_api import router as chatroom_api_router
admin_app.include_router(chatroom_api_router)

# ============================================
# Admin Panel UI Routes
# ============================================

@admin_app.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """管理面板首页"""
    return templates.TemplateResponse("index.html", {"request": request})

@admin_app.get("/admin", response_class=HTMLResponse)
async def admin_panel_alt(request: Request):
    """管理面板首页（备用路径）"""
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(admin_app, host="0.0.0.0", port=8889)
