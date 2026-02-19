# Full-Stack Boilerplate

A production-ready full-stack application boilerplate with FastAPI backend, React frontend, and comprehensive testing.

## 🚀 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **Background Jobs**: Celery + Redis
- **Email**: FastAPI-Mail with SMTP
- **Testing**: pytest

### Frontend
- **Build Tool**: Vite
- **Framework**: React + TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (all components)
- **State Management**: React Query + Zustand
- **Routing**: React Router
- **Testing**: Vitest + Playwright

### DevOps
- **Containerization**: Docker + Docker Compose
- **Hot Reload**: Both Docker and local dev workflows

## 📁 Project Structure

```
fullstack-boilerplate/
├── frontend/           # Vite + React + TypeScript
│   ├── src/
│   ├── tests/
│   └── package.json
├── backend/            # FastAPI + SQLAlchemy
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── data/               # SQLite database storage
├── uploads/            # User uploaded files
├── docker-compose.yml
├── Dockerfile.frontend
├── Dockerfile.backend
├── Makefile           # Build automation & versioning
└── README.md
```

## 🛠️ Quick Start (Using Makefile)

```bash
# First time setup
make setup

# Start with Docker (recommended)
make up-d

# Or start locally for development
make backend   # Terminal 1
make frontend  # Terminal 2
```

### Makefile Commands

Run `make` or `make help` to see all available commands.

**Docker Operations:**
```bash
make build          # Build Docker images with version tags
make up             # Start all services
make up-d           # Start services in detached mode
make down           # Stop services
make logs           # View all logs
make logs-backend   # View backend logs only
```

**Local Development:**
```bash
make backend        # Start backend (uv run)
make frontend       # Start frontend (npm run dev)
make backend-deps   # Install backend dependencies
make frontend-deps  # Install frontend dependencies
```

**Database:**
```bash
make db-init                    # Initialize database with admin user
make db-migrate                 # Run migrations
make db-migration MESSAGE="..." # Create new migration
make db-downgrade               # Downgrade one revision
```

**Testing:**
```bash
make test-backend   # Run pytest
make test-frontend  # Run Vitest
make test-e2e       # Run Playwright
```

### Option 2: Manual Docker Compose

```bash
# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 3: Manual Local Development

**Backend:**
```bash
cd backend
uv sync                    # Install dependencies
uv run alembic upgrade head # Run migrations
uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Environment Variables

Copy `.env.example` files and configure:

**Backend** (`backend/.env`):
```env
DATABASE_URL=sqlite+aiosqlite:///./app.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days
REFRESH_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

**Frontend** (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## 🧪 Testing

**Backend Tests:**
```bash
cd backend
pytest
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

**E2E Tests:**
```bash
cd e2e
npx playwright test
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ✨ Features

- ✅ JWT Authentication (register/login/refresh)
- ✅ Full CRUD operations (Tasks example)
- ✅ File upload handling
- ✅ Admin dashboard with role-based access
- ✅ Email integration
- ✅ Background jobs with Celery
- ✅ Comprehensive test coverage
- ✅ Hot reload in development
- ✅ API documentation (OpenAPI/Swagger)

## 🏷️ Semantic Versioning & Releases

This project uses [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH).

### Versioning Workflow

**1. Check current version:**
```bash
make version
# Output: Current version: v1.2.3-5-gabc1234
```

**2. Create a new release tag:**
```bash
# For a patch release (bug fixes)
make tag VERSION=1.2.4

# For a minor release (new features, backwards compatible)
make tag VERSION=1.3.0

# For a major release (breaking changes)
make tag VERSION=2.0.0
```

**3. Build and push release images:**
```bash
# Set your container registry (defaults to ghcr.io/username)
export REGISTRY=ghcr.io/myusername

# Build and push images with version tags
make release
```

This will:
- Build Docker images tagged with version (e.g., `v1.2.4`) and `latest`
- Push to your container registry

### Version Tag Format

- **Git tags**: `v1.2.3` (always prefix with 'v')
- **Docker tags**: `1.2.3` and `latest`
- **Full image name**: `ghcr.io/username/fullstack-boilerplate-backend:1.2.3`

### Docker Image Tags

Images are automatically tagged with:
- `fullstack-boilerplate-backend:1.2.3` - Specific version
- `fullstack-boilerplate-backend:latest` - Always latest
- `fullstack-boilerplate-frontend:1.2.3` - Specific version
- `fullstack-boilerplate-frontend:latest` - Always latest

### Automated Version Detection

The Makefile automatically detects the version from git tags:
- If on a tag (e.g., `v1.2.3`): Uses `1.2.3`
- If between tags: Uses `1.2.3-5-gabc1234` (5 commits since v1.2.3)
- If no tags: Uses `0.0.0-dev`

## 📝 License

MIT
