.PHONY: help install dev up down logs test clean format lint

help:
@echo "Sahool Project - Available Commands:"
@echo "  make install    - Install all dependencies"
@echo "  make dev        - Start development environment"
@echo "  make up         - Start all services with Docker Compose"
@echo "  make down       - Stop all services"
@echo "  make logs       - View logs from all services"
@echo "  make test       - Run all tests"
@echo "  make clean      - Clean up temporary files"
@echo "  make format     - Format code with black"
@echo "  make lint       - Run linters (ruff)"

install:
@echo "Installing Python dependencies..."
pip install black ruff pytest
@echo "Installing web dependencies..."
cd web && npm install

dev:
@echo "Starting development environment..."
docker-compose up postgres redis minio -d
@echo "Services started. Run individual services manually."

up:
@echo "Starting all services..."
docker-compose -f docker-compose.enterprise.yml up -d

down:
@echo "Stopping all services..."
docker-compose -f docker-compose.enterprise.yml down

logs:
docker-compose -f docker-compose.enterprise.yml logs -f

test:
@echo "Running tests..."
pytest tests/ -v

clean:
@echo "Cleaning up..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
rm -rf .coverage htmlcov/

format:
@echo "Formatting Python code..."
black multi-repo/*/multi-repo/*/app

lint:
@echo "Running linters..."
ruff check multi-repo/*/multi-repo/*/app
