"""
Agent6 全局状态管理器 (单例模式)
所有模块共享同一个状态实例,彻底解决状态隔离问题
"""
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import TIMEZONE

class StateManager:
    """全局状态管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """确保全局只有一个实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化状态管理器"""
        if self._initialized:
            return
        
        # 系统状态
        self.system_start_time = datetime.now()
        self.tool_pool_loaded = False
        self.browser_pool_loaded = False
        self.tool_pool_load_time: Optional[datetime] = None
        self.browser_pool_load_time: Optional[datetime] = None
        
        # LangGraph核心工作流
        self.app_graph = None  # 将在启动时由workflow模块设置
        
        # 模型状态
        self.current_model: Optional[str] = None
        self.model_status: Dict[str, Any] = {}
        self.model_last_check: Optional[datetime] = None
        
        # 性能数据
        self.performance_data: Dict[str, Any] = {}
        self.performance_last_check: Optional[datetime] = None
        
        # 工具池状态
        self.loaded_tools: Dict[str, Any] = {}
        self.tool_errors: Dict[str, str] = {}
        
        # 浏览器池状态
        self.browser_pool_status: Dict[str, Any] = {}
        
        # 上下文统计
        self.context_stats: Dict[str, Any] = {
            "current_tokens": 0,
            "max_tokens": 0,
            "compression_count": 0,
            "last_compression_time": None
        }
        
        # 聊天室会话
        self.chat_sessions: Dict[str, Any] = {}
        
        # 应用状态字典(用于存储LLM和工具)
        self.app_state: Dict[str, Any] = {
            "llm_with_tools": None,
            "tools": [],
            "browser_pool": None
        }
        
        self._initialized = True
        print(f"✅ StateManager初始化完成 - 启动时间: {self.system_start_time}")
    
    # ==================== 系统状态方法 ====================
    
    def get_uptime(self) -> str:
        """获取系统运行时间"""
        delta = datetime.now() - self.system_start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}小时{minutes}分钟{seconds}秒"
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取完整的系统状态"""
        return {
            "version": "Agent 6",
            "start_time": self.system_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": self.get_uptime(),
            "tool_pool_loaded": self.tool_pool_loaded,
            "browser_pool_loaded": self.browser_pool_loaded,
            "tool_pool_load_time": self.tool_pool_load_time.strftime("%Y-%m-%d %H:%M:%S") if self.tool_pool_load_time else None,
            "browser_pool_load_time": self.browser_pool_load_time.strftime("%Y-%m-%d %H:%M:%S") if self.browser_pool_load_time else None,
            "current_model": self.current_model,
            "loaded_tools_count": len(self.loaded_tools),
            "tool_errors_count": len(self.tool_errors)
        }
    
    # ==================== 模型状态方法 ====================
    
    def update_model_status(self, model_name: str, status: Dict[str, Any]):
        """更新模型状态"""
        self.current_model = model_name
        self.model_status = status
        self.model_last_check = datetime.now()
    
    # ==================== 工具池方法 ====================
    
    def mark_tool_pool_loaded(self, tools: Dict[str, Any]):
        """标记工具池已加载"""
        self.tool_pool_loaded = True
        self.tool_pool_load_time = datetime.now()
        self.loaded_tools = tools
        print(f"✅ 工具池加载完成 - {len(tools)}个工具")
    
    def mark_browser_pool_loaded(self, status: Dict[str, Any]):
        """标记浏览器池已加载"""
        self.browser_pool_loaded = True
        self.browser_pool_load_time = datetime.now()
        self.browser_pool_status = status
        print(f"✅ 浏览器池加载完成")
    
    # ==================== LangGraph方法 ====================
    
    def set_app_graph(self, graph):
        """设置LangGraph工作流实例"""
        self.app_graph = graph
        print(f"✅ LangGraph工作流已加载到全局状态")
    
    def get_app_graph(self):
        """获取LangGraph工作流实例"""
        if self.app_graph is None:
            raise RuntimeError("LangGraph工作流尚未初始化")
        return self.app_graph
    
    # ==================== 上下文统计方法 ====================
    
    def update_context_stats(self, current_tokens: int, max_tokens: int):
        """更新上下文统计"""
        self.context_stats["current_tokens"] = current_tokens
        self.context_stats["max_tokens"] = max_tokens
    
    def increment_compression_count(self):
        """增加压缩次数"""
        self.context_stats["compression_count"] += 1
        self.context_stats["last_compression_time"] = datetime.now()
    
    def get_context_stats(self) -> Dict[str, Any]:
        """获取上下文统计"""
        return self.context_stats.copy()


# 创建全局单例实例
state_manager = StateManager()
