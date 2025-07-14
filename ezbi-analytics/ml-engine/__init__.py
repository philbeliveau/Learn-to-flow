"""
EZBI Analytics ML Engine
Manufacturing-focused machine learning prediction engine

This package provides a comprehensive ML solution for manufacturing forecasting
with French business calendar integration and specialized manufacturing features.
"""

from .ml_engine import MLEngineOrchestrator
from .config.ml_config import config

# Model imports
from .models.prophet.prophet_model import ManufacturingProphetModel
from .models.lstm.lstm_attention_model import AttentionLSTMModel
from .models.ensemble.ensemble_model import ManufacturingEnsembleModel

# Feature engineering
from .features.manufacturing_features import ManufacturingFeatureEngine
from .features.extractors.time_features import TimeFeatureExtractor

# Training and inference
from .training.ml_training_pipeline import MLTrainingPipeline
from .inference.inference_server import ModelManager
from .monitoring.model_monitor import ModelMonitor

__version__ = "1.0.0"
__author__ = "EZBI Analytics Team"
__description__ = "Manufacturing ML Engine with Prophet, LSTM, and Ensemble models"

__all__ = [
    "MLEngineOrchestrator",
    "ManufacturingProphetModel",
    "AttentionLSTMModel", 
    "ManufacturingEnsembleModel",
    "ManufacturingFeatureEngine",
    "TimeFeatureExtractor",
    "MLTrainingPipeline",
    "ModelManager",
    "ModelMonitor",
    "config"
]