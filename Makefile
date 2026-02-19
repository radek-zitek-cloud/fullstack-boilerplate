.PHONY: help build up down logs shell backend frontend test clean version release

# Variables
PROJECT_NAME := fullstack-boilerplate
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "0.0.0-dev")
BACKEND_IMAGE := $(PROJECT_NAME)-backend
FRONTEND_IMAGE := $(PROJECT_NAME)-frontend
REGISTRY ?= ghcr.io/username

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

## Show this help message
help:
	@echo "$(BLUE)Full-Stack Boilerplate - Make Targets$(NC)"
	@echo "======================================"
	@echo ""
	@echo "$(GREEN)Docker Operations:$(NC)"
	@echo "  make build          - Build all Docker images with version tag"
	@echo "  make up             - Start all services with docker-compose"
	@echo "  make up-d           - Start all services in detached mode"
	@echo "  make down           - Stop all services"
	@echo "  make down-v         - Stop services and remove volumes"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-frontend  - View frontend logs"
	@echo ""
	@echo "$(GREEN)Local Development:$(NC)"
	@echo "  make backend        - Start backend locally (uv run)"
	@echo "  make frontend       - Start frontend locally (npm run dev)"
	@echo "  make backend-deps   - Install/update backend dependencies"
	@echo "  make frontend-deps  - Install/update frontend dependencies"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-init        - Initialize database and create admin user"
	@echo "  make db-migrate     - Run database migrations"
	@echo "  make db-migration   - Create new migration (MESSAGE=\"...\")"
	@echo "  make db-downgrade   - Downgrade database by one revision"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make test-e2e       - Run end-to-end tests"
	@echo ""
	@echo "$(GREEN)Release & Versioning:$(NC)"
	@echo "  make version        - Show current version"
	@echo "  make tag            - Create and push git tag (VERSION=x.y.z)"
	@echo "  make release        - Build and push Docker images for release"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make clean          - Remove Docker containers, images, and volumes"
	@echo "  make clean-all      - Full cleanup including node_modules and .venv"
	@echo "  make format         - Format backend code (ruff)"
	@echo "  make lint           - Lint backend code"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo ""

## Build Docker images with version tags
build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@echo "$(GREEN)Version: $(VERSION)$(NC)"
	docker build -f Dockerfile.backend -t $(BACKEND_IMAGE):$(VERSION) -t $(BACKEND_IMAGE):latest .
	docker build -f Dockerfile.frontend -t $(FRONTEND_IMAGE):$(VERSION) -t $(FRONTEND_IMAGE):latest .
	@echo "$(GREEN)Build complete!$(NC)"

## Build and tag for registry release
release:
	@echo "$(BLUE)Building release images...$(NC)"
	@echo "$(GREEN)Version: $(VERSION)$(NC)"
	@echo "$(GREEN)Registry: $(REGISTRY)$(NC)"
	docker build -f Dockerfile.backend -t $(REGISTRY)/$(BACKEND_IMAGE):$(VERSION) -t $(REGISTRY)/$(BACKEND_IMAGE):latest .
	docker build -f Dockerfile.frontend -t $(REGISTRY)/$(FRONTEND_IMAGE):$(VERSION) -t $(REGISTRY)/$(FRONTEND_IMAGE):latest .
	@echo "$(GREEN)Pushing images to registry...$(NC)"
	docker push $(REGISTRY)/$(BACKEND_IMAGE):$(VERSION)
	docker push $(REGISTRY)/$(BACKEND_IMAGE):latest
	docker push $(REGISTRY)/$(FRONTEND_IMAGE):$(VERSION)
	docker push $(REGISTRY)/$(FRONTEND_IMAGE):latest
	@echo "$(GREEN)Release complete!$(NC)"

## Show current version
version:
	@echo "$(GREEN)Current version: $(VERSION)$(NC)"

## Create and push git tag (usage: make tag VERSION=1.2.3)
tag:
ifndef VERSION
	@echo "$(RED)Error: VERSION is required$(NC)"
	@echo "Usage: make tag VERSION=1.2.3"
	@exit 1
endif
	@echo "$(BLUE)Creating git tag v$(VERSION)...$(NC)"
	git tag -a v$(VERSION) -m "Release v$(VERSION)"
	git push origin v$(VERSION)
	@echo "$(GREEN)Tag v$(VERSION) created and pushed!$(NC)"
	@echo "$(YELLOW)Run 'make release' to build and push Docker images$(NC)"

## Docker Compose Operations

## Start all services
up: build
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up

## Start all services in detached mode
up-d: build
	@echo "$(BLUE)Starting services in detached mode...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "API Docs: http://localhost:8000/docs"

## Stop all services
down:
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down

## Stop services and remove volumes
down-v:
	@echo "$(RED)Stopping services and removing volumes...$(NC)"
	docker-compose down -v

## View logs from all services
logs:
	docker-compose logs -f

## View backend logs
logs-backend:
	docker-compose logs -f backend

## View frontend logs
logs-frontend:
	docker-compose logs -f frontend

## Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

## Local Development

## Install backend dependencies
backend-deps:
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && uv sync

## Install frontend dependencies
frontend-deps:
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install

## Start backend locally
backend: backend-deps
	@echo "$(BLUE)Starting backend on http://localhost:8000$(NC)"
	cd backend && cp -n .env.example .env || true
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Start frontend locally
frontend: frontend-deps
	@echo "$(BLUE)Starting frontend on http://localhost:5173$(NC)"
	cd frontend && npm run dev

## Database Operations

## Initialize database and create admin user
db-init: backend-deps
	@echo "$(BLUE)Initializing database...$(NC)"
	cd backend && uv run python app/db/init_db.py
	@echo "$(GREEN)Database initialized!$(NC)"

## Run database migrations
db-migrate: backend-deps
	@echo "$(BLUE)Running migrations...$(NC)"
	cd backend && uv run alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

## Create new migration (usage: make db-migration MESSAGE="add users table")
db-migration: backend-deps
ifndef MESSAGE
	@echo "$(RED)Error: MESSAGE is required$(NC)"
	@echo "Usage: make db-migration MESSAGE=\"add users table\""
	@exit 1
endif
	@echo "$(BLUE)Creating migration: $(MESSAGE)...$(NC)"
	cd backend && uv run alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "$(GREEN)Migration created!$(NC)"

## Downgrade database by one revision
db-downgrade: backend-deps
	@echo "$(YELLOW)Downgrading database...$(NC)"
	cd backend && uv run alembic downgrade -1
	@echo "$(GREEN)Downgrade complete!$(NC)"

## Testing

## Run backend tests
test-backend: backend-deps
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd backend && uv run pytest -v

## Run frontend tests
test-frontend: frontend-deps
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd frontend && npm test

## Run end-to-end tests
test-e2e:
	@echo "$(BLUE)Running e2e tests...$(NC)"
	cd e2e && npx playwright test

## Code Quality

## Format backend code
format:
	@echo "$(BLUE)Formatting backend code...$(NC)"
	cd backend && uv run ruff format .
	cd backend && uv run ruff check --fix .

## Lint backend code
lint:
	@echo "$(BLUE)Linting backend code...$(NC)"
	cd backend && uv run ruff check .
	cd backend && uv run mypy .

## Cleanup

## Remove Docker containers, images, and volumes
clean:
	@echo "$(RED)Cleaning up Docker resources...$(NC)"
	docker-compose down -v --remove-orphans
	docker rmi $(BACKEND_IMAGE):$(VERSION) $(BACKEND_IMAGE):latest 2>/dev/null || true
	docker rmi $(FRONTEND_IMAGE):$(VERSION) $(FRONTEND_IMAGE):latest 2>/dev/null || true
	docker system prune -f
	@echo "$(GREEN)Cleanup complete!$(NC)"

## Full cleanup including dependencies
clean-all: clean
	@echo "$(RED)Cleaning up all dependencies...$(NC)"
	rm -rf backend/.venv
	rm -rf frontend/node_modules
	rm -rf data/*.db data/*.sqlite
	rm -rf uploads/*
	@echo "$(GREEN)Full cleanup complete!$(NC)"

## Development Utilities

## Setup project for first time
setup:
	@echo "$(BLUE)Setting up project...$(NC)"
	mkdir -p data uploads
	cp backend/.env.example backend/.env 2>/dev/null || true
	cp frontend/.env.example frontend/.env 2>/dev/null || true
	$(MAKE) backend-deps
	$(MAKE) frontend-deps
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "Run 'make up-d' to start with Docker or 'make backend' and 'make frontend' for local dev"

## Quick start - build and run everything
start:
	$(MAKE) setup
	$(MAKE) up-d
	@echo "$(GREEN)Application is running!$(NC)"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
