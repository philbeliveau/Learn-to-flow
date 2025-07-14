"""
End-to-end tests using Playwright for EZBI Analytics.
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
from typing import AsyncGenerator
import json
import os
from datetime import datetime, timedelta


class TestUserAuthentication:
    """Test user authentication flows."""
    
    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, page: Page, base_url: str):
        """Test complete user registration flow."""
        await page.goto(f"{base_url}/register")
        
        # Fill registration form
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#username", "testuser")
        await page.fill("#password", "testpassword123")
        await page.fill("#confirm_password", "testpassword123")
        await page.fill("#first_name", "Jean")
        await page.fill("#last_name", "Dupont")
        await page.fill("#phone", "+33123456789")
        await page.fill("#company_name", "Manufacture Lyonnaise SA")
        await page.fill("#company_siret", "12345678901234")
        
        # Submit registration
        await page.click("button[type='submit']")
        
        # Wait for success message
        await page.wait_for_selector(".success-message")
        success_message = await page.text_content(".success-message")
        assert "inscription réussie" in success_message.lower()
        
        # Check redirect to email verification page
        await page.wait_for_url("**/verify-email")
        
        # Verify email verification message
        verification_message = await page.text_content(".verification-message")
        assert "vérifiez votre email" in verification_message.lower()
    
    @pytest.mark.asyncio
    async def test_login_flow(self, page: Page, base_url: str):
        """Test user login flow."""
        await page.goto(f"{base_url}/login")
        
        # Fill login form
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        
        # Submit login
        await page.click("button[type='submit']")
        
        # Wait for redirect to dashboard
        await page.wait_for_url("**/dashboard")
        
        # Verify dashboard elements
        assert await page.is_visible(".dashboard-header")
        assert await page.is_visible(".financial-summary")
        assert await page.is_visible(".cash-flow-chart")
        
        # Check user menu
        await page.click(".user-menu-button")
        user_info = await page.text_content(".user-info")
        assert "Jean Dupont" in user_info
    
    @pytest.mark.asyncio
    async def test_invalid_login(self, page: Page, base_url: str):
        """Test invalid login handling."""
        await page.goto(f"{base_url}/login")
        
        # Try invalid credentials
        await page.fill("#email", "invalid@example.com")
        await page.fill("#password", "wrongpassword")
        await page.click("button[type='submit']")
        
        # Wait for error message
        await page.wait_for_selector(".error-message")
        error_message = await page.text_content(".error-message")
        assert "identifiants incorrects" in error_message.lower()
        
        # Verify still on login page
        assert "/login" in page.url
    
    @pytest.mark.asyncio
    async def test_logout_flow(self, page: Page, base_url: str):
        """Test user logout flow."""
        # First login
        await self.login_user(page, base_url)
        
        # Click logout
        await page.click(".user-menu-button")
        await page.click(".logout-button")
        
        # Wait for redirect to login
        await page.wait_for_url("**/login")
        
        # Verify login form is visible
        assert await page.is_visible("#email")
        assert await page.is_visible("#password")
        
        # Try to access protected page
        await page.goto(f"{base_url}/dashboard")
        await page.wait_for_url("**/login")
        
        # Verify redirect to login
        assert "/login" in page.url
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, page: Page, base_url: str):
        """Test password reset flow."""
        await page.goto(f"{base_url}/login")
        
        # Click forgot password
        await page.click(".forgot-password-link")
        await page.wait_for_url("**/reset-password")
        
        # Enter email
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.click("button[type='submit']")
        
        # Wait for confirmation message
        await page.wait_for_selector(".success-message")
        success_message = await page.text_content(".success-message")
        assert "email envoyé" in success_message.lower()
        
        # Simulate clicking reset link (would normally come from email)
        reset_token = "simulated_reset_token"
        await page.goto(f"{base_url}/reset-password/{reset_token}")
        
        # Fill new password
        await page.fill("#new_password", "newpassword123")
        await page.fill("#confirm_password", "newpassword123")
        await page.click("button[type='submit']")
        
        # Wait for success and redirect
        await page.wait_for_url("**/login")
        
        # Try login with new password
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "newpassword123")
        await page.click("button[type='submit']")
        
        # Should successfully login
        await page.wait_for_url("**/dashboard")
    
    async def login_user(self, page: Page, base_url: str):
        """Helper method to login a user."""
        await page.goto(f"{base_url}/login")
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")


class TestDashboardFunctionality:
    """Test dashboard functionality."""
    
    @pytest.mark.asyncio
    async def test_dashboard_loading(self, page: Page, base_url: str):
        """Test dashboard loading and initial state."""
        await self.login_user(page, base_url)
        
        # Wait for dashboard to load
        await page.wait_for_selector(".dashboard-header")
        
        # Check main sections
        assert await page.is_visible(".financial-summary")
        assert await page.is_visible(".cash-flow-chart")
        assert await page.is_visible(".recent-transactions")
        assert await page.is_visible(".predictions-panel")
        assert await page.is_visible(".alerts-panel")
        
        # Check French localization
        header_text = await page.text_content(".dashboard-header h1")
        assert "tableau de bord" in header_text.lower()
    
    @pytest.mark.asyncio
    async def test_financial_summary_widgets(self, page: Page, base_url: str):
        """Test financial summary widgets."""
        await self.login_user(page, base_url)
        
        # Check financial summary cards
        revenue_card = page.locator(".revenue-card")
        assert await revenue_card.is_visible()
        
        revenue_value = await revenue_card.locator(".value").text_content()
        assert "€" in revenue_value
        
        # Check expenses card
        expenses_card = page.locator(".expenses-card")
        assert await expenses_card.is_visible()
        
        # Check cash flow card
        cash_flow_card = page.locator(".cash-flow-card")
        assert await cash_flow_card.is_visible()
        
        # Check working capital card
        working_capital_card = page.locator(".working-capital-card")
        assert await working_capital_card.is_visible()
    
    @pytest.mark.asyncio
    async def test_cash_flow_chart_interaction(self, page: Page, base_url: str):
        """Test cash flow chart interactions."""
        await self.login_user(page, base_url)
        
        # Wait for chart to load
        await page.wait_for_selector(".cash-flow-chart")
        
        # Check chart elements
        chart = page.locator(".cash-flow-chart")
        assert await chart.is_visible()
        
        # Test time period selector
        await page.click(".time-period-selector")
        await page.click(".period-6months")
        
        # Wait for chart to update
        await page.wait_for_timeout(1000)
        
        # Check chart updated
        chart_title = await page.text_content(".chart-title")
        assert "6 mois" in chart_title.lower()
        
        # Test chart hover
        await page.hover(".chart-data-point")
        tooltip = page.locator(".chart-tooltip")
        assert await tooltip.is_visible()
        
        # Check tooltip content
        tooltip_text = await tooltip.text_content()
        assert "€" in tooltip_text
        assert "date" in tooltip_text.lower()
    
    @pytest.mark.asyncio
    async def test_predictions_panel(self, page: Page, base_url: str):
        """Test predictions panel functionality."""
        await self.login_user(page, base_url)
        
        # Wait for predictions panel
        await page.wait_for_selector(".predictions-panel")
        
        # Check predictions list
        predictions = page.locator(".prediction-item")
        prediction_count = await predictions.count()
        assert prediction_count > 0
        
        # Check first prediction
        first_prediction = predictions.first
        assert await first_prediction.is_visible()
        
        # Check prediction details
        prediction_value = await first_prediction.locator(".predicted-value").text_content()
        assert "€" in prediction_value
        
        confidence = await first_prediction.locator(".confidence-score").text_content()
        assert "%" in confidence
        
        # Test prediction details modal
        await first_prediction.click()
        
        # Wait for modal
        await page.wait_for_selector(".prediction-modal")
        modal = page.locator(".prediction-modal")
        assert await modal.is_visible()
        
        # Check modal content
        modal_title = await modal.locator(".modal-title").text_content()
        assert "prédiction" in modal_title.lower()
        
        # Close modal
        await page.click(".modal-close")
        await page.wait_for_selector(".prediction-modal", state="hidden")
    
    @pytest.mark.asyncio
    async def test_alerts_panel(self, page: Page, base_url: str):
        """Test alerts panel functionality."""
        await self.login_user(page, base_url)
        
        # Wait for alerts panel
        await page.wait_for_selector(".alerts-panel")
        
        # Check alerts
        alerts = page.locator(".alert-item")
        
        # If alerts exist, test them
        if await alerts.count() > 0:
            first_alert = alerts.first
            assert await first_alert.is_visible()
            
            # Check alert priority
            priority = await first_alert.get_attribute("data-priority")
            assert priority in ["low", "medium", "high", "urgent"]
            
            # Test alert dismissal
            dismiss_button = first_alert.locator(".dismiss-alert")
            if await dismiss_button.is_visible():
                await dismiss_button.click()
                
                # Wait for alert to be dismissed
                await page.wait_for_timeout(500)
                
                # Check alert is hidden or removed
                assert not await first_alert.is_visible()
    
    @pytest.mark.asyncio
    async def test_recent_transactions(self, page: Page, base_url: str):
        """Test recent transactions section."""
        await self.login_user(page, base_url)
        
        # Wait for transactions section
        await page.wait_for_selector(".recent-transactions")
        
        # Check transaction list
        transactions = page.locator(".transaction-item")
        
        if await transactions.count() > 0:
            first_transaction = transactions.first
            assert await first_transaction.is_visible()
            
            # Check transaction details
            amount = await first_transaction.locator(".transaction-amount").text_content()
            assert "€" in amount
            
            date = await first_transaction.locator(".transaction-date").text_content()
            assert len(date) > 0
            
            description = await first_transaction.locator(".transaction-description").text_content()
            assert len(description) > 0
        
        # Test "View All" link
        view_all_link = page.locator(".view-all-transactions")
        if await view_all_link.is_visible():
            await view_all_link.click()
            await page.wait_for_url("**/transactions")
            
            # Check transactions page
            assert await page.is_visible(".transactions-header")
            assert await page.is_visible(".transactions-table")
    
    async def login_user(self, page: Page, base_url: str):
        """Helper method to login a user."""
        await page.goto(f"{base_url}/login")
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")


class TestFinancialDataManagement:
    """Test financial data management workflows."""
    
    @pytest.mark.asyncio
    async def test_manual_data_entry(self, page: Page, base_url: str):
        """Test manual financial data entry."""
        await self.login_user(page, base_url)
        
        # Navigate to data entry
        await page.click(".nav-financial-data")
        await page.wait_for_url("**/financial-data")
        
        # Click add new data
        await page.click(".add-financial-data")
        
        # Fill form
        await page.fill("#period_start", "2024-04-01")
        await page.fill("#period_end", "2024-04-30")
        await page.fill("#revenue", "165000")
        await page.fill("#expenses", "123750")
        await page.fill("#accounts_receivable", "66000")
        await page.fill("#accounts_payable", "49500")
        await page.fill("#inventory", "41250")
        await page.fill("#raw_materials_cost", "57750")
        await page.fill("#labor_cost", "41250")
        await page.fill("#overhead_cost", "24750")
        await page.fill("#production_volume", "1320")
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Wait for success message
        await page.wait_for_selector(".success-message")
        success_message = await page.text_content(".success-message")
        assert "données ajoutées" in success_message.lower()
        
        # Verify data appears in table
        await page.wait_for_selector(".financial-data-table")
        table_rows = page.locator(".financial-data-table tbody tr")
        assert await table_rows.count() > 0
        
        # Check first row contains our data
        first_row = table_rows.first
        revenue_cell = await first_row.locator(".revenue-cell").text_content()
        assert "165 000" in revenue_cell
    
    @pytest.mark.asyncio
    async def test_file_upload_workflow(self, page: Page, base_url: str):
        """Test file upload workflow."""
        await self.login_user(page, base_url)
        
        # Navigate to file upload
        await page.click(".nav-financial-data")
        await page.click(".upload-data-button")
        
        # Wait for upload modal
        await page.wait_for_selector(".upload-modal")
        
        # Test drag and drop area
        upload_area = page.locator(".upload-dropzone")
        assert await upload_area.is_visible()
        
        # Check upload instructions
        instructions = await upload_area.locator(".upload-instructions").text_content()
        assert "glissez" in instructions.lower() or "déposez" in instructions.lower()
        
        # Test file selection
        file_input = page.locator("input[type='file']")
        
        # Create test file content
        test_file_content = """Date,Chiffre d'affaires,Charges,Créances clients,Dettes fournisseurs,Stocks,Trésorerie
2024-04-01,165000,123750,66000,49500,41250,22500"""
        
        # Upload file (simulated)
        await file_input.set_input_files({
            "name": "donnees_financieres.csv",
            "mimeType": "text/csv",
            "buffer": test_file_content.encode()
        })
        
        # Wait for file processing
        await page.wait_for_selector(".file-processing")
        
        # Check processing status
        processing_status = page.locator(".processing-status")
        assert await processing_status.is_visible()
        
        # Wait for completion
        await page.wait_for_selector(".processing-complete")
        
        # Check results
        results = await page.text_content(".upload-results")
        assert "importé" in results.lower()
        
        # Close modal
        await page.click(".modal-close")
        
        # Verify data in table
        await page.wait_for_selector(".financial-data-table")
        table_rows = page.locator(".financial-data-table tbody tr")
        row_count = await table_rows.count()
        assert row_count > 0
    
    @pytest.mark.asyncio
    async def test_data_validation_errors(self, page: Page, base_url: str):
        """Test data validation error handling."""
        await self.login_user(page, base_url)
        
        # Navigate to data entry
        await page.click(".nav-financial-data")
        await page.click(".add-financial-data")
        
        # Fill form with invalid data
        await page.fill("#period_start", "2024-04-01")
        await page.fill("#period_end", "2024-03-31")  # End before start
        await page.fill("#revenue", "-1000")  # Negative revenue
        await page.fill("#expenses", "invalid")  # Invalid number
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Check validation errors
        await page.wait_for_selector(".validation-errors")
        
        # Check specific error messages
        period_error = page.locator(".period-error")
        assert await period_error.is_visible()
        
        revenue_error = page.locator(".revenue-error")
        assert await revenue_error.is_visible()
        
        expenses_error = page.locator(".expenses-error")
        assert await expenses_error.is_visible()
        
        # Fix errors and resubmit
        await page.fill("#period_end", "2024-04-30")
        await page.fill("#revenue", "150000")
        await page.fill("#expenses", "112500")
        
        # Submit again
        await page.click("button[type='submit']")
        
        # Should succeed this time
        await page.wait_for_selector(".success-message")
    
    @pytest.mark.asyncio
    async def test_data_editing_workflow(self, page: Page, base_url: str):
        """Test editing existing financial data."""
        await self.login_user(page, base_url)
        
        # Navigate to financial data
        await page.click(".nav-financial-data")
        await page.wait_for_selector(".financial-data-table")
        
        # Click edit on first row
        first_row = page.locator(".financial-data-table tbody tr").first
        await first_row.locator(".edit-button").click()
        
        # Wait for edit modal
        await page.wait_for_selector(".edit-modal")
        
        # Update revenue
        await page.fill("#revenue", "175000")
        
        # Submit changes
        await page.click(".save-changes")
        
        # Wait for success message
        await page.wait_for_selector(".success-message")
        
        # Verify changes in table
        await page.wait_for_timeout(1000)
        updated_revenue = await first_row.locator(".revenue-cell").text_content()
        assert "175 000" in updated_revenue
    
    @pytest.mark.asyncio
    async def test_data_deletion_workflow(self, page: Page, base_url: str):
        """Test deleting financial data."""
        await self.login_user(page, base_url)
        
        # Navigate to financial data
        await page.click(".nav-financial-data")
        await page.wait_for_selector(".financial-data-table")
        
        # Count initial rows
        initial_count = await page.locator(".financial-data-table tbody tr").count()
        
        # Click delete on first row
        first_row = page.locator(".financial-data-table tbody tr").first
        await first_row.locator(".delete-button").click()
        
        # Wait for confirmation dialog
        await page.wait_for_selector(".delete-confirmation")
        
        # Confirm deletion
        await page.click(".confirm-delete")
        
        # Wait for success message
        await page.wait_for_selector(".success-message")
        
        # Verify row count decreased
        await page.wait_for_timeout(1000)
        final_count = await page.locator(".financial-data-table tbody tr").count()
        assert final_count == initial_count - 1
    
    async def login_user(self, page: Page, base_url: str):
        """Helper method to login a user."""
        await page.goto(f"{base_url}/login")
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")


class TestPredictionWorkflows:
    """Test prediction and forecasting workflows."""
    
    @pytest.mark.asyncio
    async def test_cash_flow_prediction_request(self, page: Page, base_url: str):
        """Test requesting cash flow predictions."""
        await self.login_user(page, base_url)
        
        # Navigate to predictions
        await page.click(".nav-predictions")
        await page.wait_for_url("**/predictions")
        
        # Click generate prediction
        await page.click(".generate-prediction")
        
        # Wait for prediction form
        await page.wait_for_selector(".prediction-form")
        
        # Select prediction type
        await page.select_option("#prediction_type", "cash_flow")
        
        # Select time horizon
        await page.select_option("#prediction_horizon", "90")
        
        # Enable confidence intervals
        await page.check("#include_confidence")
        
        # Submit prediction request
        await page.click("button[type='submit']")
        
        # Wait for processing
        await page.wait_for_selector(".prediction-processing")
        
        # Check processing status
        processing_message = await page.text_content(".processing-message")
        assert "génération" in processing_message.lower()
        
        # Wait for completion
        await page.wait_for_selector(".prediction-results")
        
        # Check results
        results = page.locator(".prediction-results")
        assert await results.is_visible()
        
        # Check prediction chart
        chart = page.locator(".prediction-chart")
        assert await chart.is_visible()
        
        # Check prediction values
        predictions = page.locator(".prediction-value")
        prediction_count = await predictions.count()
        assert prediction_count > 0
        
        # Check confidence indicators
        confidence_indicators = page.locator(".confidence-indicator")
        assert await confidence_indicators.first.is_visible()
    
    @pytest.mark.asyncio
    async def test_scenario_analysis(self, page: Page, base_url: str):
        """Test scenario analysis functionality."""
        await self.login_user(page, base_url)
        
        # Navigate to scenario analysis
        await page.click(".nav-predictions")
        await page.click(".scenario-analysis-tab")
        
        # Wait for scenario form
        await page.wait_for_selector(".scenario-form")
        
        # Add optimistic scenario
        await page.click(".add-scenario")
        await page.fill("#scenario_name", "Optimiste")
        await page.fill("#revenue_adjustment", "15")
        await page.fill("#expense_adjustment", "-5")
        await page.click(".save-scenario")
        
        # Add pessimistic scenario
        await page.click(".add-scenario")
        await page.fill("#scenario_name", "Pessimiste")
        await page.fill("#revenue_adjustment", "-10")
        await page.fill("#expense_adjustment", "8")
        await page.click(".save-scenario")
        
        # Run scenario analysis
        await page.click(".run-scenarios")
        
        # Wait for results
        await page.wait_for_selector(".scenario-results")
        
        # Check scenario comparison chart
        comparison_chart = page.locator(".scenario-comparison-chart")
        assert await comparison_chart.is_visible()
        
        # Check scenario summary
        scenario_summaries = page.locator(".scenario-summary")
        assert await scenario_summaries.count() >= 2
        
        # Verify scenario names
        optimistic_summary = page.locator(".scenario-summary[data-scenario='Optimiste']")
        assert await optimistic_summary.is_visible()
        
        pessimistic_summary = page.locator(".scenario-summary[data-scenario='Pessimiste']")
        assert await pessimistic_summary.is_visible()
    
    @pytest.mark.asyncio
    async def test_prediction_history(self, page: Page, base_url: str):
        """Test prediction history and accuracy tracking."""
        await self.login_user(page, base_url)
        
        # Navigate to prediction history
        await page.click(".nav-predictions")
        await page.click(".prediction-history-tab")
        
        # Wait for history table
        await page.wait_for_selector(".prediction-history-table")
        
        # Check table headers
        headers = page.locator(".prediction-history-table th")
        header_count = await headers.count()
        assert header_count >= 6  # Date, Type, Predicted, Actual, Accuracy, etc.
        
        # Check prediction entries
        rows = page.locator(".prediction-history-table tbody tr")
        
        if await rows.count() > 0:
            first_row = rows.first
            
            # Check prediction details
            prediction_type = await first_row.locator(".prediction-type").text_content()
            assert prediction_type in ["Cash Flow", "Revenue", "Expenses"]
            
            # Check accuracy indicator
            accuracy_indicator = first_row.locator(".accuracy-indicator")
            assert await accuracy_indicator.is_visible()
            
            # Test prediction details modal
            await first_row.locator(".view-details").click()
            
            # Wait for modal
            await page.wait_for_selector(".prediction-details-modal")
            
            # Check modal content
            modal = page.locator(".prediction-details-modal")
            assert await modal.is_visible()
            
            # Check prediction chart in modal
            modal_chart = modal.locator(".prediction-chart")
            assert await modal_chart.is_visible()
            
            # Close modal
            await page.click(".modal-close")
    
    @pytest.mark.asyncio
    async def test_model_performance_dashboard(self, page: Page, base_url: str):
        """Test model performance dashboard."""
        await self.login_user(page, base_url)
        
        # Navigate to model performance
        await page.click(".nav-predictions")
        await page.click(".model-performance-tab")
        
        # Wait for performance dashboard
        await page.wait_for_selector(".model-performance-dashboard")
        
        # Check accuracy metrics
        accuracy_metrics = page.locator(".accuracy-metrics")
        assert await accuracy_metrics.is_visible()
        
        # Check overall accuracy
        overall_accuracy = page.locator(".overall-accuracy")
        accuracy_text = await overall_accuracy.text_content()
        assert "%" in accuracy_text
        
        # Check accuracy by time horizon
        horizon_accuracy = page.locator(".horizon-accuracy-chart")
        assert await horizon_accuracy.is_visible()
        
        # Check model comparison
        model_comparison = page.locator(".model-comparison")
        assert await model_comparison.is_visible()
        
        # Check error distribution
        error_distribution = page.locator(".error-distribution-chart")
        assert await error_distribution.is_visible()
        
        # Test model selection
        model_selector = page.locator(".model-selector")
        if await model_selector.is_visible():
            await model_selector.select_option("lstm_attention")
            
            # Wait for dashboard update
            await page.wait_for_timeout(1000)
            
            # Check that dashboard updated
            selected_model = await page.text_content(".selected-model")
            assert "LSTM" in selected_model
    
    async def login_user(self, page: Page, base_url: str):
        """Helper method to login a user."""
        await page.goto(f"{base_url}/login")
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")


class TestIntegrationWorkflows:
    """Test ERP and banking integration workflows."""
    
    @pytest.mark.asyncio
    async def test_sage_integration_setup(self, page: Page, base_url: str):
        """Test Sage ERP integration setup."""
        await self.login_user(page, base_url)
        
        # Navigate to integrations
        await page.click(".nav-integrations")
        await page.wait_for_url("**/integrations")
        
        # Click add integration
        await page.click(".add-integration")
        
        # Select Sage integration
        await page.select_option("#integration_type", "sage")
        
        # Fill configuration
        await page.fill("#integration_name", "Sage 100 Production")
        await page.fill("#api_url", "https://sage.company.com/api")
        await page.fill("#username", "integration_user")
        await page.fill("#password", "integration_password")
        
        # Select sync frequency
        await page.select_option("#sync_frequency", "daily")
        
        # Configure data mapping
        await page.fill("#revenue_mapping", "411000")
        await page.fill("#expenses_mapping", "401000")
        
        # Test connection
        await page.click(".test-connection")
        
        # Wait for connection test
        await page.wait_for_selector(".connection-test-result")
        
        # Check test result
        test_result = await page.text_content(".connection-test-result")
        assert "connexion réussie" in test_result.lower()
        
        # Save integration
        await page.click("button[type='submit']")
        
        # Wait for success message
        await page.wait_for_selector(".success-message")
        
        # Verify integration in list
        await page.wait_for_selector(".integration-list")
        integrations = page.locator(".integration-item")
        assert await integrations.count() > 0
        
        # Check integration status
        first_integration = integrations.first
        status = await first_integration.locator(".integration-status").text_content()
        assert "actif" in status.lower()
    
    @pytest.mark.asyncio
    async def test_banking_integration_setup(self, page: Page, base_url: str):
        """Test banking integration setup."""
        await self.login_user(page, base_url)
        
        # Navigate to integrations
        await page.click(".nav-integrations")
        await page.click(".add-integration")
        
        # Select banking integration
        await page.select_option("#integration_type", "open_banking")
        
        # Fill configuration
        await page.fill("#integration_name", "Crédit Agricole")
        await page.select_option("#bank_provider", "credit_agricole")
        await page.fill("#account_iban", "FR1420041010050500013M02606")
        
        # Accept terms
        await page.check("#accept_terms")
        
        # Initiate connection
        await page.click(".connect-bank")
        
        # Wait for bank authentication redirect
        await page.wait_for_url("**/bank-auth*")
        
        # Simulate bank authentication
        await page.fill("#bank_username", "test_user")
        await page.fill("#bank_password", "test_password")
        await page.click(".bank-login")
        
        # Wait for consent screen
        await page.wait_for_selector(".consent-screen")
        
        # Accept consent
        await page.click(".accept-consent")
        
        # Wait for redirect back to application
        await page.wait_for_url("**/integrations")
        
        # Check integration success
        await page.wait_for_selector(".integration-success")
        success_message = await page.text_content(".integration-success")
        assert "connexion bancaire établie" in success_message.lower()
    
    @pytest.mark.asyncio
    async def test_integration_sync_monitoring(self, page: Page, base_url: str):
        """Test integration sync monitoring."""
        await self.login_user(page, base_url)
        
        # Navigate to integrations
        await page.click(".nav-integrations")
        
        # Click on existing integration
        integration = page.locator(".integration-item").first
        await integration.click()
        
        # Wait for integration details
        await page.wait_for_selector(".integration-details")
        
        # Check sync status
        sync_status = page.locator(".sync-status")
        assert await sync_status.is_visible()
        
        # Check last sync time
        last_sync = page.locator(".last-sync-time")
        assert await last_sync.is_visible()
        
        # Check sync logs
        sync_logs = page.locator(".sync-logs")
        assert await sync_logs.is_visible()
        
        # Test manual sync
        manual_sync_button = page.locator(".manual-sync")
        if await manual_sync_button.is_visible():
            await manual_sync_button.click()
            
            # Wait for sync to start
            await page.wait_for_selector(".sync-in-progress")
            
            # Check sync progress
            progress = page.locator(".sync-progress")
            assert await progress.is_visible()
            
            # Wait for sync completion
            await page.wait_for_selector(".sync-complete")
            
            # Check sync results
            sync_results = await page.text_content(".sync-results")
            assert "synchronisé" in sync_results.lower()
    
    @pytest.mark.asyncio
    async def test_integration_data_mapping(self, page: Page, base_url: str):
        """Test integration data mapping configuration."""
        await self.login_user(page, base_url)
        
        # Navigate to integrations
        await page.click(".nav-integrations")
        
        # Click on existing integration
        integration = page.locator(".integration-item").first
        await integration.locator(".configure-mapping").click()
        
        # Wait for mapping configuration
        await page.wait_for_selector(".data-mapping-config")
        
        # Check mapping fields
        mapping_fields = page.locator(".mapping-field")
        assert await mapping_fields.count() > 0
        
        # Test revenue mapping
        revenue_mapping = page.locator("#revenue_mapping")
        await revenue_mapping.fill("411000")
        
        # Test expenses mapping
        expenses_mapping = page.locator("#expenses_mapping")
        await expenses_mapping.fill("401000")
        
        # Test field validation
        await page.click(".validate-mapping")
        
        # Wait for validation results
        await page.wait_for_selector(".validation-results")
        
        # Check validation success
        validation_message = await page.text_content(".validation-results")
        assert "validation réussie" in validation_message.lower()
        
        # Save mapping
        await page.click(".save-mapping")
        
        # Wait for success message
        await page.wait_for_selector(".success-message")
    
    async def login_user(self, page: Page, base_url: str):
        """Helper method to login a user."""
        await page.goto(f"{base_url}/login")
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")


class TestReportingWorkflows:
    """Test reporting and analytics workflows."""
    
    @pytest.mark.asyncio
    async def test_financial_report_generation(self, page: Page, base_url: str):
        """Test financial report generation."""
        await self.login_user(page, base_url)
        
        # Navigate to reports
        await page.click(".nav-reports")
        await page.wait_for_url("**/reports")
        
        # Select report type
        await page.select_option("#report_type", "financial_summary")
        
        # Select date range
        await page.fill("#start_date", "2024-01-01")
        await page.fill("#end_date", "2024-12-31")
        
        # Select format
        await page.select_option("#report_format", "pdf")
        
        # Select language
        await page.select_option("#report_language", "fr")
        
        # Generate report
        await page.click(".generate-report")
        
        # Wait for report generation
        await page.wait_for_selector(".report-generation")
        
        # Check generation progress
        progress = page.locator(".generation-progress")
        assert await progress.is_visible()
        
        # Wait for completion
        await page.wait_for_selector(".report-ready")
        
        # Check download link
        download_link = page.locator(".download-report")
        assert await download_link.is_visible()
        
        # Test download
        with page.expect_download() as download_info:
            await download_link.click()
        
        download = await download_info.value
        assert download.suggested_filename.endswith(".pdf")
    
    @pytest.mark.asyncio
    async def test_manufacturing_kpi_dashboard(self, page: Page, base_url: str):
        """Test manufacturing KPI dashboard."""
        await self.login_user(page, base_url)
        
        # Navigate to manufacturing KPIs
        await page.click(".nav-analytics")
        await page.click(".manufacturing-kpis-tab")
        
        # Wait for KPI dashboard
        await page.wait_for_selector(".manufacturing-kpis")
        
        # Check production efficiency
        production_efficiency = page.locator(".production-efficiency")
        assert await production_efficiency.is_visible()
        
        efficiency_value = await production_efficiency.locator(".kpi-value").text_content()
        assert "%" in efficiency_value
        
        # Check cost per unit
        cost_per_unit = page.locator(".cost-per-unit")
        assert await cost_per_unit.is_visible()
        
        cost_value = await cost_per_unit.locator(".kpi-value").text_content()
        assert "€" in cost_value
        
        # Check inventory turnover
        inventory_turnover = page.locator(".inventory-turnover")
        assert await inventory_turnover.is_visible()
        
        # Check capacity utilization
        capacity_utilization = page.locator(".capacity-utilization")
        assert await capacity_utilization.is_visible()
        
        # Test KPI drill-down
        await production_efficiency.click()
        
        # Wait for drill-down modal
        await page.wait_for_selector(".kpi-detail-modal")
        
        # Check detailed chart
        detail_chart = page.locator(".kpi-detail-chart")
        assert await detail_chart.is_visible()
        
        # Check trend analysis
        trend_analysis = page.locator(".trend-analysis")
        assert await trend_analysis.is_visible()
        
        # Close modal
        await page.click(".modal-close")
    
    @pytest.mark.asyncio
    async def test_compliance_reporting(self, page: Page, base_url: str):
        """Test French compliance reporting."""
        await self.login_user(page, base_url)
        
        # Navigate to compliance
        await page.click(".nav-compliance")
        await page.wait_for_url("**/compliance")
        
        # Check RGPD compliance section
        rgpd_section = page.locator(".rgpd-compliance")
        assert await rgpd_section.is_visible()
        
        # Check data processing activities
        data_processing = page.locator(".data-processing-activities")
        assert await data_processing.is_visible()
        
        # Check audit trail
        audit_trail = page.locator(".audit-trail")
        assert await audit_trail.is_visible()
        
        # Test audit log export
        await page.click(".export-audit-log")
        
        # Wait for export options
        await page.wait_for_selector(".export-options")
        
        # Select date range
        await page.fill("#audit_start_date", "2024-01-01")
        await page.fill("#audit_end_date", "2024-12-31")
        
        # Select format
        await page.select_option("#audit_format", "csv")
        
        # Export
        await page.click(".export-audit")
        
        # Wait for export completion
        await page.wait_for_selector(".export-ready")
        
        # Download audit log
        with page.expect_download() as download_info:
            await page.click(".download-audit-log")
        
        download = await download_info.value
        assert download.suggested_filename.endswith(".csv")
    
    async def login_user(self, page: Page, base_url: str):
        """Helper method to login a user."""
        await page.goto(f"{base_url}/login")
        await page.fill("#email", "test@manufacture-lyon.fr")
        await page.fill("#password", "testpassword123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")


# Playwright fixtures and configuration
@pytest.fixture(scope="session")
async def browser_context():
    """Create browser context for tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="fr-FR",
            timezone_id="Europe/Paris"
        )
        yield context
        await context.close()
        await browser.close()


@pytest.fixture
async def page(browser_context):
    """Create page for tests."""
    page = await browser_context.new_page()
    yield page
    await page.close()


@pytest.fixture
def base_url():
    """Base URL for the application."""
    return os.getenv("BASE_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def event_loop():
    """Event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()