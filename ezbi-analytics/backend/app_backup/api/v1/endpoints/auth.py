from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import structlog

from app.core.database import get_async_session
from app.core.security import (
    JWTManager,
    MFAManager,
    SessionManager,
    get_current_user,
    SecurityUtils,
)
from app.core.config import settings
from app.models.user import User
from app.models.session import UserSession, LoginAttempt
from app.models.audit_log import AuditLog

logger = structlog.get_logger()
security = HTTPBearer()

router = APIRouter()

# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    mfa_token: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    requires_mfa: bool = False
    mfa_setup_required: bool = False

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    accept_terms: bool = True
    accept_privacy: bool = True
    marketing_consent: bool = False

class RegisterResponse(BaseModel):
    message: str
    user_id: int
    email_verification_required: bool = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list

class MFAVerifyRequest(BaseModel):
    token: str
    backup_code: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Authenticate user and return JWT tokens."""
    
    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Create login attempt record
    login_attempt = LoginAttempt(
        email=login_data.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=False,
    )
    
    try:
        # Find user by email
        result = await db.execute(select(User).where(User.email == login_data.email))
        user = result.scalar_one_or_none()
        
        if not user:
            login_attempt.failure_reason = "user_not_found"
            db.add(login_attempt)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is locked
        if user.is_locked:
            login_attempt.failure_reason = "account_locked"
            db.add(login_attempt)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked. Please try again later.",
            )
        
        # Verify password
        if not user.verify_password(login_data.password):
            user.increment_failed_login_attempts()
            login_attempt.failure_reason = "invalid_password"
            db.add(login_attempt)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is active
        if not user.is_active:
            login_attempt.failure_reason = "account_inactive"
            db.add(login_attempt)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not login_data.mfa_token:
                # Return partial response indicating MFA required
                return LoginResponse(
                    access_token="",
                    refresh_token="",
                    expires_in=0,
                    user={},
                    requires_mfa=True,
                )
            
            # Verify MFA token
            if not user.verify_mfa_token(login_data.mfa_token):
                # Try backup code
                if not user.verify_backup_code(login_data.mfa_token):
                    login_attempt.failure_reason = "invalid_mfa"
                    db.add(login_attempt)
                    await db.commit()
                    
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid MFA token",
                    )
        
        # Reset failed login attempts on successful login
        user.reset_failed_login_attempts()
        user.last_login = datetime.utcnow()
        user.update_last_activity()
        
        # Create session
        session_id = await SessionManager.create_session(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Generate JWT tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if login_data.remember_me:
            access_token_expires = timedelta(days=30)
        
        access_token = JWTManager.create_access_token(
            data={"sub": str(user.id), "session_id": session_id},
            expires_delta=access_token_expires,
        )
        
        refresh_token = JWTManager.create_refresh_token(
            data={"sub": str(user.id), "session_id": session_id}
        )
        
        # Mark login attempt as successful
        login_attempt.success = True
        db.add(login_attempt)
        
        # Create audit log
        audit_log = AuditLog.create_log(
            action="login",
            resource_type="user",
            resource_id=str(user.id),
            description=f"User {user.email} logged in",
            user_id=user.id,
            company_id=user.company_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit_log)
        
        await db.commit()
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=int(access_token_expires.total_seconds()),
            httponly=True,
            secure=True,
            samesite="lax",
        )
        
        logger.info("User logged in successfully", user_id=user.id, email=user.email)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=user.to_dict(),
            mfa_setup_required=not user.mfa_enabled and user.company and user.company.subscription_tier == "enterprise",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error", error=str(e))
        login_attempt.failure_reason = "system_error"
        db.add(login_attempt)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )

@router.post("/register", response_model=RegisterResponse)
async def register(
    request: Request,
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Register a new user account."""
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == register_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Validate password strength
    password_strength = SecurityUtils.get_password_strength(register_data.password)
    if password_strength["score"] < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too weak: {', '.join(password_strength['feedback'])}",
        )
    
    # Create user
    user = User(
        email=register_data.email,
        first_name=register_data.first_name,
        last_name=register_data.last_name,
        phone=register_data.phone,
        is_active=True,
        is_verified=False,
    )
    
    user.set_password(register_data.password)
    
    # GDPR consent
    user.set_gdpr_consent(register_data.accept_privacy)
    
    # Generate email verification token
    verification_token = user.generate_email_verification_token()
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # TODO: Send verification email
    # await send_verification_email(user.email, verification_token)
    
    # Create audit log
    audit_log = AuditLog.create_log(
        action="create",
        resource_type="user",
        resource_id=str(user.id),
        description=f"New user registered: {user.email}",
        user_id=user.id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info("User registered successfully", user_id=user.id, email=user.email)
    
    return RegisterResponse(
        message="User registered successfully. Please check your email for verification.",
        user_id=user.id,
    )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Refresh access token using refresh token."""
    
    try:
        # Decode refresh token
        payload = JWTManager.decode_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # Get user
        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Generate new access token
        session_id = payload.get("session_id")
        access_token = JWTManager.create_access_token(
            data={"sub": str(user.id), "session_id": session_id}
        )
        
        # Update session activity
        if session_id:
            await SessionManager.update_session_activity(session_id)
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Logout user and revoke tokens."""
    
    # Revoke access token
    await JWTManager.revoke_token(credentials.credentials)
    
    # Get session ID from token
    payload = JWTManager.decode_token(credentials.credentials)
    session_id = payload.get("session_id")
    
    if session_id:
        await SessionManager.revoke_session(session_id)
    
    # Create audit log
    audit_log = AuditLog.create_log(
        action="logout",
        resource_type="user",
        resource_id=str(current_user.id),
        description=f"User {current_user.email} logged out",
        user_id=current_user.id,
        company_id=current_user.company_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info("User logged out", user_id=current_user.id)
    
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user.to_dict()

@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Setup MFA for user."""
    
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    
    # Generate MFA secret and QR code
    secret, qr_code = current_user.setup_mfa()
    
    # Generate backup codes
    backup_codes = current_user.generate_backup_codes()
    
    await db.commit()
    
    return MFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes,
    )

@router.post("/mfa/verify")
async def verify_mfa(
    verify_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Verify MFA setup and enable MFA."""
    
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    
    # Verify MFA token
    if not current_user.verify_mfa_token(verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token",
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    await db.commit()
    
    return {"message": "MFA enabled successfully"}

@router.post("/mfa/disable")
async def disable_mfa(
    verify_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Disable MFA for user."""
    
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled",
        )
    
    # Verify MFA token or backup code
    if not (current_user.verify_mfa_token(verify_data.token) or 
            current_user.verify_backup_code(verify_data.token)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token or backup code",
        )
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.backup_codes = None
    await db.commit()
    
    return {"message": "MFA disabled successfully"}

@router.post("/password/reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Request password reset."""
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()
    
    if user:
        # Generate reset token
        reset_token = user.generate_password_reset_token()
        await db.commit()
        
        # TODO: Send password reset email
        # await send_password_reset_email(user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return {"message": "If an account exists with this email, a password reset link has been sent."}

@router.post("/password/reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Confirm password reset with token."""
    
    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == reset_data.token)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.verify_password_reset_token(reset_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    # Validate new password
    password_strength = SecurityUtils.get_password_strength(reset_data.new_password)
    if password_strength["score"] < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too weak: {', '.join(password_strength['feedback'])}",
        )
    
    # Update password
    user.set_password(reset_data.new_password)
    user.clear_password_reset_token()
    
    # Revoke all existing sessions
    await SessionManager.revoke_all_user_sessions(user.id)
    
    await db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/password/change")
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Change user password."""
    
    # Verify current password
    if not current_user.verify_password(change_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Validate new password
    password_strength = SecurityUtils.get_password_strength(change_data.new_password)
    if password_strength["score"] < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too weak: {', '.join(password_strength['feedback'])}",
        )
    
    # Update password
    current_user.set_password(change_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get user's active sessions."""
    
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        )
    )
    sessions = result.scalars().all()
    
    return [session.to_dict() for session in sessions]

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Revoke a specific session."""
    
    # Verify session belongs to current user
    result = await db.execute(
        select(UserSession).where(
            UserSession.session_id == session_id,
            UserSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Revoke session
    await SessionManager.revoke_session(session_id)
    
    return {"message": "Session revoked successfully"}

@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Revoke all user sessions."""
    
    await SessionManager.revoke_all_user_sessions(current_user.id)
    
    return {"message": "All sessions revoked successfully"}
