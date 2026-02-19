# System Architecture

Overview of the Full-Stack Boilerplate architecture and design decisions.

## High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend      │     │   Database      │
│   (React 19)    │────▶│   (FastAPI)     │────▶│   (SQLite/      │
│                 │     │                 │     │    PostgreSQL)  │
│ - React Router  │◀────│ - REST API      │     │                 │
│ - Axios         │     │ - JWT Auth      │     │ - SQLAlchemy    │
│ - Tailwind CSS  │     │ - Async/await   │     │ - Alembic       │
│ - shadcn/ui     │     │ - Rate limiting │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │
        │               ┌─────────────────┐
        └──────────────▶│     Redis       │
                        │  (Background    │
                        │   tasks)        │
                        └─────────────────┘
```

## Backend Architecture

### Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  - Request/Response handling                                │
│  - Input validation (Pydantic schemas)                      │
│  - Authentication/Authorization                             │
│  - Rate limiting                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                              │
│  - Business logic                                           │
│  - Complex operations                                       │
│  - External integrations (email)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│  - Database models (SQLAlchemy)                             │
│  - Data access                                              │
│  - Migrations (Alembic)                                     │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
backend/
├── app/
│   ├── api/              # API layer
│   │   ├── api_v1/       # API version 1
│   │   │   └── endpoints/# API endpoint handlers
│   │   └── deps.py       # Dependencies (auth, DB)
│   ├── core/             # Core utilities
│   │   ├── config.py     # Configuration
│   │   ├── security.py   # Authentication utilities
│   │   ├── database.py   # Database connection
│   │   └── logging.py    # Logging setup
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── db/               # Database initialization
└── tests/                # Test suite
```

## Frontend Architecture

### Component Structure

```
frontend/src/
├── components/           # Reusable components
│   └── ui/              # shadcn/ui components
├── contexts/            # React contexts
│   ├── AuthContext.tsx  # Authentication state
│   └── ThemeContext.tsx # Theme management
├── pages/               # Page components
├── hooks/               # Custom React hooks
└── lib/                 # Utilities
    ├── api.ts          # API client
    └── utils.ts        # Helper functions
```

### State Management

- **Authentication**: Context API with localStorage persistence
- **Theme**: Context API with localStorage persistence
- **API State**: React Query (optional, currently using direct Axios)

## Authentication Flow

### Login Flow

```
1. User submits credentials
        │
        ▼
2. Backend validates credentials
   - Check password hash
   - Verify user is active
        │
        ▼
3. Generate JWT tokens
   - Access token (30 days)
   - Refresh token (7 days)
        │
        ▼
4. Store tokens
   - localStorage (current implementation)
   - httpOnly cookies (recommended for production)
```

### Token Refresh Flow

```
1. API request with expired access token
        │
        ▼
2. Receive 401 Unauthorized
        │
        ▼
3. Axios interceptor catches 401
        │
        ▼
4. Send refresh token to /auth/refresh
        │
        ▼
5. Receive new access token
        │
        ▼
6. Retry original request
```

## Database Design

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌─────────────────────┐
│    User      │       │    Task      │       │ PasswordResetToken  │
├──────────────┤       ├──────────────┤       ├─────────────────────┤
│ id (PK)      │──┐    │ id (PK)      │       │ id (PK)             │
│ email        │  │    │ title        │       │ user_id (FK)        │──┐
│ password     │  │    │ description  │       │ token               │  │
│ first_name   │  └───▶│ completed    │       │ expires_at          │  │
│ last_name    │       │ user_id (FK) │──┐    │ used                │  │
│ is_active    │       │ created_at   │  │    └─────────────────────┘  │
│ is_admin     │       └──────────────┘  │                             │
│ created_at   │                          └─────────────────────────────┘
│ updated_at   │
└──────────────┘
```

### Key Design Decisions

1. **Soft Deletes**: Not implemented (hard deletes only)
2. **Timestamps**: All tables have created_at and updated_at
3. **Indexes**: Primary keys and foreign keys are indexed
4. **Relationships**: One-to-many (User → Tasks), One-to-many (User → ResetTokens)

## Security Architecture

### Layered Security

```
┌─────────────────────────────────────────────┐
│ Layer 1: Network Security                    │
│ - HTTPS/TLS                                  │
│ - CORS configuration                         │
│ - Rate limiting                              │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Layer 2: Application Security                │
│ - JWT authentication                         │
│ - Input validation (Pydantic)                │
│ - XSS protection (bleach)                    │
│ - Security headers                           │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Layer 3: Data Security                       │
│ - Password hashing (bcrypt)                  │
│ - Database parameterization                  │
│ - File upload validation                     │
└─────────────────────────────────────────────┘
```

### Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy` (excluded for /docs)
- `Referrer-Policy: strict-origin-when-cross-origin`

## Deployment Architecture

### Docker Setup

```
┌─────────────────────────────────────────────┐
│              Docker Compose                  │
│                                              │
│  ┌──────────────┐    ┌──────────────┐       │
│  │   Backend    │    │   Frontend   │       │
│  │   Container  │    │   Container  │       │
│  │   (FastAPI)  │    │   (Nginx)    │       │
│  └──────────────┘    └──────────────┘       │
│         │                   │                │
│         └─────────┬─────────┘                │
│                   │                          │
│            ┌──────┴──────┐                  │
│            │    Nginx    │                  │
│            │    Proxy    │                  │
│            └─────────────┘                  │
│                                              │
└─────────────────────────────────────────────┘
```

## Scalability Considerations

### Current Limitations

- Single instance deployment
- SQLite database (file-based)
- Local file storage
- Single Redis instance

### Scaling Path

1. **Database**: Migrate to PostgreSQL with connection pooling
2. **File Storage**: Use cloud storage (S3, etc.)
3. **Caching**: Redis cluster
4. **Load Balancing**: Multiple backend instances behind load balancer
5. **CDN**: For static assets

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: python-jose → PyJWT
- **Password Hashing**: bcrypt
- **Validation**: Pydantic
- **Testing**: pytest + pytest-asyncio

### Frontend
- **Framework**: React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Build Tool**: Vite

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **Background Jobs**: Celery + Redis
- **Version Control**: Git

## Monitoring & Logging

### Logging Structure

- **Application logs**: `logs/app.log`
- **Access logs**: `logs/access.log`
- **Error logs**: `logs/error.log`
- **Format**: Structured JSON

### Health Checks

- `/health` - Basic health check
- `/docs` - API documentation
- Database connection monitoring

## Development Workflow

### Local Development

```
1. Start backend: make backend
2. Start frontend: make frontend
3. Run tests: make test-backend
4. Check logs: make logs-app
```

### Code Quality

- **Linting**: ruff (Python), ESLint (TypeScript)
- **Formatting**: ruff format, Prettier
- **Type Checking**: mypy (Python), TypeScript compiler

---

For more details, see:
- [Getting Started](./getting-started.md)
- [Deployment Guide](./deployment.md)
- [API Reference](./api/README.md)
