"""
Approval Workflow Manager

This module implements human-in-the-loop approval system.
Before any action is taken, human approval is required.

Features:
- Move tasks to Pending_Approval/
- Send approval notifications
- Monitor for approval responses
- Execute approved tasks
- Archive rejected tasks

Workflow:
1. Task detected → Needs_Action/
2. Move to Pending_Approval/
3. Notify human (WhatsApp/Email)
4. Wait for approval/rejection
5. If approved → Execute → Done/
6. If rejected → Archive → Rejected/
"""

import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class ApprovalRequest:
    """
    Represents an approval request.

    Attributes:
        task_file: Path to task file
        requested_at: When approval was requested
        status: pending, approved, rejected
        approved_by: Who approved
        approved_at: When approved
        response: Approval response text
    """

    def __init__(self, task_file: Path) -> None:
        """Initialize ApprovalRequest."""
        self.task_file = task_file
        self.requested_at = datetime.now()
        self.status = "pending"
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
        self.response: Optional[str] = None

    def approve(self, approved_by: str = "human") -> None:
        """Mark as approved."""
        self.status = "approved"
        self.approved_by = approved_by
        self.approved_at = datetime.now()

    def reject(self, approved_by: str = "human") -> None:
        """Mark as rejected."""
        self.status = "rejected"
        self.approved_by = approved_by
        self.approved_at = datetime.now()

    def is_expired(self, timeout_hours: int = 24) -> bool:
        """Check if approval request has expired."""
        expiry = self.requested_at + timedelta(hours=timeout_hours)
        return datetime.now() > expiry


class ApprovalManager:
    """
    Manages approval workflow.

    Responsibilities:
    - Move tasks to Pending_Approval/
    - Send approval notifications
    - Monitor for approval responses
    - Process approved tasks
    - Archive rejected tasks
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize ApprovalManager.

        Args:
            settings: Application settings
            logger: Application logger
        """
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # Configuration
        self.approval_required = True  # Always require approval
        self.approval_timeout_hours = 24
        self.auto_approve_low_priority = False

        # Vault paths
        self.vault_path = Path(self.settings.VAULT_PATH).expanduser()
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.pending_approval_path = self.vault_path / "Pending_Approval"
        self.approved_path = self.vault_path / "Approved"
        self.rejected_path = self.vault_path / "Rejected"
        self.done_path = self.vault_path / "Done"

        # Ensure directories exist
        self._ensure_directories()

        # Active approval requests
        self.active_requests: Dict[str, ApprovalRequest] = {}

        # Notification settings
        self.notification_phone: Optional[str] = None  # Your phone for WhatsApp
        self.notification_email: Optional[str] = None  # Your email

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for path in [
            self.pending_approval_path,
            self.approved_path,
            self.rejected_path
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def request_approval(self, task_file: Path) -> Optional[ApprovalRequest]:
        """
        Request approval for a task.

        Args:
            task_file: Path to task file

        Returns:
            ApprovalRequest object or None
        """
        try:
            self.logger.info(f"Requesting approval for: {task_file.name}")

            # Move to Pending_Approval
            dest_path = self.pending_approval_path / task_file.name

            if task_file.exists():
                shutil.move(str(task_file), str(dest_path))
                self.logger.info(f"Moved to Pending_Approval: {task_file.name}")

            # Create approval request
            request = ApprovalRequest(dest_path)
            self.active_requests[dest_path.name] = request

            # Send notification
            self._send_approval_notification(request)

            return request

        except Exception as e:
            self.logger.error(f"Failed to request approval: {str(e)}")
            return None

    def _send_approval_notification(self, request: ApprovalRequest) -> bool:
        """
        Send approval notification to human.

        Args:
            request: ApprovalRequest object

        Returns:
            True if notification sent
        """
        try:
            # Read task file to get details
            content = request.task_file.read_text(encoding='utf-8')

            # Extract key info
            task_name = request.task_file.stem
            task_type = "Task"

            if "type: whatsapp_message" in content:
                task_type = "WhatsApp Message"
            elif "type: gmail_email" in content:
                task_type = "Gmail Email"
            elif "type: scheduled_task" in content:
                task_type = "Scheduled Task"
            elif "type: linkedin_post" in content:
                task_type = "LinkedIn Post"

            # Build notification message
            message = f"""
⚠️ *New Task Pending Approval*

📋 Type: {task_type}
📁 File: {task_name}
⏰ Time: {request.requested_at.strftime('%Y-%m-%d %H:%M')}

Please review and respond:
✅ APPROVE - to proceed with this task
❌ REJECT - to discard this task

This request will expire in {self.approval_timeout_hours} hours.
            """.strip()

            # Send via WhatsApp (if configured)
            if self.notification_phone:
                self._send_whatsapp_notification(self.notification_phone, message)

            # Send via Email (if configured)
            if self.notification_email:
                self._send_email_notification(self.notification_email, task_name, message)

            # Log notification
            self.logger.info(f"Approval notification sent for: {task_name}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False

    def _send_whatsapp_notification(self, phone: str, message: str) -> bool:
        """Send WhatsApp notification."""
        try:
            # Import WhatsApp Playwright monitor
            from .whatsapp_playwright import create_whatsapp_playwright_monitor

            # Create temporary monitor
            monitor = create_whatsapp_playwright_monitor(self.settings, self.logger)

            # Connect (assumes session already exists)
            if monitor.connect():
                # Send message
                success = monitor.send_message(phone, message)
                monitor.stop()
                return success

            return False

        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp notification: {str(e)}")
            return False

    def _send_email_notification(self, email: str, subject: str, message: str) -> bool:
        """Send email notification."""
        try:
            # For now, just log it
            # TODO: Implement email sending via Gmail API
            self.logger.info(f"Email notification would be sent to: {email}")
            self.logger.info(f"Subject: {subject}")
            self.logger.info(f"Message: {message}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
            return False

    def check_approval_status(self, request: ApprovalRequest) -> str:
        """
        Check approval status for a request.

        Args:
            request: ApprovalRequest object

        Returns:
            'pending', 'approved', 'rejected', or 'expired'
        """
        try:
            # Check if expired
            if request.is_expired(self.approval_timeout_hours):
                request.status = "expired"
                return "expired"

            # Check for approval response in vault
            # Look for response file or message
            response = self._check_for_response(request)

            if response:
                if response.lower() in ["approve", "approved", "yes", "✅"]:
                    request.approve()
                    return "approved"
                elif response.lower() in ["reject", "rejected", "no", "❌"]:
                    request.reject()
                    return "rejected"

            return "pending"

        except Exception as e:
            self.logger.error(f"Failed to check approval status: {str(e)}")
            return "pending"

    def _check_for_response(self, request: ApprovalRequest) -> Optional[str]:
        """
        Check for approval response.

        Looks for:
        - Response files in vault
        - WhatsApp messages with approval keywords

        Args:
            request: ApprovalRequest object

        Returns:
            Response text or None
        """
        try:
            # Check for response file
            response_file = request.task_file.parent / f"{request.task_file.stem}_response.txt"

            if response_file.exists():
                response = response_file.read_text().strip()
                response_file.unlink()  # Delete after reading
                return response

            # TODO: Check WhatsApp messages for approval responses
            # This would integrate with WhatsApp monitor

            return None

        except Exception as e:
            self.logger.error(f"Failed to check for response: {str(e)}")
            return None

    def process_approved_task(self, request: ApprovalRequest) -> bool:
        """
        Process an approved task.

        Args:
            request: ApprovalRequest object

        Returns:
            True if processed successfully
        """
        try:
            self.logger.info(f"Processing approved task: {request.task_file.name}")

            # Move to Approved/ folder
            approved_path = self.approved_path / request.task_file.name
            shutil.move(str(request.task_file), str(approved_path))

            self.logger.info(f"Moved to Approved: {request.task_file.name}")

            # TODO: Trigger AI agent to execute the task
            # For now, just log it
            self.logger.info(f"Task ready for execution: {request.task_file.name}")

            # After execution, move to Done/
            # This would be done by the AI agent

            return True

        except Exception as e:
            self.logger.error(f"Failed to process approved task: {str(e)}")
            return False

    def process_rejected_task(self, request: ApprovalRequest) -> bool:
        """
        Process a rejected task.

        Args:
            request: ApprovalRequest object

        Returns:
            True if processed successfully
        """
        try:
            self.logger.info(f"Processing rejected task: {request.task_file.name}")

            # Move to Rejected/ folder
            rejected_path = self.rejected_path / request.task_file.name
            shutil.move(str(request.task_file), str(rejected_path))

            self.logger.info(f"Moved to Rejected: {request.task_file.name}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to process rejected task: {str(e)}")
            return False

    def process_expired_task(self, request: ApprovalRequest) -> bool:
        """
        Process an expired task.

        Args:
            request: ApprovalRequest object

        Returns:
            True if processed successfully
        """
        try:
            self.logger.warning(f"Task expired: {request.task_file.name}")

            # Move to Rejected/ folder
            rejected_path = self.rejected_path / request.task_file.name
            shutil.move(str(request.task_file), str(rejected_path))

            # Send expiry notification
            self._send_expiry_notification(request)

            return True

        except Exception as e:
            self.logger.error(f"Failed to process expired task: {str(e)}")
            return False

    def _send_expiry_notification(self, request: ApprovalRequest) -> None:
        """Send notification that task has expired."""
        message = f"""
⚠️ *Task Expired*

📁 File: {request.task_file.name}
⏰ Expired at: {request.approved_at}

This task has been automatically rejected due to no response.
        """.strip()

        if self.notification_phone:
            self._send_whatsapp_notification(self.notification_phone, message)

    def run_once(self) -> Dict[str, int]:
        """
        Run one iteration of approval processing.

        Returns:
            Dictionary with counts: {'approved': X, 'rejected': Y, 'expired': Z}
        """
        results = {
            "approved": 0,
            "rejected": 0,
            "expired": 0
        }

        try:
            # Check all pending tasks
            if not self.pending_approval_path.exists():
                return results

            for task_file in self.pending_approval_path.glob("*.md"):
                # Get or create approval request
                if task_file.name not in self.active_requests:
                    request = ApprovalRequest(task_file)
                    request.requested_at = datetime.fromtimestamp(task_file.stat().st_mtime)
                    self.active_requests[task_file.name] = request
                else:
                    request = self.active_requests[task_file.name]

                # Check status
                status = self.check_approval_status(request)

                # Process based on status
                if status == "approved":
                    if self.process_approved_task(request):
                        results["approved"] += 1
                        del self.active_requests[task_file.name]

                elif status == "rejected":
                    if self.process_rejected_task(request):
                        results["rejected"] += 1
                        del self.active_requests[task_file.name]

                elif status == "expired":
                    if self.process_expired_task(request):
                        results["expired"] += 1
                        del self.active_requests[task_file.name]

            return results

        except Exception as e:
            self.logger.error(f"Error in approval processing: {str(e)}")
            return results

    def run_forever(self, check_interval: int = 60) -> None:
        """
        Run approval manager continuously.

        Args:
            check_interval: Check interval in seconds
        """
        self.logger.info(f"Starting approval manager (check interval: {check_interval}s)")

        try:
            while True:
                results = self.run_once()

                # Log results
                if any(v > 0 for v in results.values()):
                    self.logger.info(f"Approval results: {results}")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("Approval manager stopped")

    def get_pending_count(self) -> int:
        """Get count of pending approvals."""
        if not self.pending_approval_path.exists():
            return 0

        return len(list(self.pending_approval_path.glob("*.md")))

    def get_status(self) -> Dict[str, Any]:
        """Get approval manager status."""
        return {
            "pending_count": self.get_pending_count(),
            "active_requests": len(self.active_requests),
            "timeout_hours": self.approval_timeout_hours,
            "notification_phone": self.notification_phone,
            "notification_email": self.notification_email
        }


def create_approval_manager(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> ApprovalManager:
    """Factory function to create ApprovalManager instance."""
    return ApprovalManager(settings, logger)


if __name__ == "__main__":
    print("Starting Approval Manager (Test Mode)...")
    print("=" * 70)

    settings = get_settings()
    logger = get_logger()

    manager = create_approval_manager(settings, logger)

    # Set notification phone (YOUR phone number)
    manager.notification_phone = "+92XXXXXXXXXX"  # Replace with your number

    print(f"✓ Approval manager started")
    print(f"✓ Pending approvals: {manager.get_pending_count()}")
    print(f"✓ Notifications to: {manager.notification_phone}")
    print("\nMonitoring for approval responses... (Press Ctrl+C to stop)")
    print("=" * 70)

    # Run
    manager.run_forever(check_interval=30)
