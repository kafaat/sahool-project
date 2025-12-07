"""
Sahool Yemen - Query Service (خدمة الاستعلامات)
Natural language query interface for agricultural data.
"""

import os
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query as QueryParam
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response


# =============================================================================
# Configuration
# =============================================================================

app = FastAPI(
    title="Sahool Query Service",
    description="خدمة الاستعلامات - واجهة استعلام باللغة الطبيعية",
    version="9.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - use specific origins in production
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = bool(CORS_ORIGINS)  # Only allow credentials with specific origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=CORS_ALLOW_CREDENTIALS,  # False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('sahool_query_requests_total', 'Total query requests', ['query_type', 'status'])
REQUEST_LATENCY = Histogram('sahool_query_request_duration_seconds', 'Request latency', ['endpoint'])
QUERY_PARSED = Counter('sahool_query_parsed_total', 'Queries parsed', ['language', 'intent'])

# =============================================================================
# Models
# =============================================================================


class QueryLanguage(str, Enum):
    ARABIC = "ar"
    ENGLISH = "en"
    AUTO = "auto"


class QueryIntent(str, Enum):
    NDVI_STATUS = "ndvi_status"
    WEATHER_INFO = "weather_info"
    FIELD_INFO = "field_info"
    REGION_STATS = "region_stats"
    ALERTS = "alerts"
    RECOMMENDATIONS = "recommendations"
    COMPARISON = "comparison"
    TREND = "trend"
    UNKNOWN = "unknown"


class ParsedQuery(BaseModel):
    original_query: str
    language: QueryLanguage
    intent: QueryIntent
    entities: Dict[str, Any]
    confidence: float
    sql_equivalent: Optional[str] = None


class QueryResult(BaseModel):
    query_id: str
    parsed: ParsedQuery
    results: List[Dict[str, Any]]
    summary_ar: str
    summary_en: str
    executed_at: datetime
    execution_time_ms: float


class NaturalQuery(BaseModel):
    query: str = Field(..., description="Natural language query in Arabic or English")
    language: QueryLanguage = QueryLanguage.AUTO
    limit: int = Field(10, ge=1, le=100)


# =============================================================================
# Arabic/English Query Patterns
# =============================================================================

ARABIC_PATTERNS = {
    # NDVI queries
    r"(ما|كيف|كم).*(ndvi|صحة|حالة).*(الحقل|حقل|المحصول)": QueryIntent.NDVI_STATUS,
    r"(أرني|عرض|اظهر).*(ndvi|صحة)": QueryIntent.NDVI_STATUS,

    # Weather queries
    r"(ما|كيف).*(الطقس|الجو|درجة الحرارة|الرطوبة|المطر)": QueryIntent.WEATHER_INFO,
    r"(توقعات|تنبؤات).*(الطقس|الجو)": QueryIntent.WEATHER_INFO,
    r"(هل).*(سيمطر|ستمطر|مطر)": QueryIntent.WEATHER_INFO,

    # Field info
    r"(معلومات|بيانات|تفاصيل).*(الحقل|حقل)": QueryIntent.FIELD_INFO,
    r"(كم).*(مساحة|حجم).*(الحقل|الحقول)": QueryIntent.FIELD_INFO,

    # Region stats
    r"(إحصائيات|أرقام|بيانات).*(المحافظة|المنطقة|صنعاء|عدن|تعز)": QueryIntent.REGION_STATS,
    r"(كم).*(حقل|مزرعة|مزارع).*(في|بـ)": QueryIntent.REGION_STATS,

    # Alerts
    r"(تنبيهات|تحذيرات|إنذارات)": QueryIntent.ALERTS,
    r"(هل يوجد|هناك).*(تحذير|تنبيه|مشكلة)": QueryIntent.ALERTS,

    # Recommendations
    r"(ماذا|ما).*(أفعل|نفعل|يجب)": QueryIntent.RECOMMENDATIONS,
    r"(نصائح|توصيات|اقتراحات)": QueryIntent.RECOMMENDATIONS,

    # Comparison
    r"(قارن|مقارنة).*(بين|الحقول|المناطق)": QueryIntent.COMPARISON,
    r"(أي|أيهما).*(أفضل|أحسن)": QueryIntent.COMPARISON,

    # Trends
    r"(تطور|تغير|اتجاه).*(خلال|على مدى)": QueryIntent.TREND,
    r"(كيف تغير|كيف تطور)": QueryIntent.TREND,
}

ENGLISH_PATTERNS = {
    # NDVI queries
    r"(what|how).*(ndvi|health|status).*(field|crop)": QueryIntent.NDVI_STATUS,
    r"(show|display).*(ndvi|health)": QueryIntent.NDVI_STATUS,

    # Weather queries
    r"(what|how).*(weather|temperature|humidity|rain)": QueryIntent.WEATHER_INFO,
    r"(weather forecast|forecast)": QueryIntent.WEATHER_INFO,
    r"(will it rain|is it going to rain)": QueryIntent.WEATHER_INFO,

    # Field info
    r"(information|details|data).*(field)": QueryIntent.FIELD_INFO,
    r"(how many|how much).*(area|size).*(field)": QueryIntent.FIELD_INFO,

    # Region stats
    r"(statistics|stats|data).*(region|governorate|sana|aden|taiz)": QueryIntent.REGION_STATS,
    r"(how many).*(field|farm).*(in)": QueryIntent.REGION_STATS,

    # Alerts
    r"(alerts|warnings|notifications)": QueryIntent.ALERTS,
    r"(is there|are there).*(warning|alert|problem)": QueryIntent.ALERTS,

    # Recommendations
    r"(what should|what can).*(do|i do)": QueryIntent.RECOMMENDATIONS,
    r"(advice|recommendations|suggestions)": QueryIntent.RECOMMENDATIONS,

    # Comparison
    r"(compare|comparison).*(between|fields|regions)": QueryIntent.COMPARISON,
    r"(which).*(better|best)": QueryIntent.COMPARISON,

    # Trends
    r"(trend|change|evolution).*(over|during)": QueryIntent.TREND,
    r"(how did|how has).*(change|evolve)": QueryIntent.TREND,
}

ENTITY_PATTERNS = {
    "field_id": r"(field|حقل)\s*[#]?(\w{8}-\w{4}-\w{4}-\w{4}-\w{12}|\d+)",
    "region_ar": r"(صنعاء|عدن|تعز|الحديدة|إب|حضرموت|ذمار|المكلا|عمران|صعدة|حجة|البيضاء|شبوة|لحج|مأرب)",
    "region_en": r"(sana'?a|aden|taiz|hodeidah|ibb|hadramout|dhamar|mukalla|amran|saada|hajjah|bayda|shabwa|lahj|marib)",
    "crop_type": r"(wheat|قمح|coffee|بن|mango|مانجو|qat|قات|grapes|عنب|tomato|طماطم|potato|بطاطس|sorghum|ذرة)",
    "date_range": r"(last|الأخير|السابق)\s*(\d+)\s*(day|يوم|week|أسبوع|month|شهر)",
    "number": r"(\d+(?:\.\d+)?)",
}

# =============================================================================
# Query Parser
# =============================================================================


def detect_language(text: str) -> QueryLanguage:
    """Detect if text is Arabic or English."""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(re.findall(r'\w', text))

    if total_chars == 0:
        return QueryLanguage.ENGLISH

    arabic_ratio = arabic_chars / total_chars
    return QueryLanguage.ARABIC if arabic_ratio > 0.3 else QueryLanguage.ENGLISH


def parse_intent(query: str, language: QueryLanguage) -> tuple[QueryIntent, float]:
    """Parse the intent from a natural language query."""
    query_lower = query.lower()
    patterns = ARABIC_PATTERNS if language == QueryLanguage.ARABIC else ENGLISH_PATTERNS

    for pattern, intent in patterns.items():
        if re.search(pattern, query_lower, re.IGNORECASE):
            return intent, 0.85

    return QueryIntent.UNKNOWN, 0.3


def extract_entities(query: str) -> Dict[str, Any]:
    """Extract entities from query."""
    entities = {}

    for entity_name, pattern in ENTITY_PATTERNS.items():
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            if entity_name in ["field_id", "number"]:
                entities[entity_name] = matches[0] if isinstance(matches[0], str) else matches[0][-1]
            elif entity_name == "date_range":
                if matches:
                    match = matches[0]
                    value = int(match[1])
                    unit = match[2].lower()
                    entities["date_range"] = {"value": value, "unit": unit}
            else:
                entities[entity_name] = matches[0]

    return entities


def generate_sql_equivalent(intent: QueryIntent, entities: Dict[str, Any]) -> str:
    """Generate SQL equivalent for the query (for reference/debugging)."""
    sql_templates = {
        QueryIntent.NDVI_STATUS: """
            SELECT f.name_ar, n.ndvi_value, n.acquisition_date
            FROM sahool.fields f
            JOIN sahool.ndvi_results n ON f.id = n.field_id
            WHERE f.id = :field_id
            ORDER BY n.acquisition_date DESC
            LIMIT 10
        """,
        QueryIntent.WEATHER_INFO: """
            SELECT w.temperature, w.humidity, w.rainfall_mm, w.forecast_date
            FROM sahool.weather_data w
            WHERE w.region_id = :region_id
            ORDER BY w.forecast_date DESC
            LIMIT 7
        """,
        QueryIntent.FIELD_INFO: """
            SELECT f.*, r.name_ar as region_name
            FROM sahool.fields f
            JOIN sahool.regions r ON f.region_id = r.id
            WHERE f.id = :field_id
        """,
        QueryIntent.REGION_STATS: """
            SELECT r.name_ar, COUNT(f.id) as field_count, SUM(f.area_hectares) as total_area
            FROM sahool.regions r
            LEFT JOIN sahool.fields f ON r.id = f.region_id
            WHERE r.name_ar = :region_name
            GROUP BY r.id
        """,
        QueryIntent.ALERTS: """
            SELECT a.alert_type, a.severity, a.title_ar, a.created_at
            FROM sahool.alerts a
            WHERE a.status = 'active'
            ORDER BY a.severity DESC, a.created_at DESC
            LIMIT 20
        """,
    }

    return sql_templates.get(intent, "-- Complex query, requires custom handling")

# =============================================================================
# Mock Data Generator (In production, queries DB)
# =============================================================================


def execute_query(
    intent: QueryIntent, entities: Dict[str, Any], limit: int
) -> List[Dict[str, Any]]:
    """Execute query and return results. In production, this queries the database."""

    if intent == QueryIntent.NDVI_STATUS:
        return [
            {"field_id": "f-001", "field_name": "حقل القمح", "ndvi": 0.65, "health": "جيد"},
            {"field_id": "f-002", "field_name": "حقل البن", "ndvi": 0.72, "health": "ممتاز"},
            {"field_id": "f-003", "field_name": "حقل الذرة", "ndvi": 0.38, "health": "يحتاج اهتمام"},
        ][:limit]

    elif intent == QueryIntent.WEATHER_INFO:
        return [
            {"date": "2024-12-03", "temp_min": 18, "temp_max": 28, "humidity": 45, "condition": "مشمس"},
            {"date": "2024-12-04", "temp_min": 17, "temp_max": 27, "humidity": 50, "condition": "غائم جزئياً"},
            {"date": "2024-12-05", "temp_min": 16, "temp_max": 25, "humidity": 60, "condition": "ممطر"},
        ][:limit]

    elif intent == QueryIntent.FIELD_INFO:
        return [
            {
                "field_id": entities.get("field_id", "f-001"),
                "name_ar": "حقل القمح الشمالي",
                "area_hectares": 15.5,
                "crop_type": "wheat",
                "crop_name_ar": "القمح",
                "region": "صنعاء",
                "status": "active",
                "planting_date": "2024-10-15"
            }
        ]

    elif intent == QueryIntent.REGION_STATS:
        region = entities.get("region_ar") or entities.get("region_en", "صنعاء")
        return [
            {
                "region": region,
                "total_fields": 245,
                "total_area_hectares": 3250.5,
                "active_farmers": 180,
                "avg_ndvi": 0.58,
                "top_crops": ["قمح", "بن", "قات"]
            }
        ]

    elif intent == QueryIntent.ALERTS:
        return [
            {"type": "weather", "severity": "high", "title_ar": "موجة حر متوقعة"},
            {"type": "ndvi", "severity": "medium", "title_ar": "انخفاض صحة المحصول"},
        ][:limit]

    elif intent == QueryIntent.RECOMMENDATIONS:
        return [
            {"type": "irrigation", "priority": "high", "title_ar": "زيادة الري"},
            {"type": "fertilization", "priority": "medium", "title_ar": "إضافة سماد نيتروجيني"},
        ][:limit]

    elif intent == QueryIntent.COMPARISON:
        return [
            {"field_a": "حقل 1", "field_b": "حقل 2", "ndvi_a": 0.65, "ndvi_b": 0.72}
        ]

    elif intent == QueryIntent.TREND:
        return [
            {"month": "October", "avg_ndvi": 0.55},
            {"month": "November", "avg_ndvi": 0.60},
            {"month": "December", "avg_ndvi": 0.65},
        ][:limit]

    return [{"message": "No results found", "message_ar": "لا توجد نتائج"}]


def generate_summary(
    intent: QueryIntent, results: List[Dict], language: QueryLanguage
) -> tuple[str, str]:
    """Generate human-readable summary of results."""

    if not results:
        return "لا توجد نتائج للاستعلام", "No results found for the query"

    if intent == QueryIntent.NDVI_STATUS:
        avg_ndvi = sum(r.get("ndvi", 0) for r in results) / len(results)
        ar = f"تم العثور على {len(results)} حقل. متوسط NDVI: {avg_ndvi:.2f}"
        en = f"Found {len(results)} fields. Average NDVI: {avg_ndvi:.2f}"

    elif intent == QueryIntent.WEATHER_INFO:
        ar = f"توقعات الطقس لـ {len(results)} أيام قادمة"
        en = f"Weather forecast for the next {len(results)} days"

    elif intent == QueryIntent.REGION_STATS:
        if results:
            r = results[0]
            ar = f"منطقة {r.get('region')}: {r.get('total_fields')} حقل"
            en = f"Region {r.get('region')}: {r.get('total_fields')} fields"
        else:
            ar, en = "لا توجد بيانات", "No data available"

    elif intent == QueryIntent.ALERTS:
        high_count = sum(1 for r in results if r.get("severity") == "high")
        ar = f"{len(results)} تنبيه، منها {high_count} عالي الأهمية"
        en = f"{len(results)} alerts, {high_count} high priority"

    else:
        ar = f"تم العثور على {len(results)} نتيجة"
        en = f"Found {len(results)} results"

    return ar, en

# =============================================================================
# API Endpoints
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "query", "version": "9.0.0"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")


@app.post("/api/v1/query", response_model=QueryResult)
async def execute_natural_query(query_request: NaturalQuery):
    """
    Execute a natural language query.
    تنفيذ استعلام باللغة الطبيعية.

    Examples:
    - "ما حالة صحة الحقول في صنعاء؟"
    - "What is the weather forecast?"
    - "كم عدد الحقول في تعز؟"
    - "Show me NDVI trends for the last month"
    """
    import time
    start_time = time.time()

    with REQUEST_LATENCY.labels(endpoint="query").time():
        try:
            query_text = query_request.query.strip()

            # Detect language
            language = query_request.language
            if language == QueryLanguage.AUTO:
                language = detect_language(query_text)

            # Parse intent
            intent, confidence = parse_intent(query_text, language)

            # Extract entities
            entities = extract_entities(query_text)

            # Generate SQL equivalent
            sql = generate_sql_equivalent(intent, entities)

            # Create parsed query object
            parsed = ParsedQuery(
                original_query=query_text,
                language=language,
                intent=intent,
                entities=entities,
                confidence=confidence,
                sql_equivalent=sql.strip()
            )

            # Execute query
            results = execute_query(intent, entities, query_request.limit)

            # Generate summary
            summary_ar, summary_en = generate_summary(intent, results, language)

            execution_time = (time.time() - start_time) * 1000

            REQUEST_COUNT.labels(query_type=intent.value, status="success").inc()
            QUERY_PARSED.labels(language=language.value, intent=intent.value).inc()

            return QueryResult(
                query_id=f"q-{int(start_time * 1000)}",
                parsed=parsed,
                results=results,
                summary_ar=summary_ar,
                summary_en=summary_en,
                executed_at=datetime.utcnow(),
                execution_time_ms=execution_time
            )

        except Exception as e:
            REQUEST_COUNT.labels(query_type="error", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/query/suggestions")
async def get_query_suggestions(
    language: QueryLanguage = QueryLanguage.ARABIC,
    category: Optional[str] = None
):
    """
    Get example queries/suggestions.
    الحصول على أمثلة للاستعلامات.
    """
    suggestions = {
        "ar": {
            "ndvi": [
                "ما حالة صحة الحقول؟",
                "أرني قيم NDVI لحقولي",
                "أي الحقول تحتاج اهتمام؟"
            ],
            "weather": [
                "ما توقعات الطقس لهذا الأسبوع؟",
                "هل سيمطر غداً؟",
                "ما درجة الحرارة المتوقعة؟"
            ],
            "fields": [
                "كم عدد حقولي؟",
                "ما مساحة حقولي الإجمالية؟",
                "معلومات عن الحقل الشمالي"
            ],
            "regions": [
                "إحصائيات منطقة صنعاء",
                "كم حقل في تعز؟",
                "أي منطقة لديها أعلى إنتاج؟"
            ],
            "alerts": [
                "هل يوجد تنبيهات؟",
                "أرني التحذيرات الحالية",
                "ما المشاكل في حقولي؟"
            ]
        },
        "en": {
            "ndvi": [
                "What is the health status of my fields?",
                "Show me NDVI values",
                "Which fields need attention?"
            ],
            "weather": [
                "What is the weather forecast?",
                "Will it rain tomorrow?",
                "What is the expected temperature?"
            ],
            "fields": [
                "How many fields do I have?",
                "What is my total field area?",
                "Information about field 1"
            ],
            "regions": [
                "Statistics for Sana'a region",
                "How many fields in Taiz?",
                "Which region has highest production?"
            ],
            "alerts": [
                "Are there any alerts?",
                "Show current warnings",
                "What problems are in my fields?"
            ]
        }
    }

    lang_key = "ar" if language == QueryLanguage.ARABIC else "en"

    if category and category in suggestions[lang_key]:
        return {"category": category, "suggestions": suggestions[lang_key][category]}

    return {"categories": suggestions[lang_key]}


@app.get("/api/v1/query/parse")
async def parse_query_only(
    query: str = QueryParam(..., description="Natural language query"),
    language: QueryLanguage = QueryLanguage.AUTO
):
    """
    Parse a query without executing it.
    تحليل الاستعلام دون تنفيذه.
    """
    if language == QueryLanguage.AUTO:
        language = detect_language(query)

    intent, confidence = parse_intent(query, language)
    entities = extract_entities(query)
    sql = generate_sql_equivalent(intent, entities)

    return ParsedQuery(
        original_query=query,
        language=language,
        intent=intent,
        entities=entities,
        confidence=confidence,
        sql_equivalent=sql.strip()
    )

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
