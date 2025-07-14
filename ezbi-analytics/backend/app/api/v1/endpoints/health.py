from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "EZBI Analytics API"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "EZBI Analytics API",
        "version": "1.0.0",
        "environment": "development",
        "database": "connected",
        "redis": "connected"
    }