"""
Sahool Shared Library - المكتبة المشتركة لمنصة سهول
"""
__version__ = "2.0.0"

# Auth
from sahool_shared.auth import (
    hash_password,
    verify_password,
    needs_rehash,
    JWTHandler,
)

# Database
from sahool_shared.database import (
    DatabaseManager,
    get_async_db_session,
)

# Models
from sahool_shared.models import (
    Alert,
    Field,
    PlantHealth,
    Region,
    Farmer,
)

# Schemas
from sahool_shared.schemas import (
    TokenResponse,
    FieldResponse,
    WeatherResponse,
)

# Try to import optional modules
try:
    from sahool_shared.secrets_manager import secrets_manager, get_secrets_manager
except ImportError:
    secrets_manager = None
    get_secrets_manager = None

try:
    from sahool_shared.logging import get_logger, OtelLogger
except ImportError:
    get_logger = None
    OtelLogger = None

try:
    from sahool_shared.resilience import CircuitBreaker, get_circuit_breaker
except ImportError:
    CircuitBreaker = None
    get_circuit_breaker = None

__all__ = [
    # Version
    "__version__",
    # Auth
    "hash_password",
    "verify_password",
    "needs_rehash",
    "JWTHandler",
    # Database
    "DatabaseManager",
    "get_async_db_session",
    # Models
    "Alert",
    "Field",
    "PlantHealth",
    "Region",
    "Farmer",
    # Schemas
    "TokenResponse",
    "FieldResponse",
    "WeatherResponse",
    # Secrets
    "secrets_manager",
    "get_secrets_manager",
    # Logging
    "get_logger",
    "OtelLogger",
    # Resilience
    "CircuitBreaker",
    "get_circuit_breaker",
]
