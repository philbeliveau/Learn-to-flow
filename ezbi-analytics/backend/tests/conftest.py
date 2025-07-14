"""
Test configuration and shared fixtures for EZBI Analytics backend tests.
"""
import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
import factory
from faker import Faker
from datetime import datetime, timedelta
import json
import os
import tempfile
from pathlib import Path

# Import application components
from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.prediction import Prediction

# Configure test environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:password@localhost/ezbi_analytics_test"

# French locale for manufacturing test data
fake = Faker(['fr_FR'])

# Test database setup
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost/ezbi_analytics_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def sync_client():
    """Create synchronous test client."""
    return TestClient(app)

# User and Authentication Fixtures
@pytest.fixture
async def test_user(db_session) -> User:
    """Create test user."""
    user = User(
        email="test@manufacture-lyon.fr",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        first_name="Jean",
        last_name="Dupont",
        phone="+33123456789",
        is_active=True,
        is_verified=True,
        role="user",
        language="fr",
        timezone="Europe/Paris"
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def admin_user(db_session) -> User:
    """Create admin user."""
    user = User(
        email="admin@manufacture-lyon.fr",
        username="admin",
        hashed_password=get_password_hash("adminpassword123"),
        first_name="Marie",
        last_name="Martin",
        phone="+33987654321",
        is_active=True,
        is_verified=True,
        role="admin",
        language="fr",
        timezone="Europe/Paris"
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def access_token(test_user) -> str:
    """Create access token for test user."""
    return create_access_token(subject=test_user.email)

@pytest.fixture
def admin_token(admin_user) -> str:
    """Create access token for admin user."""
    return create_access_token(subject=admin_user.email)

@pytest.fixture
def auth_headers(access_token) -> Dict[str, str]:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_headers(admin_token) -> Dict[str, str]:
    """Create admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}

# Company and Manufacturing Fixtures
@pytest.fixture
async def test_company(db_session, test_user) -> Company:
    """Create test manufacturing company."""
    company = Company(
        name="Manufacture Lyonnaise SA",
        siret="12345678901234",
        siren="123456789",
        naf_code="2562Z",  # Usinage
        address="15 Rue de l'Industrie",
        city="Lyon",
        postal_code="69000",
        country="France",
        phone="+33472123456",
        email="contact@manufacture-lyonnaise.fr",
        website="https://manufacture-lyonnaise.fr",
        industry="Manufacturing",
        size="SME",
        annual_revenue=2500000.0,
        employee_count=45,
        vat_number="FR12345678901",
        owner_id=test_user.id,
        is_active=True
    )
    
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company

# Financial Data Fixtures
@pytest.fixture
async def sample_financial_data(db_session, test_company) -> List[FinancialData]:
    """Create sample financial data for manufacturing company."""
    financial_records = []
    
    # Create 24 months of financial data
    for i in range(24):
        date = datetime.now() - timedelta(days=30 * i)
        
        # Manufacturing-specific financial patterns
        base_revenue = 150000 + (i * 5000)  # Growing revenue
        seasonal_factor = 1.2 if date.month in [3, 4, 5, 9, 10, 11] else 0.8  # Manufacturing peaks
        
        record = FinancialData(
            company_id=test_company.id,
            period_start=date.replace(day=1),
            period_end=date.replace(day=28),
            revenue=base_revenue * seasonal_factor,
            expenses=base_revenue * seasonal_factor * 0.75,
            accounts_receivable=base_revenue * seasonal_factor * 0.4,
            accounts_payable=base_revenue * seasonal_factor * 0.3,
            inventory=base_revenue * seasonal_factor * 0.25,
            cash_flow=base_revenue * seasonal_factor * 0.15,
            raw_materials_cost=base_revenue * seasonal_factor * 0.35,
            labor_cost=base_revenue * seasonal_factor * 0.25,
            overhead_cost=base_revenue * seasonal_factor * 0.15,
            production_volume=1000 + (i * 50),
            data_source="manual",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        financial_records.append(record)
        db_session.add(record)
    
    await db_session.commit()
    return financial_records

@pytest.fixture
async def sample_predictions(db_session, test_company) -> List[Prediction]:
    """Create sample predictions for manufacturing company."""
    predictions = []
    
    for i in range(6):  # 6 months of predictions
        date = datetime.now() + timedelta(days=30 * i)
        
        prediction = Prediction(
            company_id=test_company.id,
            prediction_date=date,
            prediction_type="cash_flow",
            predicted_value=120000 + (i * 10000),
            confidence_score=0.85 - (i * 0.05),
            prediction_horizon=30,
            model_version="v1.0",
            model_type="lstm_attention",
            features_used={
                "revenue": 150000,
                "expenses": 112500,
                "seasonality": "high",
                "production_volume": 1200
            },
            created_at=datetime.now()
        )
        
        predictions.append(prediction)
        db_session.add(prediction)
    
    await db_session.commit()
    return predictions

# File Upload Fixtures
@pytest.fixture
def sample_excel_file():
    """Create sample Excel file for testing."""
    import openpyxl
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Données Financières"
    
    # Headers in French
    headers = [
        "Date", "Chiffre d'affaires", "Charges", "Créances clients",
        "Dettes fournisseurs", "Stocks", "Trésorerie", "Matières premières",
        "Main d'œuvre", "Frais généraux", "Volume production"
    ]
    
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # Sample data
    sample_data = [
        ["2024-01-01", 150000, 112500, 60000, 45000, 37500, 22500, 52500, 37500, 22500, 1200],
        ["2024-02-01", 160000, 120000, 64000, 48000, 40000, 24000, 56000, 40000, 24000, 1300],
        ["2024-03-01", 180000, 135000, 72000, 54000, 45000, 27000, 63000, 45000, 27000, 1400],
    ]
    
    for row, data in enumerate(sample_data, 2):
        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    wb.save(temp_file.name)
    temp_file.close()
    
    return temp_file.name

@pytest.fixture
def sample_csv_file():
    """Create sample CSV file for testing."""
    import csv
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    writer = csv.writer(temp_file)
    writer.writerow([
        "Date", "Chiffre d'affaires", "Charges", "Créances clients",
        "Dettes fournisseurs", "Stocks", "Trésorerie"
    ])
    
    writer.writerows([
        ["2024-01-01", 150000, 112500, 60000, 45000, 37500, 22500],
        ["2024-02-01", 160000, 120000, 64000, 48000, 40000, 24000],
        ["2024-03-01", 180000, 135000, 72000, 54000, 45000, 27000],
    ])
    
    temp_file.close()
    return temp_file.name

# ML Model Fixtures
@pytest.fixture
def mock_ml_model():
    """Create mock ML model for testing."""
    mock_model = Mock()
    mock_model.predict.return_value = {
        "prediction": 125000.0,
        "confidence": 0.87,
        "features": {
            "revenue_trend": 0.15,
            "seasonal_factor": 1.2,
            "production_volume": 1300
        }
    }
    return mock_model

@pytest.fixture
def mock_ml_service():
    """Create mock ML service for testing."""
    mock_service = AsyncMock()
    mock_service.predict_cash_flow.return_value = {
        "predictions": [
            {"date": "2024-04-01", "value": 125000, "confidence": 0.87},
            {"date": "2024-05-01", "value": 135000, "confidence": 0.84},
            {"date": "2024-06-01", "value": 145000, "confidence": 0.81},
        ],
        "model_info": {
            "version": "v1.0",
            "type": "lstm_attention",
            "training_date": "2024-01-15"
        }
    }
    return mock_service

# External API Fixtures
@pytest.fixture
def mock_sage_api():
    """Mock Sage ERP API responses."""
    return {
        "accounts": [
            {"code": "411000", "name": "Clients", "balance": 75000},
            {"code": "401000", "name": "Fournisseurs", "balance": -45000},
            {"code": "512000", "name": "Banque", "balance": 25000},
        ],
        "transactions": [
            {"date": "2024-01-15", "amount": 15000, "type": "credit", "description": "Vente matériel"},
            {"date": "2024-01-16", "amount": -8000, "type": "debit", "description": "Achat matières premières"},
        ]
    }

@pytest.fixture
def mock_banking_api():
    """Mock banking API responses."""
    return {
        "accounts": [
            {
                "iban": "FR1420041010050500013M02606",
                "balance": 25000.50,
                "currency": "EUR",
                "type": "current"
            }
        ],
        "transactions": [
            {
                "date": "2024-01-15",
                "amount": 15000.00,
                "description": "Virement client ACME",
                "type": "credit"
            },
            {
                "date": "2024-01-16",
                "amount": -8000.00,
                "description": "Prélèvement fournisseur",
                "type": "debit"
            }
        ]
    }

# Performance Testing Fixtures
@pytest.fixture
def performance_metrics():
    """Performance testing metrics."""
    return {
        "response_time_threshold": 200,  # milliseconds
        "throughput_threshold": 1000,   # requests per second
        "memory_threshold": 100,        # MB
        "cpu_threshold": 80,            # percentage
        "concurrent_users": 50,
        "test_duration": 60,            # seconds
    }

# Security Testing Fixtures
@pytest.fixture
def security_test_data():
    """Security testing data."""
    return {
        "sql_injection_payloads": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ],
        "invalid_tokens": [
            "invalid_token",
            "Bearer invalid",
            "expired_token_here"
        ],
        "malicious_files": [
            "malicious.exe",
            "virus.bat",
            "script.js"
        ]
    }

# Utility Fixtures
@pytest.fixture
def test_data_path():
    """Path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def cleanup_files():
    """Cleanup test files after tests."""
    files_to_cleanup = []
    
    yield files_to_cleanup
    
    for file_path in files_to_cleanup:
        if os.path.exists(file_path):
            os.remove(file_path)

# Mock External Services
@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    return AsyncMock()

@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    return AsyncMock()

@pytest.fixture
def mock_audit_service():
    """Mock audit service for testing."""
    return AsyncMock()

# French Manufacturing Test Data
@pytest.fixture
def french_manufacturing_data():
    """French manufacturing specific test data."""
    return {
        "companies": [
            {
                "name": "Métallurgie Rhône SA",
                "siret": "12345678901234",
                "naf_code": "2562Z",
                "city": "Lyon",
                "industry": "Métallurgie"
            },
            {
                "name": "Plasturgie Provence SARL",
                "siret": "98765432109876",
                "naf_code": "2229A",
                "city": "Marseille",
                "industry": "Plasturgie"
            }
        ],
        "financial_patterns": {
            "seasonal_peaks": [3, 4, 5, 9, 10, 11],  # Manufacturing seasons
            "holiday_impacts": [7, 8, 12, 1],         # French holidays
            "growth_rates": {"low": 0.02, "medium": 0.05, "high": 0.08}
        },
        "compliance_requirements": {
            "data_retention": 2555,  # 7 years in days
            "audit_frequency": 30,   # Monthly audits
            "rgpd_enabled": True
        }
    }

# Factory Classes for Test Data Generation
class UserFactory(factory.Factory):
    """Factory for creating test users."""
    class Meta:
        model = User
    
    email = factory.Faker('email', locale='fr_FR')
    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name', locale='fr_FR')
    last_name = factory.Faker('last_name', locale='fr_FR')
    phone = factory.Faker('phone_number', locale='fr_FR')
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword123"))
    is_active = True
    is_verified = True
    role = "user"
    language = "fr"
    timezone = "Europe/Paris"

class CompanyFactory(factory.Factory):
    """Factory for creating test companies."""
    class Meta:
        model = Company
    
    name = factory.Faker('company', locale='fr_FR')
    siret = factory.Faker('numerify', text='##############')
    siren = factory.Faker('numerify', text='#########')
    naf_code = factory.Faker('random_element', elements=['2562Z', '2229A', '2561Z'])
    address = factory.Faker('street_address', locale='fr_FR')
    city = factory.Faker('city', locale='fr_FR')
    postal_code = factory.Faker('postcode', locale='fr_FR')
    country = "France"
    phone = factory.Faker('phone_number', locale='fr_FR')
    email = factory.Faker('company_email', locale='fr_FR')
    industry = "Manufacturing"
    size = "SME"
    annual_revenue = factory.Faker('random_int', min=500000, max=5000000)
    employee_count = factory.Faker('random_int', min=10, max=200)
    is_active = True

@pytest.fixture
def user_factory():
    """User factory fixture."""
    return UserFactory

@pytest.fixture
def company_factory():
    """Company factory fixture."""
    return CompanyFactory