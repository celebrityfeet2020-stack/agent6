"""
Dashboard API Endpoints for v6.3
实现管理面板所需的所有API端点
"""

import httpx
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# 全局变量：记录启动时间
_startup_time = datetime.now()

def get_startup_time():
    """获取启动时间"""
    return _startup_time

def set_startup_time(time: datetime):
    """设置启动时间"""
    global _startup_time
    _startup_time = time


async def get_dashboard_status() -> Dict[str, Any]:
    """
    获取系统状态
    
    Returns:
        {
            "uptime": 1234,  # 运行时间(秒)
            "started_at": "2025-12-05T13:14:59Z",  # 启动时间(ISO格式)
            "overall_health": "healthy",  # healthy/degraded/error
        }
    """
    now = datetime.now()
    uptime_seconds = int((now - _startup_time).total_seconds())
    
    # 检查Agent API健康状态
    overall_health = "healthy"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8888/health")
            if response.status_code != 200:
                overall_health = "degraded"
    except:
        overall_health = "error"
    
    return {
        "uptime": uptime_seconds,
        "started_at": _startup_time.isoformat() + "Z",
        "overall_health": overall_health,
    }


async def get_preload_status() -> Dict[str, Any]:
    """
    获取预加载状态
    
    Returns:
        {
            "status": "completed",  # waiting/loading/completed
            "elapsed_time": 900,  # 已等待时间(秒)
            "target_time": 900,  # 目标时间(15分钟=900秒)
        }
    """
    now = datetime.now()
    elapsed_seconds = int((now - _startup_time).total_seconds())
    target_seconds = 15 * 60  # 15分钟
    
    if elapsed_seconds < target_seconds:
        status = "waiting"
    elif elapsed_seconds < target_seconds + 60:  # 给1分钟加载时间
        status = "loading"
    else:
        status = "completed"
    
    return {
        "status": status,
        "elapsed_time": elapsed_seconds,
        "target_time": target_seconds,
    }


async def get_health_details() -> Dict[str, Any]:
    """
    获取健康检测详情
    
    Returns:
        {
            "tools_count": 15,
            "tools_status": "healthy",
            "fleet_api": "healthy",
            "langgraph_api": "healthy",
            "llm_connection": "healthy",
        }
    """
    tools_count = 0
    tools_status = "unknown"
    llm_connection = "unknown"
    
    # 检查Agent API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8888/health")
            if response.status_code == 200:
                data = response.json()
                tools_count = data.get("tools_count", 0)
                tools_status = "healthy" if tools_count > 0 else "degraded"
                llm_connection = data.get("status", "unknown")
    except:
        tools_status = "error"
        llm_connection = "error"
    
    return {
        "tools_count": tools_count,
        "tools_status": tools_status,
        "fleet_api": "healthy",  # v6.3: Always healthy (no separate fleet API)
        "langgraph_api": "healthy",  # v6.3: Always healthy (integrated)
        "llm_connection": llm_connection,
    }


async def get_performance_data() -> Dict[str, Any]:
    """
    获取性能数据
    
    Returns:
        {
            "model": {
                "tokens_per_second": 22.37,
                "ttft_ms": 377.79,
                "total_latency_ms": 1500,
                "updated_at": "2025-12-05T13:30:00Z"
            },
            "api": {
                "avg_response_time_ms": 150,
                "total_requests": 1234,
                "success_rate": 99.5,
                "requests_per_hour": 120,
                "updated_at": "2025-12-05T13:30:00Z"
            }
        }
    """
    # 从performance_monitor获取缓存数据
    from app.performance.performance_monitor import get_performance_data as get_perf_cache
    
    perf_data = get_perf_cache()
    
    # 格式化为Dashboard API格式
    model_perf = perf_data.get("model_performance", {})
    api_perf = perf_data.get("api_performance", {})
    
    return {
        "model": {
            "tokens_per_second": model_perf.get("tokens_per_second", 0),
            "ttft_ms": model_perf.get("ttft_ms", 0),
            "total_latency_ms": model_perf.get("total_latency_ms", 0),
            "updated_at": model_perf.get("updated_at", datetime.now().isoformat() + "Z")
        },
        "api": {
            "avg_response_time_ms": api_perf.get("avg_response_time_ms", 0),
            "total_requests": api_perf.get("total_requests", 0),
            "success_rate": api_perf.get("success_rate", 100.0),
            "requests_per_hour": api_perf.get("requests_per_hour", 0),
            "updated_at": api_perf.get("updated_at", datetime.now().isoformat() + "Z")
        }
    }
