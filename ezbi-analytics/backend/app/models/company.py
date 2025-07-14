from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Numeric, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional, List, Dict, Any
import enum

from app.core.database import Base

class CompanyType(enum.Enum):
    """Company type classification."""
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    CONSTRUCTION = "construction"
    AGRICULTURE = "agriculture"
    OTHER = "other"

class CompanySize(enum.Enum):
    """Company size classification."""
    MICRO = "micro"        # < 10 employees
    SMALL = "small"        # 10-49 employees  
    MEDIUM = "medium"      # 50-249 employees
    LARGE = "large"        # 250+ employees

class CompanyStatus(enum.Enum):
    """Company status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    PENDING = "pending"

class Company(Base):
    """Company model for multi-tenant support."""
    
    __tablename__ = "companies"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(200), nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # French business registration
    siret = Column(String(14), unique=True, nullable=True, index=True)  # SIRET number
    siren = Column(String(9), nullable=True, index=True)  # SIREN number
    naf_code = Column(String(10), nullable=True)  # NAF/APE code
    tva_number = Column(String(20), nullable=True)  # TVA intracommunautaire
    
    # Company classification
    company_type = Column(String(20), default=CompanyType.MANUFACTURING.value)
    company_size = Column(String(20), default=CompanySize.SMALL.value)
    status = Column(String(20), default=CompanyStatus.ACTIVE.value)
    
    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Address information
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="France")
    
    # Financial information
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    employee_count = Column(Integer, nullable=True)
    founded_year = Column(Integer, nullable=True)
    
    # Manufacturing specific
    manufacturing_sectors = Column(JSON, nullable=True)  # List of manufacturing sectors
    production_capacity = Column(JSON, nullable=True)  # Production capacity metrics
    main_products = Column(JSON, nullable=True)  # List of main products
    
    # Financial settings
    default_currency = Column(String(3), default="EUR")
    fiscal_year_start = Column(Integer, default=1)  # Month (1-12)
    accounting_method = Column(String(20), default="accrual")  # accrual or cash
    
    # Subscription and billing
    subscription_tier = Column(String(20), default="basic")
    subscription_status = Column(String(20), default="active")
    trial_expires_at = Column(DateTime, nullable=True)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Features and limits
    features = Column(JSON, nullable=True)
    usage_limits = Column(JSON, nullable=True)
    current_usage = Column(JSON, nullable=True)
    
    # Compliance and certifications
    certifications = Column(JSON, nullable=True)  # ISO, etc.
    compliance_status = Column(JSON, nullable=True)  # GDPR, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="company")
    financial_data = relationship("FinancialData", back_populates="company")
    predictions = relationship("Prediction", back_populates="company")
    file_uploads = relationship("FileUpload", back_populates="company")
    integrations = relationship("Integration", back_populates="company")
    
    # Hybrid properties
    @hybrid_property
    def is_active(self) -> bool:
        """Check if company is active."""
        return self.status == CompanyStatus.ACTIVE.value
    
    @hybrid_property
    def is_trial(self) -> bool:
        """Check if company is in trial period."""
        return self.status == CompanyStatus.TRIAL.value
    
    @hybrid_property
    def is_trial_expired(self) -> bool:
        """Check if trial has expired."""
        if self.trial_expires_at:
            return datetime.utcnow() > self.trial_expires_at
        return False
    
    @hybrid_property
    def is_subscription_expired(self) -> bool:
        """Check if subscription has expired."""
        if self.subscription_expires_at:
            return datetime.utcnow() > self.subscription_expires_at
        return False
    
    @hybrid_property
    def display_name(self) -> str:
        """Get display name for company."""
        return self.legal_name or self.name
    
    @hybrid_property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city:
            parts.append(self.city)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)
    
    # Methods
    def get_default_features(self) -> Dict[str, Any]:
        """Get default features based on subscription tier."""
        tier_features = {
            "basic": {
                "max_users": 5,
                "max_predictions": 100,
                "max_file_uploads": 50,
                "data_retention_days": 365,
                "api_calls_per_day": 1000,
                "ml_models": ["prophet"],
                "integrations": ["csv", "excel"],
                "support_level": "email"
            },
            "professional": {
                "max_users": 25,
                "max_predictions": 500,
                "max_file_uploads": 250,
                "data_retention_days": 1095,  # 3 years
                "api_calls_per_day": 5000,
                "ml_models": ["prophet", "lstm"],
                "integrations": ["csv", "excel", "sage", "api"],
                "support_level": "chat"
            },
            "enterprise": {
                "max_users": -1,  # unlimited
                "max_predictions": -1,
                "max_file_uploads": -1,
                "data_retention_days": 2555,  # 7 years
                "api_calls_per_day": -1,
                "ml_models": ["prophet", "lstm", "ensemble"],
                "integrations": ["csv", "excel", "sage", "sap", "cegid", "api", "banking"],
                "support_level": "phone"
            }
        }
        
        defaults = tier_features.get(self.subscription_tier, tier_features["basic"])
        
        if self.features:
            defaults.update(self.features)
        
        return defaults
    
    def get_usage_limits(self) -> Dict[str, Any]:
        """Get usage limits for the company."""
        features = self.get_default_features()
        
        limits = {
            "max_users": features["max_users"],
            "max_predictions": features["max_predictions"],
            "max_file_uploads": features["max_file_uploads"],
            "api_calls_per_day": features["api_calls_per_day"],
        }
        
        if self.usage_limits:
            limits.update(self.usage_limits)
        
        return limits
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        defaults = {
            "users": 0,
            "predictions": 0,
            "file_uploads": 0,
            "api_calls_today": 0,
            "storage_used_mb": 0,
        }
        
        if self.current_usage:
            defaults.update(self.current_usage)
        
        return defaults
    
    def check_usage_limit(self, resource: str, requested_amount: int = 1) -> bool:
        """Check if usage limit allows the requested amount."""
        limits = self.get_usage_limits()
        current = self.get_current_usage()
        
        limit = limits.get(resource)
        if limit == -1:  # Unlimited
            return True
        
        current_value = current.get(resource, 0)
        return current_value + requested_amount <= limit
    
    def increment_usage(self, resource: str, amount: int = 1) -> None:
        """Increment usage counter for a resource."""
        current = self.get_current_usage()
        current[resource] = current.get(resource, 0) + amount
        self.current_usage = current
    
    def has_feature(self, feature: str) -> bool:
        """Check if company has access to a specific feature."""
        features = self.get_default_features()
        return feature in features
    
    def can_use_integration(self, integration: str) -> bool:
        """Check if company can use a specific integration."""
        features = self.get_default_features()
        return integration in features.get("integrations", [])
    
    def can_use_ml_model(self, model: str) -> bool:
        """Check if company can use a specific ML model."""
        features = self.get_default_features()
        return model in features.get("ml_models", [])
    
    def validate_siret(self) -> bool:
        """Validate SIRET number format."""
        if not self.siret:
            return False
        
        # SIRET should be 14 digits
        if len(self.siret) != 14 or not self.siret.isdigit():
            return False
        
        # Extract SIREN (first 9 digits)
        siren = self.siret[:9]
        
        # Validate SIREN checksum (Luhn algorithm)
        def luhn_checksum(siren):
            total = 0
            for i, digit in enumerate(siren):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n = n // 10 + n % 10
                total += n
            return total % 10 == 0
        
        return luhn_checksum(siren)
    
    def get_manufacturing_info(self) -> Dict[str, Any]:
        """Get manufacturing-specific information."""
        return {
            "sectors": self.manufacturing_sectors or [],
            "production_capacity": self.production_capacity or {},
            "main_products": self.main_products or [],
            "company_type": self.company_type,
            "company_size": self.company_size,
            "employee_count": self.employee_count,
            "annual_revenue": float(self.annual_revenue) if self.annual_revenue else None,
        }
    
    def get_financial_settings(self) -> Dict[str, Any]:
        """Get financial settings for the company."""
        return {
            "default_currency": self.default_currency,
            "fiscal_year_start": self.fiscal_year_start,
            "accounting_method": self.accounting_method,
            "annual_revenue": float(self.annual_revenue) if self.annual_revenue else None,
        }
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status information."""
        defaults = {
            "gdpr_compliant": False,
            "data_retention_policy": False,
            "privacy_policy": False,
            "terms_of_service": False,
            "security_audit": False,
        }
        
        if self.compliance_status:
            defaults.update(self.compliance_status)
        
        return defaults
    
    def update_compliance_status(self, status_updates: Dict[str, Any]) -> None:
        """Update compliance status."""
        current = self.get_compliance_status()
        current.update(status_updates)
        self.compliance_status = current
    
    def generate_slug(self) -> str:
        """Generate URL-friendly slug from company name."""
        import re
        import unicodedata
        
        # Normalize unicode characters
        value = unicodedata.normalize('NFKD', self.name).encode('ascii', 'ignore').decode('ascii')
        
        # Convert to lowercase and replace spaces with hyphens
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        value = re.sub(r'[-\s]+', '-', value)
        
        # Ensure uniqueness by checking database
        base_slug = value
        counter = 1
        
        # This would need to be implemented with proper database check
        # For now, return the generated slug
        return value
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert company to dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "legal_name": self.legal_name,
            "display_name": self.display_name,
            "slug": self.slug,
            "company_type": self.company_type,
            "company_size": self.company_size,
            "status": self.status,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
                "full_address": self.full_address,
            },
            "employee_count": self.employee_count,
            "founded_year": self.founded_year,
            "default_currency": self.default_currency,
            "subscription_tier": self.subscription_tier,
            "subscription_status": self.subscription_status,
            "features": self.get_default_features(),
            "usage_limits": self.get_usage_limits(),
            "current_usage": self.get_current_usage(),
            "manufacturing_info": self.get_manufacturing_info(),
            "financial_settings": self.get_financial_settings(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_sensitive:
            result.update({
                "siret": self.siret,
                "siren": self.siren,
                "naf_code": self.naf_code,
                "tva_number": self.tva_number,
                "annual_revenue": float(self.annual_revenue) if self.annual_revenue else None,
                "compliance_status": self.get_compliance_status(),
                "trial_expires_at": self.trial_expires_at.isoformat() if self.trial_expires_at else None,
                "subscription_expires_at": self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            })
        
        return result
    
    def __repr__(self):
        return f"<Company {self.name}>"

class CompanySettings(Base):
    """Extended company settings and configuration."""
    
    __tablename__ = "company_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), unique=True, nullable=False)
    
    # Notification settings
    notification_settings = Column(JSON, nullable=True)
    
    # Dashboard settings
    dashboard_config = Column(JSON, nullable=True)
    
    # Reporting settings
    reporting_config = Column(JSON, nullable=True)
    
    # Integration settings
    integration_settings = Column(JSON, nullable=True)
    
    # Custom fields configuration
    custom_fields = Column(JSON, nullable=True)
    
    # Workflow settings
    workflow_settings = Column(JSON, nullable=True)
    
    # Security settings
    security_settings = Column(JSON, nullable=True)
    
    # Backup settings
    backup_settings = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", backref="settings")
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings with defaults."""
        defaults = {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "prediction_alerts": True,
            "system_alerts": True,
            "billing_alerts": True,
            "frequency": "daily",
        }
        
        if self.notification_settings:
            defaults.update(self.notification_settings)
        
        return defaults
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration with defaults."""
        defaults = {
            "default_view": "overview",
            "show_welcome": True,
            "auto_refresh": True,
            "refresh_interval": 300,  # 5 minutes
            "widgets": [
                {"type": "cash_flow_chart", "size": "large", "position": {"x": 0, "y": 0}},
                {"type": "predictions_summary", "size": "medium", "position": {"x": 8, "y": 0}},
                {"type": "alerts", "size": "small", "position": {"x": 0, "y": 4}},
                {"type": "recent_uploads", "size": "medium", "position": {"x": 4, "y": 4}},
            ],
        }
        
        if self.dashboard_config:
            defaults.update(self.dashboard_config)
        
        return defaults
    
    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting configuration with defaults."""
        defaults = {
            "auto_reports": True,
            "report_frequency": "weekly",
            "report_format": "pdf",
            "include_charts": True,
            "include_raw_data": False,
            "recipients": [],
        }
        
        if self.reporting_config:
            defaults.update(self.reporting_config)
        
        return defaults
    
    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings with defaults."""
        defaults = {
            "require_mfa": False,
            "session_timeout": 3600,  # 1 hour
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special": True,
                "max_age_days": 90,
            },
            "ip_whitelist": [],
            "allowed_domains": [],
            "audit_logging": True,
        }
        
        if self.security_settings:
            defaults.update(self.security_settings)
        
        return defaults
    
    def update_setting(self, category: str, settings: Dict[str, Any]) -> None:
        """Update specific setting category."""
        current = getattr(self, f"{category}_settings") or {}
        current.update(settings)
        setattr(self, f"{category}_settings", current)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "notification_settings": self.get_notification_settings(),
            "dashboard_config": self.get_dashboard_config(),
            "reporting_config": self.get_reporting_config(),
            "security_settings": self.get_security_settings(),
            "integration_settings": self.integration_settings,
            "custom_fields": self.custom_fields,
            "workflow_settings": self.workflow_settings,
            "backup_settings": self.backup_settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<CompanySettings {self.company_id}>"
