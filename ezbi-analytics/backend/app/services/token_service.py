"""
Secure Token Storage Service
Handles secure storage and retrieval of JWT tokens with encryption and rotation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from redis import Redis
import json
import secrets
import hashlib
import structlog
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.database import get_db_session
from app.models.user import User
from app.models.session import UserSession

logger = structlog.get_logger()

class TokenType(Enum):
    """Token types for secure storage"""
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
    RESET_TOKEN = "reset"
    VERIFICATION_TOKEN = "verification"

@dataclass
class SecureToken:
    """Secure token container"""
    token_id: str
    user_id: int
    token_type: TokenType
    encrypted_token: str
    expires_at: datetime
    created_at: datetime
    last_used: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_revoked: bool = False
    device_fingerprint: Optional[str] = None

class SecureTokenService:
    """
    Secure token storage and management service
    Provides encrypted storage, automatic rotation, and comprehensive audit trails
    """
    
    def __init__(self):
        self.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.fernet_key = settings.FERNET_KEY or Fernet.generate_key()
        self.fernet = Fernet(self.fernet_key if isinstance(self.fernet_key, bytes) else self.fernet_key.encode())
        
        # Token storage prefixes
        self.token_prefix = "secure_token"
        self.blacklist_prefix = "blacklist"
        self.user_tokens_prefix = "user_tokens"
        
        # Token rotation settings
        self.rotation_threshold = 0.8  # Rotate when 80% of lifetime has passed
        self.max_tokens_per_user = 5  # Maximum concurrent tokens per user
        
    def generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Generate device fingerprint for additional security"""
        fingerprint_data = f"{user_agent}:{ip_address}:{secrets.token_hex(16)}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage"""
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from secure storage"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
    
    async def store_token(
        self,
        user_id: int,
        token: str,
        token_type: TokenType,
        expires_in: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Store token securely with encryption and metadata"""
        try:
            # Generate unique token ID
            token_id = secrets.token_urlsafe(32)
            
            # Generate device fingerprint
            device_fingerprint = self.generate_device_fingerprint(
                user_agent or "unknown", 
                ip_address or "unknown"
            )
            
            # Encrypt token
            encrypted_token = self.encrypt_token(token)
            
            # Create secure token object
            secure_token = SecureToken(
                token_id=token_id,
                user_id=user_id,
                token_type=token_type,
                encrypted_token=encrypted_token,
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                created_at=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint
            )
            
            # Store in Redis with expiration
            token_key = f"{self.token_prefix}:{token_id}"
            token_data = {
                "token_id": token_id,
                "user_id": user_id,
                "token_type": token_type.value,
                "encrypted_token": encrypted_token,
                "expires_at": secure_token.expires_at.isoformat(),
                "created_at": secure_token.created_at.isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "device_fingerprint": device_fingerprint,
                "is_revoked": False
            }
            
            # Store token data
            self.redis_client.setex(
                token_key,
                expires_in,
                json.dumps(token_data)
            )
            
            # Add to user's token list
            await self._add_to_user_tokens(user_id, token_id, token_type)
            
            # Clean up old tokens if limit exceeded
            await self._cleanup_user_tokens(user_id)
            
            # Store in database for audit
            await self._store_token_audit(secure_token)
            
            logger.info(
                "Token stored securely",
                token_id=token_id,
                user_id=user_id,
                token_type=token_type.value,
                device_fingerprint=device_fingerprint[:8]
            )
            
            return token_id
            
        except Exception as e:
            logger.error("Failed to store token", error=str(e), user_id=user_id)
            raise
    
    async def retrieve_token(
        self,
        token_id: str,
        expected_type: TokenType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve and decrypt token with validation"""
        try:
            # Get token data from Redis
            token_key = f"{self.token_prefix}:{token_id}"
            token_data = self.redis_client.get(token_key)
            
            if not token_data:
                logger.warning("Token not found", token_id=token_id)
                return None
            
            token_info = json.loads(token_data)
            
            # Check if token is revoked
            if token_info.get("is_revoked", False):
                logger.warning("Token is revoked", token_id=token_id)
                return None
            
            # Validate token type
            if token_info.get("token_type") != expected_type.value:
                logger.warning(
                    "Token type mismatch",
                    token_id=token_id,
                    expected=expected_type.value,
                    actual=token_info.get("token_type")
                )
                return None
            
            # Validate expiration
            expires_at = datetime.fromisoformat(token_info["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning("Token expired", token_id=token_id)
                await self._revoke_token(token_id)
                return None
            
            # Optional: Validate device fingerprint for additional security
            if settings.ENVIRONMENT == "production" and ip_address and user_agent:
                current_fingerprint = self.generate_device_fingerprint(user_agent, ip_address)
                stored_fingerprint = token_info.get("device_fingerprint")
                
                if stored_fingerprint and current_fingerprint != stored_fingerprint:
                    logger.warning(
                        "Device fingerprint mismatch",
                        token_id=token_id,
                        user_id=token_info["user_id"]
                    )
                    # Don't reject in development, but log for security monitoring
                    if settings.ENVIRONMENT == "production":
                        return None
            
            # Decrypt and return token
            encrypted_token = token_info["encrypted_token"]
            decrypted_token = self.decrypt_token(encrypted_token)
            
            # Update last used timestamp
            await self._update_token_usage(token_id)
            
            logger.info(
                "Token retrieved successfully",
                token_id=token_id,
                user_id=token_info["user_id"]
            )
            
            return decrypted_token
            
        except Exception as e:
            logger.error("Failed to retrieve token", error=str(e), token_id=token_id)
            return None
    
    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a specific token"""
        try:
            return await self._revoke_token(token_id)
        except Exception as e:
            logger.error("Failed to revoke token", error=str(e), token_id=token_id)
            return False
    
    async def revoke_all_user_tokens(self, user_id: int, except_token_id: Optional[str] = None) -> bool:
        """Revoke all tokens for a user"""
        try:
            # Get user's tokens
            user_tokens_key = f"{self.user_tokens_prefix}:{user_id}"
            user_tokens_data = self.redis_client.get(user_tokens_key)
            
            if not user_tokens_data:
                return True
            
            user_tokens = json.loads(user_tokens_data)
            
            # Revoke each token
            for token_id in user_tokens.get("tokens", []):
                if except_token_id and token_id == except_token_id:
                    continue
                    
                await self._revoke_token(token_id)
            
            # Clear user tokens list
            if except_token_id:
                # Keep only the excepted token
                user_tokens["tokens"] = [except_token_id]
                self.redis_client.setex(
                    user_tokens_key,
                    86400,  # 24 hours
                    json.dumps(user_tokens)
                )
            else:
                # Clear all
                self.redis_client.delete(user_tokens_key)
            
            logger.info(
                "All user tokens revoked",
                user_id=user_id,
                except_token_id=except_token_id
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to revoke all user tokens", error=str(e), user_id=user_id)
            return False
    
    async def is_token_blacklisted(self, token_id: str) -> bool:
        """Check if token is blacklisted"""
        try:
            blacklist_key = f"{self.blacklist_prefix}:{token_id}"
            return self.redis_client.exists(blacklist_key) > 0
        except Exception as e:
            logger.error("Failed to check token blacklist", error=str(e), token_id=token_id)
            return False
    
    async def get_user_tokens(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active tokens for a user"""
        try:
            user_tokens_key = f"{self.user_tokens_prefix}:{user_id}"
            user_tokens_data = self.redis_client.get(user_tokens_key)
            
            if not user_tokens_data:
                return []
            
            user_tokens = json.loads(user_tokens_data)
            token_details = []
            
            for token_id in user_tokens.get("tokens", []):
                token_key = f"{self.token_prefix}:{token_id}"
                token_data = self.redis_client.get(token_key)
                
                if token_data:
                    token_info = json.loads(token_data)
                    
                    # Check if token is still valid
                    expires_at = datetime.fromisoformat(token_info["expires_at"])
                    if datetime.utcnow() <= expires_at and not token_info.get("is_revoked", False):
                        token_details.append({
                            "token_id": token_id,
                            "token_type": token_info["token_type"],
                            "created_at": token_info["created_at"],
                            "expires_at": token_info["expires_at"],
                            "ip_address": token_info.get("ip_address"),
                            "user_agent": token_info.get("user_agent"),
                            "last_used": token_info.get("last_used")
                        })
            
            return token_details
            
        except Exception as e:
            logger.error("Failed to get user tokens", error=str(e), user_id=user_id)
            return []
    
    async def rotate_token_if_needed(self, token_id: str) -> Optional[str]:
        """Rotate token if it's approaching expiration"""
        try:
            token_key = f"{self.token_prefix}:{token_id}"
            token_data = self.redis_client.get(token_key)
            
            if not token_data:
                return None
            
            token_info = json.loads(token_data)
            
            # Check if rotation is needed
            created_at = datetime.fromisoformat(token_info["created_at"])
            expires_at = datetime.fromisoformat(token_info["expires_at"])
            
            total_lifetime = expires_at - created_at
            time_passed = datetime.utcnow() - created_at
            
            if time_passed >= total_lifetime * self.rotation_threshold:
                # Generate new token
                from app.core.security import JWTManager
                
                new_token = JWTManager.create_access_token(
                    data={"sub": str(token_info["user_id"])},
                    expires_delta=total_lifetime
                )
                
                # Store new token
                new_token_id = await self.store_token(
                    user_id=token_info["user_id"],
                    token=new_token,
                    token_type=TokenType(token_info["token_type"]),
                    expires_in=int(total_lifetime.total_seconds()),
                    ip_address=token_info.get("ip_address"),
                    user_agent=token_info.get("user_agent")
                )
                
                # Revoke old token
                await self._revoke_token(token_id)
                
                logger.info(
                    "Token rotated successfully",
                    old_token_id=token_id,
                    new_token_id=new_token_id,
                    user_id=token_info["user_id"]
                )
                
                return new_token_id
            
            return None
            
        except Exception as e:
            logger.error("Failed to rotate token", error=str(e), token_id=token_id)
            return None
    
    async def _revoke_token(self, token_id: str) -> bool:
        """Internal method to revoke a token"""
        try:
            token_key = f"{self.token_prefix}:{token_id}"
            token_data = self.redis_client.get(token_key)
            
            if not token_data:
                return False
            
            token_info = json.loads(token_data)
            
            # Mark as revoked
            token_info["is_revoked"] = True
            token_info["revoked_at"] = datetime.utcnow().isoformat()
            
            # Update in Redis
            self.redis_client.setex(
                token_key,
                3600,  # Keep for 1 hour for audit
                json.dumps(token_info)
            )
            
            # Add to blacklist
            blacklist_key = f"{self.blacklist_prefix}:{token_id}"
            expires_at = datetime.fromisoformat(token_info["expires_at"])
            ttl = max(1, int((expires_at - datetime.utcnow()).total_seconds()))
            
            self.redis_client.setex(blacklist_key, ttl, "1")
            
            # Remove from user tokens
            user_id = token_info["user_id"]
            user_tokens_key = f"{self.user_tokens_prefix}:{user_id}"
            user_tokens_data = self.redis_client.get(user_tokens_key)
            
            if user_tokens_data:
                user_tokens = json.loads(user_tokens_data)
                if token_id in user_tokens.get("tokens", []):
                    user_tokens["tokens"].remove(token_id)
                    self.redis_client.setex(
                        user_tokens_key,
                        86400,
                        json.dumps(user_tokens)
                    )
            
            logger.info("Token revoked", token_id=token_id, user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to revoke token", error=str(e), token_id=token_id)
            return False
    
    async def _add_to_user_tokens(self, user_id: int, token_id: str, token_type: TokenType):
        """Add token to user's token list"""
        try:
            user_tokens_key = f"{self.user_tokens_prefix}:{user_id}"
            user_tokens_data = self.redis_client.get(user_tokens_key)
            
            if user_tokens_data:
                user_tokens = json.loads(user_tokens_data)
            else:
                user_tokens = {"tokens": []}
            
            if token_id not in user_tokens["tokens"]:
                user_tokens["tokens"].append(token_id)
            
            self.redis_client.setex(
                user_tokens_key,
                86400,  # 24 hours
                json.dumps(user_tokens)
            )
            
        except Exception as e:
            logger.error("Failed to add token to user list", error=str(e), user_id=user_id)
    
    async def _cleanup_user_tokens(self, user_id: int):
        """Clean up old tokens if user has too many"""
        try:
            user_tokens_key = f"{self.user_tokens_prefix}:{user_id}"
            user_tokens_data = self.redis_client.get(user_tokens_key)
            
            if not user_tokens_data:
                return
            
            user_tokens = json.loads(user_tokens_data)
            tokens = user_tokens.get("tokens", [])
            
            if len(tokens) > self.max_tokens_per_user:
                # Sort by creation time and keep only the newest
                valid_tokens = []
                
                for token_id in tokens:
                    token_key = f"{self.token_prefix}:{token_id}"
                    token_data = self.redis_client.get(token_key)
                    
                    if token_data:
                        token_info = json.loads(token_data)
                        if not token_info.get("is_revoked", False):
                            valid_tokens.append({
                                "token_id": token_id,
                                "created_at": token_info["created_at"]
                            })
                
                # Sort by creation time (newest first)
                valid_tokens.sort(key=lambda x: x["created_at"], reverse=True)
                
                # Keep only the max allowed tokens
                tokens_to_keep = valid_tokens[:self.max_tokens_per_user]
                tokens_to_revoke = valid_tokens[self.max_tokens_per_user:]
                
                # Revoke old tokens
                for token_info in tokens_to_revoke:
                    await self._revoke_token(token_info["token_id"])
                
                # Update user tokens list
                user_tokens["tokens"] = [t["token_id"] for t in tokens_to_keep]
                self.redis_client.setex(
                    user_tokens_key,
                    86400,
                    json.dumps(user_tokens)
                )
                
        except Exception as e:
            logger.error("Failed to cleanup user tokens", error=str(e), user_id=user_id)
    
    async def _update_token_usage(self, token_id: str):
        """Update token last used timestamp"""
        try:
            token_key = f"{self.token_prefix}:{token_id}"
            token_data = self.redis_client.get(token_key)
            
            if token_data:
                token_info = json.loads(token_data)
                token_info["last_used"] = datetime.utcnow().isoformat()
                
                # Get remaining TTL
                ttl = self.redis_client.ttl(token_key)
                if ttl > 0:
                    self.redis_client.setex(
                        token_key,
                        ttl,
                        json.dumps(token_info)
                    )
                    
        except Exception as e:
            logger.error("Failed to update token usage", error=str(e), token_id=token_id)
    
    async def _store_token_audit(self, secure_token: SecureToken):
        """Store token audit information in database"""
        try:
            async with get_db_session() as db:
                # Store session information
                session = UserSession(
                    session_id=secure_token.token_id,
                    user_id=secure_token.user_id,
                    ip_address=secure_token.ip_address,
                    user_agent=secure_token.user_agent,
                    expires_at=secure_token.expires_at,
                    is_active=True
                )
                
                db.add(session)
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to store token audit", error=str(e))

# Global token service instance
token_service = SecureTokenService()