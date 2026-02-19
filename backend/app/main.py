from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api_v1.api import api_router
from app.core.config import get_settings
from app.core.logging import get_access_logger, get_logger, setup_logging

settings = get_settings()
logger = get_logger(__name__)
access_logger = get_access_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Application starting up", extra={"version": "0.1.0"})
    yield
    # Shutdown
    logger.info("Application shutting down")


app = FastAPI(
    title="Full-Stack Boilerplate API",
    description="A production-ready full-stack boilerplate with FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

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
    return {"status": "ok", "version": "0.1.2"}


@app.get("/")
async def root():
    return {
        "message": "Welcome to Full-Stack Boilerplate API",
        "docs": "/docs",
        "version": "0.1.2",
    }
