"""
增强型监控API (Enhanced Monitoring API)
提供实时日志流、工具使用统计、配置查看器等高级监控功能
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict, deque
import os

from app.state import state_manager
from app.config import *

router = APIRouter()

# 日志缓冲区(最多保留1000条)
log_buffer = deque(maxlen=1000)

# 工具使用统计
tool_usage_stats: Dict[str, int] = defaultdict(int)
tool_last_used: Dict[str, str] = {}


class LogEntry(BaseModel):
    """日志条目"""
    timestamp: str
    level: str
    message: str
    source: Optional[str] = None


class ToolUsageStat(BaseModel):
    """工具使用统计"""
    tool_name: str
    usage_count: int
    last_used: Optional[str] = None


def add_log(level: str, message: str, source: str = "system"):
    """添加日志到缓冲区"""
    log_entry = LogEntry(
        timestamp=datetime.now().isoformat(),
        level=level,
        message=message,
        source=source
    )
    log_buffer.append(log_entry.dict())


def record_tool_usage(tool_name: str):
    """记录工具使用"""
    tool_usage_stats[tool_name] += 1
    tool_last_used[tool_name] = datetime.now().isoformat()


@router.websocket("/api/monitoring/logs/stream")
async def websocket_logs_stream(websocket: WebSocket):
    """
    WebSocket实时日志流
    
    客户端连接后，会收到：
    1. 历史日志（最近100条）
    2. 实时新日志
    """
    await websocket.accept()
    
    try:
        # 发送历史日志
        history = list(log_buffer)[-100:]  # 最近100条
        await websocket.send_json({
            "type": "history",
            "logs": history,
            "count": len(history)
        })
        
        # 持续发送新日志
        last_sent_index = len(log_buffer)
        
        while True:
            # 检查是否有新日志
            current_index = len(log_buffer)
            if current_index > last_sent_index:
                # 发送新日志
                new_logs = list(log_buffer)[last_sent_index:current_index]
                for log in new_logs:
                    await websocket.send_json({
                        "type": "new_log",
                        "log": log
                    })
                last_sent_index = current_index
            
            # 短暂休眠
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        print("WebSocket客户端断开连接")
    except Exception as e:
        print(f"WebSocket错误: {e}")


@router.get("/api/monitoring/logs/recent")
async def get_recent_logs(limit: int = 100, level: Optional[str] = None):
    """
    获取最近的日志
    
    Args:
        limit: 返回的日志条数
        level: 过滤日志级别 (INFO, WARNING, ERROR)
    """
    logs = list(log_buffer)[-limit:]
    
    # 如果指定了级别，进行过滤
    if level:
        logs = [log for log in logs if log.get("level") == level.upper()]
    
    return {
        "logs": logs,
        "count": len(logs),
        "total_in_buffer": len(log_buffer)
    }


@router.get("/api/monitoring/tools/usage", response_model=List[ToolUsageStat])
async def get_tool_usage_stats():
    """获取工具使用统计"""
    stats = []
    
    for tool_name, count in tool_usage_stats.items():
        stats.append(ToolUsageStat(
            tool_name=tool_name,
            usage_count=count,
            last_used=tool_last_used.get(tool_name)
        ))
    
    # 按使用次数降序排序
    stats.sort(key=lambda x: x.usage_count, reverse=True)
    
    return stats


@router.get("/api/monitoring/tools/usage/summary")
async def get_tool_usage_summary():
    """获取工具使用统计摘要"""
    total_usage = sum(tool_usage_stats.values())
    
    # 找出最常用的工具
    most_used = None
    if tool_usage_stats:
        most_used_tool = max(tool_usage_stats.items(), key=lambda x: x[1])
        most_used = {
            "tool_name": most_used_tool[0],
            "usage_count": most_used_tool[1],
            "percentage": round(most_used_tool[1] / total_usage * 100, 2) if total_usage > 0 else 0
        }
    
    return {
        "total_usage": total_usage,
        "unique_tools_used": len(tool_usage_stats),
        "most_used_tool": most_used,
        "stats_since": state_manager.system_start_time.isoformat()
    }


@router.get("/api/monitoring/config/view")
async def view_system_config():
    """
    查看系统配置
    
    返回config.py中的所有关键配置
    """
    config_data = {
        "agent_info": {
            "version": AGENT_VERSION,
            "timezone": TIMEZONE,
            "api_port": API_PORT
        },
        "model_config": {
            "model_host": MODEL_HOST,
            "model_port": MODEL_PORT,
            "temperature": 0.7  # 默认值
        },
        "timing_config": {
            "tool_pool_preload_delay": f"{TOOL_POOL_PRELOAD_DELAY}秒 ({TOOL_POOL_PRELOAD_DELAY//60}分钟)",
            "tool_pool_check_interval": f"{TOOL_POOL_CHECK_INTERVAL}秒 ({TOOL_POOL_CHECK_INTERVAL//60}分钟)",
            "browser_pool_preload_delay": f"{BROWSER_POOL_PRELOAD_DELAY}秒 ({BROWSER_POOL_PRELOAD_DELAY//60}分钟)",
            "performance_check_delay": f"{PERFORMANCE_CHECK_DELAY}秒 ({PERFORMANCE_CHECK_DELAY//60}分钟)",
            "performance_check_interval": f"{PERFORMANCE_CHECK_INTERVAL}秒 ({PERFORMANCE_CHECK_INTERVAL//60}分钟)"
        },
        "context_config": {
            "max_context_length": MAX_CONTEXT_LENGTH,
            "compression_trigger_tokens": COMPRESSION_TRIGGER_TOKENS,
            "compression_threshold": COMPRESSION_THRESHOLD
        },
        "cors_config": {
            "enable_cors": ENABLE_CORS,
            "cors_origins": CORS_ORIGINS
        },
        "environment_variables": {
            "rpa_host_string": os.getenv("RPA_HOST_STRING", "未设置"),
            "fleet_api_base_url": os.getenv("FLEET_API_BASE_URL", "未设置"),
            "fleet_api_key": "***已设置***" if os.getenv("FLEET_API_KEY") else "未设置",
            "telegram_bot_token": "***已设置***" if os.getenv("TELEGRAM_BOT_TOKEN") else "未设置"
        }
    }
    
    return config_data


@router.get("/api/monitoring/system/health")
async def get_system_health():
    """
    获取系统健康状态
    
    包括：
    - 系统运行时间
    - 工具池状态
    - 模型池状态
    - 浏览器池状态
    - 内存使用情况（如果可用）
    """
    import psutil
    
    # 计算运行时间
    uptime = datetime.now() - state_manager.system_start_time
    uptime_str = str(uptime).split('.')[0]  # 去掉微秒
    
    # 获取内存使用情况
    try:
        memory = psutil.virtual_memory()
        memory_info = {
            "total_mb": round(memory.total / 1024 / 1024, 2),
            "used_mb": round(memory.used / 1024 / 1024, 2),
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "percent": memory.percent
        }
    except Exception:
        memory_info = {"error": "无法获取内存信息"}
    
    # 获取CPU使用情况
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
    except Exception:
        cpu_percent = None
    
    # 构建完整的数据结构(兼容前端期望)
    return {
        # 基础状态(兼容旧版本)
        "status": "healthy",
        "uptime": uptime_str,
        "uptime_seconds": int(uptime.total_seconds()),
        "pools": {
            "tool_pool": {
                "loaded": state_manager.tool_pool_loaded,
                "load_time": state_manager.tool_pool_load_time.isoformat() if state_manager.tool_pool_load_time else None,
                "tools_count": len(state_manager.loaded_tools),
                "errors_count": len(state_manager.tool_errors)
            },
            "model_pool": {
                "loaded": state_manager.model_pool_loaded,
                "load_time": state_manager.model_pool_load_time.isoformat() if state_manager.model_pool_load_time else None
            },
            "browser_pool": {
                "loaded": state_manager.browser_pool_loaded,
                "load_time": state_manager.browser_pool_load_time.isoformat() if state_manager.browser_pool_load_time else None
            }
        },
        "resources": {
            "memory": memory_info,
            "cpu_percent": cpu_percent
        },
        "timestamp": datetime.now().isoformat(),
        
        # 前端期望的数据结构
        "data": {
            "tools": {
                "count": len(state_manager.loaded_tools),
                "status": "available" if state_manager.tool_pool_loaded else "unavailable"
            },
            "apis": {
                "fleet": "available",  # Fleet API总是可用的
                "langgraph": "available" if state_manager.app_graph is not None else "unavailable",
                "llm": {
                    "status": "connected" if state_manager.current_model else "disconnected",
                    "model": state_manager.current_model or "未知"
                }
            }
        }
    }


@router.post("/api/monitoring/logs/clear")
async def clear_logs():
    """清空日志缓冲区"""
    log_buffer.clear()
    add_log("INFO", "日志缓冲区已清空", "monitoring_api")
    
    return {
        "success": True,
        "message": "日志缓冲区已清空"
    }


@router.post("/api/monitoring/tools/usage/reset")
async def reset_tool_usage_stats():
    """重置工具使用统计"""
    tool_usage_stats.clear()
    tool_last_used.clear()
    add_log("INFO", "工具使用统计已重置", "monitoring_api")
    
    return {
        "success": True,
        "message": "工具使用统计已重置"
    }


# 初始化时添加一条日志
add_log("INFO", "监控API模块已加载", "monitoring_api")
