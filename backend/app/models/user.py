"""
User model
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # admin, user
    
    # Foreign keys
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    
    # Relationships (use string reference to avoid circular imports)
    company = relationship("Company", back_populates="users", lazy="select")