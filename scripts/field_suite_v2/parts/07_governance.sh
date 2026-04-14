#!/bin/bash
# ==============================================================================
# Part 07: Governance & CI/CD
# SAHOOL-aligned policies and GitHub Actions
# ==============================================================================

generate_governance() {
    log_info "Creating Governance & CI/CD..."

    mkdir -p governance
    mkdir -p .github/{workflows,ISSUE_TEMPLATE}

    # ------------------------------------------------------------------------------
    # Service Registry
    # ------------------------------------------------------------------------------
    write_heredoc "governance/services.yaml" << 'YAMLEOF'
# ==============================================================================
# Field Suite Platform - Service Registry
# ==============================================================================

version: "1.0"
platform: "field-suite"

services:
  field-service:
    name: "Field Service"
    owner: "platform-team"
    port: 8001
    health_endpoint: "/health"
    dependencies:
      - postgres
      - redis
    sla:
      availability: 99.9
      latency_p99_ms: 200

  ndvi-service:
    name: "NDVI Service"
    owner: "data-team"
    port: 8002
    health_endpoint: "/health"
    dependencies:
      - postgres
      - redis
      - celery
    sla:
      availability: 99.5
      latency_p99_ms: 500
    workers:
      - ndvi-worker

  advisor-service:
    name: "Advisor Service"
    owner: "ai-team"
    port: 8003
    health_endpoint: "/health"
    dependencies:
      - ndvi-service
      - field-service
    sla:
      availability: 99.5
      latency_p99_ms: 300

  gateway:
    name: "API Gateway"
    owner: "platform-team"
    port: 80
    health_endpoint: "/health"
    sla:
      availability: 99.99
      latency_p99_ms: 50
YAMLEOF

    # ------------------------------------------------------------------------------
    # API Standards
    # ------------------------------------------------------------------------------
    write_heredoc "governance/api-standards.md" << 'MDEOF'
# API Standards

## Versioning
- All APIs must use `/api/v1/` prefix
- Breaking changes require new version

## Authentication
- All endpoints require JWT (except /health, /docs)
- Tokens must be passed in Authorization header

## Response Format
```json
{
  "data": {},
  "meta": {
    "timestamp": "ISO8601",
    "request_id": "uuid"
  }
}
```

## Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

## Rate Limits
- Standard: 100 req/s per tenant
- Auth: 10 req/s per IP
- Burst allowed: 50 requests

## Pagination
- Use `page` and `size` query params
- Default: page=1, size=20
- Max size: 100
MDEOF

    # ------------------------------------------------------------------------------
    # Security Policies
    # ------------------------------------------------------------------------------
    write_heredoc "governance/security-policies.yaml" << 'YAMLEOF'
# Security Policies

authentication:
  method: jwt
  algorithm: HS256
  access_token_expiry: 30m
  refresh_token_expiry: 7d

authorization:
  model: rbac
  roles:
    - admin
    - manager
    - operator
    - viewer
  default_role: viewer

secrets:
  storage: environment  # vault in production
  rotation: monthly

network:
  tls: required
  min_tls_version: "1.2"

audit:
  enabled: true
  events:
    - login
    - logout
    - data_access
    - data_modification
YAMLEOF

    # ------------------------------------------------------------------------------
    # GitHub Actions - CI
    # ------------------------------------------------------------------------------
    write_heredoc ".github/workflows/ci.yml" << 'YAMLEOF'
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # Backend Tests
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install shared dependencies
        run: pip install -e ./shared

      - name: Test Field Service
        working-directory: ./services/field-service
        run: |
          pip install -r requirements.txt
          pytest -v --cov=app --cov-report=xml

      - name: Test NDVI Service
        working-directory: ./services/ndvi-service
        run: |
          pip install -r requirements.txt
          pytest -v --cov=app --cov-report=xml

      - name: Test Advisor Service
        working-directory: ./services/advisor-service
        run: |
          pip install -r requirements.txt
          pytest -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          flags: backend

  # Frontend Tests
  frontend-test:
    name: Frontend Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"
          cache-dependency-path: "./frontend/package-lock.json"

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Lint
        working-directory: ./frontend
        run: npm run lint

      - name: Type check
        working-directory: ./frontend
        run: npm run type-check

      - name: Build
        working-directory: ./frontend
        run: npm run build

  # Security Scan
  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          format: "sarif"
          output: "trivy-results.sarif"

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: "trivy-results.sarif"

  # Build Docker Images
  build:
    name: Build Images
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test, security]
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Field Service
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/field-service/Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository }}/field-service:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push NDVI Service
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/ndvi-service/Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository }}/ndvi-service:${{ github.sha }}

      - name: Build and push Advisor Service
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/advisor-service/Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository }}/advisor-service:${{ github.sha }}

      - name: Build and push Frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
YAMLEOF

    # ------------------------------------------------------------------------------
    # GitHub Actions - CD
    # ------------------------------------------------------------------------------
    write_heredoc ".github/workflows/cd.yml" << 'YAMLEOF'
name: CD

on:
  push:
    branches: [main]
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      environment:
        description: "Environment"
        required: true
        default: "staging"
        type: choice
        options:
          - staging
          - production

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: staging
      url: https://staging.field-suite.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        run: |
          echo "Deploying to staging..."
          # kubectl apply -k k8s/overlays/staging

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://field-suite.example.com
    needs: [deploy-staging]

    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        run: |
          echo "Deploying to production..."
          # kubectl apply -k k8s/overlays/production
YAMLEOF

    # ------------------------------------------------------------------------------
    # Dependabot
    # ------------------------------------------------------------------------------
    write_heredoc ".github/dependabot.yml" << 'YAMLEOF'
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/services/field-service"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "python"

  - package-ecosystem: "pip"
    directory: "/services/ndvi-service"
    schedule:
      interval: "weekly"

  - package-ecosystem: "pip"
    directory: "/services/advisor-service"
    schedule:
      interval: "weekly"

  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "javascript"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
YAMLEOF

    # ------------------------------------------------------------------------------
    # PR Template
    # ------------------------------------------------------------------------------
    write_heredoc ".github/pull_request_template.md" << 'MDEOF'
## Description

<!-- What does this PR do? -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review done
- [ ] Tests added
- [ ] Docs updated (if needed)
MDEOF

    # ------------------------------------------------------------------------------
    # Issue Templates
    # ------------------------------------------------------------------------------
    write_heredoc ".github/ISSUE_TEMPLATE/bug_report.md" << 'MDEOF'
---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
---

## Description

## Steps to Reproduce

1.
2.
3.

## Expected Behavior

## Actual Behavior

## Environment

- Service:
- Version:
MDEOF

    write_heredoc ".github/ISSUE_TEMPLATE/feature_request.md" << 'MDEOF'
---
name: Feature Request
about: Suggest a feature
title: "[FEATURE] "
labels: enhancement
---

## Description

## Use Case

## Proposed Solution
MDEOF

    log_success "Governance & CI/CD created"
}
