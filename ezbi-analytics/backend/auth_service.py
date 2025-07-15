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
import sqlite3
import os

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

# Database configuration
DATABASE_PATH = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/data/ezbi_analytics.db"

def get_db_connection():
    """Get SQLite database connection"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

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
    """Get finance KPIs from real manufacturing data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Get real financial data from the database
        cursor = conn.cursor()
        
        # Total cash flow from cash ledger
        cursor.execute("SELECT SUM(amount) as total_cash FROM finance_cash_ledger WHERE amount > 0")
        total_inflow = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(ABS(amount)) as total_cash FROM finance_cash_ledger WHERE amount < 0")
        total_outflow = cursor.fetchone()[0] or 0
        
        # Total debt from debt accounts
        cursor.execute("SELECT SUM(outstanding_amount) as total_debt FROM finance_debt_accounts")
        total_debt = cursor.fetchone()[0] or 0
        
        # Monthly payments from debt accounts
        cursor.execute("SELECT SUM(monthly_payment) as monthly_payments FROM finance_debt_accounts")
        monthly_payments = cursor.fetchone()[0] or 0
        
        # Average interest rate
        cursor.execute("SELECT AVG(interest_rate) as avg_rate FROM finance_debt_accounts")
        avg_interest_rate = cursor.fetchone()[0] or 0
        
        conn.close()
        
        net_cash_flow = total_inflow - total_outflow
        debt_ratio = total_debt / (total_inflow or 1) if total_inflow > 0 else 0
        liquidity_ratio = total_inflow / (total_outflow or 1) if total_outflow > 0 else 0
        
        return {
            "total_cash_flow": round(net_cash_flow, 2),
            "total_debt": round(total_debt, 2),
            "monthly_payments": round(monthly_payments, 2),
            "interest_rate": round(avg_interest_rate, 2),
            "debt_ratio": round(debt_ratio, 3),
            "liquidity_ratio": round(liquidity_ratio, 2)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/sales/kpis")
async def get_sales_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get sales KPIs from real manufacturing data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Total revenue from invoices
        cursor.execute("SELECT SUM(amount) as total_revenue FROM sales_invoices")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Total invoice count
        cursor.execute("SELECT COUNT(*) as total_invoices FROM sales_invoices")
        total_invoices = cursor.fetchone()[0] or 0
        
        # Active customers count
        cursor.execute("SELECT COUNT(*) as active_customers FROM sales_customers")
        active_customers = cursor.fetchone()[0] or 0
        
        # Average invoice value
        avg_invoice_value = total_revenue / total_invoices if total_invoices > 0 else 0
        
        # Growth rate (comparing recent vs older invoices)
        cursor.execute("""
            SELECT SUM(amount) as recent_revenue 
            FROM sales_invoices 
            WHERE date_issued >= date('now', '-30 days')
        """)
        recent_revenue = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT SUM(amount) as older_revenue 
            FROM sales_invoices 
            WHERE date_issued < date('now', '-30 days')
        """)
        older_revenue = cursor.fetchone()[0] or 0
        
        growth_rate = (recent_revenue - older_revenue) / older_revenue if older_revenue > 0 else 0
        
        # Conversion rate (paid vs total invoices)
        cursor.execute("SELECT COUNT(*) as paid_invoices FROM sales_invoices WHERE status = 'Paid'")
        paid_invoices = cursor.fetchone()[0] or 0
        conversion_rate = paid_invoices / total_invoices if total_invoices > 0 else 0
        
        conn.close()
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_invoices": total_invoices,
            "active_customers": active_customers,
            "avg_invoice_value": round(avg_invoice_value, 2),
            "growth_rate": round(growth_rate, 3),
            "conversion_rate": round(conversion_rate, 3)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/operations/kpis")
async def get_operations_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get operations KPIs from real manufacturing data"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Total production orders
        cursor.execute("SELECT COUNT(*) as total_orders FROM operations_production_orders")
        total_production_orders = cursor.fetchone()[0] or 0
        
        # Completed orders
        cursor.execute("SELECT COUNT(*) as completed_orders FROM operations_production_orders WHERE status = 'completed'")
        completed_orders = cursor.fetchone()[0] or 0
        
        # Efficiency rate (completed vs total)
        efficiency_rate = completed_orders / total_production_orders if total_production_orders > 0 else 0
        
        # Average base cost for products
        cursor.execute("SELECT AVG(base_cost) as avg_cost FROM operations_products")
        avg_cost = cursor.fetchone()[0] or 0
        
        # Products count
        cursor.execute("SELECT COUNT(*) as total_products FROM operations_products")
        total_products = cursor.fetchone()[0] or 0
        
        # Calculate capacity utilization based on orders vs products
        capacity_utilization = total_production_orders / (total_products * 5) if total_products > 0 else 0
        
        conn.close()
        
        return {
            "total_production_orders": total_production_orders,
            "completed_orders": completed_orders,
            "efficiency_rate": round(efficiency_rate, 3),
            "defect_rate": round(0.02, 4),  # Static for now, would need defect tracking
            "capacity_utilization": round(min(capacity_utilization, 1.0), 3),
            "avg_cycle_time": round(24.0, 1),  # Static for now, would need time tracking
            "avg_product_cost": round(avg_cost, 2),
            "total_products": total_products
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/overview/kpis")
async def get_overview_kpis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get overview KPIs from all real manufacturing tables"""
    try:
        # Validate token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Count records across all tables
        tables = [
            'sales_customers', 'sales_invoices', 'accounting_vendors', 
            'accounting_accounts_receivable', 'accounting_purchases', 'accounting_accounts_payable',
            'operations_products', 'operations_production_orders', 'finance_cash_ledger', 
            'finance_debt_accounts', 'expenses_fixed_costs', 'hr_employees', 'hr_payroll_log'
        ]
        
        total_records = 0
        table_counts = {}
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
            total_records += count
        
        # Calculate data quality score based on non-null values in key tables
        cursor.execute("SELECT COUNT(*) FROM sales_invoices WHERE amount IS NOT NULL AND amount > 0")
        valid_invoices = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sales_invoices")
        total_invoices = cursor.fetchone()[0]
        
        data_quality_score = (valid_invoices / total_invoices * 100) if total_invoices > 0 else 100
        
        conn.close()
        
        return {
            "total_records": total_records,
            "active_tables": len(tables),
            "data_quality_score": round(data_quality_score, 1),
            "last_updated": datetime.now().isoformat(),
            "system_health": "operational",
            "table_counts": table_counts,
            "database_status": "connected"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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