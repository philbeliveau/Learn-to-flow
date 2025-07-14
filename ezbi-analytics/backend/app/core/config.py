from pydantic import BaseSettings, Field, validator
from typing import List, Optional, Any
import secrets
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Basic API settings
    PROJECT_NAME: str = "EZBI Analytics API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # Server settings
    SERVER_HOST: str = Field(default="http://localhost:8000")
    PRODUCTION_HOST: str = Field(default="https://api.ezbi-analytics.com")
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1", "*.ezbi-analytics.com"])
    
    # Security settings
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)  # 7 days
    RESET_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Encryption settings
    ENCRYPTION_MASTER_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    FERNET_KEY: Optional[str] = None
    
    # Database settings
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:password@localhost/ezbi_analytics")
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_ECHO: bool = Field(default=False)
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = Field(default=10)
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "https://ezbi-analytics.com",
            "https://www.ezbi-analytics.com",
        ]
    )
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)  # seconds
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".xlsx", ".xls", ".csv", ".pdf", ".docx", ".xml"]
    )
    UPLOAD_DIR: str = Field(default="./uploads")
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = Field(default=True)
    
    # Notification settings
    FROM_EMAIL: str = Field(default="noreply@ezbi-analytics.com")
    FROM_NAME: str = Field(default="EZBI Analytics")
    
    # ML settings
    MODEL_PATH: str = Field(default="./models")
    PREDICTION_CACHE_TTL: int = Field(default=3600)  # 1 hour
    MAX_PREDICTION_PERIOD: int = Field(default=365)  # days
    
    # Monitoring settings
    PROMETHEUS_ENABLED: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: Optional[str] = None
    
    # API Documentation
    CONTACT_NAME: str = Field(default="EZBI Analytics Support")
    CONTACT_EMAIL: str = Field(default="support@ezbi-analytics.com")
    CONTACT_URL: str = Field(default="https://ezbi-analytics.com/support")
    
    LICENSE_NAME: str = Field(default="MIT")
    LICENSE_URL: str = Field(default="https://opensource.org/licenses/MIT")
    
    # French compliance settings
    RGPD_ENABLED: bool = Field(default=True)
    DATA_RETENTION_DAYS: int = Field(default=2555)  # 7 years for French accounting
    AUDIT_LOG_ENABLED: bool = Field(default=True)
    
    # ERP Integration settings
    SAGE_API_ENABLED: bool = Field(default=False)
    SAP_API_ENABLED: bool = Field(default=False)
    CEGID_API_ENABLED: bool = Field(default=False)
    
    # Banking integration settings
    OPEN_BANKING_ENABLED: bool = Field(default=False)
    PSD2_CERTIFICATE_PATH: Optional[str] = None
    
    # Celery settings
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    
    # Session settings
    SESSION_COOKIE_NAME: str = Field(default="ezbi_session")
    SESSION_COOKIE_SECURE: bool = Field(default=True)
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True)
    SESSION_COOKIE_SAMESITE: str = Field(default="lax")
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from environment."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        """Assemble database URL from components or use provided URL."""
        if isinstance(v, str):
            return v
        
        # Fallback to component-based construction
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "password")
        db_name = os.getenv("DB_NAME", "ezbi_analytics")
        
        return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for migrations."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Global settings instance
settings = get_settings()
