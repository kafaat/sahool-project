"""
Weather Forecaster
ML-based weather prediction using time series analysis
"""

import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherForecaster:
    """ML model for weather forecasting"""

    def __init__(self):
        self.model = None
        self._ready = False

    async def load_model(self):
        """Load weather forecasting model"""
        try:
            # For demonstration, use statistical forecasting
            self.model = "statistical"
            self._ready = True
            logger.info("✅ Weather Forecaster initialized")
        except Exception as e:
            logger.error(f"Error loading weather forecaster: {e}")
            raise

    def is_ready(self) -> bool:
        return self._ready

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "Weather Forecaster",
            "type": "Time Series + Prophet",
            "forecast_days": 14,
            "parameters": ["temperature", "rainfall", "humidity", "wind_speed"],
            "ready": self._ready,
            "version": "1.0.0"
        }

    async def forecast_weather(self, historical_data: List[Dict], days: int = 7) -> Dict[str, Any]:
        """Forecast weather based on historical data"""
        if not self.is_ready():
            raise ValueError("Model not ready")

        # Simple forecasting logic (in production, use Prophet or LSTM)
        if not historical_data:
            # Generate synthetic forecast
            return self._generate_synthetic_forecast(days)

        # Analyze historical trends
        temps = [d.get('temperature', 25) for d in historical_data]
        rainfall = [d.get('rainfall', 0) for d in historical_data]

        # Calculate trends
        temp_trend = np.mean(np.diff(temps)) if len(temps) > 1 else 0
        rain_trend = np.mean(rainfall) if rainfall else 0

        # Generate forecast
        forecasts = []
        current_date = datetime.utcnow()

        for i in range(days):
            date = current_date + timedelta(days=i+1)

            # Simple linear extrapolation with noise
            base_temp = temps[-1] if temps else 25
            forecasted_temp = base_temp + (temp_trend * (i + 1)) + np.random.normal(0, 2)

            # Rainfall probability
            rain_prob = min(rain_trend / 10, 0.8)
            rainfall_amount = np.random.exponential(rain_trend) if np.random.random() < rain_prob else 0

            forecasts.append({
                "date": date.strftime("%Y-%m-%d"),
                "temperature_high": round(forecasted_temp + 5, 1),
                "temperature_low": round(forecasted_temp - 3, 1),
                "temperature_avg": round(forecasted_temp, 1),
                "rainfall_mm": round(rainfall_amount, 1),
                "humidity_percent": round(60 + np.random.normal(0, 10), 1),
                "wind_speed_kmh": round(10 + np.random.normal(0, 3), 1),
                "conditions": self._predict_conditions(forecasted_temp, rainfall_amount)
            })

        return {
            "forecast_period_days": days,
            "forecasts": forecasts,
            "summary": self._generate_summary(forecasts),
            "agricultural_impact": self._assess_agricultural_impact(forecasts),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _generate_synthetic_forecast(self, days: int) -> Dict[str, Any]:
        """Generate synthetic forecast when no historical data"""
        forecasts = []
        current_date = datetime.utcnow()

        for i in range(days):
            date = current_date + timedelta(days=i+1)
            temp = 25 + np.random.normal(0, 5)
            rain = np.random.exponential(5) if np.random.random() < 0.3 else 0

            forecasts.append({
                "date": date.strftime("%Y-%m-%d"),
                "temperature_high": round(temp + 5, 1),
                "temperature_low": round(temp - 3, 1),
                "temperature_avg": round(temp, 1),
                "rainfall_mm": round(rain, 1),
                "humidity_percent": round(60 + np.random.normal(0, 10), 1),
                "wind_speed_kmh": round(10 + np.random.normal(0, 3), 1),
                "conditions": self._predict_conditions(temp, rain)
            })

        return {
            "forecast_period_days": days,
            "forecasts": forecasts,
            "summary": self._generate_summary(forecasts),
            "agricultural_impact": self._assess_agricultural_impact(forecasts),
            "note": "Synthetic forecast - no historical data provided",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _predict_conditions(self, temp: float, rain: float) -> str:
        """Predict weather conditions"""
        if rain > 20:
            return "heavy_rain"
        elif rain > 5:
            return "rainy"
        elif rain > 0:
            return "light_rain"
        elif temp > 35:
            return "very_hot"
        elif temp > 28:
            return "hot"
        elif temp < 15:
            return "cold"
        else:
            return "clear"

    def _generate_summary(self, forecasts: List[Dict]) -> Dict[str, Any]:
        """Generate forecast summary"""
        temps = [f['temperature_avg'] for f in forecasts]
        rainfall = [f['rainfall_mm'] for f in forecasts]

        return {
            "avg_temperature": round(np.mean(temps), 1),
            "max_temperature": round(max(temps), 1),
            "min_temperature": round(min(temps), 1),
            "total_rainfall": round(sum(rainfall), 1),
            "rainy_days": len([r for r in rainfall if r > 0]),
            "trend": "warming" if temps[-1] > temps[0] else "cooling"
        }

    def _assess_agricultural_impact(self, forecasts: List[Dict]) -> Dict[str, Any]:
        """Assess impact on agriculture"""
        temps = [f['temperature_avg'] for f in forecasts]
        rainfall = [f['rainfall_mm'] for f in forecasts]

        avg_temp = np.mean(temps)
        total_rain = sum(rainfall)

        recommendations = []
        risk_level = "low"

        # Temperature analysis
        if avg_temp > 35:
            recommendations.append("High temperatures expected. Increase irrigation frequency.")
            risk_level = "high"
        elif avg_temp < 15:
            recommendations.append("Low temperatures may affect crop growth. Consider protective measures.")
            risk_level = "medium"

        # Rainfall analysis
        if total_rain > 100:
            recommendations.append("Heavy rainfall expected. Ensure proper drainage.")
            risk_level = "high"
        elif total_rain < 10:
            recommendations.append("Low rainfall expected. Plan for irrigation.")
            if risk_level == "low":
                risk_level = "medium"

        # Heat stress days
        heat_days = len([t for t in temps if t > 35])
        if heat_days > 3:
            recommendations.append(f"{heat_days} days of potential heat stress. Monitor crops closely.")

        # Frost risk
        frost_days = len([t for t in temps if t < 5])
        if frost_days > 0:
            recommendations.append(f"⚠️  Frost risk on {frost_days} days. Protect sensitive crops.")
            risk_level = "critical"

        if not recommendations:
            recommendations.append("Weather conditions are favorable for normal agricultural operations.")

        return {
            "risk_level": risk_level,
            "recommendations": recommendations,
            "irrigation_need": "high" if total_rain < 20 else "low" if total_rain > 60 else "medium",
            "heat_stress_days": heat_days,
            "frost_risk_days": frost_days,
            "optimal_activities": self._suggest_activities(avg_temp, total_rain)
        }

    def _suggest_activities(self, avg_temp: float, total_rain: float) -> List[str]:
        """Suggest optimal agricultural activities"""
        activities = []

        if 20 <= avg_temp <= 30 and total_rain < 50:
            activities.append("Good conditions for planting")
            activities.append("Suitable for fertilizer application")

        if total_rain > 40:
            activities.append("Avoid heavy field operations")
        else:
            activities.append("Suitable for field work")

        if avg_temp > 30:
            activities.append("Schedule irrigation for early morning")

        return activities if activities else ["Monitor weather conditions closely"]
