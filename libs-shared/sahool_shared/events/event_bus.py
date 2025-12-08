"""
Event Bus Implementation
تنفيذ ناقل الأحداث
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from uuid import uuid4
import os

from pydantic import BaseModel, Field
import redis.asyncio as redis

# Configure logger
logger = logging.getLogger(__name__)


class Event(BaseModel):
    """
    Base event class.
    فئة الحدث الأساسية
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: Optional[str] = None
    source: str = "unknown"
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


EventT = TypeVar("EventT", bound=Event)
EventHandler = Callable[[Event], Any]


class EventBus(ABC):
    """
    Abstract Event Bus interface.
    واجهة ناقل الأحداث المجردة
    """

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event."""
        pass

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        pass

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        pass


class InMemoryEventBus(EventBus):
    """
    In-memory event bus for development/testing.
    ناقل أحداث في الذاكرة للتطوير/الاختبار
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._all_handlers: List[EventHandler] = []

    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers."""
        handlers = self._handlers.get(event.type, []) + self._all_handlers

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event handler for event {event.type}: {e}", exc_info=True)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to specific event type."""
        if event_type == "*":
            self._all_handlers.append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from event type."""
        if event_type == "*":
            if handler in self._all_handlers:
                self._all_handlers.remove(handler)
        elif event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)


class RedisEventBus(EventBus):
    """
    Redis-based event bus for production.
    ناقل أحداث مبني على Redis للإنتاج
    """

    def __init__(
        self,
        url: Optional[str] = None,
        channel_prefix: str = "sahool:events",
    ):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.channel_prefix = channel_prefix
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.from_url(self.url, decode_responses=True)
        self._pubsub = self._client.pubsub()
        await self._client.ping()

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()

    def _channel_name(self, event_type: str) -> str:
        """Get channel name for event type."""
        return f"{self.channel_prefix}:{event_type}"

    async def publish(self, event: Event) -> None:
        """Publish event to Redis channel."""
        if not self._client:
            raise RuntimeError("Not connected to Redis")

        channel = self._channel_name(event.type)
        message = event.json()
        await self._client.publish(channel, message)

        # Also publish to wildcard channel
        await self._client.publish(f"{self.channel_prefix}:*", message)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to event type."""
        if not self._pubsub:
            raise RuntimeError("Not connected to Redis")

        channel = self._channel_name(event_type)

        if event_type not in self._handlers:
            self._handlers[event_type] = []
            await self._pubsub.subscribe(channel)

        self._handlers[event_type].append(handler)

        # Start listener if not running
        if not self._listener_task:
            self._listener_task = asyncio.create_task(self._listen())

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from event type."""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

            if not self._handlers[event_type]:
                del self._handlers[event_type]
                channel = self._channel_name(event_type)
                await self._pubsub.unsubscribe(channel)

    async def _listen(self) -> None:
        """Listen for messages."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message)
        except asyncio.CancelledError:
            pass

    async def _handle_message(self, message: dict) -> None:
        """Handle incoming message."""
        try:
            event_data = json.loads(message["data"])
            event = Event(**event_data)

            handlers = self._handlers.get(event.type, [])

            for handler in handlers:
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"Error in event handler: {e}")

        except Exception as e:
            print(f"Error processing message: {e}")


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus() -> EventBus:
    """Get or create global event bus instance."""
    global _event_bus
    if _event_bus is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            _event_bus = RedisEventBus(url=redis_url)
            await _event_bus.connect()
        else:
            _event_bus = InMemoryEventBus()
    return _event_bus


async def publish_event(event: Event) -> None:
    """Convenience function to publish event."""
    bus = await get_event_bus()
    await bus.publish(event)


def subscribe(event_type: str):
    """
    Decorator to subscribe function to event type.

    Usage:
        @subscribe("field.created")
        async def handle_field_created(event: Event):
            ...
    """
    def decorator(func: EventHandler) -> EventHandler:
        async def register():
            bus = await get_event_bus()
            await bus.subscribe(event_type, func)

        # Schedule registration
        asyncio.get_event_loop().create_task(register())
        return func

    return decorator
