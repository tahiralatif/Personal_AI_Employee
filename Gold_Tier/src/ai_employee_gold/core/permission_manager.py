"""Permission Manager for Gold Tier AI Employee.

This module provides permission management:
- Action categorization
- Threshold-based approval
- Risk assessment
- Permission boundaries

Part of Phase 7: Security Enhancements.
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from ..config.settings import settings
from .audit_logger import audit_logger

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level for actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionCategory(Enum):
    """Action category for permissions."""
    # Odoo Actions
    ODOO_CREATE_INVOICE = "odoo.create_invoice"
    ODOO_RECORD_PAYMENT = "odoo.record_payment"
    ODOO_CREATE_EXPENSE = "odoo.create_expense"
    
    # Social Media Actions
    FACEBOOK_POST = "facebook.post"
    FACEBOOK_DELETE_POST = "facebook.delete_post"
    INSTAGRAM_POST = "instagram.post"
    INSTAGRAM_DELETE_MEDIA = "instagram.delete_media"
    TWITTER_TWEET = "twitter.tweet"
    TWITTER_DELETE_TWEET = "twitter.delete_tweet"
    
    # System Actions
    CREDENTIAL_ACCESS = "security.credential_access"
    AUDIT_LOG_ACCESS = "security.audit_log_access"
    SYSTEM_CONFIG = "system.config"


@dataclass
class PermissionRule:
    """Permission rule for an action."""
    action: ActionCategory
    requires_approval: bool
    approval_threshold: float  # Monetary threshold
    risk_level: RiskLevel
    allowed_roles: List[str]
    max_per_day: Optional[int] = None


class PermissionManager:
    """Permission manager with threshold-based approval."""

    def __init__(self):
        """Initialize permission manager."""
        self.rules = self._load_rules()
        logger.info("Permission manager initialized")

    def _load_rules(self) -> Dict[ActionCategory, PermissionRule]:
        """Load permission rules."""
        return {
            # Odoo Actions
            ActionCategory.ODOO_CREATE_INVOICE: PermissionRule(
                action=ActionCategory.ODOO_CREATE_INVOICE,
                requires_approval=True,
                approval_threshold=500.0,  # Auto-approve < $500
                risk_level=RiskLevel.MEDIUM,
                allowed_roles=["admin", "finance"],
                max_per_day=50
            ),
            ActionCategory.ODOO_RECORD_PAYMENT: PermissionRule(
                action=ActionCategory.ODOO_RECORD_PAYMENT,
                requires_approval=True,
                approval_threshold=1000.0,  # Auto-approve < $1000
                risk_level=RiskLevel.HIGH,
                allowed_roles=["admin", "finance"],
                max_per_day=20
            ),
            ActionCategory.ODOO_CREATE_EXPENSE: PermissionRule(
                action=ActionCategory.ODOO_CREATE_EXPENSE,
                requires_approval=True,
                approval_threshold=200.0,  # Auto-approve < $200
                risk_level=RiskLevel.LOW,
                allowed_roles=["admin", "finance", "employee"],
                max_per_day=10
            ),
            
            # Social Media Actions
            ActionCategory.FACEBOOK_POST: PermissionRule(
                action=ActionCategory.FACEBOOK_POST,
                requires_approval=False,
                approval_threshold=0.0,
                risk_level=RiskLevel.LOW,
                allowed_roles=["admin", "marketing"],
                max_per_day=5
            ),
            ActionCategory.FACEBOOK_DELETE_POST: PermissionRule(
                action=ActionCategory.FACEBOOK_DELETE_POST,
                requires_approval=True,
                approval_threshold=0.0,
                risk_level=RiskLevel.HIGH,
                allowed_roles=["admin"],
                max_per_day=10
            ),
            ActionCategory.INSTAGRAM_POST: PermissionRule(
                action=ActionCategory.INSTAGRAM_POST,
                requires_approval=False,
                approval_threshold=0.0,
                risk_level=RiskLevel.LOW,
                allowed_roles=["admin", "marketing"],
                max_per_day=10
            ),
            ActionCategory.INSTAGRAM_DELETE_MEDIA: PermissionRule(
                action=ActionCategory.INSTAGRAM_DELETE_MEDIA,
                requires_approval=True,
                approval_threshold=0.0,
                risk_level=RiskLevel.HIGH,
                allowed_roles=["admin"],
                max_per_day=10
            ),
            ActionCategory.TWITTER_TWEET: PermissionRule(
                action=ActionCategory.TWITTER_TWEET,
                requires_approval=False,
                approval_threshold=0.0,
                risk_level=RiskLevel.LOW,
                allowed_roles=["admin", "marketing"],
                max_per_day=300  # Twitter API limit
            ),
            ActionCategory.TWITTER_DELETE_TWEET: PermissionRule(
                action=ActionCategory.TWITTER_DELETE_TWEET,
                requires_approval=True,
                approval_threshold=0.0,
                risk_level=RiskLevel.MEDIUM,
                allowed_roles=["admin"],
                max_per_day=100
            ),
            
            # Security Actions
            ActionCategory.CREDENTIAL_ACCESS: PermissionRule(
                action=ActionCategory.CREDENTIAL_ACCESS,
                requires_approval=True,
                approval_threshold=0.0,
                risk_level=RiskLevel.CRITICAL,
                allowed_roles=["admin"],
                max_per_day=20
            ),
            ActionCategory.AUDIT_LOG_ACCESS: PermissionRule(
                action=ActionCategory.AUDIT_LOG_ACCESS,
                requires_approval=False,
                approval_threshold=0.0,
                risk_level=RiskLevel.MEDIUM,
                allowed_roles=["admin", "auditor"],
                max_per_day=None
            ),
        }

    def check_permission(self, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if action is permitted.
        
        Args:
            action: Action name (e.g., "odoo.create_invoice")
            context: Action context (amount, role, etc.)
        
        Returns:
            Permission result with approval requirement
        """
        context = context or {}
        
        # Find matching rule
        action_enum = self._get_action_enum(action)
        if not action_enum or action_enum not in self.rules:
            return {
                "permitted": False,
                "reason": f"Unknown action: {action}",
                "requires_approval": True,
                "risk_level": RiskLevel.CRITICAL.value
            }
        
        rule = self.rules[action_enum]
        
        # Check role
        role = context.get("role", "user")
        if role not in rule.allowed_roles:
            return {
                "permitted": False,
                "reason": f"Role '{role}' not allowed for {action}",
                "requires_approval": True,
                "risk_level": rule.risk_level.value
            }
        
        # Check amount threshold
        amount = context.get("amount", 0.0)
        requires_approval = (
            rule.requires_approval and 
            amount >= rule.approval_threshold
        )
        
        # Check daily limit
        if rule.max_per_day:
            daily_count = self._get_daily_count(action)
            if daily_count >= rule.max_per_day:
                return {
                    "permitted": False,
                    "reason": f"Daily limit reached for {action} ({daily_count}/{rule.max_per_day})",
                    "requires_approval": True,
                    "risk_level": rule.risk_level.value
                }
        
        # Perform risk assessment
        risk_assessment = self._assess_risk(action, context)
        
        return {
            "permitted": not requires_approval,
            "action": action,
            "requires_approval": requires_approval,
            "approval_threshold": rule.approval_threshold,
            "amount": amount,
            "risk_level": risk_assessment["level"],
            "risk_factors": risk_assessment["factors"],
            "recommendations": risk_assessment["recommendations"]
        }

    def _get_action_enum(self, action: str) -> Optional[ActionCategory]:
        """Get action enum from string."""
        try:
            return ActionCategory(action)
        except ValueError:
            return None

    def _get_daily_count(self, action: str) -> int:
        """Get count of action today (from audit log)."""
        # Query audit log for today's actions
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            from .audit_logger import audit_logger
            entries = audit_logger.get_audit_log(
                start_date=today,
                end_date=today,
                action_type=action
            )
            return len(entries)
        except Exception:
            return 0

    def _assess_risk(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk level for action.
        
        Args:
            action: Action name
            context: Action context
        
        Returns:
            Risk assessment with level and factors
        """
        factors = []
        recommendations = []
        level = RiskLevel.LOW
        
        # Financial risk
        amount = context.get("amount", 0.0)
        if amount > 1000:
            factors.append(f"High amount: ${amount:,.2f}")
            level = RiskLevel.HIGH
        elif amount > 500:
            factors.append(f"Medium amount: ${amount:,.2f}")
            level = RiskLevel.MEDIUM
        
        # Reputation risk (social media)
        if action in ["facebook.post", "twitter.tweet", "instagram.post"]:
            if context.get("public", True):
                factors.append("Public post - reputation risk")
                recommendations.append("Review content for brand compliance")
                if level == RiskLevel.LOW:
                    level = RiskLevel.MEDIUM
        
        # Security risk
        if "credential" in action or "password" in action:
            factors.append("Security-sensitive action")
            recommendations.append("Verify user identity")
            level = RiskLevel.CRITICAL
        
        # Compliance risk
        if context.get("compliance_required"):
            factors.append("Compliance requirements apply")
            recommendations.append("Ensure regulatory compliance")
            if level == RiskLevel.LOW:
                level = RiskLevel.MEDIUM
        
        return {
            "level": level.value,
            "factors": factors,
            "recommendations": recommendations
        }

    def get_risk_level(self, action: str) -> str:
        """Get risk level for action.
        
        Args:
            action: Action name
        
        Returns:
            Risk level string
        """
        action_enum = self._get_action_enum(action)
        if action_enum and action_enum in self.rules:
            return self.rules[action_enum].risk_level.value
        return RiskLevel.CRITICAL.value

    def get_approval_threshold(self, action: str) -> float:
        """Get approval threshold for action.
        
        Args:
            action: Action name
        
        Returns:
            Approval threshold amount
        """
        action_enum = self._get_action_enum(action)
        if action_enum and action_enum in self.rules:
            return self.rules[action_enum].approval_threshold
        return 0.0


# Global permission manager instance
permission_manager = PermissionManager()
