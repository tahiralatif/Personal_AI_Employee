"""
WhatsApp Business API integration for Silver Tier AI Employee.

This module implements the WhatsAppMonitor class that:
- Connects to WhatsApp Business API
- Monitors incoming messages via polling or webhooks
- Detects task keywords in messages
- Creates task files in Needs_Action/
- Handles media (images, documents, voice notes)
- Implements retry logic and error handling
"""

import base64
import hashlib
import hmac
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class WhatsAppMessage:
    """
    Represents a WhatsApp message with metadata and media.

    Attributes:
        message_id: WhatsApp message ID
        from_number: Sender's phone number
        from_name: Sender's name (if available)
        timestamp: Message timestamp
        text: Message text content
        media_type: Type of media (image, document, audio, video)
        media_url: URL to download media
        media_id: WhatsApp media ID
    """

    def __init__(
        self,
        message_id: str,
        from_number: str,
        from_name: Optional[str],
        timestamp: datetime,
        text: Optional[str] = None,
        media_type: Optional[str] = None,
        media_url: Optional[str] = None,
        media_id: Optional[str] = None
    ) -> None:
        """
        Initialize WhatsAppMessage.

        Args:
            message_id: WhatsApp message ID
            from_number: Sender's phone number
            from_name: Sender's name (if available)
            timestamp: Message timestamp
            text: Message text content
            media_type: Type of media
            media_url: URL to download media
            media_id: WhatsApp media ID
        """
        self.message_id = message_id
        self.from_number = from_number
        self.from_name = from_name
        self.timestamp = timestamp
        self.text = text
        self.media_type = media_type
        self.media_url = media_url
        self.media_id = media_id

    def has_media(self) -> bool:
        """Check if message has media."""
        return self.media_id is not None

    def is_task(self, keywords: Optional[List[str]] = None) -> bool:
        """
        Check if message is a task based on keywords.

        Args:
            keywords: List of task keywords to check

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


class WhatsAppMonitor:
    """
    Monitors WhatsApp Business API for incoming messages.

    Responsibilities:
    - WhatsApp Business API authentication
    - Poll messages every 30 seconds (or webhook)
    - Detect task keywords in messages
    - Download and save media to Inbox/
    - Create task files in Needs_Action/
    - Handle rate limits and errors
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize WhatsAppMonitor.

        Args:
            settings: Application settings
            logger: Application logger
        """
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # WhatsApp API configuration
        self.business_account_id = self.settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        self.access_token = self.settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = self.settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = self.settings.WHATSAPP_API_VERSION
        self.webhook_verify_token = self.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        self.poll_interval = self.settings.WHATSAPP_POLL_INTERVAL
        self.task_keywords = self.settings.WHATSAPP_TASK_KEYWORDS

        # API base URL
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        # State tracking
        self.processed_messages: set = set()
        self.last_message_timestamp: Optional[datetime] = None

        # Retry configuration
        self.max_retries = self.settings.MAX_RETRY_ATTEMPTS
        self.initial_delay = self.settings.RETRY_INITIAL_DELAY
        self.max_delay = self.settings.RETRY_MAX_DELAY
        self.use_exponential_backoff = self.settings.RETRY_EXPONENTIAL_BACKOFF

        # Running state
        self._running = False

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription challenge.

        Args:
            mode: Webhook mode (should be "subscribe")
            token: Verify token
            challenge: Challenge string to return

        Returns:
            Challenge string if verification successful, None otherwise
        """
        if mode == "subscribe" and token == self.webhook_verify_token:
            self.logger.info("Webhook verification successful")
            return challenge
        else:
            self.logger.warning("Webhook verification failed")
            return None

    def handle_webhook(self, payload: Dict[str, Any]) -> List[WhatsAppMessage]:
        """
        Handle incoming webhook payload.

        Args:
            payload: Webhook payload from WhatsApp

        Returns:
            List of WhatsAppMessage objects
        """
        try:
            messages = []

            # Extract messages from payload
            if "entry" not in payload:
                return messages

            for entry in payload["entry"]:
                if "changes" not in entry:
                    continue

                for change in entry["changes"]:
                    if change.get("field") != "messages":
                        continue

                    value = change.get("value", {})
                    if "messages" not in value:
                        continue

                    for msg in value["messages"]:
                        whatsapp_msg = self._parse_message(msg, value.get("contacts", []))
                        if whatsapp_msg:
                            messages.append(whatsapp_msg)

            self.logger.info(f"Received {len(messages)} messages from webhook")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to handle webhook: {str(e)}")
            return []

    def _parse_message(
        self,
        msg: Dict[str, Any],
        contacts: List[Dict[str, Any]]
    ) -> Optional[WhatsAppMessage]:
        """
        Parse WhatsApp message into WhatsAppMessage object.

        Args:
            msg: Raw message data
            contacts: List of contact information

        Returns:
            WhatsAppMessage object or None
        """
        try:
            message_id = msg.get("id", "")
            from_number = msg.get("from", "")
            timestamp_str = msg.get("timestamp", "")
            timestamp = datetime.fromtimestamp(int(timestamp_str)) if timestamp_str else datetime.now()

            # Find sender name from contacts
            from_name = None
            for contact in contacts:
                if contact.get("wa_id") == from_number:
                    from_name = contact.get("profile", {}).get("name")
                    break

            # Extract text
            text = None
            if "text" in msg:
                text = msg["text"].get("body")

            # Extract media
            media_type = None
            media_id = None
            media_url = None

            if "image" in msg:
                media_type = "image"
                media_id = msg["image"].get("id")
            elif "document" in msg:
                media_type = "document"
                media_id = msg["document"].get("id")
            elif "audio" in msg:
                media_type = "audio"
                media_id = msg["audio"].get("id")
            elif "video" in msg:
                media_type = "video"
                media_id = msg["video"].get("id")

            return WhatsAppMessage(
                message_id=message_id,
                from_number=from_number,
                from_name=from_name,
                timestamp=timestamp,
                text=text,
                media_type=media_type,
                media_id=media_id,
                media_url=media_url
            )

        except Exception as e:
            self.logger.error(f"Failed to parse message: {str(e)}")
            return None

    def poll_messages(self) -> List[WhatsAppMessage]:
        """
        Poll WhatsApp Business API for new messages.

        Returns:
            List of WhatsAppMessage objects
        """
        try:
            self.logger.debug("Polling for new messages...")

            # Get messages from API
            endpoint = f"{self.base_url}/{self.phone_number_id}/messages"
            params = {
                "fields": "from,id,timestamp,text,image,document,audio,video",
                "limit": "50"
            }

            response = self._retry_request("GET", endpoint, params=params)

            if not response or "messages" not in response:
                return []

            messages = []
            contacts_map = {}

            for msg in response["messages"]:
                # Skip already processed
                if msg["id"] in self.processed_messages:
                    continue

                # Get sender info
                from_number = msg.get("from", "")
                if from_number not in contacts_map:
                    contacts_map[from_number] = self._get_contact_info(from_number)

                whatsapp_msg = self._parse_message(msg, [])
                if whatsapp_msg:
                    messages.append(whatsapp_msg)
                    self.processed_messages.add(msg["id"])

            self.logger.info(f"Fetched {len(messages)} new messages")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to poll messages: {str(e)}")
            return []

    def _get_contact_info(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get contact information for a phone number.

        Args:
            phone_number: WhatsApp phone number

        Returns:
            Contact info dict or None
        """
        try:
            # Note: WhatsApp Business API doesn't provide direct contact lookup
            # This would need to be implemented with your own contact database
            return {"wa_id": phone_number, "profile": {"name": phone_number}}
        except Exception as e:
            self.logger.error(f"Failed to get contact info: {str(e)}")
            return None

    def _retry_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: URL to request
            **kwargs: Additional request parameters

        Returns:
            Response JSON or None
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code

                # Rate limit (429)
                if status_code == 429:
                    self.logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    if self.use_exponential_backoff:
                        delay = min(delay * 2, self.max_delay)
                    continue

                # Server error (5xx)
                elif 500 <= status_code < 600:
                    self.logger.warning(f"Server error {status_code}, retrying in {delay}s...")
                    time.sleep(delay)
                    if self.use_exponential_backoff:
                        delay = min(delay * 2, self.max_delay)
                    continue

                # Client error (4xx) - don't retry
                else:
                    self.logger.error(f"HTTP error {status_code}: {str(e)}")
                    return None

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                time.sleep(delay)
                if self.use_exponential_backoff:
                    delay = min(delay * 2, self.max_delay)

        # All retries failed
        error_msg = f"All {self.max_retries} retries failed"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        self.logger.error(error_msg)
        return None

    def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Download media from WhatsApp.

        Args:
            media_id: WhatsApp media ID

        Returns:
            Media bytes or None
        """
        try:
            # Get media URL
            endpoint = f"{self.base_url}/{media_id}"
            params = {"fields": "url"}

            response = self._retry_request("GET", endpoint, params=params)
            if not response or "url" not in response:
                return None

            media_url = response["url"]

            # Download media
            media_response = self.session.get(media_url, timeout=30)
            media_response.raise_for_status()

            return media_response.content

        except Exception as e:
            self.logger.error(f"Failed to download media: {str(e)}")
            return None

    def save_media(
        self,
        media_content: bytes,
        media_type: str,
        from_number: str,
        timestamp: datetime
    ) -> Optional[Path]:
        """
        Save media to Inbox folder.

        Args:
            media_content: Media bytes
            media_type: Media type (image, document, etc.)
            from_number: Sender's phone number
            timestamp: Message timestamp

        Returns:
            Path to saved file or None
        """
        try:
            inbox_path = Path(self.settings.VAULT_PATH).expanduser() / "Inbox"
            inbox_path.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            safe_number = "".join(c for c in from_number if c.isdigit())

            # Determine file extension
            ext_map = {
                "image": ".jpg",
                "document": ".bin",
                "audio": ".ogg",
                "video": ".mp4"
            }
            ext = ext_map.get(media_type, ".bin")

            filename = f"WHATSAPP_{timestamp_str}_{safe_number}{ext}"
            file_path = inbox_path / filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(media_content)

            self.logger.info(f"Saved media: {filename}")
            self.logger.log_event(
                event_type="media_saved",
                detail=f"Saved {media_type} from {from_number}",
                result="success",
                file_reference=str(file_path)
            )

            return file_path

        except Exception as e:
            self.logger.error(f"Failed to save media: {str(e)}")
            return None

    def create_task_file(
        self,
        message: WhatsAppMessage,
        saved_media: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Create task file in Needs_Action for WhatsApp message.

        Args:
            message: WhatsAppMessage object
            saved_media: Path to saved media file

        Returns:
            Path to created task file or None
        """
        try:
            needs_action_path = Path(self.settings.VAULT_PATH).expanduser() / "Needs_Action"
            needs_action_path.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_number = "".join(c for c in message.from_number if c.isdigit())[-4:]
            filename = f"WHATSAPP_{timestamp}_{safe_number}.md"
            file_path = needs_action_path / filename

            # Build content
            content = self._build_task_content(message, saved_media)

            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Created task file: {filename}")
            self.logger.log_event(
                event_type="task_file_created",
                detail=f"Created task from WhatsApp message from {message.from_number}",
                result="success",
                file_reference=str(file_path)
            )

            return file_path

        except Exception as e:
            self.logger.error(f"Failed to create task file: {str(e)}")
            return None

    def _build_task_content(
        self,
        message: WhatsAppMessage,
        saved_media: Optional[Path]
    ) -> str:
        """
        Build task file content.

        Args:
            message: WhatsAppMessage object
            saved_media: Path to saved media

        Returns:
            Task file content as string
        """
        # Build YAML frontmatter
        frontmatter = {
            "type": "whatsapp_message",
            "from_number": message.from_number,
            "from_name": message.from_name or "Unknown",
            "received": message.timestamp.isoformat(),
            "message_id": message.message_id,
            "priority": "high" if message.is_task(self.task_keywords) else "medium",
            "status": "pending",
            "has_media": message.has_media(),
            "media_type": message.media_type
        }

        # Format frontmatter
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")

        # Build body
        media_line = f"- `{saved_media.name}`" if saved_media else "No media"

        body = f"""# Task: Process WhatsApp Message from {message.from_name or message.from_number}

## Message Details
- **From:** {message.from_name or message.from_number} ({message.from_number})
- **Received:** {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **WhatsApp Message ID:** {message.message_id}

## Message Content
{message.text if message.text else "*No text content*"}

## Media
{media_line}

## Suggested Next Steps
- [ ] Review the message content
- [ ] Respond to sender if needed
- [ ] Create a plan in /Plans/
- [ ] Execute the plan
- [ ] Move to /Done/ when complete

---
*Automatically generated by AI Employee Silver Tier - WhatsApp Integration*
"""
        return "\n".join(fm_lines) + body

    def process_messages(self, messages: List[WhatsAppMessage]) -> int:
        """
        Process list of WhatsApp messages.

        Args:
            messages: List of WhatsAppMessage objects

        Returns:
            Number of messages processed
        """
        processed_count = 0

        for message in messages:
            self.logger.info(f"Processing message from {message.from_number}")

            saved_media = None

            # Download and save media if present
            if message.has_media() and message.media_id:
                media_content = self.download_media(message.media_id)
                if media_content:
                    saved_media = self.save_media(
                        media_content,
                        message.media_type or "unknown",
                        message.from_number,
                        message.timestamp
                    )

            # Create task file if message is a task or has media
            if message.is_task(self.task_keywords) or saved_media:
                self.create_task_file(message, saved_media)
                processed_count += 1
            else:
                self.logger.debug(f"Message not a task, skipping: {message.message_id}")

        return processed_count

    def run_once(self) -> int:
        """
        Run one iteration of WhatsApp monitoring.

        Returns:
            Number of messages processed
        """
        try:
            # Poll for messages
            messages = self.poll_messages()

            if not messages:
                return 0

            # Process messages
            return self.process_messages(messages)

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
                    # Process messages
                    self.run_once()

                except Exception as e:
                    self.logger.error(f"Error in polling loop: {str(e)}")

                # Wait for next poll
                self.logger.debug(f"Waiting {poll_interval}s for next poll...")
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received, stopping WhatsApp monitor")
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stop the WhatsApp monitor.
        """
        self.logger.info("Stopping WhatsApp monitor...")
        self._running = False

        self.logger.log_event(
            event_type="system_stop",
            detail="WhatsApp monitor stopped",
            result="success"
        )


def create_whatsapp_monitor(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> WhatsAppMonitor:
    """
    Factory function to create a WhatsAppMonitor instance.

    Args:
        settings: Optional settings instance
        logger: Optional logger instance

    Returns:
        Configured WhatsAppMonitor instance
    """
    return WhatsAppMonitor(settings, logger)


if __name__ == "__main__":
    # Example usage / testing
    print("Starting WhatsApp Monitor (Test Mode)...")

    settings = get_settings()
    logger = get_logger()

    monitor = create_whatsapp_monitor(settings, logger)

    # Check if configured
    if settings.is_whatsapp_configured():
        print("✓ WhatsApp API configured")

        # Test polling
        messages = monitor.poll_messages()
        print(f"✓ Fetched {len(messages)} messages")

        # Test processing
        processed = monitor.process_messages(messages)
        print(f"✓ Processed {processed} messages")

        print("\nTo run continuously, use: python -m src.ai_employee_silver.main start whatsapp")
    else:
        print("✗ WhatsApp API not configured")
        print("  Please check your credentials in .env")
