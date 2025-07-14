#!/usr/bin/env python3
"""
Simple EZBI Analytics API for local testing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="EZBI Analytics API - Demo",
    description="AI-Powered Cash Flow Prediction for French Manufacturing SMEs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PredictionRequest(BaseModel):
    revenue: float
    expenses: float
    period_days: int = 30

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🏭 EZBI Analytics API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "EZBI Analytics API"
    }

# Authentication
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Demo login - accepts demo@ezbi.fr / demo123"""
    if credentials.email == "demo@ezbi.fr" and credentials.password == "demo123":
        return TokenResponse(access_token="demo_token_ezbi_2024")
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/v1/auth/me")
async def get_current_user():
    """Get demo user info"""
    return {
        "id": 1,
        "email": "demo@ezbi.fr",
        "name": "Jean Dupont",
        "company": "Manufacture Lyonnaise SA",
        "siret": "12345678901234",
        "role": "admin",
        "created_at": "2024-01-01T00:00:00Z"
    }

# Cash flow prediction (demo)
@app.post("/api/v1/predictions/cashflow")
async def predict_cashflow(request: PredictionRequest):
    """Demo cash flow prediction"""
    
    # Simple demo calculation
    monthly_net = request.revenue - request.expenses
    daily_net = monthly_net / 30
    predicted_amount = daily_net * request.period_days
    
    # Add some French manufacturing context
    confidence = 0.87  # Demo confidence
    seasonal_factor = 1.1 if request.period_days > 60 else 1.0
    
    return {
        "prediction": {
            "amount": round(predicted_amount * seasonal_factor, 2),
            "currency": "EUR",
            "period_days": request.period_days,
            "confidence": confidence,
            "created_at": datetime.utcnow().isoformat()
        },
        "factors": {
            "seasonal_adjustment": seasonal_factor,
            "base_daily_flow": round(daily_net, 2),
            "trend": "stable"
        },
        "recommendations": [
            "Consider seasonal patterns in Q4",
            "Monitor supplier payment terms",
            "Optimize inventory levels"
        ]
    }

# Company data
@app.get("/api/v1/company/kpis")
async def get_company_kpis():
    """Demo manufacturing KPIs"""
    return {
        "production": {
            "efficiency": 0.85,
            "capacity_utilization": 0.78,
            "units_produced": 1200,
            "defect_rate": 0.03
        },
        "financial": {
            "revenue_ytd": 1800000,
            "expenses_ytd": 1350000,
            "margin": 0.25,
            "cash_position": 450000
        },
        "inventory": {
            "turnover_ratio": 8.5,
            "days_on_hand": 43,
            "raw_materials": 125000,
            "finished_goods": 89000
        },
        "period": "2024-Q3",
        "currency": "EUR"
    }

# Upload endpoint (demo)
@app.post("/api/v1/upload/financial")
async def upload_financial_data():
    """Demo file upload response"""
    return {
        "status": "success",
        "message": "Financial data processed successfully",
        "records_processed": 156,
        "validation": {
            "errors": 0,
            "warnings": 2
        },
        "next_steps": [
            "Review data in dashboard",
            "Generate predictions",
            "Set up alerts"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting EZBI Analytics API Demo")
    print("📊 Access API docs at: http://localhost:8001/docs")
    print("🏭 Demo credentials: demo@ezbi.fr / demo123")
    
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )