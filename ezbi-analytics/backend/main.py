"""
EZBI Analytics Manufacturing API - Railway Deployment
Ultra-simple FastAPI app with no complex dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Create FastAPI app
app = FastAPI(
    title="EZBI Analytics Manufacturing API",
    description="Manufacturing intelligence platform - Railway deployment",
    version="1.0.1"
)

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-fen55mqxa-philippe-beliveaus-projects.vercel.app",
        "https://ezbi-analytics.vercel.app", 
        "https://ezbi-analytics-*.vercel.app",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Database connection from Railway environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:cnaAFVnruvkBnnzxCDxUEkfedixdbCHH@yamanote.proxy.rlwy.net:25571/railway"
)

def get_db():
    """Get database connection with error handling."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        print(f"PostgreSQL connection error: {e}")
        return None
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "EZBI Analytics Manufacturing API",
        "status": "online",
        "version": "1.0.0",
        "deployment": "railway",
        "database": "postgresql",
        "endpoints": {
            "health": "/health",
            "manufacturing_overview": "/api/manufacturing/overview",
            "sales_kpis": "/api/manufacturing/sales/kpis",
            "operations_kpis": "/api/manufacturing/operations/kpis",
            "finance_kpis": "/api/manufacturing/finance/kpis",
            "hr_kpis": "/api/manufacturing/hr/kpis"
        }
    }

@app.get("/health")
def health():
    """Health check with database connectivity test."""
    try:
        conn = get_db()
        if not conn:
            return {
                "status": "unhealthy", 
                "database": "connection_failed",
                "error": "Could not connect to PostgreSQL"
            }
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()['table_count']
        
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "postgresql_version": version[0][:50] if version else "unknown",
            "manufacturing_tables": table_count,
            "deployment": "railway_success"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }

@app.get("/api/manufacturing/sales/kpis")
def sales_kpis():
    """Sales KPIs from manufacturing database."""
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
            "data_source": "manufacturing_tables",
            "table_status": "live_data"
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sales KPI error: {str(e)}")

@app.get("/api/manufacturing/operations/kpis") 
def operations_kpis():
    """Operations KPIs from manufacturing database."""
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
            "data_source": "manufacturing_tables",
            "table_status": "live_data"
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operations KPI error: {str(e)}")

@app.get("/api/manufacturing/finance/kpis")
def finance_kpis():
    """Finance KPIs from manufacturing database.""" 
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
            "data_source": "manufacturing_tables",
            "table_status": "live_data"
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finance KPI error: {str(e)}")

@app.get("/api/manufacturing/hr/kpis")
def hr_kpis():
    """HR KPIs from manufacturing database."""
    try:
        conn = get_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Get employee count
        cursor.execute("SELECT COUNT(*) as count FROM hr_employees")
        employees = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return {
            "employees": employees,
            "active_employees": employees,
            "data_source": "manufacturing_tables",
            "table_status": "live_data"
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HR KPI error: {str(e)}")

@app.get("/api/manufacturing/overview")
def manufacturing_overview():
    """Complete manufacturing dashboard overview."""
    try:
        return {
            "sales": sales_kpis(),
            "operations": operations_kpis(), 
            "finance": finance_kpis(),
            "hr": hr_kpis(),
            "data_source": "manufacturing_tables",
            "status": "live_data",
            "deployment": "railway_postgresql",
            "last_updated": "real_time"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview error: {str(e)}")

# Additional endpoint for frontend compatibility
@app.get("/api/manufacturing/all")
def manufacturing_all():
    """All manufacturing data in one response."""
    return manufacturing_overview()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting EZBI Analytics API on port {port}")
    print(f"Database: {DATABASE_URL[:50]}...")
    uvicorn.run(app, host="0.0.0.0", port=port)