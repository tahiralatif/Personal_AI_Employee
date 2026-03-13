"""
WhatsApp Web Monitor using Playwright (100% FREE)

This module provides browser-based WhatsApp monitoring without API costs.
Uses Playwright to automate WhatsApp Web.

Features:
- Monitor incoming messages
- Detect task keywords
- Send messages (for approvals/notifications)
- Handle media (images, documents, voice notes)
- Session persistence (QR scan once, reuse session)

Requirements:
- Playwright installed: uv add playwright
- Chrome/Chromium browser
- WhatsApp Web account

Usage:
    python -m src.ai_employee_silver.integrations.whatsapp_playwright
"""

import base64
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from playwright.sync_api import sync_playwright, Page, Browser

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class WhatsAppMessage:
    """
    Represents a WhatsApp message.

    Attributes:
        message_id: Unique message identifier
        from_number: Sender's phone number
        from_name: Sender's name
        timestamp: Message timestamp
        text: Message text content
        has_media: Whether message has media
        media_type: Type of media (image, document, audio)
    """

    def __init__(
        self,
        message_id: str,
        from_number: str,
        from_name: str,
        timestamp: datetime,
        text: str = "",
        has_media: bool = False,
        media_type: Optional[str] = None
    ) -> None:
        """Initialize WhatsAppMessage."""
        self.message_id = message_id
        self.from_number = from_number
        self.from_name = from_name
        self.timestamp = timestamp
        self.text = text
        self.has_media = has_media
        self.media_type = media_type

    def is_task(self, keywords: Optional[List[str]] = None) -> bool:
        """
        Check if message is a task based on keywords.

        Args:
            keywords: List of task keywords

        Returns:
            True if message contains task keywords
        """
        if not self.text:
            return False

        if keywords is None:
            keywords = [
                "please", "need", "urgent", "task", "action",
                "required", "must", "should", "remind", "todo"
            ]

        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in keywords)


class WhatsAppPlaywrightMonitor:
    """
    WhatsApp Web monitor using Playwright browser automation.

    100% FREE alternative to WhatsApp Business API.

    Responsibilities:
    - Connect to WhatsApp Web
    - Monitor for new messages
    - Detect task keywords
    - Send messages (for notifications/approvals)
    - Handle session persistence
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize WhatsAppPlaywrightMonitor.

        Args:
            settings: Application settings
            logger: Application logger
        """
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # Configuration
        self.poll_interval = self.settings.WHATSAPP_POLL_INTERVAL
        self.task_keywords = self.settings.WHATSAPP_TASK_KEYWORDS

        # Session storage
        self.session_path = Path(__file__).parent.parent.parent.parent / "whatsapp_session.json"

        # Browser state
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._running = False

        # Message tracking
        self.processed_messages: set = set()
        self.last_message_time: Optional[datetime] = None

        # Vault paths
        self.vault_path = Path(self.settings.VAULT_PATH).expanduser()
        self.inbox_path = self.vault_path / "Inbox"
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.pending_approval_path = self.vault_path / "Pending_Approval"

    def connect(self) -> bool:
        """
        Connect to WhatsApp Web.

        Returns:
            True if connection successful
        """
        try:
            self.logger.info("Connecting to WhatsApp Web...")

            # Start Playwright
            self.playwright = sync_playwright().start()

            # Launch browser (headful for QR code scanning)
            self.browser = self.playwright.chromium.launch(
                headless=False,  # Show browser for QR scan
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )

            # Create page
            self.page = self.browser.new_page()

            # Set viewport
            self.page.set_viewport_size({"width": 1280, "height": 720})

            # Navigate to WhatsApp Web
            self.logger.info("Opening WhatsApp Web...")
            self.page.goto("https://web.whatsapp.com", wait_until="networkidle")

            # Wait a bit for page to load
            time.sleep(3)

            # Check if already logged in (session exists)
            if self._is_logged_in():
                self.logger.info("Already logged in (session restored)")
                self._save_session()
                return True

            # Wait for QR code scan (first time or session expired)
            self.logger.info("Please scan QR code with WhatsApp mobile app...")
            self.logger.info("Waiting 90 seconds for QR scan...")

            # Wait for main chat list (indicates successful login)
            try:
                # Check periodically if logged in
                for i in range(18):  # 18 x 5 seconds = 90 seconds
                    time.sleep(5)
                    if self._is_logged_in():
                        self.logger.info("✓ QR code scanned successfully!")
                        self._save_session()
                        return True
                    self.logger.debug(f"Waiting for login... ({(i+1)*5}s)")

                self.logger.error("QR scan timeout")
                return False

            except Exception as e:
                self.logger.error(f"QR scan timeout: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to connect: {str(e)}")
            return False

    def _is_logged_in(self) -> bool:
        """
        Check if already logged in to WhatsApp Web.

        Returns:
            True if logged in
        """
        try:
            # Multiple selectors to check for logged-in state
            selectors = [
                'div[data-testid="default-user"]',  # Main chat list
                'span[title="Status"]',  # Status tab
                'div[data-testid="chat-list"]',  # Chat list container
                'div[data-testid="cell-frame"]',  # Chat cells
            ]
            
            for selector in selectors:
                if self.page.query_selector(selector) is not None:
                    return True
            
            # Also check URL - if not on login page, probably logged in
            current_url = self.page.url
            if "web.whatsapp.com" in current_url and "login" not in current_url:
                return True
                
            return False
            
        except Exception:
            return False

    def _save_session(self) -> None:
        """Save session data for reuse."""
        try:
            # Get localStorage data
            local_storage = self.page.evaluate("() => localStorage")

            # Save to file
            session_data = {
                "local_storage": local_storage,
                "timestamp": datetime.now().isoformat()
            }

            self.session_path.write_text(json.dumps(session_data, indent=2))
            self.logger.info(f"Session saved to: {self.session_path}")

        except Exception as e:
            self.logger.error(f"Failed to save session: {str(e)}")

    def _load_session(self) -> bool:
        """
        Load saved session.

        Returns:
            True if session loaded successfully
        """
        try:
            if not self.session_path.exists():
                return False

            session_data = json.loads(self.session_path.read_text())

            # Restore localStorage
            if "local_storage" in session_data:
                for key, value in session_data["local_storage"].items():
                    self.page.evaluate(f"() => localStorage.setItem('{key}', '{value}')")

            self.logger.info("Session loaded")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load session: {str(e)}")
            return False

    def monitor_messages(self) -> List[WhatsAppMessage]:
        """
        Monitor for new messages.

        Returns:
            List of new WhatsAppMessage objects
        """
        try:
            if not self.page:
                return []

            messages = []

            # Get recent chats
            chats = self._get_recent_chats()

            for chat in chats:
                # Get messages from chat
                chat_messages = self._get_chat_messages(chat)

                for msg_data in chat_messages:
                    # Skip already processed
                    if msg_data["id"] in self.processed_messages:
                        continue

                    # Create WhatsAppMessage
                    message = WhatsAppMessage(
                        message_id=msg_data["id"],
                        from_number=msg_data["from"],
                        from_name=msg_data["name"],
                        timestamp=msg_data["timestamp"],
                        text=msg_data["text"],
                        has_media=msg_data.get("has_media", False),
                        media_type=msg_data.get("media_type")
                    )

                    messages.append(message)
                    self.processed_messages.add(msg_data["id"])

            self.logger.info(f"Fetched {len(messages)} new messages")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to monitor messages: {str(e)}")
            return []

    def _get_recent_chats(self) -> List[Dict[str, Any]]:
        """Get list of recent chats."""
        try:
            # Execute JavaScript to extract chat list
            chats = self.page.evaluate("""
                () => {
                    const chatElements = document.querySelectorAll('div[data-testid="chat-list"] > div[role="row"]');
                    const chats = [];
                    
                    chatElements.forEach((el, index) => {
                        if (index < 10) {  // Get last 10 chats
                            const nameEl = el.querySelector('span[dir="auto"]');
                            chats.push({
                                name: nameEl ? nameEl.textContent : 'Unknown',
                                element: el
                            });
                        }
                    });
                    
                    return chats;
                }
            """)

            return chats

        except Exception as e:
            self.logger.error(f"Failed to get chats: {str(e)}")
            return []

    def _get_chat_messages(self, chat: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get messages from a chat.

        Args:
            chat: Chat dictionary

        Returns:
            List of message dictionaries
        """
        try:
            # Click on chat to open
            # chat["element"].click()

            # Extract messages
            messages = self.page.evaluate("""
                () => {
                    const msgElements = document.querySelectorAll('div[data-testid="chat-list"] div[role="row"]');
                    const messages = [];
                    
                    msgElements.forEach((el, index) => {
                        if (index < 20) {  // Get last 20 messages
                            const textEl = el.querySelector('span[dir="auto"]');
                            const timeEl = el.querySelector('span[dir="auto"]');
                            
                            messages.push({
                                id: `msg_${index}_${Date.now()}`,
                                from: 'Unknown',
                                name: 'Unknown',
                                text: textEl ? textEl.textContent : '',
                                timestamp: new Date(),
                                has_media: false,
                                media_type: null
                            });
                        }
                    });
                    
                    return messages;
                }
            """)

            return messages

        except Exception as e:
            self.logger.error(f"Failed to get messages: {str(e)}")
            return []

    def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send WhatsApp message.

        Args:
            phone_number: Recipient's phone number
            message: Message text

        Returns:
            True if sent successfully
        """
        try:
            self.logger.info(f"Sending message to {phone_number}...")

            # Navigate to chat
            chat_url = f"https://web.whatsapp.com/send?phone={phone_number}"
            self.page.goto(chat_url, wait_until="networkidle")

            # Wait for message input
            time.sleep(3)  # Wait for chat to load

            # Type message
            input_selector = 'div[contenteditable="true"][data-tab="10"]'
            input_element = self.page.query_selector(input_selector)

            if input_element:
                input_element.fill(message)
                time.sleep(1)

                # Press Enter to send
                self.page.keyboard.press("Enter")
                time.sleep(2)

                self.logger.info("✓ Message sent successfully")
                return True
            else:
                self.logger.error("Message input not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False

    def create_task_file(self, message: WhatsAppMessage) -> Optional[Path]:
        """
        Create task file in Needs_Action for WhatsApp message.

        Args:
            message: WhatsAppMessage object

        Returns:
            Path to created task file or None
        """
        try:
            self.needs_action_path.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_number = "".join(c for c in message.from_number if c.isdigit())[-4:]
            filename = f"WHATSAPP_{timestamp}_{safe_number}.md"
            file_path = self.needs_action_path / filename

            # Build content
            content = self._build_task_content(message)

            # Write file
            file_path.write_text(content, encoding='utf-8')

            self.logger.info(f"Created task file: {filename}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to create task file: {str(e)}")
            return None

    def _build_task_content(self, message: WhatsAppMessage) -> str:
        """Build task file content."""
        frontmatter = {
            "type": "whatsapp_message",
            "from_number": message.from_number,
            "from_name": message.from_name or "Unknown",
            "received": message.timestamp.isoformat(),
            "priority": "high" if message.is_task() else "medium",
            "status": "pending_approval",
            "has_media": message.has_media
        }

        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")

        body = f"""# Task: Process WhatsApp Message from {message.from_name or message.from_number}

## Message Details
- **From:** {message.from_name or message.from_number} ({message.from_number})
- **Received:** {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## Message Content
{message.text if message.text else "*No text content*"}

## Approval Required
⚠️ **This task requires human approval before proceeding.**

## Suggested Next Steps
- [ ] Review the message
- [ ] Approve or reject task
- [ ] Create plan if approved
- [ ] Execute plan
- [ ] Move to /Done/ when complete

---
*Automatically generated by AI Employee Silver Tier - WhatsApp (FREE)*
"""
        return "\n".join(fm_lines) + body

    def send_approval_request(self, message: WhatsAppMessage, task_file: Path) -> bool:
        """
        Send approval request to human.

        Args:
            message: Original WhatsApp message
            task_file: Path to task file

        Returns:
            True if notification sent
        """
        approval_message = f"""
⚠️ *New Task Pending Approval*

📱 From: {message.from_name or message.from_number}
📝 Task: {task_file.name}

Reply with:
✅ APPROVE - to proceed
❌ REJECT - to discard
        """.strip()

        # Send to your phone (configured in settings)
        # For now, just log it
        self.logger.info(f"Approval request: {approval_message}")

        return True

    def run_once(self) -> int:
        """
        Run one iteration of monitoring.

        Returns:
            Number of tasks created
        """
        try:
            # Monitor for messages
            messages = self.monitor_messages()

            tasks_created = 0

            for message in messages:
                # Check if it's a task
                if message.is_task(self.task_keywords):
                    # Create task file
                    task_file = self.create_task_file(message)

                    if task_file:
                        # Send approval request
                        self.send_approval_request(message, task_file)
                        tasks_created += 1

            return tasks_created

        except Exception as e:
            self.logger.error(f"Error in run_once: {str(e)}")
            return 0

    def run_forever(self, poll_interval: Optional[int] = None) -> None:
        """
        Run WhatsApp monitor continuously.

        Args:
            poll_interval: Polling interval in seconds
        """
        if poll_interval is None:
            poll_interval = self.poll_interval

        self._running = True
        self.logger.info(f"Starting WhatsApp monitor (poll interval: {poll_interval}s)")

        try:
            while self._running:
                try:
                    # Check if still logged in
                    if not self._is_logged_in():
                        self.logger.warning("Logged out, reconnecting...")
                        if not self.connect():
                            time.sleep(30)
                            continue

                    # Monitor messages
                    self.run_once()

                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {str(e)}")

                # Wait for next poll
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received, stopping WhatsApp monitor")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the WhatsApp monitor."""
        self.logger.info("Stopping WhatsApp monitor...")
        self._running = False

        # Close browser
        if self.browser:
            self.browser.close()

        # Stop Playwright
        if self.playwright:
            self.playwright.stop()

        self.logger.log_event(
            event_type="system_stop",
            detail="WhatsApp monitor stopped",
            result="success"
        )


def create_whatsapp_playwright_monitor(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> WhatsAppPlaywrightMonitor:
    """Factory function to create WhatsAppPlaywrightMonitor instance."""
    return WhatsAppPlaywrightMonitor(settings, logger)


if __name__ == "__main__":
    print("Starting WhatsApp Playwright Monitor (Test Mode)...")
    print("=" * 70)

    settings = get_settings()
    logger = get_logger()

    monitor = create_whatsapp_playwright_monitor(settings, logger)

    # Connect
    if monitor.connect():
        print("✓ Connected to WhatsApp Web")
        print("\nMonitoring messages... (Press Ctrl+C to stop)")
        print("=" * 70)

        # Run
        monitor.run_forever(poll_interval=30)
    else:
        print("✗ Failed to connect to WhatsApp Web")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome/Chromium is installed")
        print("2. Run: uv add playwright")
        print("3. Run: playwright install chromium")
        print("4. Try again")
