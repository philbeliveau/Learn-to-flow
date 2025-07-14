"""
Analytics API endpoints  
Real analytics calculation replacing fake data
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, List

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.user import User
from ..models.transaction import Transaction

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