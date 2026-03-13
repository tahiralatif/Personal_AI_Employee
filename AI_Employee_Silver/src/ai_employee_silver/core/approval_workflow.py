"""
Enhanced Approval Workflow for AI Employee Silver Tier.

This module implements the Human-in-the-Loop (HITL) approval workflow with
four approval categories: financial, communication, data access, and system.

Agent Skills:
    - approval.request_approval(action, details, category) -> str (approval_id)
    - approval.get_approval_status(approval_id) -> dict
    - approval.approve(approval_id, notes) -> bool
    - approval.reject(approval_id, reason) -> bool
    - approval.list_pending() -> list
    - approval.auto_check_expired() -> int (rejected count)
"""

import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


class ApprovalCategory(Enum):
    """Approval categories per specification."""
    FINANCIAL = "financial"
    COMMUNICATION = "communication"
    DATA_ACCESS = "data_access"
    SYSTEM = "system"


class ApprovalStatus(Enum):
    """Approval status values."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_REJECTED = "auto_rejected"


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment for approval request."""
    financial_risk: str = "low"
    reputation_risk: str = "low"
    security_risk: str = "low"
    overall_risk: str = "low"
    assessment_notes: str = ""


@dataclass
class ApprovalRequest:
    """Represents an approval request."""
    approval_id: str
    action: str
    category: str
    created: str
    expires: str
    status: str = "pending"
    urgency: str = "medium"
    action_details: Optional[Dict[str, Any]] = None
    business_justification: str = ""
    risk_assessment: Optional[RiskAssessment] = None
    requestor: str = "ai_employee"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: str = ""


class ApprovalWorkflow:
    """
    Enhanced Approval Workflow for Human-in-the-Loop operations.
    
    This workflow manages approval requests for sensitive actions across
    four categories: financial, communication, data access, and system.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Approval Workflow.
        
        Args:
            vault_path: Path to the AI Employee vault
            settings: Application settings
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        
        # Approval directories
        self.pending_dir = self.vault_path / "Pending_Approval"
        self.approved_dir = self.vault_path / "Approved"
        self.rejected_dir = self.vault_path / "Rejected"
        
        for dir_path in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Approval timeout (hours)
        self.approval_timeout_hours = getattr(self.settings, 'APPROVAL_TIMEOUT_HOURS', 24)
        
        # Auto-approve low priority
        self.auto_approve_low_priority = getattr(self.settings, 'AUTO_APPROVE_LOW_PRIORITY', False)
        
        # Approval thresholds
        self.financial_threshold = 100.0  # USD - auto-approve below this
        self.payment_recurring_threshold = 50.0  # USD - recurring payments below this auto-approved
        
        # Tracking
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        
        # Load pending approvals
        self._load_pending_approvals()
    
    def _load_pending_approvals(self) -> None:
        """Load pending approvals from disk."""
        try:
            for approval_file in self.pending_dir.glob("APPROVAL_*.md"):
                content = approval_file.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)
                
                if frontmatter.get('status') == 'pending':
                    approval_id = frontmatter.get('approval_id')
                    if approval_id:
                        self.pending_approvals[approval_id] = self._parse_approval_request(frontmatter, content)
            
            self.logger.debug(f"Loaded {len(self.pending_approvals)} pending approvals")
        except Exception as e:
            self.logger.error(f"Failed to load pending approvals: {e}")
    
    def request_approval(
        self,
        action: str,
        category: str,
        action_details: Dict[str, Any],
        business_justification: str,
        urgency: str = "medium",
        approval_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request approval for sensitive action.
        
        Agent Skill: approval.request_approval
        
        Args:
            action: Action type (payment, email, data_access, system_change)
            category: Approval category (financial, communication, data_access, system)
            action_details: Action-specific details
            business_justification: Reason for approval request
            urgency: Urgency level (low, medium, high)
            approval_id: Optional approval ID (auto-generated if None)
            
        Returns:
            dict with 'success' (bool) and 'approval_id' (str) or 'error' (str)
        """
        try:
            self.logger.info(f"Requesting approval for {action} ({category})")
            
            # Generate approval ID if not provided
            if not approval_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                approval_id = f"approval_{timestamp}_{action[:10]}"
            
            # Calculate expiration
            created = datetime.now()
            expires = created + timedelta(hours=self.approval_timeout_hours)
            
            # Perform risk assessment
            risk_assessment = self._assess_risk(category, action_details)
            
            # Create approval request
            request = ApprovalRequest(
                approval_id=approval_id,
                action=action,
                category=category,
                created=created.isoformat(),
                expires=expires.isoformat(),
                status=ApprovalStatus.PENDING.value,
                urgency=urgency,
                action_details=action_details,
                business_justification=business_justification,
                risk_assessment=risk_assessment
            )
            
            # Check for auto-approval
            if self._should_auto_approve(request):
                self.logger.info(f"Auto-approving low-risk request: {approval_id}")
                request.status = ApprovalStatus.APPROVED.value
                request.approved_by = "auto_approval_system"
                request.approved_at = datetime.now().isoformat()
                request.notes = "Auto-approved based on low risk assessment"
            
            # Write approval file
            approval_path = self._write_approval_file(request)
            
            # Track pending approval
            if request.status == ApprovalStatus.PENDING.value:
                self.pending_approvals[approval_id] = request
            
            self.logger.info(f"Approval request created: {approval_id}")
            
            return {
                "success": True,
                "approval_id": approval_id,
                "approval_path": str(approval_path),
                "status": request.status,
                "auto_approved": request.status == ApprovalStatus.APPROVED.value
            }
            
        except Exception as e:
            self.logger.error(f"Failed to request approval: {e}")
            return {"success": False, "error": str(e)}
    
    def _assess_risk(self, category: str, details: Dict[str, Any]) -> RiskAssessment:
        """
        Assess risk for approval request.
        
        Args:
            category: Approval category
            details: Action details
            
        Returns:
            RiskAssessment object
        """
        risk = RiskAssessment()
        
        if category == ApprovalCategory.FINANCIAL.value:
            amount = details.get('amount', 0)
            
            # Financial risk based on amount
            if amount >= 1000:
                risk.financial_risk = RiskLevel.HIGH.value
            elif amount >= 500:
                risk.financial_risk = RiskLevel.MEDIUM.value
            else:
                risk.financial_risk = RiskLevel.LOW.value
            
            # New payee increases risk
            if details.get('is_new_payee', False):
                risk.financial_risk = RiskLevel.MEDIUM.value
                risk.security_risk = RiskLevel.MEDIUM.value
            
            risk.overall_risk = self._calculate_overall_risk(risk)
            risk.assessment_notes = f"Financial amount: ${amount}"
            
        elif category == ApprovalCategory.COMMUNICATION.value:
            recipient_count = details.get('recipient_count', 1)
            is_bulk = details.get('is_bulk', False)
            
            # Reputation risk for bulk communications
            if is_bulk or recipient_count > 50:
                risk.reputation_risk = RiskLevel.HIGH.value
                risk.assessment_notes = "Bulk communication detected"
            elif recipient_count > 10:
                risk.reputation_risk = RiskLevel.MEDIUM.value
            else:
                risk.reputation_risk = RiskLevel.LOW.value
            
            # Sensitive topics increase risk
            if details.get('is_sensitive_topic', False):
                risk.reputation_risk = RiskLevel.HIGH.value
            
            risk.overall_risk = self._calculate_overall_risk(risk)
            
        elif category == ApprovalCategory.DATA_ACCESS.value:
            data_sensitivity = details.get('data_sensitivity', 'low')
            
            if data_sensitivity == 'high':
                risk.security_risk = RiskLevel.HIGH.value
                risk.financial_risk = RiskLevel.MEDIUM.value
            elif data_sensitivity == 'medium':
                risk.security_risk = RiskLevel.MEDIUM.value
            else:
                risk.security_risk = RiskLevel.LOW.value
            
            risk.overall_risk = self._calculate_overall_risk(risk)
            risk.assessment_notes = f"Data sensitivity: {data_sensitivity}"
            
        elif category == ApprovalCategory.SYSTEM.value:
            change_scope = details.get('change_scope', 'minor')
            
            if change_scope == 'major':
                risk.security_risk = RiskLevel.HIGH.value
                risk.reputation_risk = RiskLevel.MEDIUM.value
            elif change_scope == 'moderate':
                risk.security_risk = RiskLevel.MEDIUM.value
            else:
                risk.security_risk = RiskLevel.LOW.value
            
            risk.overall_risk = self._calculate_overall_risk(risk)
            risk.assessment_notes = f"Change scope: {change_scope}"
        
        return risk
    
    def _calculate_overall_risk(self, risk: RiskAssessment) -> str:
        """Calculate overall risk from individual risk factors."""
        risk_levels = {
            RiskLevel.LOW.value: 1,
            RiskLevel.MEDIUM.value: 2,
            RiskLevel.HIGH.value: 3,
            RiskLevel.CRITICAL.value: 4
        }
        
        max_risk = max(
            risk_levels.get(risk.financial_risk, 1),
            risk_levels.get(risk.reputation_risk, 1),
            risk_levels.get(risk.security_risk, 1)
        )
        
        for level, value in risk_levels.items():
            if value == max_risk:
                return level
        
        return RiskLevel.LOW.value
    
    def _should_auto_approve(self, request: ApprovalRequest) -> bool:
        """
        Check if request should be auto-approved.
        
        Args:
            request: Approval request
            
        Returns:
            True if should auto-approve
        """
        if not self.auto_approve_low_priority:
            return False
        
        # Auto-approve low urgency with low risk
        if request.urgency == 'low' and request.risk_assessment:
            if request.risk_assessment.overall_risk == RiskLevel.LOW.value:
                return True
        
        # Auto-approve small financial amounts
        if request.category == ApprovalCategory.FINANCIAL.value:
            amount = request.action_details.get('amount', 0)
            if amount < self.financial_threshold:
                return True
        
        return False
    
    def _write_approval_file(self, request: ApprovalRequest) -> Path:
        """
        Write approval request to markdown file.
        
        Args:
            request: Approval request object
            
        Returns:
            Path to created file
        """
        # Generate filename
        safe_action = self._sanitize_filename(request.action)
        filename = f"APPROVAL_{request.approval_id}_{safe_action}.md"
        
        # Write to pending folder
        filepath = self.pending_dir / filename
        
        # Build YAML frontmatter
        frontmatter = {
            "type": "approval_request",
            "approval_id": request.approval_id,
            "action": request.action,
            "category": request.category,
            "created": request.created,
            "expires": request.expires,
            "status": request.status,
            "urgency": request.urgency,
            "requestor": request.requestor,
            "risk_level": request.risk_assessment.overall_risk if request.risk_assessment else "unknown"
        }
        
        # Build content
        content = self._build_approval_content(request, frontmatter)
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        
        return filepath
    
    def _build_approval_content(
        self,
        request: ApprovalRequest,
        frontmatter: Dict[str, Any]
    ) -> str:
        """
        Build approval file markdown content.
        
        Args:
            request: Approval request object
            frontmatter: YAML frontmatter dictionary
            
        Returns:
            Complete markdown content string
        """
        # Format frontmatter
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.extend(["---", ""])
        
        # Build body
        body = []
        
        # Header
        body.append(f"# Approval Request: {request.action.title().replace('_', ' ')}\n")
        
        # Action Details
        body.append("## Action Details\n")
        body.append(f"- **Type:** {request.action}")
        body.append(f"- **Category:** {request.category}")
        body.append(f"- **Urgency:** {request.urgency}")
        
        # Add action-specific details
        if request.action_details:
            body.append("\n### Details\n")
            for key, value in request.action_details.items():
                body.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        # Business Justification
        body.append("\n## Business Justification\n")
        body.append(f"{request.business_justification}\n")
        
        # Risk Assessment
        if request.risk_assessment:
            body.append("\n## Risk Assessment\n")
            body.append(f"- **Financial Risk:** {request.risk_assessment.financial_risk}")
            body.append(f"- **Reputation Risk:** {request.risk_assessment.reputation_risk}")
            body.append(f"- **Security Risk:** {request.risk_assessment.security_risk}")
            body.append(f"- **Overall Risk:** {request.risk_assessment.overall_risk}")
            if request.risk_assessment.assessment_notes:
                body.append(f"\n**Notes:** {request.risk_assessment.assessment_notes}")
        
        # Approval Options
        body.append("\n## Approval Options\n")
        body.append("1. **Approve**: Move file to `/Approved/` folder")
        body.append("2. **Reject**: Move file to `/Rejected/` folder with reason")
        body.append("3. **Modify**: Edit this file and move to `/Pending_Approval/` again")
        
        # Auto-Reject Warning
        body.append("\n## Auto-Reject\n")
        body.append(f"This request will auto-reject on **{request.expires}** if no action taken.\n")
        
        # Approval Log
        if request.approved_by:
            body.append("\n## Approval Decision\n")
            body.append(f"- **Status:** {request.status}")
            body.append(f"- **Approved By:** {request.approved_by}")
            body.append(f"- **Approved At:** {request.approved_at}")
            if request.rejection_reason:
                body.append(f"- **Rejection Reason:** {request.rejection_reason}")
            if request.notes:
                body.append(f"- **Notes:** {request.notes}")
        
        # Footer
        body.append("\n---")
        body.append(f"*Generated by AI Employee Silver Tier - Approval Workflow*")
        body.append(f"*Created: {request.created}*")
        
        return "\n".join(fm_lines + body)
    
    def get_approval_status(self, approval_id: str) -> Dict[str, Any]:
        """
        Get approval request status.
        
        Agent Skill: approval.get_approval_status
        
        Args:
            approval_id: Approval request ID
            
        Returns:
            dict with 'success' (bool) and status info or 'error' (str)
        """
        try:
            # Check pending approvals
            if approval_id in self.pending_approvals:
                request = self.pending_approvals[approval_id]
                return {
                    "success": True,
                    "approval_id": approval_id,
                    "status": request.status,
                    "category": request.category,
                    "created": request.created,
                    "expires": request.expires,
                    "urgency": request.urgency,
                    "risk_level": request.risk_assessment.overall_risk if request.risk_assessment else "unknown"
                }
            
            # Search in files
            for folder in [self.pending_dir, self.approved_dir, self.rejected_dir]:
                for approval_file in folder.glob(f"APPROVAL_{approval_id}_*.md"):
                    content = approval_file.read_text(encoding='utf-8')
                    frontmatter = self._parse_frontmatter(content)
                    
                    return {
                        "success": True,
                        "approval_id": approval_id,
                        "status": frontmatter.get('status', 'unknown'),
                        "category": frontmatter.get('category', 'unknown'),
                        "file_path": str(approval_file)
                    }
            
            return {"success": False, "error": f"Approval not found: {approval_id}"}
            
        except Exception as e:
            self.logger.error(f"Failed to get approval status: {e}")
            return {"success": False, "error": str(e)}
    
    def approve(
        self,
        approval_id: str,
        approved_by: str = "human_user",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Approve pending request.
        
        Agent Skill: approval.approve
        
        Args:
            approval_id: Approval request ID
            approved_by: Person/system approving
            notes: Optional approval notes
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            self.logger.info(f"Approving request: {approval_id}")
            
            # Find approval file
            approval_file = self._find_approval_file(approval_id)
            
            if not approval_file:
                return {"success": False, "error": "Approval request not found"}
            
            # Read current content
            content = approval_file.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)
            body = content.split("---", 2)[-1].strip()
            
            # Update frontmatter
            frontmatter['status'] = ApprovalStatus.APPROVED.value
            frontmatter['approved_by'] = approved_by
            frontmatter['approved_at'] = datetime.now().isoformat()
            
            # Rebuild file
            fm_lines = ["---"]
            for key, value in frontmatter.items():
                fm_lines.append(f"{key}: {value}")
            fm_lines.extend(["---", "", body])
            
            # Add approval decision to body
            decision_text = f"""
## Approval Decision
- **Status:** {ApprovalStatus.APPROVED.value}
- **Approved By:** {approved_by}
- **Approved At:** {datetime.now().isoformat()}
- **Notes:** {notes}
"""
            updated_content = "\n".join(fm_lines) + decision_text
            
            # Move to approved folder
            dest_path = self.approved_dir / approval_file.name
            dest_path.write_text(updated_content, encoding='utf-8')
            approval_file.unlink()
            
            # Remove from pending
            if approval_id in self.pending_approvals:
                del self.pending_approvals[approval_id]
            
            self.logger.info(f"Approval approved: {approval_id}")
            
            return {"success": True, "approved_by": approved_by}
            
        except Exception as e:
            self.logger.error(f"Failed to approve: {e}")
            return {"success": False, "error": str(e)}
    
    def reject(
        self,
        approval_id: str,
        reason: str,
        rejected_by: str = "human_user"
    ) -> Dict[str, Any]:
        """
        Reject pending request.
        
        Agent Skill: approval.reject
        
        Args:
            approval_id: Approval request ID
            reason: Rejection reason
            rejected_by: Person/system rejecting
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            self.logger.info(f"Rejecting request: {approval_id}")
            
            # Find approval file
            approval_file = self._find_approval_file(approval_id)
            
            if not approval_file:
                return {"success": False, "error": "Approval request not found"}
            
            # Read current content
            content = approval_file.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)
            body = content.split("---", 2)[-1].strip()
            
            # Update frontmatter
            frontmatter['status'] = ApprovalStatus.REJECTED.value
            frontmatter['rejected_by'] = rejected_by
            frontmatter['rejected_at'] = datetime.now().isoformat()
            frontmatter['rejection_reason'] = reason
            
            # Rebuild file
            fm_lines = ["---"]
            for key, value in frontmatter.items():
                fm_lines.append(f"{key}: {value}")
            fm_lines.extend(["---", "", body])
            
            # Add rejection decision to body
            decision_text = f"""
## Rejection Decision
- **Status:** {ApprovalStatus.REJECTED.value}
- **Rejected By:** {rejected_by}
- **Rejected At:** {datetime.now().isoformat()}
- **Reason:** {reason}
"""
            updated_content = "\n".join(fm_lines) + decision_text
            
            # Move to rejected folder
            dest_path = self.rejected_dir / approval_file.name
            dest_path.write_text(updated_content, encoding='utf-8')
            approval_file.unlink()
            
            # Remove from pending
            if approval_id in self.pending_approvals:
                del self.pending_approvals[approval_id]
            
            self.logger.info(f"Approval rejected: {approval_id}")
            
            return {"success": True, "rejected_by": rejected_by}
            
        except Exception as e:
            self.logger.error(f"Failed to reject: {e}")
            return {"success": False, "error": str(e)}
    
    def list_pending(self) -> List[Dict[str, Any]]:
        """
        List all pending approvals.
        
        Agent Skill: approval.list_pending
        
        Returns:
            List of pending approval info dictionaries
        """
        pending = []
        
        for approval_id, request in self.pending_approvals.items():
            pending.append({
                "approval_id": approval_id,
                "action": request.action,
                "category": request.category,
                "created": request.created,
                "expires": request.expires,
                "urgency": request.urgency,
                "risk_level": request.risk_assessment.overall_risk if request.risk_assessment else "unknown"
            })
        
        # Sort by urgency and expiration
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        pending.sort(key=lambda x: (urgency_order.get(x['urgency'], 1), x['expires']))
        
        return pending
    
    def auto_check_expired(self) -> int:
        """
        Check and auto-reject expired approvals.
        
        Agent Skill: approval.auto_check_expired
        
        Returns:
            Number of approvals auto-rejected
        """
        rejected_count = 0
        now = datetime.now()
        
        # Check pending approvals
        expired_ids = []
        
        for approval_id, request in list(self.pending_approvals.items()):
            expires = datetime.fromisoformat(request.expires)
            
            if now > expires:
                expired_ids.append(approval_id)
        
        # Auto-reject expired
        for approval_id in expired_ids:
            result = self.reject(
                approval_id=approval_id,
                reason="Auto-rejected: Approval timeout expired",
                rejected_by="auto_reject_system"
            )
            
            if result["success"]:
                rejected_count += 1
                self.logger.info(f"Auto-rejected expired approval: {approval_id}")
        
        return rejected_count
    
    def _find_approval_file(self, approval_id: str) -> Optional[Path]:
        """Find approval file by ID."""
        for folder in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            for approval_file in folder.glob(f"APPROVAL_{approval_id}_*.md"):
                return approval_file
        return None
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content."""
        try:
            if not content.startswith("---"):
                return {}
            
            parts = content.split("---", 2)
            if len(parts) < 2:
                return {}
            
            fm_content = parts[1].strip()
            return yaml.safe_load(fm_content) or {}
            
        except Exception as e:
            self.logger.error(f"Failed to parse frontmatter: {e}")
            return {}
    
    def _parse_approval_request(
        self,
        frontmatter: Dict[str, Any],
        content: str
    ) -> ApprovalRequest:
        """Parse approval request from frontmatter and content."""
        return ApprovalRequest(
            approval_id=frontmatter.get('approval_id', ''),
            action=frontmatter.get('action', ''),
            category=frontmatter.get('category', ''),
            created=frontmatter.get('created', ''),
            expires=frontmatter.get('expires', ''),
            status=frontmatter.get('status', 'pending'),
            urgency=frontmatter.get('urgency', 'medium'),
            approved_by=frontmatter.get('approved_by'),
            approved_at=frontmatter.get('approved_at'),
            rejection_reason=frontmatter.get('rejection_reason')
        )
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize string for filename."""
        if not filename:
            return ""
        unsafe = '<>:"/\\|?*'
        for char in unsafe:
            filename = filename.replace(char, '_')
        return filename.strip(' _.')[:30]
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this workflow.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "approval.request_approval": self.request_approval,
            "approval.get_approval_status": self.get_approval_status,
            "approval.approve": self.approve,
            "approval.reject": self.reject,
            "approval.list_pending": self.list_pending,
            "approval.auto_check_expired": self.auto_check_expired,
        }


# Global instance
_approval_workflow: Optional[ApprovalWorkflow] = None


def get_approval_workflow() -> ApprovalWorkflow:
    """Get or create global Approval Workflow instance."""
    global _approval_workflow
    if _approval_workflow is None:
        _approval_workflow = ApprovalWorkflow(
            vault_path=get_settings().VAULT_PATH
        )
    return _approval_workflow


if __name__ == "__main__":
    # Test Approval Workflow
    print("=== Approval Workflow Test ===\n")
    
    settings = get_settings()
    workflow = ApprovalWorkflow(vault_path=settings.VAULT_PATH)
    
    # Test financial approval
    result = workflow.request_approval(
        action="payment",
        category="financial",
        action_details={
            "amount": 500.00,
            "recipient": "Vendor ABC",
            "is_new_payee": True
        },
        business_justification="Payment for Q1 consulting services",
        urgency="high"
    )
    
    if result["success"]:
        print(f"✓ Approval requested: {result['approval_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Auto-approved: {result.get('auto_approved', False)}")
        
        # Get status
        status = workflow.get_approval_status(result["approval_id"])
        if status["success"]:
            print(f"  Risk Level: {status['risk_level']}")
        
        # List pending
        pending = workflow.list_pending()
        print(f"\n✓ Pending approvals: {len(pending)}")
        
        # Test approve
        if not result.get('auto_approved'):
            approve_result = workflow.approve(
                approval_id=result["approval_id"],
                approved_by="test_user",
                notes="Approved for testing"
            )
            if approve_result["success"]:
                print(f"✓ Approval approved")
    else:
        print(f"✗ Failed to request approval: {result.get('error')}")
