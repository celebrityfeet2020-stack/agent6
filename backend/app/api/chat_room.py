"""
M3 Agent System v5.8 - Triangle Chat Room API
三角聊天室API：user/api/assistant三方实时通信

应用场景：
- 数字人直播间监控
- 客服系统监督
- 教学系统辅导

三方角色：
1. audience（观众）- 通过API发送弹幕的外部用户
2. agent（大模型）- M3 Agent系统，生成回复和动作
3. admin（管理员）- 人类监督者，可以干预和纠正

人在回路（Human-in-the-Loop）机制：
- 管理员实时监控观众和大模型的对话
- 发现不当回复时立即干预
- 大模型理解干预意图并调整行为
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat-room", tags=["chat-room"])


# ============================================
# Data Models
# ============================================

class ChatRoomMessage(BaseModel):
    """聊天室消息"""
    room_id: str
    message_id: str
    source: str  # audience/agent/admin/system
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


class CreateRoomRequest(BaseModel):
    """创建聊天室请求"""
    room_name: Optional[str] = Field(None, description="聊天室名称")
    metadata: Optional[Dict] = Field(None, description="元数据")


class CreateRoomResponse(BaseModel):
    """创建聊天室响应"""
    room_id: str
    room_name: str
    created_at: str
    ws_url: str


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    source: str = Field(..., description="消息来源（audience/admin）")
    content: str = Field(..., description="消息内容")
    metadata: Optional[Dict] = Field(None, description="元数据")


class JoinRoomRequest(BaseModel):
    """加入聊天室请求"""
    role: str = Field(..., description="角色（audience/admin）")
    user_id: Optional[str] = Field(None, description="用户ID")


# ============================================
# Chat Room Manager
# ============================================

class ChatRoomManager:
    """
    聊天室管理器
    
    功能：
    - 管理多个聊天室
    - 管理WebSocket连接
    - 路由消息到所有连接者
    - 存储消息历史
    """
    
    def __init__(self):
        # 聊天室信息：{room_id: {"name": str, "created_at": str, "metadata": dict}}
        self.rooms: Dict[str, Dict] = {}
        
        # WebSocket连接：{room_id: {connection_id: WebSocket}}
        self.connections: Dict[str, Dict[str, WebSocket]] = {}
        
        # 消息历史：{room_id: [ChatRoomMessage]}
        self.message_history: Dict[str, List[ChatRoomMessage]] = {}
        
        # 连接角色：{connection_id: role}
        self.connection_roles: Dict[str, str] = {}
    
    def create_room(self, room_name: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict:
        """
        创建聊天室
        
        Args:
            room_name: 聊天室名称
            metadata: 元数据
        
        Returns:
            聊天室信息
        """
        room_id = f"room-{uuid.uuid4().hex[:8]}"
        room_name = room_name or f"Room {room_id}"
        
        self.rooms[room_id] = {
            "name": room_name,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.connections[room_id] = {}
        self.message_history[room_id] = []
        
        logger.info(f"Created chat room: {room_id} ({room_name})")
        return {
            "room_id": room_id,
            "room_name": room_name,
            "created_at": self.rooms[room_id]["created_at"]
        }
    
    async def connect(self, room_id: str, websocket: WebSocket, role: str = "admin") -> str:
        """
        连接到聊天室
        
        Args:
            room_id: 聊天室ID
            websocket: WebSocket连接
            role: 角色（audience/admin）
        
        Returns:
            连接ID
        """
        if room_id not in self.rooms:
            raise ValueError(f"Room {room_id} not found")
        
        await websocket.accept()
        
        connection_id = f"conn-{uuid.uuid4().hex[:8]}"
        self.connections[room_id][connection_id] = websocket
        self.connection_roles[connection_id] = role
        
        logger.info(f"WebSocket connected: {connection_id} to room {room_id} as {role}")
        
        # 发送欢迎消息
        await self.send_system_message(
            room_id,
            f"{role.capitalize()} joined the room",
            connection_id
        )
        
        return connection_id
    
    def disconnect(self, room_id: str, connection_id: str):
        """
        断开连接
        
        Args:
            room_id: 聊天室ID
            connection_id: 连接ID
        """
        if room_id in self.connections and connection_id in self.connections[room_id]:
            del self.connections[room_id][connection_id]
            logger.info(f"WebSocket disconnected: {connection_id} from room {room_id}")
        
        if connection_id in self.connection_roles:
            del self.connection_roles[connection_id]
    
    async def broadcast(self, room_id: str, message: ChatRoomMessage, exclude_connection: Optional[str] = None):
        """
        广播消息到聊天室的所有连接
        
        Args:
            room_id: 聊天室ID
            message: 消息
            exclude_connection: 排除的连接ID
        """
        if room_id not in self.connections:
            return
        
        # 存储到历史记录
        if room_id in self.message_history:
            self.message_history[room_id].append(message)
        
        # 广播到所有连接
        message_json = message.model_dump_json()
        disconnected = []
        
        for conn_id, websocket in self.connections[room_id].items():
            if conn_id == exclude_connection:
                continue
            
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message to {conn_id}: {e}")
                disconnected.append(conn_id)
        
        # 清理断开的连接
        for conn_id in disconnected:
            self.disconnect(room_id, conn_id)
    
    async def send_system_message(self, room_id: str, content: str, exclude_connection: Optional[str] = None):
        """
        发送系统消息
        
        Args:
            room_id: 聊天室ID
            content: 消息内容
            exclude_connection: 排除的连接ID
        """
        message = ChatRoomMessage(
            room_id=room_id,
            message_id=f"msg-{uuid.uuid4().hex[:8]}",
            source="system",
            content=content,
            timestamp=datetime.now().isoformat()
        )
        await self.broadcast(room_id, message, exclude_connection)
    
    async def process_audience_message(self, room_id: str, content: str, metadata: Optional[Dict] = None) -> ChatRoomMessage:
        """
        处理观众消息（触发Agent响应）
        
        Args:
            room_id: 聊天室ID
            content: 消息内容
            metadata: 元数据
        
        Returns:
            观众消息
        """
        # 创建观众消息
        audience_message = ChatRoomMessage(
            room_id=room_id,
            message_id=f"msg-{uuid.uuid4().hex[:8]}",
            source="audience",
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        # 广播观众消息
        await self.broadcast(room_id, audience_message)
        
        # 触发Agent响应（异步）
        asyncio.create_task(self._generate_agent_response(room_id, content, metadata))
        
        return audience_message
    
    async def _generate_agent_response(self, room_id: str, user_message: str, metadata: Optional[Dict] = None):
        """
        生成Agent响应（内部方法）
        
        Args:
            room_id: 聊天室ID
            user_message: 用户消息
            metadata: 元数据
        """
        try:
            # 导入全局变量
            from main import app_graph
            
            # 准备输入
            from langchain_core.messages import HumanMessage
            input_data = {"messages": [HumanMessage(content=user_message)]}
            config = {"configurable": {"thread_id": room_id}}
            
            # 执行Agent
            result = await app_graph.ainvoke(input_data, config=config)
            
            # 提取Agent回复
            if "messages" in result and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                agent_content = last_message.content if hasattr(last_message, "content") else str(last_message)
                
                # 创建Agent消息
                agent_message = ChatRoomMessage(
                    room_id=room_id,
                    message_id=f"msg-{uuid.uuid4().hex[:8]}",
                    source="agent",
                    content=agent_content,
                    timestamp=datetime.now().isoformat(),
                    metadata=metadata
                )
                
                # 广播Agent消息
                await self.broadcast(room_id, agent_message)
            
        except Exception as e:
            logger.error(f"Error generating agent response: {e}", exc_info=True)
            # 发送错误消息
            await self.send_system_message(
                room_id,
                f"Error: Failed to generate agent response - {str(e)}"
            )
    
    async def process_admin_intervention(self, room_id: str, content: str, metadata: Optional[Dict] = None) -> ChatRoomMessage:
        """
        处理管理员干预（人在回路）
        
        Args:
            room_id: 聊天室ID
            content: 干预内容
            metadata: 元数据
        
        Returns:
            管理员消息
        """
        # 创建管理员消息
        admin_message = ChatRoomMessage(
            room_id=room_id,
            message_id=f"msg-{uuid.uuid4().hex[:8]}",
            source="admin",
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        # 广播管理员消息
        await self.broadcast(room_id, admin_message)
        
        # 如果是干预指令，触发Agent调整
        if metadata and metadata.get("action") == "intervene":
            asyncio.create_task(self._generate_agent_response(room_id, content, metadata))
        
        return admin_message
    
    def get_room_history(self, room_id: str, limit: Optional[int] = 100) -> List[ChatRoomMessage]:
        """
        获取聊天室历史记录
        
        Args:
            room_id: 聊天室ID
            limit: 最大消息数
        
        Returns:
            消息列表
        """
        if room_id not in self.message_history:
            return []
        
        messages = self.message_history[room_id]
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def delete_room(self, room_id: str):
        """
        删除聊天室
        
        Args:
            room_id: 聊天室ID
        """
        if room_id in self.rooms:
            del self.rooms[room_id]
        if room_id in self.connections:
            del self.connections[room_id]
        if room_id in self.message_history:
            del self.message_history[room_id]
        
        logger.info(f"Deleted chat room: {room_id}")


# 全局聊天室管理器
chat_room_manager = ChatRoomManager()


# ============================================
# REST API Endpoints
# ============================================

@router.post("/create", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    """
    创建聊天室
    
    示例：
    ```bash
    curl -X POST http://localhost:8888/api/chat-room/create \
      -H "Content-Type: application/json" \
      -d '{"room_name": "数字人直播间"}'
    ```
    """
    try:
        room_info = chat_room_manager.create_room(
            room_name=request.room_name,
            metadata=request.metadata
        )
        
        return CreateRoomResponse(
            room_id=room_info["room_id"],
            room_name=room_info["room_name"],
            created_at=room_info["created_at"],
            ws_url=f"ws://localhost:8888/api/chat-room/{room_info['room_id']}/ws"
        )
    except Exception as e:
        logger.error(f"Error creating room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{room_id}/message")
async def send_message(room_id: str, request: SendMessageRequest):
    """
    发送消息到聊天室
    
    示例：
    ```bash
    # 观众消息
    curl -X POST http://localhost:8888/api/chat-room/room-123/message \
      -H "Content-Type: application/json" \
      -d '{"source": "audience", "content": "主播唱首歌吧"}'
    
    # 管理员干预
    curl -X POST http://localhost:8888/api/chat-room/room-123/message \
      -H "Content-Type: application/json" \
      -d '{"source": "admin", "content": "不要唱歌，改成讲个笑话", "metadata": {"action": "intervene"}}'
    ```
    """
    try:
        if room_id not in chat_room_manager.rooms:
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        
        if request.source == "audience":
            message = await chat_room_manager.process_audience_message(
                room_id, request.content, request.metadata
            )
        elif request.source == "admin":
            message = await chat_room_manager.process_admin_intervention(
                room_id, request.content, request.metadata
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid source: {request.source}")
        
        return {"status": "ok", "message_id": message.message_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{room_id}/history")
async def get_room_history(room_id: str, limit: Optional[int] = 100):
    """
    获取聊天室历史记录
    
    示例：
    ```bash
    curl http://localhost:8888/api/chat-room/room-123/history?limit=50
    ```
    """
    try:
        if room_id not in chat_room_manager.rooms:
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        
        messages = chat_room_manager.get_room_history(room_id, limit)
        return {"room_id": room_id, "messages": messages, "total": len(messages)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{room_id}")
async def delete_room(room_id: str):
    """
    删除聊天室
    
    示例：
    ```bash
    curl -X DELETE http://localhost:8888/api/chat-room/room-123
    ```
    """
    try:
        if room_id not in chat_room_manager.rooms:
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        
        chat_room_manager.delete_room(room_id)
        return {"status": "ok", "message": f"Room {room_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/{room_id}/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str, role: str = "admin"):
    """
    WebSocket端点（三角聊天室实时通信）
    
    连接示例：
    ```javascript
    const ws = new WebSocket('ws://localhost:8888/api/chat-room/room-123/ws?role=admin');
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log(message.source, message.content);
    };
    
    ws.send(JSON.stringify({
        source: 'admin',
        content: '不要唱歌，改成讲个笑话',
        metadata: {action: 'intervene'}
    }));
    ```
    """
    connection_id = None
    try:
        # 连接到聊天室
        connection_id = await chat_room_manager.connect(room_id, websocket, role)
        
        # 接收消息循环
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            source = message_data.get("source", role)
            content = message_data.get("content", "")
            metadata = message_data.get("metadata")
            
            # 处理消息
            if source == "audience":
                await chat_room_manager.process_audience_message(room_id, content, metadata)
            elif source == "admin":
                await chat_room_manager.process_admin_intervention(room_id, content, metadata)
            else:
                logger.warning(f"Unknown message source: {source}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        if connection_id:
            chat_room_manager.disconnect(room_id, connection_id)


# 导出
__all__ = ['router', 'chat_room_manager']
