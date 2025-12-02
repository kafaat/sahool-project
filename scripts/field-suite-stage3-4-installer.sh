#!/bin/bash
set -e

# ===========================================
# Field Suite – Stage 3 + Stage 4 Installer
# Advisor Intelligence + Monitoring Stack
# Version: 1.0.0
# ===========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

PROJECT_NAME="field_suite_full_project"
BACKEND_DIR="$PROJECT_NAME/backend"

echo_header() {
  echo -e "\n${MAGENTA}════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${MAGENTA}════════════════════════════════════════════════════${NC}\n"
}

write_file() {
  local file_path=$1
  local content=$2
  mkdir -p "$(dirname "$file_path")"
  echo "$content" > "$file_path"
  echo -e "${CYAN}📄 تم إنشاء: ${file_path}${NC}"
}

echo_success() {
  echo -e "${GREEN}✅${NC} $1"
}

echo_info() {
  echo -e "${CYAN}ℹ️${NC} $1"
}

# ===========================================
# 3️⃣ المرحلة الثالثة — Advisor Intelligence
# ===========================================
echo_header "3️⃣ بناء طبقة المستشار الزراعي Advisor Intelligence"

mkdir -p "$BACKEND_DIR/app/advisor/rules"
mkdir -p "$BACKEND_DIR/app/advisor/engine"
mkdir -p "$BACKEND_DIR/app/advisor/pipelines"
mkdir -p "$BACKEND_DIR/app/advisor/services"

# Create __init__.py files
touch "$BACKEND_DIR/app/advisor/__init__.py"
touch "$BACKEND_DIR/app/advisor/rules/__init__.py"
touch "$BACKEND_DIR/app/advisor/engine/__init__.py"
touch "$BACKEND_DIR/app/advisor/pipelines/__init__.py"
touch "$BACKEND_DIR/app/advisor/services/__init__.py"

# ------------------------------
# 3.1: Advisor Context Builder
# ------------------------------
write_file "$BACKEND_DIR/app/advisor/pipelines/context_builder.py" 'from datetime import datetime
from typing import Dict, Any, Optional
from app.services.ndvi_service import NDVIService
from app.utils.weather_client import WeatherClient


class FieldContextBuilder:
    """
    Builds comprehensive context for field analysis.
    Aggregates NDVI data, weather info, and field metadata.
    """

    def __init__(self, ndvi_service: NDVIService, weather: WeatherClient):
        self.ndvi = ndvi_service
        self.weather = weather

    def build(self, tenant_id: int, field) -> Dict[str, Any]:
        """Build analysis context for a field."""
        ndvi_data = self.ndvi.get_latest(tenant_id, field.id)
        weather_today = self.weather.get_current_weather(field.geometry)

        return {
            "field_id": field.id,
            "tenant_id": tenant_id,
            "crop_type": field.crop_type,
            "geometry": field.geometry,
            "area_ha": getattr(field, "area_ha", None),
            "soil_type": getattr(field, "soil_type", None),
            "irrigation_type": getattr(field, "irrigation_type", None),
            "ndvi": ndvi_data,
            "weather": weather_today,
            "timestamp": datetime.utcnow().isoformat()
        }
'

# ------------------------------
# 3.2 Weather Client
# ------------------------------
write_file "$BACKEND_DIR/app/utils/weather_client.py" 'import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WeatherClient:
    """
    Client for OpenWeatherMap API.
    Provides current weather data for field locations.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.timeout = 10

    def get_current_weather(self, geometry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a geometry (polygon).
        Uses the first coordinate of the polygon as the location.
        """
        try:
            # Extract coordinates from geometry
            if isinstance(geometry, dict) and "coordinates" in geometry:
                coords = geometry["coordinates"]
                if coords and coords[0] and coords[0][0]:
                    lon, lat = coords[0][0]
                else:
                    logger.warning("Invalid geometry coordinates")
                    return self._default_weather()
            else:
                logger.warning("Invalid geometry format")
                return self._default_weather()

            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }

            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            return {
                "t": data["main"]["temp"],
                "tmin": data["main"]["temp_min"],
                "tmax": data["main"]["temp_max"],
                "humidity": data["main"]["humidity"],
                "wind": data["wind"]["speed"],
                "description": data["weather"][0]["description"] if data.get("weather") else "",
                "pressure": data["main"].get("pressure"),
                "clouds": data.get("clouds", {}).get("all", 0)
            }

        except requests.RequestException as e:
            logger.error(f"Weather API request failed: {e}")
            return self._default_weather()
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Weather data parsing error: {e}")
            return self._default_weather()

    def _default_weather(self) -> Dict[str, Any]:
        """Return default weather data when API fails."""
        return {
            "t": 25.0,
            "tmin": 20.0,
            "tmax": 30.0,
            "humidity": 50,
            "wind": 5.0,
            "description": "unknown",
            "pressure": 1013,
            "clouds": 0
        }
'

# ------------------------------
# 3.3 Rule Engine
# ------------------------------
write_file "$BACKEND_DIR/app/advisor/engine/rule_engine.py" 'from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Rule engine for evaluating field conditions.
    Processes rules against field context and generates recommendations.
    """

    def __init__(self, rules: List):
        self.rules = rules

    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all rules against the given context.
        Returns a list of recommendations from matching rules.
        """
        recommendations = []

        for rule in self.rules:
            try:
                if rule.matches(context):
                    recommendation = rule.render(context)
                    if recommendation:
                        recommendations.append(recommendation)
                        logger.info(f"Rule {rule.__class__.__name__} matched for field {context.get('"'"'field_id'"'"')}")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")
                continue

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))

        return recommendations

    def add_rule(self, rule) -> None:
        """Add a new rule to the engine."""
        self.rules.append(rule)

    def remove_rule(self, rule_class) -> bool:
        """Remove a rule by its class type."""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if not isinstance(r, rule_class)]
        return len(self.rules) < original_count
'

# ------------------------------
# 3.4 Base Rule Class
# ------------------------------
write_file "$BACKEND_DIR/app/advisor/rules/base_rule.py" 'from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseRule(ABC):
    """Abstract base class for advisor rules."""

    @abstractmethod
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if this rule applies to the given context."""
        pass

    @abstractmethod
    def render(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate recommendation for this rule."""
        pass

    @property
    def name(self) -> str:
        """Return the rule name."""
        return self.__class__.__name__
'

# ------------------------------
# 3.5 Irrigation Rule
# ------------------------------
write_file "$BACKEND_DIR/app/advisor/rules/irrigation_rule.py" 'from typing import Dict, Any, Optional
from .base_rule import BaseRule


class IrrigationRule(BaseRule):
    """
    Rule for detecting irrigation needs based on NDVI values.
    Low NDVI indicates water stress in crops.
    """

    NDVI_THRESHOLD = 0.35
    CRITICAL_NDVI_THRESHOLD = 0.25

    def matches(self, ctx: Dict[str, Any]) -> bool:
        """Check if field needs irrigation based on NDVI."""
        ndvi = ctx.get("ndvi")
        if not ndvi or "mean_ndvi" not in ndvi:
            return False
        return ndvi["mean_ndvi"] < self.NDVI_THRESHOLD

    def render(self, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate irrigation recommendation."""
        ndvi_value = ctx["ndvi"]["mean_ndvi"]
        is_critical = ndvi_value < self.CRITICAL_NDVI_THRESHOLD

        return {
            "rule": "irrigation_low_ndvi",
            "priority": "critical" if is_critical else "high",
            "category": "irrigation",
            "title_ar": "الحقل يحتاج إلى ري عاجل" if is_critical else "الحقل يحتاج إلى ري",
            "title_en": "Field requires urgent irrigation" if is_critical else "Field requires irrigation",
            "description_ar": f"قيمة NDVI منخفضة ({ndvi_value:.2f}) تدل على إجهاد مائي في النبات.",
            "description_en": f"Low NDVI value ({ndvi_value:.2f}) indicates water stress in crops.",
            "actions": [
                {
                    "action_ar": "زيادة كمية الري بنسبة 30%" if is_critical else "زيادة كمية الري بنسبة 20%",
                    "action_en": "Increase irrigation by 30%" if is_critical else "Increase irrigation by 20%",
                    "urgency": "immediate" if is_critical else "within_24h"
                },
                {
                    "action_ar": "فحص نظام الري للتأكد من عدم وجود تسريبات",
                    "action_en": "Check irrigation system for leaks",
                    "urgency": "within_48h"
                }
            ],
            "confidence_score": 0.85,
            "field_id": ctx["field_id"],
            "metadata": {
                "current_ndvi": ndvi_value,
                "threshold": self.NDVI_THRESHOLD
            },
            "timestamp": ctx["timestamp"]
        }
'

# ------------------------------
# 3.6 Fertilization Rule
# ------------------------------
write_file "$BACKEND_DIR/app/advisor/rules/fertilization_rule.py" 'from typing import Dict, Any, Optional
from .base_rule import BaseRule


class FertilizationRule(BaseRule):
    """
    Rule for fertilization recommendations based on weather conditions.
    High temperatures reduce nutrient absorption efficiency.
    """

    TEMP_THRESHOLD = 34.0

    def matches(self, ctx: Dict[str, Any]) -> bool:
        """Check if fertilization should be delayed due to heat."""
        weather = ctx.get("weather")
        if not weather:
            return False
        return weather.get("tmax", 0) > self.TEMP_THRESHOLD

    def render(self, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate fertilization delay recommendation."""
        temp_max = ctx["weather"]["tmax"]

        return {
            "rule": "fertilization_heat_delay",
            "priority": "medium",
            "category": "fertilization",
            "title_ar": "تأجيل التسميد بسبب ارتفاع الحرارة",
            "title_en": "Delay fertilization due to high temperature",
            "description_ar": f"درجة الحرارة العظمى ({temp_max}°م) تقلل من كفاءة امتصاص العناصر الغذائية.",
            "description_en": f"High temperature ({temp_max}°C) reduces nutrient absorption efficiency.",
            "actions": [
                {
                    "action_ar": "تأجيل التسميد لمدة 24-48 ساعة",
                    "action_en": "Delay fertilization for 24-48 hours",
                    "urgency": "within_24h"
                },
                {
                    "action_ar": "التسميد في الصباح الباكر أو المساء",
                    "action_en": "Apply fertilizer early morning or evening",
                    "urgency": "advisory"
                }
            ],
            "confidence_score": 0.75,
            "field_id": ctx["field_id"],
            "metadata": {
                "current_temp": temp_max,
                "threshold": self.TEMP_THRESHOLD
            },
            "timestamp": ctx["timestamp"]
        }
'

# ------------------------------
# 3.7 Pest Alert Rule
# ------------------------------
write_file "$BACKEND_DIR/app/advisor/rules/pest_alert_rule.py" 'from typing import Dict, Any, Optional
from .base_rule import BaseRule


class PestAlertRule(BaseRule):
    """
    Rule for pest risk alerts based on humidity and temperature.
    High humidity combined with warm temperatures increases pest risk.
    """

    HUMIDITY_THRESHOLD = 75
    TEMP_MIN_THRESHOLD = 22
    TEMP_MAX_THRESHOLD = 32

    def matches(self, ctx: Dict[str, Any]) -> bool:
        """Check if conditions favor pest development."""
        weather = ctx.get("weather")
        if not weather:
            return False

        humidity = weather.get("humidity", 0)
        temp = weather.get("t", 0)

        return (humidity > self.HUMIDITY_THRESHOLD and
                self.TEMP_MIN_THRESHOLD < temp < self.TEMP_MAX_THRESHOLD)

    def render(self, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate pest alert recommendation."""
        humidity = ctx["weather"]["humidity"]
        temp = ctx["weather"]["t"]

        return {
            "rule": "pest_risk_alert",
            "priority": "medium",
            "category": "pest_control",
            "title_ar": "تحذير: ظروف مواتية للآفات",
            "title_en": "Alert: Favorable conditions for pests",
            "description_ar": f"الرطوبة العالية ({humidity}%) مع درجة حرارة معتدلة ({temp:.1f}°م) تزيد خطر الإصابة بالآفات.",
            "description_en": f"High humidity ({humidity}%) with moderate temperature ({temp:.1f}°C) increases pest risk.",
            "actions": [
                {
                    "action_ar": "مراقبة الحقل للكشف المبكر عن الآفات",
                    "action_en": "Monitor field for early pest detection",
                    "urgency": "within_48h"
                },
                {
                    "action_ar": "تجهيز المبيدات الوقائية",
                    "action_en": "Prepare preventive pesticides",
                    "urgency": "advisory"
                }
            ],
            "confidence_score": 0.70,
            "field_id": ctx["field_id"],
            "metadata": {
                "humidity": humidity,
                "temperature": temp
            },
            "timestamp": ctx["timestamp"]
        }
'

# ------------------------------
# 3.8 Advisor Service
# ------------------------------
write_file "$BACKEND_DIR/app/services/advisor_service.py" 'from typing import List, Dict, Any
import logging
from app.advisor.pipelines.context_builder import FieldContextBuilder
from app.advisor.engine.rule_engine import RuleEngine
from app.advisor.rules.irrigation_rule import IrrigationRule
from app.advisor.rules.fertilization_rule import FertilizationRule
from app.advisor.rules.pest_alert_rule import PestAlertRule

logger = logging.getLogger(__name__)


class AdvisorService:
    """
    Main service for field analysis and recommendations.
    Orchestrates context building and rule evaluation.
    """

    def __init__(self, ndvi_service, weather_client, field_service):
        self.ctx_builder = FieldContextBuilder(ndvi_service, weather_client)
        self.engine = RuleEngine([
            IrrigationRule(),
            FertilizationRule(),
            PestAlertRule(),
        ])
        self.field_service = field_service

    def analyze(self, tenant_id: int, field_id: int) -> Dict[str, Any]:
        """
        Analyze a field and generate recommendations.
        """
        logger.info(f"Starting analysis for field {field_id}, tenant {tenant_id}")

        # Get field data
        field = self.field_service.get_field(tenant_id, field_id)
        if not field:
            raise ValueError(f"Field {field_id} not found")

        # Build context
        ctx = self.ctx_builder.build(tenant_id, field)

        # Evaluate rules
        recommendations = self.engine.evaluate(ctx)

        logger.info(f"Analysis complete: {len(recommendations)} recommendations generated")

        return {
            "field_id": field_id,
            "tenant_id": tenant_id,
            "recommendations": recommendations,
            "analysis_summary": {
                "total_recommendations": len(recommendations),
                "critical_count": len([r for r in recommendations if r.get("priority") == "critical"]),
                "high_count": len([r for r in recommendations if r.get("priority") == "high"]),
                "medium_count": len([r for r in recommendations if r.get("priority") == "medium"]),
                "low_count": len([r for r in recommendations if r.get("priority") == "low"]),
            },
            "context": {
                "ndvi_available": ctx.get("ndvi") is not None,
                "weather_available": ctx.get("weather") is not None,
            },
            "timestamp": ctx["timestamp"]
        }

    def get_rule_list(self) -> List[str]:
        """Get list of active rules."""
        return [rule.name for rule in self.engine.rules]
'

# ------------------------------
# 3.9 Updated Advisor Routes
# ------------------------------
write_file "$BACKEND_DIR/app/api/v1/advisor_v2.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.advisor_service import AdvisorService
from app.core.security import get_current_user, TokenData
from app.core.database import get_db
from app.services.ndvi_service import NDVIService
from app.services.field_service import FieldService
from app.utils.weather_client import WeatherClient
from app.core.config import settings
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advisor", tags=["Advisor Intelligence"])


def get_advisor_service(db: Session = Depends(get_db)) -> AdvisorService:
    """Create AdvisorService with dependencies."""
    weather = WeatherClient(settings.OPENWEATHER_API_KEY)
    ndvi_service = NDVIService(db)
    field_service = FieldService(db)
    return AdvisorService(ndvi_service, weather, field_service)


@router.get("/analyze/{field_id}")
async def analyze_field(
    field_id: int,
    current_user: TokenData = Depends(get_current_user),
    advisor: AdvisorService = Depends(get_advisor_service)
):
    """
    Analyze a field and get AI-powered recommendations.
    """
    try:
        result = advisor.analyze(current_user.tenant_id, field_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/rules")
async def list_rules(
    current_user: TokenData = Depends(get_current_user),
    advisor: AdvisorService = Depends(get_advisor_service)
):
    """
    List all active advisor rules.
    """
    return {
        "rules": advisor.get_rule_list(),
        "total": len(advisor.get_rule_list())
    }
'

# ===========================================
# 4️⃣ المرحلة الرابعة — Observability Stack
# ===========================================
echo_header "4️⃣ إعداد Stack المراقبة (Prometheus + Grafana + Loki)"

mkdir -p "$PROJECT_NAME/monitoring/grafana-dashboards"
mkdir -p "$PROJECT_NAME/monitoring/grafana-provisioning/dashboards"
mkdir -p "$PROJECT_NAME/monitoring/grafana-provisioning/datasources"

# ------------------------------
# Prometheus config
# ------------------------------
write_file "$PROJECT_NAME/monitoring/prometheus.yml" 'global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: "field-suite"
    env: "production"

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: "field-suite-api"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: "/metrics"
    scrape_interval: 30s

  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]

  - job_name: "redis-exporter"
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: "postgres-exporter"
    static_configs:
      - targets: ["postgres-exporter:9187"]

  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
'

# ------------------------------
# Prometheus Alerts
# ------------------------------
write_file "$PROJECT_NAME/monitoring/alerts.yml" 'groups:
  - name: field_suite_alerts
    interval: 30s
    rules:
      - alert: APIDown
        expr: up{job="field-suite-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Field Suite API is down"
          description: "API has been unavailable for more than 2 minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is above 2 seconds"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database connections are above 80"

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory usage is above 80%"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk space running low"
          description: "Available disk space is below 15%"
'

# ------------------------------
# Grafana Datasources
# ------------------------------
write_file "$PROJECT_NAME/monitoring/grafana-provisioning/datasources/datasources.yml" 'apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
'

# ------------------------------
# Grafana Dashboard Provisioning
# ------------------------------
write_file "$PROJECT_NAME/monitoring/grafana-provisioning/dashboards/dashboards.yml" 'apiVersion: 1

providers:
  - name: "Field Suite Dashboards"
    orgId: 1
    folder: ""
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
'

# ------------------------------
# Grafana Dashboard
# ------------------------------
write_file "$PROJECT_NAME/monitoring/grafana-dashboards/field-suite-overview.json" '{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 1,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {"mode": "palette-classic"},
          "custom": {"axisCenteredZero": false},
          "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": null}]}
        }
      },
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
      "id": 1,
      "options": {"legend": {"displayMode": "list"}},
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{method}} {{endpoint}}",
          "refId": "A"
        }
      ],
      "title": "Request Rate",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {"mode": "palette-classic"},
          "unit": "s"
        }
      },
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
      "id": 2,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "p95 latency",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "p50 latency",
          "refId": "B"
        }
      ],
      "title": "API Latency",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {"unit": "percent"}
      },
      "gridPos": {"h": 8, "w": 8, "x": 0, "y": 8},
      "id": 3,
      "targets": [
        {
          "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
          "legendFormat": "CPU Usage",
          "refId": "A"
        }
      ],
      "title": "CPU Usage",
      "type": "gauge"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {"unit": "bytes"}
      },
      "gridPos": {"h": 8, "w": 8, "x": 8, "y": 8},
      "id": 4,
      "targets": [
        {
          "expr": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes",
          "legendFormat": "Used Memory",
          "refId": "A"
        }
      ],
      "title": "Memory Usage",
      "type": "gauge"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {"unit": "short"}
      },
      "gridPos": {"h": 8, "w": 8, "x": 16, "y": 8},
      "id": 5,
      "targets": [
        {
          "expr": "redis_connected_clients",
          "legendFormat": "Redis Clients",
          "refId": "A"
        }
      ],
      "title": "Redis Connections",
      "type": "stat"
    }
  ],
  "refresh": "30s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": ["field-suite", "overview"],
  "templating": {"list": []},
  "time": {"from": "now-1h", "to": "now"},
  "timepicker": {},
  "timezone": "browser",
  "title": "Field Suite Overview",
  "uid": "field-suite-overview",
  "version": 1
}'

# ------------------------------
# Loki configuration
# ------------------------------
write_file "$PROJECT_NAME/monitoring/loki-config.yml" 'auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s
  max_transfer_retries: 0
  wal:
    enabled: true
    dir: /loki/wal

schema_config:
  configs:
    - from: 2023-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v12
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
'

# ------------------------------
# Promtail configuration
# ------------------------------
write_file "$PROJECT_NAME/monitoring/promtail-config.yml" 'server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*.log

  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          __path__: /var/log/syslog
'

# ===========================================
# Docker Compose (Monitoring Services)
# ===========================================
write_file "$PROJECT_NAME/docker-compose.monitoring.yml" 'version: "3.8"

services:
  node-exporter:
    image: prom/node-exporter:latest
    container_name: field_suite_node_exporter
    ports:
      - "127.0.0.1:9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
    networks:
      - field_suite_network
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: field_suite_redis_exporter
    ports:
      - "127.0.0.1:9121:9121"
    environment:
      REDIS_ADDR: redis://redis:6379
    networks:
      - field_suite_network
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: field_suite_postgres_exporter
    ports:
      - "127.0.0.1:9187:9187"
    environment:
      DATA_SOURCE_NAME: "postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-field_suite_db}?sslmode=disable"
    networks:
      - field_suite_network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: field_suite_prometheus
    ports:
      - "127.0.0.1:9091:9090"  # Using 9091 to avoid conflict with main project
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"
      - "--web.enable-lifecycle"
    networks:
      - field_suite_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: field_suite_grafana
    ports:
      - "127.0.0.1:3003:3000"  # Using 3003 to avoid conflict with main project
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/var/lib/grafana/dashboards:ro
      - ./monitoring/grafana-provisioning:/etc/grafana/provisioning:ro
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin123}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_SERVER_ROOT_URL: "%(protocol)s://%(domain)s:%(http_port)s/grafana/"
    networks:
      - field_suite_network
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: field_suite_loki
    ports:
      - "127.0.0.1:3100:3100"
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - field_suite_network
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    container_name: field_suite_promtail
    volumes:
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - field_suite_network
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  loki_data:

networks:
  field_suite_network:
    external: true
'

# ===========================================
# Final Summary
# ===========================================
echo_header "✨ المرحلة 3 + 4 اكتملت بنجاح!"

echo_success "🧠 Advisor Intelligence Service جاهز"
echo_info "   - Rule Engine with 3 rules (Irrigation, Fertilization, Pest Alert)"
echo_info "   - Context Builder with NDVI + Weather integration"
echo_info "   - Weather Client with OpenWeatherMap API"
echo ""
echo_success "📊 Observability Stack جاهز"
echo_info "   - Prometheus: http://localhost:9091"
echo_info "   - Grafana: http://localhost:3003 (admin/${GRAFANA_PASSWORD:-admin123})"
echo_info "   - Loki: http://localhost:3100"
echo ""
echo -e "${YELLOW}⚠️ الخطوات التالية:${NC}"
echo "   1. تأكد من وجود OPENWEATHER_API_KEY في ملف .env"
echo "   2. docker-compose -f docker-compose.monitoring.yml up -d"
echo "   3. افتح Grafana وتحقق من لوحات المراقبة"
echo ""

exit 0
