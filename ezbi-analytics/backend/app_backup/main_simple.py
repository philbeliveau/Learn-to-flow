from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import asyncpg
import psycopg2
from typing import Dict, Any

# Simple FastAPI app for Railway deployment
app = FastAPI(
    title="EZBI Analytics API",
    description="Manufacturing Intelligence Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-fen55mqxa-philippe-beliveaus-projects.vercel.app",
        "https://ezbi-analytics.vercel.app",
        "https://ezbi-analytics-*.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:cnaAFVnruvkBnnzxCDxUEkfedixdbCHH@yamanote.proxy.rlwy.net:25571/railway")

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "EZBI Analytics API", "status": "online", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-01-24T19:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e),
            "timestamp": "2025-01-24T19:00:00Z"
        }

@app.get("/api/manufacturing/sales/kpis")
async def get_sales_kpis():
    """Get sales KPIs."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get customer count
        cursor.execute("SELECT COUNT(*) FROM sales_customers")
        customer_count = cursor.fetchone()[0]
        
        # Get invoice data
        cursor.execute("SELECT COUNT(*), SUM(CAST(amount AS DECIMAL)) FROM sales_invoices")
        invoice_result = cursor.fetchone()
        invoice_count = invoice_result[0]
        total_revenue = float(invoice_result[1]) if invoice_result[1] else 0
        
        cursor.close()
        conn.close()
        
        return {
            "customers": customer_count,
            "invoices": invoice_count,
            "total_revenue": total_revenue,
            "avg_revenue_per_customer": total_revenue / customer_count if customer_count > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/operations/kpis")
async def get_operations_kpis():
    """Get operations KPIs."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get product count
        cursor.execute("SELECT COUNT(*) FROM operations_products")
        product_count = cursor.fetchone()[0]
        
        # Get production orders
        cursor.execute("SELECT COUNT(*) FROM operations_production_orders")
        order_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "products": product_count,
            "production_orders": order_count,
            "active_orders": order_count  # Simplified for demo
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/finance/kpis")
async def get_finance_kpis():
    """Get finance KPIs."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get cash flow data
        cursor.execute("SELECT COUNT(*), SUM(CAST(amount AS DECIMAL)) FROM finance_cash_ledger")
        result = cursor.fetchone()
        transaction_count = result[0]
        total_cash_flow = float(result[1]) if result[1] else 0
        
        cursor.close()
        conn.close()
        
        return {
            "transactions": transaction_count,
            "total_cash_flow": total_cash_flow,
            "avg_transaction": total_cash_flow / transaction_count if transaction_count > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/hr/kpis")
async def get_hr_kpis():
    """Get HR KPIs."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get employee count
        cursor.execute("SELECT COUNT(*) FROM hr_employees")
        employee_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "employees": employee_count,
            "active_employees": employee_count  # Simplified
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/manufacturing/overview")
async def get_overview():
    """Get manufacturing overview."""
    try:
        # Get all KPIs
        sales_kpis = await get_sales_kpis()
        ops_kpis = await get_operations_kpis()
        finance_kpis = await get_finance_kpis()
        hr_kpis = await get_hr_kpis()
        
        return {
            "sales": sales_kpis,
            "operations": ops_kpis,
            "finance": finance_kpis,
            "hr": hr_kpis,
            "data_source": "manufacturing_tables",
            "connection_status": "live"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))