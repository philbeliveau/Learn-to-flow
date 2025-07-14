"""
Integration tests for API endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
import os
import tempfile

from app.main import app
from app.models.user import User
from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.prediction import Prediction
from app.core.security import get_password_hash


class TestAuthEndpoints:
    """Test authentication endpoints integration."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client, db_session):
        """Test complete authentication flow."""
        # 1. Register new user
        register_data = {
            "email": "integration@manufacture-test.fr",
            "username": "integration_test",
            "password": "integration123",
            "first_name": "Integration",
            "last_name": "Test",
            "phone": "+33123456789",
            "company_name": "Manufacture Test SA",
            "company_siret": "12345678901234"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        # 2. Login with new user
        login_data = {
            "username": "integration@manufacture-test.fr",
            "password": "integration123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == "integration@manufacture-test.fr"
        
        # 4. Refresh token
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 200
        
        new_tokens = response.json()
        new_access_token = new_tokens["access_token"]
        
        # 5. Use new access token
        headers = {"Authorization": f"Bearer {new_access_token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # 6. Logout
        response = await client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, client, test_user):
        """Test complete password reset flow."""
        # 1. Request password reset
        reset_request = {
            "email": test_user.email
        }
        
        response = await client.post("/api/v1/auth/reset-password-request", json=reset_request)
        assert response.status_code == 200
        
        # 2. Generate reset token (simulate email link)
        from app.core.security import generate_reset_token
        reset_token = generate_reset_token(test_user.email)
        
        # 3. Reset password
        reset_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        
        response = await client.post("/api/v1/auth/reset-password", json=reset_data)
        assert response.status_code == 200
        
        # 4. Login with new password
        login_data = {
            "username": test_user.email,
            "password": "newpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        # 5. Verify old password doesn't work
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401


class TestCompanyEndpoints:
    """Test company management endpoints."""
    
    @pytest.mark.asyncio
    async def test_company_crud_operations(self, client, test_user, auth_headers):
        """Test complete CRUD operations for companies."""
        # 1. Create company
        company_data = {
            "name": "Nouvelle Manufacture SARL",
            "siret": "98765432109876",
            "siren": "987654321",
            "naf_code": "2229A",
            "address": "25 Avenue de la République",
            "city": "Marseille",
            "postal_code": "13001",
            "country": "France",
            "phone": "+33491123456",
            "email": "contact@nouvelle-manufacture.fr",
            "website": "https://nouvelle-manufacture.fr",
            "industry": "Plastics",
            "size": "Small",
            "annual_revenue": 1500000.0,
            "employee_count": 25,
            "vat_number": "FR98765432109"
        }
        
        response = await client.post("/api/v1/companies/", json=company_data, headers=auth_headers)
        assert response.status_code == 201
        
        created_company = response.json()
        company_id = created_company["id"]
        assert created_company["name"] == company_data["name"]
        assert created_company["siret"] == company_data["siret"]
        
        # 2. Get company
        response = await client.get(f"/api/v1/companies/{company_id}", headers=auth_headers)
        assert response.status_code == 200
        
        retrieved_company = response.json()
        assert retrieved_company["id"] == company_id
        assert retrieved_company["name"] == company_data["name"]
        
        # 3. Update company
        update_data = {
            "name": "Manufacture Marseillaise SARL",
            "employee_count": 30,
            "annual_revenue": 1800000.0
        }
        
        response = await client.put(f"/api/v1/companies/{company_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        updated_company = response.json()
        assert updated_company["name"] == update_data["name"]
        assert updated_company["employee_count"] == update_data["employee_count"]
        assert updated_company["annual_revenue"] == update_data["annual_revenue"]
        
        # 4. List companies
        response = await client.get("/api/v1/companies/", headers=auth_headers)
        assert response.status_code == 200
        
        companies = response.json()
        assert len(companies) >= 1
        assert any(c["id"] == company_id for c in companies)
        
        # 5. Delete company
        response = await client.delete(f"/api/v1/companies/{company_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 6. Verify deletion
        response = await client.get(f"/api/v1/companies/{company_id}", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_company_validation(self, client, auth_headers):
        """Test company data validation."""
        # Test invalid SIRET
        invalid_company = {
            "name": "Test Company",
            "siret": "123",  # Too short
            "siren": "123456789",
            "naf_code": "2229A",
            "industry": "Manufacturing",
            "size": "SME"
        }
        
        response = await client.post("/api/v1/companies/", json=invalid_company, headers=auth_headers)
        assert response.status_code == 422
        
        # Test invalid email
        invalid_company = {
            "name": "Test Company",
            "siret": "12345678901234",
            "siren": "123456789",
            "naf_code": "2229A",
            "email": "invalid-email",
            "industry": "Manufacturing",
            "size": "SME"
        }
        
        response = await client.post("/api/v1/companies/", json=invalid_company, headers=auth_headers)
        assert response.status_code == 422
        
        # Test missing required fields
        invalid_company = {
            "name": "Test Company"
            # Missing required fields
        }
        
        response = await client.post("/api/v1/companies/", json=invalid_company, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_company_permissions(self, client, test_user, test_company):
        """Test company access permissions."""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            is_active=True,
            is_verified=True
        )
        
        # This test would verify that users can only access their own companies
        # Implementation depends on the actual authorization logic
        pass


class TestFinancialDataEndpoints:
    """Test financial data endpoints."""
    
    @pytest.mark.asyncio
    async def test_financial_data_crud(self, client, test_company, auth_headers):
        """Test financial data CRUD operations."""
        # 1. Create financial data
        financial_data = {
            "company_id": test_company.id,
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "revenue": 150000.0,
            "expenses": 112500.0,
            "accounts_receivable": 60000.0,
            "accounts_payable": 45000.0,
            "inventory": 37500.0,
            "cash_flow": 22500.0,
            "raw_materials_cost": 52500.0,
            "labor_cost": 37500.0,
            "overhead_cost": 22500.0,
            "production_volume": 1200,
            "data_source": "manual"
        }
        
        response = await client.post("/api/v1/financial-data/", json=financial_data, headers=auth_headers)
        assert response.status_code == 201
        
        created_data = response.json()
        data_id = created_data["id"]
        assert created_data["revenue"] == financial_data["revenue"]
        assert created_data["company_id"] == test_company.id
        
        # 2. Get financial data
        response = await client.get(f"/api/v1/financial-data/{data_id}", headers=auth_headers)
        assert response.status_code == 200
        
        retrieved_data = response.json()
        assert retrieved_data["id"] == data_id
        assert retrieved_data["revenue"] == financial_data["revenue"]
        
        # 3. Update financial data
        update_data = {
            "revenue": 160000.0,
            "expenses": 120000.0,
            "cash_flow": 28000.0
        }
        
        response = await client.put(f"/api/v1/financial-data/{data_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        updated_data = response.json()
        assert updated_data["revenue"] == update_data["revenue"]
        assert updated_data["expenses"] == update_data["expenses"]
        
        # 4. List financial data for company
        response = await client.get(f"/api/v1/companies/{test_company.id}/financial-data", headers=auth_headers)
        assert response.status_code == 200
        
        financial_records = response.json()
        assert len(financial_records) >= 1
        assert any(r["id"] == data_id for r in financial_records)
        
        # 5. Delete financial data
        response = await client.delete(f"/api/v1/financial-data/{data_id}", headers=auth_headers)
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_financial_data_bulk_import(self, client, test_company, auth_headers, sample_csv_file):
        """Test bulk import of financial data."""
        # Upload CSV file
        with open(sample_csv_file, "rb") as f:
            files = {"file": ("financial_data.csv", f, "text/csv")}
            data = {"company_id": test_company.id}
            
            response = await client.post(
                "/api/v1/financial-data/bulk-import",
                files=files,
                data=data,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        result = response.json()
        assert "imported_count" in result
        assert result["imported_count"] > 0
        assert "errors" in result
        
        # Verify data was imported
        response = await client.get(f"/api/v1/companies/{test_company.id}/financial-data", headers=auth_headers)
        assert response.status_code == 200
        
        financial_records = response.json()
        assert len(financial_records) >= result["imported_count"]
    
    @pytest.mark.asyncio
    async def test_financial_data_analytics(self, client, test_company, sample_financial_data, auth_headers):
        """Test financial data analytics endpoints."""
        # Test financial summary
        response = await client.get(f"/api/v1/companies/{test_company.id}/financial-summary", headers=auth_headers)
        assert response.status_code == 200
        
        summary = response.json()
        assert "total_revenue" in summary
        assert "total_expenses" in summary
        assert "average_cash_flow" in summary
        assert "growth_rate" in summary
        
        # Test financial trends
        response = await client.get(f"/api/v1/companies/{test_company.id}/financial-trends", headers=auth_headers)
        assert response.status_code == 200
        
        trends = response.json()
        assert "revenue_trend" in trends
        assert "cash_flow_trend" in trends
        assert "seasonality" in trends
        
        # Test financial ratios
        response = await client.get(f"/api/v1/companies/{test_company.id}/financial-ratios", headers=auth_headers)
        assert response.status_code == 200
        
        ratios = response.json()
        assert "profitability_ratios" in ratios
        assert "liquidity_ratios" in ratios
        assert "efficiency_ratios" in ratios


class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    @pytest.mark.asyncio
    async def test_cash_flow_prediction(self, client, test_company, sample_financial_data, auth_headers, mock_ml_service):
        """Test cash flow prediction endpoint."""
        with patch('app.services.ml_service.MLService', return_value=mock_ml_service):
            prediction_request = {
                "company_id": test_company.id,
                "prediction_type": "cash_flow",
                "prediction_horizon": 90,
                "include_confidence": True
            }
            
            response = await client.post("/api/v1/predictions/predict", json=prediction_request, headers=auth_headers)
            assert response.status_code == 200
            
            prediction = response.json()
            assert "predictions" in prediction
            assert "model_info" in prediction
            assert len(prediction["predictions"]) > 0
            
            # Verify prediction structure
            first_prediction = prediction["predictions"][0]
            assert "date" in first_prediction
            assert "value" in first_prediction
            assert "confidence" in first_prediction
    
    @pytest.mark.asyncio
    async def test_prediction_history(self, client, test_company, sample_predictions, auth_headers):
        """Test prediction history endpoint."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/predictions", headers=auth_headers)
        assert response.status_code == 200
        
        predictions = response.json()
        assert len(predictions) >= len(sample_predictions)
        
        # Verify prediction structure
        for prediction in predictions:
            assert "id" in prediction
            assert "prediction_date" in prediction
            assert "prediction_type" in prediction
            assert "predicted_value" in prediction
            assert "confidence_score" in prediction
            assert "model_version" in prediction
    
    @pytest.mark.asyncio
    async def test_prediction_accuracy(self, client, test_company, sample_predictions, auth_headers):
        """Test prediction accuracy analysis."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/prediction-accuracy", headers=auth_headers)
        assert response.status_code == 200
        
        accuracy = response.json()
        assert "overall_accuracy" in accuracy
        assert "model_performance" in accuracy
        assert "accuracy_by_horizon" in accuracy
        assert "accuracy_trends" in accuracy
    
    @pytest.mark.asyncio
    async def test_scenario_analysis(self, client, test_company, auth_headers, mock_ml_service):
        """Test scenario analysis endpoint."""
        with patch('app.services.ml_service.MLService', return_value=mock_ml_service):
            scenario_request = {
                "company_id": test_company.id,
                "scenarios": [
                    {
                        "name": "optimistic",
                        "adjustments": {"revenue_growth": 0.15, "expense_reduction": 0.05}
                    },
                    {
                        "name": "pessimistic",
                        "adjustments": {"revenue_growth": -0.10, "expense_increase": 0.08}
                    }
                ],
                "prediction_horizon": 180
            }
            
            response = await client.post("/api/v1/predictions/scenario-analysis", json=scenario_request, headers=auth_headers)
            assert response.status_code == 200
            
            scenarios = response.json()
            assert "scenarios" in scenarios
            assert len(scenarios["scenarios"]) == 2
            
            for scenario in scenarios["scenarios"]:
                assert "name" in scenario
                assert "predictions" in scenario
                assert "summary" in scenario


class TestFileUploadEndpoints:
    """Test file upload endpoints."""
    
    @pytest.mark.asyncio
    async def test_excel_file_upload(self, client, test_company, auth_headers, sample_excel_file):
        """Test Excel file upload and processing."""
        with open(sample_excel_file, "rb") as f:
            files = {"file": ("financial_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"company_id": test_company.id}
            
            response = await client.post(
                "/api/v1/files/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        upload_result = response.json()
        assert "file_id" in upload_result
        assert "status" in upload_result
        assert "processing_info" in upload_result
        
        file_id = upload_result["file_id"]
        
        # Check upload status
        response = await client.get(f"/api/v1/files/{file_id}/status", headers=auth_headers)
        assert response.status_code == 200
        
        status = response.json()
        assert "processing_status" in status
        assert "records_imported" in status
        assert "errors" in status
    
    @pytest.mark.asyncio
    async def test_file_upload_validation(self, client, test_company, auth_headers):
        """Test file upload validation."""
        # Test invalid file type
        invalid_file_content = b"This is not a valid Excel file"
        files = {"file": ("invalid.txt", invalid_file_content, "text/plain")}
        data = {"company_id": test_company.id}
        
        response = await client.post(
            "/api/v1/files/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        
        error = response.json()
        assert "detail" in error
        assert "file type" in error["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_file_upload_history(self, client, test_company, auth_headers):
        """Test file upload history endpoint."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/uploads", headers=auth_headers)
        assert response.status_code == 200
        
        uploads = response.json()
        assert isinstance(uploads, list)
        
        # If there are uploads, verify structure
        if uploads:
            upload = uploads[0]
            assert "id" in upload
            assert "filename" in upload
            assert "upload_date" in upload
            assert "processing_status" in upload
            assert "records_imported" in upload


class TestIntegrationEndpoints:
    """Test ERP/Banking integration endpoints."""
    
    @pytest.mark.asyncio
    async def test_sage_integration_setup(self, client, test_company, auth_headers):
        """Test Sage ERP integration setup."""
        integration_config = {
            "company_id": test_company.id,
            "integration_type": "sage",
            "name": "Sage 100 Production",
            "config": {
                "api_url": "https://sage.company.com/api",
                "username": "integration_user",
                "sync_frequency": "daily",
                "data_mapping": {
                    "revenue": "411000",
                    "expenses": "401000",
                    "accounts_receivable": "411000",
                    "accounts_payable": "401000"
                }
            }
        }
        
        response = await client.post("/api/v1/integrations/", json=integration_config, headers=auth_headers)
        assert response.status_code == 201
        
        integration = response.json()
        assert "id" in integration
        assert integration["integration_type"] == "sage"
        assert integration["name"] == integration_config["name"]
        
        integration_id = integration["id"]
        
        # Test integration sync
        response = await client.post(f"/api/v1/integrations/{integration_id}/sync", headers=auth_headers)
        assert response.status_code == 200
        
        sync_result = response.json()
        assert "status" in sync_result
        assert "records_synced" in sync_result
    
    @pytest.mark.asyncio
    async def test_banking_integration_setup(self, client, test_company, auth_headers):
        """Test banking integration setup."""
        integration_config = {
            "company_id": test_company.id,
            "integration_type": "open_banking",
            "name": "Crédit Agricole",
            "config": {
                "bank_code": "crédit_agricole",
                "account_iban": "FR1420041010050500013M02606",
                "sync_frequency": "hourly",
                "data_types": ["transactions", "balance"]
            }
        }
        
        response = await client.post("/api/v1/integrations/", json=integration_config, headers=auth_headers)
        assert response.status_code == 201
        
        integration = response.json()
        assert integration["integration_type"] == "open_banking"
        assert integration["name"] == integration_config["name"]
    
    @pytest.mark.asyncio
    async def test_integration_status(self, client, test_company, auth_headers):
        """Test integration status monitoring."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/integrations", headers=auth_headers)
        assert response.status_code == 200
        
        integrations = response.json()
        assert isinstance(integrations, list)
        
        # If there are integrations, test status endpoint
        if integrations:
            integration_id = integrations[0]["id"]
            
            response = await client.get(f"/api/v1/integrations/{integration_id}/status", headers=auth_headers)
            assert response.status_code == 200
            
            status = response.json()
            assert "is_active" in status
            assert "last_sync" in status
            assert "sync_status" in status
            assert "next_sync" in status


class TestNotificationEndpoints:
    """Test notification endpoints."""
    
    @pytest.mark.asyncio
    async def test_notification_list(self, client, test_user, auth_headers):
        """Test notification list endpoint."""
        response = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert response.status_code == 200
        
        notifications = response.json()
        assert isinstance(notifications, list)
        
        # If there are notifications, verify structure
        if notifications:
            notification = notifications[0]
            assert "id" in notification
            assert "type" in notification
            assert "title" in notification
            assert "message" in notification
            assert "priority" in notification
            assert "is_read" in notification
            assert "created_at" in notification
    
    @pytest.mark.asyncio
    async def test_notification_mark_read(self, client, test_user, auth_headers, db_session):
        """Test marking notifications as read."""
        # Create test notification
        from app.models.notification import Notification
        
        notification = Notification(
            user_id=test_user.id,
            type="TEST_NOTIFICATION",
            title="Test Notification",
            message="This is a test notification",
            priority="medium",
            channel="in_app"
        )
        
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        # Mark as read
        response = await client.post(f"/api/v1/notifications/{notification.id}/mark-read", headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_read"] is True
    
    @pytest.mark.asyncio
    async def test_notification_preferences(self, client, test_user, auth_headers):
        """Test notification preferences endpoints."""
        # Get current preferences
        response = await client.get("/api/v1/notifications/preferences", headers=auth_headers)
        assert response.status_code == 200
        
        preferences = response.json()
        assert "email_notifications" in preferences
        assert "sms_notifications" in preferences
        assert "push_notifications" in preferences
        
        # Update preferences
        new_preferences = {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "notification_types": {
                "prediction_alerts": True,
                "payment_reminders": False,
                "system_updates": True
            }
        }
        
        response = await client.put("/api/v1/notifications/preferences", json=new_preferences, headers=auth_headers)
        assert response.status_code == 200
        
        updated_preferences = response.json()
        assert updated_preferences["email_notifications"] is True
        assert updated_preferences["sms_notifications"] is False


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints."""
    
    @pytest.mark.asyncio
    async def test_dashboard_analytics(self, client, test_company, sample_financial_data, auth_headers):
        """Test dashboard analytics endpoint."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        dashboard = response.json()
        assert "financial_summary" in dashboard
        assert "recent_transactions" in dashboard
        assert "cash_flow_forecast" in dashboard
        assert "alerts" in dashboard
        assert "key_metrics" in dashboard
        
        # Verify financial summary structure
        financial_summary = dashboard["financial_summary"]
        assert "current_cash_flow" in financial_summary
        assert "monthly_revenue" in financial_summary
        assert "monthly_expenses" in financial_summary
        assert "working_capital" in financial_summary
    
    @pytest.mark.asyncio
    async def test_manufacturing_kpis(self, client, test_company, sample_financial_data, auth_headers):
        """Test manufacturing KPIs endpoint."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/manufacturing-kpis", headers=auth_headers)
        assert response.status_code == 200
        
        kpis = response.json()
        assert "production_efficiency" in kpis
        assert "cost_per_unit" in kpis
        assert "inventory_turnover" in kpis
        assert "capacity_utilization" in kpis
        assert "quality_metrics" in kpis
        
        # Verify KPI structure
        production_efficiency = kpis["production_efficiency"]
        assert "current_value" in production_efficiency
        assert "target_value" in production_efficiency
        assert "trend" in production_efficiency
    
    @pytest.mark.asyncio
    async def test_french_compliance_report(self, client, test_company, auth_headers):
        """Test French compliance reporting endpoint."""
        response = await client.get(f"/api/v1/companies/{test_company.id}/compliance-report", headers=auth_headers)
        assert response.status_code == 200
        
        report = response.json()
        assert "rgpd_compliance" in report
        assert "audit_trail" in report
        assert "data_retention" in report
        assert "financial_reporting" in report
        
        # Verify RGPD compliance structure
        rgpd_compliance = report["rgpd_compliance"]
        assert "data_processing_activities" in rgpd_compliance
        assert "consent_management" in rgpd_compliance
        assert "data_subject_rights" in rgpd_compliance
    
    @pytest.mark.asyncio
    async def test_export_financial_report(self, client, test_company, sample_financial_data, auth_headers):
        """Test financial report export."""
        export_request = {
            "company_id": test_company.id,
            "report_type": "financial_summary",
            "date_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "format": "pdf",
            "language": "fr"
        }
        
        response = await client.post("/api/v1/reports/export", json=export_request, headers=auth_headers)
        assert response.status_code == 200
        
        export_result = response.json()
        assert "export_id" in export_result
        assert "status" in export_result
        assert "download_url" in export_result
        
        # Test download
        download_url = export_result["download_url"]
        response = await client.get(download_url, headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestSearchEndpoints:
    """Test search and filtering endpoints."""
    
    @pytest.mark.asyncio
    async def test_financial_data_search(self, client, test_company, sample_financial_data, auth_headers):
        """Test financial data search and filtering."""
        search_params = {
            "company_id": test_company.id,
            "date_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-03-31"
            },
            "min_revenue": 140000,
            "max_expenses": 130000,
            "sort_by": "period_start",
            "sort_order": "desc"
        }
        
        response = await client.post("/api/v1/financial-data/search", json=search_params, headers=auth_headers)
        assert response.status_code == 200
        
        results = response.json()
        assert "data" in results
        assert "total_count" in results
        assert "page" in results
        assert "page_size" in results
        
        # Verify filtering worked
        for record in results["data"]:
            assert record["revenue"] >= 140000
            assert record["expenses"] <= 130000
    
    @pytest.mark.asyncio
    async def test_prediction_search(self, client, test_company, sample_predictions, auth_headers):
        """Test prediction search and filtering."""
        search_params = {
            "company_id": test_company.id,
            "prediction_type": "cash_flow",
            "min_confidence": 0.8,
            "model_version": "v1.0"
        }
        
        response = await client.post("/api/v1/predictions/search", json=search_params, headers=auth_headers)
        assert response.status_code == 200
        
        results = response.json()
        assert "data" in results
        assert "total_count" in results
        
        # Verify filtering worked
        for prediction in results["data"]:
            assert prediction["prediction_type"] == "cash_flow"
            assert prediction["confidence_score"] >= 0.8
            assert prediction["model_version"] == "v1.0"
    
    @pytest.mark.asyncio
    async def test_global_search(self, client, test_company, auth_headers):
        """Test global search across all data."""
        search_params = {
            "query": "manufacture",
            "types": ["companies", "financial_data", "predictions"],
            "company_id": test_company.id
        }
        
        response = await client.post("/api/v1/search", json=search_params, headers=auth_headers)
        assert response.status_code == 200
        
        results = response.json()
        assert "results" in results
        assert "total_count" in results
        assert "results_by_type" in results
        
        # Verify results structure
        for result in results["results"]:
            assert "type" in result
            assert "id" in result
            assert "title" in result
            assert "description" in result
            assert "relevance_score" in result


class TestPerformanceEndpoints:
    """Test performance and monitoring endpoints."""
    
    @pytest.mark.asyncio
    async def test_api_performance_metrics(self, client, auth_headers):
        """Test API performance metrics endpoint."""
        response = await client.get("/api/v1/system/performance", headers=auth_headers)
        assert response.status_code == 200
        
        metrics = response.json()
        assert "response_times" in metrics
        assert "throughput" in metrics
        assert "error_rates" in metrics
        assert "system_health" in metrics
        
        # Verify response times structure
        response_times = metrics["response_times"]
        assert "average" in response_times
        assert "p95" in response_times
        assert "p99" in response_times
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, client, auth_headers):
        """Test handling of concurrent requests."""
        import asyncio
        
        # Send multiple concurrent requests
        tasks = []
        for i in range(20):
            task = client.get("/health", headers=auth_headers)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Verify response times are reasonable
        for response in responses:
            process_time = float(response.headers.get("X-Process-Time", "0"))
            assert process_time < 1.0  # Should be under 1 second
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, client, test_company, auth_headers):
        """Test handling of large data requests."""
        # Request large amount of financial data
        response = await client.get(
            f"/api/v1/companies/{test_company.id}/financial-data",
            params={"limit": 1000, "include_details": True},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify response time is reasonable
        process_time = float(response.headers.get("X-Process-Time", "0"))
        assert process_time < 5.0  # Should be under 5 seconds for large requests
        
        # Verify data structure
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 1000  # Should respect limit


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    @pytest.mark.asyncio
    async def test_404_handling(self, client, auth_headers):
        """Test 404 error handling."""
        response = await client.get("/api/v1/companies/999999", headers=auth_headers)
        assert response.status_code == 404
        
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, client, auth_headers):
        """Test validation error handling."""
        invalid_data = {
            "name": "",  # Empty name
            "siret": "123",  # Invalid SIRET
            "email": "invalid-email"  # Invalid email
        }
        
        response = await client.post("/api/v1/companies/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        error = response.json()
        assert "detail" in error
        assert isinstance(error["detail"], list)
        
        # Verify validation errors are detailed
        for field_error in error["detail"]:
            assert "field" in field_error or "loc" in field_error
            assert "msg" in field_error
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, client):
        """Test authentication error handling."""
        # Test without token
        response = await client.get("/api/v1/companies/")
        assert response.status_code == 401
        
        error = response.json()
        assert "detail" in error
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/companies/", headers=invalid_headers)
        assert response.status_code == 401
        
        error = response.json()
        assert "detail" in error
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self, client, auth_headers):
        """Test server error handling."""
        # This would test 500 error handling by simulating server errors
        # Implementation depends on how errors are handled in the application
        pass
    
    @pytest.mark.asyncio
    async def test_rate_limiting_error(self, client, auth_headers):
        """Test rate limiting error handling."""
        # This would test rate limiting by sending too many requests
        # Implementation depends on rate limiting configuration
        pass