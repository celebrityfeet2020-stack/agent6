"""
管理面板API
提供系统状态、工具池状态、性能数据等信息
"""
from fastapi import APIRouter
from datetime import datetime
from app.state import state_manager
from app.config import AGENT_VERSION, MAX_CONTEXT_LENGTH, COMPRESSION_TRIGGER_TOKENS

router = APIRouter()


@router.get("/api/dashboard/system_status")
async def get_system_status():
    """获取系统状态"""
    status = state_manager.get_system_status()
    
    # 添加额外信息
    status["version"] = AGENT_VERSION
    status["current_model"] = state_manager.current_model or "未检测到模型"
    status["model_last_check"] = state_manager.model_last_check.strftime("%Y-%m-%d %H:%M:%S") if state_manager.model_last_check else "从未检查"
    
    return status


@router.get("/api/dashboard/tool_pool_status")
async def get_tool_pool_status():
    """获取工具池状态"""
    return {
        "loaded": state_manager.tool_pool_loaded,
        "load_time": state_manager.tool_pool_load_time.strftime("%Y-%m-%d %H:%M:%S") if state_manager.tool_pool_load_time else None,
        "tools_count": len(state_manager.loaded_tools),
        "tools": list(state_manager.loaded_tools.keys()),
        "errors_count": len(state_manager.tool_errors),
        "errors": state_manager.tool_errors
    }


@router.get("/api/dashboard/browser_pool_status")
async def get_browser_pool_status():
    """获取浏览器池状态"""
    return {
        "loaded": state_manager.browser_pool_loaded,
        "load_time": state_manager.browser_pool_load_time.strftime("%Y-%m-%d %H:%M:%S") if state_manager.browser_pool_load_time else None,
        "status": state_manager.browser_pool_status
    }


@router.get("/api/dashboard/performance_data")
async def get_performance_data():
    """获取性能数据"""
    return {
        "data": state_manager.performance_data,
        "last_check": state_manager.performance_last_check.strftime("%Y-%m-%d %H:%M:%S") if state_manager.performance_last_check else "从未检查"
    }


@router.get("/api/dashboard/context_config")
async def get_context_config():
    """获取上下文配置"""
    return {
        "max_context_length": MAX_CONTEXT_LENGTH,
        "compression_threshold": COMPRESSION_TRIGGER_TOKENS,
        "compression_threshold_percent": 85,
        "current_stats": state_manager.get_context_stats()
    }


@router.get("/api/dashboard/model_status")
async def get_model_status():
    """获取模型状态"""
    return {
        "current_model": state_manager.current_model or "未检测到模型",
        "status": state_manager.model_status,
        "last_check": state_manager.model_last_check.strftime("%Y-%m-%d %H:%M:%S") if state_manager.model_last_check else "从未检查"
    }
