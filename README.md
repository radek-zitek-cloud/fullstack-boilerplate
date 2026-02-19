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
└── README.md
```

## 🛠️ Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

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

## 📝 License

MIT
