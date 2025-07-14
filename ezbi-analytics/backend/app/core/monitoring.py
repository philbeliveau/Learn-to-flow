from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST as OPENMETRICS_CONTENT_TYPE
import time
import psutil
import structlog

from app.core.config import settings
from app.core.database import ConnectionPoolMonitor

logger = structlog.get_logger()

# Prometheus metrics
request_count = Counter(
    'ezbi_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'user_id', 'company_id']
)

request_duration = Histogram(
    'ezbi_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)

active_connections = Gauge(
    'ezbi_active_connections',
    'Number of active database connections'
)

active_users = Gauge(
    'ezbi_active_users',
    'Number of active users'
)

ml_predictions_total = Counter(
    'ezbi_ml_predictions_total',
    'Total ML predictions generated',
    ['model_type', 'prediction_type', 'user_id', 'company_id']
)

ml_prediction_duration = Histogram(
    'ezbi_ml_prediction_duration_seconds',
    'ML prediction generation duration in seconds',
    ['model_type', 'prediction_type']
)

ml_model_accuracy = Gauge(
    'ezbi_ml_model_accuracy',
    'ML model accuracy score',
    ['model_type', 'company_id']
)

file_uploads_total = Counter(
    'ezbi_file_uploads_total',
    'Total file uploads',
    ['file_type', 'status', 'user_id', 'company_id']
)

file_processing_duration = Histogram(
    'ezbi_file_processing_duration_seconds',
    'File processing duration in seconds',
    ['file_type', 'status']
)

integration_sync_total = Counter(
    'ezbi_integration_sync_total',
    'Total integration synchronizations',
    ['integration_type', 'provider', 'status', 'company_id']
)

integration_sync_duration = Histogram(
    'ezbi_integration_sync_duration_seconds',
    'Integration sync duration in seconds',
    ['integration_type', 'provider', 'status']
)

user_sessions_active = Gauge(
    'ezbi_user_sessions_active',
    'Number of active user sessions'
)

api_rate_limit_exceeded = Counter(
    'ezbi_api_rate_limit_exceeded_total',
    'Total API rate limit exceeded events',
    ['endpoint', 'user_id', 'company_id']
)

security_events_total = Counter(
    'ezbi_security_events_total',
    'Total security events',
    ['event_type', 'severity', 'user_id', 'company_id']
)

system_cpu_usage = Gauge(
    'ezbi_system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'ezbi_system_memory_usage_percent',
    'System memory usage percentage'
)

system_disk_usage = Gauge(
    'ezbi_system_disk_usage_percent',
    'System disk usage percentage'
)

class MetricsCollector:
    """Metrics collection and monitoring."""
    
    def __init__(self):
        self.start_time = time.time()
        self.system_metrics = SystemMetrics()
        self.app_metrics = ApplicationMetrics()
        self.business_metrics = BusinessMetrics()
    
    def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            system_disk_usage.set(disk.percent)
            
            # Database connection pool
            pool_status = ConnectionPoolMonitor.get_pool_status()
            active_connections.set(pool_status.get('checked_out', 0))
            
            logger.debug(
                "System metrics collected",
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                db_connections=pool_status.get('checked_out', 0),
            )
            
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
    
    def record_http_request(self, method: str, endpoint: str, status_code: int,
                           duration: float, user_id: str = None, company_id: str = None):
        """Record HTTP request metrics."""
        request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            user_id=user_id or "anonymous",
            company_id=company_id or "none"
        ).inc()
        
        request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).observe(duration)
    
    def record_ml_prediction(self, model_type: str, prediction_type: str,
                           duration: float, accuracy: float = None,
                           user_id: str = None, company_id: str = None):
        """Record ML prediction metrics."""
        ml_predictions_total.labels(
            model_type=model_type,
            prediction_type=prediction_type,
            user_id=user_id or "none",
            company_id=company_id or "none"
        ).inc()
        
        ml_prediction_duration.labels(
            model_type=model_type,
            prediction_type=prediction_type
        ).observe(duration)
        
        if accuracy is not None:
            ml_model_accuracy.labels(
                model_type=model_type,
                company_id=company_id or "none"
            ).set(accuracy)
    
    def record_file_upload(self, file_type: str, status: str, duration: float,
                          user_id: str = None, company_id: str = None):
        """Record file upload metrics."""
        file_uploads_total.labels(
            file_type=file_type,
            status=status,
            user_id=user_id or "none",
            company_id=company_id or "none"
        ).inc()
        
        file_processing_duration.labels(
            file_type=file_type,
            status=status
        ).observe(duration)
    
    def record_integration_sync(self, integration_type: str, provider: str,
                              status: str, duration: float, company_id: str = None):
        """Record integration sync metrics."""
        integration_sync_total.labels(
            integration_type=integration_type,
            provider=provider,
            status=status,
            company_id=company_id or "none"
        ).inc()
        
        integration_sync_duration.labels(
            integration_type=integration_type,
            provider=provider,
            status=status
        ).observe(duration)
    
    def record_security_event(self, event_type: str, severity: str,
                            user_id: str = None, company_id: str = None):
        """Record security event metrics."""
        security_events_total.labels(
            event_type=event_type,
            severity=severity,
            user_id=user_id or "none",
            company_id=company_id or "none"
        ).inc()
    
    def record_rate_limit_exceeded(self, endpoint: str, user_id: str = None,
                                  company_id: str = None):
        """Record rate limit exceeded events."""
        api_rate_limit_exceeded.labels(
            endpoint=endpoint,
            user_id=user_id or "none",
            company_id=company_id or "none"
        ).inc()
    
    def update_active_users(self, count: int):
        """Update active users count."""
        active_users.set(count)
    
    def update_active_sessions(self, count: int):
        """Update active sessions count."""
        user_sessions_active.set(count)

class SystemMetrics:
    """System-level metrics monitoring."""
    
    def __init__(self):
        self.last_collection = None
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information and usage."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information and usage."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percent": swap.percent,
            },
        }
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information and usage."""
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            "usage": {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": disk_usage.percent,
            },
            "io": {
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
            } if disk_io else None,
        }
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information and usage."""
        net_io = psutil.net_io_counters()
        
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
        } if net_io else None
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get current process information."""
        process = psutil.Process()
        
        return {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_info": process.memory_info()._asdict(),
            "num_threads": process.num_threads(),
            "create_time": process.create_time(),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all system metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
            "process": self.get_process_info(),
        }

class ApplicationMetrics:
    """Application-level metrics monitoring."""
    
    def __init__(self):
        self.request_history = []
        self.error_history = []
    
    def get_request_metrics(self) -> Dict[str, Any]:
        """Get request-related metrics."""
        # This would typically be stored in a time-series database
        # For now, we'll return some basic metrics
        return {
            "total_requests": len(self.request_history),
            "error_rate": len(self.error_history) / len(self.request_history) if self.request_history else 0,
            "avg_response_time": sum(r.get('duration', 0) for r in self.request_history) / len(self.request_history) if self.request_history else 0,
        }
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database-related metrics."""
        pool_status = ConnectionPoolMonitor.get_pool_status()
        return {
            "connection_pool": pool_status,
            "active_connections": pool_status.get('checked_out', 0),
            "pool_size": pool_status.get('pool_size', 0),
            "overflow": pool_status.get('overflow', 0),
        }
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache-related metrics."""
        # This would integrate with Redis or other cache systems
        return {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": 0,
        }
    
    def get_ml_metrics(self) -> Dict[str, Any]:
        """Get ML-related metrics."""
        # This would track ML model performance
        return {
            "predictions_generated": 0,
            "avg_prediction_time": 0,
            "model_accuracy": 0,
        }
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record a request for metrics."""
        request_info = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.request_history.append(request_info)
        
        # Keep only last 1000 requests
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
        
        # Record errors
        if status_code >= 400:
            self.error_history.append(request_info)
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]

class BusinessMetrics:
    """Business-level metrics monitoring."""
    
    def __init__(self):
        pass
    
    def get_user_metrics(self) -> Dict[str, Any]:
        """Get user-related metrics."""
        # This would query the database for user metrics
        return {
            "total_users": 0,
            "active_users_daily": 0,
            "active_users_weekly": 0,
            "active_users_monthly": 0,
            "new_registrations_today": 0,
        }
    
    def get_company_metrics(self) -> Dict[str, Any]:
        """Get company-related metrics."""
        return {
            "total_companies": 0,
            "active_companies": 0,
            "subscription_tiers": {},
            "trial_companies": 0,
        }
    
    def get_prediction_metrics(self) -> Dict[str, Any]:
        """Get prediction-related metrics."""
        return {
            "predictions_generated_today": 0,
            "predictions_generated_week": 0,
            "predictions_generated_month": 0,
            "avg_prediction_accuracy": 0,
            "most_used_models": [],
        }
    
    def get_revenue_metrics(self) -> Dict[str, Any]:
        """Get revenue-related metrics."""
        return {
            "monthly_recurring_revenue": 0,
            "annual_recurring_revenue": 0,
            "churn_rate": 0,
            "customer_lifetime_value": 0,
        }

class HealthChecker:
    """System health checking."""
    
    def __init__(self):
        self.system_metrics = SystemMetrics()
        self.app_metrics = ApplicationMetrics()
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            from app.core.database import check_db_health
            is_healthy = await check_db_health()
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": 0,  # Would measure actual response time
                "connection_pool": ConnectionPoolMonitor.get_pool_status(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None,
            }
    
    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            # This would check Redis connectivity
            return {
                "status": "healthy",
                "response_time_ms": 0,
                "memory_usage": 0,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space."""
        disk_usage = psutil.disk_usage('/')
        usage_percent = disk_usage.percent
        
        status = "healthy"
        if usage_percent > 90:
            status = "critical"
        elif usage_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "usage_percent": usage_percent,
            "free_bytes": disk_usage.free,
            "total_bytes": disk_usage.total,
        }
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        status = "healthy"
        if usage_percent > 90:
            status = "critical"
        elif usage_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "usage_percent": usage_percent,
            "available_bytes": memory.available,
            "total_bytes": memory.total,
        }
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        checks = {
            "database": await self.check_database_health(),
            "redis": self.check_redis_health(),
            "disk": self.check_disk_space(),
            "memory": self.check_memory_usage(),
        }
        
        # Determine overall status
        overall_status = "healthy"
        for check_name, check_result in checks.items():
            if check_result.get("status") == "critical":
                overall_status = "critical"
                break
            elif check_result.get("status") == "unhealthy":
                overall_status = "unhealthy"
            elif check_result.get("status") == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        }

# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()

# Middleware for automatic metrics collection
class MetricsMiddleware:
    """Middleware to automatically collect metrics."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract user info if available
        user_id = None
        company_id = None
        
        try:
            # This would extract user info from token or session
            pass
        except:
            pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        metrics_collector.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
            user_id=str(user_id) if user_id else None,
            company_id=str(company_id) if company_id else None,
        )
        
        return response

def setup_monitoring(app: FastAPI):
    """Setup monitoring for the FastAPI application."""
    
    # Add metrics middleware
    app.middleware("http")(MetricsMiddleware(app))
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        # Collect current system metrics
        metrics_collector.collect_system_metrics()
        
        # Generate Prometheus metrics
        metrics_data = generate_latest()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST,
        )
    
    # Add health check endpoint
    @app.get("/health/detailed")
    async def get_detailed_health():
        """Detailed health check endpoint."""
        return await health_checker.get_overall_health()
    
    logger.info("Monitoring setup completed")

# Utility functions
def record_custom_metric(metric_name: str, value: float, labels: Dict[str, str] = None):
    """Record a custom metric."""
    # This would record custom metrics
    logger.info("Custom metric recorded", metric=metric_name, value=value, labels=labels)

def start_background_metrics_collection():
    """Start background metrics collection."""
    import asyncio
    
    async def collect_metrics():
        while True:
            try:
                metrics_collector.collect_system_metrics()
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error("Error in background metrics collection", error=str(e))
                await asyncio.sleep(60)
    
    # Start the background task
    asyncio.create_task(collect_metrics())
    logger.info("Background metrics collection started")
