"""
A6 System v6.2.0 - Admin Panel
独立运行在端口 8002，提供管理界面和 API
v5.7.1更新：线程池浏览器+工具池，保留uvloop性能，工具调用速度提升10-20倍
v5.6更新：修复性能监控定时任务，保持任务引用防止被垃圾回收
v5.5更新：基于v5.2稳定版本，实现三角聊天室，WebSocket实时推送，优化前后端联通
"""

# v5.7.1: Browser pool uses thread pool (no need for nest_asyncio)
# Removed nest_asyncio to preserve uvloop performance

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
    version="5.7.1"
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

@admin_app.on_event("startup")
async def startup_event():
    """启动时初始化性能监控"""
    global _monitor_task
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

# ============================================
# Pydantic Models
# ============================================

class SystemPrompt(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    prompt: str
    is_active: bool = False
    created_at: str
    updated_at: str

class CreatePromptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    prompt: str

class UpdatePromptRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None

# ============================================
# Helper Functions
# ============================================

PROMPTS_FILE = "/app/data/system_prompts.json"

def load_prompts() -> List[Dict]:
    """加载所有提示词"""
    if not os.path.exists(PROMPTS_FILE):
        # 创建默认提示词
        default_prompt = {
            "id": "default",
            "name": "默认 Agent 提示词",
            "description": "M3 Agent 的默认系统提示",
            "prompt": """你是 M3 Agent，一个功能强大的 AI 助手，拥有以下能力：

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

现在，请根据用户的请求，充分利用你的工具来完成任务！""",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump([default_prompt], f, ensure_ascii=False, indent=2)
        return [default_prompt]
    
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_prompts(prompts: List[Dict]):
    """保存提示词到文件"""
    os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

async def get_available_models():
    """获取可用模型列表（v3.9简化版：不检测后端类型）"""
    llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{llm_base_url}/models")
            data = response.json()
            
            # Ollama格式
            if "models" in data:
                return data["models"]
            
            # OpenAI兼容格式
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            
            return []
    except Exception as e:
        return []

async def get_actual_running_model():
    """获取实际运行的模型（v6.3.2：通过test请求获取）"""
    llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
    llm_model_fallback = os.getenv("LLM_MODEL", "minimax/minimax-m2")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{llm_base_url}/chat/completions",
                json={
                    "model": llm_model_fallback,  # 使用配置的模型发起请求
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1
                }
            )
            data = response.json()
            # 从响应中获取实际运行的模型
            actual_model = data.get("model")
            if actual_model:
                return actual_model
    except Exception as e:
        print(f"[Admin Panel] Failed to get actual running model: {e}")
    
    # 如果失败,返回环境变量
    return llm_model_fallback

# ============================================
# Web Interface
# ============================================

@admin_app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """管理面板主页"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@admin_app.get("/chat", response_class=HTMLResponse)
async def chatroom_redirect():
    """重定向到聊天室UI (v6.1)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/chatroom/")

# ============================================
# System Status API
# ============================================

@admin_app.get("/api/benchmark")
async def run_benchmark():
    """运行性能基准测试（v3.9：只测试当前运行的模型）"""
    try:
        import time
        
        llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
        llm_model = os.getenv("LLM_MODEL", "minimax/minimax-m2")
        
        results = []
        test_prompt = "你好，请用一句话介绍你自己。"
        
        # 只测试当前运行的模型
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{llm_base_url}/chat/completions",
                    json={
                        "model": llm_model,
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 50
                    },
                    timeout=30
                )
            
            end_time = time.time()
            latency = round((end_time - start_time) * 1000, 2)  # ms
            
            # 计算 tokens/s
            response_data = response.json()
            usage = response_data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_per_second = round(completion_tokens / (end_time - start_time), 2) if completion_tokens > 0 else 0
            
            results.append({
                "model": llm_model,
                "status": "success",
                "latency_ms": latency,
                "tokens_per_second": tokens_per_second,
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens
            })
        except Exception as e:
            results.append({
                "model": llm_model,
                "status": "failed",
                "error": str(e)
            })
        
        # 更新性能缓存
        await update_performance_cache()
        
        return {"benchmark_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_app.get("/api/status")
async def get_status():
    """获取系统状态（v6.3.2：使用实际运行的模型）"""
    llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
    
    # v6.3.2: 获取实际运行的模型
    actual_model = await get_actual_running_model()
    
    # 获取可用模型列表
    models = await get_available_models()
    
    # 动态获取工具数量
    tools_count = 15  # 默认15个工具
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                tools_count = data.get("tools_count", 15)
    except:
        pass
    
    # 获取性能数据（从缓存）
    performance_data = get_performance_data()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "llm_backend": {
            "status": "running" if models else "error",
            "current_model": actual_model,  # v6.3.2: 使用实际运行的模型
            "available_models": [m.get("id", m.get("name", "unknown")) for m in models] if models else [actual_model],
            "base_url": llm_base_url
        },
        "agent_api": {
            "status": "running",
            "configured_model": actual_model,  # v6.3.2: 使用实际运行的模型
            "tools_count": tools_count,
            "api_port": 8000
        },
        "model_performance": performance_data.get("model_performance", {}),
        "api_performance": performance_data.get("api_performance", {})
    }

# ============================================
# Dashboard API (v6.3)
# ============================================

from dashboard_apis import (
    get_dashboard_status,
    get_preload_status,
    get_health_details,
    get_performance_data as get_dashboard_performance,
    set_startup_time
)

@admin_app.get("/api/dashboard/status")
async def dashboard_status():
    """获取系统状态"""
    return await get_dashboard_status()

@admin_app.get("/api/dashboard/preload-status")
async def dashboard_preload_status():
    """获取预加载状态"""
    return await get_preload_status()

@admin_app.get("/api/dashboard/health")
async def dashboard_health():
    """获取健康检测详情"""
    return await get_health_details()

@admin_app.get("/api/dashboard/performance")
async def dashboard_performance():
    """获取性能数据"""
    return await get_dashboard_performance()

# ============================================
# Unified Chat Room API (v6.3.2)
# ============================================

from app.api.unified_chat_room import router as unified_chat_room_router
admin_app.include_router(unified_chat_room_router)

# Chatroom SSE Stream API (v6.4)
from chatroom_api import router as chatroom_api_router
admin_app.include_router(chatroom_api_router)

# ============================================
# Prompt Management API
# ============================================

@admin_app.get("/api/prompts")
async def get_prompts():
    """获取所有提示词"""
    return load_prompts()

@admin_app.get("/api/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """获取单个提示词"""
    prompts = load_prompts()
    for prompt in prompts:
        if prompt["id"] == prompt_id:
            return prompt
    raise HTTPException(status_code=404, detail="Prompt not found")

@admin_app.post("/api/prompts")
async def create_prompt(request: CreatePromptRequest):
    """创建新提示词"""
    prompts = load_prompts()
    
    new_prompt = {
        "id": str(uuid.uuid4()),
        "name": request.name,
        "description": request.description,
        "prompt": request.prompt,
        "is_active": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    prompts.append(new_prompt)
    save_prompts(prompts)
    
    return new_prompt

@admin_app.put("/api/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, request: UpdatePromptRequest):
    """更新提示词"""
    prompts = load_prompts()
    
    for prompt in prompts:
        if prompt["id"] == prompt_id:
            if request.name is not None:
                prompt["name"] = request.name
            if request.description is not None:
                prompt["description"] = request.description
            if request.prompt is not None:
                prompt["prompt"] = request.prompt
            prompt["updated_at"] = datetime.now().isoformat()
            
            save_prompts(prompts)
            return prompt
    
    raise HTTPException(status_code=404, detail="Prompt not found")

@admin_app.delete("/api/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """删除提示词"""
    if prompt_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default prompt")
    
    prompts = load_prompts()
    prompts = [p for p in prompts if p["id"] != prompt_id]
    save_prompts(prompts)
    
    return {"status": "success"}

@admin_app.post("/api/prompts/{prompt_id}/activate")
async def activate_prompt(prompt_id: str):
    """激活提示词"""
    prompts = load_prompts()
    
    # 取消所有激活状态
    for prompt in prompts:
        prompt["is_active"] = False
    
    # 激活指定提示词
    found = False
    for prompt in prompts:
        if prompt["id"] == prompt_id:
            prompt["is_active"] = True
            prompt["updated_at"] = datetime.now().isoformat()
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    save_prompts(prompts)
    return {"status": "success"}

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    # 从环境变量读取端口，默认8889 (v6.3: fixed default port)
    admin_port = int(os.getenv("ADMIN_PORT", "8889"))
    print(f"[Admin Panel] Starting on port {admin_port}")
    # v5.7.1: Use default uvloop for performance
    uvicorn.run(
        admin_app,
        host="0.0.0.0",
        port=admin_port,
        log_level="info"
        # No loop="asyncio" - let uvicorn use uvloop by default
    )
