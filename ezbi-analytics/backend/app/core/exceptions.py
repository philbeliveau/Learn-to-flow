from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Any, Dict, Optional
from datetime import datetime
import structlog
import traceback

logger = structlog.get_logger()

class EZBIException(Exception):
    """Base exception class for EZBI Analytics."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(self.message)

class ValidationException(EZBIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {},
            error_code="VALIDATION_ERROR"
        )
        self.field = field

class AuthenticationException(EZBIException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationException(EZBIException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )

class NotFoundException(EZBIException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )

class ConflictException(EZBIException):
    """Exception for conflict errors."""
    
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT"
        )
        self.resource = resource

class RateLimitException(EZBIException):
    """Exception for rate limit exceeded errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )
        self.retry_after = retry_after

class ServiceUnavailableException(EZBIException):
    """Exception for service unavailable errors."""
    
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE"
        )

class FileProcessingException(EZBIException):
    """Exception for file processing errors."""
    
    def __init__(self, message: str, file_name: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {},
            error_code="FILE_PROCESSING_ERROR"
        )
        self.file_name = file_name

class MLModelException(EZBIException):
    """Exception for ML model errors."""
    
    def __init__(self, message: str, model_type: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {},
            error_code="ML_MODEL_ERROR"
        )
        self.model_type = model_type

class IntegrationException(EZBIException):
    """Exception for integration errors."""
    
    def __init__(self, message: str, integration_name: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details or {},
            error_code="INTEGRATION_ERROR"
        )
        self.integration_name = integration_name

class DataValidationException(EZBIException):
    """Exception for data validation errors."""
    
    def __init__(self, message: str, validation_errors: list = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"validation_errors": validation_errors or []},
            error_code="DATA_VALIDATION_ERROR"
        )
        self.validation_errors = validation_errors or []

class BusinessLogicException(EZBIException):
    """Exception for business logic errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {},
            error_code="BUSINESS_LOGIC_ERROR"
        )

class HTTPExceptionHandler:
    """HTTP exception handlers for the application."""
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path,
                    "method": request.method,
                }
            },
        )
    
    @staticmethod
    async def ezbi_exception_handler(request: Request, exc: EZBIException) -> JSONResponse:
        """Handle EZBI custom exceptions."""
        logger.error(
            "EZBI exception occurred",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "status_code": exc.status_code,
                    "details": exc.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path,
                    "method": request.method,
                }
            },
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation exceptions."""
        logger.warning(
            "Validation exception occurred",
            errors=exc.errors(),
            path=request.url.path,
            method=request.method,
        )
        
        # Format validation errors
        formatted_errors = []
        for error in exc.errors():
            formatted_errors.append({
                "field": ".".join(str(x) for x in error["loc"][1:]),  # Skip 'body' prefix
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input"),
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "details": {
                        "validation_errors": formatted_errors
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path,
                    "method": request.method,
                }
            },
        )
    
    @staticmethod
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        """Handle database integrity errors."""
        logger.error(
            "Database integrity error",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        
        # Try to extract meaningful error message
        error_message = "Database constraint violation"
        if "duplicate key" in str(exc).lower():
            error_message = "Resource already exists"
        elif "foreign key" in str(exc).lower():
            error_message = "Referenced resource not found"
        elif "not null" in str(exc).lower():
            error_message = "Required field is missing"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "DATABASE_INTEGRITY_ERROR",
                    "message": error_message,
                    "status_code": status.HTTP_409_CONFLICT,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path,
                    "method": request.method,
                }
            },
        )
    
    @staticmethod
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle SQLAlchemy errors."""
        logger.error(
            "SQLAlchemy error",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Database operation failed",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path,
                    "method": request.method,
                }
            },
        )
    
    @staticmethod
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle generic exceptions."""
        logger.error(
            "Unhandled exception occurred",
            error=str(exc),
            error_type=type(exc).__name__,
            traceback=traceback.format_exc(),
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path,
                    "method": request.method,
                }
            },
        )

# Exception handling utilities
class ExceptionManager:
    """Utility class for exception management."""
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str) -> EZBIException:
        """Convert database errors to appropriate EZBI exceptions."""
        if isinstance(error, IntegrityError):
            return ConflictException(f"Database constraint violation during {operation}")
        elif isinstance(error, SQLAlchemyError):
            return EZBIException(f"Database error during {operation}")
        else:
            return EZBIException(f"Unexpected error during {operation}")
    
    @staticmethod
    def handle_validation_error(errors: list, context: str = None) -> ValidationException:
        """Convert validation errors to ValidationException."""
        message = "Validation failed"
        if context:
            message = f"Validation failed for {context}"
        
        return ValidationException(
            message=message,
            details={"validation_errors": errors}
        )
    
    @staticmethod
    def handle_file_error(error: Exception, file_name: str = None) -> FileProcessingException:
        """Convert file processing errors to FileProcessingException."""
        message = f"File processing failed: {str(error)}"
        
        return FileProcessingException(
            message=message,
            file_name=file_name,
            details={"original_error": str(error)}
        )
    
    @staticmethod
    def handle_ml_error(error: Exception, model_type: str = None) -> MLModelException:
        """Convert ML model errors to MLModelException."""
        message = f"ML model operation failed: {str(error)}"
        
        return MLModelException(
            message=message,
            model_type=model_type,
            details={"original_error": str(error)}
        )
    
    @staticmethod
    def handle_integration_error(error: Exception, integration_name: str = None) -> IntegrationException:
        """Convert integration errors to IntegrationException."""
        message = f"Integration operation failed: {str(error)}"
        
        return IntegrationException(
            message=message,
            integration_name=integration_name,
            details={"original_error": str(error)}
        )

# Decorator for exception handling
def handle_exceptions(operation: str = None):
    """Decorator to handle exceptions in API endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except EZBIException:
                raise  # Re-raise EZBI exceptions as-is
            except IntegrityError as e:
                raise ExceptionManager.handle_database_error(e, operation or func.__name__)
            except SQLAlchemyError as e:
                raise ExceptionManager.handle_database_error(e, operation or func.__name__)
            except Exception as e:
                logger.error(
                    f"Unhandled exception in {operation or func.__name__}",
                    error=str(e),
                    error_type=type(e).__name__,
                    traceback=traceback.format_exc(),
                )
                raise EZBIException(f"Operation failed: {operation or func.__name__}")
        
        return wrapper
    return decorator

# Context manager for exception handling
class ExceptionContext:
    """Context manager for exception handling."""
    
    def __init__(self, operation: str, logger=None):
        self.operation = operation
        self.logger = logger or globals()["logger"]
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Exception in {self.operation}",
                error=str(exc_val),
                error_type=exc_type.__name__,
                traceback=traceback.format_exc(),
            )
        return False  # Don't suppress exceptions

# Helper functions for common exception patterns
def require_resource(resource, identifier: str = None, resource_type: str = "Resource"):
    """Raise NotFoundException if resource is None."""
    if resource is None:
        raise NotFoundException(resource_type, identifier)
    return resource

def require_permission(condition: bool, message: str = None):
    """Raise AuthorizationException if condition is False."""
    if not condition:
        raise AuthorizationException(message)

def require_authentication(user):
    """Raise AuthenticationException if user is None or not authenticated."""
    if user is None:
        raise AuthenticationException("User not authenticated")
    return user

def validate_business_rule(condition: bool, message: str):
    """Raise BusinessLogicException if business rule is violated."""
    if not condition:
        raise BusinessLogicException(message)

def validate_data(data, schema, context: str = None):
    """Validate data against schema and raise ValidationException if invalid."""
    # This would integrate with your validation library
    # For now, it's a placeholder
    if not data:
        raise ValidationException(f"Data validation failed for {context}")
    return data
