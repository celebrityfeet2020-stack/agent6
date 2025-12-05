"""
M3 Agent System - State Manager (v6.4)
全局状态管理器,使用单例模式确保跨模块状态共享
"""
import logging
from typing import Any, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class StateManager:
    """
    单例状态管理器
    
    解决v6.3.2的问题:
    - 跨模块状态共享失败
    - background_tasks更新的app_state无法被API访问
    
    使用方法:
        from app.core.state_manager import StateManager
        
        state_mgr = StateManager()
        state_mgr.set("tools", tools_list)
        tools = state_mgr.get("tools", [])
    """
    
    _instance: Optional['StateManager'] = None
    _lock: Lock = Lock()
    _state: Dict[str, Any] = {}
    
    def __new__(cls):
        """确保只有一个实例"""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize_state()
                    logger.info(f"[StateManager] Singleton instance created (ID: {id(cls._instance)})")
        return cls._instance
    
    def _initialize_state(self):
        """初始化状态"""
        self._state = {
            "browser_pool": None,
            "tools": [],
            "llm_with_tools": None,
            "app_graph": None,
            # 新增字段
            "tools_loaded": False,
            "tools_load_time": None,
        }
        logger.info("[StateManager] State initialized")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取状态值
        
        Args:
            key: 状态键
            default: 默认值
            
        Returns:
            状态值或默认值
        """
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置状态值
        
        Args:
            key: 状态键
            value: 状态值
        """
        self._state[key] = value
        logger.info(f"[StateManager] Set {key} = {type(value).__name__} (len={len(value) if hasattr(value, '__len__') else 'N/A'})")
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有状态(副本)
        
        Returns:
            状态字典的副本
        """
        return self._state.copy()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        批量更新状态
        
        Args:
            updates: 要更新的键值对
        """
        for key, value in updates.items():
            self.set(key, value)
    
    def clear(self) -> None:
        """清空所有状态"""
        self._state.clear()
        logger.warning("[StateManager] All state cleared")
    
    def __repr__(self) -> str:
        """返回状态的字符串表示"""
        return f"<StateManager(id={id(self)}, keys={list(self._state.keys())})>"


# 全局单例实例(可选,方便导入)
state_manager = StateManager()
