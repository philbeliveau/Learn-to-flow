from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from app.core.database import Base

class IntegrationType(enum.Enum):
    """Integration types."""
    BANKING = "banking"
    ERP = "erp"
    ACCOUNTING = "accounting"
    CRM = "crm"
    ECOMMERCE = "ecommerce"
    PAYMENT = "payment"
    API = "api"
    WEBHOOK = "webhook"
    FILE_IMPORT = "file_import"
    CUSTOM = "custom"

class IntegrationStatus(enum.Enum):
    """Integration status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"

class IntegrationProvider(enum.Enum):
    """Integration providers."""
    SAGE = "sage"
    SAP = "sap"
    CEGID = "cegid"
    DOLIBARR = "dolibarr"
    ODOO = "odoo"
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    BANKIN = "bankin"
    BRIDGE = "bridge"
    CUSTOM = "custom"

class Integration(Base):
    """External system integrations."""
    
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Integration identification
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    integration_type = Column(String(30), nullable=False)
    provider = Column(String(30), nullable=False)
    
    # Configuration
    configuration = Column(JSON, nullable=False)
    credentials = Column(JSON, nullable=True)  # Encrypted credentials
    
    # Connection details
    endpoint_url = Column(String(500), nullable=True)
    api_version = Column(String(20), nullable=True)
    
    # Status and health
    status = Column(String(20), default=IntegrationStatus.PENDING.value)
    health_status = Column(String(20), default="unknown")
    last_health_check = Column(DateTime, nullable=True)
    
    # Sync configuration
    sync_enabled = Column(Boolean, default=True)
    sync_frequency = Column(String(20), default="hourly")  # hourly, daily, weekly, manual
    last_sync = Column(DateTime, nullable=True)
    next_sync = Column(DateTime, nullable=True)
    
    # Data mapping
    field_mapping = Column(JSON, nullable=True)
    transformation_rules = Column(JSON, nullable=True)
    
    # Filtering and limits
    sync_filters = Column(JSON, nullable=True)
    rate_limits = Column(JSON, nullable=True)
    
    # Monitoring
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    
    # Security
    requires_auth = Column(Boolean, default=True)
    auth_type = Column(String(20), default="oauth2")
    
    # Compliance
    data_retention_days = Column(Integer, default=90)
    encryption_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="integrations")
    creator = relationship("User")
    logs = relationship("IntegrationLog", back_populates="integration")
    
    @property
    def is_active(self) -> bool:
        """Check if integration is active."""
        return self.status == IntegrationStatus.ACTIVE.value
    
    @property
    def is_healthy(self) -> bool:
        """Check if integration is healthy."""
        return self.health_status == "healthy"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    @property
    def needs_health_check(self) -> bool:
        """Check if health check is needed."""
        if not self.last_health_check:
            return True
        
        # Check every hour
        from datetime import timedelta
        return datetime.utcnow() - self.last_health_check > timedelta(hours=1)
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)."""
        config = self.configuration.copy() if self.configuration else {}
        
        # Remove sensitive keys
        sensitive_keys = ['password', 'secret', 'key', 'token', 'credential']
        for key in list(config.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                config[key] = "[REDACTED]"
        
        return config
    
    def test_connection(self) -> Dict[str, Any]:
        """Test integration connection."""
        # This would contain actual connection testing logic
        # For now, return a mock response
        return {
            "success": True,
            "response_time_ms": 250,
            "message": "Connection successful",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {},
            "overall_health": True,
        }
        
        # Connection test
        connection_test = self.test_connection()
        health_result["checks"]["connection"] = connection_test
        
        # Rate limit check
        if self.rate_limits:
            health_result["checks"]["rate_limits"] = {
                "within_limits": True,
                "current_usage": "unknown",
            }
        
        # Authentication check
        if self.requires_auth:
            health_result["checks"]["authentication"] = {
                "valid": True,
                "expires_at": None,
            }
        
        # Determine overall health
        overall_health = all(
            check.get("success", check.get("valid", True)) 
            for check in health_result["checks"].values()
        )
        
        health_result["overall_health"] = overall_health
        health_result["status"] = "healthy" if overall_health else "unhealthy"
        
        # Update integration
        self.health_status = health_result["status"]
        self.last_health_check = datetime.utcnow()
        
        return health_result
    
    def increment_success_count(self) -> None:
        """Increment success counter."""
        self.success_count += 1
        self.last_sync = datetime.utcnow()
    
    def increment_error_count(self, error_message: str) -> None:
        """Increment error counter."""
        self.error_count += 1
        self.last_error = error_message
        self.last_error_at = datetime.utcnow()
    
    def reset_counters(self) -> None:
        """Reset success and error counters."""
        self.success_count = 0
        self.error_count = 0
        self.last_error = None
        self.last_error_at = None
    
    def get_sync_schedule(self) -> Dict[str, Any]:
        """Get sync schedule information."""
        schedule = {
            "enabled": self.sync_enabled,
            "frequency": self.sync_frequency,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "next_sync": self.next_sync.isoformat() if self.next_sync else None,
        }
        
        if self.last_sync:
            time_since_sync = datetime.utcnow() - self.last_sync
            schedule["time_since_last_sync"] = str(time_since_sync)
        
        return schedule
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "health_status": self.health_status,
            "last_error": self.last_error,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "uptime_percentage": self._calculate_uptime_percentage(),
        }
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage (simplified)."""
        # This would use actual uptime monitoring data
        # For now, return a calculated value based on success rate
        return self.success_rate * 100
    
    def enable(self) -> None:
        """Enable integration."""
        self.status = IntegrationStatus.ACTIVE.value
        self.sync_enabled = True
    
    def disable(self) -> None:
        """Disable integration."""
        self.status = IntegrationStatus.DISABLED.value
        self.sync_enabled = False
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert integration to dictionary."""
        result = {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "integration_type": self.integration_type,
            "provider": self.provider,
            "status": self.status,
            "health_status": self.health_status,
            "is_active": self.is_active,
            "is_healthy": self.is_healthy,
            "sync_enabled": self.sync_enabled,
            "sync_frequency": self.sync_frequency,
            "success_rate": self.success_rate,
            "endpoint_url": self.endpoint_url,
            "api_version": self.api_version,
            "requires_auth": self.requires_auth,
            "auth_type": self.auth_type,
            "encryption_enabled": self.encryption_enabled,
            "configuration_summary": self.get_configuration_summary(),
            "sync_schedule": self.get_sync_schedule(),
            "performance_metrics": self.get_performance_metrics(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_sensitive:
            result.update({
                "configuration": self.configuration,
                "credentials": self.credentials,
                "field_mapping": self.field_mapping,
                "transformation_rules": self.transformation_rules,
                "sync_filters": self.sync_filters,
                "rate_limits": self.rate_limits,
            })
        
        return result
    
    def __repr__(self):
        return f"<Integration {self.name} ({self.provider})>"

class IntegrationLog(Base):
    """Integration operation logs."""
    
    __tablename__ = "integration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    
    # Log details
    operation = Column(String(50), nullable=False)  # sync, health_check, test, etc.
    status = Column(String(20), nullable=False)  # success, error, warning
    message = Column(Text, nullable=False)
    
    # Operation context
    duration_ms = Column(Integer, nullable=True)
    records_processed = Column(Integer, nullable=True)
    records_successful = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    
    # Request/response details
    request_details = Column(JSON, nullable=True)
    response_details = Column(JSON, nullable=True)
    
    # Error details
    error_code = Column(String(50), nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="logs")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get operation summary."""
        return {
            "operation": self.operation,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "records_processed": self.records_processed,
            "records_successful": self.records_successful,
            "records_failed": self.records_failed,
            "success_rate": self._calculate_success_rate(),
            "timestamp": self.timestamp.isoformat(),
        }
    
    def _calculate_success_rate(self) -> Optional[float]:
        """Calculate success rate for this operation."""
        if self.records_processed and self.records_processed > 0:
            successful = self.records_successful or 0
            return successful / self.records_processed
        return None
    
    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """Convert log to dictionary."""
        result = {
            "id": self.id,
            "integration_id": self.integration_id,
            "operation": self.operation,
            "status": self.status,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "records_processed": self.records_processed,
            "records_successful": self.records_successful,
            "records_failed": self.records_failed,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.get_summary(),
        }
        
        if include_details:
            result.update({
                "request_details": self.request_details,
                "response_details": self.response_details,
                "error_details": self.error_details,
            })
        
        return result
    
    def __repr__(self):
        return f"<IntegrationLog {self.operation} {self.status}>"
