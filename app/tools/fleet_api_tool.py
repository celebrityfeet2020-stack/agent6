"""
Fleet API Tool - 记忆同步工具
用于与D5航母的Fleet API进行记忆同步
"""
from langchain_core.tools import BaseTool
from pydantic import Field
import requests
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class FleetAPITool(BaseTool):
    """
    Fleet API工具 - 与D5航母进行记忆同步
    
    支持的操作:
    - sync_memory: 同步当前对话记忆到D5航母
    - retrieve_memory: 从D5航母检索历史记忆
    - list_memories: 列出所有已同步的记忆
    - delete_memory: 删除指定的记忆
    """
    
    name: str = "fleet_api"
    description: str = """Sync conversation memory with D5 Fleet API.
    Input should be a JSON string with 'action' and optional parameters.
    Actions: sync_memory, retrieve_memory, list_memories, delete_memory
    Example: {"action": "sync_memory", "session_id": "session_123", "content": "Important conversation context"}"""
    
    fleet_api_base_url: str = Field(
        default_factory=lambda: os.getenv("FLEET_API_BASE_URL", "http://d5-fleet:8080/api/v1")
    )
    fleet_api_key: str = Field(
        default_factory=lambda: os.getenv("FLEET_API_KEY", "")
    )
    
    def _run(self, query: str) -> str:
        """
        执行Fleet API操作
        
        Args:
            query: JSON字符串，包含action和参数
            
        Returns:
            操作结果的JSON字符串
        """
        try:
            # 解析输入
            params = json.loads(query) if isinstance(query, str) else query
            action = params.get("action")
            
            if not action:
                return json.dumps({"success": False, "error": "Missing 'action' parameter"})
            
            # 检查API配置
            if not self.fleet_api_key:
                return json.dumps({
                    "success": False,
                    "error": "FLEET_API_KEY environment variable not set. Please configure Fleet API credentials."
                })
            
            # 执行对应的操作
            if action == "sync_memory":
                result = self._sync_memory(params)
            elif action == "retrieve_memory":
                result = self._retrieve_memory(params)
            elif action == "list_memories":
                result = self._list_memories(params)
            elif action == "delete_memory":
                result = self._delete_memory(params)
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
    
    def _get_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        return {
            "Authorization": f"Bearer {self.fleet_api_key}",
            "Content-Type": "application/json"
        }
    
    def _sync_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步记忆到D5航母
        
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
            
            # 构造请求数据
            payload = {
                "session_id": session_id,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "source": "agent6"
            }
            
            # 发送同步请求
            response = requests.post(
                f"{self.fleet_api_base_url}/memory/sync",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Memory synced successfully",
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Fleet API returned status {response.status_code}: {response.text}"
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Sync failed: {str(e)}"
            }
    
    def _retrieve_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        从D5航母检索记忆
        
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
            
            # 构造查询参数
            query_params = {}
            if session_id:
                query_params["session_id"] = session_id
            if memory_id:
                query_params["memory_id"] = memory_id
            
            # 发送检索请求
            response = requests.get(
                f"{self.fleet_api_base_url}/memory/retrieve",
                headers=self._get_headers(),
                params=query_params,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Memory retrieved successfully",
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Fleet API returned status {response.status_code}: {response.text}"
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Retrieve failed: {str(e)}"
            }
    
    def _list_memories(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出所有已同步的记忆
        
        Args:
            params: 可选的过滤参数
            
        Returns:
            记忆列表
        """
        try:
            # 构造查询参数
            query_params = {
                "source": "agent6",
                "limit": params.get("limit", 50),
                "offset": params.get("offset", 0)
            }
            
            # 发送列表请求
            response = requests.get(
                f"{self.fleet_api_base_url}/memory/list",
                headers=self._get_headers(),
                params=query_params,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Memories listed successfully",
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Fleet API returned status {response.status_code}: {response.text}"
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"List failed: {str(e)}"
            }
    
    def _delete_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除指定的记忆
        
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
            
            # 发送删除请求
            response = requests.delete(
                f"{self.fleet_api_base_url}/memory/{memory_id}",
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Memory {memory_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Fleet API returned status {response.status_code}: {response.text}"
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Delete failed: {str(e)}"
            }
