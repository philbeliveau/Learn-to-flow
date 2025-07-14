"""
EZBI Analytics ML Engine
Main orchestrator for the complete machine learning prediction system
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import click

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ML Engine imports
from models.prophet.prophet_model import ManufacturingProphetModel
from models.lstm.lstm_attention_model import AttentionLSTMModel
from models.ensemble.ensemble_model import ManufacturingEnsembleModel
from features.manufacturing_features import ManufacturingFeatureEngine
from training.ml_training_pipeline import MLTrainingPipeline
from inference.inference_server import ModelManager, PredictionRequest, PredictionResponse
from monitoring.model_monitor import ModelMonitor
from config.ml_config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLEngineOrchestrator:
    """Main orchestrator for the ML engine"""
    
    def __init__(self, 
                 models_dir: str = './models',
                 data_dir: str = './data',
                 enable_monitoring: bool = True,
                 enable_inference: bool = True,
                 enable_training: bool = True):
        """
        Initialize ML Engine Orchestrator
        
        Args:
            models_dir: Directory for saved models
            data_dir: Directory for training data
            enable_monitoring: Enable model monitoring
            enable_inference: Enable inference server
            enable_training: Enable training capabilities
        """
        self.models_dir = Path(models_dir)
        self.data_dir = Path(data_dir)
        self.enable_monitoring = enable_monitoring
        self.enable_inference = enable_inference
        self.enable_training = enable_training
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.model_manager = None
        self.model_monitor = None
        self.training_pipeline = None
        
        # State
        self.is_running = False
        self.background_tasks = []
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize ML engine components"""
        logger.info("Initializing ML Engine components...")
        
        # Model manager for inference
        if self.enable_inference:
            self.model_manager = ModelManager(
                models_dir=str(self.models_dir),
                cache_ttl=config.inference['cache_ttl'],
                max_models=10
            )
            logger.info("Model manager initialized")
        
        # Model monitor
        if self.enable_monitoring:
            self.model_monitor = ModelMonitor(
                models_dir=str(self.models_dir),
                monitoring_db=str(self.models_dir / 'monitoring.db'),
                monitoring_interval=300,  # 5 minutes
                enable_alerts=True,
                enable_auto_retrain=True
            )
            logger.info("Model monitor initialized")
        
        # Training pipeline
        if self.enable_training:
            self.training_pipeline = MLTrainingPipeline(
                model_type='ensemble',
                output_dir=str(self.models_dir),
                enable_hyperparameter_tuning=True,
                enable_cross_validation=True
            )
            logger.info("Training pipeline initialized")
    
    def train_model(self, 
                   data: pd.DataFrame,
                   target_column: str,
                   model_type: str = 'ensemble',
                   model_name: str = None) -> Dict[str, Any]:
        """
        Train a new model
        
        Args:
            data: Training data with datetime index
            target_column: Target column name
            model_type: Type of model to train
            model_name: Name for the trained model
            
        Returns:
            Training results
        """
        if not self.enable_training:
            raise ValueError("Training is disabled")
        
        logger.info(f"Starting model training: {model_type}")
        
        # Create training pipeline
        pipeline = MLTrainingPipeline(
            model_type=model_type,
            output_dir=str(self.models_dir),
            enable_hyperparameter_tuning=True,
            enable_cross_validation=True
        )
        
        # Run training
        results = pipeline.run_full_pipeline(
            data=data,
            target_column=target_column,
            model_name=model_name or f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Refresh model manager
        if self.model_manager:
            self.model_manager._refresh_models()
        
        logger.info(f"Model training completed: {results['model_path']}")
        
        return results
    
    def predict(self, 
               data: Dict[str, Any],
               model_name: str = None,
               include_uncertainty: bool = False) -> Dict[str, Any]:
        """
        Make prediction
        
        Args:
            data: Input data for prediction
            model_name: Specific model to use
            include_uncertainty: Include uncertainty intervals
            
        Returns:
            Prediction results
        """
        if not self.enable_inference or not self.model_manager:
            raise ValueError("Inference is disabled")
        
        return self.model_manager.predict(
            data=data,
            model_name=model_name,
            include_uncertainty=include_uncertainty
        )
    
    def get_model_performance(self, model_name: str = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get model performance metrics
        
        Args:
            model_name: Specific model name
            hours: Time window in hours
            
        Returns:
            Performance metrics
        """
        if not self.enable_monitoring or not self.model_monitor:
            raise ValueError("Monitoring is disabled")
        
        if model_name:
            return self.model_monitor.get_model_metrics_history(model_name, hours).to_dict('records')
        else:
            return self.model_monitor.generate_monitoring_report(hours)
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models"""
        if not self.model_manager:
            return {}
        
        return self.model_manager.get_model_info()
    
    def create_sample_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Create sample manufacturing data for testing"""
        logger.info(f"Creating sample data with {n_samples} samples")
        
        # Generate time series
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=n_samples // 24),
            periods=n_samples,
            freq='H'
        )
        
        # Generate sample manufacturing data
        np.random.seed(42)
        
        # Base production with trend and seasonality
        base_production = 100 + np.arange(n_samples) * 0.01  # Slight upward trend
        
        # Add seasonality
        daily_pattern = 20 * np.sin(2 * np.pi * np.arange(n_samples) / 24)
        weekly_pattern = 10 * np.sin(2 * np.pi * np.arange(n_samples) / (24 * 7))
        
        # Add noise
        noise = np.random.normal(0, 5, n_samples)
        
        production_volume = base_production + daily_pattern + weekly_pattern + noise
        production_volume = np.maximum(production_volume, 0)  # Ensure non-negative
        
        # Generate correlated features
        efficiency_rate = 0.85 + 0.1 * np.sin(2 * np.pi * np.arange(n_samples) / 24) + np.random.normal(0, 0.05, n_samples)
        efficiency_rate = np.clip(efficiency_rate, 0.5, 1.0)
        
        machine_utilization = 0.8 + 0.15 * np.sin(2 * np.pi * np.arange(n_samples) / (24 * 7)) + np.random.normal(0, 0.1, n_samples)
        machine_utilization = np.clip(machine_utilization, 0.3, 1.0)
        
        quality_score = 0.95 - 0.05 * np.sin(2 * np.pi * np.arange(n_samples) / (24 * 30)) + np.random.normal(0, 0.02, n_samples)
        quality_score = np.clip(quality_score, 0.7, 1.0)
        
        temperature = 22 + 5 * np.sin(2 * np.pi * np.arange(n_samples) / (24 * 365)) + np.random.normal(0, 2, n_samples)
        
        # Create DataFrame
        data = pd.DataFrame({
            'production_volume': production_volume,
            'efficiency_rate': efficiency_rate,
            'machine_utilization': machine_utilization,
            'quality_score': quality_score,
            'temperature': temperature,
            'humidity': 50 + np.random.normal(0, 10, n_samples),
            'pressure': 1013 + np.random.normal(0, 5, n_samples),
            'operator_count': np.random.choice([2, 3, 4], n_samples),
            'maintenance_hours': np.random.exponential(0.5, n_samples),
            'raw_material_price': 100 + np.random.normal(0, 5, n_samples),
            'energy_cost': 0.12 + np.random.normal(0, 0.02, n_samples),
            'order_backlog': np.random.poisson(50, n_samples),
            'inventory_level': 1000 + np.random.normal(0, 100, n_samples)
        }, index=dates)
        
        return data
    
    def run_demo(self):
        """Run demonstration of the ML engine"""
        logger.info("Starting ML Engine demo...")
        
        # Create sample data
        data = self.create_sample_data(2000)
        
        # Train ensemble model
        logger.info("Training ensemble model...")
        training_results = self.train_model(
            data=data,
            target_column='production_volume',
            model_type='ensemble',
            model_name='demo_ensemble'
        )
        
        logger.info(f"Training completed with R2 score: {training_results['test_metrics']['r2']:.3f}")
        
        # Make sample predictions
        logger.info("Making sample predictions...")
        
        sample_data = {
            'efficiency_rate': 0.85,
            'machine_utilization': 0.8,
            'quality_score': 0.95,
            'temperature': 22.0,
            'humidity': 50.0,
            'pressure': 1013.0,
            'operator_count': 3,
            'maintenance_hours': 0.5,
            'raw_material_price': 100.0,
            'energy_cost': 0.12,
            'order_backlog': 50,
            'inventory_level': 1000.0
        }
        
        prediction = self.predict(sample_data, include_uncertainty=True)
        
        logger.info(f"Sample prediction: {prediction['prediction']:.2f}")
        logger.info(f"Uncertainty: [{prediction['uncertainty_lower']:.2f}, {prediction['uncertainty_upper']:.2f}]")
        
        # Display model information
        models = self.get_available_models()
        logger.info(f"Available models: {list(models.keys())}")
        
        logger.info("Demo completed successfully!")
        
        return {
            'training_results': training_results,
            'sample_prediction': prediction,
            'available_models': models
        }

# FastAPI app for REST API
def create_app() -> FastAPI:
    """Create FastAPI application"""
    
    app = FastAPI(
        title="EZBI Analytics ML Engine",
        description="Manufacturing ML Engine with Prophet, LSTM, and Ensemble models",
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
    
    # Initialize ML Engine
    ml_engine = MLEngineOrchestrator(
        models_dir=os.getenv('MODELS_DIR', './models'),
        data_dir=os.getenv('DATA_DIR', './data'),
        enable_monitoring=True,
        enable_inference=True,
        enable_training=True
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "EZBI Analytics ML Engine",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "predict": "/predict",
                "models": "/models",
                "train": "/train",
                "performance": "/performance",
                "demo": "/demo"
            }
        }
    
    @app.post("/predict")
    async def predict(request: PredictionRequest):
        """Make prediction endpoint"""
        try:
            result = ml_engine.predict(
                data=request.data,
                model_name=request.model_name,
                include_uncertainty=request.include_uncertainty
            )
            return PredictionResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/models")
    async def get_models():
        """Get available models"""
        try:
            return ml_engine.get_available_models()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/train")
    async def train_model(background_tasks: BackgroundTasks,
                         model_type: str = 'ensemble',
                         target_column: str = 'production_volume'):
        """Train new model endpoint"""
        try:
            # Create sample data for training
            data = ml_engine.create_sample_data(1000)
            
            # Run training in background
            background_tasks.add_task(
                ml_engine.train_model,
                data=data,
                target_column=target_column,
                model_type=model_type
            )
            
            return {"message": "Training started in background"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/performance")
    async def get_performance(model_name: str = None, hours: int = 24):
        """Get model performance metrics"""
        try:
            return ml_engine.get_model_performance(model_name, hours)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/demo")
    async def run_demo():
        """Run ML Engine demo"""
        try:
            return ml_engine.run_demo()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

# CLI Interface
@click.group()
def cli():
    """EZBI Analytics ML Engine CLI"""
    pass

@cli.command()
@click.option('--data-file', required=True, help='Path to training data CSV file')
@click.option('--target-column', required=True, help='Target column name')
@click.option('--model-type', default='ensemble', help='Model type (prophet, lstm, ensemble)')
@click.option('--model-name', help='Model name')
def train(data_file, target_column, model_type, model_name):
    """Train a new model"""
    try:
        # Load data
        data = pd.read_csv(data_file, index_col=0, parse_dates=True)
        
        # Initialize ML engine
        ml_engine = MLEngineOrchestrator()
        
        # Train model
        results = ml_engine.train_model(
            data=data,
            target_column=target_column,
            model_type=model_type,
            model_name=model_name
        )
        
        click.echo(f"Training completed successfully!")
        click.echo(f"Model saved to: {results['model_path']}")
        click.echo(f"Test R2 score: {results['test_metrics']['r2']:.3f}")
        
    except Exception as e:
        click.echo(f"Training failed: {str(e)}", err=True)

@cli.command()
@click.option('--model-name', help='Model name for prediction')
@click.option('--data', required=True, help='JSON string with input data')
def predict(model_name, data):
    """Make a prediction"""
    try:
        import json
        
        # Parse input data
        input_data = json.loads(data)
        
        # Initialize ML engine
        ml_engine = MLEngineOrchestrator()
        
        # Make prediction
        result = ml_engine.predict(
            data=input_data,
            model_name=model_name,
            include_uncertainty=True
        )
        
        click.echo(f"Prediction: {result['prediction']:.2f}")
        click.echo(f"Confidence: {result['confidence_score']:.3f}")
        click.echo(f"Model used: {result['model_used']}")
        
    except Exception as e:
        click.echo(f"Prediction failed: {str(e)}", err=True)

@cli.command()
def demo():
    """Run ML Engine demo"""
    try:
        ml_engine = MLEngineOrchestrator()
        results = ml_engine.run_demo()
        
        click.echo("Demo completed successfully!")
        click.echo(f"Training R2 score: {results['training_results']['test_metrics']['r2']:.3f}")
        click.echo(f"Sample prediction: {results['sample_prediction']['prediction']:.2f}")
        
    except Exception as e:
        click.echo(f"Demo failed: {str(e)}", err=True)

@cli.command()
@click.option('--host', default='0.0.0.0', help='Server host')
@click.option('--port', default=8000, help='Server port')
def serve(host, port):
    """Start the inference server"""
    app = create_app()
    uvicorn.run(app, host=host, port=port, reload=False)

if __name__ == "__main__":
    cli()