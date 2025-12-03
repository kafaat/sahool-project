"""
Sahool Yemen - Test Configuration
سهول اليمن - إعدادات الاختبارات

Shared fixtures and configuration for all tests.
"""
import pytest
import httpx
from typing import Generator, Dict, Any


# =============================================================================
# Yemen Data Fixtures
# =============================================================================

@pytest.fixture
def yemen_governorates() -> list[Dict[str, Any]]:
    """All 20 Yemen governorates with coordinates"""
    return [
        {"id": 1, "name_ar": "صنعاء", "name_en": "Sanaa", "lat": 15.35, "lon": 44.20},
        {"id": 2, "name_ar": "عدن", "name_en": "Aden", "lat": 12.82, "lon": 45.03},
        {"id": 3, "name_ar": "تعز", "name_en": "Taiz", "lat": 13.57, "lon": 44.02},
        {"id": 4, "name_ar": "حضرموت", "name_en": "Hadramaut", "lat": 15.95, "lon": 48.78},
        {"id": 5, "name_ar": "الحديدة", "name_en": "Al Hudaydah", "lat": 14.80, "lon": 42.95},
        {"id": 6, "name_ar": "إب", "name_en": "Ibb", "lat": 13.97, "lon": 44.18},
        {"id": 7, "name_ar": "ذمار", "name_en": "Dhamar", "lat": 14.55, "lon": 44.40},
        {"id": 8, "name_ar": "شبوة", "name_en": "Shabwah", "lat": 14.78, "lon": 47.02},
        {"id": 9, "name_ar": "لحج", "name_en": "Lahij", "lat": 13.05, "lon": 44.88},
        {"id": 10, "name_ar": "أبين", "name_en": "Abyan", "lat": 13.58, "lon": 45.72},
        {"id": 11, "name_ar": "مأرب", "name_en": "Marib", "lat": 15.47, "lon": 45.32},
        {"id": 12, "name_ar": "الجوف", "name_en": "Al Jawf", "lat": 16.20, "lon": 45.50},
        {"id": 13, "name_ar": "عمران", "name_en": "Amran", "lat": 15.67, "lon": 43.95},
        {"id": 14, "name_ar": "حجة", "name_en": "Hajjah", "lat": 15.70, "lon": 43.60},
        {"id": 15, "name_ar": "المحويت", "name_en": "Al Mahwit", "lat": 15.47, "lon": 43.55},
        {"id": 16, "name_ar": "ريمة", "name_en": "Raymah", "lat": 14.68, "lon": 43.72},
        {"id": 17, "name_ar": "المهرة", "name_en": "Al Maharah", "lat": 16.52, "lon": 52.17},
        {"id": 18, "name_ar": "سقطرى", "name_en": "Socotra", "lat": 12.47, "lon": 53.87},
        {"id": 19, "name_ar": "البيضاء", "name_en": "Al Bayda", "lat": 14.17, "lon": 45.57},
        {"id": 20, "name_ar": "صعدة", "name_en": "Saada", "lat": 16.93, "lon": 43.77},
    ]


@pytest.fixture
def yemen_crops() -> list[Dict[str, str]]:
    """Common crops grown in Yemen"""
    return [
        {"id": "wheat", "name_ar": "قمح", "name_en": "Wheat"},
        {"id": "corn", "name_ar": "ذرة", "name_en": "Corn"},
        {"id": "barley", "name_ar": "شعير", "name_en": "Barley"},
        {"id": "coffee", "name_ar": "بن", "name_en": "Coffee"},
        {"id": "tomato", "name_ar": "طماطم", "name_en": "Tomato"},
        {"id": "onion", "name_ar": "بصل", "name_en": "Onion"},
        {"id": "potato", "name_ar": "بطاطس", "name_en": "Potato"},
        {"id": "vegetables", "name_ar": "خضروات", "name_en": "Vegetables"},
        {"id": "fruits", "name_ar": "فواكه", "name_en": "Fruits"},
        {"id": "fodder", "name_ar": "أعلاف", "name_en": "Fodder"},
    ]


@pytest.fixture
def yemen_bounds() -> Dict[str, float]:
    """Geographic bounds for Yemen"""
    return {
        "min_lat": 12.0,
        "max_lat": 19.0,
        "min_lon": 42.0,
        "max_lon": 55.0,
    }


# =============================================================================
# HTTP Client Fixtures
# =============================================================================

@pytest.fixture
def http_client() -> Generator[httpx.Client, None, None]:
    """HTTP client for testing external endpoints"""
    client = httpx.Client(timeout=10.0)
    yield client
    client.close()


@pytest.fixture
def async_http_client() -> Generator[httpx.AsyncClient, None, None]:
    """Async HTTP client for testing external endpoints"""
    client = httpx.AsyncClient(timeout=10.0)
    yield client
    # Note: cleanup happens in async context


# =============================================================================
# Service URL Fixtures
# =============================================================================

@pytest.fixture
def service_urls() -> Dict[str, str]:
    """URLs for all services"""
    return {
        "gateway": "http://localhost",
        "backend": "http://localhost:8000",
        "weather": "http://localhost:8010",
        "imagery": "http://localhost:8011",
        "geo": "http://localhost:8012",
        "analytics": "http://localhost:8013",
        "query": "http://localhost:8014",
        "advisor": "http://localhost:8015",
        "prometheus": "http://localhost:9091",
        "grafana": "http://localhost:3003",
    }


# =============================================================================
# Mock Data Fixtures
# =============================================================================

@pytest.fixture
def sample_field() -> Dict[str, Any]:
    """Sample field data for testing"""
    return {
        "id": 1,
        "farmer_id": 1,
        "region_id": 1,
        "name": "حقل القمح الرئيسي",
        "crop_type": "قمح",
        "area_ha": 15.5,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[44.0, 15.0], [44.1, 15.0], [44.1, 15.1], [44.0, 15.1], [44.0, 15.0]]]
        },
        "ndvi_current": 0.65,
        "irrigation_type": "drip",
        "soil_type": "loamy",
    }


@pytest.fixture
def sample_weather_data() -> Dict[str, Any]:
    """Sample weather data for testing"""
    return {
        "location": {"lat": 15.35, "lon": 44.20, "name": "صنعاء"},
        "current": {
            "temperature": 28.5,
            "humidity": 35,
            "wind_speed": 12,
            "conditions": "sunny",
        },
        "forecast": [
            {"date": "2024-06-01", "temp_max": 32, "temp_min": 20, "rain_prob": 10},
            {"date": "2024-06-02", "temp_max": 31, "temp_min": 19, "rain_prob": 5},
            {"date": "2024-06-03", "temp_max": 33, "temp_min": 21, "rain_prob": 15},
        ],
    }


@pytest.fixture
def sample_ndvi_data() -> Dict[str, Any]:
    """Sample NDVI data for testing"""
    return {
        "field_id": 1,
        "date": "2024-06-01",
        "ndvi_mean": 0.65,
        "ndvi_min": 0.45,
        "ndvi_max": 0.82,
        "status": "جيد",
        "health_score": 85,
    }


# =============================================================================
# Helper Functions
# =============================================================================

def is_service_running(url: str) -> bool:
    """Check if a service is running"""
    try:
        response = httpx.get(f"{url}/health", timeout=5.0)
        return response.status_code == 200
    except httpx.ConnectError:
        return False
    except Exception:
        return False


@pytest.fixture
def skip_if_no_services(service_urls):
    """Skip test if services are not running"""
    if not is_service_running(service_urls["backend"]):
        pytest.skip("Services not running")
