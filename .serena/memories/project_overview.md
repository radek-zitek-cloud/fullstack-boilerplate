# Project Overview - Full-Stack Boilerplate

## What is This Project?

A production-ready full-stack application boilerplate that developers can clone and immediately start building upon. It demonstrates best practices for modern web development with a complete tech stack.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **Background Jobs**: Celery + Redis
- **Email**: FastAPI-Mail with SMTP
- **Testing**: pytest with async support

### Frontend
- **Build Tool**: Vite
- **Framework**: React 19 + TypeScript (strict)
- **Styling**: Tailwind CSS 4
- **Components**: shadcn/ui (25+ components)
- **State Management**: React Query + Zustand
- **Routing**: React Router 7
- **Testing**: Vitest + React Testing Library

### DevOps
- **Containerization**: Docker + Docker Compose
- **Versioning**: Semantic versioning with git tags
- **Logging**: Centralized JSON logging
- **CI/CD Ready**: Makefile-based workflows

## Features

- ✅ JWT Authentication (register/login/refresh)
- ✅ Full CRUD operations (Tasks example)
- ✅ File upload handling
- ✅ Admin dashboard
- ✅ Email integration
- ✅ Background jobs with Celery
- ✅ Centralized logging (JSON format)
- ✅ Hot reload in development
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Semantic versioning

## Project Structure

```
fullstack-boilerplate/
├── backend/           # FastAPI + SQLAlchemy
├── frontend/          # React + TypeScript
├── data/              # SQLite database
├── uploads/           # User uploaded files
├── logs/              # Application logs
├── docker-compose.yml
├── Makefile          # Build automation
└── README.md
```

## Key Entry Points

### Backend
- **Main**: `backend/app/main.py`
- **Config**: `backend/app/core/config.py`
- **API routes**: `backend/app/api/api_v1/endpoints/`

### Frontend
- **Main**: `frontend/src/main.tsx`
- **App**: `frontend/src/App.tsx`
- **Pages**: `frontend/src/pages/`

## URLs When Running

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Philosophy

This is a **boilerplate**, not a framework:
- Minimal abstractions
- Clear, readable code
- Best practices demonstrated
- Easy to extend and modify
- Production-ready defaults
