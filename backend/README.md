# Backend

FastAPI backend for the full-stack boilerplate.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- uv (Python package manager)

### Installation

```bash
# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

## 🗄️ Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Downgrade
uv run alembic downgrade -1
```

## 📚 API Documentation

When the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 📁 Structure

```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Config, security, database
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   └── main.py       # FastAPI app entry
├── alembic/          # Database migrations
├── tests/            # Test suite
└── pyproject.toml    # Dependencies
```
