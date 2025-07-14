"""
Transaction model for sales/purchases/expenses
"""

from sqlalchemy import Column, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Transaction(BaseModel):
    __tablename__ = "transactions"
    
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # sale, purchase, expense
    transaction_date = Column(Date, nullable=False)
    description = Column(String)
    client_name = Column(String)
    
    # Relationships
    company = relationship("Company", back_populates="transactions")