#!/usr/bin/env python3
"""
Manufacturing Data Simulator - Main Application
Railway FastAPI Service for Daily Business Simulation
"""

import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from simulator import ManufacturingSimulator
from database import get_database_connection, init_database
from exporters import ExcelExporter, SlackNotifier
from models import SimulationReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Manufacturing Data Simulator",
    description="Production-grade synthetic data generator for manufacturing business",
    version="1.0.0"
)

# CORS configuration for EZBI platform integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure with your EZBI platform domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
simulator = None
scheduler = AsyncIOScheduler()
excel_exporter = ExcelExporter()
slack_notifier = SlackNotifier(webhook_url=os.getenv("SLACK_WEBHOOK_URL"))

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
SIMULATION_SCHEDULE = os.getenv("SIMULATION_SCHEDULE", "0 6 * * *")  # Daily at 6 AM UTC
EXCEL_EXPORT_PATH = "/app/exports"

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global simulator
    
    logger.info("Starting Manufacturing Data Simulator...")
    
    # Initialize database connection
    await init_database(DATABASE_URL)
    
    # Initialize simulator
    simulator = ManufacturingSimulator(DATABASE_URL)
    
    # Ensure export directory exists
    os.makedirs(EXCEL_EXPORT_PATH, exist_ok=True)
    
    # Schedule daily simulation
    scheduler.add_job(
        run_daily_simulation,
        CronTrigger.from_crontab(SIMULATION_SCHEDULE),
        id="daily_simulation",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Daily simulation scheduled: {SIMULATION_SCHEDULE}")
    
    # Run initial simulation if requested
    if os.getenv("RUN_INITIAL_SIMULATION", "false").lower() == "true":
        await run_daily_simulation()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    scheduler.shutdown()
    logger.info("Manufacturing Data Simulator shutdown complete")

# ==============================
# API ENDPOINTS
# ==============================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Manufacturing Data Simulator",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check for Railway monitoring"""
    try:
        # Test database connection
        conn = await get_database_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "scheduler": "running" if scheduler.running else "stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/simulate/manual")
async def manual_simulation(background_tasks: BackgroundTasks):
    """Trigger manual simulation (for testing)"""
    background_tasks.add_task(run_daily_simulation)
    return {
        "message": "Manual simulation started",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/simulate/status")
async def simulation_status():
    """Get current simulation status"""
    return {
        "next_scheduled_run": scheduler.get_job("daily_simulation").next_run_time.isoformat() if scheduler.get_job("daily_simulation") else None,
        "schedule": SIMULATION_SCHEDULE,
        "last_run": "N/A",  # TODO: Implement run tracking
        "status": "active"
    }

@app.get("/data/summary")
async def data_summary():
    """Get current data summary for EZBI platform"""
    if not simulator:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    try:
        summary = await simulator.get_data_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get data summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exports/excel/latest")
async def download_latest_excel():
    """Download the latest Excel export"""
    try:
        latest_file = excel_exporter.get_latest_export_file(EXCEL_EXPORT_PATH)
        if not latest_file:
            raise HTTPException(status_code=404, detail="No Excel exports found")
        
        return FileResponse(
            latest_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(latest_file)
        )
    except Exception as e:
        logger.error(f"Failed to serve Excel file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exports/excel/list")
async def list_excel_exports():
    """List all available Excel exports"""
    try:
        files = excel_exporter.list_export_files(EXCEL_EXPORT_PATH)
        return {"files": files}
    except Exception as e:
        logger.error(f"Failed to list Excel files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================
# BACKGROUND TASKS
# ==============================

async def run_daily_simulation():
    """Execute the daily business simulation"""
    logger.info("Starting daily simulation...")
    
    try:
        # Run simulation
        report = await simulator.run_daily_simulation()
        
        # Export to Excel
        excel_file = await excel_exporter.export_daily_data(
            simulator.db_connection,
            EXCEL_EXPORT_PATH,
            report.simulation_date
        )
        
        # Send Slack notification
        await slack_notifier.send_daily_summary(report, excel_file)
        
        logger.info(f"Daily simulation completed successfully: {report.total_transactions} transactions generated")
        
        return report
        
    except Exception as e:
        logger.error(f"Daily simulation failed: {e}")
        # Send error notification to Slack
        await slack_notifier.send_error_notification(str(e))
        raise

# ==============================
# RAILWAY DEPLOYMENT
# ==============================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )