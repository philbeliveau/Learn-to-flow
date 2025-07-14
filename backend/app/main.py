"""
EZBI Analytics - FastAPI Main Application
Real backend implementation replacing the fake demo
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path

from .core.database import init_db, get_db
from .core.auth import get_current_user
from .api import auth, predictions, companies, analytics
from .models.base import Base

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    print("🔧 Initializing EZBI Analytics Backend...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    print("🛑 Shutting down EZBI Analytics Backend")

# Create FastAPI application
app = FastAPI(
    title="EZBI Analytics API",
    description="AI-Powered Manufacturing Analytics Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🏭 EZBI Analytics API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ezbi-analytics-api",
        "version": "1.0.0"
    }

@app.get("/test")
async def test_interface():
    """Simple test interface"""
    return {
        "message": "🧪 EZBI Analytics Test Interface",
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth/login",
            "predictions": "/api/v1/predictions",
            "companies": "/api/v1/companies/kpis",
            "analytics": "/api/v1/analytics/dashboard"
        },
        "demo_credentials": {
            "email": "demo@ezbi.fr",
            "password": "demo123"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "message": "Check /docs for available endpoints"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Please check logs"}
    )