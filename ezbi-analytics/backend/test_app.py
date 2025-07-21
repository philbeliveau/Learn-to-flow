#!/usr/bin/env python3
"""
Simple FastAPI app for Railway deployment testing
"""
from fastapi import FastAPI
import os

app = FastAPI(title="EZBI Analytics - Simple Test")

@app.get("/")
async def root():
    return {"message": "EZBI Analytics Backend is Running!", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ezbi-analytics-backend",
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }

@app.get("/test")
async def test():
    return {
        "message": "Railway deployment test successful",
        "port": os.getenv("PORT", "8000"),
        "database": "test_mode"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)