"""
Resource Manager - Memory Leak Prevention System
Manages lifecycle of resources (models, connections, caches) with proper cleanup
"""

import gc
import logging
import psutil
import os
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import weakref

logger = logging.getLogger(__name__)


@dataclass
class ResourceInfo:
    """Information about a managed resource"""
    name: str
    resource: Any
    resource_type: str  # "model", "connection", "cache", "file", "other"
    created_at: datetime
    memory_mb: float = 0.0
    cleanup_func: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryMonitor:
    """Monitor memory usage and detect leaks"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_memory_usage()
        self.snapshots: List[Dict[str, Any]] = []

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        mem = self.process.memory_info()
        return {
            "rss_mb": mem.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": mem.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": self.process.memory_percent(),
        }

    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """Take a memory snapshot"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "label": label,
            **self.get_memory_usage()
        }
        self.snapshots.append(snapshot)
        return snapshot

    def get_memory_delta(self) -> Dict[str, float]:
        """Get memory change since initialization"""
        current = self.get_memory_usage()
        return {
            "rss_delta_mb": current["rss_mb"] - self.initial_memory["rss_mb"],
            "vms_delta_mb": current["vms_mb"] - self.initial_memory["vms_mb"],
            "percent_delta": current["percent"] - self.initial_memory["percent"],
        }

    def detect_leak(self, threshold_mb: float = 100.0) -> bool:
        """Detect potential memory leak"""
        if len(self.snapshots) < 2:
            return False

        # Check if memory is consistently growing
        recent = self.snapshots[-5:]  # Last 5 snapshots
        if len(recent) < 2:
            return False

        growth = recent[-1]["rss_mb"] - recent[0]["rss_mb"]
        return growth > threshold_mb

    def log_memory_status(self):
        """Log current memory status"""
        current = self.get_memory_usage()
        delta = self.get_memory_delta()

        logger.info(
            f"Memory Status - "
            f"RSS: {current['rss_mb']:.1f}MB (Δ{delta['rss_delta_mb']:+.1f}MB), "
            f"VMS: {current['vms_mb']:.1f}MB, "
            f"Usage: {current['percent']:.1f}%"
        )


class ResourceManager:
    """
    Centralized resource manager with automatic cleanup

    Features:
    - Tracks all resources (models, connections, caches)
    - Automatic cleanup on shutdown
    - Memory monitoring and leak detection
    - Weak references to prevent circular refs
    - Custom cleanup functions per resource
    """

    def __init__(self):
        self.resources: Dict[str, ResourceInfo] = {}
        self.memory_monitor = MemoryMonitor()
        self.cleanup_callbacks: List[Callable] = []
        logger.info("🔧 Resource Manager initialized")

    def register_resource(
        self,
        name: str,
        resource: Any,
        resource_type: str = "other",
        cleanup_func: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResourceInfo:
        """
        Register a resource for management

        Args:
            name: Unique name for the resource
            resource: The resource object
            resource_type: Type of resource (model, connection, cache, etc.)
            cleanup_func: Optional custom cleanup function
            metadata: Optional metadata

        Returns:
            ResourceInfo object
        """
        if name in self.resources:
            logger.warning(f"Resource '{name}' already registered, replacing...")
            self.cleanup_resource(name)

        # Estimate memory usage
        memory_mb = self._estimate_memory(resource)

        info = ResourceInfo(
            name=name,
            resource=resource,
            resource_type=resource_type,
            created_at=datetime.now(),
            memory_mb=memory_mb,
            cleanup_func=cleanup_func,
            metadata=metadata or {}
        )

        self.resources[name] = info

        logger.info(
            f"📦 Registered resource: {name} "
            f"(type={resource_type}, memory≈{memory_mb:.1f}MB)"
        )

        return info

    def get_resource(self, name: str) -> Optional[Any]:
        """Get a registered resource"""
        info = self.resources.get(name)
        return info.resource if info else None

    def cleanup_resource(self, name: str) -> bool:
        """
        Clean up a specific resource

        Args:
            name: Name of the resource

        Returns:
            True if cleaned up successfully
        """
        if name not in self.resources:
            logger.warning(f"Resource '{name}' not found")
            return False

        info = self.resources[name]

        try:
            # Call custom cleanup function if provided
            if info.cleanup_func:
                logger.debug(f"Calling custom cleanup for {name}")
                info.cleanup_func(info.resource)

            # Type-specific cleanup
            self._cleanup_by_type(info)

            # Remove reference
            del self.resources[name]

            logger.info(f"🗑️  Cleaned up resource: {name}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up {name}: {e}", exc_info=True)
            return False

    def cleanup_all(self, force_gc: bool = True):
        """
        Clean up all resources

        Args:
            force_gc: Whether to force garbage collection
        """
        logger.info(f"🧹 Cleaning up {len(self.resources)} resources...")

        # Take memory snapshot before cleanup
        before = self.memory_monitor.take_snapshot("before_cleanup")

        # Cleanup in reverse order of registration
        resource_names = list(self.resources.keys())
        for name in reversed(resource_names):
            self.cleanup_resource(name)

        # Call additional cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")

        # Force garbage collection
        if force_gc:
            logger.debug("Running garbage collection...")
            collected = gc.collect()
            logger.debug(f"Garbage collector: {collected} objects collected")

        # Take memory snapshot after cleanup
        after = self.memory_monitor.take_snapshot("after_cleanup")

        # Log memory freed
        freed_mb = before["rss_mb"] - after["rss_mb"]
        logger.info(
            f"✅ Cleanup complete - "
            f"Freed: {freed_mb:.1f}MB, "
            f"Current: {after['rss_mb']:.1f}MB"
        )

    def cleanup_by_type(self, resource_type: str):
        """Clean up all resources of a specific type"""
        names = [
            name for name, info in self.resources.items()
            if info.resource_type == resource_type
        ]

        logger.info(f"Cleaning up {len(names)} resources of type '{resource_type}'")
        for name in names:
            self.cleanup_resource(name)

    def get_memory_report(self) -> Dict[str, Any]:
        """Get detailed memory report"""
        current = self.memory_monitor.get_memory_usage()
        delta = self.memory_monitor.get_memory_delta()

        resources_by_type = {}
        total_resource_memory = 0.0

        for info in self.resources.values():
            if info.resource_type not in resources_by_type:
                resources_by_type[info.resource_type] = {
                    "count": 0,
                    "memory_mb": 0.0
                }
            resources_by_type[info.resource_type]["count"] += 1
            resources_by_type[info.resource_type]["memory_mb"] += info.memory_mb
            total_resource_memory += info.memory_mb

        return {
            "current_memory": current,
            "memory_delta": delta,
            "total_resources": len(self.resources),
            "resources_by_type": resources_by_type,
            "estimated_resource_memory_mb": total_resource_memory,
            "leak_detected": self.memory_monitor.detect_leak(),
        }

    def log_status(self):
        """Log current status"""
        report = self.get_memory_report()

        logger.info(
            f"📊 Resource Manager Status - "
            f"Resources: {report['total_resources']}, "
            f"Memory: {report['current_memory']['rss_mb']:.1f}MB"
        )

        if report["leak_detected"]:
            logger.warning("⚠️  Potential memory leak detected!")

    def add_cleanup_callback(self, callback: Callable):
        """Add a callback to be called during cleanup"""
        self.cleanup_callbacks.append(callback)

    def _estimate_memory(self, obj: Any) -> float:
        """Estimate memory usage of an object (in MB)"""
        try:
            import sys
            size_bytes = sys.getsizeof(obj)

            # For complex objects, try to get deeper size
            if hasattr(obj, '__dict__'):
                size_bytes += sum(
                    sys.getsizeof(v) for v in obj.__dict__.values()
                )

            return size_bytes / 1024 / 1024

        except Exception as e:
            logger.debug(f"Could not estimate memory: {e}")
            return 0.0

    def _cleanup_by_type(self, info: ResourceInfo):
        """Type-specific cleanup logic"""
        resource_type = info.resource_type
        resource = info.resource

        try:
            if resource_type == "model":
                # ML Model cleanup
                if hasattr(resource, 'model') and resource.model is not None:
                    del resource.model
                    logger.debug(f"Deleted model from {info.name}")

                # Clear any caches
                if hasattr(resource, 'cache'):
                    resource.cache.clear()
                    logger.debug(f"Cleared cache for {info.name}")

            elif resource_type == "connection":
                # Database/Network connection cleanup
                if hasattr(resource, 'close'):
                    resource.close()
                    logger.debug(f"Closed connection {info.name}")
                elif hasattr(resource, 'disconnect'):
                    resource.disconnect()
                    logger.debug(f"Disconnected {info.name}")

            elif resource_type == "cache":
                # Cache cleanup
                if hasattr(resource, 'clear'):
                    resource.clear()
                    logger.debug(f"Cleared cache {info.name}")
                elif isinstance(resource, dict):
                    resource.clear()
                    logger.debug(f"Cleared dict cache {info.name}")

            elif resource_type == "file":
                # File handle cleanup
                if hasattr(resource, 'close'):
                    resource.close()
                    logger.debug(f"Closed file {info.name}")

        except Exception as e:
            logger.error(f"Error in type-specific cleanup for {info.name}: {e}")

    @contextmanager
    def track_memory(self, label: str):
        """Context manager to track memory usage of a block"""
        before = self.memory_monitor.take_snapshot(f"{label}_before")
        try:
            yield
        finally:
            after = self.memory_monitor.take_snapshot(f"{label}_after")
            delta = after["rss_mb"] - before["rss_mb"]
            logger.debug(f"Memory delta for '{label}': {delta:+.1f}MB")


# Global instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get or create global resource manager"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def cleanup_resources():
    """Cleanup all resources (called on shutdown)"""
    global _resource_manager
    if _resource_manager is not None:
        _resource_manager.cleanup_all()
        _resource_manager = None


# Convenience decorators
def managed_resource(name: str, resource_type: str = "other"):
    """Decorator to automatically register a resource"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            resource = func(*args, **kwargs)
            manager = get_resource_manager()
            manager.register_resource(name, resource, resource_type)
            return resource
        return wrapper
    return decorator
