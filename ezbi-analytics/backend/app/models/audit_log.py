from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from app.core.database import Base

class AuditAction(enum.Enum):
    """Audit action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PERMISSION_DENIED = "permission_denied"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_EVENT = "system_event"

class AuditSeverity(enum.Enum):
    """Audit log severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLog(Base):
    """Comprehensive audit logging for compliance and security."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User and company context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    
    # Event description
    description = Column(String(500), nullable=False)
    details = Column(JSON, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    # Response context
    response_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Security context
    severity = Column(String(20), default=AuditSeverity.LOW.value)
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)
    
    # Data changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Compliance metadata
    regulation_tags = Column(JSON, nullable=True)  # GDPR, SOX, etc.
    retention_period_days = Column(Integer, default=2555)  # 7 years default
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    company = relationship("Company")
    
    @staticmethod
    def create_log(
        action: str,
        resource_type: str,
        description: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = AuditSeverity.LOW.value,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """Create a new audit log entry."""
        return AuditLog(
            user_id=user_id,
            company_id=company_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            old_values=old_values,
            new_values=new_values,
        )
    
    def calculate_risk_score(self) -> int:
        """Calculate risk score for the audit event."""
        score = 0
        
        # High-risk actions
        high_risk_actions = [
            AuditAction.DELETE.value,
            AuditAction.FAILED_LOGIN.value,
            AuditAction.PERMISSION_DENIED.value,
            AuditAction.CONFIGURATION_CHANGE.value,
        ]
        
        if self.action in high_risk_actions:
            score += 30
        
        # Administrative actions
        admin_actions = [
            AuditAction.BACKUP.value,
            AuditAction.RESTORE.value,
            AuditAction.EXPORT.value,
        ]
        
        if self.action in admin_actions:
            score += 20
        
        # Failed operations
        if self.response_status and self.response_status >= 400:
            score += 25
        
        # Suspicious IP patterns
        if self.ip_address:
            # Check for common suspicious patterns
            if any(pattern in self.ip_address for pattern in ['10.0.', '192.168.', '127.0.']):
                score += 5
        
        # Multiple rapid actions (would need session context)
        # This is a placeholder for more sophisticated analysis
        
        # Unusual timing (outside business hours)
        if self.timestamp:
            hour = self.timestamp.hour
            if hour < 6 or hour > 22:  # Outside 6 AM - 10 PM
                score += 10
        
        return min(score, 100)
    
    def add_regulation_tags(self, tags: list) -> None:
        """Add regulation compliance tags."""
        current_tags = self.regulation_tags or []
        new_tags = list(set(current_tags + tags))
        self.regulation_tags = new_tags
    
    def mark_as_suspicious(self, reason: str) -> None:
        """Mark audit log as suspicious."""
        self.is_suspicious = True
        self.severity = AuditSeverity.HIGH.value
        details = self.details or {}
        details["suspicious_reason"] = reason
        details["marked_suspicious_at"] = datetime.utcnow().isoformat()
        self.details = details
    
    def get_data_changes(self) -> Dict[str, Any]:
        """Get summary of data changes."""
        if not self.old_values and not self.new_values:
            return {}
        
        changes = {
            "has_changes": bool(self.old_values or self.new_values),
            "fields_changed": [],
            "change_summary": {},
        }
        
        if self.old_values and self.new_values:
            # Compare old and new values
            for key in set(list(self.old_values.keys()) + list(self.new_values.keys())):
                old_val = self.old_values.get(key)
                new_val = self.new_values.get(key)
                
                if old_val != new_val:
                    changes["fields_changed"].append(key)
                    changes["change_summary"][key] = {
                        "old_value": old_val,
                        "new_value": new_val,
                    }
        
        return changes
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "severity": self.severity,
            "is_suspicious": self.is_suspicious,
            "risk_score": self.risk_score,
            "response_status": self.response_status,
            "response_time_ms": self.response_time_ms,
            "regulation_tags": self.regulation_tags,
            "timestamp": self.timestamp.isoformat(),
            "data_changes": self.get_data_changes(),
        }
        
        if include_sensitive:
            result.update({
                "details": self.details,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "request_method": self.request_method,
                "request_path": self.request_path,
                "old_values": self.old_values,
                "new_values": self.new_values,
            })
        
        return result
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type} by user {self.user_id}>"
