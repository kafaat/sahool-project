"""
ML Engine Service - Sahool Agricultural Platform
Advanced Machine Learning service for crop prediction, disease detection, and analytics
"""

from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global crop_predictor, disease_detector, soil_analyzer, weather_forecaster

    # Startup
    logger.info("🚀 Starting ML Engine Service...")
    logger.info("📊 Loading ML models...")

    try:
        # Initialize ML models
        crop_predictor = CropYieldPredictor()
        await crop_predictor.load_model()
        logger.info("✅ Crop Yield Predictor loaded")

        disease_detector = DiseaseDetector()
        await disease_detector.load_model()
        logger.info("✅ Disease Detector loaded")

        soil_analyzer = SoilAnalyzer()
        await soil_analyzer.load_model()
        logger.info("✅ Soil Analyzer loaded")

        weather_forecaster = WeatherForecaster()
        await weather_forecaster.load_model()
        logger.info("✅ Weather Forecaster loaded")

        logger.info("🎉 All ML models loaded successfully!")

    except Exception as e:
        logger.error(f"❌ Error loading ML models: {e}", exc_info=True)
        logger.warning("⚠️  Running in limited mode without ML models")

    yield

    # Shutdown
    logger.info("🛑 Shutting down ML Engine Service...")


# Create FastAPI application
app = FastAPI(
    title="Sahool ML Engine",
    description="Advanced Machine Learning service for agricultural intelligence",
    version="1.0.0",
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
        "service": "Sahool ML Engine",
        "version": "1.0.0",
        "status": "running",
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
    """Health check endpoint"""
    models_status = {
        "crop_predictor": "loaded" if crop_predictor and crop_predictor.is_ready() else "not_loaded",
        "disease_detector": "loaded" if disease_detector and disease_detector.is_ready() else "not_loaded",
        "soil_analyzer": "loaded" if soil_analyzer and soil_analyzer.is_ready() else "not_loaded",
        "weather_forecaster": "loaded" if weather_forecaster and weather_forecaster.is_ready() else "not_loaded",
    }

    all_loaded = all(status == "loaded" for status in models_status.values())

    return {
        "status": "healthy" if all_loaded else "degraded",
        "service": "ml-engine",
        "version": "1.0.0",
        "models": models_status
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
