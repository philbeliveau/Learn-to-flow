from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    companies,
    financial_data,
    predictions,
    data,
    data_cached,
    file_uploads,
    analytics,
    integrations,
    notifications,
    admin,
    health,
    manufacturing,
    performance,
)

api_router = APIRouter()

# Public endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])

# Core features
api_router.include_router(financial_data.router, prefix="/financial-data", tags=["Financial Data"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["ML Predictions"])
api_router.include_router(data.router, prefix="/data", tags=["Data Management"])
api_router.include_router(data_cached.router, prefix="/data", tags=["Cached Data Management"])
api_router.include_router(file_uploads.router, prefix="/files", tags=["File Uploads"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# System features
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Admin endpoints
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Manufacturing endpoints (secure)
api_router.include_router(manufacturing.router, prefix="/manufacturing", tags=["Manufacturing"])

# Performance monitoring endpoints
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
