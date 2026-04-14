#!/bin/bash
# ==============================================================================
# Part 03: Advisor Service
# Smart recommendations engine with ML capabilities
# ==============================================================================

generate_advisor_service() {
    log_info "Creating Advisor Service with ML Engine..."

    local SERVICE_DIR="services/advisor-service"
    mkdir -p "$SERVICE_DIR"/{app/{api,models,services,engine,ml,core},tests,models}

    # ------------------------------------------------------------------------------
    # Service Configuration
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/core/config.py" << 'PYEOF'
"""Advisor Service Configuration"""
from functools import lru_cache
import sys
sys.path.insert(0, "/app/shared")

from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Advisor service specific settings"""
    SERVICE_NAME: str = "advisor-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8003

    # Service URLs
    FIELD_SERVICE_URL: str = "http://field-service:8001"
    NDVI_SERVICE_URL: str = "http://ndvi-service:8002"

    # ML Model
    ML_MODEL_PATH: str = "/app/models/advisor_model.pkl"
    USE_ML_MODEL: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
PYEOF

    # ------------------------------------------------------------------------------
    # Rules Engine (Fallback when ML not available)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/engine/rules.py" << 'PYEOF'
"""
Rules-based recommendation engine
Fallback when ML model is not available
"""
from typing import List, Dict, Any
from enum import Enum


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationType(str, Enum):
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    HARVEST = "harvest"
    GENERAL = "general"


# NDVI-based rules
NDVI_RULES = [
    {
        "name": "critical_vegetation_stress",
        "condition": lambda ctx: ctx.get("ndvi_mean", 0) < 0.2,
        "recommendation": {
            "type": RecommendationType.IRRIGATION,
            "priority": Priority.CRITICAL,
            "title": "Critical Vegetation Stress Detected",
            "title_ar": "ضغط حرج على الغطاء النباتي",
            "description": "NDVI values indicate severe vegetation stress. Immediate action required.",
            "action": "Implement emergency irrigation and soil analysis",
            "action_ar": "تنفيذ الري الطارئ وتحليل التربة",
            "confidence": 0.95,
        }
    },
    {
        "name": "low_vegetation",
        "condition": lambda ctx: 0.2 <= ctx.get("ndvi_mean", 0) < 0.4,
        "recommendation": {
            "type": RecommendationType.FERTILIZATION,
            "priority": Priority.HIGH,
            "title": "Low Vegetation Health",
            "title_ar": "صحة نباتية منخفضة",
            "description": "Vegetation health is below optimal. Consider fertilization.",
            "action": "Apply nitrogen-rich fertilizer and increase irrigation",
            "action_ar": "تطبيق سماد غني بالنيتروجين وزيادة الري",
            "confidence": 0.85,
        }
    },
    {
        "name": "moderate_vegetation",
        "condition": lambda ctx: 0.4 <= ctx.get("ndvi_mean", 0) < 0.6,
        "recommendation": {
            "type": RecommendationType.GENERAL,
            "priority": Priority.MEDIUM,
            "title": "Moderate Vegetation Health",
            "title_ar": "صحة نباتية متوسطة",
            "description": "Vegetation is growing but could be improved.",
            "action": "Monitor closely and consider targeted fertilization",
            "action_ar": "مراقبة دقيقة والنظر في التسميد المستهدف",
            "confidence": 0.75,
        }
    },
    {
        "name": "good_vegetation",
        "condition": lambda ctx: 0.6 <= ctx.get("ndvi_mean", 0) < 0.8,
        "recommendation": {
            "type": RecommendationType.GENERAL,
            "priority": Priority.LOW,
            "title": "Good Vegetation Health",
            "title_ar": "صحة نباتية جيدة",
            "description": "Vegetation is healthy. Maintain current practices.",
            "action": "Continue current irrigation and fertilization schedule",
            "action_ar": "الاستمرار في جدول الري والتسميد الحالي",
            "confidence": 0.90,
        }
    },
    {
        "name": "excellent_vegetation",
        "condition": lambda ctx: ctx.get("ndvi_mean", 0) >= 0.8,
        "recommendation": {
            "type": RecommendationType.HARVEST,
            "priority": Priority.MEDIUM,
            "title": "Excellent Vegetation - Consider Harvest",
            "title_ar": "نباتات ممتازة - النظر في الحصاد",
            "description": "Vegetation is at peak health. May be ready for harvest.",
            "action": "Assess crop maturity and plan harvest timing",
            "action_ar": "تقييم نضج المحصول والتخطيط لتوقيت الحصاد",
            "confidence": 0.80,
        }
    },
]

# Weather-based rules
WEATHER_RULES = [
    {
        "name": "high_temperature",
        "condition": lambda ctx: ctx.get("temperature", 20) > 35,
        "recommendation": {
            "type": RecommendationType.IRRIGATION,
            "priority": Priority.HIGH,
            "title": "High Temperature Alert",
            "title_ar": "تنبيه درجة حرارة عالية",
            "description": "High temperatures detected. Plants may need extra water.",
            "action": "Increase irrigation frequency during peak heat",
            "action_ar": "زيادة تكرار الري خلال ذروة الحرارة",
            "confidence": 0.85,
        }
    },
    {
        "name": "low_humidity",
        "condition": lambda ctx: ctx.get("humidity", 50) < 30,
        "recommendation": {
            "type": RecommendationType.IRRIGATION,
            "priority": Priority.MEDIUM,
            "title": "Low Humidity Warning",
            "title_ar": "تحذير رطوبة منخفضة",
            "description": "Low humidity may increase water loss.",
            "action": "Consider mulching and drip irrigation",
            "action_ar": "النظر في التغطية والري بالتنقيط",
            "confidence": 0.75,
        }
    },
]


class RulesEngine:
    """Rules-based recommendation engine"""

    def __init__(self):
        self.all_rules = NDVI_RULES + WEATHER_RULES

    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all rules against context"""
        recommendations = []

        for rule in self.all_rules:
            try:
                if rule["condition"](context):
                    rec = rule["recommendation"].copy()
                    rec["rule_name"] = rule["name"]
                    rec["type"] = rec["type"].value
                    rec["priority"] = rec["priority"].value
                    recommendations.append(rec)
            except Exception:
                continue

        # Sort by priority
        priority_order = {
            Priority.CRITICAL.value: 0,
            Priority.HIGH.value: 1,
            Priority.MEDIUM.value: 2,
            Priority.LOW.value: 3,
        }
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))

        return recommendations
PYEOF

    # ------------------------------------------------------------------------------
    # ML Model (Predictive Advisor)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/ml/predictor.py" << 'PYEOF'
"""
ML-based Advisor Predictor
Uses trained model for intelligent recommendations
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pickle

import numpy as np

logger = logging.getLogger(__name__)


class AdvisorPredictor:
    """ML model for agricultural recommendations"""

    # Feature names expected by the model
    FEATURES = [
        "ndvi_mean",
        "ndvi_min",
        "ndvi_max",
        "ndvi_std",
        "ndvi_trend",  # -1 declining, 0 stable, 1 improving
        "temperature",
        "humidity",
        "soil_moisture",
        "days_since_irrigation",
        "days_since_fertilization",
        "crop_growth_stage",  # 0-4 (seedling to harvest)
    ]

    # Output classes
    RECOMMENDATIONS = [
        "no_action",
        "irrigate_light",
        "irrigate_heavy",
        "fertilize_nitrogen",
        "fertilize_phosphorus",
        "pest_inspection",
        "harvest_soon",
        "emergency_action",
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Load trained model from disk"""
        if self.model_path and Path(self.model_path).exists():
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"ML model loaded from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
                self.model = None
        else:
            logger.info("No ML model found, using rule-based fallback")

    def predict(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Predict recommendations using ML model

        Args:
            context: Dictionary with feature values

        Returns:
            List of recommendations with confidence scores
        """
        if self.model is None:
            return self._fallback_predict(context)

        try:
            # Extract features
            features = self._extract_features(context)

            # Get prediction probabilities
            probabilities = self.model.predict_proba([features])[0]

            # Build recommendations from top predictions
            recommendations = []
            for idx, prob in enumerate(probabilities):
                if prob > 0.1:  # Threshold
                    rec_type = self.RECOMMENDATIONS[idx]
                    recommendations.append(
                        self._build_recommendation(rec_type, prob, context)
                    )

            # Sort by confidence
            recommendations.sort(key=lambda x: x["confidence"], reverse=True)
            return recommendations[:5]  # Top 5

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._fallback_predict(context)

    def _extract_features(self, context: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector from context"""
        features = []
        for feat in self.FEATURES:
            value = context.get(feat, 0)
            if value is None:
                value = 0
            features.append(float(value))
        return np.array(features)

    def _fallback_predict(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simple rule-based fallback when ML model unavailable"""
        recommendations = []
        ndvi = context.get("ndvi_mean", 0.5)

        if ndvi < 0.3:
            recommendations.append({
                "type": "irrigation",
                "priority": "critical",
                "title": "Immediate Irrigation Needed",
                "action": "Apply emergency irrigation",
                "confidence": 0.9,
                "source": "fallback_rules",
            })
        elif ndvi < 0.5:
            recommendations.append({
                "type": "fertilization",
                "priority": "high",
                "title": "Consider Fertilization",
                "action": "Apply balanced fertilizer",
                "confidence": 0.75,
                "source": "fallback_rules",
            })

        return recommendations

    def _build_recommendation(
        self,
        rec_type: str,
        confidence: float,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build detailed recommendation from prediction"""

        # Recommendation templates
        templates = {
            "no_action": {
                "type": "general",
                "priority": "low",
                "title": "Field Healthy - No Action Required",
                "action": "Continue monitoring",
            },
            "irrigate_light": {
                "type": "irrigation",
                "priority": "medium",
                "title": "Light Irrigation Recommended",
                "action": "Apply 10-15mm of water",
            },
            "irrigate_heavy": {
                "type": "irrigation",
                "priority": "high",
                "title": "Heavy Irrigation Needed",
                "action": "Apply 25-30mm of water immediately",
            },
            "fertilize_nitrogen": {
                "type": "fertilization",
                "priority": "medium",
                "title": "Nitrogen Fertilization Recommended",
                "action": "Apply nitrogen-rich fertilizer (46-0-0)",
            },
            "fertilize_phosphorus": {
                "type": "fertilization",
                "priority": "medium",
                "title": "Phosphorus Boost Needed",
                "action": "Apply phosphorus fertilizer (0-46-0)",
            },
            "pest_inspection": {
                "type": "pest_control",
                "priority": "high",
                "title": "Pest Inspection Required",
                "action": "Conduct field inspection for pests",
            },
            "harvest_soon": {
                "type": "harvest",
                "priority": "medium",
                "title": "Harvest Window Approaching",
                "action": "Prepare for harvest in 7-14 days",
            },
            "emergency_action": {
                "type": "general",
                "priority": "critical",
                "title": "Emergency Action Required",
                "action": "Immediate field inspection needed",
            },
        }

        template = templates.get(rec_type, templates["no_action"])

        return {
            **template,
            "confidence": round(confidence, 3),
            "source": "ml_model",
            "context_summary": {
                "ndvi": context.get("ndvi_mean"),
                "temperature": context.get("temperature"),
            },
        }


def create_sample_model(output_path: str):
    """Create a sample ML model for testing"""
    from sklearn.ensemble import RandomForestClassifier

    # Generate synthetic training data
    np.random.seed(42)
    n_samples = 1000

    X = np.random.rand(n_samples, len(AdvisorPredictor.FEATURES))
    y = np.random.randint(0, len(AdvisorPredictor.RECOMMENDATIONS), n_samples)

    # Train simple model
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)

    # Save model
    with open(output_path, "wb") as f:
        pickle.dump(model, f)

    print(f"Sample model saved to {output_path}")
PYEOF

    # ------------------------------------------------------------------------------
    # Advisor Service (Combines Rules + ML)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/services/advisor_service.py" << 'PYEOF'
"""Advisor Service - Orchestrates recommendations"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
import logging

from ..engine.rules import RulesEngine
from ..ml.predictor import AdvisorPredictor
from ..core.config import settings

logger = logging.getLogger(__name__)


class AdvisorService:
    """Main advisor service combining rules and ML"""

    def __init__(self):
        self.rules_engine = RulesEngine()
        self.ml_predictor = AdvisorPredictor(
            model_path=settings.ML_MODEL_PATH if settings.USE_ML_MODEL else None
        )

    async def analyze_field(
        self,
        field_id: int,
        tenant_id: str,
        include_weather: bool = True,
        include_ndvi: bool = True,
    ) -> Dict[str, Any]:
        """
        Comprehensive field analysis

        Args:
            field_id: Field to analyze
            tenant_id: Tenant ID
            include_weather: Include weather data
            include_ndvi: Include NDVI data

        Returns:
            Analysis result with recommendations
        """
        # Build context from various data sources
        context = await self._build_context(
            field_id, tenant_id, include_weather, include_ndvi
        )

        # Get ML predictions (primary)
        ml_recommendations = []
        if settings.USE_ML_MODEL:
            ml_recommendations = self.ml_predictor.predict(context)

        # Get rule-based recommendations (fallback/supplement)
        rule_recommendations = self.rules_engine.evaluate(context)

        # Merge and deduplicate
        all_recommendations = self._merge_recommendations(
            ml_recommendations, rule_recommendations
        )

        # Calculate overall health score
        health_score = self._calculate_health_score(context)

        # Generate alerts
        alerts = self._generate_alerts(context, all_recommendations)

        return {
            "field_id": field_id,
            "tenant_id": tenant_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "overall_health_score": health_score,
            "recommendations": all_recommendations,
            "alerts": alerts,
            "context_summary": {
                "ndvi_mean": context.get("ndvi_mean"),
                "ndvi_trend": context.get("ndvi_trend"),
                "temperature": context.get("temperature"),
                "data_sources": list(context.get("_sources", [])),
            },
            "next_actions": self._get_next_actions(all_recommendations),
        }

    async def _build_context(
        self,
        field_id: int,
        tenant_id: str,
        include_weather: bool,
        include_ndvi: bool,
    ) -> Dict[str, Any]:
        """Build analysis context from multiple data sources"""
        context = {
            "field_id": field_id,
            "tenant_id": tenant_id,
            "_sources": [],
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch NDVI data
            if include_ndvi:
                try:
                    resp = await client.get(
                        f"{settings.NDVI_SERVICE_URL}/api/v1/ndvi/field/{field_id}/latest"
                    )
                    if resp.status_code == 200:
                        ndvi_data = resp.json()
                        context.update({
                            "ndvi_mean": ndvi_data.get("mean_ndvi", 0.5),
                            "ndvi_min": ndvi_data.get("min_ndvi", 0),
                            "ndvi_max": ndvi_data.get("max_ndvi", 1),
                            "ndvi_std": ndvi_data.get("std_ndvi", 0),
                            "health_score": ndvi_data.get("health_score", 50),
                        })
                        context["_sources"].append("ndvi")
                except Exception as e:
                    logger.warning(f"Failed to fetch NDVI: {e}")

            # Fetch weather data (mock for now)
            if include_weather:
                context.update({
                    "temperature": 28,
                    "humidity": 55,
                    "precipitation": 0,
                })
                context["_sources"].append("weather")

            # Add defaults for missing values
            context.setdefault("ndvi_mean", 0.5)
            context.setdefault("ndvi_trend", 0)
            context.setdefault("soil_moisture", 50)
            context.setdefault("days_since_irrigation", 3)
            context.setdefault("days_since_fertilization", 14)
            context.setdefault("crop_growth_stage", 2)

        return context

    def _merge_recommendations(
        self,
        ml_recs: List[Dict],
        rule_recs: List[Dict]
    ) -> List[Dict]:
        """Merge ML and rule-based recommendations"""
        # Use ML as primary, add rule-based if not duplicated
        seen_types = {r["type"] for r in ml_recs}
        merged = list(ml_recs)

        for rec in rule_recs:
            if rec["type"] not in seen_types:
                merged.append(rec)
                seen_types.add(rec["type"])

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        merged.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))

        return merged[:10]  # Limit to top 10

    def _calculate_health_score(self, context: Dict) -> float:
        """Calculate overall field health score"""
        ndvi = context.get("ndvi_mean", 0.5)
        # Simple formula: NDVI contributes 70%, other factors 30%
        base_score = ndvi * 70

        # Adjust for other factors
        if context.get("temperature", 25) > 35:
            base_score -= 10
        if context.get("humidity", 50) < 30:
            base_score -= 5

        return round(min(100, max(0, base_score + 30)), 1)

    def _generate_alerts(
        self,
        context: Dict,
        recommendations: List[Dict]
    ) -> List[Dict]:
        """Generate alerts based on context and recommendations"""
        alerts = []

        # Critical recommendations become alerts
        for rec in recommendations:
            if rec.get("priority") == "critical":
                alerts.append({
                    "level": "critical",
                    "message": rec.get("title"),
                    "action": rec.get("action"),
                })

        # NDVI-based alerts
        ndvi = context.get("ndvi_mean", 0.5)
        if ndvi < 0.2:
            alerts.append({
                "level": "critical",
                "message": "Severe vegetation stress detected",
                "action": "Immediate field inspection required",
            })

        return alerts

    def _get_next_actions(self, recommendations: List[Dict]) -> List[str]:
        """Extract prioritized next actions"""
        actions = []
        for rec in recommendations[:3]:
            action = rec.get("action")
            if action:
                actions.append(action)
        return actions
PYEOF

    write_heredoc "$SERVICE_DIR/app/services/__init__.py" << 'PYEOF'
"""Services module"""
from .advisor_service import AdvisorService
PYEOF

    # ------------------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/core/deps.py" << 'PYEOF'
"""Dependencies for Advisor Service"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
sys.path.insert(0, "/app/shared")

from shared.utils import decode_token, TokenPayload
from .config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    token = credentials.credentials
    payload = decode_token(token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)

    if payload is None or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return payload
PYEOF

    # ------------------------------------------------------------------------------
    # API Routes
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/api/advisor.py" << 'PYEOF'
"""Advisor API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
import sys
sys.path.insert(0, "/app/shared")

from shared.schemas.advisor import (
    AdvisorAnalysisRequest, AdvisorAnalysisResponse, RecommendationResponse,
)
from shared.utils import TokenPayload

from ..core.deps import get_current_user
from ..services.advisor_service import AdvisorService

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/analyze", response_model=AdvisorAnalysisResponse)
async def analyze_field(
    request: AdvisorAnalysisRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Analyze field and get recommendations"""
    service = AdvisorService()

    if len(request.field_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail="Currently only single field analysis is supported",
        )

    result = await service.analyze_field(
        field_id=request.field_ids[0],
        tenant_id=current_user.tenant_id,
        include_weather=request.include_weather,
        include_ndvi=request.include_ndvi,
    )

    return result


@router.get("/field/{field_id}", response_model=AdvisorAnalysisResponse)
async def get_field_analysis(
    field_id: int,
    include_weather: bool = Query(True),
    include_ndvi: bool = Query(True),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get analysis for a specific field"""
    service = AdvisorService()

    result = await service.analyze_field(
        field_id=field_id,
        tenant_id=current_user.tenant_id,
        include_weather=include_weather,
        include_ndvi=include_ndvi,
    )

    return result


@router.get("/health-score/{field_id}")
async def get_health_score(
    field_id: int,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get quick health score for a field"""
    service = AdvisorService()

    result = await service.analyze_field(
        field_id=field_id,
        tenant_id=current_user.tenant_id,
        include_weather=False,
        include_ndvi=True,
    )

    return {
        "field_id": field_id,
        "health_score": result["overall_health_score"],
        "trend": result["context_summary"].get("ndvi_trend", "stable"),
    }
PYEOF

    write_heredoc "$SERVICE_DIR/app/api/__init__.py" << 'PYEOF'
"""API module"""
from .advisor import router as advisor_router
PYEOF

    # ------------------------------------------------------------------------------
    # Main Application
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/main.py" << 'PYEOF'
"""Advisor Service - Main Application"""
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .core.config import settings
from .api import advisor_router


app = FastAPI(
    title="Advisor Service",
    description="Smart Agricultural Recommendations Engine",
    version=settings.SERVICE_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "ml_enabled": settings.USE_ML_MODEL,
        "timestamp": datetime.utcnow().isoformat(),
    }


app.include_router(advisor_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
PYEOF

    # ------------------------------------------------------------------------------
    # Dockerfile & Requirements
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/Dockerfile" << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../shared /app/shared
COPY . .

# Create models directory
RUN mkdir -p /app/models

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
DOCKERFILE

    write_heredoc "$SERVICE_DIR/requirements.txt" << 'REQEOF'
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Auth
python-jose[cryptography]==3.3.0

# HTTP
httpx==0.26.0

# ML
scikit-learn==1.4.0
numpy==1.26.3

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
REQEOF

    log_success "Advisor Service with ML Engine created"
}
