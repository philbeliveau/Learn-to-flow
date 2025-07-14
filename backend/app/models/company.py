"""
Company model
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class Company(BaseModel):
    __tablename__ = "companies"
    
    name = Column(String, nullable=False)
    sector = Column(String)  # Métallurgie, Plastique, etc.
    size = Column(String)    # 50-200, 200-500, etc.
    region = Column(String)  # Auvergne-Rhône-Alpes, etc.
    
    # Relationships
    users = relationship("User", back_populates="company")
    transactions = relationship("Transaction", back_populates="company")
    predictions = relationship("Prediction", back_populates="company")