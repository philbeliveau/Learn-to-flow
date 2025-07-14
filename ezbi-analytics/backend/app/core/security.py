from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets
import hashlib
import hmac
import pyotp
import qrcode
import io
import base64
import structlog
from redis import Redis
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import get_db_session
from app.models.user import User
from app.models.session import UserSession

# Configure logger
logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security token
security = HTTPBearer()

# Redis client for session management
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Encryption setup
if settings.FERNET_KEY:
    fernet = Fernet(settings.FERNET_KEY.encode())
else:
    fernet = Fernet(Fernet.generate_key())

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
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt sensitive data."""
        return fernet.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return fernet.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, expected_token: str) -> bool:
        """Validate CSRF token."""
        return hmac.compare_digest(token, expected_token)
    
    @staticmethod
    def sanitize_input(input_data: str) -> str:
        """Sanitize user input to prevent XSS."""
        import html
        return html.escape(input_data, quote=True)
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_password_strength(password: str) -> dict:
        """Analyze password strength."""
        import re
        
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        if len(password) >= 12:
            score += 1
        
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Include lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Include uppercase letters")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Include numbers")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Include special characters")
        
        # Common patterns check
        common_patterns = ["123456", "password", "qwerty", "admin"]
        if any(pattern in password.lower() for pattern in common_patterns):
            score = max(0, score - 2)
            feedback.append("Avoid common patterns")
        
        strength_levels = {
            0: "Very Weak",
            1: "Weak",
            2: "Fair",
            3: "Good",
            4: "Strong",
            5: "Very Strong",
            6: "Excellent"
        }
        
        return {
            "score": score,
            "max_score": 6,
            "strength": strength_levels.get(score, "Unknown"),
            "feedback": feedback
        }

class JWTManager:
    """JWT token management."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def create_reset_token(data: dict) -> str:
        """Create password reset token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "reset"
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError as e:
            logger.error("JWT decode error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def extract_token_from_header(authorization: str) -> str:
        """Extract token from Authorization header."""
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return authorization[7:]  # Remove "Bearer " prefix
    
    @staticmethod
    async def revoke_token(token: str) -> None:
        """Revoke a token by adding it to blacklist."""
        try:
            payload = JWTManager.decode_token(token)
            exp = payload.get("exp")
            if exp:
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    redis_client.setex(f"blacklist:{token}", int(ttl), "1")
        except Exception as e:
            logger.error("Error revoking token", error=str(e))
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if token is blacklisted."""
        return redis_client.exists(f"blacklist:{token}") > 0

class MFAManager:
    """Multi-Factor Authentication manager."""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup."""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="EZBI Analytics"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token."""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """Generate backup codes."""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """Hash backup code for storage."""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def verify_backup_code(code: str, hashed_code: str) -> bool:
        """Verify backup code."""
        return hashlib.sha256(code.encode()).hexdigest() == hashed_code

class SessionManager:
    """User session management."""
    
    @staticmethod
    async def create_session(user_id: int, ip_address: str, user_agent: str) -> str:
        """Create new user session."""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        
        # Store in Redis
        redis_client.setex(
            f"session:{session_id}",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            str(session_data)
        )
        
        # Store in database
        async with get_db_session() as db:
            db_session = UserSession(
                session_id=session_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            db.add(db_session)
            await db.commit()
        
        return session_id
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        """Get session data."""
        session_data = redis_client.get(f"session:{session_id}")
        if session_data:
            import ast
            return ast.literal_eval(session_data)
        return None
    
    @staticmethod
    async def update_session_activity(session_id: str) -> None:
        """Update session last activity."""
        session_data = await SessionManager.get_session(session_id)
        if session_data:
            session_data["last_activity"] = datetime.utcnow().isoformat()
            redis_client.setex(
                f"session:{session_id}",
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                str(session_data)
            )
    
    @staticmethod
    async def revoke_session(session_id: str) -> None:
        """Revoke user session."""
        redis_client.delete(f"session:{session_id}")
        
        # Update database
        async with get_db_session() as db:
            session = await db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            if session:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                await db.commit()
    
    @staticmethod
    async def revoke_all_user_sessions(user_id: int) -> None:
        """Revoke all sessions for a user."""
        # Get all session keys from Redis
        session_keys = redis_client.keys(f"session:*")
        for key in session_keys:
            session_data = redis_client.get(key)
            if session_data:
                import ast
                data = ast.literal_eval(session_data)
                if data.get("user_id") == user_id:
                    redis_client.delete(key)
        
        # Update database
        async with get_db_session() as db:
            sessions = await db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).all()
            for session in sessions:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
            await db.commit()

class RateLimiter:
    """Rate limiting implementation."""
    
    @staticmethod
    def check_rate_limit(key: str, limit: int = None, window: int = None) -> bool:
        """Check if request is within rate limit."""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW
        
        current_time = datetime.utcnow().timestamp()
        
        # Use sliding window with Redis
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, current_time - window)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, window)
        
        results = pipe.execute()
        request_count = results[1]
        
        return request_count < limit
    
    @staticmethod
    def get_rate_limit_info(key: str) -> dict:
        """Get rate limit information."""
        window = settings.RATE_LIMIT_WINDOW
        current_time = datetime.utcnow().timestamp()
        
        redis_client.zremrangebyscore(key, 0, current_time - window)
        count = redis_client.zcard(key)
        
        return {
            "requests": count,
            "limit": settings.RATE_LIMIT_REQUESTS,
            "window": window,
            "remaining": max(0, settings.RATE_LIMIT_REQUESTS - count)
        }

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
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # Remove server header
        response.headers.pop("server", None)
        
        return response

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> User:
    """Get current authenticated user."""
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
    
    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    async with get_db_session() as db:
        user = await db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user

# Optional authentication dependency
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = security) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# Permission decorators
def require_permissions(*permissions):
    """Decorator to require specific permissions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                user = kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permissions
            user_permissions = [perm.name for perm in user.permissions]
            if not all(perm in user_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_roles(*roles):
    """Decorator to require specific roles."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                user = kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check roles
            user_roles = [role.name for role in user.roles]
            if not any(role in user_roles for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient role privileges"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
