"""
API Routes
"""
from .advisor import router as advisor_router
from .health import router as health_router

__all__ = ["advisor_router", "health_router"]
