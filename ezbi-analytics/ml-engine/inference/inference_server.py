"""
Real-time Inference Server for Manufacturing ML Models
High-performance inference with caching and monitoring
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST

# Model imports
from models.prophet.prophet_model import ManufacturingProphetModel
from models.lstm.lstm_attention_model import AttentionLSTMModel
from models.ensemble.ensemble_model import ManufacturingEnsembleModel
from features.manufacturing_features import ManufacturingFeatureEngine
from config.ml_config import config

# Metrics
PREDICTION_COUNTER = Counter('ml_predictions_total', 'Total predictions made', ['model_type', 'status'])
PREDICTION_LATENCY = Histogram('ml_prediction_duration_seconds', 'Prediction latency')
CACHE_HIT_COUNTER = Counter('ml_cache_hits_total', 'Cache hits')
CACHE_MISS_COUNTER = Counter('ml_cache_misses_total', 'Cache misses')
ACTIVE_MODELS = Gauge('ml_active_models', 'Number of active models')
MODEL_LOAD_TIME = Histogram('ml_model_load_duration_seconds', 'Model loading time')

# Pydantic models
class PredictionRequest(BaseModel):
    """Request model for predictions"""
    data: Dict[str, Any] = Field(..., description="Input data for prediction")
    model_name: Optional[str] = Field(None, description="Specific model to use")
    include_uncertainty: bool = Field(False, description="Include uncertainty intervals")
    timestamp: Optional[datetime] = Field(None, description="Timestamp for prediction")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now()

class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction: float = Field(..., description="Predicted value")
    uncertainty_lower: Optional[float] = Field(None, description="Lower uncertainty bound")
    uncertainty_upper: Optional[float] = Field(None, description="Upper uncertainty bound")
    model_used: str = Field(..., description="Model used for prediction")
    confidence_score: float = Field(..., description="Confidence score")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    features_used: List[str] = Field(..., description="Features used for prediction")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    models_loaded: int = Field(..., description="Number of loaded models")
    cache_status: str = Field(..., description="Cache status")
    uptime_seconds: float = Field(..., description="Service uptime")
    version: str = Field(..., description="Service version")

class ModelManager:
    """Manager for ML models with caching and monitoring"""
    
    def __init__(self, 
                 models_dir: str = './models',
                 cache_ttl: int = 3600,
                 max_models: int = 10):
        """
        Initialize Model Manager
        
        Args:
            models_dir: Directory containing trained models
            cache_ttl: Cache time-to-live in seconds
            max_models: Maximum number of models to keep in memory
        """
        self.models_dir = Path(models_dir)
        self.cache_ttl = cache_ttl
        self.max_models = max_models
        
        # Model storage
        self.models = {}
        self.feature_engines = {}
        self.model_metadata = {}
        
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Cache for predictions
        self.redis_client = self._initialize_redis()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Model refresh thread
        self.refresh_thread = None
        self.refresh_interval = 3600  # 1 hour
        
        # Load models
        self._load_all_models()
        
        # Start refresh thread
        self._start_refresh_thread()
    
    def _initialize_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis client for caching"""
        try:
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            redis_client.ping()
            self.logger.info("Redis client initialized successfully")
            return redis_client
        except Exception as e:
            self.logger.warning(f"Redis initialization failed: {str(e)}")
            return None
    
    def _load_all_models(self):
        """Load all models from the models directory"""
        self.logger.info("Loading models from directory...")
        
        if not self.models_dir.exists():
            self.logger.warning(f"Models directory {self.models_dir} does not exist")
            return
        
        # Find model files
        model_files = []
        for pattern in ['*_model.h5', '*.pkl', '*_data.pkl']:
            model_files.extend(self.models_dir.glob(pattern))
        
        # Load models
        for model_file in model_files:
            try:
                self._load_model(model_file.stem)
            except Exception as e:
                self.logger.error(f"Failed to load model {model_file}: {str(e)}")
        
        ACTIVE_MODELS.set(len(self.models))
        self.logger.info(f"Loaded {len(self.models)} models")
    
    def _load_model(self, model_name: str):
        """Load a specific model"""
        start_time = time.time()
        
        try:
            # Determine model type from name or metadata
            if 'prophet' in model_name.lower():
                model = ManufacturingProphetModel()
                model.load_model(str(self.models_dir / model_name))
            elif 'lstm' in model_name.lower():
                model = AttentionLSTMModel()
                model.load_model(str(self.models_dir / model_name))
            elif 'ensemble' in model_name.lower():
                model = ManufacturingEnsembleModel()
                model.load_model(str(self.models_dir / model_name))
            else:
                # Try to load as joblib pickle
                model = joblib.load(self.models_dir / f"{model_name}.pkl")
            
            # Load feature engine
            feature_engine_path = self.models_dir / f"{model_name}.feature_engine.pkl"
            if feature_engine_path.exists():
                feature_engine = joblib.load(feature_engine_path)
                self.feature_engines[model_name] = feature_engine
            
            # Load metadata
            metadata_path = self.models_dir / f"{model_name}.pipeline_results.pkl"
            if metadata_path.exists():
                metadata = joblib.load(metadata_path)
                self.model_metadata[model_name] = metadata
            
            self.models[model_name] = model
            
            load_time = time.time() - start_time
            MODEL_LOAD_TIME.observe(load_time)
            
            self.logger.info(f"Model {model_name} loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise
    
    def _start_refresh_thread(self):
        """Start background thread for model refresh"""
        def refresh_models():
            while True:
                try:
                    time.sleep(self.refresh_interval)
                    self._refresh_models()
                except Exception as e:
                    self.logger.error(f"Error in model refresh thread: {str(e)}")
        
        self.refresh_thread = threading.Thread(target=refresh_models, daemon=True)
        self.refresh_thread.start()
        self.logger.info("Model refresh thread started")
    
    def _refresh_models(self):
        """Refresh models from disk"""
        self.logger.info("Refreshing models...")
        
        # Check for new models
        current_models = set(self.models.keys())
        disk_models = set()
        
        for model_file in self.models_dir.glob('*'):
            if model_file.suffix in ['.pkl', '.h5']:
                disk_models.add(model_file.stem)
        
        # Load new models
        new_models = disk_models - current_models
        for model_name in new_models:
            try:
                self._load_model(model_name)
                self.logger.info(f"Loaded new model: {model_name}")
            except Exception as e:
                self.logger.error(f"Failed to load new model {model_name}: {str(e)}")
        
        # Remove models that no longer exist
        removed_models = current_models - disk_models
        for model_name in removed_models:
            if model_name in self.models:
                del self.models[model_name]
                if model_name in self.feature_engines:
                    del self.feature_engines[model_name]
                if model_name in self.model_metadata:
                    del self.model_metadata[model_name]
                self.logger.info(f"Removed model: {model_name}")
        
        ACTIVE_MODELS.set(len(self.models))
    
    def get_model(self, model_name: str = None):
        """Get a specific model or the best available model"""
        if model_name:
            if model_name in self.models:
                return self.models[model_name], self.feature_engines.get(model_name)
            else:
                raise ValueError(f"Model {model_name} not found")
        
        # Return best model (ensemble if available, otherwise first available)
        if not self.models:
            raise ValueError("No models loaded")
        
        # Prefer ensemble models
        for name, model in self.models.items():
            if 'ensemble' in name.lower():
                return model, self.feature_engines.get(name)
        
        # Return first available
        first_model = next(iter(self.models.items()))
        return first_model[1], self.feature_engines.get(first_model[0])
    
    def predict(self, 
                data: Dict[str, Any], 
                model_name: str = None,
                include_uncertainty: bool = False) -> Dict[str, Any]:
        """Make prediction with caching"""
        
        # Create cache key
        cache_key = f"prediction:{model_name}:{hash(str(sorted(data.items())))}"
        
        # Check cache
        if self.redis_client:
            try:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    CACHE_HIT_COUNTER.inc()
                    return json.loads(cached_result)
            except Exception as e:
                self.logger.warning(f"Cache read error: {str(e)}")
        
        CACHE_MISS_COUNTER.inc()
        
        # Get model
        model, feature_engine = self.get_model(model_name)
        
        # Prepare data
        df = pd.DataFrame([data])
        
        # Set datetime index if not present
        if 'timestamp' in data:
            df.index = pd.to_datetime([data['timestamp']])
        else:
            df.index = pd.to_datetime([datetime.now()])
        
        # Apply feature engineering
        if feature_engine:
            df = feature_engine.transform(df)
        
        # Make prediction
        start_time = time.time()
        
        try:
            if include_uncertainty and hasattr(model, 'predict_with_uncertainty'):
                prediction, lower, upper = model.predict_with_uncertainty(df)
                prediction = prediction[0] if hasattr(prediction, '__len__') else prediction
                lower = lower[0] if hasattr(lower, '__len__') else lower
                upper = upper[0] if hasattr(upper, '__len__') else upper
            else:
                prediction = model.predict(df)
                prediction = prediction[0] if hasattr(prediction, '__len__') else prediction
                lower = upper = None
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(model, df, prediction)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                'prediction': float(prediction),
                'uncertainty_lower': float(lower) if lower is not None else None,
                'uncertainty_upper': float(upper) if upper is not None else None,
                'model_used': model_name or 'default',
                'confidence_score': confidence_score,
                'timestamp': datetime.now().isoformat(),
                'processing_time_ms': processing_time,
                'features_used': df.columns.tolist()
            }
            
            # Cache result
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(result))
                except Exception as e:
                    self.logger.warning(f"Cache write error: {str(e)}")
            
            PREDICTION_COUNTER.labels(model_type=model_name or 'default', status='success').inc()
            PREDICTION_LATENCY.observe(processing_time / 1000)
            
            return result
            
        except Exception as e:
            PREDICTION_COUNTER.labels(model_type=model_name or 'default', status='error').inc()
            raise
    
    def _calculate_confidence_score(self, model, df: pd.DataFrame, prediction: float) -> float:
        """Calculate confidence score for prediction"""
        try:
            # This is a simplified confidence calculation
            # In practice, you'd use model-specific methods
            
            # For ensemble models, use model agreement
            if hasattr(model, 'models'):
                predictions = []
                for sub_model in model.models.values():
                    try:
                        pred = sub_model.predict(df)
                        predictions.append(pred[0] if hasattr(pred, '__len__') else pred)
                    except:
                        continue
                
                if len(predictions) > 1:
                    # Calculate agreement (inverse of coefficient of variation)
                    cv = np.std(predictions) / (np.mean(predictions) + 1e-8)
                    confidence = 1.0 / (1.0 + cv)
                    return min(1.0, max(0.0, confidence))
            
            # Default confidence
            return 0.8
            
        except Exception as e:
            self.logger.warning(f"Confidence calculation error: {str(e)}")
            return 0.5
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        model_info = {}
        
        for name, model in self.models.items():
            info = {
                'type': type(model).__name__,
                'is_fitted': getattr(model, 'is_fitted', False),
                'feature_engine': name in self.feature_engines,
                'metadata': self.model_metadata.get(name, {})
            }
            
            # Add model-specific info
            if hasattr(model, 'performance_metrics'):
                info['performance_metrics'] = model.performance_metrics
            
            model_info[name] = info
        
        return model_info

# Initialize model manager
model_manager = ModelManager()

# FastAPI app
app = FastAPI(
    title="Manufacturing ML Inference API",
    description="Real-time inference API for manufacturing ML models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
start_time = time.time()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    cache_status = "connected" if model_manager.redis_client else "disconnected"
    
    return HealthResponse(
        status="healthy",
        models_loaded=len(model_manager.models),
        cache_status=cache_status,
        uptime_seconds=time.time() - start_time,
        version="1.0.0"
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make prediction endpoint"""
    try:
        result = model_manager.predict(
            data=request.data,
            model_name=request.model_name,
            include_uncertainty=request.include_uncertainty
        )
        
        return PredictionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
async def predict_batch(requests: List[PredictionRequest]):
    """Batch prediction endpoint"""
    try:
        results = []
        
        for request in requests:
            result = model_manager.predict(
                data=request.data,
                model_name=request.model_name,
                include_uncertainty=request.include_uncertainty
            )
            results.append(result)
        
        return {"predictions": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    """Get information about loaded models"""
    try:
        return model_manager.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/refresh")
async def refresh_models():
    """Manually refresh models"""
    try:
        model_manager._refresh_models()
        return {"message": "Models refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    registry = CollectorRegistry()
    # Add metrics to registry
    registry.register(PREDICTION_COUNTER)
    registry.register(PREDICTION_LATENCY)
    registry.register(CACHE_HIT_COUNTER)
    registry.register(CACHE_MISS_COUNTER)
    registry.register(ACTIVE_MODELS)
    registry.register(MODEL_LOAD_TIME)
    
    return generate_latest(registry)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Manufacturing ML Inference API",
        "version": "1.0.0",
        "models_loaded": len(model_manager.models),
        "docs": "/docs"
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))
    
    # Run server
    uvicorn.run(
        "inference_server:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        access_log=True
    )