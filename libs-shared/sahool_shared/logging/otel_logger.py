"""
OpenTelemetry Logger - Sahool Yemen Platform
نظام التسجيل المركزي
"""
import logging
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Optional imports
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False


class OtelLogger:
    """OpenTelemetry-enabled logger"""

    def __init__(self, service_name: str, service_version: str = "2.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.tracer = None

        self._setup_otel()
        self.logger = self._configure_logger()

    def _setup_otel(self):
        """Setup OpenTelemetry tracing"""
        if not HAS_OTEL:
            return

        try:
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "deployment.environment": os.getenv('ENVIRONMENT', 'development'),
            })

            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)

            self.tracer = trace.get_tracer(self.service_name)
        except Exception as e:
            logging.warning(f"Failed to setup OpenTelemetry: {e}")

    def _configure_logger(self) -> logging.Logger:
        """Configure the logger with JSON formatting"""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
        logger.handlers.clear()

        handler = logging.StreamHandler()

        if HAS_JSON_LOGGER:
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S%z'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _get_trace_context(self) -> Dict[str, str]:
        """Get current trace context"""
        context = {}
        if HAS_OTEL and self.tracer:
            span = trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                context['trace_id'] = format(ctx.trace_id, '032x')
                context['span_id'] = format(ctx.span_id, '016x')
        return context

    def _format_extra(self, **kwargs) -> Dict[str, Any]:
        """Format extra fields for logging"""
        extra = {
            'service': self.service_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        extra.update(self._get_trace_context())
        extra.update(kwargs)
        return {'extra': extra}

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **self._format_extra(**kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **self._format_extra(**kwargs))

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['exception_type'] = type(exception).__name__
        self.logger.error(message, exc_info=exception is not None, **self._format_extra(**kwargs))

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **self._format_extra(**kwargs))

    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a tracing span"""
        if self.tracer:
            return self.tracer.start_as_current_span(name, attributes=attributes or {})
        # Return a no-op context manager if no tracer
        from contextlib import nullcontext
        return nullcontext()


# Logger cache
_loggers: Dict[str, OtelLogger] = {}

def get_logger(service_name: str, version: str = "2.0.0") -> OtelLogger:
    """Get or create a logger for a service"""
    if service_name not in _loggers:
        _loggers[service_name] = OtelLogger(service_name, version)
    return _loggers[service_name]
