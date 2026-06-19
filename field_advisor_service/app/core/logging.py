"""
Logging configuration for Field Advisor Service
"""
import logging
import sys
from datetime import datetime


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup structured logging"""

    logger = logging.getLogger("field_advisor")
    logger.setLevel(getattr(logging, level.upper()))

    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"service": "field-advisor", "message": "%(message)s", '
        '"module": "%(module)s", "function": "%(funcName)s"}'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = setup_logging()
