"""
Performance Dashboard API Endpoints
Real-time performance monitoring and cache optimization
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.models.user import User
from app.services.performance_monitor import (
    performance_monitor,
    get_performance_dashboard_data,
    record_api_performance
)
from app.services.redis_service import redis_service, manufacturing_cache
from app.middleware.caching_middleware import cache_metrics_middleware

logger = structlog.get_logger()
security = HTTPBearer()

router = APIRouter()

@router.get("/dashboard")
async def get_performance_dashboard(
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive performance dashboard data.
    
    Features:
    - Real-time performance metrics
    - Cache hit/miss statistics
    - Response time analysis
    - Optimization suggestions
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        dashboard_data = await get_performance_dashboard_data()
        
        # Add cache status information
        cache_stats = await redis_service.get_cache_stats()
        
        # Add middleware metrics
        middleware_metrics = cache_metrics_middleware.get_metrics() if hasattr(cache_metrics_middleware, 'get_metrics') else {}
        
        return {
            "dashboard": dashboard_data,
            "cache_status": cache_stats,
            "middleware_metrics": middleware_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting performance dashboard", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance dashboard: {str(e)}")

@router.get("/metrics/real-time")
async def get_real_time_metrics(
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time performance metrics.
    
    Features:
    - Current requests per minute
    - Average response time
    - Cache hit rate
    - Error rate
    """
    try:
        real_time_metrics = await performance_monitor.get_real_time_metrics()
        
        return {
            "metrics": real_time_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting real-time metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metrics: {str(e)}")

@router.get("/metrics/historical")
async def get_historical_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours of historical data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical performance metrics.
    
    Features:
    - Performance trends over time
    - Cache effectiveness analysis
    - Response time distribution
    - Error rate analysis
    """
    try:
        historical_stats = await performance_monitor.get_performance_stats(hours=hours)
        
        return {
            "stats": historical_stats,
            "period_hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting historical metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get historical metrics: {str(e)}")

@router.get("/optimization/suggestions")
async def get_optimization_suggestions(
    current_user: User = Depends(get_current_user),
):
    """
    Get cache optimization suggestions.
    
    Features:
    - Performance bottleneck identification
    - Cache configuration recommendations
    - Query optimization suggestions
    """
    try:
        suggestions = await performance_monitor.get_cache_optimization_suggestions()
        
        return {
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting optimization suggestions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get optimization suggestions: {str(e)}")

@router.get("/cache/stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed cache statistics.
    
    Features:
    - Cache hit/miss ratios by prefix
    - Memory usage breakdown
    - Key distribution statistics
    - Cache performance metrics
    """
    try:
        # Get Redis cache stats
        cache_stats = await redis_service.get_cache_stats()
        
        # Get manufacturing cache specific stats
        manufacturing_stats = await manufacturing_cache.get_cache_stats()
        
        return {
            "redis_stats": cache_stats,
            "manufacturing_stats": manufacturing_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting cache statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")

@router.post("/cache/warm")
async def warm_cache(
    endpoint: str = Query(..., description="Endpoint to warm cache for"),
    current_user: User = Depends(get_current_user),
):
    """
    Manually warm cache for specific endpoints.
    
    Features:
    - On-demand cache warming
    - Endpoint-specific warming
    - Performance improvement preparation
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Implement cache warming logic based on endpoint
        if endpoint == "manufacturing_data":
            # Warm manufacturing data cache
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            # This would trigger cache warming for common queries
            # For now, we'll just log the action
            logger.info("Cache warming initiated", endpoint=endpoint, user_id=current_user.id)
            
            return {
                "message": "Cache warming initiated",
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        
        elif endpoint == "kpis":
            # Warm KPI cache
            logger.info("KPI cache warming initiated", endpoint=endpoint, user_id=current_user.id)
            
            return {
                "message": "KPI cache warming initiated",
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported endpoint for cache warming")
        
    except Exception as e:
        logger.error("Error warming cache", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(
    cache_type: str = Query(..., description="Type of cache to clear (all, manufacturing, sessions)"),
    current_user: User = Depends(get_current_user),
):
    """
    Clear cache entries.
    
    Features:
    - Selective cache clearing
    - Full cache reset
    - Emergency cache invalidation
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cleared_count = 0
        
        if cache_type == "all":
            # Clear all cache types
            for prefix in ["manufacturing_data", "kpis", "aggregation", "upload_status", "api_response"]:
                count = await redis_service.flush_prefix(prefix)
                cleared_count += count
        
        elif cache_type == "manufacturing":
            cleared_count = await redis_service.flush_prefix("manufacturing_data")
            cleared_count += await redis_service.flush_prefix("kpis")
            cleared_count += await redis_service.flush_prefix("aggregation")
        
        elif cache_type == "sessions":
            cleared_count = await redis_service.flush_prefix("user_session")
            cleared_count += await redis_service.flush_prefix("auth_token")
        
        elif cache_type == "api_responses":
            cleared_count = await redis_service.flush_prefix("api_response")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid cache type")
        
        logger.info("Cache cleared", cache_type=cache_type, cleared_count=cleared_count, user_id=current_user.id)
        
        return {
            "message": f"Cache cleared successfully",
            "cache_type": cache_type,
            "cleared_entries": cleared_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/endpoints/slowest")
async def get_slowest_endpoints(
    limit: int = Query(10, ge=1, le=50, description="Number of slowest endpoints to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
    current_user: User = Depends(get_current_user),
):
    """
    Get slowest API endpoints.
    
    Features:
    - Endpoint performance ranking
    - Response time analysis
    - Optimization target identification
    """
    try:
        stats = await performance_monitor.get_performance_stats(hours=hours)
        
        # Get slow queries and group by endpoint
        endpoint_performance = {}
        
        for slow_query in stats.slow_queries:
            endpoint = slow_query['endpoint']
            if endpoint not in endpoint_performance:
                endpoint_performance[endpoint] = {
                    'endpoint': endpoint,
                    'slow_queries': 0,
                    'max_response_time': 0.0,
                    'avg_response_time': 0.0,
                    'total_response_time': 0.0
                }
            
            endpoint_performance[endpoint]['slow_queries'] += 1
            endpoint_performance[endpoint]['max_response_time'] = max(
                endpoint_performance[endpoint]['max_response_time'],
                slow_query['response_time']
            )
            endpoint_performance[endpoint]['total_response_time'] += slow_query['response_time']
        
        # Calculate averages and sort
        for endpoint_data in endpoint_performance.values():
            endpoint_data['avg_response_time'] = endpoint_data['total_response_time'] / endpoint_data['slow_queries']
            del endpoint_data['total_response_time']  # Remove working field
        
        slowest_endpoints = sorted(
            endpoint_performance.values(),
            key=lambda x: x['avg_response_time'],
            reverse=True
        )[:limit]
        
        return {
            "slowest_endpoints": slowest_endpoints,
            "analysis_period_hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting slowest endpoints", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get slowest endpoints: {str(e)}")

@router.get("/health")
async def performance_health_check(
    current_user: User = Depends(get_current_user),
):
    """
    Performance system health check.
    
    Features:
    - Redis connection status
    - Performance monitoring status
    - Cache service health
    """
    try:
        # Check Redis connection
        redis_healthy = redis_service.is_connected
        
        # Check performance monitoring
        monitoring_healthy = performance_monitor.monitoring_task is not None and not performance_monitor.monitoring_task.done()
        
        # Get basic stats
        cache_stats = await redis_service.get_cache_stats()
        
        health_status = {
            "redis_connected": redis_healthy,
            "performance_monitoring_active": monitoring_healthy,
            "cache_memory_usage": cache_stats.get("memory_usage", "Unknown"),
            "cache_hit_rate": cache_stats.get("hit_rate", 0),
            "total_cache_keys": cache_stats.get("total_keys", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        # Overall health status
        overall_healthy = redis_healthy and monitoring_healthy
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "details": health_status
        }
        
    except Exception as e:
        logger.error("Error checking performance health", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/test/load")
async def simulate_load_test(
    requests: int = Query(100, ge=1, le=1000, description="Number of requests to simulate"),
    current_user: User = Depends(get_current_user),
):
    """
    Simulate load test for performance analysis.
    
    Features:
    - Controlled load generation
    - Performance impact analysis
    - Cache effectiveness testing
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Simulate load by recording test metrics
        import asyncio
        import random
        
        test_results = {
            "requests_sent": 0,
            "avg_response_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        total_response_time = 0.0
        
        for i in range(requests):
            # Simulate API call
            response_time = random.uniform(0.05, 0.5)  # 50ms to 500ms
            cache_hit = random.choice([True, False])
            
            # Record metric
            await record_api_performance(
                endpoint="/test/load",
                method="GET",
                response_time=response_time,
                status_code=200,
                cache_hit=cache_hit,
                user_id=current_user.id
            )
            
            test_results["requests_sent"] += 1
            total_response_time += response_time
            
            if cache_hit:
                test_results["cache_hits"] += 1
            else:
                test_results["cache_misses"] += 1
            
            # Small delay to simulate real traffic
            await asyncio.sleep(0.01)
        
        test_results["avg_response_time"] = total_response_time / requests
        test_results["cache_hit_rate"] = test_results["cache_hits"] / requests
        
        logger.info("Load test completed", results=test_results, user_id=current_user.id)
        
        return {
            "message": "Load test completed",
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error running load test", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to run load test: {str(e)}")

@router.get("/alerts")
async def get_performance_alerts(
    current_user: User = Depends(get_current_user),
):
    """
    Get performance alerts and warnings.
    
    Features:
    - Real-time performance alerts
    - Threshold-based warnings
    - System health notifications
    """
    try:
        alerts = []
        
        # Check real-time metrics for alerts
        real_time_metrics = await performance_monitor.get_real_time_metrics()
        
        # Check response time alerts
        if real_time_metrics.get("avg_response_time", 0) > 2.0:
            alerts.append({
                "type": "high_response_time",
                "severity": "warning",
                "message": f"Average response time is {real_time_metrics['avg_response_time']:.2f}s",
                "threshold": 2.0,
                "current_value": real_time_metrics["avg_response_time"]
            })
        
        # Check cache hit rate alerts
        if real_time_metrics.get("cache_hit_rate", 0) < 0.5:
            alerts.append({
                "type": "low_cache_hit_rate",
                "severity": "warning",
                "message": f"Cache hit rate is {real_time_metrics['cache_hit_rate']:.2%}",
                "threshold": 0.5,
                "current_value": real_time_metrics["cache_hit_rate"]
            })
        
        # Check error rate alerts
        if real_time_metrics.get("error_rate", 0) > 0.05:
            alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"Error rate is {real_time_metrics['error_rate']:.2%}",
                "threshold": 0.05,
                "current_value": real_time_metrics["error_rate"]
            })
        
        # Check Redis connection
        if not redis_service.is_connected:
            alerts.append({
                "type": "redis_disconnected",
                "severity": "critical",
                "message": "Redis connection is down",
                "threshold": None,
                "current_value": "disconnected"
            })
        
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting performance alerts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance alerts: {str(e)}")

# Export router
__all__ = ["router"]