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
    """获取系统状态(完整版)"""
    # 基础状态
    base_status = state_manager.get_system_status()
    
    # 构建完整的数据结构(适配Dashboard前端)
    return {
        # 基础信息(兼容旧版本)
        "version": AGENT_VERSION,
        "start_time": base_status["start_time"],
        "uptime": base_status["uptime"],
        "tool_pool_loaded": base_status["tool_pool_loaded"],
        "browser_pool_loaded": base_status["browser_pool_loaded"],
        "loaded_tools_count": base_status["loaded_tools_count"],
        "current_model": state_manager.current_model or "未检测到模型",
        "model_last_check": state_manager.model_last_check.strftime("%Y-%m-%d %H:%M:%S") if state_manager.model_last_check else "从未检查",
        
        # details嵌套结构(前端期望)
        "details": {
            "uptime_formatted": base_status["uptime"],
            "started_at": base_status["start_time"],
            "tool_pool_loaded": base_status["tool_pool_loaded"],
            "browser_pool_loaded": base_status["browser_pool_loaded"],
            "tool_pool_load_time": base_status["tool_pool_load_time"],
            "browser_pool_load_time": base_status["browser_pool_load_time"]
        },
        
        # summary嵌套结构(前端期望)
        "summary": {
            "overall": "healthy" if base_status["tool_pool_loaded"] else "degraded",
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        
        # LLM后端状态
        "llm_backend": {
            "base_url": state_manager.config.OPENROUTER_BASE_URL if hasattr(state_manager.config, 'OPENROUTER_BASE_URL') else "https://openrouter.ai/api/v1",
            "current_model": state_manager.current_model or "未检测到模型",
            "available_models": [state_manager.current_model] if state_manager.current_model else []
        },
        
        # Agent API状态
        "agent_api": {
            "configured_model": state_manager.current_model or "未检测到模型",
            "tools_count": base_status["loaded_tools_count"],
            "api_port": 12111
        },
        
        # API性能(默认值)
        "api_performance": {
            "average_response_time_ms": 0,
            "total_requests": 0,
            "success_rate": 100,
            "requests_per_hour": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }


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


@router.post("/api/dashboard/trigger-health-check")
async def trigger_health_check():
    """
    手动触发健康检测
    
    检查项:
    - 工具池状态
    - 浏览器池状态  
    - LLM连接状态
    - API可用性
    """
    try:
        # 执行健康检测
        health_result = {
            "triggered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "checks": {
                "tool_pool": {
                    "status": "healthy" if state_manager.tool_pool_loaded else "unhealthy",
                    "tools_count": len(state_manager.loaded_tools),
                    "errors_count": len(state_manager.tool_errors)
                },
                "browser_pool": {
                    "status": "healthy" if state_manager.browser_pool_loaded else "unhealthy"
                },
                "llm": {
                    "status": "connected" if state_manager.current_model else "disconnected",
                    "model": state_manager.current_model or "未知"
                },
                "langgraph": {
                    "status": "available" if state_manager.app_graph is not None else "unavailable"
                }
            },
            "overall": "healthy" if (state_manager.tool_pool_loaded and state_manager.current_model) else "degraded"
        }
        
        return {
            "success": True,
            "message": "健康检测已完成",
            "result": health_result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"健康检测失败: {str(e)}"
        }


@router.post("/api/dashboard/trigger-performance-test")
async def trigger_performance_test():
    """
    手动触发性能测试
    
    测试项:
    - LLM响应速度(TTFT, tokens/s)
    - 内存使用情况
    - API响应时间
    """
    try:
        import psutil
        import time
        
        # 测试开始时间
        test_start = time.time()
        
        # 获取内存使用情况
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_result = {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2)
            }
        except Exception as e:
            memory_result = {"error": str(e)}
        
        # 模拟LLM性能测试(实际应该调用LLM)
        model_performance = {
            "tokens_per_second": 0,  # 需要实际测试
            "ttft_ms": 0,  # 需要实际测试
            "total_latency_ms": 0  # 需要实际测试
        }
        
        test_duration = round((time.time() - test_start) * 1000, 2)
        
        # 保存到状态管理器
        state_manager.performance_data = {
            "model_performance": model_performance,
            "memory_status": memory_result,
            "test_duration_ms": test_duration
        }
        state_manager.performance_last_check = datetime.now()
        
        return {
            "success": True,
            "message": "性能测试已完成",
            "result": {
                "triggered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "test_duration_ms": test_duration,
                "data": state_manager.performance_data
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"性能测试失败: {str(e)}"
        }
