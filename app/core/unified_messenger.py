"""
统一消息推送机制 (Unified Messenger)
所有模块通过此总线发送带有角色信息的消息到多维聊天室
"""
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import deque
import json
import logging

logger = logging.getLogger(__name__)


class Message:
    """统一消息格式"""
    
    def __init__(
        self,
        content: str,
        role_type: str,
        role_id: str,
        role_name: str,
        thread_id: str = "default",
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.role_type = role_type  # user, admin, n8_workflow, digital_human_guest, git_committer等
        self.role_id = role_id
        self.role_name = role_name
        self.thread_id = thread_id
        self.message_type = message_type  # text, tool_call, tool_result, system
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        self.message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "role_type": self.role_type,
            "role_id": self.role_id,
            "role_name": self.role_name,
            "thread_id": self.thread_id,
            "message_type": self.message_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class UnifiedMessenger:
    """统一消息总线"""
    
    def __init__(self):
        # WebSocket连接池 {thread_id: set of websocket connections}
        self.connections: Dict[str, Set] = {}
        
        # 消息历史缓冲区 {thread_id: deque of messages}
        self.message_history: Dict[str, deque] = {}
        
        # 默认线程ID
        self.default_thread_id = "default"
        
        # 每个线程最多保留的历史消息数
        self.max_history_per_thread = 500
        
        logger.info("✅ 统一消息总线已初始化")
    
    def register_connection(self, thread_id: str, websocket):
        """注册WebSocket连接"""
        if thread_id not in self.connections:
            self.connections[thread_id] = set()
        
        self.connections[thread_id].add(websocket)
        logger.info(f"📡 新连接注册到线程 {thread_id}, 当前连接数: {len(self.connections[thread_id])}")
    
    def unregister_connection(self, thread_id: str, websocket):
        """注销WebSocket连接"""
        if thread_id in self.connections:
            self.connections[thread_id].discard(websocket)
            logger.info(f"📡 连接从线程 {thread_id} 注销, 剩余连接数: {len(self.connections[thread_id])}")
            
            # 如果没有连接了，清理
            if not self.connections[thread_id]:
                del self.connections[thread_id]
    
    async def broadcast_message(self, message: Message):
        """
        广播消息到指定线程的所有连接
        
        Args:
            message: 消息对象
        """
        thread_id = message.thread_id
        
        # 保存到历史
        self._save_to_history(thread_id, message)
        
        # 如果没有连接，只保存历史
        if thread_id not in self.connections or not self.connections[thread_id]:
            logger.debug(f"线程 {thread_id} 没有活跃连接，消息已保存到历史")
            return
        
        # 广播到所有连接
        message_dict = message.to_dict()
        disconnected = set()
        
        for websocket in self.connections[thread_id]:
            try:
                await websocket.send_json({
                    "type": "message",
                    "data": message_dict
                })
            except Exception as e:
                logger.error(f"发送消息到WebSocket失败: {e}")
                disconnected.add(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            self.unregister_connection(thread_id, ws)
    
    def _save_to_history(self, thread_id: str, message: Message):
        """保存消息到历史缓冲区"""
        if thread_id not in self.message_history:
            self.message_history[thread_id] = deque(maxlen=self.max_history_per_thread)
        
        self.message_history[thread_id].append(message.to_dict())
    
    def get_history(self, thread_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取指定线程的历史消息
        
        Args:
            thread_id: 线程ID
            limit: 返回的消息数量
            
        Returns:
            消息列表
        """
        if thread_id not in self.message_history:
            return []
        
        history = list(self.message_history[thread_id])
        return history[-limit:] if len(history) > limit else history
    
    def get_all_threads(self) -> List[str]:
        """获取所有活跃的线程ID"""
        return list(self.message_history.keys())
    
    def clear_history(self, thread_id: str):
        """清空指定线程的历史消息"""
        if thread_id in self.message_history:
            self.message_history[thread_id].clear()
            logger.info(f"🗑️ 线程 {thread_id} 的历史消息已清空")
    
    async def send_system_message(
        self,
        content: str,
        thread_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        发送系统消息
        
        Args:
            content: 消息内容
            thread_id: 线程ID
            metadata: 元数据
        """
        message = Message(
            content=content,
            role_type="system",
            role_id="system",
            role_name="系统",
            thread_id=thread_id,
            message_type="system",
            metadata=metadata
        )
        
        await self.broadcast_message(message)
    
    async def send_user_message(
        self,
        content: str,
        role_type: str,
        role_id: str,
        role_name: str,
        thread_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        发送用户消息
        
        Args:
            content: 消息内容
            role_type: 角色类型 (user, admin, n8_workflow等)
            role_id: 角色ID
            role_name: 角色显示名称
            thread_id: 线程ID
            metadata: 元数据
        """
        message = Message(
            content=content,
            role_type=role_type,
            role_id=role_id,
            role_name=role_name,
            thread_id=thread_id,
            message_type="text",
            metadata=metadata
        )
        
        await self.broadcast_message(message)
    
    async def send_tool_call_message(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        thread_id: str = "default"
    ):
        """
        发送工具调用消息
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            thread_id: 线程ID
        """
        message = Message(
            content=f"调用工具: {tool_name}",
            role_type="assistant",
            role_id="agent",
            role_name="AI助手",
            thread_id=thread_id,
            message_type="tool_call",
            metadata={
                "tool_name": tool_name,
                "tool_args": tool_args
            }
        )
        
        await self.broadcast_message(message)
    
    async def send_tool_result_message(
        self,
        tool_name: str,
        result: str,
        thread_id: str = "default"
    ):
        """
        发送工具结果消息
        
        Args:
            tool_name: 工具名称
            result: 工具执行结果
            thread_id: 线程ID
        """
        message = Message(
            content=result[:500],  # 限制长度
            role_type="tool",
            role_id=tool_name,
            role_name=f"工具:{tool_name}",
            thread_id=thread_id,
            message_type="tool_result",
            metadata={
                "tool_name": tool_name,
                "full_result": result
            }
        )
        
        await self.broadcast_message(message)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_connections = sum(len(conns) for conns in self.connections.values())
        total_messages = sum(len(hist) for hist in self.message_history.values())
        
        return {
            "active_threads": len(self.connections),
            "total_connections": total_connections,
            "threads_with_history": len(self.message_history),
            "total_messages": total_messages,
            "threads": {
                thread_id: {
                    "connections": len(self.connections.get(thread_id, set())),
                    "messages": len(self.message_history.get(thread_id, []))
                }
                for thread_id in set(list(self.connections.keys()) + list(self.message_history.keys()))
            }
        }


# 全局统一消息总线实例
unified_messenger = UnifiedMessenger()
