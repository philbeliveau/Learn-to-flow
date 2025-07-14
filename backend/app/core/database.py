"""
Database configuration and session management
Using SQLite for local development
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
import os

# Database configuration
DATABASE_DIR = Path(__file__).parent.parent.parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/ezbi_analytics.db"

# Create engine with proper SQLite settings
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database tables"""
    from ..models import user, company, transaction, prediction
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create demo data
    await create_demo_data()

async def create_demo_data():
    """Create demo company and user for testing"""
    from ..models.user import User
    from ..models.company import Company
    from ..models.transaction import Transaction
    from ..core.auth import get_password_hash
    from datetime import datetime, timedelta
    import random
    
    db = SessionLocal()
    try:
        # Check if demo data already exists
        existing_user = db.query(User).filter(User.email == "demo@ezbi.fr").first()
        if existing_user:
            return
        
        # Create demo company
        demo_company = Company(
            name="Metalux SARL",
            sector="Métallurgie",
            size="50-200",
            region="Auvergne-Rhône-Alpes"
        )
        db.add(demo_company)
        db.flush()
        
        # Create demo user
        demo_user = User(
            email="demo@ezbi.fr",
            name="Marie Dupont",
            hashed_password=get_password_hash("demo123"),
            company_id=demo_company.id,
            role="admin"
        )
        db.add(demo_user)
        db.flush()
        
        # Create demo transactions (last 6 months)
        base_date = datetime.now() - timedelta(days=180)
        for i in range(180):
            date = base_date + timedelta(days=i)
            
            # Simulate realistic manufacturing sales pattern
            base_amount = 50000
            seasonal_factor = 1 + 0.3 * (i / 180)  # Growth trend
            noise = random.uniform(0.7, 1.3)
            
            amount = base_amount * seasonal_factor * noise
            
            transaction = Transaction(
                company_id=demo_company.id,
                amount=round(amount, 2),
                transaction_type="sale",
                transaction_date=date.date(),
                description=f"Vente journalière {date.strftime('%Y-%m-%d')}",
                client_name="Client Standard"
            )
            db.add(transaction)
        
        db.commit()
        print("✅ Demo data created successfully")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create demo data: {e}")
    finally:
        db.close()