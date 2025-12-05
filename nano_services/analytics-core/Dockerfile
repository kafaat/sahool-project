FROM python:3.11-slim

LABEL maintainer="Sahool Yemen <dev@sahool.ye>"
LABEL description="Analytics Core Service - سهول اليمن"

WORKDIR /app

# Install shared library first
COPY libs-shared ./libs-shared
RUN pip install --no-cache-dir ./libs-shared

# Install service dependencies
COPY nano_services/analytics-core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY nano_services/analytics-core/app ./app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
