"""
ML Engine API Routes
RESTful API endpoints for all ML services
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ML Engine"])


# Pydantic Models
class CropPredictionRequest(BaseModel):
    """Crop yield prediction request"""
    field_id: Optional[int] = None
    crop_type: str = Field(..., description="Type of crop")
    field_area: float = Field(..., gt=0, description="Field area in hectares")
    ndvi_avg: float = Field(..., ge=0, le=1)
    ndvi_min: float = Field(..., ge=0, le=1)
    ndvi_max: float = Field(..., ge=0, le=1)
    ndvi_trend: float = Field(default=0.0)
    temp_avg: float
    temp_min: float
    temp_max: float
    rainfall_total: float = Field(..., ge=0)
    rainfall_days: int = Field(..., ge=0)
    soil_moisture_avg: float = Field(..., ge=0, le=100)
    soil_ph: float = Field(default=6.5, ge=0, le=14)
    soil_ec: float = Field(default=0.5, ge=0)
    days_since_planting: int = Field(..., ge=0)


class SoilAnalysisRequest(BaseModel):
    """Soil analysis request"""
    field_id: Optional[int] = None
    ph: float = Field(..., ge=0, le=14)
    ec: float = Field(..., ge=0)
    nitrogen: float = Field(..., ge=0, description="Nitrogen in ppm")
    phosphorus: float = Field(..., ge=0, description="Phosphorus in ppm")
    potassium: float = Field(..., ge=0, description="Potassium in ppm")
    moisture: float = Field(..., ge=0, le=100, description="Moisture percentage")
    organic_matter: float = Field(default=3.0, ge=0, description="Organic matter percentage")


class WeatherForecastRequest(BaseModel):
    """Weather forecast request"""
    field_id: Optional[int] = None
    location: Optional[Dict[str, float]] = None
    historical_data: Optional[List[Dict[str, Any]]] = None
    forecast_days: int = Field(default=7, ge=1, le=14)


# Crop Yield Prediction Endpoints

@router.post("/predict/crop-yield", summary="Predict Crop Yield")
async def predict_crop_yield(request: CropPredictionRequest, req: Request):
    """
    Predict crop yield based on field conditions

    Uses machine learning to estimate expected yield considering:
    - NDVI values (vegetation health)
    - Weather conditions
    - Soil properties
    - Crop type and growth stage
    """
    try:
        crop_predictor = req.app.state.crop_predictor

        if not crop_predictor or not crop_predictor.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Crop prediction model not available"
            )

        # Convert request to dictionary
        field_data = request.dict()

        # Make prediction
        result = await crop_predictor.predict_yield(field_data)

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in crop yield prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during prediction"
        )


@router.post("/predict/crop-yield/batch", summary="Batch Crop Yield Prediction")
async def batch_predict_crop_yield(requests: List[CropPredictionRequest], req: Request):
    """
    Batch prediction for multiple fields

    Efficiently process yield predictions for multiple fields at once
    """
    try:
        crop_predictor = req.app.state.crop_predictor

        if not crop_predictor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model not available"
            )

        fields_data = [r.dict() for r in requests]
        results = await crop_predictor.batch_predict(fields_data)

        return {
            "total_fields": len(results),
            "predictions": results
        }

    except Exception as e:
        logger.error(f"Error in batch prediction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Disease Detection Endpoints

@router.post("/detect/disease", summary="Detect Crop Disease")
async def detect_disease(
    image: UploadFile = File(..., description="Crop leaf image"),
    field_id: Optional[int] = None,
    req: Request = None
):
    """
    Detect crop diseases from leaf images

    Upload an image of a crop leaf to detect diseases using computer vision.
    Supports detection of 10+ common crop diseases.
    """
    try:
        disease_detector = req.app.state.disease_detector

        if not disease_detector or not disease_detector.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Disease detection model not available"
            )

        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        # Read image data
        image_data = await image.read()

        # Prepare metadata
        metadata = {
            "filename": image.filename,
            "field_id": field_id
        }

        # Detect disease
        result = await disease_detector.detect_disease(image_data, metadata)

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in disease detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during detection"
        )


@router.get("/detect/disease/classes", summary="Get Disease Classes")
async def get_disease_classes(req: Request):
    """Get list of detectable disease classes"""
    try:
        disease_detector = req.app.state.disease_detector

        if not disease_detector:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        return {
            "classes": disease_detector.class_names,
            "total_classes": len(disease_detector.class_names),
            "disease_info": disease_detector.disease_info
        }

    except Exception as e:
        logger.error(f"Error getting disease classes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Soil Analysis Endpoints

@router.post("/analyze/soil", summary="Analyze Soil Quality")
async def analyze_soil(request: SoilAnalysisRequest, req: Request):
    """
    Analyze soil quality and get recommendations

    Analyzes soil parameters including:
    - pH level
    - Electrical conductivity (EC)
    - Nutrient levels (N, P, K)
    - Moisture content
    - Organic matter

    Returns quality scores and improvement recommendations
    """
    try:
        soil_analyzer = req.app.state.soil_analyzer

        if not soil_analyzer or not soil_analyzer.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Soil analyzer not available"
            )

        # Analyze soil
        result = await soil_analyzer.analyze_soil(request.dict())

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in soil analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during analysis"
        )


# Weather Forecasting Endpoints

@router.post("/forecast/weather", summary="Forecast Weather")
async def forecast_weather(request: WeatherForecastRequest, req: Request):
    """
    Generate weather forecast using ML

    Predicts weather conditions for agricultural planning including:
    - Temperature trends
    - Rainfall predictions
    - Humidity levels
    - Wind speed
    - Agricultural impact assessment
    """
    try:
        weather_forecaster = req.app.state.weather_forecaster

        if not weather_forecaster or not weather_forecaster.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Weather forecaster not available"
            )

        # Forecast weather
        result = await weather_forecaster.forecast_weather(
            request.historical_data or [],
            request.forecast_days
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in weather forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during forecasting"
        )


# Combined Analysis Endpoints

@router.post("/analyze/field-comprehensive", summary="Comprehensive Field Analysis")
async def comprehensive_field_analysis(
    field_id: int,
    crop_data: Optional[CropPredictionRequest] = None,
    soil_data: Optional[SoilAnalysisRequest] = None,
    weather_request: Optional[WeatherForecastRequest] = None,
    req: Request = None
):
    """
    Comprehensive field analysis combining multiple ML models

    Provides holistic analysis including:
    - Crop yield prediction
    - Soil quality assessment
    - Weather forecast
    - Integrated recommendations
    """
    try:
        results = {
            "field_id": field_id,
            "analyses": {}
        }

        # Crop prediction
        if crop_data and req.app.state.crop_predictor:
            crop_result = await req.app.state.crop_predictor.predict_yield(crop_data.dict())
            results["analyses"]["crop_prediction"] = crop_result

        # Soil analysis
        if soil_data and req.app.state.soil_analyzer:
            soil_result = await req.app.state.soil_analyzer.analyze_soil(soil_data.dict())
            results["analyses"]["soil_analysis"] = soil_result

        # Weather forecast
        if weather_request and req.app.state.weather_forecaster:
            weather_result = await req.app.state.weather_forecaster.forecast_weather(
                weather_request.historical_data or [],
                weather_request.forecast_days
            )
            results["analyses"]["weather_forecast"] = weather_result

        # Generate integrated recommendations
        results["integrated_recommendations"] = _generate_integrated_recommendations(results["analyses"])

        return results

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


def _generate_integrated_recommendations(analyses: Dict[str, Any]) -> List[str]:
    """Generate integrated recommendations from multiple analyses"""
    recommendations = []

    # Crop predictions
    if "crop_prediction" in analyses:
        crop = analyses["crop_prediction"]
        if crop.get("predicted_yield", 0) < 3.0:
            recommendations.append("⚠️  Low yield predicted. Review all factors and consider interventions.")

    # Soil analysis
    if "soil_analysis" in analyses:
        soil = analyses["soil_analysis"]
        if soil.get("overall_quality") == "poor":
            recommendations.append("❌ Soil quality needs significant improvement.")

    # Weather forecast
    if "weather_forecast" in analyses:
        weather = analyses["weather_forecast"]
        impact = weather.get("agricultural_impact", {})
        if impact.get("risk_level") in ["high", "critical"]:
            recommendations.append(f"⚠️  Weather risk level: {impact['risk_level'].upper()}")

    if not recommendations:
        recommendations.append("✅ All systems indicate favorable conditions.")

    return recommendations


# Statistics and Monitoring

@router.get("/stats", summary="Get ML Engine Statistics")
async def get_stats():
    """Get ML engine usage statistics"""
    return {
        "service": "ml-engine",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "crop_prediction": "/predict/crop-yield",
            "disease_detection": "/detect/disease",
            "soil_analysis": "/analyze/soil",
            "weather_forecast": "/forecast/weather",
            "comprehensive": "/analyze/field-comprehensive"
        }
    }
