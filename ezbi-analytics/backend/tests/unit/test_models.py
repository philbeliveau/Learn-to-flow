"""
Unit tests for database models.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
import json

from app.models.user import User
from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.prediction import Prediction
from app.models.audit_log import AuditLog
from app.models.session import Session
from app.models.notification import Notification
from app.models.file_upload import FileUpload
from app.models.integration import Integration
from app.core.security import get_password_hash, verify_password


class TestUserModel:
    """Test User model functionality."""
    
    @pytest.mark.asyncio
    async def test_user_creation(self, db_session):
        """Test user creation with valid data."""
        user = User(
            email="test@manufacture-lyon.fr",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Jean",
            last_name="Dupont",
            phone="+33123456789",
            role="user",
            language="fr",
            timezone="Europe/Paris"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@manufacture-lyon.fr"
        assert user.username == "testuser"
        assert user.full_name == "Jean Dupont"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.language == "fr"
        assert user.timezone == "Europe/Paris"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_unique_constraints(self, db_session):
        """Test user unique constraints."""
        user1 = User(
            email="test@manufacture-lyon.fr",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Jean",
            last_name="Dupont"
        )
        
        user2 = User(
            email="test@manufacture-lyon.fr",  # Same email
            username="anotheruser",
            hashed_password=get_password_hash("password123"),
            first_name="Marie",
            last_name="Martin"
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    def test_user_password_verification(self):
        """Test password verification."""
        password = "test_password123"
        hashed = get_password_hash(password)
        
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed,
            first_name="Test",
            last_name="User"
        )
        
        assert verify_password(password, user.hashed_password) is True
        assert verify_password("wrong_password", user.hashed_password) is False
    
    def test_user_full_name_property(self):
        """Test full name property."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            first_name="Jean-Claude",
            last_name="Van Damme"
        )
        
        assert user.full_name == "Jean-Claude Van Damme"
    
    def test_user_role_validation(self):
        """Test user role validation."""
        valid_roles = ["user", "admin", "manager", "viewer"]
        
        for role in valid_roles:
            user = User(
                email=f"test{role}@example.com",
                username=f"test{role}",
                hashed_password="hashed",
                first_name="Test",
                last_name="User",
                role=role
            )
            assert user.role == role
    
    def test_user_language_timezone_defaults(self):
        """Test user language and timezone defaults."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            first_name="Test",
            last_name="User"
        )
        
        assert user.language == "fr"
        assert user.timezone == "Europe/Paris"
    
    def test_user_phone_validation(self):
        """Test phone number validation."""
        valid_phones = ["+33123456789", "+33 1 23 45 67 89", "0123456789"]
        
        for phone in valid_phones:
            user = User(
                email=f"test{phone[-4:]}@example.com",
                username=f"test{phone[-4:]}",
                hashed_password="hashed",
                first_name="Test",
                last_name="User",
                phone=phone
            )
            assert user.phone == phone
    
    def test_user_audit_fields(self):
        """Test user audit fields."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            first_name="Test",
            last_name="User"
        )
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.last_login is None
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestCompanyModel:
    """Test Company model functionality."""
    
    @pytest.mark.asyncio
    async def test_company_creation(self, db_session, test_user):
        """Test company creation with valid data."""
        company = Company(
            name="Manufacture Lyonnaise SA",
            siret="12345678901234",
            siren="123456789",
            naf_code="2562Z",
            address="15 Rue de l'Industrie",
            city="Lyon",
            postal_code="69000",
            country="France",
            phone="+33472123456",
            email="contact@manufacture-lyonnaise.fr",
            industry="Manufacturing",
            size="SME",
            annual_revenue=2500000.0,
            employee_count=45,
            owner_id=test_user.id
        )
        
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        assert company.id is not None
        assert company.name == "Manufacture Lyonnaise SA"
        assert company.siret == "12345678901234"
        assert company.siren == "123456789"
        assert company.naf_code == "2562Z"
        assert company.industry == "Manufacturing"
        assert company.size == "SME"
        assert company.annual_revenue == 2500000.0
        assert company.employee_count == 45
        assert company.is_active is True
        assert company.owner_id == test_user.id
    
    def test_company_siret_validation(self):
        """Test SIRET validation."""
        valid_sirets = ["12345678901234", "98765432109876"]
        
        for siret in valid_sirets:
            company = Company(
                name="Test Company",
                siret=siret,
                siren=siret[:9],
                naf_code="2562Z",
                industry="Manufacturing",
                size="SME",
                owner_id=1
            )
            assert company.siret == siret
            assert len(company.siret) == 14
    
    def test_company_siren_validation(self):
        """Test SIREN validation."""
        valid_sirens = ["123456789", "987654321"]
        
        for siren in valid_sirens:
            company = Company(
                name="Test Company",
                siret=siren + "12345",
                siren=siren,
                naf_code="2562Z",
                industry="Manufacturing",
                size="SME",
                owner_id=1
            )
            assert company.siren == siren
            assert len(company.siren) == 9
    
    def test_company_naf_code_validation(self):
        """Test NAF code validation."""
        valid_naf_codes = ["2562Z", "2229A", "2561Z", "1520Z"]
        
        for naf_code in valid_naf_codes:
            company = Company(
                name="Test Company",
                siret="12345678901234",
                siren="123456789",
                naf_code=naf_code,
                industry="Manufacturing",
                size="SME",
                owner_id=1
            )
            assert company.naf_code == naf_code
    
    def test_company_size_validation(self):
        """Test company size validation."""
        valid_sizes = ["Micro", "Small", "Medium", "SME", "Large"]
        
        for size in valid_sizes:
            company = Company(
                name="Test Company",
                siret="12345678901234",
                siren="123456789",
                naf_code="2562Z",
                industry="Manufacturing",
                size=size,
                owner_id=1
            )
            assert company.size == size
    
    def test_company_industry_validation(self):
        """Test industry validation."""
        valid_industries = [
            "Manufacturing", "Metallurgy", "Plastics", "Textiles", 
            "Food Processing", "Automotive", "Aerospace"
        ]
        
        for industry in valid_industries:
            company = Company(
                name="Test Company",
                siret="12345678901234",
                siren="123456789",
                naf_code="2562Z",
                industry=industry,
                size="SME",
                owner_id=1
            )
            assert company.industry == industry
    
    def test_company_french_postal_code(self):
        """Test French postal code validation."""
        valid_postal_codes = ["69000", "75001", "13001", "31000"]
        
        for postal_code in valid_postal_codes:
            company = Company(
                name="Test Company",
                siret="12345678901234",
                siren="123456789",
                naf_code="2562Z",
                postal_code=postal_code,
                country="France",
                industry="Manufacturing",
                size="SME",
                owner_id=1
            )
            assert company.postal_code == postal_code
            assert len(company.postal_code) == 5
    
    def test_company_vat_number_validation(self):
        """Test VAT number validation."""
        valid_vat_numbers = ["FR12345678901", "FR98765432109"]
        
        for vat_number in valid_vat_numbers:
            company = Company(
                name="Test Company",
                siret="12345678901234",
                siren="123456789",
                naf_code="2562Z",
                vat_number=vat_number,
                industry="Manufacturing",
                size="SME",
                owner_id=1
            )
            assert company.vat_number == vat_number
            assert company.vat_number.startswith("FR")


class TestFinancialDataModel:
    """Test FinancialData model functionality."""
    
    @pytest.mark.asyncio
    async def test_financial_data_creation(self, db_session, test_company):
        """Test financial data creation."""
        financial_data = FinancialData(
            company_id=test_company.id,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            revenue=150000.0,
            expenses=112500.0,
            accounts_receivable=60000.0,
            accounts_payable=45000.0,
            inventory=37500.0,
            cash_flow=22500.0,
            raw_materials_cost=52500.0,
            labor_cost=37500.0,
            overhead_cost=22500.0,
            production_volume=1200,
            data_source="manual"
        )
        
        db_session.add(financial_data)
        await db_session.commit()
        await db_session.refresh(financial_data)
        
        assert financial_data.id is not None
        assert financial_data.company_id == test_company.id
        assert financial_data.revenue == 150000.0
        assert financial_data.expenses == 112500.0
        assert financial_data.cash_flow == 22500.0
        assert financial_data.production_volume == 1200
        assert financial_data.data_source == "manual"
    
    def test_financial_data_calculations(self):
        """Test financial data calculations."""
        financial_data = FinancialData(
            company_id=1,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            revenue=150000.0,
            expenses=112500.0,
            accounts_receivable=60000.0,
            accounts_payable=45000.0,
            inventory=37500.0,
            raw_materials_cost=52500.0,
            labor_cost=37500.0,
            overhead_cost=22500.0,
            production_volume=1200,
            data_source="manual"
        )
        
        # Test profit calculation
        profit = financial_data.revenue - financial_data.expenses
        assert profit == 37500.0
        
        # Test margin calculation
        margin = profit / financial_data.revenue
        assert margin == 0.25
        
        # Test working capital
        working_capital = (financial_data.accounts_receivable + 
                          financial_data.inventory - 
                          financial_data.accounts_payable)
        assert working_capital == 52500.0
    
    def test_financial_data_ratios(self):
        """Test financial ratio calculations."""
        financial_data = FinancialData(
            company_id=1,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            revenue=150000.0,
            expenses=112500.0,
            accounts_receivable=60000.0,
            accounts_payable=45000.0,
            inventory=37500.0,
            raw_materials_cost=52500.0,
            labor_cost=37500.0,
            overhead_cost=22500.0,
            production_volume=1200,
            data_source="manual"
        )
        
        # Test Days Sales Outstanding (DSO)
        dso = (financial_data.accounts_receivable / financial_data.revenue) * 30
        assert dso == 12.0  # 12 days
        
        # Test Days Payable Outstanding (DPO)
        dpo = (financial_data.accounts_payable / financial_data.expenses) * 30
        assert dpo == 12.0  # 12 days
        
        # Test Inventory Turnover
        inventory_turnover = financial_data.raw_materials_cost / financial_data.inventory
        assert inventory_turnover == 1.4
    
    def test_financial_data_manufacturing_metrics(self):
        """Test manufacturing-specific metrics."""
        financial_data = FinancialData(
            company_id=1,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            revenue=150000.0,
            expenses=112500.0,
            raw_materials_cost=52500.0,
            labor_cost=37500.0,
            overhead_cost=22500.0,
            production_volume=1200,
            data_source="manual"
        )
        
        # Test cost per unit
        total_production_cost = (financial_data.raw_materials_cost + 
                               financial_data.labor_cost + 
                               financial_data.overhead_cost)
        cost_per_unit = total_production_cost / financial_data.production_volume
        assert cost_per_unit == 93.75
        
        # Test revenue per unit
        revenue_per_unit = financial_data.revenue / financial_data.production_volume
        assert revenue_per_unit == 125.0
        
        # Test profit per unit
        profit_per_unit = revenue_per_unit - cost_per_unit
        assert profit_per_unit == 31.25
    
    def test_financial_data_validation(self):
        """Test financial data validation."""
        # Test negative values are allowed where appropriate
        financial_data = FinancialData(
            company_id=1,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            revenue=150000.0,
            expenses=175000.0,  # Higher than revenue (loss)
            cash_flow=-25000.0,  # Negative cash flow
            production_volume=1200,
            data_source="manual"
        )
        
        assert financial_data.cash_flow == -25000.0
        assert financial_data.expenses > financial_data.revenue
    
    def test_financial_data_period_validation(self):
        """Test financial data period validation."""
        financial_data = FinancialData(
            company_id=1,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            revenue=150000.0,
            expenses=112500.0,
            production_volume=1200,
            data_source="manual"
        )
        
        # Period end should be after period start
        period_length = financial_data.period_end - financial_data.period_start
        assert period_length.days > 0
        assert period_length.days <= 31  # Monthly data


class TestPredictionModel:
    """Test Prediction model functionality."""
    
    @pytest.mark.asyncio
    async def test_prediction_creation(self, db_session, test_company):
        """Test prediction creation."""
        prediction = Prediction(
            company_id=test_company.id,
            prediction_date=datetime(2024, 4, 1),
            prediction_type="cash_flow",
            predicted_value=125000.0,
            confidence_score=0.87,
            prediction_horizon=30,
            model_version="v1.0",
            model_type="lstm_attention",
            features_used={
                "revenue": 150000,
                "expenses": 112500,
                "seasonality": "high",
                "production_volume": 1200
            }
        )
        
        db_session.add(prediction)
        await db_session.commit()
        await db_session.refresh(prediction)
        
        assert prediction.id is not None
        assert prediction.company_id == test_company.id
        assert prediction.prediction_type == "cash_flow"
        assert prediction.predicted_value == 125000.0
        assert prediction.confidence_score == 0.87
        assert prediction.prediction_horizon == 30
        assert prediction.model_version == "v1.0"
        assert prediction.model_type == "lstm_attention"
        assert isinstance(prediction.features_used, dict)
    
    def test_prediction_confidence_validation(self):
        """Test prediction confidence score validation."""
        prediction = Prediction(
            company_id=1,
            prediction_date=datetime(2024, 4, 1),
            prediction_type="cash_flow",
            predicted_value=125000.0,
            confidence_score=0.95,
            prediction_horizon=30,
            model_version="v1.0",
            model_type="lstm_attention"
        )
        
        assert 0.0 <= prediction.confidence_score <= 1.0
        assert prediction.confidence_score == 0.95
    
    def test_prediction_types_validation(self):
        """Test prediction types validation."""
        valid_types = ["cash_flow", "revenue", "expenses", "profit", "working_capital"]
        
        for pred_type in valid_types:
            prediction = Prediction(
                company_id=1,
                prediction_date=datetime(2024, 4, 1),
                prediction_type=pred_type,
                predicted_value=125000.0,
                confidence_score=0.87,
                prediction_horizon=30,
                model_version="v1.0",
                model_type="lstm_attention"
            )
            assert prediction.prediction_type == pred_type
    
    def test_prediction_model_types(self):
        """Test prediction model types."""
        valid_models = ["lstm_attention", "prophet", "ensemble", "linear_regression"]
        
        for model_type in valid_models:
            prediction = Prediction(
                company_id=1,
                prediction_date=datetime(2024, 4, 1),
                prediction_type="cash_flow",
                predicted_value=125000.0,
                confidence_score=0.87,
                prediction_horizon=30,
                model_version="v1.0",
                model_type=model_type
            )
            assert prediction.model_type == model_type
    
    def test_prediction_features_json(self):
        """Test prediction features JSON handling."""
        features = {
            "revenue": 150000,
            "expenses": 112500,
            "seasonality": "high",
            "production_volume": 1200,
            "trend": "increasing",
            "market_conditions": "stable"
        }
        
        prediction = Prediction(
            company_id=1,
            prediction_date=datetime(2024, 4, 1),
            prediction_type="cash_flow",
            predicted_value=125000.0,
            confidence_score=0.87,
            prediction_horizon=30,
            model_version="v1.0",
            model_type="lstm_attention",
            features_used=features
        )
        
        assert prediction.features_used == features
        assert prediction.features_used["revenue"] == 150000
        assert prediction.features_used["seasonality"] == "high"
    
    def test_prediction_horizon_validation(self):
        """Test prediction horizon validation."""
        valid_horizons = [1, 7, 30, 90, 365]
        
        for horizon in valid_horizons:
            prediction = Prediction(
                company_id=1,
                prediction_date=datetime(2024, 4, 1),
                prediction_type="cash_flow",
                predicted_value=125000.0,
                confidence_score=0.87,
                prediction_horizon=horizon,
                model_version="v1.0",
                model_type="lstm_attention"
            )
            assert prediction.prediction_horizon == horizon
            assert prediction.prediction_horizon > 0


class TestAuditLogModel:
    """Test AuditLog model functionality."""
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self, db_session, test_user):
        """Test audit log creation."""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="CREATE_COMPANY",
            entity_type="Company",
            entity_id=1,
            old_values={},
            new_values={"name": "New Company", "industry": "Manufacturing"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            session_id="test_session_123"
        )
        
        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)
        
        assert audit_log.id is not None
        assert audit_log.user_id == test_user.id
        assert audit_log.action == "CREATE_COMPANY"
        assert audit_log.entity_type == "Company"
        assert audit_log.entity_id == 1
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.timestamp is not None
    
    def test_audit_log_actions(self):
        """Test audit log actions."""
        valid_actions = ["CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "EXPORT"]
        
        for action in valid_actions:
            audit_log = AuditLog(
                user_id=1,
                action=action,
                entity_type="User",
                entity_id=1,
                old_values={},
                new_values={"status": "active"},
                ip_address="192.168.1.1"
            )
            assert audit_log.action == action
    
    def test_audit_log_json_fields(self):
        """Test audit log JSON fields."""
        old_values = {"name": "Old Company", "revenue": 100000}
        new_values = {"name": "New Company", "revenue": 150000}
        
        audit_log = AuditLog(
            user_id=1,
            action="UPDATE",
            entity_type="Company",
            entity_id=1,
            old_values=old_values,
            new_values=new_values,
            ip_address="192.168.1.1"
        )
        
        assert audit_log.old_values == old_values
        assert audit_log.new_values == new_values
        assert audit_log.old_values["name"] == "Old Company"
        assert audit_log.new_values["name"] == "New Company"


class TestSessionModel:
    """Test Session model functionality."""
    
    @pytest.mark.asyncio
    async def test_session_creation(self, db_session, test_user):
        """Test session creation."""
        session = Session(
            user_id=test_user.id,
            session_token="test_session_token_123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.session_token == "test_session_token_123"
        assert session.ip_address == "192.168.1.1"
        assert session.is_active is True
        assert session.expires_at > datetime.now()
    
    def test_session_expiration(self):
        """Test session expiration logic."""
        # Active session
        active_session = Session(
            user_id=1,
            session_token="active_token",
            ip_address="192.168.1.1",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        assert active_session.expires_at > datetime.now()
        
        # Expired session
        expired_session = Session(
            user_id=1,
            session_token="expired_token",
            ip_address="192.168.1.1",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        assert expired_session.expires_at < datetime.now()
    
    def test_session_revocation(self):
        """Test session revocation."""
        session = Session(
            user_id=1,
            session_token="test_token",
            ip_address="192.168.1.1",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Session starts active
        assert session.is_active is True
        
        # Revoke session
        session.is_active = False
        assert session.is_active is False


class TestNotificationModel:
    """Test Notification model functionality."""
    
    @pytest.mark.asyncio
    async def test_notification_creation(self, db_session, test_user):
        """Test notification creation."""
        notification = Notification(
            user_id=test_user.id,
            type="PREDICTION_ALERT",
            title="Alerte de trésorerie",
            message="Votre trésorerie pourrait être négative dans 30 jours",
            data={"predicted_value": -5000, "confidence": 0.87},
            priority="high",
            channel="email"
        )
        
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.type == "PREDICTION_ALERT"
        assert notification.title == "Alerte de trésorerie"
        assert notification.priority == "high"
        assert notification.channel == "email"
        assert notification.is_read is False
        assert notification.created_at is not None
    
    def test_notification_types(self):
        """Test notification types."""
        valid_types = [
            "PREDICTION_ALERT", "PAYMENT_REMINDER", "SYSTEM_UPDATE", 
            "INTEGRATION_ERROR", "MONTHLY_REPORT"
        ]
        
        for notif_type in valid_types:
            notification = Notification(
                user_id=1,
                type=notif_type,
                title="Test Notification",
                message="Test message",
                priority="medium",
                channel="email"
            )
            assert notification.type == notif_type
    
    def test_notification_priorities(self):
        """Test notification priorities."""
        valid_priorities = ["low", "medium", "high", "urgent"]
        
        for priority in valid_priorities:
            notification = Notification(
                user_id=1,
                type="SYSTEM_UPDATE",
                title="Test Notification",
                message="Test message",
                priority=priority,
                channel="email"
            )
            assert notification.priority == priority
    
    def test_notification_channels(self):
        """Test notification channels."""
        valid_channels = ["email", "sms", "push", "in_app"]
        
        for channel in valid_channels:
            notification = Notification(
                user_id=1,
                type="SYSTEM_UPDATE",
                title="Test Notification",
                message="Test message",
                priority="medium",
                channel=channel
            )
            assert notification.channel == channel
    
    def test_notification_data_json(self):
        """Test notification data JSON handling."""
        data = {
            "predicted_value": -5000,
            "confidence": 0.87,
            "timeline": 30,
            "recommendations": ["Increase collections", "Delay payments"]
        }
        
        notification = Notification(
            user_id=1,
            type="PREDICTION_ALERT",
            title="Cash Flow Alert",
            message="Alert message",
            data=data,
            priority="high",
            channel="email"
        )
        
        assert notification.data == data
        assert notification.data["predicted_value"] == -5000
        assert notification.data["confidence"] == 0.87
        assert "recommendations" in notification.data


class TestFileUploadModel:
    """Test FileUpload model functionality."""
    
    @pytest.mark.asyncio
    async def test_file_upload_creation(self, db_session, test_user, test_company):
        """Test file upload creation."""
        file_upload = FileUpload(
            user_id=test_user.id,
            company_id=test_company.id,
            filename="donnees_financieres.xlsx",
            original_filename="Données Financières Mars 2024.xlsx",
            file_path="/uploads/2024/03/donnees_financieres.xlsx",
            file_size=125000,
            file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            processing_status="completed",
            records_imported=156,
            errors=[]
        )
        
        db_session.add(file_upload)
        await db_session.commit()
        await db_session.refresh(file_upload)
        
        assert file_upload.id is not None
        assert file_upload.user_id == test_user.id
        assert file_upload.company_id == test_company.id
        assert file_upload.filename == "donnees_financieres.xlsx"
        assert file_upload.file_size == 125000
        assert file_upload.processing_status == "completed"
        assert file_upload.records_imported == 156
        assert file_upload.upload_date is not None
    
    def test_file_upload_status(self):
        """Test file upload status."""
        valid_statuses = ["pending", "processing", "completed", "failed"]
        
        for status in valid_statuses:
            file_upload = FileUpload(
                user_id=1,
                company_id=1,
                filename="test.xlsx",
                original_filename="test.xlsx",
                file_path="/uploads/test.xlsx",
                file_size=1000,
                file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                processing_status=status
            )
            assert file_upload.processing_status == status
    
    def test_file_upload_errors_json(self):
        """Test file upload errors JSON handling."""
        errors = [
            {"row": 5, "column": "revenue", "error": "Invalid number format"},
            {"row": 10, "column": "date", "error": "Invalid date format"}
        ]
        
        file_upload = FileUpload(
            user_id=1,
            company_id=1,
            filename="test.xlsx",
            original_filename="test.xlsx",
            file_path="/uploads/test.xlsx",
            file_size=1000,
            file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            processing_status="failed",
            errors=errors
        )
        
        assert file_upload.errors == errors
        assert len(file_upload.errors) == 2
        assert file_upload.errors[0]["row"] == 5
        assert file_upload.errors[0]["error"] == "Invalid number format"


class TestIntegrationModel:
    """Test Integration model functionality."""
    
    @pytest.mark.asyncio
    async def test_integration_creation(self, db_session, test_company):
        """Test integration creation."""
        integration = Integration(
            company_id=test_company.id,
            integration_type="sage",
            name="Sage 100 Integration",
            config={
                "api_url": "https://sage.company.com/api",
                "username": "api_user",
                "sync_frequency": "daily"
            },
            is_active=True,
            last_sync=datetime.now() - timedelta(hours=2),
            sync_status="success"
        )
        
        db_session.add(integration)
        await db_session.commit()
        await db_session.refresh(integration)
        
        assert integration.id is not None
        assert integration.company_id == test_company.id
        assert integration.integration_type == "sage"
        assert integration.name == "Sage 100 Integration"
        assert integration.is_active is True
        assert integration.sync_status == "success"
        assert integration.created_at is not None
    
    def test_integration_types(self):
        """Test integration types."""
        valid_types = ["sage", "sap", "cegid", "open_banking", "custom"]
        
        for int_type in valid_types:
            integration = Integration(
                company_id=1,
                integration_type=int_type,
                name=f"{int_type.upper()} Integration",
                config={},
                is_active=True
            )
            assert integration.integration_type == int_type
    
    def test_integration_sync_status(self):
        """Test integration sync status."""
        valid_statuses = ["success", "failed", "pending", "in_progress"]
        
        for status in valid_statuses:
            integration = Integration(
                company_id=1,
                integration_type="sage",
                name="Test Integration",
                config={},
                is_active=True,
                sync_status=status
            )
            assert integration.sync_status == status
    
    def test_integration_config_json(self):
        """Test integration config JSON handling."""
        config = {
            "api_url": "https://api.example.com",
            "username": "api_user",
            "sync_frequency": "hourly",
            "data_mapping": {
                "revenue": "sales_total",
                "expenses": "cost_total"
            },
            "filters": {
                "date_from": "2024-01-01",
                "accounts": ["401000", "411000"]
            }
        }
        
        integration = Integration(
            company_id=1,
            integration_type="sage",
            name="Sage Integration",
            config=config,
            is_active=True
        )
        
        assert integration.config == config
        assert integration.config["api_url"] == "https://api.example.com"
        assert integration.config["data_mapping"]["revenue"] == "sales_total"
        assert "filters" in integration.config
    
    def test_integration_last_sync_tracking(self):
        """Test integration last sync tracking."""
        last_sync = datetime.now() - timedelta(hours=1)
        
        integration = Integration(
            company_id=1,
            integration_type="sage",
            name="Test Integration",
            config={},
            is_active=True,
            last_sync=last_sync,
            sync_status="success"
        )
        
        assert integration.last_sync == last_sync
        assert integration.last_sync < datetime.now()
        
        # Test sync age calculation
        sync_age = datetime.now() - integration.last_sync
        assert sync_age.seconds > 0
        assert sync_age.seconds < 3600  # Less than 1 hour