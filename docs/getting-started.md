# Getting Started

This guide will help you get the project up and running on your local machine.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Make (optional but recommended)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/radek-zitek-cloud/fullstack-boilerplate.git
cd fullstack-boilerplate
```

### 2. Setup Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Or using uv (recommended)
uv sync --extra dev

# Copy environment file
cp .env.example .env

# Run database migrations
uv run alembic upgrade head

# Initialize database (creates admin user)
uv run python app/db/init_db.py

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Setup Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The frontend will be available at:
- http://localhost:5173

### 4. Using Docker (Alternative)

```bash
# Build and start all services
make up-d

# Or using docker-compose directly
docker-compose up -d
```

This will start:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Redis: for background tasks

## Default Credentials

After initialization, the following admin user is created:

- **Email**: admin@example.com
- **Password**: admin123

**⚠️ Important**: Change these credentials immediately in production!

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///../data/app.db

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-in-production

# Email (for password reset)
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
MAIL_SERVER=smtp.gmail.com

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

## Next Steps

1. Explore the [API Documentation](./api/README.md)
2. Read about [Authentication](./authentication.md)
3. Check the [Development Guide](./development.md)

## Troubleshooting

If you encounter issues, see the [Troubleshooting](./troubleshooting.md) guide.
