#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 1: Backend Core - Config, Database, Logging
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء ملفات Backend Core..."

# ─────────────────────────────────────────────────────────────────────────────
# Core Config (Pydantic v2)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/core/config.py" << 'EOF'
"""
Application Configuration - Pydantic Settings v2
إعدادات التطبيق باستخدام Pydantic v2
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    """إعدادات التطبيق الرئيسية"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Application
    # ─────────────────────────────────────────────────────────────────────────
    APP_NAME: str = "Field Suite Pro"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "نظام إدارة الحقول الزراعية المتقدم"
    DEBUG: bool = False
    ENV: str = Field(default="development", pattern="^(development|staging|production)$")

    # ─────────────────────────────────────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ─────────────────────────────────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────────────────────────────────
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "field_suite_db"
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v, info):
        if v:
            return v
        values = info.data
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    # ─────────────────────────────────────────────────────────────────────────
    # Redis
    # ─────────────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # ─────────────────────────────────────────────────────────────────────────
    # Celery
    # ─────────────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ─────────────────────────────────────────────────────────────────────────
    # External APIs
    # ─────────────────────────────────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""
    SENTINEL_CLIENT_ID: str = ""
    SENTINEL_CLIENT_SECRET: str = ""

    # ─────────────────────────────────────────────────────────────────────────
    # Rate Limiting
    # ─────────────────────────────────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/minute"

    # ─────────────────────────────────────────────────────────────────────────
    # File Upload
    # ─────────────────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".tif", ".tiff", ".jp2", ".png", ".jpg"]
    UPLOAD_DIR: str = "/tmp/uploads"

    # ─────────────────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ─────────────────────────────────────────────────────────────────────────
    # Features
    # ─────────────────────────────────────────────────────────────────────────
    ENABLE_METRICS: bool = True
    ENABLE_WEBSOCKET: bool = True
    ENABLE_ADVISOR: bool = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Database - Async SQLAlchemy
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/core/database.py" << 'EOF'
"""
Database Configuration - Async SQLAlchemy
إعداد قاعدة البيانات باستخدام SQLAlchemy غير المتزامن
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from typing import AsyncGenerator

from app.core.config import settings

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all models"""
    metadata = metadata


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Redis Manager
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/core/redis.py" << 'EOF'
"""
Redis Configuration and Cache Manager
إدارة Redis والتخزين المؤقت
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
from datetime import timedelta

from app.core.config import settings


class RedisManager:
    """Redis connection and cache manager"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Initialize Redis connection"""
        self._client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client"""
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache"""
        ttl = ttl or settings.REDIS_CACHE_TTL
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        await self.client.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """Delete keys matching pattern"""
        async for key in self.client.scan_iter(match=pattern):
            await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0


# Global instance
redis_manager = RedisManager()


async def get_redis() -> RedisManager:
    """Dependency for getting Redis manager"""
    return redis_manager
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/core/logging.py" << 'EOF'
"""
Structured Logging Configuration
نظام التسجيل المنظم
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        log_record["app"] = settings.APP_NAME
        log_record["env"] = settings.ENV

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging() -> None:
    """Configure application logging"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Security Utilities
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/core/security.py" << 'EOF'
"""
Security Utilities - Password Hashing & JWT
أدوات الأمان - تشفير كلمات المرور و JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    if extra_data:
        to_encode.update(extra_data)

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(subject: str) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/core/exceptions.py" << 'EOF'
"""
Custom Exceptions
الاستثناءات المخصصة
"""
from typing import Any, Optional, Dict


class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AppException):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            status_code=401
        )


class AuthorizationError(AppException):
    """Authorization failed"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )


class NotFoundError(AppException):
    """Resource not found"""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class ValidationError(AppException):
    """Validation error"""

    def __init__(self, message: str, errors: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors or {}}
        )


class RateLimitError(AppException):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT",
            status_code=429
        )


class FileUploadError(AppException):
    """File upload error"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="FILE_UPLOAD_ERROR",
            status_code=400
        )
EOF

log_success "تم إنشاء ملفات Backend Core"
