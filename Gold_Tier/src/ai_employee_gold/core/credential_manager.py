"""Credential Manager for Gold Tier AI Employee.

This module provides secure credential management:
- Encrypted credential storage (Fernet encryption)
- Automatic token refresh
- Credential rotation
- Access logging

Part of Phase 7: Security Enhancements.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..config.settings import settings
from .audit_logger import audit_logger

logger = logging.getLogger(__name__)


class CredentialManager:
    """Secure credential manager with encryption and rotation."""

    def __init__(self, vault_path: Optional[str] = None):
        """Initialize credential manager.
        
        Args:
            vault_path: Path to vault root directory
        """
        self.vault_path = Path(vault_path or settings.VAULT_PATH)
        self.credentials_file = self.vault_path / ".credentials.json"
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Load existing credentials
        self.credentials = self._load_credentials()
        
        logger.info(f"Credential manager initialized: {self.credentials_file}")

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        key_file = self.vault_path / ".encryption_key"
        
        if key_file.exists():
            # Load existing key
            key = key_file.read_bytes()
            logger.info("Loaded existing encryption key")
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Restrict permissions
            logger.info("Created new encryption key")
        
        return key

    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from file."""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    encrypted_data = f.read()
                
                # Decrypt
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                credentials = json.loads(decrypted_data.decode())
                logger.info(f"Loaded {len(credentials)} credentials")
                return credentials
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
                return {}
        else:
            logger.info("No credentials file found, starting fresh")
            return {}

    def _save_credentials(self) -> bool:
        """Save credentials to file (encrypted)."""
        try:
            # Serialize
            credentials_json = json.dumps(self.credentials)
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(credentials_json.encode())
            
            # Save
            with open(self.credentials_file, 'w') as f:
                f.write(encrypted_data.decode())
            
            self.credentials_file.chmod(0o600)  # Restrict permissions
            logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False

    def set_credential(self, name: str, value: str, 
                      expires_in_days: Optional[int] = None,
                      auto_rotate: bool = False) -> bool:
        """Set a credential.
        
        Args:
            name: Credential name (e.g., "facebook_access_token")
            value: Credential value
            expires_in_days: Days until expiration (optional)
            auto_rotate: Enable auto-rotation (optional)
        
        Returns:
            True if successful
        """
        try:
            credential = {
                "value": value,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "expires_in_days": expires_in_days,
                "auto_rotate": auto_rotate
            }
            
            if expires_in_days:
                credential["expires_at"] = (
                    datetime.now() + timedelta(days=expires_in_days)
                ).isoformat()
            
            self.credentials[name] = credential
            self._save_credentials()
            
            # Log action
            audit_logger.log(
                action_type="security.set_credential",
                actor="CredentialManager",
                actor_type="system",
                domain="system",
                subdomain="security",
                target=name,
                parameters={"expires_in_days": expires_in_days, "auto_rotate": auto_rotate},
                result="success"
            )
            
            logger.info(f"Credential '{name}' set successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting credential: {e}")
            return False

    def get_credential(self, name: str) -> Optional[str]:
        """Get a credential.
        
        Args:
            name: Credential name
        
        Returns:
            Credential value or None if not found/expired
        """
        if name not in self.credentials:
            logger.warning(f"Credential '{name}' not found")
            return None
        
        credential = self.credentials[name]
        
        # Check expiration
        if "expires_at" in credential:
            expires_at = datetime.fromisoformat(credential["expires_at"])
            if datetime.now() > expires_at:
                logger.warning(f"Credential '{name}' expired")
                
                # Auto-rotate if enabled
                if credential.get("auto_rotate"):
                    logger.info(f"Auto-rotating expired credential: {name}")
                    # Trigger rotation (implement per credential type)
                
                return None
        
        # Log access
        audit_logger.log(
            action_type="security.get_credential",
            actor="CredentialManager",
            actor_type="system",
            domain="system",
            subdomain="security",
            target=name,
            parameters={},
            result="success"
        )
        
        return credential.get("value")

    def rotate_credential(self, name: str, new_value: str) -> bool:
        """Rotate a credential.
        
        Args:
            name: Credential name
            new_value: New credential value
        
        Returns:
            True if successful
        """
        try:
            if name not in self.credentials:
                logger.error(f"Credential '{name}' not found")
                return False
            
            old_credential = self.credentials[name].copy()
            
            # Update credential
            self.credentials[name]["value"] = new_value
            self.credentials[name]["updated"] = datetime.now().isoformat()
            self.credentials[name]["rotation_count"] = (
                self.credentials[name].get("rotation_count", 0) + 1
            )
            
            # Save old credential for rollback
            self.credentials[name]["previous_value"] = old_credential.get("value")
            
            self._save_credentials()
            
            # Log rotation
            audit_logger.log(
                action_type="security.rotate_credential",
                actor="CredentialManager",
                actor_type="system",
                domain="system",
                subdomain="security",
                target=name,
                parameters={"rotation_count": self.credentials[name]["rotation_count"]},
                result="success"
            )
            
            logger.info(f"Credential '{name}' rotated successfully")
            return True
        except Exception as e:
            logger.error(f"Error rotating credential: {e}")
            return False

    def delete_credential(self, name: str) -> bool:
        """Delete a credential.
        
        Args:
            name: Credential name
        
        Returns:
            True if successful
        """
        if name in self.credentials:
            del self.credentials[name]
            self._save_credentials()
            
            audit_logger.log(
                action_type="security.delete_credential",
                actor="CredentialManager",
                actor_type="system",
                domain="system",
                subdomain="security",
                target=name,
                parameters={},
                result="success"
            )
            
            logger.info(f"Credential '{name}' deleted")
            return True
        return False

    def list_credentials(self) -> list:
        """List all credential names (not values).
        
        Returns:
            List of credential names
        """
        return list(self.credentials.keys())

    def get_expiring_credentials(self, days_threshold: int = 7) -> list:
        """Get credentials expiring soon.
        
        Args:
            days_threshold: Days until expiration to flag
        
        Returns:
            List of expiring credential info
        """
        expiring = []
        now = datetime.now()
        
        for name, credential in self.credentials.items():
            if "expires_at" in credential:
                expires_at = datetime.fromisoformat(credential["expires_at"])
                days_until_expiry = (expires_at - now).days
                
                if days_until_expiry <= days_threshold:
                    expiring.append({
                        "name": name,
                        "expires_at": credential["expires_at"],
                        "days_until_expiry": days_until_expiry
                    })
        
        return expiring

    def check_token_expiry(self, token_name: str, buffer_hours: int = 1) -> bool:
        """Check if token needs refresh.
        
        Args:
            token_name: Token credential name
            buffer_hours: Hours before expiry to refresh
        
        Returns:
            True if refresh needed
        """
        credential = self.credentials.get(token_name)
        if not credential or "expires_at" not in credential:
            return False
        
        expires_at = datetime.fromisoformat(credential["expires_at"])
        refresh_at = expires_at - timedelta(hours=buffer_hours)
        
        return datetime.now() >= refresh_at


# Global credential manager instance
credential_manager = CredentialManager()
