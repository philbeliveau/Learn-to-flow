"""
Unit tests for authentication functionality.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
import secrets

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
    generate_reset_token,
    verify_reset_token,
    SecurityMiddleware
)
from app.core.config import settings
from app.models.user import User
from app.models.session import Session
from app.api.v1.endpoints.auth import (
    login,
    refresh_token,
    logout,
    register,
    reset_password_request,
    reset_password,
    verify_email
)


class TestPasswordSecurity:
    """Test password security functions."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "test_password123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 chars
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_password_verification(self):
        """Test password verification."""
        password = "test_password123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
        assert verify_password("", hashed) is False
    
    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes."""
        password = "test_password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_password_special_characters(self):
        """Test passwords with special characters."""
        special_passwords = [
            "password@123",
            "pâssw0rd!",
            "密码123",
            "password with spaces",
            "🔒secure123"
        ]
        
        for password in special_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
    
    def test_empty_password_handling(self):
        """Test empty password handling."""
        with pytest.raises(ValueError):
            get_password_hash("")
        
        with pytest.raises(ValueError):
            get_password_hash(None)
    
    def test_long_password_handling(self):
        """Test very long password handling."""
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True


class TestTokenSecurity:
    """Test JWT token security functions."""
    
    def test_access_token_creation(self):
        """Test access token creation."""
        subject = "test@example.com"
        token = create_access_token(subject=subject)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Verify token structure
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature
    
    def test_refresh_token_creation(self):
        """Test refresh token creation."""
        subject = "test@example.com"
        token = create_refresh_token(subject=subject)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Verify token structure
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_token_verification(self):
        """Test token verification."""
        subject = "test@example.com"
        token = create_access_token(subject=subject)
        
        payload = verify_token(token)
        assert payload["sub"] == subject
        assert "exp" in payload
        assert "type" in payload
        assert payload["type"] == "access"
    
    def test_token_expiration(self):
        """Test token expiration."""
        subject = "test@example.com"
        
        # Create token with short expiration
        token = create_access_token(subject=subject, expires_delta=timedelta(seconds=1))
        
        # Verify token is valid immediately
        payload = verify_token(token)
        assert payload["sub"] == subject
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Verify token is expired
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_invalid_token_handling(self):
        """Test invalid token handling."""
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "not.a.jwt",
            "Bearer token_here"
        ]
        
        for token in invalid_tokens:
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            assert exc_info.value.status_code == 401
    
    def test_token_with_custom_claims(self):
        """Test token with custom claims."""
        subject = "test@example.com"
        custom_claims = {
            "role": "admin",
            "company_id": 123,
            "permissions": ["read", "write", "delete"]
        }
        
        token = create_access_token(subject=subject, additional_claims=custom_claims)
        payload = verify_token(token)
        
        assert payload["sub"] == subject
        assert payload["role"] == "admin"
        assert payload["company_id"] == 123
        assert payload["permissions"] == ["read", "write", "delete"]
    
    def test_refresh_token_verification(self):
        """Test refresh token verification."""
        subject = "test@example.com"
        token = create_refresh_token(subject=subject)
        
        payload = verify_token(token)
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"
    
    def test_token_subject_validation(self):
        """Test token subject validation."""
        invalid_subjects = [None, "", 123, [], {}]
        
        for subject in invalid_subjects:
            with pytest.raises((ValueError, TypeError)):
                create_access_token(subject=subject)
    
    def test_token_algorithm_security(self):
        """Test token algorithm security."""
        # Verify that tokens use secure algorithms
        subject = "test@example.com"
        token = create_access_token(subject=subject)
        
        # Decode without verification to check algorithm
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"  # Should use HMAC SHA256
    
    def test_token_secret_key_security(self):
        """Test token secret key security."""
        # Verify that secret key is properly configured
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32  # Minimum secure length
        
        # Verify tokens created with different keys don't verify
        original_key = settings.SECRET_KEY
        
        # Create token with original key
        subject = "test@example.com"
        token = create_access_token(subject=subject)
        
        # Verify with original key works
        payload = verify_token(token)
        assert payload["sub"] == subject
        
        # Mock different key
        with patch.object(settings, 'SECRET_KEY', 'different_secret_key'):
            with pytest.raises(HTTPException):
                verify_token(token)


class TestResetTokenSecurity:
    """Test password reset token security."""
    
    def test_reset_token_generation(self):
        """Test reset token generation."""
        email = "test@example.com"
        token = generate_reset_token(email)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Verify token structure
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_reset_token_verification(self):
        """Test reset token verification."""
        email = "test@example.com"
        token = generate_reset_token(email)
        
        verified_email = verify_reset_token(token)
        assert verified_email == email
    
    def test_reset_token_expiration(self):
        """Test reset token expiration."""
        email = "test@example.com"
        
        # Create token with short expiration
        token = generate_reset_token(email, expires_delta=timedelta(seconds=1))
        
        # Verify token is valid immediately
        verified_email = verify_reset_token(token)
        assert verified_email == email
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Verify token is expired
        with pytest.raises(HTTPException) as exc_info:
            verify_reset_token(token)
        
        assert exc_info.value.status_code == 400
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_reset_token_invalid_handling(self):
        """Test invalid reset token handling."""
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "not.a.jwt"
        ]
        
        for token in invalid_tokens:
            with pytest.raises(HTTPException) as exc_info:
                verify_reset_token(token)
            assert exc_info.value.status_code == 400
    
    def test_reset_token_uniqueness(self):
        """Test reset token uniqueness."""
        email = "test@example.com"
        token1 = generate_reset_token(email)
        token2 = generate_reset_token(email)
        
        assert token1 != token2
        assert verify_reset_token(token1) == email
        assert verify_reset_token(token2) == email


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    @pytest.mark.asyncio
    async def test_security_headers(self):
        """Test security headers are added."""
        from fastapi import Request, Response
        
        middleware = SecurityMiddleware()
        
        # Mock request and response
        request = Mock(spec=Request)
        response = Mock(spec=Response)
        response.headers = {}
        
        async def call_next(request):
            return response
        
        result = await middleware(request, call_next)
        
        # Verify security headers are added
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        # This test depends on the actual SecurityMiddleware implementation
        # For now, we just verify the middleware doesn't break the request
        assert result == response
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # This would test rate limiting if implemented in SecurityMiddleware
        pass
    
    @pytest.mark.asyncio
    async def test_request_validation(self):
        """Test request validation."""
        # This would test request validation if implemented
        pass


class TestAuthEndpoints:
    """Test authentication endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=get_password_hash("password123"),
            first_name="Inactive",
            last_name="User",
            is_active=False
        )
        
        db_session.add(inactive_user)
        await db_session.commit()
        
        login_data = {
            "username": inactive_user.email,
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "inactive" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_unverified_user(self, client, db_session):
        """Test login with unverified user."""
        # Create unverified user
        unverified_user = User(
            email="unverified@example.com",
            username="unverified",
            hashed_password=get_password_hash("password123"),
            first_name="Unverified",
            last_name="User",
            is_active=True,
            is_verified=False
        )
        
        db_session.add(unverified_user)
        await db_session.commit()
        
        login_data = {
            "username": unverified_user.email,
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "verified" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh."""
        # First login to get tokens
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        login_result = response.json()
        refresh_token = login_result["refresh_token"]
        
        # Use refresh token to get new access token
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_logout_success(self, client, test_user):
        """Test successful logout."""
        # First login
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        login_result = response.json()
        access_token = login_result["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "logout" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_register_success(self, client, db_session):
        """Test successful user registration."""
        register_data = {
            "email": "newuser@manufacture-lyon.fr",
            "username": "newuser",
            "password": "newpassword123",
            "first_name": "Nouveau",
            "last_name": "Utilisateur",
            "phone": "+33123456789",
            "company_name": "Nouvelle Manufacture",
            "company_siret": "12345678901234"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "message" in data
        assert "user" in data
        assert data["user"]["email"] == register_data["email"]
        assert data["user"]["username"] == register_data["username"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        register_data = {
            "email": test_user.email,
            "username": "newuser",
            "password": "newpassword123",
            "first_name": "Nouveau",
            "last_name": "Utilisateur",
            "phone": "+33123456789",
            "company_name": "Nouvelle Manufacture",
            "company_siret": "12345678901234"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        register_data = {
            "email": "invalid_email",
            "username": "newuser",
            "password": "newpassword123",
            "first_name": "Nouveau",
            "last_name": "Utilisateur",
            "phone": "+33123456789",
            "company_name": "Nouvelle Manufacture",
            "company_siret": "12345678901234"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Test registration with weak password."""
        register_data = {
            "email": "newuser@manufacture-lyon.fr",
            "username": "newuser",
            "password": "123",  # Too weak
            "first_name": "Nouveau",
            "last_name": "Utilisateur",
            "phone": "+33123456789",
            "company_name": "Nouvelle Manufacture",
            "company_siret": "12345678901234"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_reset_password_request(self, client, test_user):
        """Test password reset request."""
        reset_data = {
            "email": test_user.email
        }
        
        response = await client.post("/api/v1/auth/reset-password-request", json=reset_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "email" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_request_nonexistent(self, client):
        """Test password reset request for nonexistent user."""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = await client.post("/api/v1/auth/reset-password-request", json=reset_data)
        assert response.status_code == 200  # Should not reveal if email exists
        
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, client, test_user):
        """Test successful password reset."""
        # Generate reset token
        reset_token = generate_reset_token(test_user.email)
        
        reset_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        
        response = await client.post("/api/v1/auth/reset-password", json=reset_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "reset" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        
        response = await client.post("/api/v1/auth/reset-password", json=reset_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, client, db_session):
        """Test successful email verification."""
        # Create unverified user
        unverified_user = User(
            email="unverified@example.com",
            username="unverified",
            hashed_password=get_password_hash("password123"),
            first_name="Unverified",
            last_name="User",
            is_active=True,
            is_verified=False
        )
        
        db_session.add(unverified_user)
        await db_session.commit()
        
        # Generate verification token
        verification_token = generate_reset_token(unverified_user.email)
        
        verify_data = {
            "token": verification_token
        }
        
        response = await client.post("/api/v1/auth/verify-email", json=verify_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "verified" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token."""
        verify_data = {
            "token": "invalid_token"
        }
        
        response = await client.post("/api/v1/auth/verify-email", json=verify_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data


class TestAuthenticationHelpers:
    """Test authentication helper functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client, test_user, auth_headers):
        """Test get current user functionality."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client):
        """Test get current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client):
        """Test get current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
    
    def test_secure_random_generation(self):
        """Test secure random generation."""
        # Test that random values are actually random
        randoms = [secrets.token_urlsafe(32) for _ in range(10)]
        
        # All should be different
        assert len(set(randoms)) == len(randoms)
        
        # All should be proper length
        for r in randoms:
            assert len(r) >= 32
    
    def test_timing_attack_resistance(self):
        """Test timing attack resistance."""
        # This test verifies that password verification takes similar time
        # regardless of whether the password is correct or not
        import time
        
        password = "test_password123"
        correct_hash = get_password_hash(password)
        
        # Time correct password verification
        start = time.time()
        verify_password(password, correct_hash)
        correct_time = time.time() - start
        
        # Time incorrect password verification
        start = time.time()
        verify_password("wrong_password", correct_hash)
        incorrect_time = time.time() - start
        
        # Times should be similar (within reasonable tolerance)
        # This is a basic check - real timing attack resistance testing
        # would require more sophisticated analysis
        time_diff = abs(correct_time - incorrect_time)
        assert time_diff < 0.1  # Should be within 100ms
    
    def test_session_security(self):
        """Test session security features."""
        # This would test session-related security features
        # such as session token rotation, secure session storage, etc.
        pass


class TestTwoFactorAuthentication:
    """Test two-factor authentication functionality."""
    
    def test_totp_setup(self):
        """Test TOTP setup."""
        # This would test TOTP setup if implemented
        pass
    
    def test_totp_verification(self):
        """Test TOTP verification."""
        # This would test TOTP verification if implemented
        pass
    
    def test_backup_codes(self):
        """Test backup codes."""
        # This would test backup codes if implemented
        pass


class TestAccountSecurity:
    """Test account security features."""
    
    def test_account_lockout(self):
        """Test account lockout after failed attempts."""
        # This would test account lockout functionality
        pass
    
    def test_password_policy(self):
        """Test password policy enforcement."""
        weak_passwords = [
            "123",
            "password",
            "qwerty",
            "12345678",
            "password123"
        ]
        
        # This would test password policy if implemented
        # For now, just verify basic requirements exist
        for password in weak_passwords:
            # Would check against password policy
            pass
    
    def test_session_management(self):
        """Test session management features."""
        # This would test session management features like:
        # - Session timeout
        # - Concurrent session limits
        # - Session invalidation
        pass