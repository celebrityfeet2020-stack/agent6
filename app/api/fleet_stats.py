"""
Fleet记忆统计API
"""
from fastapi import APIRouter
from typing import Dict, Any

from app.core.fleet_memory_db import FleetMemoryDB

router = APIRouter()


@router.get("/api/monitoring/fleet/stats")
async def get_fleet_stats() -> Dict[str, Any]:
    """
    获取Fleet记忆库统计信息
    
    Returns:
        统计信息
    """
    try:
        fleet_db = FleetMemoryDB()
        stats = fleet_db.get_stats()
        return stats
    except Exception as e:
        return {
            "total_memories": 0,
            "synced_memories": 0,
            "unsynced_memories": 0,
            "total_sessions": 0,
            "latest_memory_timestamp": None,
            "sync_rate": "0%",
            "storage_size_bytes": 0,
            "storage_size_mb": 0,
            "storage_size_gb": 0,
            "storage_limit_gb": 500,
            "storage_usage_percent": 0,
            "storage_is_full": False,
            "error": str(e)
        }
