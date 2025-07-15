"""
Authentication Caching for EZBI Analytics
Redis-based session and token caching for improved performance
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.redis_service import session_cache, redis_service

logger = structlog.get_logger()

class AuthCacheManager:
    """Manages authentication caching with Redis."""
    
    def __init__(self):
        self.token_cache_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        self.session_cache_ttl = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        self.user_cache_ttl = 3600  # 1 hour for user data
        
    async def cache_user_session(self, user_id: str, user_data: Dict[str, Any], 
                               session_id: Optional[str] = None) -> str:
        """
        Cache user session data.
        
        Args:
            user_id: User ID
            user_data: User data to cache
            session_id: Optional session ID, generated if not provided
            
        Returns:
            Session ID
        """
        try:
            if not session_id:
                session_id = hashlib.md5(f"{user_id}:{datetime.now().isoformat()}".encode()).hexdigest()
            
            # Prepare session data
            session_data = {
                "user_id": user_id,
                "user_data": user_data,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            # Store in cache
            await session_cache.store_session(session_id, session_data)
            
            logger.info("User session cached", user_id=user_id, session_id=session_id)
            return session_id
            
        except Exception as e:
            logger.error("Failed to cache user session", user_id=user_id, error=str(e))
            raise
    
    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data if found, None otherwise
        """
        try:
            session_data = await session_cache.get_session(session_id)
            
            if session_data:
                # Update last accessed time
                session_data["last_accessed"] = datetime.now().isoformat()
                await session_cache.store_session(session_id, session_data)
                
                logger.debug("Session cache hit", session_id=session_id)
                return session_data
            
            logger.debug("Session cache miss", session_id=session_id)
            return None
            
        except Exception as e:
            logger.error("Failed to get cached session", session_id=session_id, error=str(e))
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate cached session.
        
        Args:
            session_id: Session ID to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await session_cache.invalidate_session(session_id)
            logger.info("Session invalidated", session_id=session_id, success=result)
            return result
            
        except Exception as e:
            logger.error("Failed to invalidate session", session_id=session_id, error=str(e))
            return False
    
    async def cache_auth_token(self, token: str, user_id: str, token_type: str = "access") -> bool:
        """
        Cache authentication token.
        
        Args:
            token: JWT token
            user_id: User ID
            token_type: Type of token (access, refresh)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            token_data = {
                "user_id": user_id,
                "token_type": token_type,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=self.token_cache_ttl)).isoformat()
            }
            
            await session_cache.store_auth_token(token_hash, user_id)
            
            logger.debug("Auth token cached", user_id=user_id, token_type=token_type)
            return True
            
        except Exception as e:
            logger.error("Failed to cache auth token", user_id=user_id, error=str(e))
            return False
    
    async def validate_cached_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate cached authentication token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token data if valid, None otherwise
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            token_data = await session_cache.get_auth_token(token_hash)
            
            if token_data:
                # Check if token is expired
                expires_at = datetime.fromisoformat(token_data.get("expires_at", ""))
                if datetime.now() > expires_at:
                    await session_cache.invalidate_auth_token(token_hash)
                    return None
                
                logger.debug("Token cache hit", user_id=token_data.get("user_id"))
                return token_data
            
            logger.debug("Token cache miss")
            return None
            
        except Exception as e:
            logger.error("Failed to validate cached token", error=str(e))
            return None
    
    async def invalidate_auth_token(self, token: str) -> bool:
        """
        Invalidate cached authentication token.
        
        Args:
            token: JWT token to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = await session_cache.invalidate_auth_token(token_hash)
            
            logger.info("Auth token invalidated", success=result)
            return result
            
        except Exception as e:
            logger.error("Failed to invalidate auth token", error=str(e))
            return False
    
    async def cache_user_data(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Cache user data for quick access.
        
        Args:
            user_id: User ID
            user_data: User data to cache
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = f"user_data:{user_id}"
            
            # Serialize user data
            cached_data = {
                "user_id": user_id,
                "data": user_data,
                "cached_at": datetime.now().isoformat()
            }
            
            await redis_service.set(cache_key, cached_data, self.user_cache_ttl, 'user_session')
            
            logger.debug("User data cached", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to cache user data", user_id=user_id, error=str(e))
            return False
    
    async def get_cached_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached user data.
        
        Args:
            user_id: User ID
            
        Returns:
            User data if found, None otherwise
        """
        try:
            cache_key = f"user_data:{user_id}"
            cached_data = await redis_service.get(cache_key, 'user_session')
            
            if cached_data:
                logger.debug("User data cache hit", user_id=user_id)
                return cached_data.get("data")
            
            logger.debug("User data cache miss", user_id=user_id)
            return None
            
        except Exception as e:
            logger.error("Failed to get cached user data", user_id=user_id, error=str(e))
            return None
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """
        Invalidate all cached data for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Invalidate user data
            cache_key = f"user_data:{user_id}"
            await redis_service.delete(cache_key, 'user_session')
            
            # Invalidate all sessions for the user
            # This is a simplified approach - in production, you'd want to track user sessions
            await redis_service.flush_prefix('user_session')
            
            logger.info("User cache invalidated", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to invalidate user cache", user_id=user_id, error=str(e))
            return False

# Global auth cache manager
auth_cache = AuthCacheManager()

# Enhanced authentication dependencies with caching

security = HTTPBearer()

async def get_current_user_cached(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user with caching support.
    
    This function first checks the cache for token validation,
    then falls back to database validation if needed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # First, try to validate token from cache
        cached_token_data = await auth_cache.validate_cached_token(token)
        
        if cached_token_data:
            user_id = cached_token_data.get("user_id")
            
            # Try to get user data from cache
            cached_user_data = await auth_cache.get_cached_user_data(user_id)
            
            if cached_user_data:
                # Create user object from cached data
                user = User(**cached_user_data)
                logger.debug("User authentication from cache", user_id=user_id)
                return user
        
        # Fallback to JWT validation and database lookup
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id: str = payload.get("sub")
            
            if user_id is None:
                raise credentials_exception
                
        except JWTError:
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            raise credentials_exception
        
        # Cache the token and user data for future requests
        await auth_cache.cache_auth_token(token, user_id)
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
        
        await auth_cache.cache_user_data(user_id, user_data)
        
        logger.debug("User authentication from database", user_id=user_id)
        return user
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise credentials_exception

async def logout_user_cached(user_id: str, token: str) -> bool:
    """
    Logout user and invalidate all cached data.
    
    Args:
        user_id: User ID
        token: JWT token to invalidate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Invalidate auth token
        await auth_cache.invalidate_auth_token(token)
        
        # Invalidate user cache
        await auth_cache.invalidate_user_cache(user_id)
        
        logger.info("User logged out with cache invalidation", user_id=user_id)
        return True
        
    except Exception as e:
        logger.error("Failed to logout user", user_id=user_id, error=str(e))
        return False

# Session management functions

async def create_user_session(user: User, additional_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new user session with caching.
    
    Args:
        user: User object
        additional_data: Optional additional session data
        
    Returns:
        Session ID
    """
    try:
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
        
        if additional_data:
            user_data.update(additional_data)
        
        session_id = await auth_cache.cache_user_session(user.id, user_data)
        
        logger.info("User session created", user_id=user.id, session_id=session_id)
        return session_id
        
    except Exception as e:
        logger.error("Failed to create user session", user_id=user.id, error=str(e))
        raise

async def get_user_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user session data.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session data if found, None otherwise
    """
    return await auth_cache.get_cached_session(session_id)

async def invalidate_user_session(session_id: str) -> bool:
    """
    Invalidate user session.
    
    Args:
        session_id: Session ID to invalidate
        
    Returns:
        True if successful, False otherwise
    """
    return await auth_cache.invalidate_session(session_id)

# Cache warming for frequently accessed users
async def warm_user_cache(user_ids: List[str], db: Session) -> None:
    """
    Warm up user cache for frequently accessed users.
    
    Args:
        user_ids: List of user IDs to warm up
        db: Database session
    """
    try:
        for user_id in user_ids:
            # Check if user is already cached
            cached_data = await auth_cache.get_cached_user_data(user_id)
            
            if not cached_data:
                # Load user from database and cache
                user = db.query(User).filter(User.id == user_id).first()
                
                if user:
                    user_data = {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "full_name": user.full_name,
                        "is_active": user.is_active,
                        "is_superuser": user.is_superuser,
                    }
                    
                    await auth_cache.cache_user_data(user_id, user_data)
                    logger.debug("User cache warmed", user_id=user_id)
        
        logger.info("User cache warming completed", user_count=len(user_ids))
        
    except Exception as e:
        logger.error("Failed to warm user cache", error=str(e))

# Performance monitoring
async def get_auth_cache_stats() -> Dict[str, Any]:
    """
    Get authentication cache statistics.
    
    Returns:
        Cache statistics
    """
    try:
        cache_stats = await session_cache.get_cache_stats()
        
        return {
            "cache_connected": cache_stats.get("connected", False),
            "total_sessions": cache_stats.get("prefix_counts", {}).get("user_session", 0),
            "total_tokens": cache_stats.get("prefix_counts", {}).get("auth_token", 0),
            "cache_hit_rate": cache_stats.get("hit_rate", 0),
            "memory_usage": cache_stats.get("memory_usage", "Unknown"),
            "cache_ttls": {
                "token_cache": auth_cache.token_cache_ttl,
                "session_cache": auth_cache.session_cache_ttl,
                "user_cache": auth_cache.user_cache_ttl,
            }
        }
        
    except Exception as e:
        logger.error("Failed to get auth cache stats", error=str(e))
        return {"error": str(e)}