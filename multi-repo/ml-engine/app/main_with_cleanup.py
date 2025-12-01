"""
ML Engine Service with Comprehensive Resource Cleanup
Prevents memory leaks through proper resource management
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import gc
from typing import Optional
import sys

# Add shared path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.resource_manager import get_resource_manager, cleanup_resources
from app.services.crop_predictor import CropYieldPredictor
from app.services.disease_detector import DiseaseDetector
from app.services.soil_analyzer import SoilAnalyzer
from app.services.weather_forecaster import WeatherForecaster
from app.api import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ML models
crop_predictor: Optional[CropYieldPredictor] = None
disease_detector: Optional[DiseaseDetector] = None
soil_analyzer: Optional[SoilAnalyzer] = None
weather_forecaster: Optional[WeatherForecaster] = None


def cleanup_ml_models():
    """Custom cleanup function for ML models"""
    global crop_predictor, disease_detector, soil_analyzer, weather_forecaster

    logger.info("🧹 Cleaning up ML models...")

    models = [
        ("crop_predictor", crop_predictor),
        ("disease_detector", disease_detector),
        ("soil_analyzer", soil_analyzer),
        ("weather_forecaster", weather_forecaster)
    ]

    for name, model in models:
        if model is not None:
            try:
                # Call model-specific cleanup if available
                if hasattr(model, 'cleanup'):
                    model.cleanup()

                # Delete model weights
                if hasattr(model, 'model') and model.model is not None:
                    del model.model
                    logger.debug(f"Deleted {name} model weights")

                # Clear any caches
                if hasattr(model, '_cache'):
                    model._cache.clear()
                    logger.debug(f"Cleared {name} cache")

                # Delete the model object
                del model
                logger.debug(f"Deleted {name} object")

            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")

    # Clear global references
    crop_predictor = None
    disease_detector = None
    soil_analyzer = None
    weather_forecaster = None

    # Force garbage collection
    collected = gc.collect()
    logger.info(f"✅ ML models cleaned up, GC collected {collected} objects")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with resource management"""
    global crop_predictor, disease_detector, soil_analyzer, weather_forecaster

    # Get resource manager
    resource_manager = get_resource_manager()

    # Startup
    logger.info("🚀 Starting ML Engine Service with Resource Management...")

    # Take initial memory snapshot
    resource_manager.memory_monitor.take_snapshot("startup")

    try:
        logger.info("📊 Loading ML models...")

        # Initialize and register ML models
        with resource_manager.track_memory("crop_predictor_load"):
            crop_predictor = CropYieldPredictor()
            await crop_predictor.load_model()
            resource_manager.register_resource(
                name="crop_predictor",
                resource=crop_predictor,
                resource_type="model",
                metadata={"model_type": "crop_yield"}
            )
            logger.info("✅ Crop Yield Predictor loaded")

        with resource_manager.track_memory("disease_detector_load"):
            disease_detector = DiseaseDetector()
            await disease_detector.load_model()
            resource_manager.register_resource(
                name="disease_detector",
                resource=disease_detector,
                resource_type="model",
                metadata={"model_type": "disease_detection"}
            )
            logger.info("✅ Disease Detector loaded")

        with resource_manager.track_memory("soil_analyzer_load"):
            soil_analyzer = SoilAnalyzer()
            await soil_analyzer.load_model()
            resource_manager.register_resource(
                name="soil_analyzer",
                resource=soil_analyzer,
                resource_type="model",
                metadata={"model_type": "soil_analysis"}
            )
            logger.info("✅ Soil Analyzer loaded")

        with resource_manager.track_memory("weather_forecaster_load"):
            weather_forecaster = WeatherForecaster()
            await weather_forecaster.load_model()
            resource_manager.register_resource(
                name="weather_forecaster",
                resource=weather_forecaster,
                resource_type="model",
                metadata={"model_type": "weather_forecast"}
            )
            logger.info("✅ Weather Forecaster loaded")

        logger.info("🎉 All ML models loaded successfully!")

        # Log memory status after loading
        resource_manager.log_status()

    except Exception as e:
        logger.error(f"❌ Error loading ML models: {e}", exc_info=True)
        logger.warning("⚠️  Running in limited mode without ML models")

    # Register cleanup callback
    resource_manager.add_cleanup_callback(cleanup_ml_models)

    yield

    # Shutdown - CRITICAL: Cleanup all resources!
    logger.info("🛑 Shutting down ML Engine Service...")

    # Take memory snapshot before cleanup
    resource_manager.memory_monitor.take_snapshot("before_shutdown_cleanup")

    # Cleanup all managed resources
    cleanup_resources()

    # Final garbage collection
    gc.collect()

    # Take final memory snapshot
    resource_manager.memory_monitor.take_snapshot("after_shutdown_cleanup")

    # Log final memory report
    report = resource_manager.get_memory_report()
    logger.info(
        f"📊 Final Memory Report - "
        f"Resources cleaned: {report['total_resources']}, "
        f"Memory freed: {-report['memory_delta']['rss_delta_mb']:.1f}MB"
    )

    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Sahool ML Engine (with Cleanup)",
    description="ML service with comprehensive resource management and memory leak prevention",
    version="3.2.5",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:9000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    max_age=3600,
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root():
    """Root endpoint - Service information"""
    return {
        "service": "Sahool ML Engine (with Cleanup)",
        "version": "3.2.5",
        "status": "running",
        "features": ["resource_management", "memory_leak_prevention", "cleanup_on_shutdown"],
        "models": {
            "crop_predictor": crop_predictor is not None,
            "disease_detector": disease_detector is not None,
            "soil_analyzer": soil_analyzer is not None,
            "weather_forecaster": weather_forecaster is not None,
        },
        "docs": "/docs"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint with memory monitoring"""
    models_status = {
        "crop_predictor": "loaded" if crop_predictor and crop_predictor.is_ready() else "not_loaded",
        "disease_detector": "loaded" if disease_detector and disease_detector.is_ready() else "not_loaded",
        "soil_analyzer": "loaded" if soil_analyzer and soil_analyzer.is_ready() else "not_loaded",
        "weather_forecaster": "loaded" if weather_forecaster and weather_forecaster.is_ready() else "not_loaded",
    }

    all_loaded = all(status == "loaded" for status in models_status.values())

    # Get memory info
    resource_manager = get_resource_manager()
    memory_report = resource_manager.get_memory_report()

    return {
        "status": "healthy" if all_loaded else "degraded",
        "service": "ml-engine",
        "version": "3.2.5",
        "models": models_status,
        "memory": {
            "rss_mb": memory_report["current_memory"]["rss_mb"],
            "usage_percent": memory_report["current_memory"]["percent"],
            "leak_detected": memory_report["leak_detected"]
        }
    }


@app.get("/models/info", tags=["System"])
async def models_info():
    """Get information about loaded models"""
    return {
        "crop_predictor": crop_predictor.get_info() if crop_predictor else None,
        "disease_detector": disease_detector.get_info() if disease_detector else None,
        "soil_analyzer": soil_analyzer.get_info() if soil_analyzer else None,
        "weather_forecaster": weather_forecaster.get_info() if weather_forecaster else None,
    }


@app.get("/memory/status", tags=["System"])
async def memory_status():
    """Get detailed memory status"""
    resource_manager = get_resource_manager()
    report = resource_manager.get_memory_report()

    return {
        "current_memory_mb": report["current_memory"]["rss_mb"],
        "memory_usage_percent": report["current_memory"]["percent"],
        "memory_delta_mb": report["memory_delta"]["rss_delta_mb"],
        "total_resources": report["total_resources"],
        "resources_by_type": report["resources_by_type"],
        "estimated_model_memory_mb": report["estimated_resource_memory_mb"],
        "leak_detected": report["leak_detected"],
        "snapshots": resource_manager.memory_monitor.snapshots[-10:]  # Last 10 snapshots
    }


@app.post("/memory/gc", tags=["System"])
async def force_garbage_collection():
    """Force garbage collection (admin only)"""
    before = get_resource_manager().memory_monitor.get_memory_usage()

    collected = gc.collect()

    after = get_resource_manager().memory_monitor.get_memory_usage()
    freed_mb = before["rss_mb"] - after["rss_mb"]

    return {
        "objects_collected": collected,
        "memory_freed_mb": freed_mb,
        "before_mb": before["rss_mb"],
        "after_mb": after["rss_mb"]
    }


# Make models available to routes
app.state.crop_predictor = crop_predictor
app.state.disease_detector = disease_detector
app.state.soil_analyzer = soil_analyzer
app.state.weather_forecaster = weather_forecaster


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010,
        log_level="info",
        access_log=True
    )
