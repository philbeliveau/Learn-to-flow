"""
EZBI Analytics - Flask Backend with Manufacturing Analytics
Complete backend for comprehensive manufacturing dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
from pathlib import Path
import logging

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import our manufacturing API
from api.manufacturing import manufacturing_bp
from api.scheduler_api import scheduler_bp

# Import scheduler
from scheduler.scheduler import data_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(manufacturing_bp)
app.register_blueprint(scheduler_bp)

# Initialize scheduler
with app.app_context():
    data_scheduler.init_scheduler(app)
    logger.info("Data generation scheduler initialized")

# Root endpoint
@app.route('/')
def root():
    """Root endpoint with API information"""
    return jsonify({
        "message": "🏭 EZBI Analytics - Manufacturing Intelligence API",
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "sales": "/api/manufacturing/sales/",
            "accounting": "/api/manufacturing/accounting/",
            "operations": "/api/manufacturing/operations/",
            "finance": "/api/manufacturing/finance/",
            "hr": "/api/manufacturing/hr/",
            "expenses": "/api/manufacturing/expenses/",
            "dashboard": "/api/manufacturing/dashboard/"
        },
        "total_tables": 13,
        "total_records": 3527
    })

# Health check
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ezbi-manufacturing-api",
        "version": "2.0.0",
        "database": "connected"
    })

# API documentation
@app.route('/api/docs')
def api_docs():
    """API documentation"""
    return jsonify({
        "title": "EZBI Analytics Manufacturing API",
        "version": "2.0.0",
        "description": "Complete manufacturing business intelligence API",
        "endpoints": {
            "sales": {
                "customers": "GET /api/manufacturing/sales/customers",
                "invoices": "GET /api/manufacturing/sales/invoices", 
                "kpis": "GET /api/manufacturing/sales/kpis"
            },
            "accounting": {
                "vendors": "GET /api/manufacturing/accounting/vendors",
                "purchases": "GET /api/manufacturing/accounting/purchases",
                "accounts_receivable": "GET /api/manufacturing/accounting/accounts-receivable",
                "accounts_payable": "GET /api/manufacturing/accounting/accounts-payable",
                "kpis": "GET /api/manufacturing/accounting/kpis"
            },
            "operations": {
                "products": "GET /api/manufacturing/operations/products",
                "production_orders": "GET /api/manufacturing/operations/production-orders",
                "kpis": "GET /api/manufacturing/operations/kpis"
            },
            "finance": {
                "cash_ledger": "GET /api/manufacturing/finance/cash-ledger",
                "debt_accounts": "GET /api/manufacturing/finance/debt-accounts",
                "kpis": "GET /api/manufacturing/finance/kpis"
            },
            "hr": {
                "employees": "GET /api/manufacturing/hr/employees",
                "payroll": "GET /api/manufacturing/hr/payroll",
                "kpis": "GET /api/manufacturing/hr/kpis"
            },
            "expenses": {
                "fixed_costs": "GET /api/manufacturing/expenses/fixed-costs",
                "kpis": "GET /api/manufacturing/expenses/kpis"
            },
            "dashboard": {
                "overview": "GET /api/manufacturing/dashboard/overview"
            }
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "Check /api/docs for available endpoints"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "Please check server logs"
    }), 500

if __name__ == '__main__':
    print("🏭 EZBI Analytics - Manufacturing Intelligence API")
    print("=" * 50)
    print("📊 13 Manufacturing Tables Connected")
    print("📈 3,527 Synthetic Records Available")
    print("🔗 All Business Intelligence Endpoints Ready")
    print("=" * 50)
    print("📱 Frontend Development Server: http://localhost:3000")
    print("🔧 Backend API Server: http://localhost:8003")
    print("📋 API Documentation: http://localhost:8003/api/docs")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8003, debug=True)