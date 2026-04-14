"""
WebSocket Manager for Sahool Yemen
سهول اليمن - مدير الاتصالات المباشرة

Real-time updates for field monitoring, weather alerts, and notifications.
"""
import asyncio
import json
import time
from typing import Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    # Field Updates
    FIELD_UPDATE = "field_update"
    NDVI_UPDATE = "ndvi_update"

    # Weather
    WEATHER_UPDATE = "weather_update"
    WEATHER_ALERT = "weather_alert"

    # Notifications
    NOTIFICATION = "notification"
    ALERT = "alert"

    # System
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    data: Any
    timestamp: float = field(default_factory=time.time)
    channel: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value if isinstance(self.type, MessageType) else self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "channel": self.channel,
        }, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, data: str) -> 'WebSocketMessage':
        parsed = json.loads(data)
        return cls(
            type=parsed.get("type", "unknown"),
            data=parsed.get("data", {}),
            timestamp=parsed.get("timestamp", time.time()),
            channel=parsed.get("channel"),
        )


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection"""
    websocket: WebSocket
    client_id: str
    user_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    async def send(self, message: WebSocketMessage):
        """Send message to this connection"""
        try:
            await self.websocket.send_text(message.to_json())
        except Exception as e:
            logger.error("ws_send_error", client_id=self.client_id, error=str(e))
            raise


class ConnectionManager:
    """
    WebSocket Connection Manager

    Handles multiple connections, subscriptions, and broadcasting.
    """

    def __init__(self):
        self._connections: dict[str, WebSocketConnection] = {}
        self._channels: dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._message_handlers: dict[str, Callable] = {}
        self._stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
        }

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None
    ) -> WebSocketConnection:
        """Accept and register a new connection"""
        await websocket.accept()

        async with self._lock:
            connection = WebSocketConnection(
                websocket=websocket,
                client_id=client_id,
                user_id=user_id,
            )
            self._connections[client_id] = connection
            self._stats["total_connections"] += 1

        logger.info(
            "ws_connected",
            client_id=client_id,
            user_id=user_id
        )

        # Send connected message
        await self.send_to_client(
            client_id,
            WebSocketMessage(
                type=MessageType.CONNECTED,
                data={"client_id": client_id, "message": "مرحباً بك في سهول اليمن"}
            )
        )

        return connection

    async def disconnect(self, client_id: str):
        """Disconnect and cleanup a connection"""
        async with self._lock:
            if client_id in self._connections:
                connection = self._connections[client_id]

                # Remove from all channels
                for channel in connection.subscriptions:
                    self._channels[channel].discard(client_id)

                del self._connections[client_id]

                logger.info("ws_disconnected", client_id=client_id)

    async def subscribe(self, client_id: str, channel: str):
        """Subscribe a client to a channel"""
        async with self._lock:
            if client_id in self._connections:
                self._connections[client_id].subscriptions.add(channel)
                self._channels[channel].add(client_id)

                logger.debug(
                    "ws_subscribed",
                    client_id=client_id,
                    channel=channel
                )

                await self.send_to_client(
                    client_id,
                    WebSocketMessage(
                        type=MessageType.SUBSCRIBED,
                        data={"channel": channel}
                    )
                )

    async def unsubscribe(self, client_id: str, channel: str):
        """Unsubscribe a client from a channel"""
        async with self._lock:
            if client_id in self._connections:
                self._connections[client_id].subscriptions.discard(channel)
                self._channels[channel].discard(client_id)

                await self.send_to_client(
                    client_id,
                    WebSocketMessage(
                        type=MessageType.UNSUBSCRIBED,
                        data={"channel": channel}
                    )
                )

    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """Send message to a specific client"""
        if client_id in self._connections:
            try:
                await self._connections[client_id].send(message)
                self._stats["total_messages_sent"] += 1
            except Exception:
                await self.disconnect(client_id)

    async def broadcast(self, message: WebSocketMessage, exclude: Optional[Set[str]] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        disconnected = []

        for client_id, connection in self._connections.items():
            if client_id not in exclude:
                try:
                    await connection.send(message)
                    self._stats["total_messages_sent"] += 1
                except Exception:
                    disconnected.append(client_id)

        # Cleanup disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)

    async def broadcast_to_channel(
        self,
        channel: str,
        message: WebSocketMessage,
        exclude: Optional[Set[str]] = None
    ):
        """Broadcast message to all subscribers of a channel"""
        exclude = exclude or set()
        message.channel = channel

        subscribers = self._channels.get(channel, set())
        disconnected = []

        for client_id in subscribers:
            if client_id not in exclude and client_id in self._connections:
                try:
                    await self._connections[client_id].send(message)
                    self._stats["total_messages_sent"] += 1
                except Exception:
                    disconnected.append(client_id)

        # Cleanup disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)

    async def handle_message(
        self,
        client_id: str,
        raw_message: str
    ) -> Optional[WebSocketMessage]:
        """Handle incoming message from client"""
        try:
            message = WebSocketMessage.from_json(raw_message)
            self._stats["total_messages_received"] += 1

            # Handle ping
            if message.type == MessageType.PING.value:
                await self.send_to_client(
                    client_id,
                    WebSocketMessage(type=MessageType.PONG, data={})
                )
                if client_id in self._connections:
                    self._connections[client_id].last_ping = time.time()
                return None

            # Handle subscribe/unsubscribe
            if message.type == "subscribe" and "channel" in message.data:
                await self.subscribe(client_id, message.data["channel"])
                return None

            if message.type == "unsubscribe" and "channel" in message.data:
                await self.unsubscribe(client_id, message.data["channel"])
                return None

            # Custom handlers
            if message.type in self._message_handlers:
                await self._message_handlers[message.type](client_id, message)
                return None

            return message

        except json.JSONDecodeError:
            await self.send_to_client(
                client_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Invalid JSON message"}
                )
            )
            return None

    def register_handler(self, message_type: str, handler: Callable):
        """Register a custom message handler"""
        self._message_handlers[message_type] = handler

    def get_connection(self, client_id: str) -> Optional[WebSocketConnection]:
        """Get connection by client ID"""
        return self._connections.get(client_id)

    def get_connections_for_user(self, user_id: str) -> list[WebSocketConnection]:
        """Get all connections for a user"""
        return [
            conn for conn in self._connections.values()
            if conn.user_id == user_id
        ]

    def get_channel_subscribers(self, channel: str) -> Set[str]:
        """Get all subscribers for a channel"""
        return self._channels.get(channel, set()).copy()

    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            **self._stats,
            "active_connections": len(self._connections),
            "active_channels": len([c for c in self._channels if self._channels[c]]),
        }


# Global connection manager
connection_manager = ConnectionManager()


# =============================================================================
# Yemen-Specific Channels
# =============================================================================

class YemenChannels:
    """Pre-defined channels for Yemen agricultural data"""

    # Regional channels (one per governorate)
    @staticmethod
    def region(region_id: int) -> str:
        return f"region:{region_id}"

    # Field-specific updates
    @staticmethod
    def field(field_id: int) -> str:
        return f"field:{field_id}"

    # Weather alerts for region
    @staticmethod
    def weather(region_id: int) -> str:
        return f"weather:{region_id}"

    # Crop-specific updates
    @staticmethod
    def crop(crop_type: str) -> str:
        return f"crop:{crop_type}"

    # User notifications
    @staticmethod
    def user(user_id: str) -> str:
        return f"user:{user_id}"

    # System-wide broadcasts
    SYSTEM = "system"
    ALERTS = "alerts"
    NDVI = "ndvi"


# =============================================================================
# Real-time Event Emitters
# =============================================================================

class EventEmitter:
    """
    Event emitter for real-time updates

    Used by services to push updates to connected clients.
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def emit_field_update(self, field_id: int, data: dict):
        """Emit field update to subscribers"""
        await self.manager.broadcast_to_channel(
            YemenChannels.field(field_id),
            WebSocketMessage(
                type=MessageType.FIELD_UPDATE,
                data={"field_id": field_id, **data}
            )
        )

    async def emit_ndvi_update(self, field_id: int, ndvi_data: dict):
        """Emit NDVI update"""
        await self.manager.broadcast_to_channel(
            YemenChannels.field(field_id),
            WebSocketMessage(
                type=MessageType.NDVI_UPDATE,
                data={"field_id": field_id, **ndvi_data}
            )
        )

        # Also broadcast to NDVI channel
        await self.manager.broadcast_to_channel(
            YemenChannels.NDVI,
            WebSocketMessage(
                type=MessageType.NDVI_UPDATE,
                data={"field_id": field_id, **ndvi_data}
            )
        )

    async def emit_weather_update(self, region_id: int, weather: dict):
        """Emit weather update for a region"""
        await self.manager.broadcast_to_channel(
            YemenChannels.weather(region_id),
            WebSocketMessage(
                type=MessageType.WEATHER_UPDATE,
                data={"region_id": region_id, **weather}
            )
        )

    async def emit_weather_alert(self, region_id: int, alert: dict):
        """Emit weather alert"""
        message = WebSocketMessage(
            type=MessageType.WEATHER_ALERT,
            data={"region_id": region_id, **alert}
        )

        # Send to region channel
        await self.manager.broadcast_to_channel(
            YemenChannels.weather(region_id),
            message
        )

        # Also send to system alerts
        await self.manager.broadcast_to_channel(
            YemenChannels.ALERTS,
            message
        )

    async def emit_notification(self, user_id: str, notification: dict):
        """Emit notification to a user"""
        connections = self.manager.get_connections_for_user(user_id)
        for conn in connections:
            await self.manager.send_to_client(
                conn.client_id,
                WebSocketMessage(
                    type=MessageType.NOTIFICATION,
                    data=notification
                )
            )

    async def emit_system_alert(self, alert: dict):
        """Emit system-wide alert"""
        await self.manager.broadcast(
            WebSocketMessage(
                type=MessageType.ALERT,
                data=alert
            )
        )


# Global event emitter
event_emitter = EventEmitter(connection_manager)


# =============================================================================
# WebSocket Endpoint Handler
# =============================================================================

async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user_id: Optional[str] = None
):
    """
    WebSocket endpoint handler

    Usage in FastAPI:
        @app.websocket("/ws/{client_id}")
        async def ws_endpoint(websocket: WebSocket, client_id: str):
            await websocket_endpoint(websocket, client_id)
    """
    await connection_manager.connect(websocket, client_id, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.handle_message(client_id, data)

    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error("ws_error", client_id=client_id, error=str(e))
        await connection_manager.disconnect(client_id)


# =============================================================================
# Background Tasks
# =============================================================================

class WebSocketBackgroundTasks:
    """Background tasks for WebSocket maintenance"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self._running = False
        self._tasks = []

    async def start(self):
        """Start background tasks"""
        self._running = True
        self._tasks = [
            asyncio.create_task(self._ping_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]
        logger.info("ws_background_tasks_started")

    async def stop(self):
        """Stop background tasks"""
        self._running = False
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("ws_background_tasks_stopped")

    async def _ping_loop(self):
        """Periodically ping all connections"""
        while self._running:
            await asyncio.sleep(30)  # Ping every 30 seconds

            disconnected = []
            for client_id, conn in self.manager._connections.items():
                # Check for stale connections (no ping response in 60s)
                if time.time() - conn.last_ping > 60:
                    disconnected.append(client_id)
                else:
                    try:
                        await conn.send(
                            WebSocketMessage(type=MessageType.PING, data={})
                        )
                    except Exception:
                        disconnected.append(client_id)

            for client_id in disconnected:
                await self.manager.disconnect(client_id)

    async def _cleanup_loop(self):
        """Periodically cleanup empty channels"""
        while self._running:
            await asyncio.sleep(300)  # Cleanup every 5 minutes

            async with self.manager._lock:
                empty_channels = [
                    ch for ch, subs in self.manager._channels.items()
                    if not subs
                ]
                for channel in empty_channels:
                    del self.manager._channels[channel]

                if empty_channels:
                    logger.debug(
                        "ws_channels_cleaned",
                        count=len(empty_channels)
                    )


# Background tasks instance
ws_background_tasks = WebSocketBackgroundTasks(connection_manager)
