"""
سهول اليمن - OpenAPI Configuration
تكوين توثيق API المشترك
"""
from .config import (
    OpenAPIConfig,
    get_openapi_config,
    API_TAGS,
    SECURITY_SCHEMES,
    get_custom_openapi,
)
from .examples import (
    WeatherExamples,
    GeoExamples,
    FieldExamples,
    AuthExamples,
)

__all__ = [
    "OpenAPIConfig",
    "get_openapi_config",
    "API_TAGS",
    "SECURITY_SCHEMES",
    "get_custom_openapi",
    "WeatherExamples",
    "GeoExamples",
    "FieldExamples",
    "AuthExamples",
]
