"""
Database models for manufacturing and cash flow data.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
from datetime import datetime

class ManufacturingData(Base):
    """Model for manufacturing process data."""
    __tablename__ = "manufacturing_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, index=True)
    machine_id = Column(String, nullable=False, index=True)
    
    # Production metrics
    production_quantity = Column(Float, default=0)
    quality_score = Column(Float, default=0)  # 0-100
    efficiency = Column(Float, default=0)  # 0-100
    
    # Operational metrics
    energy_consumption = Column(Float, default=0)  # kWh
    maintenance_indicator = Column(Float, default=0)  # 0-100
    
    # Sensor data
    temperature = Column(Float, default=0)
    pressure = Column(Float, default=0)
    vibration = Column(Float, default=0)
    
    # Raw sensor data (JSON)
    raw_data = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ManufacturingData(id={self.id}, machine={self.machine_id}, timestamp={self.timestamp})>"

class CashFlowData(Base):
    """Model for cash flow data."""
    __tablename__ = "cash_flow_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime, nullable=False, index=True)
    company_identifier = Column(String, nullable=False, index=True)
    
    # Cash flow components
    net_cash_flow = Column(Float, default=0)
    operating_cash_flow = Column(Float, default=0)
    investment_cash_flow = Column(Float, default=0)
    financing_cash_flow = Column(Float, default=0)
    
    # Growth and ratios
    cash_flow_growth_rate = Column(Float, default=0)
    operating_ratio = Column(Float, default=0)
    investment_ratio = Column(Float, default=0)
    financing_ratio = Column(Float, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CashFlowData(id={self.id}, company={self.company_identifier}, date={self.date})>"

class PredictionResult(Base):
    """Model for ML prediction results."""
    __tablename__ = "prediction_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, nullable=False, index=True)
    model_name = Column(String, nullable=False)
    model_version = Column(String, default="1.0")
    
    # Prediction details
    prediction_type = Column(String, nullable=False)  # 'cash_flow', 'quality', 'maintenance'
    prediction_horizon = Column(Integer, default=30)  # days
    confidence_score = Column(Float, default=0)  # 0-1
    
    # Input and output data
    input_data = Column(JSON)
    prediction_value = Column(Float)
    prediction_data = Column(JSON)  # Detailed prediction results
    
    # Feature importance and explanations
    feature_importance = Column(JSON)
    explanation = Column(Text)
    
    # Processing metadata
    processing_time_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())
    
    # User context
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    company_id = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<PredictionResult(id={self.id}, type={self.prediction_type}, confidence={self.confidence_score})>"

class MLModel(Base):
    """Model for ML model metadata."""
    __tablename__ = "ml_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # 'prophet', 'lstm', 'ensemble'
    
    # Model configuration
    hyperparameters = Column(JSON)
    feature_columns = Column(JSON)
    target_column = Column(String)
    
    # Performance metrics
    accuracy = Column(Float, default=0)
    mse = Column(Float, default=0)
    mae = Column(Float, default=0)
    r2_score = Column(Float, default=0)
    
    # Model status
    status = Column(String, default="training")  # 'training', 'active', 'deprecated'
    training_data_size = Column(Integer, default=0)
    training_start_time = Column(DateTime)
    training_end_time = Column(DateTime)
    
    # Model artifacts (paths to saved models)
    model_path = Column(String)
    scaler_path = Column(String)
    
    # Metadata
    description = Column(Text)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MLModel(id={self.id}, name={self.name}, version={self.version}, status={self.status})>"

class DataUpload(Base):
    """Model for tracking data uploads."""
    __tablename__ = "data_uploads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String, nullable=False)  # 'csv', 'xlsx', 'json'
    
    # Upload metadata
    upload_status = Column(String, default="processing")  # 'processing', 'completed', 'failed'
    records_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Processing results
    validation_results = Column(JSON)
    processing_log = Column(Text)
    
    # User context
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, nullable=True)
    
    # Metadata
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<DataUpload(id={self.id}, filename={self.filename}, status={self.upload_status})>"

class KPI(Base):
    """Model for Key Performance Indicators."""
    __tablename__ = "kpis"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # 'production', 'quality', 'financial', 'maintenance'
    
    # KPI configuration
    calculation_method = Column(String, nullable=False)
    target_value = Column(Float, nullable=True)
    unit = Column(String, default="")
    
    # Current value and trends
    current_value = Column(Float, default=0)
    previous_value = Column(Float, default=0)
    trend_direction = Column(String, default="stable")  # 'up', 'down', 'stable'
    
    # Thresholds
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)
    
    # Update metadata
    last_calculated = Column(DateTime, default=func.now())
    calculation_frequency = Column(String, default="daily")  # 'hourly', 'daily', 'weekly'
    
    # User context
    company_id = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<KPI(id={self.id}, name={self.name}, value={self.current_value})>"