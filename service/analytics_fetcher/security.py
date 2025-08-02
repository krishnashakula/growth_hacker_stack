import os
import hashlib
import hmac
import base64
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import jwt
import bcrypt


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    encryption_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    bcrypt_rounds: int = 12
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    audit_log_enabled: bool = True
    ssl_verify: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour


class SecurityManager:
    """Enterprise-grade security manager for the analytics fetcher service."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger("security_manager")
        self._setup_encryption()
        self._setup_audit_logging()
        self._failed_attempts: Dict[str, List[datetime]] = {}
        self._rate_limit_tracker: Dict[str, List[datetime]] = {}
    
    def _setup_encryption(self):
        """Setup encryption keys and ciphers."""
        if not self.config.encryption_key:
            self.config.encryption_key = Fernet.generate_key()
        
        self.fernet = Fernet(self.config.encryption_key)
        
        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def _setup_audit_logging(self):
        """Setup audit logging."""
        if self.config.audit_log_enabled:
            audit_logger = logging.getLogger("audit")
            audit_logger.setLevel(logging.INFO)
            
            # Create audit log file handler
            audit_handler = logging.FileHandler("logs/audit.log")
            audit_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            ))
            audit_logger.addHandler(audit_handler)
            self.audit_logger = audit_logger
        else:
            self.audit_logger = None
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=self.config.bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_jwt_token(self, user_id: str, permissions: List[str]) -> str:
        """Generate JWT token for authentication."""
        if not self.config.jwt_secret:
            raise ValueError("JWT secret not configured")
        
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(minutes=self.config.session_timeout_minutes),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(32)
        }
        
        token = jwt.encode(payload, self.config.jwt_secret, algorithm='HS256')
        self._audit_log("JWT_TOKEN_GENERATED", user_id=user_id)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=['HS256'])
            self._audit_log("JWT_TOKEN_VERIFIED", user_id=payload.get('user_id'))
            return payload
        except jwt.ExpiredSignatureError:
            self._audit_log("JWT_TOKEN_EXPIRED", token=token[:10] + "...")
            return None
        except jwt.InvalidTokenError as e:
            self._audit_log("JWT_TOKEN_INVALID", error=str(e))
            return None
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limits."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.config.rate_limit_window)
        
        # Clean old entries
        if identifier in self._rate_limit_tracker:
            self._rate_limit_tracker[identifier] = [
                t for t in self._rate_limit_tracker[identifier] 
                if t > window_start
            ]
        else:
            self._rate_limit_tracker[identifier] = []
        
        # Check rate limit
        if len(self._rate_limit_tracker[identifier]) >= self.config.rate_limit_requests:
            self._audit_log("RATE_LIMIT_EXCEEDED", identifier=identifier)
            return False
        
        # Add current request
        self._rate_limit_tracker[identifier].append(now)
        return True
    
    def check_login_attempts(self, identifier: str) -> bool:
        """Check if login attempts are within limits."""
        now = datetime.utcnow()
        lockout_start = now - timedelta(minutes=self.config.lockout_duration_minutes)
        
        # Clean old attempts
        if identifier in self._failed_attempts:
            self._failed_attempts[identifier] = [
                t for t in self._failed_attempts[identifier] 
                if t > lockout_start
            ]
        else:
            self._failed_attempts[identifier] = []
        
        # Check if account is locked
        if len(self._failed_attempts[identifier]) >= self.config.max_login_attempts:
            self._audit_log("ACCOUNT_LOCKED", identifier=identifier)
            return False
        
        return True
    
    def record_failed_login(self, identifier: str):
        """Record a failed login attempt."""
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []
        
        self._failed_attempts[identifier].append(datetime.utcnow())
        self._audit_log("LOGIN_FAILED", identifier=identifier)
    
    def record_successful_login(self, identifier: str):
        """Record a successful login attempt."""
        if identifier in self._failed_attempts:
            del self._failed_attempts[identifier]
        self._audit_log("LOGIN_SUCCESSFUL", identifier=identifier)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: str) -> str:
        """Generate SHA-256 hash of data."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_signature(self, data: str, signature: str, public_key: bytes) -> bool:
        """Verify digital signature."""
        try:
            pub_key = serialization.load_pem_public_key(public_key)
            pub_key.verify(
                base64.b64decode(signature),
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return False
    
    def sign_data(self, data: str) -> str:
        """Sign data with private key."""
        try:
            signature = self.private_key.sign(
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode()
        except Exception as e:
            self.logger.error(f"Data signing failed: {e}")
            raise
    
    def _audit_log(self, event: str, **kwargs):
        """Log security events for audit purposes."""
        if self.audit_logger:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event': event,
                'details': kwargs
            }
            self.audit_logger.info(f"SECURITY_EVENT: {log_entry}")
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format."""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()
    
    def validate_input(self, data: str, max_length: int = 1000) -> bool:
        """Validate and sanitize input data."""
        if not data or len(data) > max_length:
            return False
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            '<script>', 'javascript:', 'data:', 'vbscript:',
            'onload=', 'onerror=', 'onclick=', 'eval(',
            'document.cookie', 'window.location'
        ]
        
        data_lower = data.lower()
        for pattern in dangerous_patterns:
            if pattern in data_lower:
                self._audit_log("DANGEROUS_INPUT_DETECTED", pattern=pattern)
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations."""
        import re
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized
    
    def cleanup_expired_data(self):
        """Clean up expired security data."""
        now = datetime.utcnow()
        
        # Clean up expired rate limit data
        for identifier in list(self._rate_limit_tracker.keys()):
            window_start = now - timedelta(seconds=self.config.rate_limit_window)
            self._rate_limit_tracker[identifier] = [
                t for t in self._rate_limit_tracker[identifier] 
                if t > window_start
            ]
            if not self._rate_limit_tracker[identifier]:
                del self._rate_limit_tracker[identifier]
        
        # Clean up expired failed attempts
        for identifier in list(self._failed_attempts.keys()):
            lockout_start = now - timedelta(minutes=self.config.lockout_duration_minutes)
            self._failed_attempts[identifier] = [
                t for t in self._failed_attempts[identifier] 
                if t > lockout_start
            ]
            if not self._failed_attempts[identifier]:
                del self._failed_attempts[identifier]
        
        self.logger.info("Security data cleanup completed") 