"""
Cash Flow Prediction API
FastAPI endpoints for cash flow prediction service
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import asyncio
from pydantic import BaseModel
import os

from cash_flow_prediction_engine import create_cash_flow_prediction_engine
from realistic_excel_generator import create_realistic_excel_generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cash Flow Prediction API",
    description="Manufacturing cash flow prediction service combining PostgreSQL operational data with Excel business planning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
prediction_engine = None
excel_generator = None

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/manufacturing_db")
EXCEL_DATA_PATH = os.getenv("EXCEL_DATA_PATH", "/app/business-planning")

# Request/Response models
class PredictionRequest(BaseModel):
    start_date: str
    end_date: str
    model_type: Optional[str] = "ensemble"
    include_scenarios: Optional[bool] = True

class PredictionResponse(BaseModel):
    success: bool
    prediction_info: Dict[str, Any]
    predictions: Dict[str, Any]
    scenarios: Optional[Dict[str, Any]] = None
    insights: Dict[str, Any]
    data_quality: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global prediction_engine, excel_generator
    
    try:
        # Initialize prediction engine
        prediction_engine = create_cash_flow_prediction_engine(DATABASE_URL, EXCEL_DATA_PATH)
        await prediction_engine.initialize_connection_pool()
        
        # Initialize Excel generator
        excel_generator = create_realistic_excel_generator(EXCEL_DATA_PATH)
        
        logger.info("Cash flow prediction service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start cash flow prediction service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    if prediction_engine:
        await prediction_engine.close()
    logger.info("Cash flow prediction service shut down")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        if prediction_engine and prediction_engine.connection_pool:
            async with prediction_engine.connection_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "cash_flow_prediction_api",
            "timestamp": datetime.now().isoformat(),
            "database_connected": True
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/v1/predict-cash-flow")
async def predict_cash_flow(request: PredictionRequest):
    """Generate cash flow predictions"""
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Update model configuration
        if request.model_type:
            prediction_engine.config.model_type = request.model_type
        
        # Generate predictions
        prediction_result = await prediction_engine.predict_cash_flow(start_date, end_date)
        
        # Prepare response
        response_data = {
            "success": True,
            "prediction_info": prediction_result["prediction_info"],
            "predictions": prediction_result["predictions"],
            "insights": prediction_result["insights"],
            "data_quality": prediction_result["data_quality"]
        }
        
        # Include scenarios if requested
        if request.include_scenarios:
            response_data["scenarios"] = prediction_result["scenarios"]
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to generate cash flow prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/api/v1/quick-prediction")
async def quick_prediction(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to predict")
):
    """Generate quick cash flow prediction for specified days"""
    try:
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days)
        
        # Generate prediction
        prediction_result = await prediction_engine.predict_cash_flow(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.min.time())
        )
        
        # Return simplified response
        return {
            "success": True,
            "period": f"{days} days",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "summary": {
                "total_predicted_inflows": sum(day["predicted_inflows"] for day in prediction_result["predictions"]["daily_predictions"]),
                "total_predicted_outflows": sum(day["predicted_outflows"] for day in prediction_result["predictions"]["daily_predictions"]),
                "net_cash_flow": sum(day["net_cash_flow"] for day in prediction_result["predictions"]["daily_predictions"]),
                "ending_balance": prediction_result["predictions"]["daily_predictions"][-1]["cumulative_balance"]
            },
            "risk_factors": prediction_result["insights"]["risk_factors"],
            "key_insights": prediction_result["insights"]["key_insights"]
        }
        
    except Exception as e:
        logger.error(f"Failed to generate quick prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Quick prediction failed: {str(e)}")

@app.get("/api/v1/current-cash-position")
async def get_current_cash_position():
    """Get current cash position and real-time metrics"""
    try:
        # Get current cash balance
        current_balance = await prediction_engine._get_current_cash_balance()
        
        # Get today's transactions
        today = datetime.now().date()
        async with prediction_engine.connection_pool.acquire() as conn:
            today_transactions = await conn.fetch("""
                SELECT 
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as today_inflows,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as today_outflows,
                    SUM(amount) as today_net_flow,
                    COUNT(*) as transaction_count
                FROM finance.cash_ledger
                WHERE date_recorded = $1
            """, today)
            
            today_data = dict(today_transactions[0]) if today_transactions else {}
            
            # Get outstanding receivables
            outstanding_ar = await conn.fetchval("""
                SELECT COALESCE(SUM(amount_outstanding), 0) 
                FROM accounting.accounts_receivable
                WHERE as_of_date = $1
            """, today)
            
            # Get outstanding payables
            outstanding_ap = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM accounting.purchases
                WHERE payment_status = 'Outstanding'
            """)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "current_position": {
                "cash_balance": float(current_balance),
                "outstanding_receivables": float(outstanding_ar or 0),
                "outstanding_payables": float(outstanding_ap or 0),
                "net_working_capital": float(current_balance) + float(outstanding_ar or 0) - float(outstanding_ap or 0)
            },
            "today_activity": {
                "inflows": float(today_data.get('today_inflows', 0)),
                "outflows": float(today_data.get('today_outflows', 0)),
                "net_flow": float(today_data.get('today_net_flow', 0)),
                "transaction_count": int(today_data.get('transaction_count', 0))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get current cash position: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cash position: {str(e)}")

@app.get("/api/v1/cash-flow-dashboard")
async def get_cash_flow_dashboard():
    """Get comprehensive cash flow dashboard data"""
    try:
        # Get 30-day prediction
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        prediction_result = await prediction_engine.predict_cash_flow(start_date, end_date)
        
        # Get current position
        current_position = await get_current_cash_position()
        
        # Prepare dashboard data
        dashboard_data = {
            "success": True,
            "dashboard_info": {
                "generated_at": datetime.now().isoformat(),
                "period": "30 days",
                "data_sources": ["postgresql_operational", "excel_business_planning"]
            },
            "current_position": current_position["current_position"],
            "predictions": {
                "daily_predictions": prediction_result["predictions"]["daily_predictions"][:7],  # Next 7 days
                "weekly_summary": prediction_result["predictions"]["weekly_summary"],
                "monthly_summary": prediction_result["predictions"]["monthly_summary"]
            },
            "scenarios": {
                "base_case": prediction_result["scenarios"]["base_case"]["monthly_summary"],
                "optimistic": prediction_result["scenarios"]["optimistic"]["monthly_summary"],
                "pessimistic": prediction_result["scenarios"]["pessimistic"]["monthly_summary"]
            },
            "insights": prediction_result["insights"],
            "data_quality": prediction_result["data_quality"],
            "charts": await _generate_dashboard_charts(prediction_result)
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to generate dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

@app.post("/api/v1/regenerate-business-planning")
async def regenerate_business_planning(background_tasks: BackgroundTasks):
    """Regenerate business planning Excel files"""
    try:
        def generate_files():
            year = datetime.now().year
            files = excel_generator.generate_all_business_files(year)
            logger.info(f"Generated {len(files)} business planning files")
        
        # Run in background
        background_tasks.add_task(generate_files)
        
        return {
            "success": True,
            "message": "Business planning files regeneration started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to regenerate business planning files: {e}")
        raise HTTPException(status_code=500, detail=f"File regeneration failed: {str(e)}")

@app.get("/api/v1/business-planning-status")
async def get_business_planning_status():
    """Get status of business planning files"""
    try:
        from pathlib import Path
        
        excel_path = Path(EXCEL_DATA_PATH)
        files = list(excel_path.glob("*.xlsx"))
        
        file_status = []
        for file in files:
            stat = file.stat()
            file_status.append({
                "filename": file.name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "age_hours": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
            })
        
        return {
            "success": True,
            "excel_data_path": str(excel_path),
            "total_files": len(files),
            "files": sorted(file_status, key=lambda x: x["modified"], reverse=True),
            "last_generated": max([f["modified"] for f in file_status]) if file_status else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get business planning status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/api/v1/model-performance")
async def get_model_performance():
    """Get model performance metrics"""
    try:
        performance_data = {
            "success": True,
            "model_info": {
                "model_type": prediction_engine.config.model_type,
                "last_training_date": prediction_engine.last_training_date.isoformat() if prediction_engine.last_training_date else None,
                "retrain_frequency_days": prediction_engine.config.retrain_frequency_days,
                "prediction_horizon_days": prediction_engine.config.prediction_horizon_days,
                "confidence_interval": prediction_engine.config.confidence_interval
            },
            "available_models": list(prediction_engine.models.keys()),
            "training_required": prediction_engine._should_retrain_models(),
            "data_sources": prediction_engine.prediction_components
        }
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Model performance check failed: {str(e)}")

async def _generate_dashboard_charts(prediction_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate chart configurations for dashboard"""
    charts = []
    
    # Cash flow trend chart
    daily_predictions = prediction_result["predictions"]["daily_predictions"]
    
    charts.append({
        "type": "line",
        "title": "Cash Flow Forecast",
        "data": {
            "labels": [day["date"] for day in daily_predictions],
            "datasets": [
                {
                    "label": "Predicted Inflows",
                    "data": [day["predicted_inflows"] for day in daily_predictions],
                    "borderColor": "#10B981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": False
                },
                {
                    "label": "Predicted Outflows",
                    "data": [day["predicted_outflows"] for day in daily_predictions],
                    "borderColor": "#EF4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.1)",
                    "fill": False
                },
                {
                    "label": "Net Cash Flow",
                    "data": [day["net_cash_flow"] for day in daily_predictions],
                    "borderColor": "#3B82F6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": True
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "30-Day Cash Flow Forecast"
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "ticks": {
                        "callback": "function(value) { return '$' + value.toLocaleString(); }"
                    }
                }
            }
        }
    })
    
    # Cumulative cash balance chart
    charts.append({
        "type": "line",
        "title": "Cumulative Cash Balance",
        "data": {
            "labels": [day["date"] for day in daily_predictions],
            "datasets": [{
                "label": "Cumulative Balance",
                "data": [day["cumulative_balance"] for day in daily_predictions],
                "borderColor": "#8B5CF6",
                "backgroundColor": "rgba(139, 92, 246, 0.1)",
                "fill": True
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Projected Cash Balance"
                }
            },
            "scales": {
                "y": {
                    "ticks": {
                        "callback": "function(value) { return '$' + value.toLocaleString(); }"
                    }
                }
            }
        }
    })
    
    # Scenario comparison chart
    scenarios = prediction_result["scenarios"]
    charts.append({
        "type": "bar",
        "title": "Scenario Comparison",
        "data": {
            "labels": ["Base Case", "Optimistic", "Pessimistic"],
            "datasets": [{
                "label": "Month-End Balance",
                "data": [
                    scenarios["base_case"]["monthly_summary"][0]["ending_balance"] if scenarios["base_case"]["monthly_summary"] else 0,
                    scenarios["optimistic"]["monthly_summary"][0]["ending_balance"] if scenarios["optimistic"]["monthly_summary"] else 0,
                    scenarios["pessimistic"]["monthly_summary"][0]["ending_balance"] if scenarios["pessimistic"]["monthly_summary"] else 0
                ],
                "backgroundColor": ["#3B82F6", "#10B981", "#EF4444"]
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Scenario Analysis - Month-End Balance"
                }
            },
            "scales": {
                "y": {
                    "ticks": {
                        "callback": "function(value) { return '$' + value.toLocaleString(); }"
                    }
                }
            }
        }
    })
    
    return charts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)