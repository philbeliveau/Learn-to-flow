#!/usr/bin/env python3
"""
Simple EZBI Analytics API for local testing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn
import pandas as pd
import os

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
    user: dict

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
    """Demo login - accepts multiple demo credentials"""
    valid_credentials = [
        ("demo@ezbi.fr", "demo123"),
        ("admin@ezbi.com", "admin"),
        ("user@ezbi.com", "password"),
        ("demo@ezbi.com", "demo")
    ]
    
    if (credentials.email, credentials.password) in valid_credentials:
        return TokenResponse(
            access_token="demo_token_ezbi_2024",
            user={
                "id": 1,
                "email": credentials.email,
                "name": "Demo User",
                "company": "EZBI Analytics",
                "role": "admin"
            }
        )
    
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

# Cash Flow API Endpoints (Required by Frontend)
@app.get("/api/v1/current-cash-position")
async def get_current_cash_position():
    """Get current cash position - matches syntheticDataService.ts expectations"""
    return {
        "success": True,
        "current_position": {
            "cash_balance": 847392.45,
            "outstanding_receivables": 325000.00,
            "outstanding_payables": 189000.00,
            "net_working_capital": 983392.45,
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d")
        },
        "today_activity": {
            "inflows": 45000.00,
            "outflows": 32000.00,
            "net_flow": 13000.00
        },
        "metadata": {
            "currency": "EUR",
            "company": "Manufacture Lyonnaise SA",
            "data_source": "Manufacturing Tables"
        }
    }

@app.get("/api/v1/quick-prediction")
async def get_quick_prediction(days: int = 30):
    """Get quick cash flow prediction - matches syntheticDataService.ts expectations"""
    
    # Simple prediction logic based on current position
    daily_avg_inflow = 45000.00
    daily_avg_outflow = 32000.00
    daily_net = daily_avg_inflow - daily_avg_outflow
    
    total_predicted_inflows = daily_avg_inflow * days
    total_predicted_outflows = daily_avg_outflow * days
    net_cash_flow = daily_net * days
    
    current_balance = 847392.45
    ending_balance = current_balance + net_cash_flow
    
    return {
        "success": True,
        "summary": {
            "total_predicted_inflows": round(total_predicted_inflows, 2),
            "total_predicted_outflows": round(total_predicted_outflows, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "ending_balance": round(ending_balance, 2),
            "period_days": days,
            "daily_average": round(daily_net, 2)
        },
        "period": f"{days} days",
        "confidence": 0.78,
        "risk_factors": [
            "Seasonal variations in Q4",
            "Customer payment delays",
            "Raw material cost volatility"
        ],
        "key_insights": [
            f"Positive cash flow trend: +€{daily_net:.2f}/day",
            "Receivables collection improving",
            "Working capital optimized"
        ],
        "metadata": {
            "model_version": "v2.0",
            "currency": "EUR",
            "data_source": "Manufacturing Analytics",
            "generated_at": datetime.utcnow().isoformat()
        }
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

# Business Planning Status (Required by Frontend)
@app.get("/api/v1/business-planning-status")
async def get_business_planning_status():
    """Get Excel business planning status - fixes 404 error"""
    return {
        "success": True,
        "files": {
            "cash_flow_projection.xlsx": {
                "status": "updated", 
                "records": 203331,
                "last_modified": datetime.utcnow().isoformat(),
                "size_mb": 15.2
            },
            "business_plan_2024.xlsx": {
                "status": "current", 
                "records": 14088,
                "last_modified": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "size_mb": 8.7
            }
        },
        "total_files": 2,
        "last_updated": datetime.utcnow().isoformat(),
        "data_sources": ["Manufacturing Tables", "Financial Projections", "Excel Imports"],
        "processing_status": "complete",
        "sync_health": "excellent"
    }

# Manufacturing Dashboard (Required by Manufacturing BI)
@app.get("/api/v1/analytics/manufacturing-dashboard")  
async def get_manufacturing_dashboard():
    """Manufacturing dashboard data with authentication bypass for development"""
    return {
        "success": True,
        "total_customers": 50,
        "total_revenue": 4136902.14,
        "total_orders": 150,
        "total_products": 20,
        "active_employees": 30,
        "monthly_costs": 125000,
        "operational_efficiency": 0.87,
        "production_capacity": 0.78,
        "inventory_turnover": 8.5,
        "key_metrics": [
            {"name": "Production Efficiency", "value": "87%", "trend": "up"},
            {"name": "Quality Rate", "value": "97%", "trend": "stable"},
            {"name": "On-Time Delivery", "value": "94%", "trend": "up"},
            {"name": "Cost Per Unit", "value": "€12.45", "trend": "down"}
        ],
        "recent_activity": [
            {
                "type": "Invoice", 
                "reference": "INV-2024-001", 
                "amount": 15000, 
                "date": "2024-07-15",
                "customer": "Automotive Parts Ltd"
            },
            {
                "type": "Production Order", 
                "reference": "PO-2024-045", 
                "amount": 8500, 
                "date": "2024-07-15",
                "product": "Engine Components"
            },
            {
                "type": "Payment", 
                "reference": "PAY-2024-078", 
                "amount": -3200, 
                "date": "2024-07-14",
                "vendor": "Steel Supplier SA"
            }
        ],
        "financial_summary": {
            "cash_position": 847392.45,
            "accounts_receivable": 325000.00,
            "accounts_payable": 189000.00,
            "working_capital": 983392.45
        },
        "production_summary": {
            "units_produced_today": 45,
            "units_shipped": 38,
            "quality_passes": 42,
            "defects": 3
        },
        "data_sources": ["Manufacturing Tables", "Real-time Production", "Financial Systems"],
        "last_updated": datetime.utcnow().isoformat(),
        "currency": "EUR"
    }

# Manufacturing Schema Endpoints (Supporting Manufacturing BI)
@app.get("/api/manufacturing/sales/kpis")
async def get_sales_kpis():
    """Sales KPIs from manufacturing tables"""
    return {
        "success": True,
        "total_customers": 50,
        "total_invoices": 150,
        "revenue_this_month": 345000.00,
        "revenue_last_month": 312000.00,
        "avg_order_value": 2760.60,
        "top_customers": [
            {"name": "Automotive Parts Ltd", "revenue": 45000.00},
            {"name": "Steel Works SA", "revenue": 38000.00},
            {"name": "Manufacturing Corp", "revenue": 32000.00}
        ],
        "data_source": "sales.customers, sales.invoices",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/manufacturing/operations/products")
async def get_operations_products():
    """Operations and products data from manufacturing tables"""
    return {
        "success": True,
        "total_products": 20,
        "total_production_orders": 45,
        "production_efficiency": 0.87,
        "capacity_utilization": 0.78,
        "active_orders": 12,
        "recent_production": [
            {"product": "Engine Component A", "quantity": 150, "status": "completed"},
            {"product": "Steel Frame B", "quantity": 200, "status": "in_progress"},
            {"product": "Automotive Part C", "quantity": 75, "status": "queued"}
        ],
        "data_source": "operations.products, operations.production_orders",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/manufacturing/finance/summary")
async def get_finance_summary():
    """Finance summary from manufacturing tables"""
    return {
        "success": True,
        "cash_balance": 847392.45,
        "accounts_receivable": 325000.00,
        "accounts_payable": 189000.00,
        "debt_accounts": 145000.00,
        "working_capital": 983392.45,
        "monthly_burn_rate": 125000.00,
        "days_cash_remaining": 203,
        "data_source": "finance.cash_ledger, finance.debt_accounts",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/manufacturing/hr/overview")
async def get_hr_overview():
    """HR overview from manufacturing tables"""
    return {
        "success": True,
        "total_employees": 30,
        "active_employees": 28,
        "monthly_payroll": 185000.00,
        "avg_salary": 6607.14,
        "departments": [
            {"name": "Production", "count": 15},
            {"name": "Quality Control", "count": 5},
            {"name": "Administration", "count": 8},
            {"name": "Management", "count": 2}
        ],
        "data_source": "hr.employees, hr.payroll",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/manufacturing/expenses/analysis")
async def get_expenses_analysis():
    """Expenses analysis from manufacturing tables"""
    return {
        "success": True,
        "total_monthly_expenses": 125000.00,
        "expense_categories": [
            {"category": "Raw Materials", "amount": 45000.00, "percentage": 36},
            {"category": "Labor", "amount": 35000.00, "percentage": 28},
            {"category": "Utilities", "amount": 15000.00, "percentage": 12},
            {"category": "Equipment", "amount": 20000.00, "percentage": 16},
            {"category": "Other", "amount": 10000.00, "percentage": 8}
        ],
        "trend": "stable",
        "cost_per_unit": 12.45,
        "data_source": "expenses.expenses",
        "last_updated": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting EZBI Analytics API Demo")
    print("📊 Access API docs at: http://localhost:8000/docs")
    print("🏭 Demo credentials: demo@ezbi.fr / demo123")
    print("💰 Cash Flow endpoints: /api/v1/current-cash-position, /api/v1/quick-prediction")
    print("📋 NEW: Business Planning: /api/v1/business-planning-status")
    print("🏭 NEW: Manufacturing Dashboard: /api/v1/analytics/manufacturing-dashboard")
    print("📊 NEW: Manufacturing Schema endpoints: /api/manufacturing/{sales,operations,finance,hr,expenses}")
    print("🔗 Manufacturing BI endpoints ready for data connectivity")
    
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )