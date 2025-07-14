from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from app.core.database import Base

class NotificationType(enum.Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"
    SYSTEM = "system"
    MARKETING = "marketing"

class NotificationChannel(enum.Enum):
    """Notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"

class NotificationPriority(enum.Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(enum.Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Notification(Base):
    """User notifications and alerts."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Notification content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(20), default=NotificationType.INFO.value)
    
    # Delivery settings
    channels = Column(JSON, nullable=False)  # List of channels to send to
    priority = Column(String(20), default=NotificationPriority.MEDIUM.value)
    
    # Status and tracking
    status = Column(String(20), default=NotificationStatus.PENDING.value)
    delivery_attempts = Column(Integer, default=0)
    max_delivery_attempts = Column(Integer, default=3)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Interaction tracking
    read_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    
    # Grouping and categorization
    category = Column(String(50), nullable=True)
    group_key = Column(String(100), nullable=True)  # For grouping related notifications
    
    # Templates
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    template_variables = Column(JSON, nullable=True)
    
    # Delivery tracking
    delivery_log = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    company = relationship("Company")
    template = relationship("NotificationTemplate")
    
    @property
    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.read_at is not None
    
    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    @property
    def is_scheduled(self) -> bool:
        """Check if notification is scheduled for future delivery."""
        return self.scheduled_for and datetime.utcnow() < self.scheduled_for
    
    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return (self.status == NotificationStatus.FAILED.value and 
                self.delivery_attempts < self.max_delivery_attempts)
    
    def mark_as_read(self) -> None:
        """Mark notification as read."""
        if not self.is_read:
            self.read_at = datetime.utcnow()
            self.status = NotificationStatus.READ.value
    
    def mark_as_clicked(self) -> None:
        """Mark notification as clicked."""
        if not self.clicked_at:
            self.clicked_at = datetime.utcnow()
            if not self.is_read:
                self.mark_as_read()
    
    def dismiss(self) -> None:
        """Dismiss notification."""
        self.dismissed_at = datetime.utcnow()
        if not self.is_read:
            self.mark_as_read()
    
    def mark_as_sent(self, channel: str) -> None:
        """Mark notification as sent on specific channel."""
        self.status = NotificationStatus.SENT.value
        self.sent_at = datetime.utcnow()
        
        # Update delivery log
        delivery_log = self.delivery_log or {}
        delivery_log[channel] = {
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat(),
            "attempt": self.delivery_attempts + 1,
        }
        self.delivery_log = delivery_log
        
        self.delivery_attempts += 1
    
    def mark_as_failed(self, channel: str, error: str) -> None:
        """Mark notification as failed on specific channel."""
        self.status = NotificationStatus.FAILED.value
        
        # Update delivery log
        delivery_log = self.delivery_log or {}
        delivery_log[channel] = {
            "status": "failed",
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "attempt": self.delivery_attempts + 1,
        }
        self.delivery_log = delivery_log
        
        self.delivery_attempts += 1
    
    def should_send_now(self) -> bool:
        """Check if notification should be sent now."""
        if self.is_expired:
            return False
        
        if self.is_scheduled:
            return False
        
        if self.status in [NotificationStatus.SENT.value, NotificationStatus.DELIVERED.value]:
            return False
        
        return True
    
    def get_delivery_summary(self) -> Dict[str, Any]:
        """Get delivery summary for all channels."""
        summary = {
            "total_channels": len(self.channels),
            "delivery_attempts": self.delivery_attempts,
            "max_attempts": self.max_delivery_attempts,
            "can_retry": self.can_retry,
            "channels": {},
        }
        
        if self.delivery_log:
            for channel, log in self.delivery_log.items():
                summary["channels"][channel] = {
                    "status": log.get("status"),
                    "timestamp": log.get("timestamp"),
                    "attempt": log.get("attempt"),
                    "error": log.get("error"),
                }
        
        return summary
    
    def get_engagement_metrics(self) -> Dict[str, Any]:
        """Get engagement metrics for the notification."""
        return {
            "is_read": self.is_read,
            "is_clicked": self.clicked_at is not None,
            "is_dismissed": self.dismissed_at is not None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "time_to_read": self._calculate_time_to_read(),
            "time_to_click": self._calculate_time_to_click(),
        }
    
    def _calculate_time_to_read(self) -> Optional[int]:
        """Calculate time to read in seconds."""
        if self.sent_at and self.read_at:
            return int((self.read_at - self.sent_at).total_seconds())
        return None
    
    def _calculate_time_to_click(self) -> Optional[int]:
        """Calculate time to click in seconds."""
        if self.sent_at and self.clicked_at:
            return int((self.clicked_at - self.sent_at).total_seconds())
        return None
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "channels": self.channels,
            "priority": self.priority,
            "status": self.status,
            "category": self.category,
            "group_key": self.group_key,
            "action_url": self.action_url,
            "action_text": self.action_text,
            "is_read": self.is_read,
            "is_expired": self.is_expired,
            "is_scheduled": self.is_scheduled,
            "can_retry": self.can_retry,
            "engagement_metrics": self.get_engagement_metrics(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
        
        if include_sensitive:
            result.update({
                "metadata": self.metadata,
                "template_id": self.template_id,
                "template_variables": self.template_variables,
                "delivery_summary": self.get_delivery_summary(),
                "delivery_attempts": self.delivery_attempts,
                "max_delivery_attempts": self.max_delivery_attempts,
            })
        
        return result
    
    def __repr__(self):
        return f"<Notification {self.title} to user {self.user_id}>"

class NotificationTemplate(Base):
    """Notification templates for consistent messaging."""
    
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Template identification
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Template content
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Default settings
    default_type = Column(String(20), default=NotificationType.INFO.value)
    default_channels = Column(JSON, nullable=False)
    default_priority = Column(String(20), default=NotificationPriority.MEDIUM.value)
    
    # Template configuration
    variables = Column(JSON, nullable=True)  # Available template variables
    validation_rules = Column(JSON, nullable=True)  # Validation for variables
    
    # Localization
    language = Column(String(10), default="en")
    
    # Status and usage
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    company = relationship("Company")
    creator = relationship("User")
    notifications = relationship("Notification")
    
    def render_template(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render template with provided variables."""
        import re
        
        # Simple template variable replacement
        title = self.title_template
        message = self.message_template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        return {
            "title": title,
            "message": message,
        }
    
    def validate_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template variables."""
        errors = []
        warnings = []
        
        # Check required variables
        required_vars = [var for var in (self.variables or []) if var.get("required", False)]
        
        for var in required_vars:
            var_name = var["name"]
            if var_name not in variables:
                errors.append(f"Required variable '{var_name}' is missing")
        
        # Check variable types
        for var in (self.variables or []):
            var_name = var["name"]
            var_type = var.get("type", "string")
            
            if var_name in variables:
                value = variables[var_name]
                
                if var_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Variable '{var_name}' must be a number")
                elif var_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Variable '{var_name}' must be a boolean")
                elif var_type == "date" and not isinstance(value, (str, datetime)):
                    errors.append(f"Variable '{var_name}' must be a date")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "title_template": self.title_template,
            "message_template": self.message_template,
            "default_type": self.default_type,
            "default_channels": self.default_channels,
            "default_priority": self.default_priority,
            "variables": self.variables,
            "validation_rules": self.validation_rules,
            "language": self.language,
            "is_active": self.is_active,
            "is_system_template": self.is_system_template,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<NotificationTemplate {self.name}>"
