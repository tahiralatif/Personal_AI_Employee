"""Security Agent for Gold Tier AI Employee.

This agent provides security capabilities:
- Credential management
- Permission checking
- Audit log access
- Security monitoring

Part of Phase 7: Security Enhancements.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .credential_manager import credential_manager, CredentialManager
from .permission_manager import permission_manager, PermissionManager, RiskLevel
from .audit_logger import audit_logger
from .vault_manager import vault

logger = logging.getLogger(__name__)


class SecurityAgent:
    """Autonomous Security Agent.

    This agent specializes in security tasks:
    - Manage credentials (get, set, rotate)
    - Check permissions
    - Access audit logs
    - Monitor security events
    """

    def __init__(self):
        """Initialize Security Agent."""
        self.name = "SecurityAgent"
        self.version = "1.0.0"
        self.domain = "system"
        self.subdomain = "security"

        # Components
        self.credential_manager = credential_manager
        self.permission_manager = permission_manager
        self.audit_logger = audit_logger
        self.vault = vault

        # Statistics
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()

        logger.info(f"Security Agent initialized: {self.name} v{self.version}")

    # ==================== AGENT SKILLS ====================

    def get_credential(self, name: str) -> Optional[str]:
        """Agent Skill: Get encrypted credential.

        Args:
            name: Credential name (e.g., "facebook_access_token")

        Returns:
            Credential value or None

        Example:
            >>> agent.get_credential("facebook_access_token")
            "EAAB..."
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Getting credential: {name}")
            value = self.credential_manager.get_credential(name)

            if value:
                self.successful_actions += 1
                logger.info(f"Credential '{name}' retrieved successfully")
            else:
                self.failed_actions += 1
                logger.warning(f"Credential '{name}' not found or expired")

            return value
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error getting credential: {e}")
            return None

    def set_credential(self, name: str, value: str, 
                      expires_in_days: Optional[int] = None) -> bool:
        """Agent Skill: Set encrypted credential.

        Args:
            name: Credential name
            value: Credential value
            expires_in_days: Days until expiration

        Returns:
            True if successful

        Example:
            >>> agent.set_credential("facebook_access_token", "EAAB...", expires_in_days=60)
            True
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Setting credential: {name}")
            success = self.credential_manager.set_credential(
                name=name,
                value=value,
                expires_in_days=expires_in_days
            )

            if success:
                self.successful_actions += 1
                logger.info(f"Credential '{name}' set successfully")
            else:
                self.failed_actions += 1
                logger.error(f"Failed to set credential '{name}'")

            return success
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error setting credential: {e}")
            return False

    def rotate_credential(self, name: str, new_value: str) -> bool:
        """Agent Skill: Rotate credential.

        Args:
            name: Credential name
            new_value: New credential value

        Returns:
            True if successful

        Example:
            >>> agent.rotate_credential("facebook_access_token", "new_token...")
            True
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Rotating credential: {name}")
            success = self.credential_manager.rotate_credential(
                name=name,
                value=new_value
            )

            if success:
                self.successful_actions += 1
                logger.info(f"Credential '{name}' rotated successfully")
            else:
                self.failed_actions += 1
                logger.error(f"Failed to rotate credential '{name}'")

            return success
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error rotating credential: {e}")
            return False

    def check_permission(self, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Agent Skill: Check if action is permitted.

        Args:
            action: Action name (e.g., "odoo.create_invoice")
            context: Action context (amount, role, etc.)

        Returns:
            Permission result

        Example:
            >>> agent.check_permission("odoo.create_invoice", {"amount": 600, "role": "admin"})
            {
                "permitted": False,
                "requires_approval": True,
                "risk_level": "medium"
            }
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Checking permission for: {action}")
            result = self.permission_manager.check_permission(action, context)

            self.successful_actions += 1
            logger.info(f"Permission check for '{action}': {result['permitted']}")

            return result
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error checking permission: {e}")
            return {
                "permitted": False,
                "error": str(e)
            }

    def get_audit_log(self, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     action_type: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Agent Skill: Get audit log entries.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            action_type: Filter by action type
            limit: Maximum entries to return

        Returns:
            List of audit log entries

        Example:
            >>> agent.get_audit_log(action_type="odoo.create_invoice", limit=10)
            [{...}, {...}]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Getting audit log: {action_type or 'all'}")
            entries = self.audit_logger.get_audit_log(
                start_date=start_date,
                end_date=end_date,
                action_type=action_type,
                limit=limit
            )

            self.successful_actions += 1
            logger.info(f"Retrieved {len(entries)} audit log entries")

            return entries
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error getting audit log: {e}")
            return []

    def get_expiring_credentials(self, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """Agent Skill: Get credentials expiring soon.

        Args:
            days_threshold: Days until expiration to flag

        Returns:
            List of expiring credentials

        Example:
            >>> agent.get_expiring_credentials(days_threshold=7)
            [
                {
                    "name": "facebook_access_token",
                    "expires_at": "2026-03-20",
                    "days_until_expiry": 5
                }
            ]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Getting expiring credentials (threshold: {days_threshold} days)")
            expiring = self.credential_manager.get_expiring_credentials(days_threshold)

            self.successful_actions += 1
            logger.info(f"Found {len(expiring)} expiring credentials")

            return expiring
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error getting expiring credentials: {e}")
            return []

    def get_security_summary(self, period: str = "week") -> Dict[str, Any]:
        """Agent Skill: Get security summary.

        Args:
            period: Time period (day, week, month)

        Returns:
            Security summary

        Example:
            >>> agent.get_security_summary(period="week")
            {
                "period": "week",
                "total_actions": 150,
                "failed_actions": 5,
                "expiring_credentials": 2,
                "permission_denials": 3
            }
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Getting security summary for {period}")

            # Get expiring credentials
            expiring = self.get_expiring_credentials()

            # Get failed actions from audit log
            failed_actions = self.audit_logger.get_audit_log(
                action_type="*",
                limit=1000
            )
            failed_count = sum(1 for entry in failed_actions if entry.get("result") == "failed")

            summary = {
                "period": period,
                "total_actions": self.total_actions,
                "successful_actions": self.successful_actions,
                "failed_actions": self.failed_actions,
                "expiring_credentials": len(expiring),
                "expiring_credentials_list": expiring,
                "audit_log_failures": failed_count
            }

            self.successful_actions += 1
            logger.info(f"Security summary generated for {period}")

            return summary
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error getting security summary: {e}")
            return {
                "error": str(e)
            }


# Global security agent instance
security_agent = SecurityAgent()
