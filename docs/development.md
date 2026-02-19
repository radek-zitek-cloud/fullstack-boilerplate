# Development Guide

Guide for developers working on the Full-Stack Boilerplate project.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Make (optional)
- Docker (optional)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/radek-zitek-cloud/fullstack-boilerplate.git
cd fullstack-boilerplate

# Setup backend
cd backend
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run python app/db/init_db.py

# Setup frontend
cd ../frontend
npm install
cp .env.example .env
```

## Development Workflow

### Running the Application

```bash
# Terminal 1: Backend
cd backend
make backend
# Or: uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
make frontend
# Or: npm run dev
```

### Available Make Commands

```bash
# Build Docker images
make build

# Start with Docker
make up        # Foreground
make up-d      # Detached

# View logs
make logs
make logs-backend
make logs-frontend

# Database
make db-migrate
make db-migration MESSAGE="add new table"
make db-downgrade

# Testing
make test-backend
make test-frontend

# Code quality
make format
make lint

# Cleanup
make clean
make clean-all
```

## Project Structure

### Backend

```
backend/
├── app/
│   ├── api/                 # API routes
│   │   ├── api_v1/         # API version 1
│   │   │   └── endpoints/  # Endpoint handlers
│   │   └── deps.py         # Dependencies
│   ├── core/               # Core utilities
│   │   ├── config.py       # Configuration
│   │   ├── security.py     # Security utilities
│   │   └── database.py     # Database setup
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic
├── tests/                  # Test suite
└── alembic/               # Database migrations
```

### Frontend

```
frontend/src/
├── components/            # Reusable components
│   └── ui/               # shadcn/ui components
├── contexts/             # React contexts
├── pages/                # Page components
├── hooks/                # Custom hooks
└── lib/                  # Utilities
```

## Code Style

### Python

- **Formatter**: ruff
- **Linter**: ruff
- **Type Checker**: mypy

```bash
# Format code
make format

# Run linter
make lint
```

**Style Guidelines:**
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Docstrings for public functions/classes

### TypeScript

- **Formatter**: Prettier
- **Linter**: ESLint

```bash
# In frontend directory
npm run lint
npm run format
```

## Testing

### Running Tests

```bash
# Backend tests
make test-backend
# Or: cd backend && uv run pytest -v

# Frontend tests
make test-frontend
# Or: cd frontend && npm test

# Coverage
make test-coverage
```

### Writing Tests

**Backend Example:**
```python
# tests/api/test_auth.py
async def test_login_success(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Frontend Example:**
```typescript
// __tests__/Login.test.tsx
test("submits login form", async () => {
  render(<Login />);
  fireEvent.change(screen.getByLabelText(/email/i), {
    target: { value: "test@example.com" },
  });
  fireEvent.click(screen.getByText(/login/i));
  await waitFor(() => {
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });
});
```

## Database Migrations

### Creating Migrations

```bash
cd backend

# Auto-generate from models
make db-migration MESSAGE="add users table"

# Or manually
uv run alembic revision --autogenerate -m "add users table"
```

### Applying Migrations

```bash
# Upgrade to latest
make db-migrate

# Upgrade to specific version
uv run alembic upgrade head

# Downgrade
uv run alembic downgrade -1
```

### Migration Best Practices

1. **Always review auto-generated migrations**
2. **Test migrations on fresh database**
3. **Never modify existing migrations**
4. **Include both upgrade and downgrade**

## Adding New Features

### 1. Backend Endpoint

```python
# app/api/api_v1/endpoints/items.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/")
async def get_items(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all items for current user."""
    # Implementation
    pass
```

### 2. Register Router

```python
# app/api/api_v1/api.py
from app.api.api_v1.endpoints import items

api_router.include_router(items.router, prefix="/items", tags=["items"])
```

### 3. Create Schema

```python
# app/schemas/item.py
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemResponse(ItemCreate):
    id: int
    user_id: int
```

### 4. Create Model

```python
# app/models/item.py
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Item(Base, TimestampMixin):
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

### 5. Create Migration

```bash
uv run alembic revision --autogenerate -m "add items table"
uv run alembic upgrade head
```

### 6. Frontend Integration

```typescript
// Add API call
export const getItems = async () => {
  const response = await api.get("/items");
  return response.data;
};

// Add component
export default function Items() {
  const [items, setItems] = useState([]);
  
  useEffect(() => {
    getItems().then(setItems);
  }, []);
  
  return (
    <div>
      {items.map(item => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  );
}
```

## Debugging

### Backend Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use logging
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.debug("Debug message", extra={"user_id": user_id})
```

### Frontend Debugging

```typescript
// Console logging
console.log("Debug:", data);

// React DevTools
// Install browser extension
```

### Log Files

```bash
# Application logs
tail -f logs/app.log

# Access logs
tail -f logs/access.log

# Error logs
tail -f logs/error.log
```

## Common Tasks

### Reset Database

```bash
cd backend
rm ../data/app.db
uv run alembic upgrade head
uv run python app/db/init_db.py
```

### Update Dependencies

```bash
# Backend
cd backend
uv lock
uv sync --extra dev

# Frontend
cd frontend
npm update
```

### Run Linter Fixes

```bash
# Backend
make format

# Frontend
npm run format
```

### Clear Cache

```bash
# Python cache
find . -type d -name __pycache__ -exec rm -r {} +

# Node modules
rm -rf frontend/node_modules
npm install
```

## Environment Variables

### Backend

```bash
# .env file
DEBUG=true                    # Debug mode
LOG_LEVEL=debug              # Logging level
DATABASE_URL=sqlite:///...   # Database URL
SECRET_KEY=your-secret       # JWT secret
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Token expiry
```

### Frontend

```bash
# .env file
VITE_API_URL=http://localhost:8000/api/v1
```

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:
```
feat: add user profile page
fix: resolve authentication bug
docs: update API documentation
test: add user registration tests
```

### Pull Request Process

1. Create feature branch
2. Make changes with tests
3. Run full test suite
4. Update documentation
5. Create PR with description
6. Code review
7. Merge to main

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Locked

```bash
# Remove lock file
rm backend/data/app.db-journal
```

### Frontend Build Errors

```bash
# Clear Vite cache
rm -rf frontend/node_modules/.vite

# Restart dev server
npm run dev
```

---

For more information, see:
- [Getting Started](./getting-started.md)
- [Architecture](./architecture.md)
- [API Reference](./api/README.md)
