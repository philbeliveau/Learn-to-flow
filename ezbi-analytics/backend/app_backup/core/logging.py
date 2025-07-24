import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json

import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import JSONRenderer, TimeStamper

from app.core.config import settings

def setup_logging():
    """Setup structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

class RequestLogger:
    """Logger for HTTP requests with security and performance monitoring."""
    
    def __init__(self):
        self.logger = structlog.get_logger("request")
    
    def log_request(self, request, response=None, duration_ms=None, user_id=None):
        """Log HTTP request details."""
        
        # Extract request information
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "user_id": user_id,
        }
        
        # Add response information if available
        if response:
            request_info.update({
                "status_code": response.status_code,
                "response_size": len(response.body) if hasattr(response, 'body') else None,
                "duration_ms": duration_ms,
            })
        
        # Remove sensitive headers
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]
        for header in sensitive_headers:
            request_info["headers"].pop(header, None)
        
        # Log with appropriate level
        if response and response.status_code >= 500:
            self.logger.error("HTTP request error", **request_info)
        elif response and response.status_code >= 400:
            self.logger.warning("HTTP request warning", **request_info)
        else:
            self.logger.info("HTTP request", **request_info)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "warning"):
        """Log security-related events."""
        
        security_info = {
            "event_type": event_type,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        }
        
        if severity == "critical":
            self.logger.critical("Security event", **security_info)
        elif severity == "high":
            self.logger.error("Security event", **security_info)
        elif severity == "medium":
            self.logger.warning("Security event", **security_info)
        else:
            self.logger.info("Security event", **security_info)

class DatabaseLogger:
    """Logger for database operations."""
    
    def __init__(self):
        self.logger = structlog.get_logger("database")
    
    def log_query(self, query: str, params: Dict[str, Any] = None, duration_ms: float = None, 
                  rows_affected: int = None, user_id: int = None):
        """Log database query execution."""
        
        query_info = {
            "query": query,
            "params": params,
            "duration_ms": duration_ms,
            "rows_affected": rows_affected,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Log slow queries as warnings
        if duration_ms and duration_ms > 1000:  # 1 second
            self.logger.warning("Slow database query", **query_info)
        else:
            self.logger.info("Database query", **query_info)
    
    def log_connection_event(self, event_type: str, details: Dict[str, Any]):
        """Log database connection events."""
        
        connection_info = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        }
        
        self.logger.info("Database connection event", **connection_info)
    
    def log_transaction_event(self, event_type: str, transaction_id: str = None, 
                             details: Dict[str, Any] = None):
        """Log database transaction events."""
        
        transaction_info = {
            "event_type": event_type,
            "transaction_id": transaction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        
        self.logger.info("Database transaction", **transaction_info)

class AuditLogger:
    """Logger for audit events and compliance."""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_user_action(self, user_id: int, action: str, resource_type: str, 
                       resource_id: str = None, details: Dict[str, Any] = None,
                       ip_address: str = None, user_agent: str = None):
        """Log user actions for audit trail."""
        
        audit_info = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        
        self.logger.info("User action", **audit_info)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any], 
                        severity: str = "info"):
        """Log system events for audit trail."""
        
        system_info = {
            "event_type": event_type,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        }
        
        if severity == "critical":
            self.logger.critical("System event", **system_info)
        elif severity == "error":
            self.logger.error("System event", **system_info)
        elif severity == "warning":
            self.logger.warning("System event", **system_info)
        else:
            self.logger.info("System event", **system_info)
    
    def log_data_access(self, user_id: int, data_type: str, operation: str,
                       record_count: int = None, filters: Dict[str, Any] = None,
                       ip_address: str = None):
        """Log data access for GDPR compliance."""
        
        access_info = {
            "user_id": user_id,
            "data_type": data_type,
            "operation": operation,
            "record_count": record_count,
            "filters": filters,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.logger.info("Data access", **access_info)
    
    def log_gdpr_event(self, user_id: int, event_type: str, details: Dict[str, Any],
                      data_subject_id: str = None):
        """Log GDPR-related events."""
        
        gdpr_info = {
            "user_id": user_id,
            "event_type": event_type,
            "data_subject_id": data_subject_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "regulation": "GDPR",
        }
        
        self.logger.info("GDPR event", **gdpr_info)

class PerformanceLogger:
    """Logger for performance monitoring."""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    def log_operation_timing(self, operation: str, duration_ms: float, 
                           context: Dict[str, Any] = None, user_id: int = None):
        """Log operation timing for performance monitoring."""
        
        timing_info = {
            "operation": operation,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {},
        }
        
        # Log slow operations as warnings
        if duration_ms > 5000:  # 5 seconds
            self.logger.warning("Slow operation", **timing_info)
        else:
            self.logger.info("Operation timing", **timing_info)
    
    def log_ml_model_performance(self, model_type: str, operation: str, 
                               duration_ms: float, accuracy: float = None,
                               data_points: int = None, user_id: int = None):
        """Log ML model performance metrics."""
        
        ml_info = {
            "model_type": model_type,
            "operation": operation,
            "duration_ms": duration_ms,
            "accuracy": accuracy,
            "data_points": data_points,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.logger.info("ML model performance", **ml_info)
    
    def log_resource_usage(self, resource_type: str, usage_amount: float, 
                          limit: float = None, user_id: int = None,
                          company_id: int = None):
        """Log resource usage for monitoring."""
        
        usage_info = {
            "resource_type": resource_type,
            "usage_amount": usage_amount,
            "limit": limit,
            "usage_percentage": (usage_amount / limit * 100) if limit else None,
            "user_id": user_id,
            "company_id": company_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Log high usage as warnings
        if limit and usage_amount > limit * 0.8:  # 80% of limit
            self.logger.warning("High resource usage", **usage_info)
        else:
            self.logger.info("Resource usage", **usage_info)

class BusinessLogger:
    """Logger for business events and metrics."""
    
    def __init__(self):
        self.logger = structlog.get_logger("business")
    
    def log_user_registration(self, user_id: int, email: str, company_id: int = None,
                            source: str = None, ip_address: str = None):
        """Log user registration events."""
        
        registration_info = {
            "user_id": user_id,
            "email": email,
            "company_id": company_id,
            "source": source,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.logger.info("User registration", **registration_info)
    
    def log_subscription_event(self, company_id: int, event_type: str, 
                             tier: str = None, details: Dict[str, Any] = None):
        """Log subscription-related events."""
        
        subscription_info = {
            "company_id": company_id,
            "event_type": event_type,
            "tier": tier,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        
        self.logger.info("Subscription event", **subscription_info)
    
    def log_feature_usage(self, user_id: int, feature: str, company_id: int = None,
                         usage_details: Dict[str, Any] = None):
        """Log feature usage for analytics."""
        
        usage_info = {
            "user_id": user_id,
            "company_id": company_id,
            "feature": feature,
            "timestamp": datetime.utcnow().isoformat(),
            "usage_details": usage_details or {},
        }
        
        self.logger.info("Feature usage", **usage_info)
    
    def log_prediction_event(self, user_id: int, company_id: int, prediction_type: str,
                           model_type: str, accuracy: float = None, 
                           duration_ms: float = None):
        """Log prediction generation events."""
        
        prediction_info = {
            "user_id": user_id,
            "company_id": company_id,
            "prediction_type": prediction_type,
            "model_type": model_type,
            "accuracy": accuracy,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.logger.info("Prediction event", **prediction_info)

class IntegrationLogger:
    """Logger for integration events and monitoring."""
    
    def __init__(self):
        self.logger = structlog.get_logger("integration")
    
    def log_integration_event(self, integration_id: int, event_type: str, 
                            status: str, details: Dict[str, Any] = None,
                            duration_ms: float = None, company_id: int = None):
        """Log integration events."""
        
        integration_info = {
            "integration_id": integration_id,
            "company_id": company_id,
            "event_type": event_type,
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        
        if status == "failed":
            self.logger.error("Integration event", **integration_info)
        elif status == "warning":
            self.logger.warning("Integration event", **integration_info)
        else:
            self.logger.info("Integration event", **integration_info)
    
    def log_sync_event(self, integration_id: int, records_processed: int,
                      records_successful: int, records_failed: int,
                      duration_ms: float, company_id: int = None):
        """Log integration sync events."""
        
        sync_info = {
            "integration_id": integration_id,
            "company_id": company_id,
            "records_processed": records_processed,
            "records_successful": records_successful,
            "records_failed": records_failed,
            "success_rate": records_successful / records_processed if records_processed > 0 else 0,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if records_failed > 0:
            self.logger.warning("Integration sync with errors", **sync_info)
        else:
            self.logger.info("Integration sync", **sync_info)

# Global logger instances
request_logger = RequestLogger()
database_logger = DatabaseLogger()
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
business_logger = BusinessLogger()
integration_logger = IntegrationLogger()

# Log level utilities
def get_log_level(level_name: str) -> int:
    """Get numeric log level from string."""
    return getattr(logging, level_name.upper(), logging.INFO)

def is_debug_enabled() -> bool:
    """Check if debug logging is enabled."""
    return settings.LOG_LEVEL.upper() == "DEBUG"

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data in logs."""
    sensitive_keys = {
        "password", "secret", "token", "key", "credential", "auth",
        "ssn", "social_security", "credit_card", "card_number",
        "email", "phone", "address", "name"
    }
    
    masked_data = {}
    for key, value in data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            masked_data[key] = "[REDACTED]"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        else:
            masked_data[key] = value
    
    return masked_data

def log_context(**kwargs):
    """Add context to all log messages in the current scope."""
    return structlog.contextvars.bind_contextvars(**kwargs)

def clear_log_context():
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()
