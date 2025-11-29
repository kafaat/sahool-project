
from pydantic import BaseModel
from typing import List, Optional

class FieldHealth(BaseModel):
    ndvi_score: float
    soil_score: float
    weather_score: float
    total_health: float

class FieldStress(BaseModel):
    water_stress: float
    heat_stress: float
    salinity_stress: float
    combined_stress: float

class Insights(BaseModel):
    recommendations: List[str]
