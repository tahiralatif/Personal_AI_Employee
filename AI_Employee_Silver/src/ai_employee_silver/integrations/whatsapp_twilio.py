"""
WhatsApp Monitor using Twilio API (Production-Ready)

This module provides official WhatsApp Business API integration via Twilio.
Much more reliable than browser automation.

Features:
- Official WhatsApp Business API
- Webhook support for real-time messages
- Polling fallback
- Task keyword detection
- Media handling
- Two-way messaging

Requirements:
- Twilio account (free sandbox available)
- uv add twilio

Usage:
    python -m src.ai_employee_silver.integrations.whatsapp_twilio
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class WhatsAppMessage:
    """Represents a WhatsApp message."""

    def __init__(
        self,
        message_id: str,
        from_number: str,
        timestamp: datetime,
        text: str = "",
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> None:
        self.message_id = message_id
        self.from_number = from_number
        self.timestamp = timestamp
        self.text = text
        self.media_url = media_url
        self.media_type = media_type

    def is_task(self, keywords: Optional[List[str]] = None) -> bool:
        """Check if message is a task."""
        if not self.text:
            return False

        if keywords is None:
            keywords = ["please", "need", "urgent", "task", "action", "required"]

        return any(k in self.text.lower() for k in keywords)


class WhatsAppTwilioMonitor:
    """
    WhatsApp monitor using Twilio API (Production-Ready).

    Much more reliable than Playwright browser automation.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # Twilio configuration
        self.account_sid = self.settings.TWILIO_ACCOUNT_SID
        self.auth_token = self.settings.TWILIO_AUTH_TOKEN
        self.whatsapp_number = self.settings.TWILIO_WHATSAPP_NUMBER

        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)

        # Configuration
        self.poll_interval = self.settings.WHATSAPP_POLL_INTERVAL
        self.task_keywords = self.settings.WHATSAPP_TASK_KEYWORDS

        # Message tracking
        self.processed_messages: set = set()

        # Vault paths
        self.vault_path = Path(self.settings.VAULT_PATH).expanduser()
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.pending_approval_path = self.vault_path / "Pending_Approval"

        self._running = False

    def test_connection(self) -> bool:
        """Test Twilio connection."""
        try:
            # Fetch account info
            account = self.client.api.accounts(self.account_sid).fetch()
            self.logger.info(f"✓ Connected to Twilio: {account.friendly_name}")
            return True
        except Exception as e:
            self.logger.error(f"✗ Twilio connection failed: {str(e)}")
            return False

    def fetch_messages(self, limit: int = 50) -> List[WhatsAppMessage]:
        """Fetch recent WhatsApp messages."""
        try:
            messages = []

            # Fetch messages sent TO the Twilio number (incoming messages from users)
            twilio_messages = self.client.messages.list(
                to=f"whatsapp:{self.whatsapp_number}",
                limit=limit
            )

            for msg in twilio_messages:
                # Skip already processed
                if msg.sid in self.processed_messages:
                    continue

                # Create WhatsAppMessage
                message = WhatsAppMessage(
                    message_id=msg.sid,
                    from_number=msg.from_.replace("whatsapp:", ""),
                    timestamp=msg.date_sent,
                    text=msg.body,
                    media_url=msg.media_sid if msg.num_media > 0 else None,
                    media_type="image" if msg.num_media > 0 else None
                )

                messages.append(message)
                self.processed_messages.add(msg.sid)

            self.logger.info(f"Fetched {len(messages)} new messages")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to fetch messages: {str(e)}")
            return []

    def send_message(self, to_number: str, message: str) -> bool:
        """Send WhatsApp message."""
        try:
            self.logger.info(f"Sending message to {to_number}...")

            message = self.client.messages.create(
                from_=f"whatsapp:{self.whatsapp_number}",
                body=message,
                to=f"whatsapp:{to_number}"
            )

            self.logger.info(f"✓ Message sent: {message.sid}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False

    def create_task_file(self, message: WhatsAppMessage) -> Optional[Path]:
        """Create task file for WhatsApp message."""
        try:
            self.needs_action_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_number = "".join(c for c in message.from_number if c.isdigit())[-4:]
            filename = f"WHATSAPP_{timestamp}_{safe_number}.md"
            file_path = self.needs_action_path / filename

            content = self._build_task_content(message)
            file_path.write_text(content, encoding='utf-8')

            self.logger.info(f"✓ Created task file: {filename}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to create task file: {str(e)}")
            return None

    def _build_task_content(self, message: WhatsAppMessage) -> str:
        """Build task file content."""
        frontmatter = {
            "type": "whatsapp_message",
            "from_number": message.from_number,
            "received": message.timestamp.isoformat(),
            "priority": "high" if message.is_task() else "medium",
            "status": "pending_approval",
            "has_media": message.media_url is not None
        }

        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.append("---\n")

        body = f"""# Task: Process WhatsApp Message

## Message Details
- **From:** {message.from_number}
- **Received:** {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## Message Content
{message.text if message.text else "*No text content*"}

## Approval Required
⚠️ **This task requires human approval before proceeding.**

## Suggested Next Steps
- [ ] Review the message
- [ ] Approve or reject task
- [ ] Execute if approved
- [ ] Move to /Done/ when complete

---
*Generated by AI Employee - Twilio WhatsApp Integration*
"""
        return "\n".join(fm_lines) + body

    def send_approval_notification(self, message: WhatsAppMessage, task_file: Path) -> bool:
        """Send approval notification to user."""
        notification = f"""
⚠️ New Task Pending Approval

📱 From: {message.from_number}
📝 Task: {task_file.name}

Reply: APPROVE or REJECT
        """.strip()

        # Send to your phone (configure in .env)
        your_number = getattr(self.settings, 'YOUR_PHONE_NUMBER', None)
        if your_number:
            return self.send_message(your_number, notification)
        return False

    def run_once(self) -> int:
        """Run one iteration of monitoring."""
        try:
            messages = self.fetch_messages()
            tasks_created = 0

            for message in messages:
                if message.is_task(self.task_keywords):
                    task_file = self.create_task_file(message)
                    if task_file:
                        self.send_approval_notification(message, task_file)
                        tasks_created += 1

            return tasks_created

        except Exception as e:
            self.logger.error(f"Error in run_once: {str(e)}")
            return 0

    def run_forever(self, poll_interval: Optional[int] = None) -> None:
        """Run WhatsApp monitor continuously."""
        if poll_interval is None:
            poll_interval = self.poll_interval

        self._running = True
        self.logger.info(f"Starting Twilio WhatsApp monitor (interval: {poll_interval}s)")

        try:
            while self._running:
                self.run_once()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            self.logger.info("Stopping WhatsApp monitor...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the monitor."""
        self._running = False
        self.logger.info("Twilio WhatsApp monitor stopped")


def create_whatsapp_twilio_monitor(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> WhatsAppTwilioMonitor:
    """Factory function."""
    return WhatsAppTwilioMonitor(settings, logger)


if __name__ == "__main__":
    print("Starting Twilio WhatsApp Monitor (Test Mode)...")
    print("=" * 70)

    settings = get_settings()
    logger = get_logger()

    monitor = create_whatsapp_twilio_monitor(settings, logger)

    # Test connection
    if monitor.test_connection():
        print("✓ Connected to Twilio")
        print("\nMonitoring WhatsApp messages... (Press Ctrl+C to stop)")
        print("=" * 70)
        monitor.run_forever(poll_interval=30)
    else:
        print("✗ Failed to connect to Twilio")
        print("\nCheck your Twilio credentials in .env")
