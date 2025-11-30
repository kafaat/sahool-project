# Contributing to Sahool

Thank you for your interest in contributing to Sahool! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kafaat/sahool-project.git
   cd sahool-project
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **For local development of a specific service**
   ```bash
   cd multi-repo/<service-name>/multi-repo/<service-name>
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

## Code Style

### Python

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `black` for formatting:
  ```bash
  pip install black
  black .
  ```
- Use `ruff` for linting:
  ```bash
  pip install ruff
  ruff check .
  ```

### TypeScript/JavaScript

- Follow the existing code style
- Use ESLint for linting
- Use Prettier for formatting

## Testing

### Running Tests

```bash
# For Python services
cd multi-repo/<service-name>/multi-repo/<service-name>
pytest

# For the web frontend
cd web
npm test
```

### Writing Tests

- Write unit tests for all new functions
- Write integration tests for API endpoints
- Aim for >80% code coverage

## Commit Messages

Follow the Conventional Commits specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```
feat: add NDVI calculation for Sentinel-2 imagery

- Implement vectorized NDVI computation
- Add support for cloud masking
- Include unit tests
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black --check .
   ruff check .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure all CI checks pass

## Project Structure

```
sahool-project/
├── multi-repo/              # Microservices
│   ├── geo-core/           # Geographic data service
│   ├── weather-core/       # Weather data service
│   ├── imagery-core/       # Satellite imagery service
│   ├── agent-ai/           # AI assistant service
│   └── ...
├── web/                    # Next.js frontend
├── tests/                  # Integration tests
├── helm/                   # Kubernetes deployment
└── scripts/                # Utility scripts
```

## Adding a New Service

1. Create service directory structure:
   ```bash
   mkdir -p multi-repo/new-service/multi-repo/new-service/app
   ```

2. Add required files:
   - `app/main.py` - FastAPI application
   - `app/api/routes/` - API endpoints
   - `app/models/` - Database models
   - `app/schemas/` - Pydantic schemas
   - `Dockerfile` - Container definition
   - `requirements.txt` - Python dependencies

3. Update `docker-compose.enterprise.yml`

4. Add tests in `tests/new-service/`

## Need Help?

- 📖 Check the [README](README.md) and [README_ENTERPRISE](README_ENTERPRISE.md)
- 🐛 Report bugs via [GitHub Issues](https://github.com/kafaat/sahool-project/issues)
- 💬 Ask questions in [Discussions](https://github.com/kafaat/sahool-project/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
