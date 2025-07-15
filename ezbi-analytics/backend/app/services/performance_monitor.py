"""
Performance Monitoring Service for EZBI Analytics
Redis-based performance tracking and optimization
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import structlog

from app.services.redis_service import redis_service
from app.core.config import settings

logger = structlog.get_logger()

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    cache_hit: bool
    user_id: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None
    cache_key: Optional[str] = None

@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_response_time_cached: float
    avg_response_time_uncached: float
    cache_savings: float
    memory_usage: str
    top_cached_endpoints: List[Dict[str, Any]]
    slow_queries: List[Dict[str, Any]]

class PerformanceMonitor:
    """Performance monitoring service with Redis storage."""
    
    def __init__(self):
        self.metrics_queue = deque(maxlen=10000)  # In-memory buffer
        self.flush_interval = 60  # Flush to Redis every minute
        self.metric_retention_days = 7
        
        # Performance thresholds
        self.slow_query_threshold = 2.0  # 2 seconds
        self.cache_hit_rate_threshold = 0.8  # 80%
        
        # Start background tasks
        self.monitoring_task = None
        self.cleanup_task = None
        
    async def start_monitoring(self):
        """Start performance monitoring tasks."""
        try:
            if not redis_service.is_connected:
                await redis_service.initialize()
            
            # Start background tasks
            self.monitoring_task = asyncio.create_task(self._metrics_flush_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("Performance monitoring started")
            
        except Exception as e:
            logger.error("Failed to start performance monitoring", error=str(e))
            raise
    
    async def stop_monitoring(self):
        """Stop performance monitoring tasks."""
        try:
            if self.monitoring_task:
                self.monitoring_task.cancel()
            
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Flush remaining metrics
            await self._flush_metrics()
            
            logger.info("Performance monitoring stopped")
            
        except Exception as e:
            logger.error("Failed to stop performance monitoring", error=str(e))
    
    async def record_request(self, metric: PerformanceMetric):
        """Record a request performance metric."""
        try:
            # Add to in-memory queue
            self.metrics_queue.append(metric)
            
            # Log slow queries immediately
            if metric.response_time > self.slow_query_threshold:
                await self._log_slow_query(metric)
            
            # Check for performance issues
            await self._check_performance_alerts(metric)
            
        except Exception as e:
            logger.error("Failed to record request metric", error=str(e))
    
    async def get_performance_stats(self, hours: int = 24) -> CachePerformanceMetrics:
        """Get performance statistics for the specified time period."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get metrics from Redis
            metrics = await self._get_metrics_from_redis(start_time, end_time)
            
            if not metrics:
                return CachePerformanceMetrics(
                    total_requests=0,
                    cache_hits=0,
                    cache_misses=0,
                    hit_rate=0.0,
                    avg_response_time_cached=0.0,
                    avg_response_time_uncached=0.0,
                    cache_savings=0.0,
                    memory_usage="0",
                    top_cached_endpoints=[],
                    slow_queries=[]
                )
            
            # Calculate statistics
            total_requests = len(metrics)
            cache_hits = sum(1 for m in metrics if m.cache_hit)
            cache_misses = total_requests - cache_hits
            hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
            
            # Calculate response times
            cached_times = [m.response_time for m in metrics if m.cache_hit]
            uncached_times = [m.response_time for m in metrics if not m.cache_hit]
            
            avg_cached = sum(cached_times) / len(cached_times) if cached_times else 0.0
            avg_uncached = sum(uncached_times) / len(uncached_times) if uncached_times else 0.0
            
            # Calculate cache savings (time saved by caching)
            cache_savings = (avg_uncached - avg_cached) * cache_hits if avg_uncached > 0 else 0.0
            
            # Get top cached endpoints
            endpoint_stats = defaultdict(lambda: {'hits': 0, 'total': 0, 'avg_time': 0.0})
            for metric in metrics:
                key = f"{metric.method} {metric.endpoint}"
                endpoint_stats[key]['total'] += 1
                endpoint_stats[key]['avg_time'] += metric.response_time
                if metric.cache_hit:
                    endpoint_stats[key]['hits'] += 1
            
            # Calculate averages and sort by cache hit rate
            top_endpoints = []
            for endpoint, stats in endpoint_stats.items():
                stats['avg_time'] /= stats['total']
                stats['hit_rate'] = stats['hits'] / stats['total']
                top_endpoints.append({
                    'endpoint': endpoint,
                    'requests': stats['total'],
                    'cache_hits': stats['hits'],
                    'hit_rate': stats['hit_rate'],
                    'avg_response_time': stats['avg_time']
                })
            
            top_endpoints.sort(key=lambda x: x['hit_rate'], reverse=True)
            
            # Get slow queries
            slow_queries = [
                {
                    'endpoint': f"{m.method} {m.endpoint}",
                    'response_time': m.response_time,
                    'timestamp': m.timestamp.isoformat(),
                    'cache_hit': m.cache_hit,
                    'status_code': m.status_code
                }
                for m in metrics
                if m.response_time > self.slow_query_threshold
            ]
            slow_queries.sort(key=lambda x: x['response_time'], reverse=True)
            
            # Get memory usage
            cache_stats = await redis_service.get_cache_stats()
            memory_usage = cache_stats.get("memory_usage", "Unknown")
            
            return CachePerformanceMetrics(
                total_requests=total_requests,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                hit_rate=hit_rate,
                avg_response_time_cached=avg_cached,
                avg_response_time_uncached=avg_uncached,
                cache_savings=cache_savings,
                memory_usage=memory_usage,
                top_cached_endpoints=top_endpoints[:10],
                slow_queries=slow_queries[:20]
            )
            
        except Exception as e:
            logger.error("Failed to get performance stats", error=str(e))
            raise
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics."""
        try:
            # Get metrics from the last 5 minutes
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)
            
            # Get from in-memory queue first
            recent_metrics = [
                m for m in self.metrics_queue
                if m.timestamp >= start_time
            ]
            
            # Also get from Redis for completeness
            redis_metrics = await self._get_metrics_from_redis(start_time, end_time)
            
            # Combine and deduplicate
            all_metrics = recent_metrics + redis_metrics
            
            if not all_metrics:
                return {
                    "requests_per_minute": 0,
                    "avg_response_time": 0.0,
                    "cache_hit_rate": 0.0,
                    "error_rate": 0.0,
                    "active_requests": 0
                }
            
            # Calculate real-time metrics
            total_requests = len(all_metrics)
            requests_per_minute = total_requests / 5  # 5-minute window
            
            avg_response_time = sum(m.response_time for m in all_metrics) / total_requests
            
            cache_hits = sum(1 for m in all_metrics if m.cache_hit)
            cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
            
            errors = sum(1 for m in all_metrics if m.status_code >= 400)
            error_rate = errors / total_requests if total_requests > 0 else 0.0
            
            return {
                "requests_per_minute": requests_per_minute,
                "avg_response_time": avg_response_time,
                "cache_hit_rate": cache_hit_rate,
                "error_rate": error_rate,
                "active_requests": len(self.metrics_queue)
            }
            
        except Exception as e:
            logger.error("Failed to get real-time metrics", error=str(e))
            return {}
    
    async def get_cache_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get cache optimization suggestions based on performance data."""
        try:
            stats = await self.get_performance_stats(hours=24)
            suggestions = []
            
            # Check cache hit rate
            if stats.hit_rate < self.cache_hit_rate_threshold:
                suggestions.append({
                    "type": "cache_hit_rate",
                    "priority": "high",
                    "message": f"Cache hit rate is {stats.hit_rate:.2%}, below threshold of {self.cache_hit_rate_threshold:.2%}",
                    "recommendations": [
                        "Increase cache TTL for frequently accessed data",
                        "Add caching for uncached endpoints",
                        "Review cache invalidation strategy"
                    ]
                })
            
            # Check slow queries
            if stats.slow_queries:
                suggestions.append({
                    "type": "slow_queries",
                    "priority": "medium",
                    "message": f"Found {len(stats.slow_queries)} slow queries (>{self.slow_query_threshold}s)",
                    "recommendations": [
                        "Add database indexes for slow queries",
                        "Implement query result caching",
                        "Consider database query optimization"
                    ],
                    "slow_queries": stats.slow_queries[:5]
                })
            
            # Check uncached endpoints
            uncached_endpoints = [
                ep for ep in stats.top_cached_endpoints
                if ep['hit_rate'] < 0.1  # Less than 10% cache hit rate
            ]
            
            if uncached_endpoints:
                suggestions.append({
                    "type": "uncached_endpoints",
                    "priority": "medium",
                    "message": f"Found {len(uncached_endpoints)} endpoints with low cache hit rates",
                    "recommendations": [
                        "Implement caching for these endpoints",
                        "Review if these endpoints should be cached",
                        "Consider increasing cache TTL"
                    ],
                    "endpoints": uncached_endpoints[:5]
                })
            
            # Check memory usage
            cache_stats = await redis_service.get_cache_stats()
            if cache_stats.get("connected"):
                memory_usage = cache_stats.get("memory_usage", "0")
                if "GB" in memory_usage and float(memory_usage.split()[0]) > 1.0:
                    suggestions.append({
                        "type": "memory_usage",
                        "priority": "low",
                        "message": f"High Redis memory usage: {memory_usage}",
                        "recommendations": [
                            "Review cache TTL settings",
                            "Consider implementing cache compression",
                            "Clean up expired cache entries"
                        ]
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error("Failed to get cache optimization suggestions", error=str(e))
            return []
    
    async def _metrics_flush_loop(self):
        """Background task to flush metrics to Redis."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in metrics flush loop", error=str(e))
                await asyncio.sleep(10)  # Wait 10 seconds before retrying
    
    async def _flush_metrics(self):
        """Flush metrics from memory to Redis."""
        try:
            if not self.metrics_queue:
                return
            
            # Convert metrics to serializable format
            metrics_data = []
            while self.metrics_queue:
                metric = self.metrics_queue.popleft()
                metrics_data.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "endpoint": metric.endpoint,
                    "method": metric.method,
                    "response_time": metric.response_time,
                    "status_code": metric.status_code,
                    "cache_hit": metric.cache_hit,
                    "user_id": metric.user_id,
                    "query_params": metric.query_params,
                    "cache_key": metric.cache_key
                })
            
            # Store in Redis with hourly partitioning
            hour_key = datetime.now().strftime("%Y-%m-%d-%H")
            cache_key = f"metrics:{hour_key}"
            
            # Get existing metrics for this hour
            existing_metrics = await redis_service.get(cache_key, 'metrics') or []
            
            # Append new metrics
            existing_metrics.extend(metrics_data)
            
            # Store back with TTL
            ttl = self.metric_retention_days * 24 * 3600
            await redis_service.set(cache_key, existing_metrics, ttl, 'metrics')
            
            logger.debug("Metrics flushed to Redis", count=len(metrics_data))
            
        except Exception as e:
            logger.error("Failed to flush metrics", error=str(e))
    
    async def _get_metrics_from_redis(self, start_time: datetime, end_time: datetime) -> List[PerformanceMetric]:
        """Get metrics from Redis for the specified time period."""
        try:
            metrics = []
            
            # Generate hour keys for the time period
            current_hour = start_time.replace(minute=0, second=0, microsecond=0)
            end_hour = end_time.replace(minute=0, second=0, microsecond=0)
            
            while current_hour <= end_hour:
                hour_key = current_hour.strftime("%Y-%m-%d-%H")
                cache_key = f"metrics:{hour_key}"
                
                # Get metrics for this hour
                hour_metrics = await redis_service.get(cache_key, 'metrics') or []
                
                # Convert back to PerformanceMetric objects
                for metric_data in hour_metrics:
                    metric_time = datetime.fromisoformat(metric_data["timestamp"])
                    
                    # Filter by time range
                    if start_time <= metric_time <= end_time:
                        metrics.append(PerformanceMetric(
                            timestamp=metric_time,
                            endpoint=metric_data["endpoint"],
                            method=metric_data["method"],
                            response_time=metric_data["response_time"],
                            status_code=metric_data["status_code"],
                            cache_hit=metric_data["cache_hit"],
                            user_id=metric_data.get("user_id"),
                            query_params=metric_data.get("query_params"),
                            cache_key=metric_data.get("cache_key")
                        ))
                
                current_hour += timedelta(hours=1)
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to get metrics from Redis", error=str(e))
            return []
    
    async def _cleanup_loop(self):
        """Background task to clean up old metrics."""
        while True:
            try:
                # Clean up once per day
                await asyncio.sleep(24 * 3600)
                await self._cleanup_old_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics from Redis."""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.metric_retention_days)
            
            # Find old metric keys
            pattern = "metrics:*"
            keys = await redis_service.redis_client.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                try:
                    # Extract date from key
                    date_part = key.decode().split(":")[-1]  # metrics:2024-01-01-14
                    key_time = datetime.strptime(date_part, "%Y-%m-%d-%H")
                    
                    if key_time < cutoff_time:
                        await redis_service.redis_client.delete(key)
                        deleted_count += 1
                        
                except Exception as e:
                    logger.warning("Failed to parse metric key", key=key, error=str(e))
                    continue
            
            logger.info("Old metrics cleaned up", deleted_keys=deleted_count)
            
        except Exception as e:
            logger.error("Failed to cleanup old metrics", error=str(e))
    
    async def _log_slow_query(self, metric: PerformanceMetric):
        """Log slow query for immediate attention."""
        logger.warning(
            "Slow query detected",
            endpoint=metric.endpoint,
            method=metric.method,
            response_time=metric.response_time,
            cache_hit=metric.cache_hit,
            user_id=metric.user_id
        )
    
    async def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check for performance alerts based on current metric."""
        try:
            # Check if this is a repeated slow query
            if metric.response_time > self.slow_query_threshold:
                await self._handle_slow_query_alert(metric)
            
            # Check error rates
            if metric.status_code >= 500:
                await self._handle_error_alert(metric)
            
        except Exception as e:
            logger.error("Failed to check performance alerts", error=str(e))
    
    async def _handle_slow_query_alert(self, metric: PerformanceMetric):
        """Handle slow query alert."""
        # This could trigger notifications, automatic scaling, etc.
        logger.warning(
            "Slow query alert",
            endpoint=metric.endpoint,
            response_time=metric.response_time,
            threshold=self.slow_query_threshold
        )
    
    async def _handle_error_alert(self, metric: PerformanceMetric):
        """Handle error alert."""
        # This could trigger notifications, automatic retries, etc.
        logger.error(
            "Error alert",
            endpoint=metric.endpoint,
            status_code=metric.status_code,
            response_time=metric.response_time
        )

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Utility functions for integration

async def record_api_performance(
    endpoint: str,
    method: str,
    response_time: float,
    status_code: int,
    cache_hit: bool,
    user_id: Optional[str] = None,
    query_params: Optional[Dict[str, Any]] = None,
    cache_key: Optional[str] = None
):
    """
    Record API performance metric.
    
    This function should be called from middleware or endpoint handlers.
    """
    metric = PerformanceMetric(
        timestamp=datetime.now(),
        endpoint=endpoint,
        method=method,
        response_time=response_time,
        status_code=status_code,
        cache_hit=cache_hit,
        user_id=user_id,
        query_params=query_params,
        cache_key=cache_key
    )
    
    await performance_monitor.record_request(metric)

async def get_performance_dashboard_data() -> Dict[str, Any]:
    """
    Get performance dashboard data.
    
    Returns comprehensive performance metrics for dashboard display.
    """
    try:
        # Get performance stats for different time periods
        stats_24h = await performance_monitor.get_performance_stats(hours=24)
        stats_7d = await performance_monitor.get_performance_stats(hours=24 * 7)
        real_time = await performance_monitor.get_real_time_metrics()
        suggestions = await performance_monitor.get_cache_optimization_suggestions()
        
        return {
            "real_time": real_time,
            "last_24h": asdict(stats_24h),
            "last_7d": asdict(stats_7d),
            "optimization_suggestions": suggestions,
            "monitoring_status": "active" if performance_monitor.monitoring_task else "inactive"
        }
        
    except Exception as e:
        logger.error("Failed to get performance dashboard data", error=str(e))
        return {"error": str(e)}

# Initialization function
async def initialize_performance_monitoring():
    """Initialize performance monitoring service."""
    try:
        await performance_monitor.start_monitoring()
        logger.info("Performance monitoring initialized")
    except Exception as e:
        logger.error("Failed to initialize performance monitoring", error=str(e))
        raise

# Cleanup function
async def cleanup_performance_monitoring():
    """Cleanup performance monitoring service."""
    try:
        await performance_monitor.stop_monitoring()
        logger.info("Performance monitoring cleaned up")
    except Exception as e:
        logger.error("Failed to cleanup performance monitoring", error=str(e))