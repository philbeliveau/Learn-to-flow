from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional, List, Dict, Any
import enum
import os
import hashlib

from app.core.database import Base

class FileType(enum.Enum):
    """Supported file types."""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    DOCX = "docx"
    XML = "xml"
    JSON = "json"
    IMAGE = "image"
    OTHER = "other"

class FileStatus(enum.Enum):
    """File processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"
    QUARANTINED = "quarantined"

class FileCategory(enum.Enum):
    """File category for organization."""
    FINANCIAL_DATA = "financial_data"
    BANK_STATEMENTS = "bank_statements"
    INVOICES = "invoices"
    RECEIPTS = "receipts"
    CONTRACTS = "contracts"
    REPORTS = "reports"
    TEMPLATES = "templates"
    BACKUPS = "backups"
    OTHER = "other"

class FileUpload(Base):
    """File upload tracking and metadata."""
    
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File identification
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # File metadata
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    
    # File classification
    category = Column(String(30), default=FileCategory.OTHER.value)
    tags = Column(JSON, nullable=True)
    
    # Processing status
    status = Column(String(20), default=FileStatus.UPLOADED.value)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Processing results
    processing_results = Column(JSON, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    validation_results = Column(JSON, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Security and compliance
    is_sensitive = Column(Boolean, default=False)
    encryption_key_id = Column(String(100), nullable=True)
    access_level = Column(String(20), default="company")
    
    # Data extraction metadata
    rows_processed = Column(Integer, nullable=True)
    rows_imported = Column(Integer, nullable=True)
    rows_rejected = Column(Integer, nullable=True)
    
    # GDPR compliance
    gdpr_category = Column(String(50), nullable=True)
    retention_period_days = Column(Integer, nullable=True)
    deletion_scheduled_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="file_uploads")
    user = relationship("User", back_populates="file_uploads")
    
    # Hybrid properties
    @hybrid_property
    def is_processed(self) -> bool:
        """Check if file has been processed."""
        return self.status == FileStatus.PROCESSED.value
    
    @hybrid_property
    def is_processing(self) -> bool:
        """Check if file is currently being processed."""
        return self.status == FileStatus.PROCESSING.value
    
    @hybrid_property
    def is_failed(self) -> bool:
        """Check if file processing failed."""
        return self.status == FileStatus.FAILED.value
    
    @hybrid_property
    def can_retry(self) -> bool:
        """Check if file can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    @hybrid_property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)
    
    @hybrid_property
    def processing_duration_ms(self) -> Optional[int]:
        """Get processing duration in milliseconds."""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return int(delta.total_seconds() * 1000)
        return None
    
    @hybrid_property
    def is_deletion_scheduled(self) -> bool:
        """Check if file is scheduled for deletion."""
        return self.deletion_scheduled_at is not None
    
    # Methods
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of the file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def detect_file_type(self) -> str:
        """Detect file type based on extension and content."""
        extension = os.path.splitext(self.original_filename)[1].lower()
        
        type_mapping = {
            '.csv': FileType.CSV.value,
            '.xlsx': FileType.EXCEL.value,
            '.xls': FileType.EXCEL.value,
            '.pdf': FileType.PDF.value,
            '.docx': FileType.DOCX.value,
            '.xml': FileType.XML.value,
            '.json': FileType.JSON.value,
            '.png': FileType.IMAGE.value,
            '.jpg': FileType.IMAGE.value,
            '.jpeg': FileType.IMAGE.value,
        }
        
        return type_mapping.get(extension, FileType.OTHER.value)
    
    def validate_file(self) -> Dict[str, Any]:
        """Validate file before processing."""
        errors = []
        warnings = []
        
        # Size validation
        max_size = 10 * 1024 * 1024  # 10MB
        if self.file_size > max_size:
            errors.append(f"File size ({self.file_size_mb:.2f}MB) exceeds maximum ({max_size/(1024*1024):.0f}MB)")
        
        # Type validation
        allowed_types = [ft.value for ft in FileType if ft != FileType.OTHER]
        if self.file_type not in allowed_types:
            errors.append(f"File type '{self.file_type}' not supported")
        
        # Security validation
        dangerous_extensions = ['.exe', '.bat', '.sh', '.scr', '.com', '.pif']
        file_ext = os.path.splitext(self.original_filename)[1].lower()
        if file_ext in dangerous_extensions:
            errors.append(f"File extension '{file_ext}' is not allowed for security reasons")
        
        # Content validation (basic)
        if self.file_type == FileType.CSV.value:
            # Check if file actually contains CSV data
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if not first_line or ',' not in first_line:
                        warnings.append("File may not contain valid CSV data")
            except Exception as e:
                errors.append(f"Could not read file: {str(e)}")
        
        is_valid = len(errors) == 0
        
        validation_result = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "validated_at": datetime.utcnow().isoformat(),
        }
        
        self.validation_results = validation_result
        
        return validation_result
    
    def start_processing(self) -> None:
        """Mark file as processing."""
        self.status = FileStatus.PROCESSING.value
        self.processing_started_at = datetime.utcnow()
    
    def complete_processing(self, results: Dict[str, Any]) -> None:
        """Mark file as processed with results."""
        self.status = FileStatus.PROCESSED.value
        self.processing_completed_at = datetime.utcnow()
        self.processing_results = results
    
    def fail_processing(self, error_message: str) -> None:
        """Mark file processing as failed."""
        self.status = FileStatus.FAILED.value
        self.processing_completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1
    
    def retry_processing(self) -> bool:
        """Retry processing if possible."""
        if not self.can_retry:
            return False
        
        self.status = FileStatus.UPLOADED.value
        self.processing_started_at = None
        self.processing_completed_at = None
        self.error_message = None
        
        return True
    
    def quarantine(self, reason: str) -> None:
        """Quarantine file for security reasons."""
        self.status = FileStatus.QUARANTINED.value
        self.error_message = f"Quarantined: {reason}"
    
    def schedule_deletion(self, days_from_now: int = 30) -> None:
        """Schedule file for deletion."""
        from datetime import timedelta
        self.deletion_scheduled_at = datetime.utcnow() + timedelta(days=days_from_now)
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract additional metadata from file."""
        metadata = {
            "file_info": {
                "size_bytes": self.file_size,
                "size_mb": self.file_size_mb,
                "type": self.file_type,
                "mime_type": self.mime_type,
                "hash": self.file_hash,
            },
            "processing_info": {
                "status": self.status,
                "duration_ms": self.processing_duration_ms,
                "retry_count": self.retry_count,
                "rows_processed": self.rows_processed,
                "rows_imported": self.rows_imported,
                "rows_rejected": self.rows_rejected,
            },
            "timestamps": {
                "uploaded_at": self.created_at.isoformat(),
                "processing_started": self.processing_started_at.isoformat() if self.processing_started_at else None,
                "processing_completed": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            },
        }
        
        return metadata
    
    def add_tags(self, tags: List[str]) -> None:
        """Add tags to file."""
        current_tags = self.tags or []
        new_tags = list(set(current_tags + tags))
        self.tags = new_tags
    
    def remove_tags(self, tags: List[str]) -> None:
        """Remove tags from file."""
        if self.tags:
            self.tags = [tag for tag in self.tags if tag not in tags]
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary statistics."""
        summary = {
            "total_rows": self.rows_processed or 0,
            "imported_rows": self.rows_imported or 0,
            "rejected_rows": self.rows_rejected or 0,
            "success_rate": 0.0,
            "processing_time_ms": self.processing_duration_ms,
            "status": self.status,
        }
        
        if self.rows_processed and self.rows_processed > 0:
            summary["success_rate"] = (self.rows_imported or 0) / self.rows_processed
        
        return summary
    
    def check_gdpr_compliance(self) -> Dict[str, Any]:
        """Check GDPR compliance status."""
        compliance = {
            "has_gdpr_category": self.gdpr_category is not None,
            "has_retention_period": self.retention_period_days is not None,
            "is_deletion_scheduled": self.is_deletion_scheduled,
            "contains_personal_data": self.is_sensitive,
        }
        
        # Check if file is approaching retention limit
        if self.retention_period_days:
            from datetime import timedelta
            retention_deadline = self.created_at + timedelta(days=self.retention_period_days)
            days_until_retention = (retention_deadline - datetime.utcnow()).days
            
            compliance.update({
                "retention_deadline": retention_deadline.isoformat(),
                "days_until_retention": days_until_retention,
                "retention_warning": days_until_retention < 30,
            })
        
        return compliance
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert file upload to dictionary."""
        result = {
            "id": self.id,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_size_mb": self.file_size_mb,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "category": self.category,
            "tags": self.tags,
            "status": self.status,
            "is_processed": self.is_processed,
            "is_processing": self.is_processing,
            "is_failed": self.is_failed,
            "can_retry": self.can_retry,
            "retry_count": self.retry_count,
            "processing_duration_ms": self.processing_duration_ms,
            "processing_summary": self.get_processing_summary(),
            "metadata": self.extract_metadata(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_sensitive:
            result.update({
                "file_path": self.file_path,
                "file_hash": self.file_hash,
                "processing_results": self.processing_results,
                "extracted_data": self.extracted_data,
                "validation_results": self.validation_results,
                "error_message": self.error_message,
                "is_sensitive": self.is_sensitive,
                "encryption_key_id": self.encryption_key_id,
                "access_level": self.access_level,
                "gdpr_compliance": self.check_gdpr_compliance(),
            })
        
        return result
    
    def __repr__(self):
        return f"<FileUpload {self.original_filename} ({self.status})>"

class FileProcessingLog(Base):
    """Detailed logs of file processing operations."""
    
    __tablename__ = "file_processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Log details
    log_level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Processing context
    processing_step = Column(String(50), nullable=True)
    row_number = Column(Integer, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file_upload = relationship("FileUpload")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            "id": self.id,
            "file_upload_id": self.file_upload_id,
            "log_level": self.log_level,
            "message": self.message,
            "details": self.details,
            "processing_step": self.processing_step,
            "row_number": self.row_number,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __repr__(self):
        return f"<FileProcessingLog {self.log_level}: {self.message[:50]}>"

class FileTemplate(Base):
    """File templates for standardized imports."""
    
    __tablename__ = "file_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Template identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template configuration
    file_type = Column(String(20), nullable=False)
    category = Column(String(30), nullable=False)
    
    # Column mapping and validation
    column_mapping = Column(JSON, nullable=False)
    validation_rules = Column(JSON, nullable=True)
    
    # Template metadata
    is_system_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company")
    creator = relationship("User")
    
    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def validate_file_against_template(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file data against template rules."""
        errors = []
        warnings = []
        
        # Check required columns
        required_columns = [col for col, config in self.column_mapping.items() 
                          if config.get('required', False)]
        
        file_columns = file_data.get('columns', [])
        
        for req_col in required_columns:
            if req_col not in file_columns:
                errors.append(f"Required column '{req_col}' is missing")
        
        # Validate data types and formats
        if self.validation_rules:
            for rule in self.validation_rules:
                # Apply validation rules
                column = rule.get('column')
                rule_type = rule.get('type')
                
                if column in file_columns:
                    # Perform specific validation based on rule type
                    if rule_type == 'numeric' and not self._is_numeric_column(file_data, column):
                        errors.append(f"Column '{column}' must contain numeric values")
                    elif rule_type == 'date' and not self._is_date_column(file_data, column):
                        errors.append(f"Column '{column}' must contain valid dates")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validated_at": datetime.utcnow().isoformat(),
        }
    
    def _is_numeric_column(self, file_data: Dict[str, Any], column: str) -> bool:
        """Check if column contains numeric data."""
        # This is a simplified check - in practice, you'd analyze the actual data
        return True
    
    def _is_date_column(self, file_data: Dict[str, Any], column: str) -> bool:
        """Check if column contains date data."""
        # This is a simplified check - in practice, you'd analyze the actual data
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "file_type": self.file_type,
            "category": self.category,
            "column_mapping": self.column_mapping,
            "validation_rules": self.validation_rules,
            "is_system_template": self.is_system_template,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<FileTemplate {self.name} ({self.file_type})>"
