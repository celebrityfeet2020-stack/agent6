"""
M3 Agent System v6.0 - Dashboard API
控制面板API：汇报健康状态和性能数据
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger("m3_agent")

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    获取系统整体状态
    
    Returns:
        系统状态摘要
    """
    try:
        from app.core.background_tasks import background_tasks_manager
        
        status = background_tasks_manager.get_status()
        
        # 添加简化的摘要
        summary = {
            "overall": "healthy",
            "uptime": status["uptime_formatted"],
            "preload_completed": status["preload_completed"],
            "last_check": status.get("last_api_check"),
            "last_performance": status.get("last_performance_test")
        }
        
        # 判断整体健康状态
        if status.get("last_api_check"):
            health = status.get("health_status", {})
            apis = health.get("apis", {})
            tools = health.get("tools", {})
            
            if tools.get("status") != "available" or apis.get("llm", {}).get("status") != "connected":
                summary["overall"] = "degraded"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "details": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """
    获取健康检测结果
    
    Returns:
        最新的健康检测结果
    """
    try:
        from app.core.background_tasks import background_tasks_manager
        
        if not background_tasks_manager.last_api_check:
            return {
                "status": "pending",
                "message": "Health check not yet performed (scheduled at T+15min)"
            }
        
        return {
            "status": "ok",
            "data": background_tasks_manager.last_api_check
        }
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_data() -> Dict[str, Any]:
    """
    获取性能检测结果
    
    Returns:
        最新的性能检测结果
    """
    try:
        from app.core.background_tasks import background_tasks_manager
        
        if not background_tasks_manager.last_performance_test:
            return {
                "status": "pending",
                "message": "Performance test not yet performed (scheduled at T+30min)"
            }
        
        return {
            "status": "ok",
            "data": background_tasks_manager.last_performance_test
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preload-status")
async def get_preload_status() -> Dict[str, Any]:
    """
    获取内存预加载状态
    
    Returns:
        预加载状态和详情
    """
    try:
        from app.core.background_tasks import background_tasks_manager
        
        return {
            "completed": background_tasks_manager.preload_completed,
            "preload_time": background_tasks_manager.preload_time.isoformat() if background_tasks_manager.preload_time else None,
            "health_status": background_tasks_manager.health_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get preload status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-health-check")
async def trigger_health_check() -> Dict[str, Any]:
    """
    手动触发健康检测
    
    Returns:
        触发结果
    """
    try:
        from app.core.background_tasks import background_tasks_manager
        import asyncio
        
        # 创建异步任务执行检测
        asyncio.create_task(background_tasks_manager._check_api_and_tools())
        
        return {
            "status": "triggered",
            "message": "Health check started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-performance-test")
async def trigger_performance_test() -> Dict[str, Any]:
    """
    手动触发性能测试
    
    Returns:
        触发结果
    """
    try:
        from app.core.background_tasks import background_tasks_manager
        import asyncio
        
        # 创建异步任务执行测试
        asyncio.create_task(background_tasks_manager._run_performance_test())
        
        return {
            "status": "triggered",
            "message": "Performance test started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger performance test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
