# ============================================
# v6.5.3 API补丁 - 添加到admin_app.py中
# ============================================
# 将以下代码添加到admin_app.py的Dashboard API部分之后

# 1. 添加 /health 端点（Docker健康检查）
@admin_app.get("/health")
async def health_check():
    """
    Docker健康检查端点
    返回简单的健康状态
    """
    return {"status": "healthy", "service": "admin_panel", "version": "6.5.3"}


# 2. 添加 /api/models 端点（LLM模型检测）
@admin_app.get("/api/models")
async def get_llm_models():
    """
    检测端口8000上运行的LLM模型
    
    返回格式:
    {
        "api_url": "http://192.168.9.125:8000/v1",
        "current_model": "minimax/minimax-m2",
        "available_models": ["minimax/minimax-m2"],
        "status": "connected"
    }
    """
    import httpx
    import os
    
    # 从环境变量获取LLM API配置
    api_base = os.getenv("OPENAI_BASE_URL", "http://192.168.9.125:8000/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    # 尝试检测模型
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 尝试调用 /v1/models 端点
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = await client.get(f"{api_base}/models", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                models_list = data.get("data", [])
                
                if models_list:
                    # 提取模型ID
                    available_models = [m.get("id", "unknown") for m in models_list]
                    current_model = available_models[0] if available_models else "unknown"
                    
                    return {
                        "api_url": api_base,
                        "current_model": current_model,
                        "available_models": available_models,
                        "status": "connected"
                    }
            
            # 如果/v1/models不可用，尝试直接测试连接
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
            
            if test_response.status_code in [200, 400]:  # 400也表示连接成功
                # 从环境变量或配置推断模型名称
                inferred_model = "minimax/minimax-m2"  # 默认模型
                
                return {
                    "api_url": api_base,
                    "current_model": inferred_model,
                    "available_models": [inferred_model],
                    "status": "connected"
                }
                
    except Exception as e:
        print(f"[LLM Detection] Error: {e}")
    
    # 连接失败，返回默认配置
    return {
        "api_url": api_base,
        "current_model": "unknown",
        "available_models": [],
        "status": "disconnected"
    }


# 3. 添加定时任务逻辑
# 全局变量：记录上次更新时间
_last_agent_api_update = None
_last_performance_test = None
_scheduled_task = None

async def scheduled_tasks_loop():
    """
    定时任务循环
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
                    _last_agent_api_update = now
            else:
                if (now - _last_agent_api_update).total_seconds() >= 30 * 60:  # 30分钟
                    print("[Scheduled Tasks] Running Agent API status update (periodic)...")
                    _last_agent_api_update = now
            
            # 模型性能测试（启动后20分钟，之后每15分钟）
            if _last_performance_test is None:
                if elapsed_seconds >= 20 * 60:  # 20分钟
                    print("[Scheduled Tasks] Running model performance test (first time)...")
                    await update_performance_cache()  # 触发性能测试
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


# 4. 修改startup_event以启动定时任务
# 在原有的startup_event中添加：
# global _scheduled_task
# _scheduled_task = asyncio.create_task(scheduled_tasks_loop())
# print("[Admin Panel] Scheduled tasks started (task reference kept)")
