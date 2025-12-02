"""
Context Aggregator Service
Collects and aggregates field context from multiple data sources:
- NDVI Database
- Weather API
- Crop Database
- Soil / History
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..core.config import settings
from ..core.logging import logger
from ..schemas.advisor import (
    FieldContext,
    NDVIContext,
    WeatherContext,
    CropContext,
    SoilContext,
    NDVITrend,
)


class ContextAggregator:
    """
    Aggregates field context from multiple sources
    """

    def __init__(self):
        self.ndvi_service_url = settings.ndvi_service_url
        self.weather_api_url = settings.weather_api_url
        self.timeout = 30.0

    async def aggregate_context(
        self,
        field_id: UUID,
        include_weather: bool = True,
        include_forecast: bool = True,
        location: Optional[Dict[str, float]] = None,
    ) -> FieldContext:
        """
        Aggregate all context data for a field

        Args:
            field_id: UUID of the field
            include_weather: Whether to fetch weather data
            include_forecast: Whether to include weather forecast
            location: Optional location override {"lat": ..., "lng": ...}

        Returns:
            FieldContext with all aggregated data
        """
        logger.info(f"Aggregating context for field {field_id}")

        # Initialize context
        context = FieldContext(field_id=field_id)

        # Fetch NDVI data
        try:
            ndvi_data = await self._fetch_ndvi_data(field_id)
            if ndvi_data:
                context.ndvi = ndvi_data
        except Exception as e:
            logger.error(f"Failed to fetch NDVI data: {e}")

        # Fetch weather data
        if include_weather and location:
            try:
                weather_data = await self._fetch_weather_data(
                    location["lat"],
                    location["lng"],
                    include_forecast=include_forecast,
                )
                if weather_data:
                    context.weather = weather_data
            except Exception as e:
                logger.error(f"Failed to fetch weather data: {e}")

        # Fetch crop data (from local DB or service)
        try:
            crop_data = await self._fetch_crop_data(field_id)
            if crop_data:
                context.crop = crop_data
        except Exception as e:
            logger.error(f"Failed to fetch crop data: {e}")

        # Fetch soil data
        try:
            soil_data = await self._fetch_soil_data(field_id)
            if soil_data:
                context.soil = soil_data
        except Exception as e:
            logger.error(f"Failed to fetch soil data: {e}")

        # Fetch historical issues
        try:
            history = await self._fetch_field_history(field_id)
            context.previous_issues = history.get("issues", [])
            context.previous_recommendations = history.get("recommendations", [])
        except Exception as e:
            logger.error(f"Failed to fetch field history: {e}")

        logger.info(f"Context aggregation complete for field {field_id}")
        return context

    async def _fetch_ndvi_data(self, field_id: UUID) -> Optional[NDVIContext]:
        """Fetch NDVI data from NDVI service or database"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try to get latest NDVI analysis
                response = await client.get(
                    f"{self.ndvi_service_url}/api/fields/{field_id}/ndvi"
                )

                if response.status_code == 200:
                    data = response.json()

                    # Calculate trend from history
                    trend = self._calculate_ndvi_trend(data.get("history", []))

                    return NDVIContext(
                        mean=data.get("mean_ndvi", 0.5),
                        min=data.get("min_ndvi", 0.0),
                        max=data.get("max_ndvi", 1.0),
                        std_dev=data.get("std_dev"),
                        acquisition_date=data.get("acquisition_date"),
                        trend=trend,
                        zones=data.get("zones", []),
                        history=data.get("history", []),
                    )

                elif response.status_code == 404:
                    logger.warning(f"No NDVI data found for field {field_id}")
                    return None

        except httpx.RequestError as e:
            logger.warning(f"NDVI service unavailable: {e}")

        # Return mock data for development
        return NDVIContext(
            mean=0.55,
            min=0.2,
            max=0.8,
            std_dev=0.15,
            trend=NDVITrend.STABLE,
            zones=[
                {"zone": "low", "percentage": 15, "mean_ndvi": 0.25},
                {"zone": "medium", "percentage": 35, "mean_ndvi": 0.45},
                {"zone": "high", "percentage": 50, "mean_ndvi": 0.72},
            ],
        )

    async def _fetch_weather_data(
        self,
        lat: float,
        lng: float,
        include_forecast: bool = True,
    ) -> Optional[WeatherContext]:
        """Fetch weather data from Open-Meteo API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build API URL
                params = {
                    "latitude": lat,
                    "longitude": lng,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
                    "past_days": 7,
                    "forecast_days": 7 if include_forecast else 0,
                    "timezone": "auto",
                }

                response = await client.get(
                    f"{self.weather_api_url}/forecast",
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    current = data.get("current", {})
                    daily = data.get("daily", {})

                    # Calculate 7-day precipitation
                    precip_7d = sum(daily.get("precipitation_sum", [])[:7])

                    # Build forecast list
                    forecast = []
                    if include_forecast and "time" in daily:
                        for i, date in enumerate(daily["time"]):
                            forecast.append({
                                "date": date,
                                "temp_max": daily.get("temperature_2m_max", [None])[i],
                                "temp_min": daily.get("temperature_2m_min", [None])[i],
                                "precipitation": daily.get("precipitation_sum", [None])[i],
                                "et0": daily.get("et0_fao_evapotranspiration", [None])[i],
                            })

                    return WeatherContext(
                        temperature_current=current.get("temperature_2m"),
                        humidity=current.get("relative_humidity_2m"),
                        precipitation=current.get("precipitation"),
                        precipitation_7d=precip_7d,
                        wind_speed=current.get("wind_speed_10m"),
                        evapotranspiration=daily.get("et0_fao_evapotranspiration", [None])[0],
                        forecast=forecast,
                    )

        except httpx.RequestError as e:
            logger.warning(f"Weather API unavailable: {e}")

        # Return mock data for development
        return WeatherContext(
            temperature_current=28.5,
            temperature_min=22.0,
            temperature_max=35.0,
            humidity=45.0,
            precipitation=0.0,
            precipitation_7d=5.2,
            wind_speed=12.5,
            evapotranspiration=6.2,
            forecast=[
                {"date": "2025-12-03", "temp_max": 34, "temp_min": 21, "precipitation": 0},
                {"date": "2025-12-04", "temp_max": 33, "temp_min": 20, "precipitation": 2},
                {"date": "2025-12-05", "temp_max": 31, "temp_min": 19, "precipitation": 5},
            ],
        )

    async def _fetch_crop_data(self, field_id: UUID) -> Optional[CropContext]:
        """Fetch crop information from database"""
        # TODO: Implement actual database query
        # For now, return mock data
        return CropContext(
            crop_type="wheat",
            growth_stage="vegetative",
            planting_date=datetime.now() - timedelta(days=45),
            expected_harvest=datetime.now() + timedelta(days=75),
            variety="Hard Red Winter",
            irrigation_type="sprinkler",
        )

    async def _fetch_soil_data(self, field_id: UUID) -> Optional[SoilContext]:
        """Fetch soil information from database"""
        # TODO: Implement actual database query
        # For now, return mock data
        return SoilContext(
            soil_type="loam",
            ph=6.8,
            organic_matter=3.2,
            nitrogen=45,
            phosphorus=28,
            potassium=180,
            moisture=35,
            last_test_date=datetime.now() - timedelta(days=90),
        )

    async def _fetch_field_history(self, field_id: UUID) -> Dict[str, List[str]]:
        """Fetch field history from database"""
        # TODO: Implement actual database query
        return {
            "issues": ["water_stress_2024_07", "pest_aphids_2024_05"],
            "recommendations": ["irrigation_increase", "pesticide_application"],
        }

    def _calculate_ndvi_trend(self, history: List[Dict[str, Any]]) -> Optional[NDVITrend]:
        """Calculate NDVI trend from historical data"""
        if not history or len(history) < 2:
            return None

        # Get last 3 measurements
        recent = sorted(history, key=lambda x: x.get("date", ""), reverse=True)[:3]

        if len(recent) < 2:
            return NDVITrend.STABLE

        # Calculate average change
        changes = []
        for i in range(len(recent) - 1):
            curr = recent[i].get("mean_ndvi", 0)
            prev = recent[i + 1].get("mean_ndvi", 0)
            changes.append(curr - prev)

        avg_change = sum(changes) / len(changes)

        if avg_change > 0.05:
            return NDVITrend.IMPROVING
        elif avg_change < -0.05:
            return NDVITrend.DECLINING
        else:
            return NDVITrend.STABLE
