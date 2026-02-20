from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.api_v1.api import api_router
from app.core.config import get_settings
from app.core.logging import get_access_logger, get_logger, setup_logging
from app.core.migrations import check_and_migrate

# Rate limiter setup
# Use memory storage for simplicity (can be changed to Redis in production)
from limits.storage import MemoryStorage

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
)

settings = get_settings()
logger = get_logger(__name__)
access_logger = get_access_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (basic) - Skip for docs/redoc to allow Swagger UI
        if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self';"
            )

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Application starting up", extra={"version": "0.2.0"})

    # Validate production settings
    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        logger.warning("Using default SECRET_KEY - change for production!")

    # Check and run database migrations
    await check_and_migrate()

    yield
    # Shutdown
    logger.info("Application shutting down")


app = FastAPI(
    title="Full-Stack Boilerplate API",
    description="A production-ready full-stack boilerplate with FastAPI",
    version="0.1.3",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Store limiter reference for potential test disabling
app.state._limiter = limiter

# Security Headers (must be before CORS to ensure headers are added)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time

    start_time = time.time()

    # Log request
    access_logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
        },
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        access_logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
            },
        )

        # Add process time header
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": round(process_time, 4),
            },
            exc_info=True,
        )
        raise


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"path": request.url.path, "method": request.method},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# API Routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "ok", "version": "0.2.0"}


@app.get("/")
async def root():
    return {
        "message": "Welcome to Full-Stack Boilerplate API",
        "docs": "/docs",
        "version": "0.2.0",
    }
