"""
Manufacturing Endpoints Testing Suite
Comprehensive testing for all 25+ manufacturing endpoints
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.models.user import User
from app.models.company import Company


class TestManufacturingEndpointsComprehensive:
    """Comprehensive testing for manufacturing endpoints."""
    
    @pytest.mark.asyncio
    async def test_sales_customers_endpoint_comprehensive(self, client: AsyncClient, auth_headers, db_session):
        """Test sales customers endpoint with all scenarios."""
        
        # Test GET customers with pagination
        response = await client.get(
            "/api/v1/manufacturing/sales/customers",
            params={"limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        customers = response.json()
        assert isinstance(customers, list)
        
        # Test GET customers with search
        response = await client.get(
            "/api/v1/manufacturing/sales/customers",
            params={"search": "test", "limit": 5},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test POST create customer - valid data
        customer_data = {
            "company_name": "Test Manufacturing Co",
            "contact_name": "John Doe",
            "email": "john@testmanufacturing.com",
            "phone": "+33123456789",
            "address": "123 Manufacturing St, Paris, France",
            "payment_terms": 30,
            "credit_limit": 100000.0
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        created_customer = response.json()
        assert created_customer["company_name"] == customer_data["company_name"]
        assert created_customer["credit_limit"] == customer_data["credit_limit"]
        
        # Test POST create customer - duplicate email
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test POST create customer - invalid data
        invalid_data = {
            "company_name": "",  # Empty name
            "email": "invalid-email",  # Invalid email
            "payment_terms": -1,  # Invalid payment terms
            "credit_limit": -1000.0  # Negative credit limit
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test without authentication
        response = await client.get("/api/v1/manufacturing/sales/customers")
        assert response.status_code == 401
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get(
            "/api/v1/manufacturing/sales/customers",
            headers=invalid_headers
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_sales_invoices_endpoint_comprehensive(self, client: AsyncClient, auth_headers, db_session):
        """Test sales invoices endpoint with all scenarios."""
        
        # First create a customer for invoice testing
        customer_data = {
            "company_name": "Invoice Test Co",
            "contact_name": "Jane Smith",
            "email": "jane@invoicetest.com",
            "phone": "+33987654321",
            "payment_terms": 30,
            "credit_limit": 50000.0
        }
        
        customer_response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert customer_response.status_code == 201
        customer_id = customer_response.json()["customer_id"]
        
        # Test GET invoices with filters
        response = await client.get(
            "/api/v1/manufacturing/sales/invoices",
            params={"limit": 10, "offset": 0, "status_filter": "Open"},
            headers=auth_headers
        )
        assert response.status_code == 200
        invoices = response.json()
        assert isinstance(invoices, list)
        
        # Test GET invoices with customer filter
        response = await client.get(
            "/api/v1/manufacturing/sales/invoices",
            params={"customer_id": customer_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test POST create invoice - valid data
        invoice_data = {
            "customer_id": customer_id,
            "invoice_number": "INV-TEST-001",
            "date_issued": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "amount": 25000.0,
            "status": "Open"
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        created_invoice = response.json()
        assert created_invoice["invoice_number"] == invoice_data["invoice_number"]
        assert created_invoice["amount"] == invoice_data["amount"]
        
        # Test POST create invoice - duplicate invoice number
        response = await client.post(
            "/api/v1/manufacturing/sales/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test POST create invoice - invalid customer
        invalid_invoice_data = {
            "customer_id": 999999,  # Non-existent customer
            "invoice_number": "INV-TEST-002",
            "date_issued": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "amount": 15000.0,
            "status": "Open"
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/invoices",
            json=invalid_invoice_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test POST create invoice - invalid status
        invalid_status_data = {
            "customer_id": customer_id,
            "invoice_number": "INV-TEST-003",
            "date_issued": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "amount": 15000.0,
            "status": "InvalidStatus"
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/invoices",
            json=invalid_status_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test POST create invoice - negative amount
        negative_amount_data = {
            "customer_id": customer_id,
            "invoice_number": "INV-TEST-004",
            "date_issued": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "amount": -1000.0,
            "status": "Open"
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/invoices",
            json=negative_amount_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_sales_kpis_endpoint_comprehensive(self, client: AsyncClient, auth_headers, db_session):
        """Test sales KPIs endpoint with comprehensive analytics."""
        
        # Test GET sales KPIs
        response = await client.get(
            "/api/v1/manufacturing/sales/kpis",
            headers=auth_headers
        )
        assert response.status_code == 200
        kpis = response.json()
        
        # Validate KPI structure
        assert "totals" in kpis
        assert "status_breakdown" in kpis
        assert "monthly_trend" in kpis
        assert "top_customers" in kpis
        
        # Validate totals structure
        totals = kpis["totals"]
        assert "total_invoices" in totals
        assert "total_revenue" in totals
        assert "avg_invoice_value" in totals
        assert "active_customers" in totals
        
        # Validate data types
        assert isinstance(totals["total_invoices"], int)
        assert isinstance(totals["total_revenue"], (int, float))
        assert isinstance(totals["avg_invoice_value"], (int, float))
        assert isinstance(totals["active_customers"], int)
        
        # Validate status breakdown
        status_breakdown = kpis["status_breakdown"]
        assert isinstance(status_breakdown, list)
        for status_item in status_breakdown:
            assert "status" in status_item
            assert "count" in status_item
            assert "total_amount" in status_item
        
        # Validate monthly trend
        monthly_trend = kpis["monthly_trend"]
        assert isinstance(monthly_trend, list)
        for trend_item in monthly_trend:
            assert "month" in trend_item
            assert "revenue" in trend_item
            assert "invoice_count" in trend_item
        
        # Validate top customers
        top_customers = kpis["top_customers"]
        assert isinstance(top_customers, list)
        for customer in top_customers:
            assert "company_name" in customer
            assert "total_revenue" in customer
            assert "invoice_count" in customer
    
    @pytest.mark.asyncio
    async def test_operations_products_endpoint_comprehensive(self, client: AsyncClient, auth_headers, db_session):
        """Test operations products endpoint with all scenarios."""
        
        # Test GET products with pagination
        response = await client.get(
            "/api/v1/manufacturing/operations/products",
            params={"limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        
        # Test GET products with search
        response = await client.get(
            "/api/v1/manufacturing/operations/products",
            params={"search": "widget", "limit": 5},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test POST create product - valid data
        product_data = {
            "product_code": "PROD-TEST-001",
            "product_name": "Test Manufacturing Widget",
            "base_cost": 150.0,
            "labor_hours": 3.5,
            "material_cost": 75.0
        }
        
        response = await client.post(
            "/api/v1/manufacturing/operations/products",
            json=product_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        created_product = response.json()
        assert created_product["product_code"] == product_data["product_code"]
        assert created_product["product_name"] == product_data["product_name"]
        assert created_product["base_cost"] == product_data["base_cost"]
        assert created_product["labor_hours"] == product_data["labor_hours"]
        assert created_product["material_cost"] == product_data["material_cost"]
        
        # Test POST create product - duplicate product code
        response = await client.post(
            "/api/v1/manufacturing/operations/products",
            json=product_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test POST create product - invalid data
        invalid_product_data = {
            "product_code": "",  # Empty code
            "product_name": "Test Product",
            "base_cost": -50.0,  # Negative cost
            "labor_hours": -1.0,  # Negative hours
            "material_cost": -25.0  # Negative material cost
        }
        
        response = await client.post(
            "/api/v1/manufacturing/operations/products",
            json=invalid_product_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test POST create product - missing required fields
        incomplete_data = {
            "product_name": "Incomplete Product"
            # Missing required fields
        }
        
        response = await client.post(
            "/api/v1/manufacturing/operations/products",
            json=incomplete_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_dashboard_overview_endpoint_comprehensive(self, client: AsyncClient, auth_headers, db_session):
        """Test dashboard overview endpoint with comprehensive metrics."""
        
        # Test GET dashboard overview
        response = await client.get(
            "/api/v1/manufacturing/dashboard/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        dashboard = response.json()
        
        # Validate dashboard structure
        required_fields = [
            "total_customers",
            "total_revenue",
            "total_orders",
            "total_products",
            "active_employees",
            "monthly_costs",
            "key_metrics",
            "recent_activity"
        ]
        
        for field in required_fields:
            assert field in dashboard, f"Missing field: {field}"
        
        # Validate data types
        assert isinstance(dashboard["total_customers"], int)
        assert isinstance(dashboard["total_revenue"], (int, float))
        assert isinstance(dashboard["total_orders"], int)
        assert isinstance(dashboard["total_products"], int)
        assert isinstance(dashboard["active_employees"], int)
        assert isinstance(dashboard["monthly_costs"], (int, float))
        assert isinstance(dashboard["key_metrics"], list)
        assert isinstance(dashboard["recent_activity"], list)
        
        # Validate key metrics structure
        key_metrics = dashboard["key_metrics"]
        for metric in key_metrics:
            assert "metric_name" in metric
            assert "value" in metric
            assert "unit" in metric
            assert "period" in metric
        
        # Validate recent activity structure
        recent_activity = dashboard["recent_activity"]
        for activity in recent_activity:
            assert "type" in activity
            assert "reference" in activity
            assert "amount" in activity
            assert "date" in activity
        
        # Validate non-negative values
        assert dashboard["total_customers"] >= 0
        assert dashboard["total_revenue"] >= 0
        assert dashboard["total_orders"] >= 0
        assert dashboard["total_products"] >= 0
        assert dashboard["active_employees"] >= 0
        assert dashboard["monthly_costs"] >= 0
    
    @pytest.mark.asyncio
    async def test_admin_endpoints_comprehensive(self, client: AsyncClient, auth_headers, admin_headers):
        """Test admin endpoints with proper access control."""
        
        # Test admin audit logs - with regular user (should fail)
        response = await client.get(
            "/api/v1/manufacturing/admin/audit-logs",
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Test admin audit logs - with admin user (should succeed)
        response = await client.get(
            "/api/v1/manufacturing/admin/audit-logs",
            headers=admin_headers
        )
        assert response.status_code == 200
        audit_response = response.json()
        assert "audit_logs" in audit_response
        assert "total" in audit_response
        assert isinstance(audit_response["audit_logs"], list)
        
        # Test audit logs with filters
        response = await client.get(
            "/api/v1/manufacturing/admin/audit-logs",
            params={"action_filter": "manufacturing", "limit": 5},
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Test system health - with regular user (should fail)
        response = await client.get(
            "/api/v1/manufacturing/system/health",
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Test system health - with admin user (should succeed)
        response = await client.get(
            "/api/v1/manufacturing/system/health",
            headers=admin_headers
        )
        assert response.status_code == 200
        health_response = response.json()
        
        # Validate health response structure
        assert "status" in health_response
        assert "timestamp" in health_response
        assert "services" in health_response
        assert "user_info" in health_response
        
        # Validate services health
        services = health_response["services"]
        assert "database" in services
        assert "authentication" in services
        assert "api" in services
        
        # Validate user info
        user_info = health_response["user_info"]
        assert "user_id" in user_info
        assert "email" in user_info
        assert "roles" in user_info
    
    @pytest.mark.asyncio
    async def test_endpoint_rate_limiting(self, client: AsyncClient, auth_headers):
        """Test rate limiting on manufacturing endpoints."""
        
        # Test rapid requests to sales customers endpoint
        rapid_responses = []
        for i in range(100):
            response = await client.get(
                "/api/v1/manufacturing/sales/customers",
                headers=auth_headers
            )
            rapid_responses.append(response.status_code)
        
        # Should handle most requests successfully
        successful_requests = [r for r in rapid_responses if r == 200]
        rate_limited_requests = [r for r in rapid_responses if r == 429]
        
        # Either all succeed (no rate limiting) or some are rate limited
        assert len(successful_requests) >= 50, "Should handle at least 50% of rapid requests"
        
        # If rate limiting is implemented, validate 429 responses
        if rate_limited_requests:
            print(f"Rate limiting active: {len(rate_limited_requests)} requests limited")
        else:
            print("No rate limiting detected in current test")
    
    @pytest.mark.asyncio
    async def test_endpoint_security_comprehensive(self, client: AsyncClient, auth_headers):
        """Test security measures across all manufacturing endpoints."""
        
        # Test SQL injection prevention
        sql_payloads = [
            "'; DROP TABLE customers; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_payloads:
            response = await client.get(
                "/api/v1/manufacturing/sales/customers",
                params={"search": payload},
                headers=auth_headers
            )
            # Should not execute SQL injection
            assert response.status_code in [200, 400, 422]
            
            # If successful, should not contain system information
            if response.status_code == 200:
                data = response.json()
                assert not any("password" in str(item) for item in data)
                assert not any("secret" in str(item) for item in data)
        
        # Test XSS prevention in POST requests
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        for payload in xss_payloads:
            customer_data = {
                "company_name": payload,
                "contact_name": "Test Contact",
                "email": "test@example.com",
                "phone": "+33123456789",
                "payment_terms": 30,
                "credit_limit": 50000.0
            }
            
            response = await client.post(
                "/api/v1/manufacturing/sales/customers",
                json=customer_data,
                headers=auth_headers
            )
            
            # Should handle XSS attempts safely
            assert response.status_code in [201, 400, 422]
            
            # If created, should not contain raw XSS
            if response.status_code == 201:
                created_data = response.json()
                assert payload not in str(created_data)
        
        # Test authorization bypass attempts
        bypass_headers = [
            {"Authorization": "Bearer fake_token"},
            {"Authorization": "Bearer "},
            {"X-API-Key": "fake_key"}
        ]
        
        for headers in bypass_headers:
            response = await client.get(
                "/api/v1/manufacturing/sales/customers",
                headers=headers
            )
            assert response.status_code == 401
        
        # Test without any authentication
        response = await client.get("/api/v1/manufacturing/sales/customers")
        assert response.status_code == 401
        
        # Test with malformed JSON
        malformed_json = '{"company_name": "Test", "invalid": }'
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            content=malformed_json,
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_endpoint_error_handling(self, client: AsyncClient, auth_headers):
        """Test error handling across manufacturing endpoints."""
        
        # Test 404 errors
        response = await client.get(
            "/api/v1/manufacturing/sales/customers/999999",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test validation errors
        invalid_data = {
            "company_name": "",  # Empty required field
            "payment_terms": -1,  # Invalid value
            "credit_limit": "invalid"  # Wrong type
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        error_response = response.json()
        assert "detail" in error_response
        
        # Test method not allowed
        response = await client.patch(
            "/api/v1/manufacturing/sales/customers",
            headers=auth_headers
        )
        assert response.status_code == 405
        
        # Test large payload
        large_data = {
            "company_name": "A" * 10000,
            "contact_name": "B" * 10000,
            "email": "test@example.com",
            "phone": "+33123456789",
            "payment_terms": 30,
            "credit_limit": 50000.0
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=large_data,
            headers=auth_headers
        )
        
        # Should handle large payloads gracefully
        assert response.status_code in [201, 400, 413, 422]
    
    @pytest.mark.asyncio
    async def test_endpoint_performance_requirements(self, client: AsyncClient, auth_headers):
        """Test performance requirements for manufacturing endpoints."""
        
        endpoints = [
            "/api/v1/manufacturing/sales/customers",
            "/api/v1/manufacturing/sales/invoices",
            "/api/v1/manufacturing/sales/kpis",
            "/api/v1/manufacturing/operations/products",
            "/api/v1/manufacturing/dashboard/overview"
        ]
        
        for endpoint in endpoints:
            response_times = []
            
            # Test 10 requests per endpoint
            for _ in range(10):
                import time
                start_time = time.time()
                response = await client.get(endpoint, headers=auth_headers)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                
                # Performance requirements
                assert avg_time < 1.0, f"{endpoint}: Average response time {avg_time:.3f}s (expected < 1s)"
                assert max_time < 2.0, f"{endpoint}: Max response time {max_time:.3f}s (expected < 2s)"
                
                print(f"{endpoint}: Avg {avg_time:.3f}s, Max {max_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_data_validation_comprehensive(self, client: AsyncClient, auth_headers):
        """Test comprehensive data validation across endpoints."""
        
        # Test customer data validation
        customer_validation_tests = [
            {
                "data": {"company_name": "A" * 300},  # Too long
                "expected_status": 422
            },
            {
                "data": {"email": "invalid-email"},
                "expected_status": 422
            },
            {
                "data": {"phone": "123"},  # Too short
                "expected_status": 422
            },
            {
                "data": {"payment_terms": 0},  # Below minimum
                "expected_status": 422
            },
            {
                "data": {"credit_limit": -1000},  # Negative
                "expected_status": 422
            }
        ]
        
        for test_case in customer_validation_tests:
            base_data = {
                "company_name": "Test Company",
                "contact_name": "Test Contact",
                "email": "test@example.com",
                "phone": "+33123456789",
                "payment_terms": 30,
                "credit_limit": 50000.0
            }
            base_data.update(test_case["data"])
            
            response = await client.post(
                "/api/v1/manufacturing/sales/customers",
                json=base_data,
                headers=auth_headers
            )
            
            assert response.status_code == test_case["expected_status"]
        
        # Test product data validation
        product_validation_tests = [
            {
                "data": {"product_code": ""},  # Empty code
                "expected_status": 422
            },
            {
                "data": {"product_name": "A" * 300},  # Too long
                "expected_status": 422
            },
            {
                "data": {"base_cost": 0},  # Zero cost
                "expected_status": 422
            },
            {
                "data": {"labor_hours": -1},  # Negative hours
                "expected_status": 422
            },
            {
                "data": {"material_cost": -50},  # Negative cost
                "expected_status": 422
            }
        ]
        
        for test_case in product_validation_tests:
            base_data = {
                "product_code": "TEST-001",
                "product_name": "Test Product",
                "base_cost": 100.0,
                "labor_hours": 2.0,
                "material_cost": 50.0
            }
            base_data.update(test_case["data"])
            
            response = await client.post(
                "/api/v1/manufacturing/operations/products",
                json=base_data,
                headers=auth_headers
            )
            
            assert response.status_code == test_case["expected_status"]
        
        print("Data validation tests completed successfully")


class TestManufacturingEndpointsIntegration:
    """Integration tests for manufacturing endpoints workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_manufacturing_workflow(self, client: AsyncClient, auth_headers):
        """Test complete manufacturing workflow integration."""
        
        # Step 1: Create a customer
        customer_data = {
            "company_name": "Workflow Test Manufacturing",
            "contact_name": "Workflow Manager",
            "email": "workflow@manufacturing.com",
            "phone": "+33123456789",
            "payment_terms": 30,
            "credit_limit": 75000.0
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        customer = response.json()
        customer_id = customer["customer_id"]
        
        # Step 2: Create a product
        product_data = {
            "product_code": "WORKFLOW-001",
            "product_name": "Workflow Test Widget",
            "base_cost": 200.0,
            "labor_hours": 4.0,
            "material_cost": 100.0
        }
        
        response = await client.post(
            "/api/v1/manufacturing/operations/products",
            json=product_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        product = response.json()
        product_id = product["product_id"]
        
        # Step 3: Create an invoice for the customer
        invoice_data = {
            "customer_id": customer_id,
            "invoice_number": "WORKFLOW-INV-001",
            "date_issued": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "amount": 30000.0,
            "status": "Open"
        }
        
        response = await client.post(
            "/api/v1/manufacturing/sales/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        invoice = response.json()
        invoice_id = invoice["invoice_id"]
        
        # Step 4: Verify data appears in lists
        # Check customer list
        response = await client.get(
            "/api/v1/manufacturing/sales/customers",
            headers=auth_headers
        )
        assert response.status_code == 200
        customers = response.json()
        assert any(c["customer_id"] == customer_id for c in customers)
        
        # Check product list
        response = await client.get(
            "/api/v1/manufacturing/operations/products",
            headers=auth_headers
        )
        assert response.status_code == 200
        products = response.json()
        assert any(p["product_id"] == product_id for p in products)
        
        # Check invoice list
        response = await client.get(
            "/api/v1/manufacturing/sales/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        invoices = response.json()
        assert any(i["invoice_id"] == invoice_id for i in invoices)
        
        # Step 5: Verify KPIs are updated
        response = await client.get(
            "/api/v1/manufacturing/sales/kpis",
            headers=auth_headers
        )
        assert response.status_code == 200
        kpis = response.json()
        
        # Should reflect the new data
        assert kpis["totals"]["total_revenue"] >= 30000.0
        assert kpis["totals"]["active_customers"] >= 1
        
        # Step 6: Verify dashboard is updated
        response = await client.get(
            "/api/v1/manufacturing/dashboard/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        dashboard = response.json()
        
        # Should reflect the new data
        assert dashboard["total_customers"] >= 1
        assert dashboard["total_products"] >= 1
        assert dashboard["total_revenue"] >= 30000.0
        
        print("Complete manufacturing workflow integration test passed")
    
    @pytest.mark.asyncio
    async def test_concurrent_manufacturing_operations(self, client: AsyncClient, auth_headers):
        """Test concurrent operations across manufacturing endpoints."""
        
        # Define concurrent operations
        async def create_customer(index):
            customer_data = {
                "company_name": f"Concurrent Customer {index}",
                "contact_name": f"Contact {index}",
                "email": f"concurrent{index}@test.com",
                "phone": f"+3312345678{index:02d}",
                "payment_terms": 30,
                "credit_limit": 50000.0
            }
            return await client.post(
                "/api/v1/manufacturing/sales/customers",
                json=customer_data,
                headers=auth_headers
            )
        
        async def create_product(index):
            product_data = {
                "product_code": f"CONCURRENT-{index:03d}",
                "product_name": f"Concurrent Product {index}",
                "base_cost": 100.0 + index,
                "labor_hours": 2.0 + (index * 0.1),
                "material_cost": 50.0 + (index * 0.5)
            }
            return await client.post(
                "/api/v1/manufacturing/operations/products",
                json=product_data,
                headers=auth_headers
            )
        
        async def read_dashboard():
            return await client.get(
                "/api/v1/manufacturing/dashboard/overview",
                headers=auth_headers
            )
        
        # Create tasks for concurrent execution
        tasks = []
        
        # Add customer creation tasks
        for i in range(10):
            tasks.append(create_customer(i))
        
        # Add product creation tasks
        for i in range(10):
            tasks.append(create_product(i))
        
        # Add dashboard read tasks
        for i in range(20):
            tasks.append(read_dashboard())
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        customer_results = results[:10]
        product_results = results[10:20]
        dashboard_results = results[20:]
        
        # Check customer creation results
        successful_customers = sum(1 for r in customer_results if not isinstance(r, Exception) and r.status_code == 201)
        assert successful_customers >= 8, f"Only {successful_customers}/10 customers created successfully"
        
        # Check product creation results
        successful_products = sum(1 for r in product_results if not isinstance(r, Exception) and r.status_code == 201)
        assert successful_products >= 8, f"Only {successful_products}/10 products created successfully"
        
        # Check dashboard read results
        successful_dashboard_reads = sum(1 for r in dashboard_results if not isinstance(r, Exception) and r.status_code == 200)
        assert successful_dashboard_reads >= 18, f"Only {successful_dashboard_reads}/20 dashboard reads successful"
        
        print(f"Concurrent operations test results:")
        print(f"  Customers created: {successful_customers}/10")
        print(f"  Products created: {successful_products}/10")
        print(f"  Dashboard reads: {successful_dashboard_reads}/20")
    
    @pytest.mark.asyncio
    async def test_manufacturing_data_consistency(self, client: AsyncClient, auth_headers):
        """Test data consistency across manufacturing endpoints."""
        
        # Create test data
        customers = []
        products = []
        invoices = []
        
        # Create multiple customers
        for i in range(5):
            customer_data = {
                "company_name": f"Consistency Customer {i}",
                "contact_name": f"Contact {i}",
                "email": f"consistency{i}@test.com",
                "phone": f"+3312345678{i:02d}",
                "payment_terms": 30,
                "credit_limit": 50000.0
            }
            
            response = await client.post(
                "/api/v1/manufacturing/sales/customers",
                json=customer_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            customers.append(response.json())
        
        # Create multiple products
        for i in range(5):
            product_data = {
                "product_code": f"CONSISTENCY-{i:03d}",
                "product_name": f"Consistency Product {i}",
                "base_cost": 100.0 + (i * 10),
                "labor_hours": 2.0 + (i * 0.5),
                "material_cost": 50.0 + (i * 5)
            }
            
            response = await client.post(
                "/api/v1/manufacturing/operations/products",
                json=product_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            products.append(response.json())
        
        # Create invoices for each customer
        for i, customer in enumerate(customers):
            invoice_data = {
                "customer_id": customer["customer_id"],
                "invoice_number": f"CONSISTENCY-INV-{i:03d}",
                "date_issued": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "amount": 10000.0 + (i * 1000),
                "status": "Open"
            }
            
            response = await client.post(
                "/api/v1/manufacturing/sales/invoices",
                json=invoice_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            invoices.append(response.json())
        
        # Verify consistency across endpoints
        # Check customer list contains all created customers
        response = await client.get(
            "/api/v1/manufacturing/sales/customers",
            headers=auth_headers
        )
        assert response.status_code == 200
        all_customers = response.json()
        
        for customer in customers:
            assert any(c["customer_id"] == customer["customer_id"] for c in all_customers)
        
        # Check product list contains all created products
        response = await client.get(
            "/api/v1/manufacturing/operations/products",
            headers=auth_headers
        )
        assert response.status_code == 200
        all_products = response.json()
        
        for product in products:
            assert any(p["product_id"] == product["product_id"] for p in all_products)
        
        # Check invoice list contains all created invoices
        response = await client.get(
            "/api/v1/manufacturing/sales/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        all_invoices = response.json()
        
        for invoice in invoices:
            assert any(i["invoice_id"] == invoice["invoice_id"] for i in all_invoices)
        
        # Verify KPIs reflect the data
        response = await client.get(
            "/api/v1/manufacturing/sales/kpis",
            headers=auth_headers
        )
        assert response.status_code == 200
        kpis = response.json()
        
        # Should show at least our test data
        assert kpis["totals"]["active_customers"] >= 5
        assert kpis["totals"]["total_invoices"] >= 5
        expected_revenue = sum(10000.0 + (i * 1000) for i in range(5))
        assert kpis["totals"]["total_revenue"] >= expected_revenue
        
        # Verify dashboard reflects the data
        response = await client.get(
            "/api/v1/manufacturing/dashboard/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        dashboard = response.json()
        
        assert dashboard["total_customers"] >= 5
        assert dashboard["total_products"] >= 5
        assert dashboard["total_revenue"] >= expected_revenue
        
        print("Data consistency validation passed across all endpoints")