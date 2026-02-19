# Style and Conventions - Full-Stack Boilerplate

## Project Structure

### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Main code**: `backend/app/`
- **Models**: `backend/app/models/`
- **API routes**: `backend/app/api/api_v1/endpoints/`
- **Core**: `backend/app/core/`
- **Schemas**: `backend/app/schemas/`

### Frontend (TypeScript/React)
- **Location**: `frontend/src/`
- **Components**: `frontend/src/components/`
- **Pages**: `frontend/src/pages/`
- **Contexts**: `frontend/src/contexts/`
- **Lib**: `frontend/src/lib/`

## Backend (Python) Conventions

### Code Style
- **Line length**: 100 characters
- **Python version**: 3.11+
- **Type hints**: REQUIRED (mypy strict mode enabled)
- **Docstrings**: Minimal - only for complex logic

### Import Style
```python
from app.core.logging import get_logger
from app.models.user import User
```

### Naming
- **Functions/variables**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_CASE
- **Private**: _prefixed_with_underscore

### Error Handling
- Use try/except with specific exceptions
- Log errors with context
- Return proper HTTP status codes

### Database
- Use async SQLAlchemy
- Models in `app/models/`
- Pydantic schemas in `app/schemas/`

## Frontend (TypeScript) Conventions

### Code Style
- **TypeScript**: Strict mode enabled
- **Type imports**: Use `type` keyword for type-only imports
- **Components**: Function components with hooks

### Naming
- **Components**: PascalCase
- **Files**: PascalCase for components, camelCase for utils
- **Hooks**: usePascalCase

### Import Paths
- Use `@/` alias for src directory
- Example: `import { Button } from "@/components/ui/button"`

### Component Structure
```typescript
export default function ComponentName() {
  // hooks at top
  // handlers
  // render
}
```

## Git Conventions

### Commit Messages
```
feat: add new feature
fix: fix bug
docs: update documentation
refactor: code refactoring
test: add tests
chore: maintenance
```

### Semantic Versioning
- Use `make tag VERSION=x.y.z` to create releases
- Git tags: `v1.2.3` format
- Docker images tagged with version

## When Task is Complete

1. **Code Quality**:
   ```bash
   make format  # Format code
   make lint    # Check for issues
   ```

2. **Testing** (if applicable):
   ```bash
   make test-backend
   ```

3. **Git**:
   ```bash
   git add .
   git commit -m "feat: description"
   ```

## Design Patterns

### Backend
- **Dependency Injection**: FastAPI Depends()
- **Repository Pattern**: Database operations in models
- **Service Layer**: Business logic in endpoints

### Frontend
- **Context API**: For global state (auth)
- **React Query**: For server state
- **Zustand**: For client state
