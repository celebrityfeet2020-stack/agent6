"""
Fleet API Tool v2 - 记忆同步工具(支持本地SQLite降级)
用于与D5航母的Fleet API进行记忆同步,当Fleet API不可用时自动降级到本地SQLite存储
"""
from langchain_core.tools import BaseTool
from pydantic import Field
import requests
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.fleet_memory_db import fleet_memory_db


class FleetAPIToolV2(BaseTool):
    """
    Fleet API工具 v2 - 与D5航母进行记忆同步(支持本地降级)
    
    支持的操作:
    - sync_memory: 同步当前对话记忆(优先Fleet API,降级到本地SQLite)
    - retrieve_memory: 检索历史记忆(优先Fleet API,降级到本地SQLite)
    - list_memories: 列出所有记忆(优先Fleet API,降级到本地SQLite)
    - delete_memory: 删除指定记忆(优先Fleet API,降级到本地SQLite)
    - get_stats: 获取记忆统计信息
    - sync_to_fleet: 手动同步本地记忆到Fleet API
    """
    
    name: str = "fleet_api"
    description: str = """Sync conversation memory with D5 Fleet API or local SQLite database.
    Input should be a JSON string with 'action' and optional parameters.
    Actions: sync_memory, retrieve_memory, list_memories, delete_memory, get_stats, sync_to_fleet
    Example: {"action": "sync_memory", "session_id": "session_123", "content": "Important conversation context"}"""
    
    fleet_api_base_url: str = Field(
        default_factory=lambda: os.getenv("FLEET_API_BASE_URL", "")
    )
    fleet_api_key: str = Field(
        default_factory=lambda: os.getenv("FLEET_API_KEY", "")
    )
    
    def _run(self, query: str) -> str:
        """
        执行Fleet API操作
        
        Args:
            query: JSON字符串,包含action和参数
            
        Returns:
            操作结果的JSON字符串
        """
        try:
            # 解析输入
            params = json.loads(query) if isinstance(query, str) else query
            action = params.get("action")
            
            if not action:
                return json.dumps({"success": False, "error": "Missing 'action' parameter"})
            
            # 执行对应的操作
            if action == "sync_memory":
                result = self._sync_memory(params)
            elif action == "retrieve_memory":
                result = self._retrieve_memory(params)
            elif action == "list_memories":
                result = self._list_memories(params)
            elif action == "delete_memory":
                result = self._delete_memory(params)
            elif action == "get_stats":
                result = self._get_stats(params)
            elif action == "sync_to_fleet":
                result = self._sync_to_fleet(params)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return json.dumps(result, ensure_ascii=False)
            
        except json.JSONDecodeError as e:
            return json.dumps({"success": False, "error": f"Invalid JSON input: {str(e)}"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    async def _arun(self, query: str) -> str:
        """异步执行 (当前使用同步实现)"""
        return self._run(query)
    
    def _is_fleet_api_available(self) -> bool:
        """检查Fleet API是否可用"""
        if not self.fleet_api_base_url or not self.fleet_api_key:
            return False
        
        try:
            # 尝试ping Fleet API
            response = requests.get(
                f"{self.fleet_api_base_url}/health",
                headers={"Authorization": f"Bearer {self.fleet_api_key}"},
                timeout=3
            )
            return response.status_code == 200
        except:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        return {
            "Authorization": f"Bearer {self.fleet_api_key}",
            "Content-Type": "application/json"
        }
    
    def _sync_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步记忆(优先Fleet API,降级到本地SQLite)
        
        Args:
            params: 包含session_id, content等参数
            
        Returns:
            同步结果
        """
        try:
            session_id = params.get("session_id")
            content = params.get("content")
            metadata = params.get("metadata", {})
            
            if not session_id or not content:
                return {
                    "success": False,
                    "error": "session_id and content are required"
                }
            
            # 1. 先保存到本地SQLite
            memory_id = fleet_memory_db.add_memory(
                session_id=session_id,
                content=content,
                metadata=metadata
            )
            
            # 2. 尝试同步到Fleet API
            if self._is_fleet_api_available():
                try:
                    payload = {
                        "session_id": session_id,
                        "content": content,
                        "metadata": metadata,
                        "timestamp": datetime.now().isoformat(),
                        "source": "agent6"
                    }
                    
                    response = requests.post(
                        f"{self.fleet_api_base_url}/memory/sync",
                        headers=self._get_headers(),
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        fleet_data = response.json()
                        fleet_memory_id = fleet_data.get("memory_id", memory_id)
                        
                        # 标记为已同步
                        fleet_memory_db.mark_as_synced(memory_id, fleet_memory_id)
                        
                        # 同步成功后删除本地数据(节省存储空间)
                        fleet_memory_db.delete_memory(memory_id)
                        
                        return {
                            "success": True,
                            "message": "Memory synced to Fleet API successfully",
                            "storage": "fleet_api",
                            "memory_id": memory_id,
                            "fleet_memory_id": fleet_memory_id
                        }
                except Exception as e:
                    # Fleet API同步失败,但本地已保存
                    return {
                        "success": True,
                        "message": f"Memory saved locally, Fleet API sync failed: {str(e)}",
                        "storage": "local_sqlite",
                        "memory_id": memory_id,
                        "fleet_sync_status": "failed"
                    }
            else:
                # Fleet API不可用,仅本地存储
                return {
                    "success": True,
                    "message": "Memory saved to local SQLite (Fleet API unavailable)",
                    "storage": "local_sqlite",
                    "memory_id": memory_id,
                    "fleet_sync_status": "unavailable"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sync failed: {str(e)}"
            }
    
    def _retrieve_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        检索记忆(优先Fleet API,降级到本地SQLite)
        
        Args:
            params: 包含session_id或memory_id
            
        Returns:
            检索结果
        """
        try:
            session_id = params.get("session_id")
            memory_id = params.get("memory_id")
            
            if not session_id and not memory_id:
                return {
                    "success": False,
                    "error": "Either session_id or memory_id is required"
                }
            
            # 1. 尝试从Fleet API检索
            if self._is_fleet_api_available():
                try:
                    query_params = {}
                    if session_id:
                        query_params["session_id"] = session_id
                    if memory_id:
                        query_params["memory_id"] = memory_id
                    
                    response = requests.get(
                        f"{self.fleet_api_base_url}/memory/retrieve",
                        headers=self._get_headers(),
                        params=query_params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "message": "Memory retrieved from Fleet API",
                            "storage": "fleet_api",
                            "data": response.json()
                        }
                except Exception as e:
                    pass  # 降级到本地
            
            # 2. 从本地SQLite检索
            if memory_id:
                memory = fleet_memory_db.get_memory(memory_id)
                if memory:
                    return {
                        "success": True,
                        "message": "Memory retrieved from local SQLite",
                        "storage": "local_sqlite",
                        "data": memory
                    }
            elif session_id:
                memories = fleet_memory_db.get_session_memories(session_id, limit=100)
                return {
                    "success": True,
                    "message": f"Retrieved {len(memories)} memories from local SQLite",
                    "storage": "local_sqlite",
                    "data": memories
                }
            
            return {
                "success": False,
                "error": "Memory not found"
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Retrieve failed: {str(e)}"
            }
    
    def _list_memories(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出所有记忆(优先Fleet API,降级到本地SQLite)
        
        Args:
            params: 可选参数(limit, offset)
            
        Returns:
            记忆列表
        """
        try:
            limit = params.get("limit", 100)
            offset = params.get("offset", 0)
            
            # 1. 尝试从Fleet API列出
            if self._is_fleet_api_available():
                try:
                    response = requests.get(
                        f"{self.fleet_api_base_url}/memory/list",
                        headers=self._get_headers(),
                        params={"limit": limit, "offset": offset},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "message": "Memories listed from Fleet API",
                            "storage": "fleet_api",
                            "data": response.json()
                        }
                except Exception as e:
                    pass  # 降级到本地
            
            # 2. 从本地SQLite列出
            memories = fleet_memory_db.list_all_memories(limit=limit, offset=offset)
            return {
                "success": True,
                "message": f"Listed {len(memories)} memories from local SQLite",
                "storage": "local_sqlite",
                "data": memories
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"List failed: {str(e)}"
            }
    
    def _delete_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除记忆(同时删除Fleet API和本地SQLite)
        
        Args:
            params: 包含memory_id
            
        Returns:
            删除结果
        """
        try:
            memory_id = params.get("memory_id")
            
            if not memory_id:
                return {
                    "success": False,
                    "error": "memory_id is required"
                }
            
            results = []
            
            # 1. 尝试从Fleet API删除
            if self._is_fleet_api_available():
                try:
                    response = requests.delete(
                        f"{self.fleet_api_base_url}/memory/{memory_id}",
                        headers=self._get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        results.append("Deleted from Fleet API")
                except Exception as e:
                    results.append(f"Fleet API delete failed: {str(e)}")
            
            # 2. 从本地SQLite删除
            if fleet_memory_db.delete_memory(memory_id):
                results.append("Deleted from local SQLite")
            else:
                results.append("Not found in local SQLite")
            
            return {
                "success": True,
                "message": "; ".join(results),
                "memory_id": memory_id
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Delete failed: {str(e)}"
            }
    
    def _get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Args:
            params: 空参数
            
        Returns:
            统计信息
        """
        try:
            stats = fleet_memory_db.get_stats()
            return {
                "success": True,
                "message": "Statistics retrieved successfully",
                "data": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Get stats failed: {str(e)}"
            }
    
    def _sync_to_fleet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        手动同步本地记忆到Fleet API
        
        Args:
            params: 可选参数(limit)
            
        Returns:
            同步结果
        """
        try:
            if not self._is_fleet_api_available():
                return {
                    "success": False,
                    "error": "Fleet API is not available"
                }
            
            limit = params.get("limit", 100)
            
            # 获取未同步的记忆
            unsynced_memories = fleet_memory_db.get_unsynced_memories(limit=limit)
            
            if not unsynced_memories:
                return {
                    "success": True,
                    "message": "No unsynced memories found",
                    "synced_count": 0
                }
            
            synced_count = 0
            failed_count = 0
            
            for memory in unsynced_memories:
                try:
                    payload = {
                        "session_id": memory["session_id"],
                        "content": memory["content"],
                        "metadata": memory["metadata"],
                        "timestamp": memory["timestamp"],
                        "source": memory["source"]
                    }
                    
                    response = requests.post(
                        f"{self.fleet_api_base_url}/memory/sync",
                        headers=self._get_headers(),
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        fleet_data = response.json()
                        fleet_memory_id = fleet_data.get("memory_id", memory["id"])
                        fleet_memory_db.mark_as_synced(memory["id"], fleet_memory_id)
                        
                        # 同步成功后删除本地数据
                        fleet_memory_db.delete_memory(memory["id"])
                        
                        synced_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
            
            return {
                "success": True,
                "message": f"Synced {synced_count} memories, {failed_count} failed",
                "synced_count": synced_count,
                "failed_count": failed_count,
                "total_unsynced": len(unsynced_memories)
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sync to fleet failed: {str(e)}"
            }
