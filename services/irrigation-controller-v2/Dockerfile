FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY services/irrigation-controller-v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared library and install
COPY libs-shared /app/libs-shared
RUN pip install -e /app/libs-shared

# Copy application
COPY services/irrigation-controller-v2/app /app/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
