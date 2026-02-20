# PROJECT KNOWLEDGE BASE

FastAPI + React full-stack boilerplate with JWT auth, async SQLAlchemy, shadcn/ui.

## STRUCTURE

```
fullstack-boilerplate/
├── frontend/           # Vite + React 19 + TypeScript + Tailwind v4
│   ├── src/
│   │   ├── components/ui/  # shadcn/ui components (25 files)
│   │   ├── pages/          # Route pages (Login, Dashboard, etc.)
│   │   ├── contexts/       # AuthContext, ThemeContext
│   │   ├── hooks/          # Custom React hooks
│   │   └── lib/utils.ts    # cn() for Tailwind
│   └── package.json
├── backend/            # FastAPI + SQLAlchemy 2.0 (async)
│   ├── app/
│   │   ├── api/api_v1/     # API routes (/api/v1 prefix)
│   │   ├── core/           # Config, security, logging, db
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic v2 schemas
│   │   └── services/       # Business logic
│   └── tests/
└── Makefile           # Build automation
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `backend/app/api/api_v1/endpoints/` | Use existing routers as template |
| Add SQLAlchemy model | `backend/app/models/` | Inherit from `base.py`, use Mapped[] types |
| Add Pydantic schema | `backend/app/schemas/` | v2 style, ConfigDict not class Config |
| Add React component | `frontend/src/components/` | UI components go in `ui/` subdir |
| Add route page | `frontend/src/pages/` | Default export, use `useAuth()` for auth |
| Add custom hook | `frontend/src/hooks/` | Prefix with `use`, camelCase |
| Core config | `backend/app/core/config.py` | Pydantic-settings, env vars |
| Security utils | `backend/app/core/security.py` | JWT, password hashing |

## COMMANDS

```bash
# Dev servers
make backend      # http://localhost:8000
make frontend     # http://localhost:5173

# Testing
make test-backend              # pytest -v
uv run pytest tests/test_auth.py::test_login -v  # single test
make test-frontend             # vitest
npm test -- Button.test.tsx    # single test file

# Code quality
make format       # ruff format + check --fix
make lint         # ruff check + mypy
cd frontend && npm run lint    # ESLint

# Database
make db-migrate                    # alembic upgrade head (manual)
make db-migration MESSAGE="..."    # create migration
# Note: Migrations auto-run on startup by default (AUTO_MIGRATE=true)
```

## Code Style Guidelines

### TypeScript / React

- **Path Alias**: Use `@/` for imports from `src/` (e.g., `import { Button } from "@/components/ui/button"`)
- **Imports**: Group: 1) React/libs, 2) Components, 3) Hooks/contexts, 4) Utils
- **Components**: PascalCase, default exports for pages, named for UI components
- **Hooks**: camelCase starting with `use` (e.g., `useAuth`)
- **Types**: Use strict TypeScript with `noUnusedLocals: true`
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Components**: All UI components in `@/components/ui/` (shadcn/ui pattern)
- **Formatting**: Use double quotes, semicolons, 2-space indent
- **⚠️ CRITICAL**: Always use `import type` when importing interfaces or type aliases to avoid Vite HMR issues:
  ```typescript
  // ❌ Wrong - causes "does not provide an export named" error
  import { auditApi, AuditLog } from "@/services/audit";
  
  // ✅ Correct
  import { auditApi, type AuditLog } from "@/services/audit";
  ```

### Python / FastAPI

- **Line Length**: 100 characters (Ruff config)
- **Python Version**: 3.11+
- **Type Hints**: Required for all function signatures (`disallow_untyped_defs = true`)
- **Async**: Use async/await for database operations
- **Imports**: Group: 1) stdlib, 2) third-party, 3) local app imports
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Models**: SQLAlchemy 2.0 style with type annotations
- **Schemas**: Pydantic v2 models
- **Logging**: Use structured JSON logging via `app.core.logging.get_logger(__name__)`

### Import Patterns

**Frontend (TypeScript):**
```typescript
// React/Third-party
import { useState } from "react";
import { Link } from "react-router-dom";

// UI Components (shadcn/ui)
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// App Components
import { Layout } from "@/components/Layout";

// Hooks/Contexts
import { useAuth } from "@/contexts/AuthContext";

// Utils - use 'import type' for interfaces/type aliases
import { cn } from "@/lib/utils";
import { auditApi, type AuditLog } from "@/services/audit";
```

**Backend (Python):**
```python
# Standard library
from contextlib import asynccontextmanager

# Third-party
from fastapi import FastAPI
from sqlalchemy import select

# Local app
from app.core.config import get_settings
from app.models.user import User
from app.schemas.user import UserCreate
```

## Testing Guidelines

**Backend:**
- Use pytest with async support (`pytest-asyncio`)
- Test files: `tests/test_*.py`
- Use factories (factory-boy) for test data
- Run single test: `uv run pytest tests/test_auth.py::test_login -v`

**Frontend:**
- Use Vitest for unit tests
- Use Playwright for E2E tests (in `e2e/` directory)
- Test files: `*.test.tsx` alongside components or in `tests/`
- Run single test: `npm test -- Button.test.tsx`

## Error Handling

**Frontend:**
- Use ErrorBoundary component for React errors
- Use sonner for toast notifications
- Handle async errors with try/catch

**Backend:**
- Use FastAPI exception handlers
- Log errors with structured JSON via `get_logger(__name__)`
- Return consistent error responses: `{"detail": "Error message"}`

**Debugging & Monitoring:**
- **Backend logs**: Check `backend/logs/` directory for detailed error logs and application events
  - `app.log` - Application logs
  - `access.log` - HTTP request logs
  - `error.log` - Error-specific logs
- **Console output**: Backend logs to stdout/stderr during development
- **Frontend errors**: Check browser console and Network tab for API issues

## Key Conventions

- Never use `as any` or `@ts-ignore` in TypeScript
- Always use explicit return types in Python
- Use React Query for server state management
- Use Zustand for client state
- All database operations must be async with SQLAlchemy 2.0
- API routes use prefix `/api/v1`

## Database Migrations

The backend automatically checks and runs Alembic migrations on startup:

- **Default behavior**: Migrations run automatically when `AUTO_MIGRATE=true` (default in .env)
- **Development**: Set `AUTO_MIGRATE=false` when using `uvicorn --reload` to avoid conflicts
- **First startup**: Migrations will create/update the database schema automatically
- **Docker**: Auto-migration is enabled by default in containerized environments

**Environment variables:**
```bash
AUTO_MIGRATE=true   # Enable automatic migrations on startup
ENVIRONMENT=development  # development, staging, production
```

## RBAC (Role-Based Access Control)

The system implements a comprehensive RBAC system with hierarchical permissions and component-scoped roles.

### Architecture

**Key Features:**
- **Component-scoped roles**: Each role belongs to a specific component (e.g., "tasks", "users")
- **Hierarchical permissions**: Users can have managers/subordinates forming a tree
- **Permission union**: Multiple roles per user with union of permissions
- **Four permission levels**:
  - `"own"` - Only own resources
  - `"subordinates"` - Own + subordinates' resources
  - `"all"` - All resources in component
  - `null` - No access

### Backend Implementation

**Models:**
- `app/models/role.py` - Role definition with permissions JSON
- `app/models/user_role.py` - User-role assignments
- `app/models/user.py` - Extended with manager_id and subordinates

**Core Services:**
- `app/services/rbac.py` - `check_permission()`, `get_user_permissions()`, `is_in_hierarchy()`

**API Endpoints** (Admin only):
- `GET /api/v1/admin/rbac/roles` - List all roles
- `POST /api/v1/admin/rbac/roles` - Create role
- `PUT /api/v1/admin/rbac/roles/{id}` - Update role
- `DELETE /api/v1/admin/rbac/roles/{id}` - Delete role
- `GET /api/v1/admin/rbac/users/{id}/roles` - Get user's roles
- `POST /api/v1/admin/rbac/users/{id}/roles` - Assign role to user
- `DELETE /api/v1/admin/rbac/users/{id}/roles/{role_id}` - Remove role from user
- `PUT /api/v1/admin/rbac/users/{id}/manager` - Set user's manager
- `GET /api/v1/admin/rbac/hierarchy/{id}` - View user hierarchy
- `GET /api/v1/admin/rbac/users` - List all users with roles

**Checking Permissions in Endpoints:**
```python
from app.core.permissions import require_permission
from app.services.rbac import check_permission

# Using dependency (returns 403 if no access)
@router.post("/tasks")
async def create_task(
    current_user = Depends(require_permission("tasks", "create")),
    # ...
):
    pass

# Manual check with ownership
async def update_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task(db, task_id)
    has_access = await check_permission(
        db, current_user.id, "tasks", "update", task.user_id
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Default Roles:**
Run `uv run python scripts/seed_roles.py` to create default roles:
- `tasks:user` - CRUD on own tasks
- `tasks:manager` - CRUD on own + subordinates' tasks
- `tasks:admin` - Full CRUD on all tasks

### Frontend Implementation

**Hooks:**
- `src/hooks/usePermission.ts` - Check permissions in components

**Components:**
- `src/components/PermissionGuard.tsx` - Conditional rendering based on permissions

**Usage:**
```typescript
import { usePermission } from "@/hooks/usePermission";
import { PermissionGuard } from "@/components/PermissionGuard";

// Hook usage
function TaskList() {
  const { canCreate, canUpdate } = usePermission("tasks");
  // canCreate, canRead, canUpdate, canDelete are booleans
}

// Component usage
function TaskActions({ task }) {
  return (
    <PermissionGuard component="tasks" action="delete" resourceOwnerId={task.user_id}>
      <Button onClick={deleteTask}>Delete</Button>
    </PermissionGuard>
  );
}
```

**Admin Pages:**
- `/admin/rbac/roles` - Role management (CRUD)
- `/admin/rbac/users` - User-role assignment
- Both accessible from User menu (admin only)

### Adding RBAC to New Components

1. **Backend:**
   - Add component name to RBAC checks
   - Define roles with permissions in seed script
   - Use `require_permission()` dependency or `check_permission()` service

2. **Frontend:**
   - Use `usePermission()` hook to check access
   - Wrap UI elements in `<PermissionGuard>` for conditional rendering
