#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 11: CI/CD - GitHub Actions Workflows
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء ملفات CI/CD..."

# ─────────────────────────────────────────────────────────────────────────────
# GitHub Actions Directory Structure
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p "$PROJECT_NAME/.github/workflows"
mkdir -p "$PROJECT_NAME/.github/ISSUE_TEMPLATE"

# ─────────────────────────────────────────────────────────────────────────────
# CI Workflow - Tests & Linting
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/workflows/ci.yml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Continuous Integration
# ═══════════════════════════════════════════════════════════════════════════════

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: test_db
  REDIS_URL: redis://localhost:6379/0

jobs:
  # ─────────────────────────────────────────────────────────────────────────────
  # Backend Tests
  # ─────────────────────────────────────────────────────────────────────────────
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_USER: ${{ env.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
          POSTGRES_DB: ${{ env.POSTGRES_DB }}
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
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run linting
        working-directory: ./backend
        run: |
          pip install ruff
          ruff check app/

      - name: Run type checking
        working-directory: ./backend
        run: |
          pip install mypy types-redis
          mypy app/ --ignore-missing-imports

      - name: Run tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql+asyncpg://${{ env.POSTGRES_USER }}:${{ env.POSTGRES_PASSWORD }}@localhost:5432/${{ env.POSTGRES_DB }}
          REDIS_URL: ${{ env.REDIS_URL }}
          SECRET_KEY: test-secret-key
          ENV: testing
        run: |
          pytest -v --cov=app --cov-report=xml --cov-report=html

      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend
          fail_ci_if_error: true

  # ─────────────────────────────────────────────────────────────────────────────
  # Frontend Tests
  # ─────────────────────────────────────────────────────────────────────────────
  frontend-test:
    name: Frontend Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: './frontend/package-lock.json'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run linting
        working-directory: ./frontend
        run: npm run lint

      - name: Run type checking
        working-directory: ./frontend
        run: npm run type-check

      - name: Run tests
        working-directory: ./frontend
        run: npm run test -- --coverage --watchAll=false

      - name: Build
        working-directory: ./frontend
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: ./frontend/dist

  # ─────────────────────────────────────────────────────────────────────────────
  # Security Scan
  # ─────────────────────────────────────────────────────────────────────────────
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          ignore-unfixed: true
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Python security check
        working-directory: ./backend
        run: |
          pip install bandit safety
          bandit -r app/ -f json -o bandit-report.json || true
          safety check -r requirements.txt --json > safety-report.json || true

  # ─────────────────────────────────────────────────────────────────────────────
  # Build Docker Images (on main branch only)
  # ─────────────────────────────────────────────────────────────────────────────
  build-images:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test, security-scan]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for Backend
        id: meta-backend
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/backend
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push Backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta-backend.outputs.tags }}
          labels: ${{ steps.meta-backend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Extract metadata for Frontend
        id: meta-frontend
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/frontend
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push Frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta-frontend.outputs.tags }}
          labels: ${{ steps.meta-frontend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
EOF

# ─────────────────────────────────────────────────────────────────────────────
# CD Workflow - Deployment
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/workflows/cd.yml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Continuous Deployment
# ═══════════════════════════════════════════════════════════════════════════════

name: CD

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

env:
  DOCKER_REGISTRY: ghcr.io/${{ github.repository }}

jobs:
  # ─────────────────────────────────────────────────────────────────────────────
  # Deploy to Staging
  # ─────────────────────────────────────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: staging
      url: https://staging.field-suite.example.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Deploy to Kubernetes
        run: |
          export KUBECONFIG=kubeconfig
          kubectl apply -k k8s/overlays/staging
          kubectl rollout status deployment/field-suite-backend -n field-suite
          kubectl rollout status deployment/field-suite-frontend -n field-suite

      - name: Run smoke tests
        run: |
          sleep 30
          curl -f https://staging.field-suite.example.com/health || exit 1

      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          fields: repo,message,commit,author,action,eventName,ref,workflow
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  # ─────────────────────────────────────────────────────────────────────────────
  # Deploy to Production
  # ─────────────────────────────────────────────────────────────────────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v') || (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'production')
    environment:
      name: production
      url: https://field-suite.example.com
    needs: [deploy-staging]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG_PRODUCTION }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Create backup
        run: |
          export KUBECONFIG=kubeconfig
          kubectl exec -n field-suite deployment/field-suite-postgres -- pg_dump -U postgres field_suite_db > backup-$(date +%Y%m%d-%H%M%S).sql

      - name: Deploy to Kubernetes
        run: |
          export KUBECONFIG=kubeconfig
          kubectl apply -k k8s/overlays/production
          kubectl rollout status deployment/field-suite-backend -n field-suite --timeout=300s
          kubectl rollout status deployment/field-suite-frontend -n field-suite --timeout=300s

      - name: Run smoke tests
        run: |
          sleep 30
          curl -f https://field-suite.example.com/health || exit 1

      - name: Create GitHub Release
        if: startsWith(github.ref, 'refs/tags/v')
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          fields: repo,message,commit,author,action,eventName,ref,workflow
          text: 'Production deployment ${{ job.status }}'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Release Workflow
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/workflows/release.yml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Release Workflow
# ═══════════════════════════════════════════════════════════════════════════════

name: Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 1.0.0)'
        required: true
      release_type:
        description: 'Release type'
        required: true
        default: 'minor'
        type: choice
        options:
          - patch
          - minor
          - major

permissions:
  contents: write
  packages: write

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Update version in files
        run: |
          VERSION="${{ github.event.inputs.version }}"

          # Update backend version
          sed -i "s/APP_VERSION: str = \".*\"/APP_VERSION: str = \"$VERSION\"/" backend/app/core/config.py

          # Update frontend version
          npm --prefix frontend version $VERSION --no-git-tag-version

          # Commit changes
          git add .
          git commit -m "chore: bump version to $VERSION"

      - name: Create and push tag
        run: |
          VERSION="${{ github.event.inputs.version }}"
          git tag -a "v$VERSION" -m "Release v$VERSION"
          git push origin main --follow-tags

      - name: Generate changelog
        id: changelog
        uses: mikepenz/release-changelog-builder-action@v4
        with:
          configuration: ".github/changelog-config.json"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ github.event.inputs.version }}
          name: Release v${{ github.event.inputs.version }}
          body: ${{ steps.changelog.outputs.changelog }}
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Dependabot Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/dependabot.yml" << 'EOF'
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore(deps)"

  # NPM dependencies
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "javascript"
    commit-message:
      prefix: "chore(deps)"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "chore(deps)"

  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/backend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"
    commit-message:
      prefix: "chore(deps)"

  - package-ecosystem: "docker"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"
    commit-message:
      prefix: "chore(deps)"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# CodeQL Analysis
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/workflows/codeql.yml" << 'EOF'
name: CodeQL Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ['python', 'javascript']

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended

      - name: Autobuild
        uses: github/codeql-action/autobuild@v2

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2
        with:
          category: "/language:${{ matrix.language }}"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# PR Template
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/pull_request_template.md" << 'EOF'
## Description

<!-- Describe your changes in detail -->

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Configuration change
- [ ] ♻️ Refactoring (no functional changes)

## Related Issues

<!-- Link any related issues here using #issue_number -->

Fixes #

## Testing

<!-- Describe the tests you ran -->

- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Manual testing completed

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Issue Templates
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/ISSUE_TEMPLATE/bug_report.md" << 'EOF'
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## Bug Description

<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior

<!-- A clear and concise description of what you expected to happen -->

## Actual Behavior

<!-- What actually happened -->

## Screenshots

<!-- If applicable, add screenshots to help explain your problem -->

## Environment

- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 2.0.0]

## Additional Context

<!-- Add any other context about the problem here -->
EOF

cat > "$PROJECT_NAME/.github/ISSUE_TEMPLATE/feature_request.md" << 'EOF'
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: 'enhancement'
assignees: ''
---

## Feature Description

<!-- A clear and concise description of the feature -->

## Problem it Solves

<!-- What problem does this feature solve? -->

## Proposed Solution

<!-- Describe the solution you'd like -->

## Alternatives Considered

<!-- Describe any alternative solutions or features you've considered -->

## Additional Context

<!-- Add any other context or screenshots about the feature request here -->
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Changelog Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.github/changelog-config.json" << 'EOF'
{
  "categories": [
    {
      "title": "## 🚀 Features",
      "labels": ["feature", "enhancement"]
    },
    {
      "title": "## 🐛 Bug Fixes",
      "labels": ["bug", "fix"]
    },
    {
      "title": "## 📝 Documentation",
      "labels": ["documentation"]
    },
    {
      "title": "## 🔧 Maintenance",
      "labels": ["chore", "dependencies"]
    },
    {
      "title": "## 🔒 Security",
      "labels": ["security"]
    }
  ],
  "sort": "ASC",
  "template": "${{CHANGELOG}}\n\n**Full Changelog**: ${{RELEASE_DIFF}}",
  "pr_template": "- ${{TITLE}} (#${{NUMBER}}) by @${{AUTHOR}}",
  "empty_template": "No changes",
  "transformers": [],
  "max_tags_to_fetch": 200,
  "max_pull_requests": 200,
  "max_back_track_time_days": 90
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Git Configuration Files
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.gitignore" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Git Ignore
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────────────────────
.env
.env.local
.env.*.local
.env.production
*.env

# ─────────────────────────────────────────────────────────────────────────────
# Python
# ─────────────────────────────────────────────────────────────────────────────
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# ─────────────────────────────────────────────────────────────────────────────
# Node.js
# ─────────────────────────────────────────────────────────────────────────────
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# ─────────────────────────────────────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────────────────────────────────────
/frontend/dist/
/frontend/build/
*.local

# ─────────────────────────────────────────────────────────────────────────────
# IDE
# ─────────────────────────────────────────────────────────────────────────────
.idea/
.vscode/
*.swp
*.swo
*~
.project
.classpath
.settings/

# ─────────────────────────────────────────────────────────────────────────────
# OS
# ─────────────────────────────────────────────────────────────────────────────
.DS_Store
Thumbs.db
*.log

# ─────────────────────────────────────────────────────────────────────────────
# Docker
# ─────────────────────────────────────────────────────────────────────────────
docker-compose.override.yml

# ─────────────────────────────────────────────────────────────────────────────
# Kubernetes
# ─────────────────────────────────────────────────────────────────────────────
kubeconfig
*.kubeconfig

# ─────────────────────────────────────────────────────────────────────────────
# Uploads & Data
# ─────────────────────────────────────────────────────────────────────────────
/uploads/
/tmp/
*.tif
*.tiff
*.jp2

# ─────────────────────────────────────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────────────────────────────────────
coverage/
*.xml
*.json
!package.json
!package-lock.json
!tsconfig.json
EOF

cat > "$PROJECT_NAME/.editorconfig" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Editor Configuration
# ═══════════════════════════════════════════════════════════════════════════════

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Pre-commit Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/.pre-commit-config.yaml" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Pre-commit Configuration
# ═══════════════════════════════════════════════════════════════════════════════

repos:
  # General
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-redis
          - pydantic

  # JavaScript/TypeScript
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@8.56.0
          - eslint-config-prettier@9.1.0
          - '@typescript-eslint/parser@6.18.0'
          - '@typescript-eslint/eslint-plugin@6.18.0'

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        types_or: [css, javascript, jsx, ts, tsx, json, yaml]

  # Docker
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker
        args: ['--ignore', 'DL3008', '--ignore', 'DL3013']

  # Security
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Alembic Configuration
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p "$PROJECT_NAME/backend/alembic/versions"

cat > "$PROJECT_NAME/backend/alembic.ini" << 'EOF'
# ═══════════════════════════════════════════════════════════════════════════════
# Field Suite Pro - Alembic Configuration
# ═══════════════════════════════════════════════════════════════════════════════

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

cat > "$PROJECT_NAME/backend/alembic/env.py" << 'EOF'
"""
Alembic Environment Configuration
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.core.database import Base

# Import all models to register them with SQLAlchemy
from app.models import user, field, ndvi, advisor  # noqa

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

cat > "$PROJECT_NAME/backend/alembic/script.py.mako" << 'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# README
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/README.md" << 'EOF'
# Field Suite Pro 🌾

نظام إدارة الحقول الزراعية المتقدم - Advanced Agricultural Field Management System

![CI](https://github.com/your-org/field-suite-pro/workflows/CI/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node](https://img.shields.io/badge/node-20+-green.svg)

## 🚀 Features

- **Field Management**: Create, update, and monitor agricultural fields with GIS support
- **NDVI Analysis**: Real-time vegetation health monitoring using satellite imagery
- **Smart Advisor**: AI-powered recommendations for irrigation, fertilization, and pest control
- **Real-time Alerts**: WebSocket-based notifications for critical events
- **Multi-language**: Full Arabic and English support
- **PWA Ready**: Install as a mobile app

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL with PostGIS
- Redis

## 🛠️ Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/field-suite-pro.git
cd field-suite-pro

# Copy environment file
cp .env.example .env

# Start development environment
make dev

# Run database migrations
make migrate
```

## 🏗️ Architecture

```
field-suite-pro/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Core configuration
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── tasks/     # Celery tasks
│   └── tests/         # Test suite
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── stores/
│   └── public/
├── k8s/               # Kubernetes manifests
├── monitoring/        # Prometheus & Grafana
└── docker-compose.yml
```

## 📚 API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
# Run all tests
make test

# Run backend tests only
cd backend && pytest -v

# Run frontend tests only
cd frontend && npm test
```

## 📦 Deployment

### Docker

```bash
# Build images
make build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -k k8s/overlays/production
```

## 🔐 Security

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Rate limiting
- Input validation
- SQL injection protection
- XSS protection

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

- Documentation: https://docs.field-suite.example.com
- Issues: https://github.com/your-org/field-suite-pro/issues
EOF

log_success "تم إنشاء ملفات CI/CD"
