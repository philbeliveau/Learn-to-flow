"""
Redis Caching Service for EZBI Analytics
High-performance caching layer for manufacturing API optimization
"""

import json
import pickle
import hashlib
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from contextlib import asynccontextmanager

from app.core.config import settings

logger = structlog.get_logger()

class RedisService:
    """Redis caching service for manufacturing API optimization."""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self.is_connected = False
        
        # Cache configuration
        self.default_ttl = 3600  # 1 hour default TTL
        self.session_ttl = 28800  # 8 hours for sessions
        self.query_cache_ttl = 1800  # 30 minutes for query results
        self.kpi_cache_ttl = 900  # 15 minutes for KPIs
        
        # Cache key prefixes
        self.prefixes = {
            'manufacturing_data': 'mfg_data:',
            'kpis': 'kpi:',
            'user_session': 'session:',
            'query_result': 'query:',
            'upload_status': 'upload:',
            'api_response': 'api:',
            'aggregation': 'agg:',
            'auth_token': 'auth:',
            'rate_limit': 'rate:',
            'metrics': 'metrics:'
        }
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            logger.info("Initializing Redis connection", redis_url=settings.REDIS_URL)
            
            # Create connection pool
            self.connection_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                retry_on_timeout=True,
                health_check_interval=30,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Create Redis client
            self.redis_client = Redis(
                connection_pool=self.connection_pool,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Redis connection", error=str(e))
            self.is_connected = False
            raise
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, key: str, params: Optional[Dict] = None) -> str:
        """Generate cache key with prefix and optional parameters."""
        if params:
            # Sort parameters for consistent key generation
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            key = f"{key}:{hashlib.md5(param_str.encode()).hexdigest()}"
        
        return f"{self.prefixes.get(prefix, '')}{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode()
        return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            return json.loads(value.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return pickle.loads(value)
    
    async def get(self, key: str, prefix: str = 'api_response') -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected:
            logger.warning("Redis not connected, skipping cache get")
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            value = await self.redis_client.get(cache_key)
            
            if value is None:
                return None
            
            result = self._deserialize_value(value)
            logger.debug("Cache hit", key=cache_key)
            return result
            
        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = 'api_response') -> bool:
        """Set value in cache."""
        if not self.is_connected:
            logger.warning("Redis not connected, skipping cache set")
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            serialized_value = self._serialize_value(value)
            
            # Use default TTL if not specified
            cache_ttl = ttl or self.default_ttl
            
            await self.redis_client.setex(cache_key, cache_ttl, serialized_value)
            logger.debug("Cache set", key=cache_key, ttl=cache_ttl)
            return True
            
        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str, prefix: str = 'api_response') -> bool:
        """Delete value from cache."""
        if not self.is_connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            result = await self.redis_client.delete(cache_key)
            logger.debug("Cache delete", key=cache_key, deleted=bool(result))
            return bool(result)
            
        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str, prefix: str = 'api_response') -> bool:
        """Check if key exists in cache."""
        if not self.is_connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            result = await self.redis_client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error("Cache exists check failed", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int, prefix: str = 'api_response') -> bool:
        """Set expiration time for key."""
        if not self.is_connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            result = await self.redis_client.expire(cache_key, ttl)
            return bool(result)
            
        except Exception as e:
            logger.error("Cache expire failed", key=key, error=str(e))
            return False
    
    async def get_ttl(self, key: str, prefix: str = 'api_response') -> Optional[int]:
        """Get TTL for key."""
        if not self.is_connected:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            ttl = await self.redis_client.ttl(cache_key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error("Cache TTL check failed", key=key, error=str(e))
            return None
    
    async def flush_prefix(self, prefix: str) -> int:
        """Flush all keys with given prefix."""
        if not self.is_connected:
            return 0
        
        try:
            pattern = f"{self.prefixes.get(prefix, '')}*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info("Cache prefix flushed", prefix=prefix, deleted=deleted)
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error("Cache flush failed", prefix=prefix, error=str(e))
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_connected:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info()
            
            # Count keys by prefix
            prefix_counts = {}
            for prefix_name, prefix_key in self.prefixes.items():
                pattern = f"{prefix_key}*"
                keys = await self.redis_client.keys(pattern)
                prefix_counts[prefix_name] = len(keys)
            
            return {
                "connected": True,
                "memory_usage": info.get("used_memory_human", "Unknown"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "prefix_counts": prefix_counts,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100
            }
            
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"connected": False, "error": str(e)}

# Manufacturing-specific cache methods
class ManufacturingCache(RedisService):
    """Manufacturing-specific caching methods."""
    
    async def cache_manufacturing_data(self, machine_id: str, start_date: str, end_date: str, 
                                     data: List[Dict], limit: int = 100) -> bool:
        """Cache manufacturing data query results."""
        key = f"data:{machine_id}:{start_date}:{end_date}:{limit}"
        return await self.set(key, data, self.query_cache_ttl, 'manufacturing_data')
    
    async def get_manufacturing_data(self, machine_id: str, start_date: str, end_date: str, 
                                   limit: int = 100) -> Optional[List[Dict]]:
        """Get cached manufacturing data."""
        key = f"data:{machine_id}:{start_date}:{end_date}:{limit}"
        return await self.get(key, 'manufacturing_data')
    
    async def cache_kpis(self, period: str, kpis: Dict) -> bool:
        """Cache KPI calculations."""
        key = f"kpis:{period}:{datetime.now().strftime('%Y-%m-%d-%H')}"
        return await self.set(key, kpis, self.kpi_cache_ttl, 'kpis')
    
    async def get_kpis(self, period: str) -> Optional[Dict]:
        """Get cached KPIs."""
        key = f"kpis:{period}:{datetime.now().strftime('%Y-%m-%d-%H')}"
        return await self.get(key, 'kpis')
    
    async def cache_upload_status(self, upload_id: str, status: Dict) -> bool:
        """Cache upload processing status."""
        key = f"status:{upload_id}"
        return await self.set(key, status, 3600, 'upload_status')  # 1 hour TTL
    
    async def get_upload_status(self, upload_id: str) -> Optional[Dict]:
        """Get cached upload status."""
        key = f"status:{upload_id}"
        return await self.get(key, 'upload_status')
    
    async def cache_aggregation(self, query_hash: str, result: Dict) -> bool:
        """Cache aggregation results."""
        key = f"agg:{query_hash}"
        return await self.set(key, result, self.query_cache_ttl, 'aggregation')
    
    async def get_aggregation(self, query_hash: str) -> Optional[Dict]:
        """Get cached aggregation results."""
        key = f"agg:{query_hash}"
        return await self.get(key, 'aggregation')
    
    async def invalidate_manufacturing_cache(self, machine_id: Optional[str] = None) -> int:
        """Invalidate manufacturing data cache."""
        if machine_id:
            # Invalidate specific machine data
            pattern = f"{self.prefixes['manufacturing_data']}data:{machine_id}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
        else:
            # Invalidate all manufacturing data
            return await self.flush_prefix('manufacturing_data')
        
        return 0
    
    async def invalidate_kpi_cache(self) -> int:
        """Invalidate KPI cache."""
        return await self.flush_prefix('kpis')

# Session cache methods
class SessionCache(RedisService):
    """Session-specific caching methods."""
    
    async def store_session(self, session_id: str, user_data: Dict) -> bool:
        """Store user session data."""
        key = f"user:{session_id}"
        return await self.set(key, user_data, self.session_ttl, 'user_session')
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get user session data."""
        key = f"user:{session_id}"
        return await self.get(key, 'user_session')
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session."""
        key = f"user:{session_id}"
        return await self.delete(key, 'user_session')
    
    async def store_auth_token(self, token_hash: str, user_id: str) -> bool:
        """Store authentication token."""
        key = f"token:{token_hash}"
        return await self.set(key, {"user_id": user_id, "created_at": datetime.now().isoformat()}, 
                            self.session_ttl, 'auth_token')
    
    async def get_auth_token(self, token_hash: str) -> Optional[Dict]:
        """Get authentication token data."""
        key = f"token:{token_hash}"
        return await self.get(key, 'auth_token')
    
    async def invalidate_auth_token(self, token_hash: str) -> bool:
        """Invalidate authentication token."""
        key = f"token:{token_hash}"
        return await self.delete(key, 'auth_token')

# Rate limiting
class RateLimitCache(RedisService):
    """Rate limiting cache."""
    
    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> Dict[str, Any]:
        """Check rate limit for identifier."""
        key = f"limit:{identifier}"
        
        try:
            # Get current count
            current = await self.redis_client.get(self._generate_cache_key('rate_limit', key))
            current_count = int(current) if current else 0
            
            if current_count >= limit:
                ttl = await self.redis_client.ttl(self._generate_cache_key('rate_limit', key))
                return {
                    "allowed": False,
                    "current": current_count,
                    "limit": limit,
                    "reset_in": ttl
                }
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            cache_key = self._generate_cache_key('rate_limit', key)
            pipe.incr(cache_key)
            pipe.expire(cache_key, window)
            results = await pipe.execute()
            
            new_count = results[0]
            
            return {
                "allowed": True,
                "current": new_count,
                "limit": limit,
                "reset_in": window
            }
            
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            # Allow request on error
            return {
                "allowed": True,
                "current": 0,
                "limit": limit,
                "reset_in": window
            }

# Global cache instances
redis_service = RedisService()
manufacturing_cache = ManufacturingCache()
session_cache = SessionCache()
rate_limit_cache = RateLimitCache()

# Cache context manager
@asynccontextmanager
async def get_redis_client():
    """Context manager for Redis client."""
    await redis_service.initialize()
    try:
        yield redis_service.redis_client
    finally:
        await redis_service.close()

# Cache decorators
def cache_result(ttl: int = 3600, prefix: str = 'api_response'):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await redis_service.get(cache_key, prefix)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_service.set(cache_key, result, ttl, prefix)
            
            return result
        return wrapper
    return decorator

def cache_invalidate(prefix: str):
    """Decorator to invalidate cache after function execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await redis_service.flush_prefix(prefix)
            return result
        return wrapper
    return decorator