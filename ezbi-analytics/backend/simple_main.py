"""
Ultra-simple FastAPI app for Railway deployment
No complex dependencies, just direct PostgreSQL connection
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Create FastAPI app
app = FastAPI(
    title="EZBI Analytics Manufacturing API",
    description="Simple manufacturing intelligence API",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-fen55mqxa-philippe-beliveaus-projects.vercel.app",
        "https://ezbi-analytics.vercel.app", 
        "https://ezbi-analytics-*.vercel.app",
        "http://localhost:3000",
        "*"  # Allow all for testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:cnaAFVnruvkBnnzxCDxUEkfedixdbCHH@yamanote.proxy.rlwy.net:25571/railway"
)

def get_db():
    """Get database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "EZBI Analytics Manufacturing API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/manufacturing/sales/kpis",
            "/api/manufacturing/operations/kpis", 
            "/api/manufacturing/finance/kpis",
            "/api/manufacturing/overview"
        ]
    }

@app.get("/health")
def health():
    """Health check."""
    try:
        conn = get_db()
        if not conn:
            return {"status": "unhealthy", "database": "connection_failed"}
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected", 
            "test_query": "success"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }

@app.get("/api/manufacturing/sales/kpis")
def sales_kpis():
    """Sales KPIs from manufacturing tables."""
    try:
        conn = get_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Get customer count
        cursor.execute("SELECT COUNT(*) as count FROM sales_customers")
        customers = cursor.fetchone()['count']
        
        # Get invoice count and revenue
        cursor.execute("""
            SELECT COUNT(*) as count, 
                   COALESCE(SUM(CAST(amount AS DECIMAL)), 0) as revenue 
            FROM sales_invoices
        """)
        invoice_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "customers": customers,
            "invoices": invoice_data['count'],
            "total_revenue": float(invoice_data['revenue']),
            "avg_revenue_per_customer": float(invoice_data['revenue']) / customers if customers > 0 else 0,
            "data_source": "manufacturing_tables"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sales KPI error: {str(e)}")

@app.get("/api/manufacturing/operations/kpis") 
def operations_kpis():
    """Operations KPIs from manufacturing tables."""
    try:
        conn = get_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Get products
        cursor.execute("SELECT COUNT(*) as count FROM operations_products")
        products = cursor.fetchone()['count']
        
        # Get production orders
        cursor.execute("SELECT COUNT(*) as count FROM operations_production_orders")
        orders = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return {
            "products": products,
            "production_orders": orders,
            "active_orders": orders,
            "data_source": "manufacturing_tables"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operations KPI error: {str(e)}")

@app.get("/api/manufacturing/finance/kpis")
def finance_kpis():
    """Finance KPIs from manufacturing tables.""" 
    try:
        conn = get_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Get cash flow data
        cursor.execute("""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(CAST(amount AS DECIMAL)), 0) as total
            FROM finance_cash_ledger
        """)
        cash_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "transactions": cash_data['count'],
            "total_cash_flow": float(cash_data['total']),
            "avg_transaction": float(cash_data['total']) / cash_data['count'] if cash_data['count'] > 0 else 0,
            "data_source": "manufacturing_tables"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finance KPI error: {str(e)}")

@app.get("/api/manufacturing/overview")
def manufacturing_overview():
    """Complete manufacturing overview."""
    try:
        return {
            "sales": sales_kpis(),
            "operations": operations_kpis(), 
            "finance": finance_kpis(),
            "data_source": "manufacturing_tables",
            "status": "live_data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)