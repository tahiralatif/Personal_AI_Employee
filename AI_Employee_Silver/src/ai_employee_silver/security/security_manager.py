"""
Security Manager for AI Employee Silver Tier.

This module implements security features including:
- Secure credential management
- OAuth token refresh mechanisms
- Session management
- Audit logging
- Permission boundary enforcement

Agent Skills:
    - security.get_credential(name) -> str
    - security.set_credential(name, value) -> bool
    - security.rotate_credential(name) -> bool
    - security.get_audit_log(start_date, end_date) -> list
    - security.check_permission(action, resource) -> bool
"""

import logging
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


class AuditEventType(Enum):
    """Audit log event types."""
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_UPDATE = "credential_update"
    TOKEN_REFRESH = "token_refresh"
    PERMISSION_CHECK = "permission_check"
    PERMISSION_DENIED = "permission_denied"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SECURITY_ALERT = "security_alert"


class PermissionLevel(Enum):
    """Permission levels for actions."""
    PUBLIC = "public"
    USER = "user"
    ADMIN = "admin"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """Represents an audit log entry."""
    timestamp: str
    event_type: str
    action: str
    resource: str
    user: str
    success: bool
    ip_address: Optional[str] = None
    details: Optional[str] = None


@dataclass
class CredentialInfo:
    """Credential metadata (not the actual value)."""
    name: str
    created: str
    last_accessed: Optional[str] = None
    last_rotated: Optional[str] = None
    access_count: int = 0
    requires_rotation: bool = False


class SecurityManager:
    """
    Security Manager for AI Employee system.
    
    This manager handles:
    - Encrypted credential storage
    - OAuth token refresh
    - Session management
    - Audit logging
    - Permission enforcement
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Security Manager.
        
        Args:
            vault_path: Path to the AI Employee vault
            settings: Application settings
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        
        # Security directories
        self.security_dir = self.vault_path / ".security"
        self.security_dir.mkdir(parents=True, exist_ok=True)
        
        # Credential storage (encrypted)
        self.credentials_file = self.security_dir / "credentials.enc"
        self.credential_meta_file = self.security_dir / "credential_meta.json"
        
        # Audit log
        self.audit_log_file = self.security_dir / "audit_log.jsonl"
        
        # Session storage
        self.sessions_dir = self.security_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Encryption key (derived from master password)
        self.fernet: Optional[Fernet] = None
        self._initialize_encryption()
        
        # Permission boundaries
        self.permission_boundaries = self._load_permission_boundaries()
        
        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Log security initialization
        self._log_audit_event(
            event_type=AuditEventType.SECURITY_ALERT,
            action="security_manager_initialized",
            resource=str(self.security_dir),
            user="system",
            success=True,
            details="Security manager initialized"
        )
    
    def _initialize_encryption(self) -> None:
        """Initialize encryption using master password from environment."""
        try:
            # Get master password from environment
            master_password = os.getenv("SECURITY_MASTER_PASSWORD", "default_password_change_me")
            
            # Derive key from password using PBKDF2
            salt_file = self.security_dir / "salt"
            
            if salt_file.exists():
                salt = base64.b64decode(salt_file.read_text())
            else:
                salt = os.urandom(16)
                salt_file.write_text(base64.b64encode(salt).decode())
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self.fernet = Fernet(key)
            
            self.logger.info("Encryption initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            self._log_audit_event(
                event_type=AuditEventType.SECURITY_ALERT,
                action="encryption_init_failed",
                resource="encryption",
                user="system",
                success=False,
                details=str(e)
            )
    
    def _load_permission_boundaries(self) -> Dict[str, Any]:
        """Load permission boundaries from configuration."""
        return {
            # Email permissions
            "email.send": {
                "level": PermissionLevel.USER.value,
                "requires_approval": True,
                "daily_limit": 100
            },
            "email.bulk_send": {
                "level": PermissionLevel.ADMIN.value,
                "requires_approval": True,
                "daily_limit": 10
            },
            
            # Payment permissions
            "payment.send": {
                "level": PermissionLevel.ADMIN.value,
                "requires_approval": True,
                "amount_limit": 1000
            },
            "payment.recurring": {
                "level": PermissionLevel.ADMIN.value,
                "requires_approval": True,
                "amount_limit": 100
            },
            
            # Data access permissions
            "data.read": {
                "level": PermissionLevel.USER.value,
                "requires_approval": False
            },
            "data.sensitive_read": {
                "level": PermissionLevel.ADMIN.value,
                "requires_approval": True
            },
            "data.delete": {
                "level": PermissionLevel.CRITICAL.value,
                "requires_approval": True
            },
            
            # System permissions
            "system.config_change": {
                "level": PermissionLevel.CRITICAL.value,
                "requires_approval": True
            },
            "system.restart": {
                "level": PermissionLevel.ADMIN.value,
                "requires_approval": True
            }
        }
    
    # =========================================================================
    # Credential Management
    # =========================================================================
    
    def set_credential(
        self,
        name: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store encrypted credential.
        
        Agent Skill: security.set_credential
        
        Args:
            name: Credential name
            value: Credential value
            metadata: Optional metadata
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            self.logger.info(f"Storing credential: {name}")
            
            if not self.fernet:
                return {"success": False, "error": "Encryption not initialized"}
            
            # Load existing credentials
            credentials = self._load_credentials()
            
            # Encrypt and store
            encrypted_value = self.fernet.encrypt(value.encode())
            credentials[name] = base64.b64encode(encrypted_value).decode()
            
            # Save credentials
            self._save_credentials(credentials)
            
            # Update metadata
            self._update_credential_metadata(name, metadata)
            
            # Log access
            self._log_audit_event(
                event_type=AuditEventType.CREDENTIAL_UPDATE,
                action="set_credential",
                resource=name,
                user="system",
                success=True
            )
            
            self.logger.info(f"Credential stored: {name}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to store credential: {e}")
            self._log_audit_event(
                event_type=AuditEventType.CREDENTIAL_UPDATE,
                action="set_credential",
                resource=name,
                user="system",
                success=False,
                details=str(e)
            )
            return {"success": False, "error": str(e)}
    
    def get_credential(self, name: str) -> Dict[str, Any]:
        """
        Retrieve decrypted credential.
        
        Agent Skill: security.get_credential
        
        Args:
            name: Credential name
            
        Returns:
            dict with 'success' (bool) and 'value' (str) or 'error' (str)
        """
        try:
            self.logger.debug(f"Retrieving credential: {name}")
            
            if not self.fernet:
                return {"success": False, "error": "Encryption not initialized"}
            
            # Load credentials
            credentials = self._load_credentials()
            
            if name not in credentials:
                self._log_audit_event(
                    event_type=AuditEventType.PERMISSION_DENIED,
                    action="get_credential",
                    resource=name,
                    user="system",
                    success=False,
                    details="Credential not found"
                )
                return {"success": False, "error": "Credential not found"}
            
            # Decrypt
            encrypted_value = base64.b64decode(credentials[name])
            value = self.fernet.decrypt(encrypted_value).decode()
            
            # Update metadata
            self._update_credential_access(name)
            
            # Log access
            self._log_audit_event(
                event_type=AuditEventType.CREDENTIAL_ACCESS,
                action="get_credential",
                resource=name,
                user="system",
                success=True
            )
            
            return {"success": True, "value": value}
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential: {e}")
            self._log_audit_event(
                event_type=AuditEventType.CREDENTIAL_ACCESS,
                action="get_credential",
                resource=name,
                user="system",
                success=False,
                details=str(e)
            )
            return {"success": False, "error": str(e)}
    
    def rotate_credential(self, name: str, new_value: str) -> Dict[str, Any]:
        """
        Rotate credential.
        
        Agent Skill: security.rotate_credential
        
        Args:
            name: Credential name
            new_value: New credential value
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            self.logger.info(f"Rotating credential: {name}")
            
            # Store new credential
            result = self.set_credential(
                name,
                new_value,
                metadata={"rotation_reason": "manual_rotation"}
            )
            
            if result["success"]:
                # Log rotation
                self._log_audit_event(
                    event_type=AuditEventType.TOKEN_REFRESH,
                    action="rotate_credential",
                    resource=name,
                    user="system",
                    success=True
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to rotate credential: {e}")
            return {"success": False, "error": str(e)}
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load encrypted credentials from file."""
        try:
            if self.credentials_file.exists():
                content = self.credentials_file.read_text()
                return json.loads(content)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, str]) -> None:
        """Save encrypted credentials to file."""
        try:
            self.credentials_file.write_text(json.dumps(credentials, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save credentials: {e}")
    
    def _update_credential_metadata(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update credential metadata."""
        try:
            meta_file = self.credential_meta_file
            meta = {}
            
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
            
            now = datetime.now().isoformat()
            
            if name not in meta:
                meta[name] = {
                    "name": name,
                    "created": now,
                    "last_accessed": None,
                    "last_rotated": now,
                    "access_count": 0
                }
            
            if metadata:
                meta[name].update(metadata)
            
            meta_file.write_text(json.dumps(meta, indent=2))
            
        except Exception as e:
            self.logger.error(f"Failed to update metadata: {e}")
    
    def _update_credential_access(self, name: str) -> None:
        """Update credential access timestamp."""
        try:
            meta_file = self.credential_meta_file
            meta = {}
            
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
            
            if name in meta:
                meta[name]["last_accessed"] = datetime.now().isoformat()
                meta[name]["access_count"] = meta[name].get("access_count", 0) + 1
                meta_file.write_text(json.dumps(meta, indent=2))
                
        except Exception as e:
            self.logger.error(f"Failed to update access: {e}")
    
    # =========================================================================
    # OAuth Token Refresh
    # =========================================================================
    
    def refresh_oauth_token(
        self,
        service: str,
        refresh_token_credential: str,
        token_endpoint: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """
        Refresh OAuth access token.
        
        Args:
            service: Service name (gmail, linkedin, etc.)
            refresh_token_credential: Credential name containing refresh token
            token_endpoint: OAuth token endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            
        Returns:
            dict with 'success' (bool) and token info or 'error' (str)
        """
        try:
            self.logger.info(f"Refreshing OAuth token for: {service}")
            
            # Get refresh token
            token_result = self.get_credential(refresh_token_credential)
            if not token_result["success"]:
                return {"success": False, "error": "Refresh token not found"}
            
            refresh_token = token_result["value"]
            
            # Make token refresh request (using requests library)
            import requests
            
            response = requests.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Store new access token
                if "access_token" in token_data:
                    self.set_credential(
                        f"{service}_access_token",
                        token_data["access_token"]
                    )
                
                # Store new refresh token if provided
                if "refresh_token" in token_data:
                    self.set_credential(
                        refresh_token_credential,
                        token_data["refresh_token"]
                    )
                
                # Log refresh
                self._log_audit_event(
                    event_type=AuditEventType.TOKEN_REFRESH,
                    action="refresh_oauth_token",
                    resource=service,
                    user="system",
                    success=True
                )
                
                self.logger.info(f"OAuth token refreshed for: {service}")
                
                return {
                    "success": True,
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type")
                }
            else:
                self.logger.error(f"Token refresh failed: {response.text}")
                return {"success": False, "error": f"Token refresh failed: {response.status_code}"}
            
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def start_session(
        self,
        session_name: str,
        user: str = "system"
    ) -> Dict[str, Any]:
        """
        Start new session.
        
        Args:
            session_name: Session name
            user: User identifier
            
        Returns:
            dict with 'success' (bool) and 'session_id' (str) or 'error' (str)
        """
        try:
            session_id = f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.active_sessions[session_id] = {
                "name": session_name,
                "user": user,
                "started": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            # Save session
            session_file = self.sessions_dir / f"{session_id}.json"
            session_file.write_text(json.dumps(self.active_sessions[session_id], indent=2))
            
            # Log session start
            self._log_audit_event(
                event_type=AuditEventType.SESSION_START,
                action="start_session",
                resource=session_id,
                user=user,
                success=True
            )
            
            self.logger.info(f"Session started: {session_id}")
            
            return {"success": True, "session_id": session_id}
            
        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            return {"success": False, "error": str(e)}
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End session.
        
        Args:
            session_id: Session ID
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            # Log session end
            self._log_audit_event(
                event_type=AuditEventType.SESSION_END,
                action="end_session",
                resource=session_id,
                user=session.get("user", "system"),
                success=True,
                details=f"Duration: {session.get('last_activity')} - {session.get('started')}"
            )
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Archive session
            archive_file = self.sessions_dir / "archive" / f"{session_id}.json"
            archive_file.parent.mkdir(parents=True, exist_ok=True)
            session["ended"] = datetime.now().isoformat()
            archive_file.write_text(json.dumps(session, indent=2))
            
            self.logger.info(f"Session ended: {session_id}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Permission Enforcement
    # =========================================================================
    
    def check_permission(
        self,
        action: str,
        resource: str,
        user: str = "system"
    ) -> Dict[str, Any]:
        """
        Check if action is permitted.
        
        Agent Skill: security.check_permission
        
        Args:
            action: Action to perform
            resource: Resource to access
            user: User identifier
            
        Returns:
            dict with 'permitted' (bool) and reason
        """
        try:
            # Get permission boundary for action
            boundary = self.permission_boundaries.get(action)
            
            if not boundary:
                # Unknown action, default to requiring approval
                self.logger.warning(f"Unknown action: {action}, requiring approval")
                return {
                    "permitted": False,
                    "reason": "Unknown action, approval required",
                    "requires_approval": True
                }
            
            # Check permission level
            level = boundary.get("level", PermissionLevel.USER.value)
            requires_approval = boundary.get("requires_approval", False)
            
            # Log check
            self._log_audit_event(
                event_type=AuditEventType.PERMISSION_CHECK,
                action="check_permission",
                resource=f"{action}:{resource}",
                user=user,
                success=True,
                details=f"Level: {level}, Requires approval: {requires_approval}"
            )
            
            return {
                "permitted": not requires_approval,
                "reason": f"Permission level: {level}",
                "requires_approval": requires_approval,
                "level": level
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check permission: {e}")
            return {
                "permitted": False,
                "reason": f"Error checking permission: {e}",
                "requires_approval": True
            }
    
    # =========================================================================
    # Audit Logging
    # =========================================================================
    
    def _log_audit_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource: str,
        user: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[str] = None
    ) -> None:
        """
        Log audit event.
        
        Args:
            event_type: Type of event
            action: Action performed
            resource: Resource accessed
            user: User identifier
            success: Whether action succeeded
            ip_address: Optional IP address
            details: Optional details
        """
        try:
            entry = AuditLogEntry(
                timestamp=datetime.now().isoformat(),
                event_type=event_type.value,
                action=action,
                resource=resource,
                user=user,
                success=success,
                ip_address=ip_address,
                details=details
            )
            
            # Append to audit log
            with open(self.audit_log_file, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    def get_audit_log(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit log entries.
        
        Agent Skill: security.get_audit_log
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            event_type: Filter by event type
            
        Returns:
            dict with 'success' (bool) and 'entries' (list) or 'error' (str)
        """
        try:
            if not self.audit_log_file.exists():
                return {"success": True, "entries": [], "count": 0}
            
            entries = []
            
            with open(self.audit_log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Filter by date
                        if start_date and entry["timestamp"] < start_date:
                            continue
                        if end_date and entry["timestamp"] > end_date:
                            continue
                        
                        # Filter by event type
                        if event_type and entry["event_type"] != event_type:
                            continue
                        
                        entries.append(entry)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Sort by timestamp (newest first)
            entries.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return {
                "success": True,
                "entries": entries,
                "count": len(entries)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get audit log: {e}")
            return {"success": False, "error": str(e)}
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this security manager.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "security.get_credential": self.get_credential,
            "security.set_credential": self.set_credential,
            "security.rotate_credential": self.rotate_credential,
            "security.get_audit_log": self.get_audit_log,
            "security.check_permission": self.check_permission,
        }


# Global instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get or create global Security Manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(
            vault_path=get_settings().VAULT_PATH
        )
    return _security_manager


if __name__ == "__main__":
    # Test Security Manager
    print("=== Security Manager Test ===\n")
    
    settings = get_settings()
    security = SecurityManager(vault_path=settings.VAULT_PATH)
    
    # Test credential storage
    result = security.set_credential(
        name="test_api_key",
        value="sk_test_1234567890"
    )
    if result["success"]:
        print("✓ Credential stored")
    
    # Test credential retrieval
    result = security.get_credential("test_api_key")
    if result["success"]:
        print(f"✓ Credential retrieved: {result['value'][:10]}...")
    
    # Test permission check
    result = security.check_permission(
        action="email.send",
        resource="client@example.com"
    )
    print(f"\n✓ Permission check: {result['permitted']} ({result['reason']})")
    
    # Test audit log
    result = security.get_audit_log()
    if result["success"]:
        print(f"\n✓ Audit log entries: {result['count']}")
        for entry in result["entries"][:5]:
            print(f"  - {entry['timestamp']}: {entry['event_type']} ({entry['action']})")
