"""
M3 Agent System v5.9 - Unified Chat Room (三角聊天室)

默认统一聊天室：
- 用户（User）：正常聊天
- API用户（API）：性能测试、外部调用等
- Agent模型（Agent）：大模型回复

所有对话三方可见，无需"创建聊天室"。
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unified-chat", tags=["Unified Chat Room"])

# ============================================
# Pydantic Models
# ============================================

class Message(BaseModel):
    """聊天消息"""
    source: str  # "user", "api", "agent"
    content: str
    timestamp: str
    metadata: Optional[Dict] = None

class ChatHistory(BaseModel):
    """聊天历史"""
    messages: List[Message]
    total: int

# ============================================
# Unified Chat Room Manager
# ============================================

class UnifiedChatRoomManager:
    """统一聊天室管理器（单例）"""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.messages: List[Message] = []
        self.max_history = 1000  # 最多保留1000条消息
        logger.info("✅ Unified Chat Room initialized")
    
    async def connect(self, websocket: WebSocket):
        """新连接加入聊天室"""
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"🔌 New connection, total: {len(self.connections)}")
        
        # 发送历史消息（最近50条）
        recent_messages = self.messages[-50:] if len(self.messages) > 50 else self.messages
        for msg in recent_messages:
            await websocket.send_json({
                "type": "history",
                "message": msg.dict()
            })
    
    def disconnect(self, websocket: WebSocket):
        """连接断开"""
        if websocket in self.connections:
            self.connections.remove(websocket)
        logger.info(f"🔌 Connection closed, remaining: {len(self.connections)}")
    
    async def broadcast(self, message: Message):
        """广播消息到所有连接"""
        # 保存消息
        self.messages.append(message)
        
        # 限制历史消息数量
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        # 广播到所有连接
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json({
                    "type": "message",
                    "message": message.dict()
                })
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_history(self, limit: int = 100) -> List[Message]:
        """获取历史消息"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages

# 全局单例
unified_chat_room = UnifiedChatRoomManager()

# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket连接端点
    
    前端连接后，可以：
    1. 接收所有三方消息（user/api/agent）
    2. 发送用户消息
    """
    await unified_chat_room.connect(websocket)
    
    try:
        while True:
            # 接收用户消息
            data = await websocket.receive_json()
            
            if data.get("type") == "user_message":
                # 用户发送的消息
                message = Message(
                    source="user",
                    content=data.get("content", ""),
                    timestamp=datetime.now().isoformat(),
                    metadata=data.get("metadata")
                )
                
                # 广播用户消息
                await unified_chat_room.broadcast(message)
                
                # TODO: 调用Agent处理用户消息
                # agent_response = await process_user_message(message.content)
                # await unified_chat_room.broadcast(Message(
                #     source="agent",
                #     content=agent_response,
                #     timestamp=datetime.now().isoformat()
                # ))
                
    except WebSocketDisconnect:
        unified_chat_room.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        unified_chat_room.disconnect(websocket)

# ============================================
# REST API Endpoints
# ============================================

@router.post("/message")
async def send_message(source: str, content: str, metadata: Optional[Dict] = None):
    """
    发送消息到聊天室（REST API）
    
    用于：
    - API用户发送消息（source="api"）
    - Agent发送消息（source="agent"）
    - 后台任务发送消息（source="system"）
    """
    if source not in ["user", "api", "agent", "system"]:
        raise HTTPException(status_code=400, detail="Invalid source")
    
    message = Message(
        source=source,
        content=content,
        timestamp=datetime.now().isoformat(),
        metadata=metadata
    )
    
    await unified_chat_room.broadcast(message)
    
    return {"status": "ok", "message": "Message sent"}

@router.get("/history", response_model=ChatHistory)
async def get_history(limit: int = 100):
    """获取聊天历史"""
    messages = unified_chat_room.get_history(limit)
    return ChatHistory(
        messages=messages,
        total=len(unified_chat_room.messages)
    )

@router.get("/status")
async def get_status():
    """获取聊天室状态"""
    return {
        "connections": len(unified_chat_room.connections),
        "total_messages": len(unified_chat_room.messages),
        "status": "active"
    }

# ============================================
# Helper Functions for Background Tasks
# ============================================

async def send_system_message(content: str, metadata: Optional[Dict] = None):
    """
    后台任务发送系统消息
    
    用于：
    - 性能测试结果
    - API检测结果
    - 工具池加载状态
    - 全面体检结果
    """
    message = Message(
        source="system",
        content=content,
        timestamp=datetime.now().isoformat(),
        metadata=metadata
    )
    await unified_chat_room.broadcast(message)
    logger.info(f"📢 System message sent: {content[:50]}...")

async def send_api_message(content: str, metadata: Optional[Dict] = None):
    """
    API用户发送消息
    
    用于：
    - 外部API调用
    - 数字人直播间弹幕
    """
    message = Message(
        source="api",
        content=content,
        timestamp=datetime.now().isoformat(),
        metadata=metadata
    )
    await unified_chat_room.broadcast(message)
    logger.info(f"📢 API message sent: {content[:50]}...")
