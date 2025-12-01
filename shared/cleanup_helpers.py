"""
Cleanup Helper Functions
Easy-to-use cleanup utilities for FastAPI applications
"""

import gc
import logging
from typing import Any, Dict, List, Optional, Callable
import weakref

logger = logging.getLogger(__name__)


def cleanup_ml_model(model: Any, model_name: str = "model"):
    """
    Clean up a single ML model

    Args:
        model: Model object to cleanup
        model_name: Name for logging
    """
    if model is None:
        return

    try:
        # Step 1: Call model's cleanup method if exists
        if hasattr(model, 'cleanup'):
            model.cleanup()
            logger.debug(f"Called cleanup() on {model_name}")

        # Step 2: Delete model weights/parameters
        if hasattr(model, 'model') and model.model is not None:
            del model.model
            logger.debug(f"Deleted {model_name}.model")

        # Step 3: Clear caches
        for cache_attr in ['_cache', 'cache', '_predictions_cache']:
            if hasattr(model, cache_attr):
                cache = getattr(model, cache_attr)
                if hasattr(cache, 'clear'):
                    cache.clear()
                    logger.debug(f"Cleared {model_name}.{cache_attr}")

        # Step 4: Delete the model object itself
        del model
        logger.info(f"✅ Cleaned up {model_name}")

    except Exception as e:
        logger.error(f"Error cleaning up {model_name}: {e}")


def cleanup_ml_models_dict(models: Dict[str, Any]):
    """
    Clean up multiple ML models from a dictionary

    Args:
        models: Dictionary of model_name -> model_object
    """
    logger.info(f"Cleaning up {len(models)} ML models...")

    for name, model in list(models.items()):
        cleanup_ml_model(model, name)
        models[name] = None

    models.clear()

    # Force garbage collection
    collected = gc.collect()
    logger.info(f"GC collected {collected} objects")


def cleanup_connections(connections: List[Any]):
    """
    Clean up database/network connections

    Args:
        connections: List of connection objects
    """
    logger.info(f"Closing {len(connections)} connections...")

    for conn in connections:
        try:
            if hasattr(conn, 'close'):
                conn.close()
            elif hasattr(conn, 'disconnect'):
                conn.disconnect()
            logger.debug("Connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    connections.clear()


def cleanup_caches(*caches):
    """
    Clear multiple caches

    Args:
        *caches: Variable number of cache objects (dicts, lists, or objects with clear())
    """
    logger.info(f"Clearing {len(caches)} caches...")

    for cache in caches:
        try:
            if cache is None:
                continue

            if hasattr(cache, 'clear'):
                cache.clear()
            elif isinstance(cache, dict):
                cache.clear()
            elif isinstance(cache, list):
                cache.clear()

            logger.debug("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


def force_garbage_collection(generations: int = 2) -> int:
    """
    Force garbage collection

    Args:
        generations: Number of GC generations to collect (0-2)

    Returns:
        Number of objects collected
    """
    total_collected = 0

    for gen in range(generations + 1):
        collected = gc.collect(gen)
        total_collected += collected

    logger.info(f"GC collected {total_collected} objects across {generations + 1} generations")
    return total_collected


def get_memory_info() -> Dict[str, float]:
    """
    Get current memory usage

    Returns:
        Dict with memory info in MB
    """
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem = process.memory_info()

        return {
            "rss_mb": mem.rss / 1024 / 1024,
            "vms_mb": mem.vms / 1024 / 1024,
            "percent": process.memory_percent()
        }
    except ImportError:
        logger.warning("psutil not installed, cannot get memory info")
        return {}


def log_memory_usage(label: str = ""):
    """Log current memory usage"""
    mem = get_memory_info()
    if mem:
        logger.info(
            f"Memory {label}: "
            f"RSS={mem['rss_mb']:.1f}MB, "
            f"VMS={mem['vms_mb']:.1f}MB, "
            f"Usage={mem['percent']:.1f}%"
        )


# Quick cleanup decorator
def with_cleanup(cleanup_func: Callable):
    """
    Decorator to ensure cleanup is called

    Example:
        @with_cleanup(lambda: cleanup_ml_models(models))
        async def my_function():
            # ... code that uses models
            pass
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            finally:
                cleanup_func()

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                cleanup_func()

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Context manager for cleanup
class CleanupContext:
    """
    Context manager for automatic cleanup

    Example:
        with CleanupContext([model1, model2], cleanup_func=cleanup_ml_model):
            # ... use models
            pass
        # Models are automatically cleaned up
    """

    def __init__(
        self,
        resources: List[Any],
        cleanup_func: Optional[Callable] = None,
        force_gc: bool = True
    ):
        self.resources = resources
        self.cleanup_func = cleanup_func
        self.force_gc = force_gc

    def __enter__(self):
        return self.resources

    def __exit__(self, exc_type, exc_val, exc_tb):
        for resource in self.resources:
            try:
                if self.cleanup_func:
                    self.cleanup_func(resource)
                else:
                    del resource
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")

        if self.force_gc:
            gc.collect()

        return False  # Don't suppress exceptions


# Simple cleanup function for FastAPI lifespan
def create_cleanup_handler(*resources_to_cleanup):
    """
    Create a cleanup handler function for FastAPI lifespan

    Args:
        *resources_to_cleanup: Variable number of (name, resource, type) tuples

    Returns:
        Cleanup function

    Example:
        models = {
            "model1": model1_obj,
            "model2": model2_obj
        }

        cleanup_handler = create_cleanup_handler(
            ("models", models, "models_dict"),
            ("cache", my_cache, "cache")
        )

        # Use in lifespan:
        yield
        cleanup_handler()
    """

    def cleanup():
        logger.info(f"Running cleanup for {len(resources_to_cleanup)} resource groups...")

        for name, resource, resource_type in resources_to_cleanup:
            try:
                if resource_type == "models_dict":
                    cleanup_ml_models_dict(resource)
                elif resource_type == "model":
                    cleanup_ml_model(resource, name)
                elif resource_type == "cache":
                    cleanup_caches(resource)
                elif resource_type == "connections":
                    cleanup_connections(resource)
                else:
                    del resource

            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")

        # Final GC
        force_garbage_collection()

    return cleanup
