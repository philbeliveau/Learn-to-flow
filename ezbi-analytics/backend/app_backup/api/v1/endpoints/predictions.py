"""
API endpoints for ML predictions and model management.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.ml_service import ml_service
from app.services.data_ingestion import data_ingestion_service
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

class PredictionRequest(BaseModel):
    """Request model for prediction generation."""
    horizon_days: int = Field(default=30, ge=1, le=365, description="Prediction horizon in days")
    model_type: str = Field(default="cash_flow", description="Type of prediction model")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional input data")

class TrainingRequest(BaseModel):
    """Request model for model training."""
    model_type: str = Field(..., description="Type of model to train")
    hyperparameters: Optional[Dict[str, Any]] = Field(default=None, description="Model hyperparameters")
    data_source: str = Field(default="database", description="Data source for training")

class PredictionResponse(BaseModel):
    """Response model for predictions."""
    prediction_id: str
    model_id: str
    prediction_type: str
    horizon_days: int
    predictions: List[Dict[str, Any]]
    confidence_intervals: Dict[str, float]
    feature_importance: Dict[str, float]
    explanation: str
    generated_at: str

@router.post("/predict/cash-flow", response_model=PredictionResponse)
async def predict_cash_flow(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate cash flow predictions using trained ML models.
    
    This endpoint uses ensemble models (Prophet + LSTM) trained on real manufacturing
    and financial data to predict future cash flows with confidence intervals.
    """
    try:
        logger.info(f"Generating cash flow prediction for user {current_user.id}")
        
        # Get the latest active cash flow model
        model_id = await get_latest_model_id("cash_flow")
        if not model_id:
            # Train a new model if none exists
            logger.info("No trained model found, training new cash flow model...")
            training_result = await ml_service.train_cash_flow_prediction_model()
            model_id = training_result['model_id']
        
        # Generate predictions
        prediction_result = await ml_service.predict_cash_flow(
            model_id=model_id,
            horizon_days=request.horizon_days,
            input_data=request.input_data
        )
        
        return PredictionResponse(
            prediction_id=prediction_result.get('id', 'pred_' + datetime.now().strftime('%Y%m%d_%H%M%S')),
            model_id=model_id,
            prediction_type=prediction_result['prediction_type'],
            horizon_days=prediction_result['horizon_days'],
            predictions=prediction_result['predictions'],
            confidence_intervals=prediction_result['confidence_intervals'],
            feature_importance=prediction_result['feature_importance'],
            explanation=prediction_result['explanation'],
            generated_at=prediction_result['timestamp']
        )
        
    except Exception as e:
        logger.error(f"Error generating cash flow prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction generation failed: {str(e)}")

@router.post("/models/train")
async def train_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Train a new machine learning model with real data.
    
    Supports training cash flow prediction models using real Kaggle datasets
    integrated with manufacturing process data.
    """
    try:
        logger.info(f"Starting model training: {request.model_type}")
        
        if request.model_type == "cash_flow":
            # Train cash flow prediction model
            training_result = await ml_service.train_cash_flow_prediction_model()
            
            return {
                "status": "training_completed",
                "model_id": training_result['model_id'],
                "metrics": training_result['metrics'],
                "training_samples": training_result['training_samples'],
                "message": "Cash flow prediction model trained successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model type: {request.model_type}")
        
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@router.get("/models")
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query("active", description="Filter by model status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List available ML models with their metadata and performance metrics.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            query = "SELECT * FROM ml_models WHERE status = :status"
            params = {"status": status}
            
            if model_type:
                query += " AND model_type LIKE :model_type"
                params["model_type"] = f"%{model_type}%"
            
            query += " ORDER BY created_at DESC"
            
            result = await session.execute(text(query), params)
            models = [dict(row._mapping) for row in result.fetchall()]
            
            return {
                "models": models,
                "total": len(models)
            }
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.get("/models/{model_id}")
async def get_model_details(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific ML model.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            query = "SELECT * FROM ml_models WHERE id = :model_id"
            result = await session.execute(text(query), {"model_id": model_id})
            model = result.fetchone()
            
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            return dict(model._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")

@router.get("/predictions")
async def list_predictions(
    limit: int = Query(50, ge=1, le=200, description="Number of predictions to return"),
    model_type: Optional[str] = Query(None, description="Filter by prediction type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List recent predictions with their results and confidence scores.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            query = """
            SELECT id, model_id, model_name, prediction_type, prediction_horizon,
                   confidence_score, timestamp, processing_time_ms
            FROM prediction_results
            WHERE user_id = :user_id OR user_id IS NULL
            """
            params = {"user_id": current_user.id}
            
            if model_type:
                query += " AND prediction_type = :model_type"
                params["model_type"] = model_type
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            result = await session.execute(text(query), params)
            predictions = [dict(row._mapping) for row in result.fetchall()]
            
            return {
                "predictions": predictions,
                "total": len(predictions)
            }
        
    except Exception as e:
        logger.error(f"Error listing predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list predictions: {str(e)}")

@router.get("/predictions/{prediction_id}")
async def get_prediction_details(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed results for a specific prediction.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            query = "SELECT * FROM prediction_results WHERE id = :prediction_id"
            result = await session.execute(text(query), {"prediction_id": prediction_id})
            prediction = result.fetchone()
            
            if not prediction:
                raise HTTPException(status_code=404, detail="Prediction not found")
            
            return dict(prediction._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get prediction details: {str(e)}")

@router.post("/data/ingest")
async def ingest_kaggle_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest real manufacturing and cash flow data from Kaggle datasets.
    
    This endpoint processes the downloaded Kaggle datasets and stores
    the structured data in the database for ML model training.
    """
    try:
        logger.info(f"Starting data ingestion for user {current_user.id}")
        
        # Start data ingestion in background
        background_tasks.add_task(run_data_ingestion)
        
        return {
            "status": "ingestion_started",
            "message": "Data ingestion started in background. Check status with /data/status endpoint."
        }
        
    except Exception as e:
        logger.error(f"Error starting data ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data ingestion failed to start: {str(e)}")

@router.get("/data/status")
async def get_data_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of data ingestion and available datasets.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            # Check manufacturing data
            manufacturing_query = "SELECT COUNT(*) as count FROM manufacturing_data"
            manufacturing_result = await session.execute(text(manufacturing_query))
            manufacturing_count = manufacturing_result.scalar()
            
            # Check cash flow data
            cash_flow_query = "SELECT COUNT(*) as count FROM cash_flow_data"
            cash_flow_result = await session.execute(text(cash_flow_query))
            cash_flow_count = cash_flow_result.scalar()
            
            # Check latest data timestamps
            latest_manufacturing_query = "SELECT MAX(timestamp) as latest FROM manufacturing_data"
            latest_manufacturing_result = await session.execute(text(latest_manufacturing_query))
            latest_manufacturing = latest_manufacturing_result.scalar()
            
            latest_cash_flow_query = "SELECT MAX(date) as latest FROM cash_flow_data"
            latest_cash_flow_result = await session.execute(text(latest_cash_flow_query))
            latest_cash_flow = latest_cash_flow_result.scalar()
            
            return {
                "manufacturing_data": {
                    "total_records": manufacturing_count,
                    "latest_timestamp": latest_manufacturing.isoformat() if latest_manufacturing else None
                },
                "cash_flow_data": {
                    "total_records": cash_flow_count,
                    "latest_timestamp": latest_cash_flow.isoformat() if latest_cash_flow else None
                },
                "status": "ready" if manufacturing_count > 0 and cash_flow_count > 0 else "no_data"
            }
        
    except Exception as e:
        logger.error(f"Error getting data status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get data status: {str(e)}")

# Helper functions

async def get_latest_model_id(model_type: str) -> Optional[str]:
    """Get the latest active model ID for a given type."""
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            query = """
            SELECT id FROM ml_models 
            WHERE status = 'active' AND model_type LIKE :model_type
            ORDER BY created_at DESC 
            LIMIT 1
            """
            result = await session.execute(text(query), {"model_type": f"%{model_type}%"})
            row = result.fetchone()
            return row[0] if row else None
            
    except Exception as e:
        logger.error(f"Error getting latest model ID: {str(e)}")
        return None

async def run_data_ingestion():
    """Background task for data ingestion."""
    try:
        logger.info("Starting background data ingestion...")
        result = await data_ingestion_service.ingest_all_datasets()
        logger.info(f"Data ingestion completed: {result}")
    except Exception as e:
        logger.error(f"Background data ingestion failed: {str(e)}")