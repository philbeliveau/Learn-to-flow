# 🔒 SPÉCIFICATIONS SÉCURITÉ - EZBI ANALYTICS

## 🎯 PHILOSOPHIE SÉCURITÉ

### Security-First Approach
```
🛡️ "Security by Design, Privacy by Default"

Principes Fondamentaux:
├── Zero-Trust Architecture: Confiance zéro par défaut
├── RGPD Compliance: Conformité native européenne
├── Defense in Depth: Sécurité multi-couches
├── Least Privilege: Privilèges minimaux
└── Continuous Monitoring: Surveillance continue
```

### Modèle de Menaces
```
⚔️ Threat Model pour PME Manufacturières

Menaces Identifiées:
├── 🎭 Usurpation d'identité: Comptes utilisateurs compromis
├── 💰 Fraude financière: Manipulation données financières
├── 🕵️ Espionnage industriel: Vol données sensibles
├── 🦠 Malware: Infections via uploads fichiers
├── 🌐 Attaques DDoS: Déni de service
├── 🔓 Accès non autorisé: Élévation de privilèges
└── 📊 Fuite de données: Exposition données clients
```

---

## 🔐 AUTHENTIFICATION & AUTORISATION

### Architecture d'Authentification
```python
# 🔐 security/auth_architecture.py - Architecture d'authentification

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import jwt
import bcrypt
import secrets
from enum import Enum
from dataclasses import dataclass
from app.core.config import settings

class AuthMethod(Enum):
    PASSWORD = "password"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    SSO_SAML = "sso_saml"
    API_KEY = "api_key"

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_CLIENT = "api_client"

class Permission(Enum):
    # Données
    VIEW_TRANSACTIONS = "view_transactions"
    CREATE_TRANSACTIONS = "create_transactions"
    EDIT_TRANSACTIONS = "edit_transactions"
    DELETE_TRANSACTIONS = "delete_transactions"
    
    # Prédictions
    VIEW_PREDICTIONS = "view_predictions"
    CREATE_PREDICTIONS = "create_predictions"
    EDIT_PREDICTIONS = "edit_predictions"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    
    # Administration
    MANAGE_USERS = "manage_users"
    MANAGE_COMPANY = "manage_company"
    MANAGE_INTEGRATIONS = "manage_integrations"
    
    # Système
    VIEW_LOGS = "view_logs"
    MANAGE_WEBHOOKS = "manage_webhooks"

@dataclass
class SecurityContext:
    user_id: str
    company_id: str
    role: UserRole
    permissions: List[Permission]
    session_id: str
    ip_address: str
    user_agent: str
    auth_method: AuthMethod
    mfa_verified: bool
    last_activity: datetime
    expires_at: datetime

class EnhancedAuthService:
    """Service d'authentification avancé avec MFA et RBAC"""
    
    def __init__(self):
        self.password_policy = {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_symbols': True,
            'max_age_days': 90,
            'history_count': 5
        }
        
        self.session_config = {
            'timeout_minutes': 30,
            'max_concurrent_sessions': 3,
            'require_mfa_for_sensitive': True
        }
    
    async def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        mfa_token: Optional[str] = None
    ) -> Tuple[bool, Optional[SecurityContext], Optional[str]]:
        """Authentification complète avec MFA"""
        
        # 1. Vérifier le rate limiting
        if await self._check_rate_limit(email, ip_address):
            return False, None, "Trop de tentatives de connexion"
        
        # 2. Vérifier les credentials
        user = await self._verify_credentials(email, password)
        if not user:
            await self._log_failed_attempt(email, ip_address, "invalid_credentials")
            return False, None, "Identifiants invalides"
        
        # 3. Vérifier si le compte est actif
        if not user.is_active:
            return False, None, "Compte désactivé"
        
        # 4. Vérifier MFA si requis
        if user.mfa_enabled:
            if not mfa_token:
                return False, None, "MFA requis"
            
            if not await self._verify_mfa_token(user.id, mfa_token):
                await self._log_failed_attempt(email, ip_address, "invalid_mfa")
                return False, None, "Token MFA invalide"
        
        # 5. Créer le contexte de sécurité
        security_context = SecurityContext(
            user_id=user.id,
            company_id=user.company_id,
            role=UserRole(user.role),
            permissions=await self._get_user_permissions(user.id),
            session_id=secrets.token_urlsafe(32),
            ip_address=ip_address,
            user_agent=user_agent,
            auth_method=AuthMethod.MFA_TOTP if user.mfa_enabled else AuthMethod.PASSWORD,
            mfa_verified=user.mfa_enabled,
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=self.session_config['timeout_minutes'])
        )
        
        # 6. Enregistrer la session
        await self._create_session(security_context)
        
        # 7. Logger la connexion réussie
        await self._log_successful_login(user.id, ip_address)
        
        return True, security_context, None
    
    async def _verify_credentials(self, email: str, password: str) -> Optional[object]:
        """Vérifier les identifiants utilisateur"""
        
        # Rechercher l'utilisateur
        user = await self._get_user_by_email(email)
        if not user:
            return None
        
        # Vérifier le mot de passe
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None
        
        # Vérifier si le mot de passe n'est pas expiré
        if user.password_updated_at:
            password_age = datetime.utcnow() - user.password_updated_at
            if password_age.days > self.password_policy['max_age_days']:
                user.password_expired = True
                await self._update_user(user)
        
        return user
    
    async def _verify_mfa_token(self, user_id: str, token: str) -> bool:
        """Vérifier le token MFA TOTP"""
        
        import pyotp
        
        # Récupérer le secret MFA de l'utilisateur
        user_mfa = await self._get_user_mfa_secret(user_id)
        if not user_mfa:
            return False
        
        # Vérifier le token TOTP
        totp = pyotp.TOTP(user_mfa.secret)
        return totp.verify(token, valid_window=1)
    
    async def authorize_action(
        self,
        security_context: SecurityContext,
        required_permission: Permission,
        resource_id: Optional[str] = None
    ) -> bool:
        """Autoriser une action spécifique"""
        
        # Vérifier que la session est valide
        if datetime.utcnow() > security_context.expires_at:
            return False
        
        # Vérifier la permission
        if required_permission not in security_context.permissions:
            return False
        
        # Vérifications spécifiques aux ressources
        if resource_id:
            if not await self._check_resource_access(
                security_context.user_id,
                security_context.company_id,
                resource_id
            ):
                return False
        
        # Mettre à jour l'activité
        security_context.last_activity = datetime.utcnow()
        await self._update_session_activity(security_context.session_id)
        
        return True
    
    async def require_elevated_auth(
        self,
        security_context: SecurityContext,
        action: str
    ) -> bool:
        """Exiger une authentification élevée pour actions sensibles"""
        
        sensitive_actions = [
            "delete_company_data",
            "export_all_data",
            "change_user_permissions",
            "delete_user_account"
        ]
        
        if action in sensitive_actions:
            # Vérifier que MFA a été utilisé récemment (< 5 minutes)
            if security_context.mfa_verified:
                time_since_mfa = datetime.utcnow() - security_context.last_activity
                if time_since_mfa.seconds < 300:  # 5 minutes
                    return True
            
            # Sinon, re-demander MFA
            return False
        
        return True
```

### Système MFA (Multi-Factor Authentication)
```python
# 🔐 security/mfa_system.py - Système MFA

import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Dict, Optional, Tuple
from app.models.user import User, UserMFA
from app.core.database import get_db

class MFAService:
    """Service de gestion MFA (Multi-Factor Authentication)"""
    
    def __init__(self):
        self.issuer_name = "EZBI Analytics"
        self.backup_codes_count = 8
    
    async def setup_mfa(self, user_id: str) -> Dict:
        """Configurer MFA pour un utilisateur"""
        
        # Générer un secret unique
        secret = pyotp.random_base32()
        
        # Créer l'URI TOTP
        user = await self._get_user(user_id)
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=self.issuer_name
        )
        
        # Générer le QR code
        qr_code_data = self._generate_qr_code(totp_uri)
        
        # Générer les codes de récupération
        backup_codes = self._generate_backup_codes()
        
        # Sauvegarder temporairement (activation pending)
        await self._save_pending_mfa(user_id, secret, backup_codes)
        
        return {
            'secret': secret,
            'qr_code': qr_code_data,
            'backup_codes': backup_codes,
            'setup_instructions': self._get_setup_instructions()
        }
    
    async def verify_and_activate_mfa(
        self,
        user_id: str,
        token: str
    ) -> Tuple[bool, Optional[str]]:
        """Vérifier le token et activer MFA"""
        
        # Récupérer le secret pending
        pending_mfa = await self._get_pending_mfa(user_id)
        if not pending_mfa:
            return False, "Configuration MFA non trouvée"
        
        # Vérifier le token
        totp = pyotp.TOTP(pending_mfa.secret)
        if not totp.verify(token, valid_window=1):
            return False, "Token invalide"
        
        # Activer MFA
        await self._activate_mfa(user_id, pending_mfa.secret, pending_mfa.backup_codes)
        
        # Supprimer le pending
        await self._delete_pending_mfa(user_id)
        
        return True, None
    
    async def verify_mfa_token(
        self,
        user_id: str,
        token: str
    ) -> Tuple[bool, Optional[str]]:
        """Vérifier un token MFA"""
        
        user_mfa = await self._get_user_mfa(user_id)
        if not user_mfa or not user_mfa.is_active:
            return False, "MFA non configuré"
        
        # Vérifier si c'est un code de récupération
        if token in user_mfa.backup_codes:
            # Utiliser le code (one-time use)
            await self._use_backup_code(user_id, token)
            return True, "Code de récupération utilisé"
        
        # Vérifier le token TOTP
        totp = pyotp.TOTP(user_mfa.secret)
        if totp.verify(token, valid_window=1):
            return True, None
        
        return False, "Token invalide"
    
    async def disable_mfa(
        self,
        user_id: str,
        password: str,
        token: str
    ) -> Tuple[bool, Optional[str]]:
        """Désactiver MFA (avec vérifications)"""
        
        # Vérifier le mot de passe
        if not await self._verify_password(user_id, password):
            return False, "Mot de passe incorrect"
        
        # Vérifier le token MFA
        token_valid, error = await self.verify_mfa_token(user_id, token)
        if not token_valid:
            return False, error
        
        # Désactiver MFA
        await self._deactivate_mfa(user_id)
        
        return True, None
    
    def _generate_qr_code(self, totp_uri: str) -> str:
        """Générer le QR code pour l'URI TOTP"""
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def _generate_backup_codes(self) -> List[str]:
        """Générer des codes de récupération"""
        
        import secrets
        import string
        
        codes = []
        for _ in range(self.backup_codes_count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            # Formatter: XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    def _get_setup_instructions(self) -> List[str]:
        """Instructions de configuration MFA"""
        
        return [
            "1. Installez une application d'authentification (Google Authenticator, Authy, etc.)",
            "2. Scannez le QR code avec votre application",
            "3. Saisissez le code à 6 chiffres généré par l'application",
            "4. Sauvegardez vos codes de récupération en lieu sûr",
            "5. Cliquez sur 'Activer MFA' pour terminer la configuration"
        ]
```

---

## 🔒 CHIFFREMENT & PROTECTION DES DONNÉES

### Architecture de Chiffrement
```python
# 🔒 security/encryption.py - Architecture de chiffrement

from typing import Dict, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os
import secrets
from app.core.config import settings

class EncryptionService:
    """Service de chiffrement pour données sensibles"""
    
    def __init__(self):
        # Clé maître depuis les variables d'environnement
        self.master_key = settings.ENCRYPTION_MASTER_KEY.encode()
        
        # Types de données et leurs niveaux de chiffrement
        self.encryption_levels = {
            'financial_data': 'AES-256-GCM',
            'personal_data': 'AES-256-GCM',
            'api_keys': 'AES-256-GCM',
            'passwords': 'bcrypt',
            'session_data': 'AES-128-GCM',
            'logs': 'AES-128-GCM'
        }
    
    def encrypt_financial_data(self, data: Union[str, Dict]) -> str:
        """Chiffrer les données financières (niveau maximum)"""
        
        if isinstance(data, dict):
            import json
            data = json.dumps(data)
        
        # Générer un salt unique
        salt = secrets.token_bytes(16)
        
        # Dériver une clé spécifique
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(self.master_key)
        
        # Chiffrer avec AES-256-GCM
        iv = secrets.token_bytes(12)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        
        # Combiner salt + iv + tag + ciphertext
        encrypted_data = salt + iv + encryptor.tag + ciphertext
        
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_financial_data(self, encrypted_data: str) -> str:
        """Déchiffrer les données financières"""
        
        try:
            # Décoder base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extraire les composants
            salt = encrypted_bytes[:16]
            iv = encrypted_bytes[16:28]
            tag = encrypted_bytes[28:44]
            ciphertext = encrypted_bytes[44:]
            
            # Dériver la clé
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(self.master_key)
            
            # Déchiffrer
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode()
            
        except Exception as e:
            raise ValueError(f"Erreur déchiffrement: {str(e)}")
    
    def encrypt_pii(self, data: str) -> str:
        """Chiffrer les données personnelles (PII)"""
        
        # Utiliser Fernet pour PII (plus simple, sécurisé)
        f = Fernet(self._derive_fernet_key('pii'))
        return f.encrypt(data.encode()).decode()
    
    def decrypt_pii(self, encrypted_data: str) -> str:
        """Déchiffrer les données personnelles"""
        
        try:
            f = Fernet(self._derive_fernet_key('pii'))
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise ValueError(f"Erreur déchiffrement PII: {str(e)}")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Chiffrer une clé API"""
        
        f = Fernet(self._derive_fernet_key('api_keys'))
        return f.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Déchiffrer une clé API"""
        
        try:
            f = Fernet(self._derive_fernet_key('api_keys'))
            return f.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            raise ValueError(f"Erreur déchiffrement API key: {str(e)}")
    
    def _derive_fernet_key(self, purpose: str) -> bytes:
        """Dériver une clé Fernet pour un usage spécifique"""
        
        # Utiliser le purpose comme salt
        salt = purpose.encode().ljust(16, b'0')[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(self.master_key)
        
        return base64.urlsafe_b64encode(key)
    
    def hash_password(self, password: str) -> str:
        """Hasher un mot de passe avec bcrypt"""
        
        import bcrypt
        
        # Générer un salt aléatoire
        salt = bcrypt.gensalt(rounds=12)
        
        # Hasher le mot de passe
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérifier un mot de passe contre son hash"""
        
        import bcrypt
        
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )

# Chiffrement au niveau base de données
class DatabaseEncryption:
    """Chiffrement transparent au niveau base de données"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
    
    def encrypt_column(self, value: str, column_type: str) -> str:
        """Chiffrer une colonne selon son type"""
        
        if column_type == 'financial':
            return self.encryption_service.encrypt_financial_data(value)
        elif column_type == 'pii':
            return self.encryption_service.encrypt_pii(value)
        elif column_type == 'api_key':
            return self.encryption_service.encrypt_api_key(value)
        else:
            return value
    
    def decrypt_column(self, encrypted_value: str, column_type: str) -> str:
        """Déchiffrer une colonne selon son type"""
        
        if column_type == 'financial':
            return self.encryption_service.decrypt_financial_data(encrypted_value)
        elif column_type == 'pii':
            return self.encryption_service.decrypt_pii(encrypted_value)
        elif column_type == 'api_key':
            return self.encryption_service.decrypt_api_key(encrypted_value)
        else:
            return encrypted_value
```

---

## 🛡️ SÉCURITÉ API

### API Security Framework
```python
# 🛡️ security/api_security.py - Sécurité API

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import ipaddress
from app.core.config import settings

class APISecurityService:
    """Service de sécurité API avec rate limiting et protection"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        self.rate_limits = {
            'auth': {'requests': 5, 'window': 60},      # 5 req/min pour auth
            'predictions': {'requests': 100, 'window': 3600},  # 100 req/h pour prédictions
            'uploads': {'requests': 10, 'window': 3600},       # 10 req/h pour uploads
            'analytics': {'requests': 200, 'window': 3600},    # 200 req/h pour analytics
            'default': {'requests': 1000, 'window': 3600}     # 1000 req/h par défaut
        }
        
        # IP whitelist pour API keys
        self.ip_whitelist = self._load_ip_whitelist()
        
        # Blocked IPs
        self.blocked_ips = self._load_blocked_ips()
    
    async def check_rate_limit(
        self,
        request: Request,
        endpoint_type: str = 'default'
    ) -> Tuple[bool, Dict]:
        """Vérifier le rate limiting"""
        
        # Identifier le client
        client_id = await self._get_client_identifier(request)
        
        # Clé Redis pour le rate limiting
        rate_key = f"rate_limit:{endpoint_type}:{client_id}"
        
        # Configuration du rate limit
        config = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        # Vérifier le count actuel
        current_count = self.redis_client.get(rate_key)
        
        if current_count is None:
            # Première requête dans la fenêtre
            pipeline = self.redis_client.pipeline()
            pipeline.incr(rate_key)
            pipeline.expire(rate_key, config['window'])
            pipeline.execute()
            
            return True, {
                'remaining': config['requests'] - 1,
                'reset_time': datetime.utcnow() + timedelta(seconds=config['window'])
            }
        
        current_count = int(current_count)
        
        if current_count >= config['requests']:
            # Rate limit dépassé
            ttl = self.redis_client.ttl(rate_key)
            
            return False, {
                'remaining': 0,
                'reset_time': datetime.utcnow() + timedelta(seconds=ttl),
                'error': 'Rate limit exceeded'
            }
        
        # Incrémenter le compteur
        self.redis_client.incr(rate_key)
        
        return True, {
            'remaining': config['requests'] - current_count - 1,
            'reset_time': datetime.utcnow() + timedelta(seconds=self.redis_client.ttl(rate_key))
        }
    
    async def validate_request_security(
        self,
        request: Request,
        require_auth: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Validation sécuritaire complète de la requête"""
        
        # 1. Vérifier l'IP
        client_ip = await self._get_client_ip(request)
        
        if client_ip in self.blocked_ips:
            return False, "IP bloquée"
        
        # 2. Vérifier les headers de sécurité
        if not self._validate_security_headers(request):
            return False, "Headers de sécurité manquants"
        
        # 3. Vérifier la taille de la requête
        if not await self._validate_request_size(request):
            return False, "Taille de requête excessive"
        
        # 4. Vérifier l'User-Agent
        if not self._validate_user_agent(request):
            return False, "User-Agent suspect"
        
        # 5. Vérifier CORS si nécessaire
        if request.method == "OPTIONS":
            return True, None
        
        # 6. Validation spécifique selon le type de requête
        if request.url.path.startswith('/api/upload'):
            return await self._validate_upload_request(request)
        
        return True, None
    
    async def _get_client_identifier(self, request: Request) -> str:
        """Obtenir l'identifiant client pour rate limiting"""
        
        # Prioriser l'API key si présente
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"api_key:{api_key[:10]}"
        
        # Utiliser l'IP comme fallback
        return f"ip:{await self._get_client_ip(request)}"
    
    async def _get_client_ip(self, request: Request) -> str:
        """Obtenir l'IP réelle du client"""
        
        # Vérifier les headers de proxy
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Prendre la première IP (client original)
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback sur l'IP directe
        return request.client.host
    
    def _validate_security_headers(self, request: Request) -> bool:
        """Valider les headers de sécurité"""
        
        # Vérifier les headers requis pour certaines routes
        if request.url.path.startswith('/api/upload'):
            if 'Content-Type' not in request.headers:
                return False
        
        # Vérifier l'absence de headers suspects
        suspicious_headers = ['X-Forwarded-Host', 'X-Forwarded-Server']
        for header in suspicious_headers:
            if header in request.headers:
                # Logger l'activité suspecte
                self._log_suspicious_activity(request, f"Suspicious header: {header}")
        
        return True
    
    async def _validate_request_size(self, request: Request) -> bool:
        """Valider la taille de la requête"""
        
        content_length = request.headers.get('Content-Length')
        if content_length:
            size = int(content_length)
            
            # Limite générale: 50MB
            if size > 50 * 1024 * 1024:
                return False
            
            # Limite spécifique pour uploads: 10MB
            if request.url.path.startswith('/api/upload') and size > 10 * 1024 * 1024:
                return False
        
        return True
    
    def _validate_user_agent(self, request: Request) -> bool:
        """Valider l'User-Agent"""
        
        user_agent = request.headers.get('User-Agent', '').lower()
        
        # Bloquer les User-Agents suspects
        blocked_agents = [
            'bot', 'crawler', 'spider', 'scraper',
            'wget', 'curl', 'python-requests'
        ]
        
        # Exception pour les API keys légitimes
        if request.headers.get('X-API-Key'):
            return True
        
        for blocked in blocked_agents:
            if blocked in user_agent:
                return False
        
        return True
    
    async def _validate_upload_request(self, request: Request) -> Tuple[bool, Optional[str]]:
        """Validation spécifique pour les uploads"""
        
        # Vérifier le Content-Type
        content_type = request.headers.get('Content-Type', '')
        
        allowed_types = [
            'multipart/form-data',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv'
        ]
        
        if not any(allowed_type in content_type for allowed_type in allowed_types):
            return False, "Type de contenu non autorisé"
        
        return True, None
    
    def _log_suspicious_activity(self, request: Request, reason: str):
        """Logger une activité suspecte"""
        
        import logging
        
        logger = logging.getLogger('security')
        logger.warning(f"Suspicious activity detected: {reason}", extra={
            'ip': request.client.host,
            'user_agent': request.headers.get('User-Agent'),
            'path': request.url.path,
            'method': request.method,
            'headers': dict(request.headers)
        })
    
    def _load_ip_whitelist(self) -> List[str]:
        """Charger la whitelist d'IPs"""
        
        # À charger depuis la base de données ou config
        return [
            '127.0.0.1',
            '::1',
            # IPs des partenaires ERP
            # IPs des services bancaires
        ]
    
    def _load_blocked_ips(self) -> List[str]:
        """Charger la liste des IPs bloquées"""
        
        # À charger depuis la base de données
        return []

# Middleware de sécurité
class SecurityMiddleware:
    """Middleware de sécurité pour FastAPI"""
    
    def __init__(self, app):
        self.app = app
        self.security_service = APISecurityService()
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            request = Request(scope, receive)
            
            # Validation sécuritaire
            is_valid, error = await self.security_service.validate_request_security(request)
            
            if not is_valid:
                response = HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error
                )
                await response(scope, receive, send)
                return
            
            # Rate limiting
            endpoint_type = self._get_endpoint_type(request.url.path)
            rate_ok, rate_info = await self.security_service.check_rate_limit(request, endpoint_type)
            
            if not rate_ok:
                response = HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        'X-RateLimit-Remaining': str(rate_info['remaining']),
                        'X-RateLimit-Reset': rate_info['reset_time'].isoformat()
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def _get_endpoint_type(self, path: str) -> str:
        """Déterminer le type d'endpoint pour rate limiting"""
        
        if '/auth/' in path:
            return 'auth'
        elif '/predictions/' in path:
            return 'predictions'
        elif '/upload/' in path:
            return 'uploads'
        elif '/analytics/' in path:
            return 'analytics'
        else:
            return 'default'
```

---

## 🔍 MONITORING & AUDIT

### Security Monitoring System
```python
# 🔍 security/monitoring.py - Système de monitoring sécuritaire

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass
from app.core.database import get_db
from app.models.security_event import SecurityEvent, SecurityAlert

class SecurityEventType(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    PASSWORD_CHANGED = "password_changed"
    PERMISSION_CHANGED = "permission_changed"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    API_KEY_USED = "api_key_used"
    INTEGRATION_ACCESS = "integration_access"

class SecuritySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEventData:
    event_type: SecurityEventType
    severity: SecuritySeverity
    user_id: Optional[str]
    company_id: Optional[str]
    ip_address: str
    user_agent: str
    details: Dict
    timestamp: datetime

class SecurityMonitoringService:
    """Service de monitoring sécuritaire"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.alert_thresholds = {
            SecurityEventType.LOGIN_FAILED: {'count': 5, 'window': 300},  # 5 échecs en 5 min
            SecurityEventType.RATE_LIMIT_EXCEEDED: {'count': 10, 'window': 3600},  # 10 fois en 1h
            SecurityEventType.SUSPICIOUS_ACTIVITY: {'count': 1, 'window': 1},  # Immédiat
            SecurityEventType.DATA_EXPORT: {'count': 10, 'window': 3600},  # 10 exports en 1h
        }
    
    async def log_security_event(self, event_data: SecurityEventData):
        """Logger un événement de sécurité"""
        
        # 1. Logger dans les logs
        self.logger.info(f"Security event: {event_data.event_type.value}", extra={
            'event_type': event_data.event_type.value,
            'severity': event_data.severity.value,
            'user_id': event_data.user_id,
            'company_id': event_data.company_id,
            'ip_address': event_data.ip_address,
            'user_agent': event_data.user_agent,
            'details': event_data.details,
            'timestamp': event_data.timestamp.isoformat()
        })
        
        # 2. Sauvegarder en base
        db = next(get_db())
        security_event = SecurityEvent(
            event_type=event_data.event_type.value,
            severity=event_data.severity.value,
            user_id=event_data.user_id,
            company_id=event_data.company_id,
            ip_address=event_data.ip_address,
            user_agent=event_data.user_agent,
            details=event_data.details,
            timestamp=event_data.timestamp
        )
        db.add(security_event)
        db.commit()
        
        # 3. Vérifier les seuils d'alerte
        await self._check_alert_thresholds(event_data)
        
        # 4. Actions automatiques si nécessaire
        await self._trigger_automatic_actions(event_data)
    
    async def _check_alert_thresholds(self, event_data: SecurityEventData):
        """Vérifier les seuils d'alerte"""
        
        if event_data.event_type not in self.alert_thresholds:
            return
        
        threshold_config = self.alert_thresholds[event_data.event_type]
        
        # Compter les événements récents
        since = datetime.utcnow() - timedelta(seconds=threshold_config['window'])
        
        db = next(get_db())
        recent_events = db.query(SecurityEvent).filter(
            SecurityEvent.event_type == event_data.event_type.value,
            SecurityEvent.ip_address == event_data.ip_address,
            SecurityEvent.timestamp >= since
        ).count()
        
        if recent_events >= threshold_config['count']:
            await self._create_security_alert(event_data, recent_events)
    
    async def _create_security_alert(
        self,
        event_data: SecurityEventData,
        event_count: int
    ):
        """Créer une alerte de sécurité"""
        
        db = next(get_db())
        
        alert = SecurityAlert(
            event_type=event_data.event_type.value,
            severity=SecuritySeverity.HIGH.value,
            title=f"Seuil d'alerte dépassé: {event_data.event_type.value}",
            description=f"{event_count} événements détectés depuis {event_data.ip_address}",
            ip_address=event_data.ip_address,
            user_id=event_data.user_id,
            company_id=event_data.company_id,
            metadata={
                'event_count': event_count,
                'threshold_window': self.alert_thresholds[event_data.event_type]['window'],
                'user_agent': event_data.user_agent
            },
            created_at=datetime.utcnow(),
            resolved=False
        )
        
        db.add(alert)
        db.commit()
        
        # Envoyer notification
        await self._send_security_alert_notification(alert)
    
    async def _trigger_automatic_actions(self, event_data: SecurityEventData):
        """Déclencher des actions automatiques"""
        
        # Bloquer temporairement l'IP en cas d'activité suspecte
        if event_data.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY:
            await self._temporary_ip_block(event_data.ip_address, duration=3600)
        
        # Révoquer la session en cas de changement de permission
        if event_data.event_type == SecurityEventType.PERMISSION_CHANGED:
            await self._revoke_user_sessions(event_data.user_id)
        
        # Alerter en cas d'export massif
        if event_data.event_type == SecurityEventType.DATA_EXPORT:
            if event_data.details.get('export_size', 0) > 100000:  # 100k records
                await self._send_immediate_alert(event_data)
    
    async def _temporary_ip_block(self, ip_address: str, duration: int):
        """Bloquer temporairement une IP"""
        
        import redis
        
        redis_client = redis.Redis()
        redis_client.setex(f"blocked_ip:{ip_address}", duration, "1")
        
        self.logger.warning(f"IP {ip_address} bloquée temporairement pour {duration} secondes")
    
    async def _send_security_alert_notification(self, alert: SecurityAlert):
        """Envoyer une notification d'alerte"""
        
        # Envoyer par email aux admins
        # Envoyer sur Slack si configuré
        # Envoyer webhook si configuré
        
        pass  # Implémentation selon les besoins
    
    async def get_security_dashboard(
        self,
        company_id: str,
        timeframe: str = "24h"
    ) -> Dict:
        """Récupérer le dashboard de sécurité"""
        
        # Calculer la période
        hours = {'24h': 24, '7d': 168, '30d': 720}[timeframe]
        since = datetime.utcnow() - timedelta(hours=hours)
        
        db = next(get_db())
        
        # Événements par type
        events_by_type = db.query(SecurityEvent).filter(
            SecurityEvent.company_id == company_id,
            SecurityEvent.timestamp >= since
        ).all()
        
        # Grouper par type
        event_counts = {}
        for event in events_by_type:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Alertes actives
        active_alerts = db.query(SecurityAlert).filter(
            SecurityAlert.company_id == company_id,
            SecurityAlert.resolved == False
        ).count()
        
        # Top IPs
        ip_activity = {}
        for event in events_by_type:
            ip_activity[event.ip_address] = ip_activity.get(event.ip_address, 0) + 1
        
        top_ips = sorted(ip_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'timeframe': timeframe,
            'total_events': len(events_by_type),
            'events_by_type': event_counts,
            'active_alerts': active_alerts,
            'top_ips': top_ips,
            'security_score': self._calculate_security_score(events_by_type, active_alerts)
        }
    
    def _calculate_security_score(self, events: List, active_alerts: int) -> int:
        """Calculer un score de sécurité (0-100)"""
        
        base_score = 100
        
        # Pénalités selon les événements
        penalties = {
            SecurityEventType.LOGIN_FAILED.value: 2,
            SecurityEventType.SUSPICIOUS_ACTIVITY.value: 10,
            SecurityEventType.RATE_LIMIT_EXCEEDED.value: 5,
            SecurityEventType.DATA_EXPORT.value: 1
        }
        
        for event in events:
            penalty = penalties.get(event.event_type, 0)
            base_score -= penalty
        
        # Pénalité pour alertes actives
        base_score -= active_alerts * 15
        
        return max(0, min(100, base_score))
```

Cette spécification de sécurité complète garantit que EZBI Analytics respecte les plus hauts standards de sécurité pour les PME manufacturières françaises, avec une conformité RGPD native et des protections multicouches contre les menaces modernes.