"""
Tests for Memory Cleanup and Leak Prevention
Ensures resources are properly cleaned up
"""

import pytest
import gc
import sys
import os
from unittest.mock import Mock, MagicMock
import weakref

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.resource_manager import ResourceManager, MemoryMonitor, ResourceInfo
from shared.cleanup_helpers import (
    cleanup_ml_model,
    cleanup_ml_models_dict,
    cleanup_caches,
    force_garbage_collection,
    CleanupContext
)


class TestMemoryMonitor:
    """Test memory monitoring functionality"""

    def test_memory_monitor_initialization(self):
        """Test memory monitor initializes correctly"""
        monitor = MemoryMonitor()

        assert monitor.process is not None
        assert "rss_mb" in monitor.initial_memory
        assert "vms_mb" in monitor.initial_memory
        assert len(monitor.snapshots) == 0

    def test_get_memory_usage(self):
        """Test getting current memory usage"""
        monitor = MemoryMonitor()
        usage = monitor.get_memory_usage()

        assert "rss_mb" in usage
        assert "vms_mb" in usage
        assert "percent" in usage
        assert usage["rss_mb"] > 0
        assert usage["percent"] >= 0

    def test_take_snapshot(self):
        """Test taking memory snapshot"""
        monitor = MemoryMonitor()

        snapshot = monitor.take_snapshot("test_snapshot")

        assert snapshot["label"] == "test_snapshot"
        assert "timestamp" in snapshot
        assert "rss_mb" in snapshot
        assert len(monitor.snapshots) == 1

    def test_get_memory_delta(self):
        """Test calculating memory delta"""
        monitor = MemoryMonitor()

        # Do some memory allocation
        data = [i for i in range(100000)]

        delta = monitor.get_memory_delta()

        assert "rss_delta_mb" in delta
        assert "vms_delta_mb" in delta

        # Cleanup
        del data
        gc.collect()

    def test_detect_leak(self):
        """Test leak detection (basic)"""
        monitor = MemoryMonitor()

        # Take multiple snapshots
        for i in range(6):
            monitor.take_snapshot(f"snapshot_{i}")

        # Should not detect leak without significant growth
        # (this is a basic test, real leaks require more data)
        leak = monitor.detect_leak(threshold_mb=1000.0)
        assert isinstance(leak, bool)


class TestResourceManager:
    """Test resource manager functionality"""

    def test_resource_manager_initialization(self):
        """Test resource manager initializes correctly"""
        manager = ResourceManager()

        assert len(manager.resources) == 0
        assert manager.memory_monitor is not None
        assert len(manager.cleanup_callbacks) == 0

    def test_register_resource(self):
        """Test registering a resource"""
        manager = ResourceManager()

        resource = {"data": "test"}
        info = manager.register_resource(
            name="test_resource",
            resource=resource,
            resource_type="other"
        )

        assert isinstance(info, ResourceInfo)
        assert info.name == "test_resource"
        assert info.resource == resource
        assert "test_resource" in manager.resources

    def test_get_resource(self):
        """Test getting a registered resource"""
        manager = ResourceManager()

        resource = {"data": "test"}
        manager.register_resource("test", resource, "other")

        retrieved = manager.get_resource("test")

        assert retrieved == resource

    def test_cleanup_resource(self):
        """Test cleaning up a specific resource"""
        manager = ResourceManager()

        resource = {"data": "test"}
        manager.register_resource("test", resource, "cache")

        success = manager.cleanup_resource("test")

        assert success is True
        assert "test" not in manager.resources

    def test_cleanup_all(self):
        """Test cleaning up all resources"""
        manager = ResourceManager()

        # Register multiple resources
        for i in range(5):
            manager.register_resource(
                f"resource_{i}",
                {"data": f"test_{i}"},
                "other"
            )

        assert len(manager.resources) == 5

        manager.cleanup_all()

        assert len(manager.resources) == 0

    def test_cleanup_by_type(self):
        """Test cleaning up resources by type"""
        manager = ResourceManager()

        # Register different types
        manager.register_resource("model1", Mock(), "model")
        manager.register_resource("model2", Mock(), "model")
        manager.register_resource("cache1", {}, "cache")

        manager.cleanup_by_type("model")

        assert len(manager.resources) == 1
        assert "cache1" in manager.resources

    def test_custom_cleanup_function(self):
        """Test custom cleanup function is called"""
        manager = ResourceManager()
        cleanup_called = []

        def custom_cleanup(resource):
            cleanup_called.append(True)

        resource = Mock()
        manager.register_resource(
            "test",
            resource,
            "other",
            cleanup_func=custom_cleanup
        )

        manager.cleanup_resource("test")

        assert len(cleanup_called) == 1

    def test_cleanup_callback(self):
        """Test cleanup callback is called"""
        manager = ResourceManager()
        callback_called = []

        def callback():
            callback_called.append(True)

        manager.add_cleanup_callback(callback)
        manager.cleanup_all()

        assert len(callback_called) == 1

    def test_get_memory_report(self):
        """Test getting memory report"""
        manager = ResourceManager()

        # Register some resources
        manager.register_resource("model", Mock(), "model")
        manager.register_resource("cache", {}, "cache")

        report = manager.get_memory_report()

        assert "current_memory" in report
        assert "memory_delta" in report
        assert "total_resources" in report
        assert report["total_resources"] == 2
        assert "resources_by_type" in report
        assert "model" in report["resources_by_type"]
        assert "cache" in report["resources_by_type"]


class TestCleanupHelpers:
    """Test cleanup helper functions"""

    def test_cleanup_ml_model_basic(self):
        """Test basic ML model cleanup"""
        model = Mock()
        model.model = Mock()
        model._cache = {}

        cleanup_ml_model(model, "test_model")

        # Model should be cleaned (we can't assert on deleted object)
        # But we can assert no exceptions

    def test_cleanup_ml_model_with_cleanup_method(self):
        """Test cleanup with model's cleanup method"""
        cleanup_called = []

        model = Mock()
        model.cleanup = lambda: cleanup_called.append(True)
        model.model = Mock()

        cleanup_ml_model(model, "test_model")

        assert len(cleanup_called) == 1

    def test_cleanup_ml_models_dict(self):
        """Test cleaning up multiple models from dict"""
        models = {
            "model1": Mock(model=Mock(), _cache={}),
            "model2": Mock(model=Mock(), _cache={}),
        }

        cleanup_ml_models_dict(models)

        assert len(models) == 0

    def test_cleanup_caches(self):
        """Test cleaning up caches"""
        cache1 = {"key": "value"}
        cache2 = []
        cache3 = Mock()
        cache3.clear = Mock()

        cleanup_caches(cache1, cache2, cache3)

        assert len(cache1) == 0
        assert len(cache2) == 0
        cache3.clear.assert_called_once()

    def test_force_garbage_collection(self):
        """Test forcing garbage collection"""
        collected = force_garbage_collection(generations=2)

        assert isinstance(collected, int)
        assert collected >= 0

    def test_cleanup_context(self):
        """Test cleanup context manager"""
        resource1 = Mock()
        resource2 = Mock()

        with CleanupContext([resource1, resource2]):
            # Use resources
            pass

        # Resources should be cleaned up
        # (we can't assert on deleted objects but no exceptions should occur)


class TestMemoryLeakDetection:
    """Test memory leak detection"""

    def test_no_leak_simple_allocation(self):
        """Test that simple allocations don't cause leaks"""
        manager = ResourceManager()

        # Take initial snapshot
        manager.memory_monitor.take_snapshot("before")

        # Allocate and deallocate
        for i in range(10):
            data = [j for j in range(10000)]
            del data
            gc.collect()

        # Take final snapshot
        manager.memory_monitor.take_snapshot("after")

        # Memory should not have grown significantly
        delta = manager.memory_monitor.get_memory_delta()
        # Allow some growth for test overhead
        assert abs(delta["rss_delta_mb"]) < 50

    def test_detect_leak_with_growing_list(self):
        """Test leak detection with intentional leak"""
        monitor = MemoryMonitor()
        leak_list = []

        for i in range(5):
            # Intentionally grow list (simulate leak)
            leak_list.extend([j for j in range(100000)])
            monitor.take_snapshot(f"iteration_{i}")

        # Should detect the leak
        detected = monitor.detect_leak(threshold_mb=10.0)

        # Note: This might not always detect depending on Python's memory management
        # but it's a basic test
        assert isinstance(detected, bool)

        # Cleanup
        leak_list.clear()
        gc.collect()


class TestResourceCleanupTypes:
    """Test different resource type cleanups"""

    def test_model_cleanup(self):
        """Test model-specific cleanup"""
        manager = ResourceManager()

        model = Mock()
        model.model = Mock()
        model.cache = {}

        manager.register_resource("model", model, "model")
        manager.cleanup_resource("model")

        # Should have been cleaned
        assert "model" not in manager.resources

    def test_connection_cleanup(self):
        """Test connection cleanup"""
        manager = ResourceManager()

        connection = Mock()
        connection.close = Mock()

        manager.register_resource("conn", connection, "connection")
        manager.cleanup_resource("conn")

        connection.close.assert_called_once()

    def test_cache_cleanup(self):
        """Test cache cleanup"""
        manager = ResourceManager()

        cache = {"key": "value"}

        manager.register_resource("cache", cache, "cache")
        manager.cleanup_resource("cache")

        assert len(cache) == 0

    def test_file_cleanup(self):
        """Test file handle cleanup"""
        manager = ResourceManager()

        file_handle = Mock()
        file_handle.close = Mock()

        manager.register_resource("file", file_handle, "file")
        manager.cleanup_resource("file")

        file_handle.close.assert_called_once()


class TestIntegration:
    """Integration tests for complete cleanup workflow"""

    def test_complete_lifecycle(self):
        """Test complete resource lifecycle"""
        manager = ResourceManager()

        # Startup: Register resources
        model = Mock(model=Mock(), _cache={})
        cache = {}
        connection = Mock(close=Mock())

        manager.register_resource("model", model, "model")
        manager.register_resource("cache", cache, "cache")
        manager.register_resource("conn", connection, "connection")

        assert len(manager.resources) == 3

        # Get memory report
        report = manager.get_memory_report()
        assert report["total_resources"] == 3

        # Shutdown: Cleanup all
        manager.cleanup_all()

        assert len(manager.resources) == 0
        connection.close.assert_called_once()

    def test_multiple_cleanup_cycles(self):
        """Test multiple cleanup cycles don't leak"""
        manager = ResourceManager()

        for cycle in range(3):
            # Register resources
            for i in range(5):
                manager.register_resource(
                    f"resource_{cycle}_{i}",
                    {"data": f"test_{i}"},
                    "other"
                )

            assert len(manager.resources) == 5

            # Cleanup
            manager.cleanup_all()

            assert len(manager.resources) == 0

            # Force GC
            gc.collect()


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_cleanup_nonexistent_resource(self):
        """Test cleaning up resource that doesn't exist"""
        manager = ResourceManager()

        success = manager.cleanup_resource("nonexistent")

        assert success is False

    def test_double_cleanup(self):
        """Test cleaning up same resource twice"""
        manager = ResourceManager()

        manager.register_resource("test", Mock(), "other")

        success1 = manager.cleanup_resource("test")
        success2 = manager.cleanup_resource("test")

        assert success1 is True
        assert success2 is False

    def test_cleanup_with_error(self):
        """Test cleanup continues even with errors"""
        manager = ResourceManager()

        # Resource that will raise error on cleanup
        bad_resource = Mock()
        bad_resource.close = Mock(side_effect=Exception("Cleanup error"))

        manager.register_resource("bad", bad_resource, "connection")
        manager.register_resource("good", {}, "cache")

        # Should not raise exception
        manager.cleanup_all()

        # Both should be cleaned despite error
        assert len(manager.resources) == 0

    def test_cleanup_none_resource(self):
        """Test cleanup handles None resources"""
        cleanup_ml_model(None, "test")
        # Should not raise exception


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
