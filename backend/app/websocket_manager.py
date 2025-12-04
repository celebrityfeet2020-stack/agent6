"""
WebSocket Manager for M3 Agent System v5.5
管理WebSocket连接和消息广播
"""

from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # thread_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, thread_id: str):
        """连接WebSocket客户端"""
        await websocket.accept()
        
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = set()
        
        self.active_connections[thread_id].add(websocket)
        logger.info(f"WebSocket connected to thread {thread_id}, total: {len(self.active_connections[thread_id])}")
    
    def disconnect(self, websocket: WebSocket, thread_id: str):
        """断开WebSocket客户端"""
        if thread_id in self.active_connections:
            self.active_connections[thread_id].discard(websocket)
            
            # 如果该thread没有连接了，删除key
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]
            
            logger.info(f"WebSocket disconnected from thread {thread_id}")
    
    async def broadcast_to_thread(self, thread_id: str, message: dict):
        """向指定thread的所有客户端广播消息"""
        if thread_id not in self.active_connections:
            return
        
        # 复制集合避免在迭代时修改
        connections = self.active_connections[thread_id].copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {e}")
                # 移除失败的连接
                self.disconnect(connection, thread_id)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """向单个客户端发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    def get_thread_connections_count(self, thread_id: str) -> int:
        """获取指定thread的连接数"""
        return len(self.active_connections.get(thread_id, set()))
    
    def get_total_connections_count(self) -> int:
        """获取总连接数"""
        return sum(len(conns) for conns in self.active_connections.values())


# 全局连接管理器实例
manager = ConnectionManager()
