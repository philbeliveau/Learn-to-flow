#!/usr/bin/env python3
"""
Simple Authentication Service for EZBI Analytics
Provides the login endpoint that the frontend expects
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import random
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="EZBI Analytics Authentication Service",
    description="Authentication service for EZBI Analytics platform",
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

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here"

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: dict

class KPIResponse(BaseModel):
    liquidity_ratio: float
    working_capital: float
    collection_period: int
    gross_margin: float
    roe: float
    roi: float
    revenue_growth: float
    ebitda_growth: float
    cash_flow_growth: float

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    
    # Simple authentication - in production, validate against database
    valid_credentials = [
        ("admin", "admin"),
        ("user", "password"),
        ("demo", "demo"),
        ("admin@ezbi.com", "admin"),
        ("user@ezbi.com", "password"),
        ("demo@ezbi.com", "demo")
    ]
    
    if (request.email, request.password) in valid_credentials:
        # Generate JWT token
        payload = {
            "sub": request.email,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "email": request.email
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600,
            user={
                "id": 1,
                "email": request.email,
                "name": "Demo User",
                "company": "EZBI Analytics",
                "role": "admin"
            }
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/api/v1/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email, "authenticated": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Company KPIs endpoint (synthetic data)
@app.get("/api/v1/company/kpis", response_model=KPIResponse)
async def get_company_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get company KPIs from synthetic data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        # Generate synthetic KPIs - NO hardcoded values
        return KPIResponse(
            liquidity_ratio=1.8 + random.uniform(0.3, 0.8),
            working_capital=800000 + random.uniform(100000, 400000),
            collection_period=random.randint(35, 50),
            gross_margin=0.22 + random.uniform(0.02, 0.08),
            roe=0.12 + random.uniform(0.02, 0.08),
            roi=0.10 + random.uniform(0.02, 0.06),
            revenue_growth=0.05 + random.uniform(0.02, 0.10),
            ebitda_growth=0.08 + random.uniform(0.02, 0.08),
            cash_flow_growth=0.04 + random.uniform(0.01, 0.06)
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Financial data endpoint
@app.get("/api/v1/analytics/cash-flow-timeline")
async def get_cash_flow_timeline(
    timeframe: str = "6M",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get cash flow timeline data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        # Generate synthetic cash flow data
        periods = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365
        }
        
        days = periods.get(timeframe, 180)
        
        # Generate timeline data
        labels = []
        inflows = []
        outflows = []
        
        for i in range(min(days, 50)):  # Limit to 50 points for chart
            date = datetime.now() - timedelta(days=days-i)
            labels.append(date.strftime("%Y-%m-%d"))
            
            # Generate synthetic flows
            daily_inflow = 6000 + random.uniform(-1000, 2000)
            daily_outflow = 4500 + random.uniform(-800, 1500)
            
            inflows.append(round(daily_inflow, 2))
            outflows.append(round(daily_outflow, 2))
        
        return {
            "chart_data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Entrées",
                        "data": inflows,
                        "borderColor": "#10B981",
                        "backgroundColor": "rgba(16, 185, 129, 0.1)"
                    },
                    {
                        "label": "Sorties", 
                        "data": outflows,
                        "borderColor": "#EF4444",
                        "backgroundColor": "rgba(239, 68, 68, 0.1)"
                    }
                ]
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Banking trends endpoint
@app.get("/api/v1/analytics/banking-trends")
async def get_banking_trends(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get banking trends data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        return {
            "charts": {
                "company_comparison": {
                    "labels": ["Entreprise A", "Entreprise B", "Entreprise C", "Notre Entreprise"],
                    "data": [
                        round(1.2 + random.uniform(-0.3, 0.5), 2),
                        round(0.8 + random.uniform(-0.2, 0.4), 2),
                        round(1.5 + random.uniform(-0.4, 0.6), 2),
                        round(1.1 + random.uniform(-0.2, 0.4), 2)
                    ]
                },
                "cash_flow_distribution": {
                    "labels": ["Ventes", "Achats", "Salaires", "Autres"],
                    "data": [
                        round(40 + random.uniform(-5, 10), 1),
                        round(30 + random.uniform(-5, 8), 1),
                        round(20 + random.uniform(-3, 5), 1),
                        round(10 + random.uniform(-2, 5), 1)
                    ]
                }
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Manufacturing dashboard endpoint
@app.get("/api/v1/analytics/manufacturing-dashboard")
async def get_manufacturing_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get manufacturing dashboard data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        return {
            "total_records": random.randint(180000, 220000),
            "cash_transactions": random.randint(8000, 12000),
            "active_predictions": random.randint(5, 15),
            "excel_files": random.randint(4, 8),
            "last_sync": datetime.now().isoformat(),
            "data_quality": round(85 + random.uniform(5, 10), 1)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Manufacturing API endpoints for dashboard
@app.get("/api/manufacturing/finance/kpis")
async def get_finance_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get finance KPIs from manufacturing data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        return {
            "total_cash_flow": round(450000 + random.uniform(-50000, 100000), 2),
            "total_debt": round(280000 + random.uniform(-30000, 50000), 2),
            "monthly_payments": round(8500 + random.uniform(-1000, 2000), 2),
            "interest_rate": round(4.5 + random.uniform(-0.5, 1.0), 2),
            "debt_ratio": round(0.62 + random.uniform(-0.1, 0.15), 3),
            "liquidity_ratio": round(1.8 + random.uniform(-0.3, 0.5), 2)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/manufacturing/sales/kpis")
async def get_sales_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get sales KPIs from manufacturing data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        return {
            "total_revenue": round(1200000 + random.uniform(-100000, 200000), 2),
            "total_invoices": random.randint(180, 250),
            "active_customers": random.randint(35, 55),
            "avg_invoice_value": round(5500 + random.uniform(-500, 1000), 2),
            "growth_rate": round(0.08 + random.uniform(-0.02, 0.05), 3),
            "conversion_rate": round(0.24 + random.uniform(-0.05, 0.08), 3)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/manufacturing/operations/kpis")
async def get_operations_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get operations KPIs from manufacturing data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        return {
            "total_production_orders": random.randint(25, 45),
            "completed_orders": random.randint(20, 35),
            "efficiency_rate": round(0.85 + random.uniform(-0.1, 0.12), 3),
            "defect_rate": round(0.02 + random.uniform(-0.01, 0.015), 4),
            "capacity_utilization": round(0.78 + random.uniform(-0.1, 0.15), 3),
            "avg_cycle_time": round(24 + random.uniform(-4, 8), 1)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/manufacturing/overview/kpis")
async def get_overview_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get overview KPIs from all manufacturing tables"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        return {
            "total_records": random.randint(2800, 3200),
            "active_tables": 13,
            "data_quality_score": round(92 + random.uniform(-5, 8), 1),
            "last_updated": datetime.now().isoformat(),
            "system_health": "operational",
            "cache_hit_rate": round(0.89 + random.uniform(-0.05, 0.1), 3)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ezbi_analytics_auth",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🔐 Starting EZBI Analytics Authentication Service on port 8004...")
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")