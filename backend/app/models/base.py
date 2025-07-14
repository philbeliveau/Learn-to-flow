"""
Base model for all database models
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)