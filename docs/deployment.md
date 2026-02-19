# Deployment Guide

Instructions for deploying the Full-Stack Boilerplate to production.

## Prerequisites

- Server with Docker and Docker Compose
- Domain name (for HTTPS)
- SMTP credentials (for email notifications)
- SSL certificate (Let's Encrypt recommended)

## Quick Deployment with Docker

### 1. Clone Repository

```bash
git clone https://github.com/radek-zitek-cloud/fullstack-boilerplate.git
cd fullstack-boilerplate
```

### 2. Configure Environment

Create production `.env` files:

**backend/.env:**
```bash
# Copy example
cp backend/.env.example backend/.env

# Edit with production values
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/appdb
SECRET_KEY=$(openssl rand -hex 32)  # Generate secure key
FIRST_ADMIN_EMAIL=admin@yourdomain.com
FIRST_ADMIN_PASSWORD=secure-admin-password

# Email (required for password reset)
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-app-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Frontend URL
FRONTEND_URL=https://yourdomain.com

# CORS (production frontend)
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

**frontend/.env:**
```bash
VITE_API_URL=https://api.yourdomain.com/api/v1
```

### 3. Update Docker Compose

Edit `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - backend/.env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - uploads:/app/uploads
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  uploads:
```

### 4. Build and Start

```bash
# Build images
docker-compose -f docker-compose.yml build

# Run migrations
docker-compose -f docker-compose.yml run --rm backend uv run alembic upgrade head

# Start services
docker-compose -f docker-compose.yml up -d
```

## Production Checklist

### Security

- [ ] Change default `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Change default admin password
- [ ] Use strong database passwords
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall (allow only 80, 443)
- [ ] Set up fail2ban for SSH protection
- [ ] Disable root SSH login
- [ ] Use non-root user for deployment

### Configuration

- [ ] Update `FRONTEND_URL` to production domain
- [ ] Update `BACKEND_CORS_ORIGINS` with production domain
- [ ] Configure SMTP for email notifications
- [ ] Set up log rotation
- [ ] Configure backup strategy
- [ ] Set appropriate token expiry times

### Database

- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable database backups
- [ ] Configure connection pooling
- [ ] Set up database monitoring

### Monitoring

- [ ] Set up application monitoring (e.g., Sentry)
- [ ] Configure log aggregation
- [ ] Set up health check alerts
- [ ] Monitor disk space
- [ ] Monitor memory usage

## SSL Certificate (Let's Encrypt)

### Using Certbot

```bash
# Install Certbot
apt-get update
apt-get install -y certbot

# Obtain certificate
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Auto-renewal

Add to crontab:
```bash
0 12 * * * /usr/bin/certbot renew --quiet
```

## Nginx Configuration

### Reverse Proxy Setup

```nginx
# /etc/nginx/nginx.conf

events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:5173;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Uploads
        location /uploads/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Environment-Specific Considerations

### Development

- SQLite database
- Debug mode enabled
- CORS allows localhost
- No rate limiting (or relaxed)

### Staging

- PostgreSQL database
- Debug mode disabled
- Similar to production
- Lower resource limits

### Production

- PostgreSQL with backups
- Debug mode disabled
- Strict CORS
- Rate limiting enabled
- Monitoring enabled
- SSL/TLS enforced

## Database Migration

### SQLite to PostgreSQL

1. **Export data from SQLite:**
```bash
cd backend
uv run python -c "
import sqlite3
import json
conn = sqlite3.connect('../data/app.db')
cursor = conn.cursor()
# Export users
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()
print(json.dumps(users))
"
```

2. **Import to PostgreSQL:**
```bash
# Use appropriate tools for your setup
# Consider using pgAdmin, DBeaver, or psql commands
```

### Running Migrations

```bash
# Automatic migration
docker-compose exec backend uv run alembic upgrade head

# Check current version
docker-compose exec backend uv run alembic current

# Rollback one version
docker-compose exec backend uv run alembic downgrade -1
```

## Backup Strategy

### Database Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U user appdb > backup_$DATE.sql

# Upload to S3 (optional)
aws s3 cp backup_$DATE.sql s3://your-bucket/backups/

# Keep only last 7 days
find . -name "backup_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### File Uploads Backup

```bash
# Backup uploads directory
tar -czf uploads_backup_$DATE.tar.gz uploads/
```

## Scaling

### Horizontal Scaling

For high traffic, scale backend horizontally:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    # Load balancer will distribute requests
```

Use external load balancer (e.g., AWS ALB, Nginx Plus).

### Database Scaling

- Use read replicas for read-heavy workloads
- Connection pooling with PgBouncer
- Consider database sharding for massive scale

### Caching

Enable Redis caching for:
- User sessions
- Rate limiting counters
- Expensive queries

## Monitoring

### Health Checks

```bash
# Backend health
curl https://api.yourdomain.com/health

# Frontend health
curl -I https://yourdomain.com
```

### Log Aggregation

Send logs to centralized system:
```bash
# Example: Send to ELK stack
docker-compose logs -f backend | nc logstash 5000
```

### Metrics

Consider adding:
- Prometheus metrics endpoint
- Grafana dashboards
- Application Performance Monitoring (APM)

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check for errors
docker-compose exec backend uv run python -c "import app.main"
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec backend uv run python -c "
from app.core.database import engine
import asyncio
async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print(result.fetchone())
asyncio.run(test())
"
```

### SSL Certificate Issues

```bash
# Verify certificate
certbot certificates

# Renew manually
certbot renew
```

## Security Hardening

### Docker Security

```dockerfile
# Run as non-root user
RUN useradd -m appuser
USER appuser
```

### Secrets Management

Use Docker secrets or external vault:
```yaml
secrets:
  db_password:
    external: true
```

### Network Security

```yaml
# docker-compose.yml
networks:
  backend:
    internal: true  # No external access
  frontend:
    driver: bridge
```

---

For local development, see [Getting Started](./getting-started.md).
For architecture details, see [Architecture](./architecture.md).
