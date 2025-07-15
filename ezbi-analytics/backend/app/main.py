from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import structlog
import time
import uvicorn

from app.core.config import settings
from app.core.security import SecurityMiddleware
from app.core.database import init_db
from app.core.exceptions import HTTPExceptionHandler
from app.core.rbac import rbac_manager
from app.api.v1.router import api_router
from app.core.monitoring import setup_monitoring
from app.core.logging import setup_logging
from app.middleware.auth_middleware import ManufacturingAuthMiddleware, InputValidationMiddleware
from app.services.token_service import token_service

# Import caching components
from app.middleware.caching_middleware import (
    CachingMiddleware, 
    SmartCacheMiddleware, 
    CacheMetricsMiddleware,
    initialize_caching,
    cleanup_caching
)
from app.services.performance_monitor import (
    performance_monitor, 
    initialize_performance_monitoring,
    cleanup_performance_monitoring,
    record_api_performance
)

# Configure structured logging
setup_logging()
logger = structlog.get_logger()

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting EZBI Analytics API", version=settings.VERSION)
    
    # Initialize database
    await init_db()
    
    # Initialize caching services
    try:
        await initialize_caching()
        logger.info("Caching services initialized")
    except Exception as e:
        logger.error("Failed to initialize caching services", error=str(e))
        # Continue without caching if Redis is not available
    
    # Initialize performance monitoring
    try:
        await initialize_performance_monitoring()
        logger.info("Performance monitoring initialized")
    except Exception as e:
        logger.error("Failed to initialize performance monitoring", error=str(e))
        # Continue without performance monitoring if Redis is not available
    
    # Setup monitoring
    setup_monitoring(app)
    
    # Initialize RBAC system
    try:
        await rbac_manager.create_default_roles_and_permissions()
        logger.info("RBAC system initialized")
    except Exception as e:
        logger.error("Failed to initialize RBAC system", error=str(e))
    
    logger.info("API startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down EZBI Analytics API")
    
    # Cleanup caching services
    try:
        await cleanup_caching()
        logger.info("Caching services cleaned up")
    except Exception as e:
        logger.error("Failed to cleanup caching services", error=str(e))
    
    # Cleanup performance monitoring
    try:
        await cleanup_performance_monitoring()
        logger.info("Performance monitoring cleaned up")
    except Exception as e:
        logger.error("Failed to cleanup performance monitoring", error=str(e))

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Cash Flow Prediction Platform for French Manufacturing SMEs",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    servers=[
        {"url": settings.SERVER_HOST, "description": "Development server"},
        {"url": settings.PRODUCTION_HOST, "description": "Production server"},
    ],
)

# Security middleware
app.add_middleware(SecurityMiddleware)

# Manufacturing authentication middleware
app.add_middleware(ManufacturingAuthMiddleware)

# Input validation middleware
app.add_middleware(InputValidationMiddleware)

# Caching middleware (before CORS to cache responses)
app.add_middleware(CacheMetricsMiddleware)  # Metrics collection
app.add_middleware(SmartCacheMiddleware)    # Smart caching with warming

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent"),
        remote_addr=request.client.host if request.client else None,
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time,
        )
        raise

# Exception handlers
app.add_exception_handler(HTTPException, HTTPExceptionHandler.http_exception_handler)
app.add_exception_handler(Exception, HTTPExceptionHandler.generic_exception_handler)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
    }

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "EZBI Analytics API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # We use our custom logging
    )
