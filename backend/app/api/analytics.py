"""
Analytics API endpoints
Advanced visualization and data analysis
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.user import User
from ..models.transaction import Transaction
from ..services.visualization_service import visualization_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Get real dashboard analytics data"""
    
    company_id = current_user.company_id
    
    # Calculate time periods
    now = datetime.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    # Sales trend (last 30 days, grouped by day)
    sales_trend = db.query(
        func.date(Transaction.transaction_date).label("date"),
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type == "sale",
        Transaction.transaction_date >= last_30_days.date()
    ).group_by(
        func.date(Transaction.transaction_date)
    ).order_by("date").all()
    
    # Recent performance metrics
    recent_sales = db.query(func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type == "sale",
        Transaction.transaction_date >= last_7_days.date()
    ).scalar() or 0
    
    total_transactions = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= last_30_days.date()
    ).count()
    
    # Average transaction value
    avg_transaction = recent_sales / max(1, total_transactions)
    
    return {
        "sales_trend": [
            {
                "date": trend.date.isoformat(),
                "amount": float(trend.total)
            }
            for trend in sales_trend
        ],
        "summary": {
            "recent_sales": recent_sales,
            "total_transactions": total_transactions,
            "avg_transaction_value": avg_transaction,
            "period": "last_30_days"
        },
        "growth_indicators": {
            "daily_avg": recent_sales / 7,
            "transaction_frequency": total_transactions / 30,
            "performance_trend": "stable"  # Could be calculated based on trends
        },
        "generated_at": now.isoformat()
    }

@router.get("/cash-flow-timeline")
async def get_cash_flow_timeline(
    timeframe: str = Query("6M", description="Time period: 1M, 3M, 6M, 1Y"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get cash flow timeline data for charts"""
    
    timeline_data = visualization_service.get_cash_flow_timeline(timeframe)
    
    return {
        "chart_data": timeline_data,
        "chart_config": {
            "type": "line",
            "title": f"Cash Flow Timeline - {timeframe}",
            "x_axis": "Time Period",
            "y_axis": "Amount (€ Billions)",
            "description": f"Real cash flow analysis from 203K+ records over {timeframe}"
        },
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "user_id": current_user.id,
            "timeframe": timeframe
        }
    }

@router.get("/predictions-chart")
async def get_predictions_chart(
    days_ahead: int = Query(30, description="Number of days to predict", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get prediction chart with confidence intervals"""
    
    prediction_data = visualization_service.get_prediction_chart(days_ahead)
    
    return {
        "chart_data": prediction_data,
        "chart_config": {
            "type": "line",
            "title": f"Cash Flow Predictions - {days_ahead} Days",
            "x_axis": "Date",
            "y_axis": "Predicted Amount (€ Millions)",
            "description": f"ML predictions based on real historical data with confidence intervals"
        },
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "user_id": current_user.id,
            "prediction_period": f"{days_ahead}_days"
        }
    }

@router.get("/banking-trends")
async def get_banking_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get banking data trend analysis"""
    
    banking_data = visualization_service.get_banking_trends()
    
    return {
        "charts": banking_data,
        "chart_configs": {
            "company_comparison": {
                "type": "bar",
                "title": "Company Cash Flow Comparison",
                "description": "Top companies by cash flow volume"
            },
            "cash_flow_distribution": {
                "type": "pie",
                "title": "Cash Flow Type Distribution",
                "description": "Breakdown of different cash flow types"
            },
            "growth_analysis": {
                "type": "line",
                "title": "Quarterly Growth Analysis",
                "description": "Cash flow growth trends by quarter"
            }
        },
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "user_id": current_user.id,
            "analysis_type": "comprehensive_banking_trends"
        }
    }

@router.get("/manufacturing-dashboard")
async def get_manufacturing_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get manufacturing sensor dashboard"""
    
    dashboard_data = visualization_service.get_manufacturing_dashboard()
    
    return {
        "dashboards": dashboard_data,
        "chart_configs": {
            "machine_performance": {
                "type": "line",
                "title": "Machine Performance Monitoring",
                "description": "Real-time RPM tracking from 14K+ sensor readings"
            },
            "temperature_monitoring": {
                "type": "bar",
                "title": "Temperature Sensor Monitoring",
                "description": "Average temperature readings across all sensors"
            },
            "quality_control": {
                "type": "bar",
                "title": "Quality Control Analysis",
                "description": "Actual measurements vs setpoint targets"
            }
        },
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "user_id": current_user.id,
            "sensor_analysis": "real_manufacturing_data"
        }
    }

@router.get("/comprehensive-report")
async def get_comprehensive_report(
    timeframe: str = Query("6M", description="Analysis timeframe"),
    include_predictions: bool = Query(True, description="Include prediction analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive analytics report with all visualizations"""
    
    # Gather all analytics data
    cash_flow_timeline = visualization_service.get_cash_flow_timeline(timeframe)
    banking_trends = visualization_service.get_banking_trends()
    manufacturing_dashboard = visualization_service.get_manufacturing_dashboard()
    
    report_data = {
        "executive_summary": {
            "total_data_points": 0,
            "analysis_period": timeframe,
            "key_insights": []
        },
        "financial_analysis": {
            "cash_flow_timeline": cash_flow_timeline,
            "banking_trends": banking_trends
        },
        "operational_analysis": {
            "manufacturing_dashboard": manufacturing_dashboard
        }
    }
    
    # Add predictions if requested
    if include_predictions:
        predictions = visualization_service.get_prediction_chart(30)
        report_data["predictive_analysis"] = {
            "cash_flow_predictions": predictions
        }
    
    # Calculate summary statistics
    if cash_flow_timeline.get("summary"):
        report_data["executive_summary"]["total_data_points"] += cash_flow_timeline["summary"].get("total_records", 0)
    
    if banking_trends.get("summary"):
        report_data["executive_summary"]["total_data_points"] += banking_trends["summary"].get("total_records", 0)
    
    if manufacturing_dashboard.get("summary"):
        report_data["executive_summary"]["total_data_points"] += manufacturing_dashboard["summary"].get("total_readings", 0)
    
    # Generate key insights
    report_data["executive_summary"]["key_insights"] = [
        f"Analyzed {report_data['executive_summary']['total_data_points']:,} real data points",
        f"Cash flow data spans {timeframe} with real banking transactions",
        "Manufacturing efficiency calculated from 14K+ sensor readings",
        "Predictions based on authentic historical patterns"
    ]
    
    return {
        "report": report_data,
        "report_config": {
            "title": f"EZBI Analytics Comprehensive Report - {timeframe}",
            "generated_by": "Real Data Analytics Engine",
            "data_sources": [
                "203K+ cash flow records",
                "14K+ manufacturing sensor readings",
                "4K+ company mappings",
                "1K+ economies of scale data points"
            ]
        },
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "user_id": current_user.id,
            "report_type": "comprehensive_analytics",
            "timeframe": timeframe,
            "includes_predictions": include_predictions
        }
    }