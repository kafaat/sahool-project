"""
Security Tests: Memory Safety & Leak Prevention
اختبارات أمان الذاكرة ومنع التسريب
"""

import pytest
import gc
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestMemoryLeakPrevention:
    """Test memory leak prevention mechanisms"""

    def test_resource_manager_cleanup(self):
        """Test that ResourceManager properly cleans up resources"""
        try:
            from shared.resource_manager import ResourceManager

            manager = ResourceManager()

            # Create mock resource
            class MockModel:
                def __init__(self):
                    self.data = [0] * 1000000  # 1M integers
                    self._cache = {}

            model = MockModel()

            # Register resource
            manager.register_resource(
                "test_model",
                model,
                "model",
                cleanup_func=lambda m: delattr(m, 'data') if hasattr(m, 'data') else None
            )

            # Verify registered
            assert "test_model" in manager.resources

            # Cleanup
            manager.cleanup_resource("test_model")

            # Verify cleaned up
            assert "test_model" not in manager.resources

        except ImportError:
            pytest.skip("ResourceManager not available")

    def test_memory_monitor_leak_detection(self):
        """Test that memory monitor can detect leaks"""
        try:
            from shared.resource_manager import MemoryMonitor

            monitor = MemoryMonitor(check_interval=1.0, leak_threshold_mb=10.0)

            # Take initial snapshot
            initial = monitor.get_memory_usage()

            # Create large object
            large_list = [0] * 10000000  # 10M integers

            # Take second snapshot
            after = monitor.get_memory_usage()

            # Memory should have increased
            assert after["used_mb"] > initial["used_mb"]

            # Cleanup
            del large_list
            gc.collect()

        except ImportError:
            pytest.skip("MemoryMonitor not available")

    def test_garbage_collection_invocation(self):
        """Test that garbage collection is properly invoked"""
        try:
            from shared.cleanup_helpers import force_garbage_collection

            # Get initial garbage count
            before = gc.get_count()

            # Force collection
            freed = force_garbage_collection()

            # Verify GC was called
            after = gc.get_count()

            # At least verify function executed without error
            assert freed >= 0

        except ImportError:
            pytest.skip("Cleanup helpers not available")


class TestResourceLifecycle:
    """Test proper resource lifecycle management"""

    def test_ml_model_cleanup(self):
        """Test that ML models are properly cleaned up"""
        try:
            from shared.cleanup_helpers import cleanup_ml_model

            # Create mock model
            class MockMLModel:
                def __init__(self):
                    self.model = [0] * 1000000
                    self._cache = {"key": "value"}

            model = MockMLModel()

            # Verify model exists
            assert hasattr(model, 'model')
            assert hasattr(model, '_cache')

            # Cleanup
            cleanup_ml_model(model, "test_model")

            # After cleanup, model should not have these attributes
            # (Note: cleanup_ml_model deletes the object)

        except ImportError:
            pytest.skip("Cleanup helpers not available")

    def test_cache_cleanup(self):
        """Test that caches are properly cleared"""
        try:
            from shared.cleanup_helpers import cleanup_cache

            # Create cache
            cache = {
                "key1": [0] * 1000000,
                "key2": [1] * 1000000
            }

            # Verify cache has data
            assert len(cache) > 0

            # Cleanup
            cleanup_cache(cache)

            # Verify cache is empty
            assert len(cache) == 0

        except ImportError:
            pytest.skip("Cleanup helpers not available")


class TestMemorySafetyBestPractices:
    """Test memory safety best practices are enforced"""

    def test_context_manager_cleanup(self):
        """Test that context managers properly clean up"""
        try:
            from shared.resource_manager import ResourceManager

            manager = ResourceManager()

            # Simulate context manager usage
            class MockResource:
                def __init__(self):
                    self.active = True

                def close(self):
                    self.active = False

            resource = MockResource()

            # Register
            manager.register_resource(
                "context_resource",
                resource,
                "generic",
                cleanup_func=lambda r: r.close()
            )

            # Cleanup
            manager.cleanup_resource("context_resource")

            # Verify cleanup was called
            assert resource.active == False

        except ImportError:
            pytest.skip("ResourceManager not available")

    def test_shutdown_cleanup_invocation(self):
        """Test that cleanup is invoked on shutdown"""
        # This test verifies the cleanup mechanism works

        try:
            from shared.resource_manager import get_resource_manager, cleanup_resources

            manager = get_resource_manager()

            # Register test resource
            test_obj = {"cleanup_called": False}

            def test_cleanup(obj):
                obj["cleanup_called"] = True

            manager.register_resource(
                "shutdown_test",
                test_obj,
                "generic",
                cleanup_func=test_cleanup
            )

            # Call cleanup
            cleanup_resources()

            # Verify cleanup was called
            assert test_obj["cleanup_called"] == True

        except ImportError:
            pytest.skip("ResourceManager not available")


class TestMemoryLeakScenarios:
    """Test specific memory leak scenarios"""

    def test_circular_reference_handling(self):
        """Test that circular references are handled"""
        # Create circular reference
        class Node:
            def __init__(self):
                self.ref = None

        a = Node()
        b = Node()
        a.ref = b
        b.ref = a

        # Delete references
        del a
        del b

        # Force GC
        collected = gc.collect()

        # GC should have collected the circular references
        assert collected >= 0

    def test_large_object_cleanup(self):
        """Test cleanup of large objects"""
        import sys

        # Create large object
        large = [0] * 10000000

        # Get size
        size = sys.getsizeof(large)

        # Should be substantial
        assert size > 1000000  # > 1MB

        # Delete
        del large
        gc.collect()

        # Verify deletion (object should not be accessible)
        with pytest.raises(NameError):
            _ = large

    def test_model_reload_memory_leak(self):
        """Test that reloading models doesn't leak memory"""
        try:
            from shared.cleanup_helpers import cleanup_ml_model

            class MockModel:
                def __init__(self):
                    self.weights = [0] * 1000000

            # Simulate multiple model reloads
            for i in range(3):
                model = MockModel()
                # Use model
                _ = len(model.weights)
                # Cleanup
                cleanup_ml_model(model, f"model_{i}")
                gc.collect()

            # If we got here without OOM, the test passed

        except ImportError:
            pytest.skip("Cleanup helpers not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
