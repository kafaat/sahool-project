FROM python:3.11-slim

LABEL maintainer="Sahool Yemen <dev@sahool.ye>"
LABEL description="Query Core Service - سهول اليمن"

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared library first
COPY libs-shared ./libs-shared
# NOTE: The Docker build context MUST be set to the project root so that 'libs-shared' is available.
COPY libs-shared ./libs-shared
# Fail early if libs-shared is missing
RUN test -d ./libs-shared || (echo "ERROR: 'libs-shared' directory not found in build context. Please set build context to project root." && exit 1)
RUN pip install --no-cache-dir ./libs-shared

# Install service dependencies
COPY nano_services/query-core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY nano_services/query-core/app ./app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
