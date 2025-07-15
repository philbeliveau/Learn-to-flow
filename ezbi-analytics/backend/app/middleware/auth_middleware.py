"""
Enhanced Authentication Middleware for Manufacturing API
Provides role-based access control, rate limiting, and security headers
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional, Dict, Any, List
import time
import structlog
from datetime import datetime, timedelta
import json
import re

from app.core.security import (
    JWTManager, 
    RateLimiter, 
    get_current_user,
    SecurityUtils
)
from app.core.config import settings
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.database import get_db_session

logger = structlog.get_logger()
security = HTTPBearer()

class ManufacturingAuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced authentication middleware for manufacturing API endpoints
    with role-based access control and comprehensive security features
    """
    
    # Role-based endpoint access control
    ENDPOINT_PERMISSIONS = {
        # Sales endpoints - accessible to Sales, Manager, Admin
        "/api/v1/manufacturing/sales/": ["sales_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/sales/customers": ["sales_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/sales/invoices": ["sales_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/sales/kpis": ["sales_read", "manager_access", "admin_access"],
        
        # Accounting endpoints - accessible to Accounting, Manager, Admin
        "/api/v1/manufacturing/accounting/": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/vendors": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/purchases": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/accounts-receivable": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/accounts-payable": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/kpis": ["accounting_read", "manager_access", "admin_access"],
        
        # Operations endpoints - accessible to Operations, Manager, Admin
        "/api/v1/manufacturing/operations/": ["operations_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/operations/products": ["operations_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/operations/production-orders": ["operations_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/operations/kpis": ["operations_read", "manager_access", "admin_access"],
        
        # Finance endpoints - accessible to Finance, Manager, Admin
        "/api/v1/manufacturing/finance/": ["finance_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/finance/cash-ledger": ["finance_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/finance/debt-accounts": ["finance_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/finance/kpis": ["finance_read", "manager_access", "admin_access"],
        
        # HR endpoints - accessible to HR, Manager, Admin
        "/api/v1/manufacturing/hr/": ["hr_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/hr/employees": ["hr_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/hr/payroll": ["hr_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/hr/kpis": ["hr_read", "manager_access", "admin_access"],
        
        # Expenses endpoints - accessible to Accounting, Manager, Admin
        "/api/v1/manufacturing/expenses/": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/expenses/fixed-costs": ["accounting_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/expenses/kpis": ["accounting_read", "manager_access", "admin_access"],
        
        # Dashboard endpoints - accessible to all authenticated users
        "/api/v1/manufacturing/dashboard/": ["analyst_access", "sales_read", "accounting_read", "operations_read", "finance_read", "hr_read", "manager_access", "admin_access"],
        "/api/v1/manufacturing/dashboard/overview": ["analyst_access", "sales_read", "accounting_read", "operations_read", "finance_read", "hr_read", "manager_access", "admin_access"],
        
        # Write operations - higher privileges required
        "/api/v1/manufacturing/sales/customers/create": ["sales_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/sales/invoices/create": ["sales_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/vendors/create": ["accounting_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/accounting/purchases/create": ["accounting_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/operations/products/create": ["operations_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/operations/production-orders/create": ["operations_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/hr/employees/create": ["hr_write", "manager_access", "admin_access"],
        "/api/v1/manufacturing/hr/payroll/create": ["hr_write", "manager_access", "admin_access"],
        
        # Admin-only endpoints
        "/api/v1/manufacturing/admin/": ["admin_access"],
        "/api/v1/manufacturing/system/": ["admin_access"],
    }
    
    # Rate limiting by role
    RATE_LIMITS = {
        "admin": {"requests": 1000, "window": 60},
        "manager": {"requests": 500, "window": 60},
        "analyst": {"requests": 200, "window": 60},
        "user": {"requests": 100, "window": 60},
    }
    
    # Sensitive endpoints requiring additional validation
    SENSITIVE_ENDPOINTS = [
        "/api/v1/manufacturing/finance/",
        "/api/v1/manufacturing/hr/payroll",
        "/api/v1/manufacturing/accounting/",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive authentication and authorization"""
        start_time = time.time()
        
        # Skip authentication for excluded paths
        if self._is_excluded_path(request.url.path):
            response = await call_next(request)
            return self._add_security_headers(response)
        
        # Skip non-manufacturing endpoints
        if not request.url.path.startswith("/api/v1/manufacturing/"):
            response = await call_next(request)
            return self._add_security_headers(response)
        
        try:
            # Extract and validate JWT token
            user = await self._authenticate_request(request)
            
            # Apply rate limiting
            await self._apply_rate_limiting(request, user)
            
            # Check endpoint permissions
            await self._check_endpoint_permissions(request, user)
            
            # Validate request data for sensitive endpoints
            await self._validate_sensitive_request(request, user)
            
            # Add user to request state for downstream use
            request.state.user = user
            
            # Process request
            response = await call_next(request)
            
            # Log successful access
            await self._log_access(request, user, response.status_code, time.time() - start_time)
            
            return self._add_security_headers(response)
            
        except HTTPException as e:
            # Log failed access attempt
            await self._log_failed_access(request, str(e.detail), e.status_code)
            
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail, "error_code": "AUTH_FAILED"},
                headers=self._get_security_headers()
            )
        except Exception as e:
            logger.error("Authentication middleware error", error=str(e))
            
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error", "error_code": "AUTH_ERROR"},
                headers=self._get_security_headers()
            )
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should skip authentication"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    async def _authenticate_request(self, request: Request) -> User:
        """Extract and validate JWT token from request"""
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Try to get token from cookie
            token = request.cookies.get("access_token")
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No authentication token provided",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            try:
                token = JWTManager.extract_token_from_header(auth_header)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Check if token is blacklisted
        if JWTManager.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decode and validate token
        try:
            payload = JWTManager.decode_token(token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
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
            
            if user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is locked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
    
    async def _apply_rate_limiting(self, request: Request, user: User):
        """Apply rate limiting based on user role"""
        # Determine user's highest role
        user_roles = [role.name for role in user.roles]
        
        # Apply most permissive rate limit
        rate_limit = self.RATE_LIMITS["user"]  # Default
        if "admin" in user_roles:
            rate_limit = self.RATE_LIMITS["admin"]
        elif "manager" in user_roles:
            rate_limit = self.RATE_LIMITS["manager"]
        elif "analyst" in user_roles:
            rate_limit = self.RATE_LIMITS["analyst"]
        
        # Create rate limit key
        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"rate_limit:{user.id}:{client_ip}"
        
        # Check rate limit
        if not RateLimiter.check_rate_limit(
            rate_limit_key,
            rate_limit["requests"],
            rate_limit["window"]
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_limit["requests"]),
                    "X-RateLimit-Window": str(rate_limit["window"]),
                    "Retry-After": str(rate_limit["window"]),
                }
            )
    
    async def _check_endpoint_permissions(self, request: Request, user: User):
        """Check if user has permission to access endpoint"""
        endpoint_path = request.url.path
        method = request.method
        
        # Find matching endpoint permission
        required_permissions = None
        for pattern, permissions in self.ENDPOINT_PERMISSIONS.items():
            if endpoint_path.startswith(pattern) or endpoint_path == pattern:
                required_permissions = permissions
                break
        
        # If no specific permissions defined, allow access
        if not required_permissions:
            return
        
        # Check if user has any of the required permissions
        user_permissions = user.get_all_permissions()
        user_roles = [role.name for role in user.roles]
        
        # Check direct permissions
        has_permission = any(perm in user_permissions for perm in required_permissions)
        
        # Check role-based permissions
        if not has_permission:
            # Map roles to permissions
            role_permissions = {
                "admin": ["admin_access"],
                "manager": ["manager_access"],
                "analyst": ["analyst_access"],
                "sales_user": ["sales_read", "sales_write"],
                "accounting_user": ["accounting_read", "accounting_write"],
                "operations_user": ["operations_read", "operations_write"],
                "finance_user": ["finance_read", "finance_write"],
                "hr_user": ["hr_read", "hr_write"],
            }
            
            for role in user_roles:
                if role in role_permissions:
                    role_perms = role_permissions[role]
                    if any(perm in required_permissions for perm in role_perms):
                        has_permission = True
                        break
        
        # Special handling for write operations
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            write_permissions = [
                "admin_access", "manager_access",
                "sales_write", "accounting_write", "operations_write",
                "finance_write", "hr_write"
            ]
            
            if not any(perm in user_permissions for perm in write_permissions):
                has_permission = False
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this endpoint",
            )
    
    async def _validate_sensitive_request(self, request: Request, user: User):
        """Additional validation for sensitive endpoints"""
        endpoint_path = request.url.path
        
        # Check if this is a sensitive endpoint
        is_sensitive = any(endpoint_path.startswith(pattern) for pattern in self.SENSITIVE_ENDPOINTS)
        
        if not is_sensitive:
            return
        
        # Require MFA for sensitive endpoints if enabled
        if user.company and user.company.subscription_tier == "enterprise":
            if not user.mfa_enabled:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="MFA required for sensitive operations",
                )
        
        # Additional IP validation for finance endpoints
        if "/finance/" in endpoint_path:
            client_ip = request.client.host if request.client else "unknown"
            
            # Check if IP is in allowed range (implement your IP whitelist logic)
            if not self._is_allowed_ip(client_ip):
                logger.warning(
                    "Finance access from unauthorized IP",
                    user_id=user.id,
                    ip=client_ip,
                    endpoint=endpoint_path
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied from this IP address",
                )
    
    def _is_allowed_ip(self, ip: str) -> bool:
        """Check if IP is in allowed range for sensitive operations"""
        # Implement your IP whitelist logic here
        # For now, allow all private IPs and localhost
        private_ranges = [
            "127.0.0.1",
            "localhost",
            "192.168.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
        ]
        
        return any(ip.startswith(range_) for range_ in private_ranges)
    
    async def _log_access(self, request: Request, user: User, status_code: int, duration: float):
        """Log successful access attempt"""
        try:
            async with get_db_session() as db:
                audit_log = AuditLog.create_log(
                    action="api_access",
                    resource_type="manufacturing_endpoint",
                    resource_id=request.url.path,
                    description=f"User {user.email} accessed {request.method} {request.url.path}",
                    user_id=user.id,
                    company_id=user.company_id,
                    ip_address=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent", "unknown"),
                    additional_data={
                        "status_code": status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "method": request.method,
                    }
                )
                db.add(audit_log)
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to log access", error=str(e))
    
    async def _log_failed_access(self, request: Request, error: str, status_code: int):
        """Log failed access attempt"""
        try:
            async with get_db_session() as db:
                audit_log = AuditLog.create_log(
                    action="api_access_failed",
                    resource_type="manufacturing_endpoint",
                    resource_id=request.url.path,
                    description=f"Failed access to {request.method} {request.url.path}: {error}",
                    ip_address=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent", "unknown"),
                    additional_data={
                        "status_code": status_code,
                        "error": error,
                        "method": request.method,
                    }
                )
                db.add(audit_log)
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to log failed access", error=str(e))
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers for response"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            "X-API-Version": "v1",
            "X-Service": "EZBI-Manufacturing-API",
        }
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        headers = self._get_security_headers()
        for key, value in headers.items():
            response.headers[key] = value
        
        # Remove server header for security
        response.headers.pop("server", None)
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Input validation middleware for manufacturing API
    Validates request data and sanitizes inputs
    """
    
    # Validation patterns
    VALIDATION_PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^[\+]?[\d\s\-\(\)]{10,20}$",
        "amount": r"^\d+(\.\d{1,2})?$",
        "date": r"^\d{4}-\d{2}-\d{2}$",
        "invoice_number": r"^[A-Z0-9\-]{1,50}$",
        "product_code": r"^[A-Z0-9\-]{1,20}$",
        "employee_number": r"^[A-Z0-9]{1,20}$",
    }
    
    # Maximum lengths for string fields
    MAX_LENGTHS = {
        "company_name": 255,
        "contact_name": 255,
        "product_name": 255,
        "description": 1000,
        "notes": 1000,
        "address": 500,
    }
    
    def __init__(self, app):
        super().__init__(app)
        self.validation_endpoints = [
            "/api/v1/manufacturing/",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with input validation"""
        # Skip validation for GET requests and non-manufacturing endpoints
        if request.method == "GET" or not self._should_validate(request.url.path):
            return await call_next(request)
        
        try:
            # Validate request data
            await self._validate_request_data(request)
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail, "error_code": "VALIDATION_ERROR"}
            )
        except Exception as e:
            logger.error("Input validation error", error=str(e))
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request data", "error_code": "VALIDATION_ERROR"}
            )
    
    def _should_validate(self, path: str) -> bool:
        """Check if path should be validated"""
        return any(path.startswith(endpoint) for endpoint in self.validation_endpoints)
    
    async def _validate_request_data(self, request: Request):
        """Validate request data"""
        if not hasattr(request, '_body'):
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    self._validate_data_structure(data)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON format"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Data validation error: {str(e)}"
                )
    
    def _validate_data_structure(self, data: Dict[str, Any]):
        """Validate data structure and content"""
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400,
                detail="Request data must be a JSON object"
            )
        
        # Validate each field
        for field, value in data.items():
            if isinstance(value, str):
                # Check maximum length
                if field in self.MAX_LENGTHS:
                    if len(value) > self.MAX_LENGTHS[field]:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field}' exceeds maximum length of {self.MAX_LENGTHS[field]}"
                        )
                
                # Check pattern validation
                if field in self.VALIDATION_PATTERNS:
                    pattern = self.VALIDATION_PATTERNS[field]
                    if not re.match(pattern, value):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field}' has invalid format"
                        )
                
                # Sanitize string inputs
                data[field] = SecurityUtils.sanitize_input(value)
            
            elif isinstance(value, (int, float)):
                # Validate numeric ranges
                if field.endswith("_amount") or field.endswith("_cost"):
                    if value < 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field}' cannot be negative"
                        )
                    if value > 999999999.99:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field}' exceeds maximum value"
                        )