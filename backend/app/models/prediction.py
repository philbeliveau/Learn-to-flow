"""
Prediction model for ML predictions
"""

from sqlalchemy import Column, String, Float, Date, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Prediction(BaseModel):
    __tablename__ = "predictions"
    
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    target_date = Column(Date, nullable=False)
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    model_type = Column(String, nullable=False)  # prophet, lstm, ensemble
    model_version = Column(String)
    
    # Optional fields for evaluation
    actual_value = Column(Float)
    prediction_accuracy = Column(Float)  # MAPE or similar metric
    
    # Metadata
    features_used = Column(JSON)
    model_metadata = Column(JSON)
    
    # Relationships
    company = relationship("Company", back_populates="predictions")