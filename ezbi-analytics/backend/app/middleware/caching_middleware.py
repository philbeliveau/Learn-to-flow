"""
Caching Middleware for EZBI Analytics API
Automatic response caching with intelligent cache invalidation
"""

import json
import time
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import structlog

from app.services.redis_service import redis_service, manufacturing_cache, rate_limit_cache

logger = structlog.get_logger()

class CachingMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic API response caching."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Cacheable endpoints with custom TTL
        self.cacheable_endpoints = {
            '/api/v1/data/manufacturing': {
                'ttl': 1800,  # 30 minutes
                'vary_on': ['machine_id', 'start_date', 'end_date', 'limit']
            },
            '/api/v1/data/kpis': {
                'ttl': 900,   # 15 minutes
                'vary_on': ['period']
            },
            '/api/v1/data/uploads': {
                'ttl': 300,   # 5 minutes
                'vary_on': ['status', 'limit']
            },
            '/api/v1/predictions': {
                'ttl': 3600,  # 1 hour
                'vary_on': ['company_id', 'period']
            },
            '/api/v1/health': {
                'ttl': 60,    # 1 minute
                'vary_on': []
            }
        }
        
        # Endpoints that should invalidate cache
        self.cache_invalidating_endpoints = {
            '/api/v1/data/upload': ['manufacturing_data', 'kpis'],
            '/api/v1/auth/logout': ['user_session', 'auth_token'],
        }
        
        # Rate-limited endpoints
        self.rate_limited_endpoints = {
            '/api/v1/data/upload': {'limit': 10, 'window': 300},  # 10 uploads per 5 minutes
            '/api/v1/auth/login': {'limit': 5, 'window': 300},    # 5 login attempts per 5 minutes
            '/api/v1/predictions': {'limit': 100, 'window': 3600}, # 100 predictions per hour
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with caching and rate limiting."""
        start_time = time.time()
        
        # Check if Redis is available
        if not redis_service.is_connected:
            try:
                await redis_service.initialize()
            except Exception as e:
                logger.warning("Redis initialization failed, proceeding without cache", error=str(e))
        
        # Apply rate limiting
        if redis_service.is_connected:
            rate_limit_result = await self._check_rate_limit(request)
            if not rate_limit_result['allowed']:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests",
                        "retry_after": rate_limit_result['reset_in']
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limit_result['limit']),
                        "X-RateLimit-Remaining": str(max(0, rate_limit_result['limit'] - rate_limit_result['current'])),
                        "X-RateLimit-Reset": str(rate_limit_result['reset_in']),
                        "Retry-After": str(rate_limit_result['reset_in'])
                    }
                )
        
        # Check if endpoint is cacheable
        if request.method == "GET" and self._is_cacheable(request):
            cached_response = await self._get_cached_response(request)
            if cached_response:
                # Add cache headers
                cache_headers = {
                    "X-Cache": "HIT",
                    "X-Cache-TTL": str(await redis_service.get_ttl(self._generate_cache_key(request))),
                    "X-Process-Time": str(time.time() - start_time)
                }
                
                # Create response with cache headers
                response = JSONResponse(
                    content=cached_response,
                    headers=cache_headers
                )
                
                logger.info("Cache hit", path=request.url.path, processing_time=time.time() - start_time)
                return response
        
        # Process request
        response = await call_next(request)
        
        # Cache response if applicable
        if (request.method == "GET" and 
            self._is_cacheable(request) and 
            response.status_code == 200 and
            redis_service.is_connected):
            
            await self._cache_response(request, response)
        
        # Invalidate cache if needed
        if (request.method in ["POST", "PUT", "DELETE"] and 
            self._should_invalidate_cache(request) and
            redis_service.is_connected):
            
            await self._invalidate_cache(request)
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(time.time() - start_time)
        response.headers["X-Cache"] = "MISS"
        
        return response
    
    def _is_cacheable(self, request: Request) -> bool:
        """Check if request is cacheable."""
        return request.url.path in self.cacheable_endpoints
    
    def _should_invalidate_cache(self, request: Request) -> bool:
        """Check if request should invalidate cache."""
        return request.url.path in self.cache_invalidating_endpoints
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        path = request.url.path
        
        # Get cache configuration
        cache_config = self.cacheable_endpoints.get(path, {})
        vary_on = cache_config.get('vary_on', [])
        
        # Build key components
        key_parts = [path]
        
        # Add query parameters that affect caching
        for param in vary_on:
            value = request.query_params.get(param)
            if value:
                key_parts.append(f"{param}={value}")
        
        # Add user context if authenticated
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            key_parts.append(f"user={user_id}")
        
        # Generate hash
        cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
        return cache_key
    
    async def _get_cached_response(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get cached response for request."""
        try:
            cache_key = self._generate_cache_key(request)
            return await redis_service.get(cache_key, 'api_response')
        except Exception as e:
            logger.error("Failed to get cached response", error=str(e))
            return None
    
    async def _cache_response(self, request: Request, response: Response) -> None:
        """Cache response for request."""
        try:
            # Only cache JSON responses
            if not isinstance(response, JSONResponse):
                return
            
            cache_key = self._generate_cache_key(request)
            
            # Get cache configuration
            path = request.url.path
            cache_config = self.cacheable_endpoints.get(path, {})
            ttl = cache_config.get('ttl', 3600)
            
            # Extract response content
            if hasattr(response, 'body'):
                content = json.loads(response.body.decode())
            else:
                # For streaming responses, we can't cache easily
                return
            
            # Store in cache
            await redis_service.set(cache_key, content, ttl, 'api_response')
            
            logger.debug("Response cached", path=path, cache_key=cache_key, ttl=ttl)
            
        except Exception as e:
            logger.error("Failed to cache response", error=str(e))
    
    async def _invalidate_cache(self, request: Request) -> None:
        """Invalidate cache for request."""
        try:
            path = request.url.path
            prefixes_to_invalidate = self.cache_invalidating_endpoints.get(path, [])
            
            invalidation_count = 0
            for prefix in prefixes_to_invalidate:
                count = await redis_service.flush_prefix(prefix)
                invalidation_count += count
            
            logger.info("Cache invalidated", path=path, invalidated_keys=invalidation_count)
            
        except Exception as e:
            logger.error("Failed to invalidate cache", error=str(e))
    
    async def _check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """Check rate limit for request."""
        try:
            path = request.url.path
            rate_config = self.rate_limited_endpoints.get(path)
            
            if not rate_config:
                return {"allowed": True, "current": 0, "limit": 0, "reset_in": 0}
            
            # Generate identifier (IP + user if authenticated)
            identifier = request.client.host if request.client else "unknown"
            
            user_id = getattr(request.state, 'user_id', None)
            if user_id:
                identifier = f"{identifier}:{user_id}"
            
            # Check rate limit
            return await rate_limit_cache.check_rate_limit(
                identifier=identifier,
                limit=rate_config['limit'],
                window=rate_config['window']
            )
            
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            return {"allowed": True, "current": 0, "limit": 0, "reset_in": 0}

class SmartCacheMiddleware(BaseHTTPMiddleware):
    """Smart caching middleware with predictive cache warming."""
    
    def __init__(self, app):
        super().__init__(app)
        self.cache_warming_enabled = True
        self.cache_warming_interval = 300  # 5 minutes
        
        # Start background cache warming task
        if self.cache_warming_enabled:
            asyncio.create_task(self._cache_warming_loop())
    
    async def dispatch(self, request: Request, call_next):
        """Process request with smart caching."""
        # Use base caching middleware
        caching_middleware = CachingMiddleware(None)
        return await caching_middleware.dispatch(request, call_next)
    
    async def _cache_warming_loop(self):
        """Background task to warm frequently accessed cache entries."""
        while True:
            try:
                await asyncio.sleep(self.cache_warming_interval)
                
                if not redis_service.is_connected:
                    continue
                
                # Warm up common KPI queries
                await self._warm_kpi_cache()
                
                # Warm up recent manufacturing data
                await self._warm_manufacturing_cache()
                
                logger.info("Cache warming completed")
                
            except Exception as e:
                logger.error("Cache warming failed", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _warm_kpi_cache(self):
        """Warm up KPI cache with common queries."""
        try:
            from app.api.v1.endpoints.data import get_manufacturing_kpis
            from app.core.database import get_db
            
            # Common KPI periods
            periods = ["1h", "24h", "7d", "30d"]
            
            for period in periods:
                # Check if already cached
                cached_kpis = await manufacturing_cache.get_kpis(period)
                if cached_kpis:
                    continue
                
                # Create a mock request context
                class MockUser:
                    id = "system"
                
                # This would need proper implementation with actual database session
                # For now, we'll just mark the intention
                logger.debug("Would warm KPI cache", period=period)
                
        except Exception as e:
            logger.error("Failed to warm KPI cache", error=str(e))
    
    async def _warm_manufacturing_cache(self):
        """Warm up manufacturing data cache."""
        try:
            from datetime import datetime, timedelta
            
            # Get recent data (last 24 hours)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            # This would need proper implementation with actual database queries
            logger.debug("Would warm manufacturing data cache", 
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat())
            
        except Exception as e:
            logger.error("Failed to warm manufacturing data cache", error=str(e))

class CacheMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect cache performance metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_errors': 0,
            'rate_limit_hits': 0,
            'response_times': [],
            'cache_sizes': {}
        }
    
    async def dispatch(self, request: Request, call_next):
        """Collect cache metrics."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Collect metrics
        response_time = time.time() - start_time
        self.metrics['response_times'].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
        
        # Check cache status
        cache_status = response.headers.get('X-Cache', 'MISS')
        if cache_status == 'HIT':
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
        
        # Check rate limit
        if response.status_code == 429:
            self.metrics['rate_limit_hits'] += 1
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        total_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        hit_rate = (self.metrics['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times']) if self.metrics['response_times'] else 0
        
        return {
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'cache_hit_rate': round(hit_rate, 2),
            'cache_errors': self.metrics['cache_errors'],
            'rate_limit_hits': self.metrics['rate_limit_hits'],
            'average_response_time': round(avg_response_time, 3),
            'total_requests': total_requests
        }

# Global middleware instances
caching_middleware = CachingMiddleware
smart_cache_middleware = SmartCacheMiddleware
cache_metrics_middleware = CacheMetricsMiddleware

# Initialize Redis connection at startup
async def initialize_caching():
    """Initialize caching services."""
    try:
        await redis_service.initialize()
        await manufacturing_cache.initialize()
        logger.info("Caching services initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize caching services", error=str(e))
        raise

# Cleanup function
async def cleanup_caching():
    """Cleanup caching services."""
    try:
        await redis_service.close()
        await manufacturing_cache.close()
        logger.info("Caching services cleaned up")
    except Exception as e:
        logger.error("Failed to cleanup caching services", error=str(e))