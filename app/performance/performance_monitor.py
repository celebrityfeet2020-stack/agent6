"""
性能监控模块（v3.9.0）
监控模型性能和API性能，每小时自动更新一次
v3.9修复：使用get_current_model()避免模型切换
"""
import time
import asyncio
from datetime import datetime
from typing import Dict, Optional
import httpx
import os

# 性能数据缓存
_performance_cache = {
    "model_performance": {
        "tokens_per_second": 0,
        "time_to_first_token_ms": 0,
        "average_latency_ms": 0,
        "last_updated": None
    },
    "api_performance": {
        "average_response_time_ms": 0,
        "total_requests": 0,
        "success_rate": 100.0,
        "requests_per_hour": 0,
        "last_updated": None
    }
}

# API统计数据
_api_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_response_time": 0.0,
    "hourly_requests": [],  # [(timestamp, count), ...]
    "start_time": time.time()
}


def record_api_request(success: bool, response_time_ms: float):
    """记录API请求"""
    _api_stats["total_requests"] += 1
    if success:
        _api_stats["successful_requests"] += 1
    else:
        _api_stats["failed_requests"] += 1
    _api_stats["total_response_time"] += response_time_ms
    
    # 记录每小时请求数
    current_hour = int(time.time() // 3600)
    if not _api_stats["hourly_requests"] or _api_stats["hourly_requests"][-1][0] != current_hour:
        _api_stats["hourly_requests"].append((current_hour, 1))
    else:
        _api_stats["hourly_requests"][-1] = (current_hour, _api_stats["hourly_requests"][-1][1] + 1)
    
    # 只保留最近24小时的数据
    cutoff_hour = current_hour - 24
    _api_stats["hourly_requests"] = [(h, c) for h, c in _api_stats["hourly_requests"] if h > cutoff_hour]


async def get_current_model(llm_base_url: str) -> Optional[str]:
    """获取当前运行的模型"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{llm_base_url}/models")
            data = response.json()
            models = data.get("data", [])
            if models:
                # 返回第一个模型（通常是当前加载的模型）
                return models[0].get("id")
    except Exception as e:
        print(f"[Performance Monitor] Failed to get current model: {e}")
    return None


async def measure_model_performance() -> Dict:
    """测量模型性能（使用当前运行的模型，不切换模型）"""
    llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
    
    # 获取当前运行的模型
    current_model = await get_current_model(llm_base_url)
    if not current_model:
        print("[Performance Monitor] No model currently loaded, skipping performance test")
        return {
            "tokens_per_second": 0,
            "time_to_first_token_ms": 0,
            "average_latency_ms": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    test_prompt = "你好"
    
    try:
        # 测量TTFT和总延迟
        start_time = time.time()
        ttft = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{llm_base_url}/chat/completions",
                json={
                    "model": current_model,  # 使用当前模型
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 50,
                    "stream": True
                }
            ) as response:
                first_chunk = True
                async for line in response.aiter_lines():
                    if first_chunk and line.strip():
                        ttft = (time.time() - start_time) * 1000  # ms
                        first_chunk = False
        
        end_time = time.time()
        total_latency = (end_time - start_time) * 1000  # ms
        
        # 获取token统计
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{llm_base_url}/chat/completions",
                json={
                    "model": current_model,  # 使用当前模型
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 50
                }
            )
            data = response.json()
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        
        # 计算tokens/s
        tokens_per_second = round(completion_tokens / (total_latency / 1000), 2) if total_latency > 0 else 0
        
        print(f"[Performance Monitor] Model: {current_model}, Tokens/s: {tokens_per_second}, TTFT: {ttft}ms")
        
        return {
            "tokens_per_second": tokens_per_second,
            "time_to_first_token_ms": round(ttft, 2) if ttft else 0,
            "average_latency_ms": round(total_latency, 2),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[Performance Monitor] Failed to measure model performance: {e}")
        return {
            "tokens_per_second": 0,
            "time_to_first_token_ms": 0,
            "average_latency_ms": 0,
            "last_updated": datetime.now().isoformat()
        }


def calculate_api_performance() -> Dict:
    """计算API性能"""
    total = _api_stats["total_requests"]
    successful = _api_stats["successful_requests"]
    
    # 平均响应时间
    avg_response_time = round(_api_stats["total_response_time"] / total, 2) if total > 0 else 0
    
    # 成功率
    success_rate = round((successful / total) * 100, 2) if total > 0 else 100.0
    
    # 每小时请求数（最近一小时）
    current_hour = int(time.time() // 3600)
    requests_per_hour = 0
    for hour, count in _api_stats["hourly_requests"]:
        if hour == current_hour:
            requests_per_hour = count
            break
    
    return {
        "average_response_time_ms": avg_response_time,
        "total_requests": total,
        "success_rate": success_rate,
        "requests_per_hour": requests_per_hour,
        "last_updated": datetime.now().isoformat()
    }


async def update_performance_cache():
    """更新性能缓存（每小时执行一次）"""
    print("[Performance Monitor] Updating performance cache...")
    
    # 测量模型性能
    model_perf = await measure_model_performance()
    _performance_cache["model_performance"] = model_perf
    
    # 计算API性能
    api_perf = calculate_api_performance()
    _performance_cache["api_performance"] = api_perf
    
    print(f"[Performance Monitor] Cache updated: Model={model_perf['tokens_per_second']}tok/s, API={api_perf['average_response_time_ms']}ms")


def get_performance_data() -> Dict:
    """获取性能数据（从缓存）"""
    return _performance_cache.copy()


async def performance_monitor_loop():
    """性能监控后台任务（每小时更新一次）"""
    while True:
        try:
            await update_performance_cache()
        except Exception as e:
            print(f"[Performance Monitor] Error in monitor loop: {e}")
        
        # 等待1小时
        await asyncio.sleep(3600)
