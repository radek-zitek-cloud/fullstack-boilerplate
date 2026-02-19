# Suggested Commands - Full-Stack Boilerplate

## Quick Start

```bash
# First time setup
make setup

# Start with Docker (recommended)
make up-d

# Or start locally for development
make backend   # Terminal 1
make frontend  # Terminal 2
```

## Essential Commands

### Docker Operations
```bash
make build          # Build Docker images
make up             # Start services
make up-d           # Start in detached mode
make down           # Stop services
make logs           # View all logs
make logs-backend   # View backend container logs
```

### Local Development
```bash
make backend        # Start backend (uv run uvicorn)
make frontend       # Start frontend (npm run dev)
make backend-deps   # Install Python dependencies
make frontend-deps  # Install npm dependencies
```

### Logging
```bash
make logs-app       # View application logs
make logs-error     # View error logs
make logs-access    # View access logs
make grep-logs      # Search for errors
```

### Database
```bash
make db-init                    # Initialize database
make db-migrate                 # Run migrations
make db-migration MESSAGE="..." # Create migration
```

### Testing & Quality
```bash
make test-backend   # Run pytest
make test-frontend  # Run Vitest
make format         # Format Python code
make lint           # Lint Python code
```

### System Utilities
```bash
cd backend          # Navigate to backend
cd frontend         # Navigate to frontend
git add .           # Stage changes
git commit -m "..." # Commit changes
git log             # View commit history
grep -r "pattern"   # Search codebase
find . -name "*.py" # Find files
```
