"""
M3 Agent System - Fleet Integration API
舰队集成接口：用于与D5管理航母和Temporal调度系统对接

版本: v2.5
状态: 预留框架，待第三、第四阶段实现
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import httpx
import time
import psutil
import os

router = APIRouter(prefix="/api/fleet", tags=["fleet"])

# ============================================
# 数据模型
# ============================================

class TaskRequest(BaseModel):
    """来自Temporal的任务请求"""
    task_id: str
    task_type: str  # code_generation, research, writing, analysis
    message: str  # 任务描述消息
    task_content: Optional[str] = None  # 可选，默认使用message
    priority: Union[str, int] = "normal"  # 支持字符串和整数
    deadline: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('priority')
    def normalize_priority(cls, v):
        """标准化优先级值"""
        if isinstance(v, int):
            # 将整数映射为字符串
            priority_map = {1: "low", 2: "normal", 3: "high", 4: "urgent"}
            return priority_map.get(v, "normal")
        return v
    
    @validator('task_content', always=True)
    def set_task_content(cls, v, values):
        """如果task_content为空，使用message"""
        return v or values.get('message')

class TaskStatus(BaseModel):
    """任务状态上报"""
    task_id: str
    status: str  # queued, running, completed, failed
    progress: int = 0  # 0-100
    current_step: Optional[str] = None
    error: Optional[str] = None

class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str
    search_type: str = "hybrid"  # vector, graph, hybrid
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class MemoryStoreRequest(BaseModel):
    """记忆存储请求"""
    content: str
    source: str  # 来源标识，如 "M3_task_12345"
    entities: Optional[List[str]] = None
    importance: float = 5.0  # 1-10
    metadata: Optional[Dict[str, Any]] = None

class TaskCompletion(BaseModel):
    """任务完成信息"""
    task_id: str
    result: Union[str, Dict[str, Any]]  # 支持字符串和字典
    execution_time: Optional[float] = None  # 执行时间（秒），可选

class TaskError(BaseModel):
    """任务错误信息"""
    task_id: str
    error: Optional[str] = None  # 兼容旧参数
    error_message: Optional[str] = None
    error_type: Optional[str] = "UnknownError"
    stack_trace: Optional[str] = None
    
    @validator('error_message', always=True)
    def set_error_message(cls, v, values):
        """如果error_message为空，使用error"""
        return v or values.get('error') or "Unknown error"

# ============================================
# Temporal任务管理接口（通用标准）
# ============================================

@router.post("/task/receive")
async def receive_task(task: TaskRequest):
    """
    接收来自Temporal的任务分配
    
    这是一个通用的Temporal Worker接口，遵循Temporal的任务分发标准。
    任何Temporal服务端都可以通过此接口向M3分配任务。
    
    TODO: 第四阶段实现完整逻辑
    - 将任务加入M3的任务队列
    - 根据任务类型选择合适的模型
    - 启动异步任务执行
    """
    print(f"[Fleet API] Received task: {task.task_id} ({task.task_type})")
    
    # 暂时返回接受状态（mock实现）
    return {
        "status": "accepted",
        "task_id": task.task_id,
        "estimated_time": 300,  # 秒
        "message": "Task queued successfully (mock)"
    }

@router.post("/task/status")
async def report_status(status: TaskStatus):
    """
    向Temporal上报任务执行状态
    
    这是一个通用的状态上报接口，M3会定期调用此接口向Temporal汇报进度。
    
    TODO: 第四阶段实现
    - 通过httpx调用Temporal的状态接收API
    - 处理网络异常和重试逻辑
    """
    print(f"[Fleet API] Status update: {status.task_id} - {status.status} ({status.progress}%)")
    
    # 暂时返回成功（mock实现）
    return {"status": "reported", "message": "Status reported successfully (mock)"}

@router.post("/task/complete")
async def complete_task(completion: TaskCompletion):
    """
    任务完成上报接口
    
    M3在任务执行完成后调用此接口向Temporal汇报结果。
    
    Args:
        completion: 任务完成信息
            - task_id: 任务ID
            - result: 任务结果（dict）
            - execution_time: 执行时间（秒）
    
    TODO: 第四阶段实现
    - 通过httpx调用Temporal的任务完成API
    - 处理网络异常和重试逻辑
    """
    print(f"[Fleet API] Task completed: {completion.task_id} (execution_time: {completion.execution_time}s)")
    
    # 暂时返回成功（mock实现）
    return {
        "task_id": completion.task_id,
        "status": "completed",
        "message": "Task completion recorded (mock)"
    }

@router.post("/task/error")
async def report_error(error: TaskError):
    """
    任务错误上报接口
    
    M3在任务执行失败时调用此接口向Temporal汇报错误。
    
    Args:
        error: 任务错误信息
            - task_id: 任务ID
            - error_message: 错误消息
            - error_type: 错误类型
            - stack_trace: 堆栈跟踪（可选）
    
    TODO: 第四阶段实现
    - 通过httpx调用Temporal的错误处理API
    - 处理网络异常和重试逻辑
    """
    print(f"[Fleet API] Task error: {error.task_id} - {error.error_type}: {error.error_message}")
    
    # 暂时返回成功（mock实现）
    return {
        "task_id": error.task_id,
        "status": "error_recorded",
        "message": "Task error recorded (mock)"
    }

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    查询任务状态
    
    供Temporal或其他服务查询M3上任务的执行状态。
    
    TODO: 第四阶段实现
    """
    return {
        "task_id": task_id,
        "status": "unknown",
        "message": "Task status query not implemented yet (mock)"
    }

# ============================================
# D5记忆系统接口（通用标准）
# ============================================

@router.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """
    从D5记忆系统搜索相关记忆
    
    这是一个通用的记忆检索接口，遵循HybridRAG的查询标准。
    支持向量检索、图谱查询和混合检索三种模式。
    
    TODO: 第三阶段实现
    - 通过httpx调用D5的记忆检索API
    - 处理不同的search_type（vector/graph/hybrid）
    - 解析并返回记忆结果
    
    接口标准：
    - 请求格式：遵循HybridRAG标准
    - 响应格式：统一的记忆对象列表
    - 支持过滤器：时间范围、来源、重要性等
    """
    print(f"[Fleet API] Memory search: {request.query} ({request.search_type})")
    
    # 暂时返回空列表（mock实现）
    return {
        "memories": [],
        "total": 0,
        "message": "Memory search not implemented yet (mock)"
    }

@router.post("/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """
    向D5记忆系统存储新记忆
    
    这是一个通用的记忆存储接口，M3在完成任务后会调用此接口将重要信息发送给D5。
    D5的80B模型会对这些记忆进行整理、去重和推理。
    
    TODO: 第三阶段实现
    - 通过httpx调用D5的记忆存储API
    - 自动提取实体和关键信息
    - 处理存储失败的重试逻辑
    
    接口标准：
    - 请求格式：遵循HybridRAG标准
    - 自动生成：timestamp, source标识
    - 返回：memory_id用于后续引用
    """
    print(f"[Fleet API] Store memory: {request.content[:50]}... (importance: {request.importance})")
    
    # 暂时返回mock的memory_id
    return {
        "memory_id": f"mem_mock_{datetime.now().timestamp()}",
        "status": "stored",
        "message": "Memory storage not implemented yet (mock)"
    }

@router.get("/memory/context/{task_id}")
async def get_task_context(task_id: str):
    """
    获取任务相关的上下文记忆
    
    在M3开始执行任务前，可以调用此接口从D5获取相关的历史记忆，
    帮助Agent更好地理解用户需求和偏好。
    
    TODO: 第三阶段实现
    """
    return {
        "task_id": task_id,
        "context": [],
        "message": "Context retrieval not implemented yet (mock)"
    }

# ============================================
# Agent注册和心跳（v2.7新增）
# ============================================

class AgentRegisterRequest(BaseModel):
    """
Agent注册请求"""
    agent_id: str
    hostname: str
    ip_address: Optional[str] = None
    tools: List[str] = []
    system_info: Optional[Dict[str, Any]] = None

class AgentHeartbeatRequest(BaseModel):
    """
Agent心跳请求"""
    agent_id: str
    status: str = "running"  # running, idle, busy, error
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    active_tasks: int = 0

@router.post("/agent/register")
async def register_agent(request: AgentRegisterRequest):
    """
    M3 Agent启动时注册到D5
    
    TODO: 将注册信息发送到D5
    """
    print(f"[Fleet API] Agent registered: {request.agent_id}")
    
    return {
        "status": "registered",
        "agent_id": request.agent_id,
        "message": "Agent registered successfully"
    }

@router.post("/agent/heartbeat")
async def agent_heartbeat(request: AgentHeartbeatRequest):
    """
    M3 Agent定期心跳（30秒）
    
    TODO: 将心跳信息发送到D5
    """
    # print(f"[Fleet API] Heartbeat from {request.agent_id}: {request.status}")
    
    return {
        "status": "ok",
        "message": "Heartbeat received"
    }

@router.get("/agent/status")
async def get_agent_status():
    """
    获取M3 Agent状态
    
    D5可以调用此接口查询M3的当前状态
    """
    return {
        "agent_id": os.getenv("AGENT_ID", "m3-unknown"),
        "status": "running",
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "uptime": int(time.time() - psutil.boot_time()),
        "active_tasks": 0  # TODO: 实现任务计数
    }

# ============================================
# 记忆同步状态（v2.7新增）
# ============================================

@router.get("/memory/sync/status")
async def get_memory_sync_status():
    """
    获取记忆同步状态
    
    返回本地缓冲区的统计信息和同步状态
    """
    from app.memory.memory_sync import get_buffer_stats
    
    stats = get_buffer_stats()
    
    return {
        "status": "active",
        "buffer_stats": stats,
        "sync_enabled": bool(stats.get("d5_url") and stats.get("d5_url") != "Not configured")
    }

@router.post("/memory/sync/trigger")
async def trigger_memory_sync():
    """
    手动触发记忆同步
    
    强制立即同步所有未同步的记录到D5
    """
    from app.memory.memory_sync import get_unsynced_records, sync_to_d5
    
    records = get_unsynced_records(limit=1000)  # 最多同步1000条
    
    if not records:
        return {
            "status": "no_data",
            "message": "No unsynced records found"
        }
    
    success = sync_to_d5(records)
    
    return {
        "status": "success" if success else "failed",
        "synced_count": len(records) if success else 0,
        "message": f"Synced {len(records)} records" if success else "Sync failed"
    }

# ============================================
# 健康检查
# ============================================

@router.get("/health")
async def fleet_health():
    """
    舰队集成模块健康检查
    """
    return {
        "status": "healthy",
        "module": "fleet_integration",
        "version": "2.9.0",
        "features": {
            "temporal_integration": "mock",
            "memory_integration": "active",
            "memory_sync": "active",
            "langgraph_api": "active",
            "rpa_tool": "active",
            "file_sync_tool": "active"
        },
        "message": "Fleet API endpoints are ready"
    }


@router.get("/memory/status")
async def get_memory_status_alias():
    """
    记忆同步状态检查（别名端点，指向/memory/sync/status）
    """
    return await get_memory_sync_status()
