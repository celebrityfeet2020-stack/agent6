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
    version="6.5.7"
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

# v6.5.5: 容器启动时间(北京时间)
_container_start_time = None

@admin_app.on_event("startup")
async def startup_event():
    """启动时初始化性能监控"""
    global _monitor_task, _scheduled_task, _container_start_time
    from beijing_time_utils import get_beijing_time, get_beijing_time_str
    
    # v6.5.5: 记录容器启动时间(北京时间)
    _container_start_time = get_beijing_time()
    print(f"[Admin Panel] 容器启动时间: {get_beijing_time_str()}")
    
    # v6.3: 初始化启动时间(向后兼容)
    from dashboard_apis import set_startup_time
    set_startup_time(_container_start_time)
    
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
    return {"status": "healthy", "service": "admin_panel", "version": "6.5.5"}

@admin_app.get("/api/system/uptime")
async def get_system_uptime():
    """
    v6.5.5: 获取系统运行时间(北京时间)
    前端使用此端点获取启动时间,避免刷新页面重置
    """
    from beijing_time_utils import get_beijing_time
    
    if _container_start_time:
        current_time = get_beijing_time()
        uptime_seconds = int((current_time - _container_start_time).total_seconds())
        return {
            "start_time": _container_start_time.isoformat(),
            "current_time": current_time.isoformat(),
            "uptime_seconds": uptime_seconds,
            "timezone": "Asia/Shanghai (UTC+8)"
        }
    else:
        return {"error": "启动时间未记录"}

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
                        "status": "connected",
                        "readonly": True  # 标记为只读
                    }
            
            # 如果/v1/models失败,返回错误(不再尝试发送测试请求,避免修改模型)
            return {
                "api_url": api_base,
                "current_model": "unknown",
                "available_models": [],
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "readonly": True  # 标记为只读
            }
            
    except Exception as e:
        return {
            "api_url": api_base,
            "current_model": "unknown",
            "available_models": [],
            "status": "disconnected",
            "error": str(e),
            "readonly": True  # 标记为只读
        }

# ============================================
# v6.5.4: 定时任务系统（修复版）
# ============================================

async def task_a_tools_and_api_check():
    """
    任务A: 工具池+浏览器池+API检测
    检查15个工具是否都在内存,如果缺失则记录警告
    """
    global _agent_api_status_cache
    from beijing_time_utils import get_beijing_time_str
    
    try:
        # 检查Agent API的健康状态
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8888/health")
            
            if response.status_code == 200:
                data = response.json()
                tool_count = data.get("tools_count", 0)
                llm_model = data.get("llm_model", "unknown")
                
                # 期望15个工具
                expected_tool_count = 15
                status = "healthy" if tool_count == expected_tool_count else "warning"
                
                # 如果工具数量不对,记录警告
                if tool_count < expected_tool_count:
                    print(f"[Task A] ⚠️ 警告: 只有{tool_count}个工具,期望{expected_tool_count}个")
                else:
                    print(f"[Task A] ✅ 工具池正常: {tool_count}个工具已加载")
                
                _agent_api_status_cache = {
                    "config_model": llm_model,
                    "tool_count": tool_count,
                    "expected_tool_count": expected_tool_count,
                    "status": status,
                    "api_port": 8000,
                    "last_check": get_beijing_time_str()
                }
                
                print(f"[Task A] 工具池+API检测完成: {_agent_api_status_cache}")
            else:
                print(f"[Task A] Agent API健康检查失败: HTTP {response.status_code}")
                
    except Exception as e:
        print(f"[Task A] 执行失败: {e}")

async def task_b_model_and_api_performance():
    """
    任务B: 模型性能+API性能测试
    """
    from beijing_time_utils import get_beijing_time_str
    
    try:
        print(f"[Task B] 开始性能测试 at {get_beijing_time_str()}")
        await update_performance_cache()
        print(f"[Task B] 性能测试完成 at {get_beijing_time_str()}")
    except Exception as e:
        print(f"[Task B] 执行失败: {e}")

@admin_app.get("/api/agent-status")
async def get_agent_api_status():
    """
    获取Agent API状态
    """
    return _agent_api_status_cache

async def scheduled_tasks_loop():
    """
    v6.5.5: 定时任务循环（修复版）
    任务A: T+5min首次, 之后每30min (工具池+API检测)
    任务B: T+20min首次, 之后每30min (模型性能测试)
    两个任务错开15分钟
    """
    from beijing_time_utils import get_beijing_time_str
    
    print("[Scheduled Tasks] Task loop started")
    
    try:
        # 等待5分钟后首次执行任务A
        print(f"[Scheduled Tasks] 等待5分钟后执行任务A... at {get_beijing_time_str()}")
        await asyncio.sleep(300)  # 5分钟
        await task_a_tools_and_api_check()
        print(f"[Scheduled Tasks] ✅ 任务A首次执行完成 at {get_beijing_time_str()}")
        
        # 再等15分钟后首次执行任务B (总共20分钟)
        print(f"[Scheduled Tasks] 等待15分钟后执行任务B... at {get_beijing_time_str()}")
        await asyncio.sleep(900)  # 15分钟
        await task_b_model_and_api_performance()
        print(f"[Scheduled Tasks] ✅ 任务B首次执行完成 at {get_beijing_time_str()}")
        
        # 进入30分钟循环,两个任务错开15分钟
        while True:
            # 再等15分钟后执行任务A (距离上次任务A是30分钟)
            print(f"[Scheduled Tasks] 等待15分钟后执行任务A... at {get_beijing_time_str()}")
            await asyncio.sleep(900)  # 15分钟
            await task_a_tools_and_api_check()
            print(f"[Scheduled Tasks] ✅ 任务A执行完成 at {get_beijing_time_str()}")
            
            # 再等15分钟后执行任务B (距离上次任务B是30分钟)
            print(f"[Scheduled Tasks] 等待15分钟后执行任务B... at {get_beijing_time_str()}")
            await asyncio.sleep(900)  # 15分钟
            await task_b_model_and_api_performance()
            print(f"[Scheduled Tasks] ✅ 任务B执行完成 at {get_beijing_time_str()}")
            
    except Exception as e:
        print(f"[Scheduled Tasks] Error: {e}")
        # 出错后等待1分钟再重试
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

# v6.5.7: 元提示词API
@admin_app.get("/api/prompts")
async def get_prompts():
    """获取所有元提示词"""
    import json
    prompts_file = "/app/data/system_prompts.json"
    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts = json.load(f)
        return prompts
    except Exception as e:
        return {"error": str(e)}

@admin_app.post("/api/prompts")
async def save_prompt(prompt_data: dict):
    """保存新的元提示词"""
    import json
    from datetime import datetime
    prompts_file = "/app/data/system_prompts.json"
    try:
        # 读取现有prompts
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts = json.load(f)
        
        # 生成ID
        new_id = f"custom_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_prompt = {
            "id": new_id,
            "name": prompt_data.get("name", "未命名提示词"),
            "prompt": prompt_data.get("content", ""),
            "is_active": False,
            "created_at": datetime.now().isoformat(),
            "version": "custom"
        }
        
        # 添加到列表
        prompts.append(new_prompt)
        
        # 保存
        with open(prompts_file, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "id": new_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@admin_app.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """管理面板首页"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@admin_app.get("/admin", response_class=HTMLResponse)
async def admin_panel_alt(request: Request):
    """管理面板首页（备用路径）"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(admin_app, host="0.0.0.0", port=8889)
