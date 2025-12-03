"""
Logging Utilities
أدوات التسجيل
"""

import logging
import sys
from typing import Optional

import structlog


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    service_name: Optional[str] = None,
) -> None:
    """
    Setup structured logging with structlog.
    إعداد التسجيل المنظم مع structlog
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if service_name:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
        )

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    الحصول على مسجل منظم
    """
    logger = structlog.get_logger(name)
    return logger


class RequestLogger:
    """
    Context manager for request logging.
    مدير السياق لتسجيل الطلبات
    """

    def __init__(self, request_id: str, service: str, **kwargs):
        self.request_id = request_id
        self.service = service
        self.extra = kwargs
        self.logger = get_logger()

    def __enter__(self):
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=self.request_id,
            service=self.service,
            **self.extra
        )
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.clear_contextvars()
        return False
