"""
Soil Analyzer
ML model for analyzing soil quality and providing recommendations
"""

import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SoilAnalyzer:
    """ML model for soil quality analysis"""

    def __init__(self):
        self.model = None
        self._ready = False

    async def load_model(self):
        """Load soil analysis model"""
        try:
            # For demonstration, use rule-based system
            self.model = "rule_based"
            self._ready = True
            logger.info("✅ Soil Analyzer initialized")
        except Exception as e:
            logger.error(f"Error loading soil analyzer: {e}")
            raise

    def is_ready(self) -> bool:
        return self._ready

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "Soil Analyzer",
            "type": "Rule-based + ML Hybrid",
            "parameters": ["pH", "EC", "N", "P", "K", "moisture", "organic_matter"],
            "ready": self._ready,
            "version": "1.0.0"
        }

    async def analyze_soil(self, soil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze soil quality"""
        if not self.is_ready():
            raise ValueError("Model not ready")

        ph = soil_data.get('ph', 6.5)
        ec = soil_data.get('ec', 0.5)
        nitrogen = soil_data.get('nitrogen', 50)
        phosphorus = soil_data.get('phosphorus', 30)
        potassium = soil_data.get('potassium', 150)
        moisture = soil_data.get('moisture', 40)
        organic_matter = soil_data.get('organic_matter', 3.0)

        # Calculate quality score
        scores = {
            'ph': self._score_ph(ph),
            'ec': self._score_ec(ec),
            'nutrients': self._score_nutrients(nitrogen, phosphorus, potassium),
            'moisture': self._score_moisture(moisture),
            'organic_matter': self._score_organic_matter(organic_matter)
        }

        overall_score = np.mean(list(scores.values()))

        # Generate recommendations
        recommendations = self._generate_soil_recommendations(ph, ec, nitrogen, phosphorus, potassium, moisture, organic_matter)

        return {
            "overall_quality": self._quality_category(overall_score),
            "overall_score": float(overall_score),
            "component_scores": scores,
            "measurements": {
                "ph": ph,
                "ec": ec,
                "nitrogen_ppm": nitrogen,
                "phosphorus_ppm": phosphorus,
                "potassium_ppm": potassium,
                "moisture_percent": moisture,
                "organic_matter_percent": organic_matter
            },
            "recommendations": recommendations,
            "crop_suitability": self._assess_crop_suitability(soil_data),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _score_ph(self, ph: float) -> float:
        """Score pH (optimal 6.0-7.0)"""
        if 6.0 <= ph <= 7.0:
            return 100.0
        elif 5.5 <= ph <= 7.5:
            return 80.0
        elif 5.0 <= ph <= 8.0:
            return 60.0
        return 40.0

    def _score_ec(self, ec: float) -> float:
        """Score electrical conductivity"""
        if 0.3 <= ec <= 0.8:
            return 100.0
        elif 0.2 <= ec <= 1.5:
            return 80.0
        return 50.0

    def _score_nutrients(self, n: float, p: float, k: float) -> float:
        """Score nutrient levels"""
        n_score = 100 if n >= 40 else (n / 40) * 100
        p_score = 100 if p >= 25 else (p / 25) * 100
        k_score = 100 if k >= 120 else (k / 120) * 100
        return np.mean([n_score, p_score, k_score])

    def _score_moisture(self, moisture: float) -> float:
        """Score moisture level"""
        if 35 <= moisture <= 55:
            return 100.0
        elif 25 <= moisture <= 65:
            return 80.0
        return 50.0

    def _score_organic_matter(self, om: float) -> float:
        """Score organic matter"""
        if om >= 3.0:
            return 100.0
        elif om >= 2.0:
            return 80.0
        return (om / 2.0) * 60.0

    def _quality_category(self, score: float) -> str:
        """Categorize overall quality"""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "fair"
        return "poor"

    def _generate_soil_recommendations(self, ph, ec, n, p, k, moisture, om) -> List[str]:
        """Generate soil improvement recommendations"""
        recs = []

        if ph < 6.0:
            recs.append(f"Soil is acidic (pH {ph:.1f}). Apply lime to raise pH.")
        elif ph > 7.5:
            recs.append(f"Soil is alkaline (pH {ph:.1f}). Apply sulfur to lower pH.")

        if n < 40:
            recs.append(f"Low nitrogen ({n} ppm). Apply nitrogen fertilizer or compost.")
        if p < 25:
            recs.append(f"Low phosphorus ({p} ppm). Apply phosphate fertilizer.")
        if k < 120:
            recs.append(f"Low potassium ({k} ppm). Apply potash fertilizer.")

        if moisture < 30:
            recs.append("Soil moisture is low. Increase irrigation.")
        elif moisture > 60:
            recs.append("Soil moisture is high. Improve drainage.")

        if om < 2.0:
            recs.append(f"Low organic matter ({om:.1f}%). Add compost or organic amendments.")

        if not recs:
            recs.append("Soil conditions are optimal. Maintain current practices.")

        return recs

    def _assess_crop_suitability(self, soil_data: Dict) -> Dict[str, Any]:
        """Assess soil suitability for different crops"""
        ph = soil_data.get('ph', 6.5)

        crops = {
            'wheat': {'min_ph': 6.0, 'max_ph': 7.5},
            'corn': {'min_ph': 5.8, 'max_ph': 7.0},
            'rice': {'min_ph': 5.5, 'max_ph': 6.5},
            'tomato': {'min_ph': 6.0, 'max_ph': 6.8},
            'potato': {'min_ph': 5.0, 'max_ph': 6.0},
        }

        suitability = {}
        for crop, ph_range in crops.items():
            if ph_range['min_ph'] <= ph <= ph_range['max_ph']:
                suitability[crop] = "highly_suitable"
            elif ph_range['min_ph'] - 0.5 <= ph <= ph_range['max_ph'] + 0.5:
                suitability[crop] = "suitable"
            else:
                suitability[crop] = "not_suitable"

        return suitability
