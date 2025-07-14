from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.core.database import Base

class UserSession(Base):
    """User session tracking for security and analytics."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session information
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    location_info = Column(JSON, nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Session lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)."""
        return self.is_active and not self.is_expired and not self.revoked_at
    
    @property
    def time_until_expiry(self) -> Optional[timedelta]:
        """Get time until session expires."""
        if self.is_expired:
            return None
        return self.expires_at - datetime.utcnow()
    
    def extend_session(self, minutes: int = 30) -> None:
        """Extend session expiry time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.last_activity = datetime.utcnow()
    
    def revoke(self) -> None:
        """Revoke the session."""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def parse_user_agent(self) -> Dict[str, Any]:
        """Parse user agent string for device information."""
        if not self.user_agent:
            return {}
        
        # Simple user agent parsing (in production, use a proper library)
        user_agent = self.user_agent.lower()
        
        # Browser detection
        browsers = {
            'chrome': 'Chrome',
            'firefox': 'Firefox',
            'safari': 'Safari',
            'edge': 'Edge',
            'opera': 'Opera'
        }
        
        browser = 'Unknown'
        for key, value in browsers.items():
            if key in user_agent:
                browser = value
                break
        
        # OS detection
        operating_systems = {
            'windows': 'Windows',
            'mac': 'macOS',
            'linux': 'Linux',
            'android': 'Android',
            'ios': 'iOS'
        }
        
        os = 'Unknown'
        for key, value in operating_systems.items():
            if key in user_agent:
                os = value
                break
        
        # Device type detection
        device_type = 'Desktop'
        if 'mobile' in user_agent:
            device_type = 'Mobile'
        elif 'tablet' in user_agent:
            device_type = 'Tablet'
        
        return {
            'browser': browser,
            'os': os,
            'device_type': device_type,
            'raw_user_agent': self.user_agent
        }
    
    def calculate_risk_score(self) -> int:
        """Calculate risk score for this session."""
        score = 0
        
        # Check for suspicious IP patterns
        if self.ip_address:
            # Check if IP is from a known proxy/VPN range (simplified)
            suspicious_ip_patterns = ['10.0.', '127.0.', '192.168.']
            if any(pattern in self.ip_address for pattern in suspicious_ip_patterns):
                score += 10
        
        # Check for unusual user agent
        if self.user_agent:
            # Very short or very long user agents are suspicious
            if len(self.user_agent) < 20 or len(self.user_agent) > 1000:
                score += 15
            
            # Check for bot indicators
            bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
            if any(indicator in self.user_agent.lower() for indicator in bot_indicators):
                score += 25
        
        # Check session duration
        if self.created_at:
            duration = datetime.utcnow() - self.created_at
            # Sessions longer than 24 hours are suspicious
            if duration > timedelta(hours=24):
                score += 20
        
        # Check for multiple rapid requests (would need additional tracking)
        # This is a placeholder for more sophisticated analysis
        
        return min(score, 100)  # Cap at 100
    
    def update_location_info(self, location_data: Dict[str, Any]) -> None:
        """Update location information for the session."""
        self.location_info = location_data
    
    def update_device_info(self, device_data: Dict[str, Any]) -> None:
        """Update device information for the session."""
        self.device_info = device_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_info": self.device_info or self.parse_user_agent(),
            "location_info": self.location_info,
            "is_active": self.is_active,
            "is_valid": self.is_valid,
            "is_expired": self.is_expired,
            "is_suspicious": self.is_suspicious,
            "risk_score": self.risk_score,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "time_until_expiry": str(self.time_until_expiry) if self.time_until_expiry else None,
        }
    
    def __repr__(self):
        return f"<UserSession {self.session_id} for user {self.user_id}>"

class SessionActivity(Base):
    """Track detailed session activities for security monitoring."""
    
    __tablename__ = "session_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("user_sessions.session_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # login, logout, api_call, etc.
    endpoint = Column(String(200), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.
    status_code = Column(Integer, nullable=True)
    
    # Request details
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # Timing information
    duration_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)
    
    # Relationships
    session = relationship("UserSession")
    user = relationship("User")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "is_suspicious": self.is_suspicious,
            "risk_score": self.risk_score,
        }
    
    def __repr__(self):
        return f"<SessionActivity {self.activity_type} for session {self.session_id}>"

class LoginAttempt(Base):
    """Track login attempts for security monitoring."""
    
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Attempt details
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Attempt result
    success = Column(Boolean, default=False)
    failure_reason = Column(String(100), nullable=True)
    
    # Security information
    risk_score = Column(Integer, default=0)
    is_suspicious = Column(Boolean, default=False)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Additional context
    context = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert login attempt to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "risk_score": self.risk_score,
            "is_suspicious": self.is_suspicious,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }
    
    def __repr__(self):
        return f"<LoginAttempt {self.email} {'success' if self.success else 'failed'}>"
