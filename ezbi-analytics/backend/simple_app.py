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

    """Get current cash position from real cash flow data"""
    import pandas as pd
    import os
    
    try:
        # Load actual cash flow data
        csv_path = os.path.join(os.path.dirname(__file__), "data", "cash_flow.csv")
        df = pd.read_csv(csv_path)
        
        # Get latest data for current position
        latest = df.iloc[-1]
        
        # Calculate current position metrics
        current_cash_balance = float(latest['net cash flow-net cash flow'])
        operating_cash_flow = float(latest['operating cash flow-net operating cash flow'])
        investment_cash_flow = float(latest['investment cash flow-net investment cash flow'])
        financing_cash_flow = float(latest['Cash flow from financing-net cash flow'])
        
        # Calculate outstanding receivables and payables (estimated from cash flows)
        outstanding_receivables = max(0, operating_cash_flow * 0.3)  # 30% of operating CF
        outstanding_payables = max(0, abs(investment_cash_flow) * 0.2)  # 20% of investment CF
        
        # Today's activity simulation
        today_inflows = operating_cash_flow / 30  # Daily average from monthly
        today_outflows = abs(investment_cash_flow) / 30
        net_flow = today_inflows - today_outflows
        
        return {
            "success": True,
            "current_position": {
                "cash_balance": round(current_cash_balance, 2),
                "outstanding_receivables": round(outstanding_receivables, 2),
                "outstanding_payables": round(outstanding_payables, 2),
                "net_working_capital": round(current_cash_balance + outstanding_receivables - outstanding_payables, 2),
                "last_updated": latest['Date']
            },
            "today_activity": {
                "inflows": round(today_inflows, 2),
                "outflows": round(today_outflows, 2),
                "net_flow": round(net_flow, 2)
            },
            "cash_flow_breakdown": {
                "operating": round(operating_cash_flow, 2),
                "investing": round(investment_cash_flow, 2),
                "financing": round(financing_cash_flow, 2)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading cash flow data: {str(e)}")

@app.get("/api/v1/quick-prediction")
async def get_quick_prediction(days: int = 30):
    """Get cash flow predictions for specified number of days"""
    import pandas as pd
    import os
    from datetime import datetime, timedelta
    
    try:
        # Load actual cash flow data
        csv_path = os.path.join(os.path.dirname(__file__), "data", "cash_flow.csv")
        df = pd.read_csv(csv_path)
        
        # Calculate prediction metrics from historical data
        net_flows = df['net cash flow-net cash flow'].values
        operating_flows = df['operating cash flow-net operating cash flow'].values
        
        # Calculate averages and trends
        avg_net_flow = float(net_flows.mean())
        avg_operating_flow = float(operating_flows.mean())
        
        # Simple trend calculation (last 3 vs first 3 records)
        recent_avg = float(net_flows[-3:].mean())
        historical_avg = float(net_flows[:3].mean())
        trend_factor = recent_avg / historical_avg if historical_avg != 0 else 1.0
        
        # Predict daily cash flow
        daily_flow = avg_net_flow / 30  # Convert monthly to daily
        adjusted_daily_flow = daily_flow * trend_factor
        
        # Generate prediction for specified days
        predicted_total = adjusted_daily_flow * days
        
        # Create confidence score based on data variance
        variance = float(net_flows.var())
        confidence = max(0.6, min(0.95, 1 - (variance / abs(avg_net_flow)) * 0.1))
        
        # Generate prediction scenarios
        optimistic = predicted_total * 1.15
        pessimistic = predicted_total * 0.85
        
        # Generate daily breakdown
        daily_predictions = []
        base_date = datetime.now()
        for i in range(min(days, 30)):  # Limit to 30 days for performance
            date = base_date + timedelta(days=i)
            daily_flow_amount = adjusted_daily_flow * (0.9 + 0.2 * (i % 7) / 7)  # Weekly pattern
            daily_predictions.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_flow": round(daily_flow_amount, 2),
                "cumulative": round(daily_flow_amount * (i + 1), 2)
            })
        
        return {
            "success": True,
            "summary": {
                "period_days": days,
                "predicted_net_flow": round(predicted_total, 2),
                "daily_average": round(adjusted_daily_flow, 2),
                "confidence": round(confidence, 3),
                "trend": "positive" if trend_factor > 1.05 else "negative" if trend_factor < 0.95 else "stable"
            },
            "scenarios": {
                "optimistic": round(optimistic, 2),
                "realistic": round(predicted_total, 2),
                "pessimistic": round(pessimistic, 2)
            },
            "daily_breakdown": daily_predictions,
            "data_source": {
                "records_analyzed": len(df),
                "date_range": f"{df['Date'].min()} to {df['Date'].max()}",
                "companies": df['ticker'].nunique()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prediction: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting EZBI Analytics API Demo")
    print("📊 Access API docs at: http://localhost:8000/docs")
    print("🏭 Demo credentials: demo@ezbi.fr / demo123")
    print("💰 Cash Flow endpoints: /api/v1/current-cash-position, /api/v1/quick-prediction")
    
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )