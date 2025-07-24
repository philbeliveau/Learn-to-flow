from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import enum

from app.core.database import Base
from app.core.security import SecurityUtils

# Many-to-many association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class UserStatus(enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    LOCKED = "locked"

class User(Base):
    """User model with comprehensive authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    status = Column(String(20), default=UserStatus.ACTIVE.value)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="Europe/Paris")
    language = Column(String(10), default="fr")
    
    # Company association
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    
    # Security settings
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32), nullable=True)
    backup_codes = Column(JSON, nullable=True)  # Stored as hashed codes
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Account tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_sent_at = Column(DateTime, nullable=True)
    
    # Preferences and settings
    preferences = Column(JSON, nullable=True)
    notification_settings = Column(JSON, nullable=True)
    
    # GDPR compliance
    gdpr_consent = Column(Boolean, default=False)
    gdpr_consent_date = Column(DateTime, nullable=True)
    data_retention_date = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    permissions = relationship("Permission", secondary=user_permissions, back_populates="users")
    sessions = relationship("UserSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    file_uploads = relationship("FileUpload", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    
    # Hybrid properties
    @hybrid_property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    @hybrid_property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    @hybrid_property
    def is_password_expired(self) -> bool:
        """Check if password has expired (90 days)."""
        if self.password_changed_at:
            return datetime.utcnow() - self.password_changed_at > timedelta(days=90)
        return True
    
    @hybrid_property
    def is_email_verification_expired(self) -> bool:
        """Check if email verification token has expired (24 hours)."""
        if self.email_verification_sent_at:
            return datetime.utcnow() - self.email_verification_sent_at > timedelta(hours=24)
        return True
    
    @hybrid_property
    def is_password_reset_expired(self) -> bool:
        """Check if password reset token has expired (1 hour)."""
        if self.password_reset_sent_at:
            return datetime.utcnow() - self.password_reset_sent_at > timedelta(hours=1)
        return True
    
    # Methods
    def set_password(self, password: str) -> None:
        """Set user password with hashing."""
        self.hashed_password = SecurityUtils.hash_password(password)
        self.password_changed_at = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def verify_password(self, password: str) -> bool:
        """Verify user password."""
        return SecurityUtils.verify_password(password, self.hashed_password)
    
    def generate_email_verification_token(self) -> str:
        """Generate email verification token."""
        token = SecurityUtils.generate_random_token()
        self.email_verification_token = token
        self.email_verification_sent_at = datetime.utcnow()
        return token
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token."""
        token = SecurityUtils.generate_random_token()
        self.password_reset_token = token
        self.password_reset_sent_at = datetime.utcnow()
        return token
    
    def verify_email_verification_token(self, token: str) -> bool:
        """Verify email verification token."""
        if (self.email_verification_token == token and 
            not self.is_email_verification_expired):
            self.is_verified = True
            self.email_verification_token = None
            self.email_verification_sent_at = None
            return True
        return False
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token."""
        return (self.password_reset_token == token and 
                not self.is_password_reset_expired)
    
    def clear_password_reset_token(self) -> None:
        """Clear password reset token."""
        self.password_reset_token = None
        self.password_reset_sent_at = None
    
    def increment_failed_login_attempts(self) -> None:
        """Increment failed login attempts and lock if necessary."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
            self.status = UserStatus.LOCKED.value
    
    def reset_failed_login_attempts(self) -> None:
        """Reset failed login attempts after successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        if self.status == UserStatus.LOCKED.value:
            self.status = UserStatus.ACTIVE.value
    
    def update_last_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission."""
        # Check direct permissions
        for permission in self.permissions:
            if permission.name == permission_name:
                return True
        
        # Check role permissions
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        for role in self.roles:
            if role.name == role_name:
                return True
        return False
    
    def get_all_permissions(self) -> List[str]:
        """Get all user permissions (direct + role-based)."""
        permissions = set()
        
        # Add direct permissions
        for permission in self.permissions:
            permissions.add(permission.name)
        
        # Add role permissions
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        
        return list(permissions)
    
    def setup_mfa(self) -> tuple[str, str]:
        """Setup MFA for user."""
        from app.core.security import MFAManager
        
        secret = MFAManager.generate_secret()
        qr_code = MFAManager.generate_qr_code(self.email, secret)
        
        # Store encrypted secret
        self.mfa_secret = SecurityUtils.encrypt_data(secret)
        
        return secret, qr_code
    
    def verify_mfa_token(self, token: str) -> bool:
        """Verify MFA token."""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        
        from app.core.security import MFAManager
        
        secret = SecurityUtils.decrypt_data(self.mfa_secret)
        return MFAManager.verify_totp(secret, token)
    
    def generate_backup_codes(self) -> List[str]:
        """Generate MFA backup codes."""
        from app.core.security import MFAManager
        
        codes = MFAManager.generate_backup_codes()
        
        # Store hashed codes
        self.backup_codes = [MFAManager.hash_backup_code(code) for code in codes]
        
        return codes
    
    def verify_backup_code(self, code: str) -> bool:
        """Verify MFA backup code."""
        if not self.backup_codes:
            return False
        
        from app.core.security import MFAManager
        
        for i, hashed_code in enumerate(self.backup_codes):
            if MFAManager.verify_backup_code(code, hashed_code):
                # Remove used backup code
                self.backup_codes.pop(i)
                return True
        
        return False
    
    def set_gdpr_consent(self, consent: bool) -> None:
        """Set GDPR consent."""
        self.gdpr_consent = consent
        self.gdpr_consent_date = datetime.utcnow()
        
        if consent:
            # Set data retention date (7 years for French accounting)
            self.data_retention_date = datetime.utcnow() + timedelta(days=2555)
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get user preferences with defaults."""
        defaults = {
            "theme": "light",
            "language": "fr",
            "timezone": "Europe/Paris",
            "date_format": "DD/MM/YYYY",
            "currency": "EUR",
            "notifications": {
                "email": True,
                "push": True,
                "sms": False
            },
            "dashboard": {
                "default_view": "overview",
                "show_tips": True,
                "auto_refresh": True
            }
        }
        
        if self.preferences:
            defaults.update(self.preferences)
        
        return defaults
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences."""
        current_prefs = self.get_preferences()
        current_prefs.update(preferences)
        self.preferences = current_prefs
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary."""
        result = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "language": self.language,
            "company_id": self.company_id,
            "department": self.department,
            "job_title": self.job_title,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "status": self.status,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "preferences": self.get_preferences(),
            "roles": [role.name for role in self.roles],
            "permissions": self.get_all_permissions(),
        }
        
        if include_sensitive:
            result.update({
                "gdpr_consent": self.gdpr_consent,
                "gdpr_consent_date": self.gdpr_consent_date.isoformat() if self.gdpr_consent_date else None,
                "failed_login_attempts": self.failed_login_attempts,
                "is_locked": self.is_locked,
                "is_password_expired": self.is_password_expired,
            })
        
        return result
    
    def __repr__(self):
        return f"<User {self.email}>"

class Role(Base):
    """Role model for role-based access control."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Role hierarchy
    parent_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    level = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System roles cannot be deleted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    parent = relationship("Role", remote_side=[id])
    children = relationship("Role", back_populates="parent")
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has specific permission."""
        for permission in self.permissions:
            if permission.name == permission_name:
                return True
        return False
    
    def get_all_permissions(self) -> List[str]:
        """Get all permissions for this role."""
        return [permission.name for permission in self.permissions]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "level": self.level,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "permissions": self.get_all_permissions(),
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<Role {self.name}>"

class Permission(Base):
    """Permission model for fine-grained access control."""
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permission categorization
    category = Column(String(50), nullable=False)  # e.g., 'users', 'companies', 'predictions'
    action = Column(String(50), nullable=False)    # e.g., 'create', 'read', 'update', 'delete'
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System permissions cannot be deleted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    users = relationship("User", secondary=user_permissions, back_populates="permissions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert permission to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "action": self.action,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<Permission {self.name}>"

class UserProfile(Base):
    """Extended user profile for additional information."""
    
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Extended profile information
    bio = Column(Text, nullable=True)
    website = Column(String(200), nullable=True)
    social_links = Column(JSON, nullable=True)
    
    # Address information
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Professional information
    education = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="profile")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bio": self.bio,
            "website": self.website,
            "social_links": self.social_links,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "emergency_contact": {
                "name": self.emergency_contact_name,
                "phone": self.emergency_contact_phone,
                "relationship": self.emergency_contact_relationship,
            },
            "education": self.education,
            "certifications": self.certifications,
            "skills": self.skills,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<UserProfile {self.user_id}>"
