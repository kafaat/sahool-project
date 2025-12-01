"""
Knowledge Retrieval Module
Handles knowledge base queries and context formatting
"""

import logging
from typing import Dict, Any, List, Optional

from app.services.knowledge_base import get_knowledge_base

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Retrieves relevant knowledge from vector store and formats context"""

    def __init__(self):
        """Initialize knowledge retriever"""
        self.knowledge_base = get_knowledge_base()
        logger.info("Knowledge Retriever initialized")

    def get_relevant_context(
        self,
        query: str,
        field_data: Optional[Dict[str, Any]] = None,
        max_results: int = 5
    ) -> str:
        """
        Retrieve relevant knowledge from vector store

        Args:
            query: User query or analysis request
            field_data: Field context for enhanced retrieval
            max_results: Maximum number of results to retrieve

        Returns:
            Formatted context string
        """
        try:
            context = self.knowledge_base.get_relevant_context(
                query,
                field_data or {},
                max_results=max_results
            )
            return context if context else "لا توجد معلومات ذات صلة في قاعدة المعرفة"

        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            return "حدث خطأ في استرجاع المعلومات"

    def format_field_data(self, field_data: Dict[str, Any]) -> str:
        """
        Format field data for LLM consumption

        Args:
            field_data: Field context (soil, weather, ndvi, alerts)

        Returns:
            Formatted field data string
        """
        parts = []

        # Soil data
        soil = field_data.get("soil_summary", {})
        if soil:
            parts.append("**بيانات التربة:**")
            if soil.get("ph_avg"):
                parts.append(f"- pH: {soil['ph_avg']:.1f}")
            if soil.get("ec_avg"):
                parts.append(f"- EC: {soil['ec_avg']:.1f} dS/m")
            if soil.get("moisture_avg"):
                parts.append(f"- الرطوبة: {soil['moisture_avg']:.1f}%")
            parts.append("")

        # Weather data
        weather = field_data.get("weather_forecast", {})
        if weather and weather.get("points"):
            parts.append("**توقعات الطقس (72 ساعة):**")
            points = weather["points"][:3]  # First 3 points
            for p in points:
                parts.append(
                    f"- درجة الحرارة: {p.get('temp_c', 'N/A')}°م، "
                    f"أمطار: {p.get('rain_mm', 0):.1f}مم"
                )
            parts.append("")

        # NDVI data
        ndvi = field_data.get("imagery_latest", {})
        if ndvi:
            parts.append("**بيانات NDVI:**")
            if ndvi.get("ndvi_avg"):
                parts.append(f"- متوسط NDVI: {ndvi['ndvi_avg']:.2f}")
            parts.append("")

        # Alerts
        alerts = field_data.get("alerts", [])
        if alerts:
            parts.append(f"**التنبيهات الأخيرة ({len(alerts)}):**")
            for alert in alerts[:3]:  # First 3 alerts
                parts.append(f"- {alert.get('message', 'تنبيه')}")
            parts.append("")

        return "\n".join(parts) if parts else "لا توجد بيانات متوفرة"

    def extract_soil_metrics(self, field_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract soil metrics from field data"""
        soil = field_data.get("soil_summary", {})
        return {
            "ph": soil.get("ph_avg"),
            "ec": soil.get("ec_avg"),
            "moisture": soil.get("moisture_avg"),
        }

    def extract_weather_metrics(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weather metrics from field data"""
        weather = field_data.get("weather_forecast", {})
        points = weather.get("points", [])

        if not points:
            return {}

        return {
            "max_temp": max((p.get("temp_c") or 0) for p in points),
            "min_temp": min((p.get("temp_c") or 99) for p in points),
            "total_rain": sum((p.get("rain_mm") or 0) for p in points),
            "avg_humidity": sum((p.get("humidity") or 0) for p in points) / len(points)
            if all(p.get("humidity") for p in points)
            else None,
        }

    def extract_ndvi_metrics(self, field_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract NDVI metrics from field data"""
        ndvi = field_data.get("imagery_latest", {})
        return {
            "ndvi_avg": ndvi.get("ndvi_avg"),
            "ndvi_min": ndvi.get("ndvi_min"),
            "ndvi_max": ndvi.get("ndvi_max"),
        }

    def build_retrieval_context(
        self,
        query: str,
        field_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build complete retrieval context

        Args:
            query: User query
            field_data: Field data

        Returns:
            Complete context with knowledge and formatted data
        """
        return {
            "knowledge_context": self.get_relevant_context(query, field_data),
            "field_summary": self.format_field_data(field_data),
            "soil_metrics": self.extract_soil_metrics(field_data),
            "weather_metrics": self.extract_weather_metrics(field_data),
            "ndvi_metrics": self.extract_ndvi_metrics(field_data),
        }


# Global retriever instance
_retriever_instance: Optional[KnowledgeRetriever] = None


def get_retriever() -> KnowledgeRetriever:
    """Get or create retriever instance"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = KnowledgeRetriever()
    return _retriever_instance
