"""
Crop Yield Predictor
Uses ML to predict crop yields based on historical data, weather, soil, and NDVI
"""

import numpy as np
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class CropYieldPredictor:
    """Machine Learning model for crop yield prediction"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = [
            'ndvi_avg', 'ndvi_min', 'ndvi_max', 'ndvi_trend',
            'temp_avg', 'temp_min', 'temp_max',
            'rainfall_total', 'rainfall_days',
            'soil_moisture_avg', 'soil_ph', 'soil_ec',
            'field_area', 'days_since_planting',
            'crop_type_encoded'
        ]
        self.crop_types = {
            'wheat': 0, 'corn': 1, 'rice': 2, 'tomato': 3,
            'potato': 4, 'cucumber': 5, 'pepper': 6, 'lettuce': 7
        }
        self._ready = False

    async def load_model(self):
        """Load pre-trained model or create a new one"""
        try:
            model_path = Path("models_data/crop_yield_model.pkl")
            scaler_path = Path("models_data/crop_yield_scaler.pkl")

            if model_path.exists() and scaler_path.exists():
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info("✅ Loaded pre-trained crop yield model")
            else:
                # Create a simple model for demonstration
                from sklearn.ensemble import RandomForestRegressor
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                from sklearn.preprocessing import StandardScaler
                self.scaler = StandardScaler()
                logger.info("⚠️  Created new crop yield model (needs training)")

            self._ready = True

        except Exception as e:
            logger.error(f"Error loading crop yield model: {e}")
            self._ready = False
            raise

    def is_ready(self) -> bool:
        """Check if model is ready"""
        return self._ready and self.model is not None

    def get_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "name": "Crop Yield Predictor",
            "type": "Random Forest Regressor",
            "features": len(self.feature_names),
            "feature_names": self.feature_names,
            "supported_crops": list(self.crop_types.keys()),
            "ready": self._ready,
            "version": "1.0.0"
        }

    def _prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for prediction"""
        # Extract features in the correct order
        features = [
            data.get('ndvi_avg', 0.5),
            data.get('ndvi_min', 0.3),
            data.get('ndvi_max', 0.7),
            data.get('ndvi_trend', 0.0),
            data.get('temp_avg', 25.0),
            data.get('temp_min', 15.0),
            data.get('temp_max', 35.0),
            data.get('rainfall_total', 100.0),
            data.get('rainfall_days', 10),
            data.get('soil_moisture_avg', 40.0),
            data.get('soil_ph', 6.5),
            data.get('soil_ec', 0.5),
            data.get('field_area', 1.0),
            data.get('days_since_planting', 90),
            self.crop_types.get(data.get('crop_type', 'wheat'), 0)
        ]

        return np.array([features])

    async def predict_yield(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict crop yield based on field data

        Args:
            field_data: Dictionary containing field metrics

        Returns:
            Dictionary with prediction results
        """
        if not self.is_ready():
            raise ValueError("Model not ready for predictions")

        try:
            # Prepare features
            features = self._prepare_features(field_data)

            # Scale features if scaler is available
            if self.scaler is not None:
                try:
                    features = self.scaler.transform(features)
                except:
                    logger.warning("Scaler not fitted, using raw features")

            # Make prediction
            if hasattr(self.model, 'predict'):
                # Model is trained
                prediction = self.model.predict(features)[0]
                confidence = self._calculate_confidence(features)
            else:
                # Model not trained - use heuristic
                prediction = self._heuristic_prediction(field_data)
                confidence = 0.5

            # Get recommendations
            recommendations = self._generate_recommendations(field_data, prediction)

            return {
                "predicted_yield": float(prediction),
                "unit": "tons/hectare",
                "confidence": float(confidence),
                "field_area": field_data.get('field_area', 1.0),
                "total_predicted_yield": float(prediction * field_data.get('field_area', 1.0)),
                "crop_type": field_data.get('crop_type', 'unknown'),
                "recommendations": recommendations,
                "factors": self._analyze_factors(field_data),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in crop yield prediction: {e}", exc_info=True)
            raise

    def _heuristic_prediction(self, data: Dict[str, Any]) -> float:
        """Heuristic-based prediction when model is not trained"""
        base_yield = 5.0  # tons/hectare

        # NDVI factor (0.3 to 0.9 -> 0.6 to 1.4 multiplier)
        ndvi_avg = data.get('ndvi_avg', 0.5)
        ndvi_factor = 0.6 + (ndvi_avg - 0.3) * (0.8 / 0.6)

        # Temperature factor (optimal around 25°C)
        temp_avg = data.get('temp_avg', 25.0)
        temp_factor = 1.0 - abs(temp_avg - 25) * 0.02

        # Rainfall factor (optimal around 500-800mm)
        rainfall = data.get('rainfall_total', 600.0)
        if rainfall < 500:
            rain_factor = rainfall / 500
        elif rainfall > 800:
            rain_factor = 1.0 - (rainfall - 800) / 1000
        else:
            rain_factor = 1.0

        # Soil factors
        soil_moisture = data.get('soil_moisture_avg', 40.0)
        moisture_factor = min(soil_moisture / 40, 1.2)

        # Combined prediction
        prediction = base_yield * ndvi_factor * temp_factor * rain_factor * moisture_factor

        return max(0.5, min(prediction, 15.0))  # Clamp between 0.5 and 15

    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Calculate prediction confidence"""
        # Simple confidence based on feature quality
        confidence = 0.7  # Base confidence

        # If model is RandomForest, use std of tree predictions
        if hasattr(self.model, 'estimators_'):
            try:
                predictions = np.array([tree.predict(features)[0] for tree in self.model.estimators_])
                std = np.std(predictions)
                # Lower std = higher confidence
                confidence = max(0.5, 1.0 - (std / 10))
            except:
                pass

        return confidence

    def _analyze_factors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze factors affecting yield"""
        factors = {}

        # NDVI analysis
        ndvi_avg = data.get('ndvi_avg', 0.5)
        if ndvi_avg >= 0.6:
            factors['ndvi'] = {"status": "excellent", "impact": "positive", "value": ndvi_avg}
        elif ndvi_avg >= 0.4:
            factors['ndvi'] = {"status": "good", "impact": "neutral", "value": ndvi_avg}
        else:
            factors['ndvi'] = {"status": "poor", "impact": "negative", "value": ndvi_avg}

        # Temperature analysis
        temp_avg = data.get('temp_avg', 25.0)
        if 20 <= temp_avg <= 30:
            factors['temperature'] = {"status": "optimal", "impact": "positive", "value": temp_avg}
        elif 15 <= temp_avg <= 35:
            factors['temperature'] = {"status": "acceptable", "impact": "neutral", "value": temp_avg}
        else:
            factors['temperature'] = {"status": "extreme", "impact": "negative", "value": temp_avg}

        # Rainfall analysis
        rainfall = data.get('rainfall_total', 600.0)
        if 500 <= rainfall <= 800:
            factors['rainfall'] = {"status": "optimal", "impact": "positive", "value": rainfall}
        elif 300 <= rainfall <= 1000:
            factors['rainfall'] = {"status": "acceptable", "impact": "neutral", "value": rainfall}
        else:
            factors['rainfall'] = {"status": "extreme", "impact": "negative", "value": rainfall}

        # Soil moisture
        moisture = data.get('soil_moisture_avg', 40.0)
        if 35 <= moisture <= 55:
            factors['soil_moisture'] = {"status": "optimal", "impact": "positive", "value": moisture}
        elif 25 <= moisture <= 65:
            factors['soil_moisture'] = {"status": "acceptable", "impact": "neutral", "value": moisture}
        else:
            factors['soil_moisture'] = {"status": "extreme", "impact": "negative", "value": moisture}

        return factors

    def _generate_recommendations(self, data: Dict[str, Any], predicted_yield: float) -> List[str]:
        """Generate recommendations based on prediction"""
        recommendations = []

        # NDVI-based recommendations
        ndvi_avg = data.get('ndvi_avg', 0.5)
        if ndvi_avg < 0.4:
            recommendations.append("Low NDVI detected. Consider fertilization or irrigation.")
        elif ndvi_avg < 0.5:
            recommendations.append("NDVI could be improved with proper nutrient management.")

        # Temperature recommendations
        temp_avg = data.get('temp_avg', 25.0)
        if temp_avg > 32:
            recommendations.append("High temperatures may stress crops. Ensure adequate irrigation.")
        elif temp_avg < 18:
            recommendations.append("Low temperatures may slow growth. Consider protective measures.")

        # Rainfall recommendations
        rainfall = data.get('rainfall_total', 600.0)
        if rainfall < 400:
            recommendations.append("Low rainfall expected. Plan for supplemental irrigation.")
        elif rainfall > 900:
            recommendations.append("High rainfall expected. Ensure proper drainage.")

        # Soil recommendations
        moisture = data.get('soil_moisture_avg', 40.0)
        if moisture < 30:
            recommendations.append("Soil moisture is low. Increase irrigation frequency.")
        elif moisture > 60:
            recommendations.append("Soil moisture is high. Reduce irrigation to prevent waterlogging.")

        # Yield-based recommendations
        if predicted_yield < 3.0:
            recommendations.append("Low yield predicted. Consider crop rotation or soil amendment.")
        elif predicted_yield > 10.0:
            recommendations.append("Excellent yield predicted. Maintain current practices.")

        return recommendations if recommendations else ["Conditions are optimal. Continue current management practices."]

    async def batch_predict(self, fields_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch prediction for multiple fields"""
        results = []

        for field_data in fields_data:
            try:
                prediction = await self.predict_yield(field_data)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Error in batch prediction for field: {e}")
                results.append({"error": str(e)})

        return results
