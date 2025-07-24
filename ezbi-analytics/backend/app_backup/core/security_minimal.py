from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import structlog

# Simple in-memory store for development/minimal setup
_blacklisted_tokens = set()
_active_sessions = {}

# Configure logger
logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security token
security = HTTPBearer()

# Basic settings (fallback)
SECRET_KEY = "a91367f865689d7bad5d1ece7d23aa7cd3080dd02029a71f28b529a8cc7392d7"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class SecurityUtils:
    """Security utility functions."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """Generate a random token."""
        return secrets.token_urlsafe(length)

class JWTManager:
    """JWT token management."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError as e:
            logger.error("JWT decode error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if token is blacklisted."""
        return token in _blacklisted_tokens
    
    @staticmethod
    def revoke_token(token: str) -> None:
        """Revoke a token by adding it to blacklist."""
        _blacklisted_tokens.add(token)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request processing."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server header
        response.headers.pop("server", None)
        
        return response

# Simplified authentication for Railway deployment
async def get_current_user_simple(credentials: HTTPAuthorizationCredentials = security):
    """Get current authenticated user (simplified version)."""
    token = credentials.credentials
    
    # Check if token is blacklisted
    if JWTManager.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = JWTManager.decode_token(token)
    
    # Validate token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user info from token
    return {
        "id": payload.get("sub"),
        "email": payload.get("email", "user@example.com"),
        "is_active": True
    }