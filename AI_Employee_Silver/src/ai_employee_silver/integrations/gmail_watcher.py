"""
Gmail integration for Silver Tier AI Employee.

This module implements the GmailWatcher class that:
- Connects to Gmail API using OAuth 2.0
- Polls for new emails every 60 seconds
- Extracts attachments and saves to Inbox/
- Creates action files with email metadata
- Handles rate limits and API errors gracefully
"""

import base64
import os
import time
from datetime import datetime
from email import message_from_bytes
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


# Gmail API Scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Token file path (stored in project root, outside vault)
TOKEN_FILE = "token.json"


class GmailAttachment:
    """
    Represents an attachment from a Gmail message.

    Attributes:
        filename: Name of the attachment file
        mime_type: MIME type of the attachment
        size: Size in bytes
        data: Base64 encoded attachment data
    """

    def __init__(
        self,
        filename: str,
        mime_type: str,
        size: int,
        data: str
    ) -> None:
        """
        Initialize GmailAttachment.

        Args:
            filename: Name of the attachment file
            mime_type: MIME type of the attachment
            size: Size in bytes
            data: Base64 encoded attachment data
        """
        self.filename = filename
        self.mime_type = mime_type
        self.size = size
        self.data = data

    def decode_data(self) -> bytes:
        """
        Decode base64 data to bytes.

        Returns:
            Decoded bytes
        """
        # Gmail uses URL-safe base64 encoding
        return base64.urlsafe_b64decode(self.data)


class GmailMessage:
    """
    Represents a Gmail message with metadata and attachments.

    Attributes:
        message_id: Gmail message ID
        thread_id: Gmail thread ID
        subject: Email subject
        sender: Email sender
        date: Email date
        body: Email body (plain text)
        attachments: List of GmailAttachment objects
    """

    def __init__(
        self,
        message_id: str,
        thread_id: str,
        subject: str,
        sender: str,
        date: datetime,
        body: str,
        attachments: List[GmailAttachment]
    ) -> None:
        """
        Initialize GmailMessage.

        Args:
            message_id: Gmail message ID
            thread_id: Gmail thread ID
            subject: Email subject
            sender: Email sender
            date: Email date
            body: Email body (plain text)
            attachments: List of GmailAttachment objects
        """
        self.message_id = message_id
        self.thread_id = thread_id
        self.subject = subject
        self.sender = sender
        self.date = date
        self.body = body
        self.attachments = attachments

    def has_attachments(self) -> bool:
        """
        Check if message has attachments.

        Returns:
            True if message has attachments, False otherwise
        """
        return len(self.attachments) > 0


class GmailWatcher:
    """
    Watches Gmail account for new emails with attachments.

    Responsibilities:
    - OAuth 2.0 authentication
    - Poll Gmail API every 60 seconds
    - Extract attachments from emails
    - Save attachments to Inbox/ folder
    - Create action files with email metadata
    - Handle rate limits and errors
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize GmailWatcher.

        Args:
            settings: Application settings (uses global if None)
            logger: Application logger (uses global if None)
        """
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # Gmail API service
        self.service = None
        self.creds = None

        # State tracking
        self.last_message_id: Optional[str] = None
        self.processed_messages: set = set()

        # Retry configuration
        self.max_retries = self.settings.MAX_RETRY_ATTEMPTS
        self.initial_delay = self.settings.RETRY_INITIAL_DELAY
        self.max_delay = self.settings.RETRY_MAX_DELAY
        self.use_exponential_backoff = self.settings.RETRY_EXPONENTIAL_BACKOFF

        # Running state
        self._running = False

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.info("Authenticating with Gmail API...")

            # Check if credentials are configured
            if not self.settings.is_gmail_configured():
                self.logger.error("Gmail API credentials not configured")
                return False

            # Get token file path
            token_path = Path(__file__).parent.parent.parent.parent / TOKEN_FILE

            # Load existing credentials
            self.creds = None
            if token_path.exists():
                self.creds = Credentials.from_authorized_user_file(
                    str(token_path),
                    SCOPES
                )

            # Refresh or obtain new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    # Refresh expired credentials
                    self.logger.info("Refreshing expired credentials...")
                    self.creds.refresh(Request())
                else:
                    # Start OAuth 2.0 flow
                    self.logger.info("Starting OAuth 2.0 flow...")
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": self.settings.GMAIL_CLIENT_ID,
                                "client_secret": self.settings.GMAIL_CLIENT_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [self.settings.GMAIL_REDIRECT_URI],
                            }
                        },
                        SCOPES,
                    )
                    self.creds = flow.run_local_server(
                        port=int(self.settings.GMAIL_REDIRECT_URI.split(":")[-1]),
                        open_browser=False
                    )

                # Save credentials for future use
                with open(token_path, "w") as token:
                    token.write(self.creds.to_json())
                self.logger.info("Credentials saved successfully")

            # Build Gmail API service
            self.service = build("gmail", "v1", credentials=self.creds)
            self.logger.info("Gmail API authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False

    def fetch_messages(self, max_results: int = 10) -> List[GmailMessage]:
        """
        Fetch new messages from Gmail.

        Args:
            max_results: Maximum number of messages to fetch

        Returns:
            List of GmailMessage objects
        """
        try:
            if not self.service:
                self.logger.error("Gmail service not initialized")
                return []

            self.logger.debug(f"Fetching up to {max_results} messages...")

            # List messages
            response = self._retry_operation(
                lambda: self.service.users().messages().list(
                    userId="me",
                    maxResults=max_results
                ).execute()
            )

            messages = response.get("messages", [])
            if not messages:
                self.logger.debug("No new messages found")
                return []

            # Fetch full message details
            gmail_messages: List[GmailMessage] = []

            for msg in messages:
                message_id = msg["id"]

                # Skip already processed messages
                if message_id in self.processed_messages:
                    continue

                # Fetch full message
                full_message = self._retry_operation(
                    lambda mid=message_id: self.service.users().messages().get(
                        userId="me",
                        id=mid,
                        format="full"
                    ).execute()
                )

                # Parse message
                parsed = self._parse_message(full_message)
                if parsed:
                    gmail_messages.append(parsed)
                    self.processed_messages.add(message_id)

                    # Update last message ID
                    if self.last_message_id is None:
                        self.last_message_id = message_id

            self.logger.info(f"Fetched {len(gmail_messages)} new messages")
            return gmail_messages

        except Exception as e:
            self.logger.error(f"Failed to fetch messages: {str(e)}")
            return []

    def _parse_message(self, message: Dict[str, Any]) -> Optional[GmailMessage]:
        """
        Parse Gmail API message into GmailMessage object.

        Args:
            message: Gmail API message object

        Returns:
            GmailMessage object or None if parsing fails
        """
        try:
            message_id = message["id"]
            thread_id = message["threadId"]
            payload = message["payload"]
            headers = payload["headers"]

            # Extract headers
            subject = self._get_header(headers, "Subject")
            sender = self._get_header(headers, "From")
            date_str = self._get_header(headers, "Date")

            # Parse date
            try:
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            # Extract body
            body = self._extract_body(payload)

            # Extract attachments
            attachments = self._extract_attachments(payload, message_id)

            return GmailMessage(
                message_id=message_id,
                thread_id=thread_id,
                subject=subject,
                sender=sender,
                date=date,
                body=body,
                attachments=attachments
            )

        except Exception as e:
            self.logger.error(f"Failed to parse message {message.get('id', 'unknown')}: {str(e)}")
            return None

    def _get_header(self, headers: List[Dict[str, str]], name: str) -> str:
        """
        Extract header value from headers list.

        Args:
            headers: List of header dictionaries
            name: Header name to find

        Returns:
            Header value or empty string
        """
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body as string
        """
        body = ""

        # Try multipart
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "body" in part:
                    part_data = part["body"].get("data", "")
                    if part_data:
                        body = base64.urlsafe_b64decode(part_data).decode("utf-8", errors="ignore")
                        break
        # Try single part
        elif payload["mimeType"] == "text/plain" and "body" in payload:
            part_data = payload["body"].get("data", "")
            if part_data:
                body = base64.urlsafe_b64decode(part_data).decode("utf-8", errors="ignore")

        return body

    def _extract_attachments(
        self,
        payload: Dict[str, Any],
        message_id: str
    ) -> List[GmailAttachment]:
        """
        Extract attachments from payload.

        Args:
            payload: Gmail message payload
            message_id: Gmail message ID

        Returns:
            List of GmailAttachment objects
        """
        attachments: List[GmailAttachment] = []

        try:
            # Check parts for attachments
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["filename"] and part["body"].get("attachmentId"):
                        attachment_data = self._fetch_attachment(
                            message_id,
                            part["body"]["attachmentId"]
                        )
                        if attachment_data:
                            attachments.append(attachment_data)

            # Check for single attachment
            elif payload["filename"] and payload["body"].get("attachmentId"):
                attachment_data = self._fetch_attachment(
                    message_id,
                    payload["body"]["attachmentId"]
                )
                if attachment_data:
                    attachments.append(attachment_data)

        except Exception as e:
            self.logger.error(f"Failed to extract attachments: {str(e)}")

        return attachments

    def _fetch_attachment(
        self,
        message_id: str,
        attachment_id: str
    ) -> Optional[GmailAttachment]:
        """
        Fetch attachment data from Gmail API.

        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID

        Returns:
            GmailAttachment object or None
        """
        try:
            attachment = self._retry_operation(
                lambda: self.service.users().messages().attachments().get(
                    userId="me",
                    messageId=message_id,
                    id=attachment_id
                ).execute()
            )

            return GmailAttachment(
                filename=attachment["filename"],
                mime_type=attachment["mimeType"],
                size=attachment["size"],
                data=attachment["data"]
            )

        except Exception as e:
            self.logger.error(f"Failed to fetch attachment: {str(e)}")
            return None

    def _retry_operation(self, operation, is_read_only: bool = True) -> Any:
        """
        Execute operation with retry logic.

        Args:
            operation: Callable to execute
            is_read_only: Whether operation is read-only

        Returns:
            Operation result

        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries):
            try:
                return operation()

            except HttpError as e:
                last_exception = e

                # Check for rate limit (429)
                if e.resp.status == 429:
                    self.logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)

                    if self.use_exponential_backoff:
                        delay = min(delay * 2, self.max_delay)

                # Check for server error (5xx)
                elif 500 <= e.resp.status < 600:
                    self.logger.warning(f"Server error {e.resp.status}, retrying in {delay}s...")
                    time.sleep(delay)

                    if self.use_exponential_backoff:
                        delay = min(delay * 2, self.max_delay)

                else:
                    # Other errors, don't retry
                    self.logger.error(f"HTTP error: {str(e)}")
                    raise

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(delay)

                if self.use_exponential_backoff:
                    delay = min(delay * 2, self.max_delay)

        # All retries failed
        error_msg = f"All {self.max_retries} retries failed"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        raise Exception(error_msg)

    def save_attachments(self, message: GmailMessage) -> List[Path]:
        """
        Save attachments from message to Inbox folder.

        Args:
            message: GmailMessage object

        Returns:
            List of saved file paths
        """
        saved_files: List[Path] = []

        if not message.has_attachments():
            self.logger.debug(f"Message {message.message_id} has no attachments")
            return saved_files

        try:
            inbox_path = Path(self.settings.VAULT_PATH).expanduser() / "Inbox"
            inbox_path.mkdir(parents=True, exist_ok=True)

            for attachment in message.attachments:
                # Generate unique filename
                timestamp = message.date.strftime("%Y%m%d_%H%M%S")
                safe_filename = self._sanitize_filename(attachment.filename)
                filename = f"GMAIL_{timestamp}_{safe_filename}"
                file_path = inbox_path / filename

                # Check if file already exists
                if file_path.exists():
                    self.logger.info(f"Attachment already exists: {filename}")
                    saved_files.append(file_path)
                    continue

                # Save attachment
                try:
                    with open(file_path, "wb") as f:
                        f.write(attachment.decode_data())

                    saved_files.append(file_path)
                    self.logger.info(f"Saved attachment: {filename} ({attachment.size} bytes)")

                    # Log event
                    self.logger.log_event(
                        event_type="attachment_saved",
                        detail=f"Saved {attachment.filename} from {message.sender}",
                        result="success",
                        file_reference=str(file_path)
                    )

                except Exception as e:
                    self.logger.error(f"Failed to save attachment {attachment.filename}: {str(e)}")
                    self.logger.log_event(
                        event_type="attachment_save_failed",
                        detail=f"Failed to save {attachment.filename}: {str(e)}",
                        result="error"
                    )

        except Exception as e:
            self.logger.error(f"Failed to save attachments: {str(e)}")

        return saved_files

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system storage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace unsafe characters
        unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '_')

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')

        # Limit length
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext

        return sanitized or "attachment"

    def create_action_file(self, message: GmailMessage, saved_files: List[Path]) -> Optional[Path]:
        """
        Create action file in Needs_Action for processed email.

        Args:
            message: GmailMessage object
            saved_files: List of saved attachment paths

        Returns:
            Path to created action file or None
        """
        try:
            needs_action_path = Path(self.settings.VAULT_PATH).expanduser() / "Needs_Action"
            needs_action_path.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = self._sanitize_filename(message.subject)[:50] or "NoSubject"
            filename = f"EMAIL_{timestamp}_{safe_subject}.md"
            file_path = needs_action_path / filename

            # Build content
            content = self._build_action_content(message, saved_files)

            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Created action file: {filename}")
            self.logger.log_event(
                event_type="action_file_created",
                detail=f"Created action file for email from {message.sender}",
                result="success",
                file_reference=str(file_path)
            )

            return file_path

        except Exception as e:
            self.logger.error(f"Failed to create action file: {str(e)}")
            self.logger.log_event(
                event_type="action_file_creation_failed",
                detail=f"Failed to create action file: {str(e)}",
                result="error"
            )
            return None

    def _build_action_content(
        self,
        message: GmailMessage,
        saved_files: List[Path]
    ) -> str:
        """
        Build action file content.

        Args:
            message: GmailMessage object
            saved_files: List of saved attachment paths

        Returns:
            Action file content as string
        """
        # Build YAML frontmatter
        frontmatter = {
            "type": "gmail_email",
            "sender": message.sender,
            "subject": message.subject,
            "received": message.date.isoformat(),
            "message_id": message.message_id,
            "priority": "medium",
            "status": "pending",
            "has_attachments": message.has_attachments(),
            "attachment_count": len(saved_files)
        }

        # Format frontmatter
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")

        # Build body
        attachments_list = "\n".join([f"- `{f.name}`" for f in saved_files]) or "No attachments"

        body = f"""# Task: Process Email from {message.sender}

## Email Details
- **From:** {message.sender}
- **Subject:** {message.subject}
- **Received:** {message.date.strftime('%Y-%m-%d %H:%M:%S')}
- **Gmail Message ID:** {message.message_id}

## Attachments
{attachments_list}

## Email Body
{message.body if message.body else "*No plain text body available*"}

## Suggested Next Steps
- [ ] Review the email content
- [ ] Process attachments if needed
- [ ] Create a plan in /Plans/
- [ ] Execute the plan
- [ ] Move to /Done/ when complete

---
*Automatically generated by AI Employee Silver Tier - Gmail Integration*
"""
        return "\n".join(fm_lines) + body

    def process_messages(self, max_results: int = 10) -> int:
        """
        Process new messages from Gmail.

        Args:
            max_results: Maximum number of messages to process

        Returns:
            Number of messages processed
        """
        try:
            self.logger.info(f"Processing up to {max_results} messages...")

            # Fetch messages
            messages = self.fetch_messages(max_results)

            if not messages:
                self.logger.debug("No new messages to process")
                return 0

            processed_count = 0

            for message in messages:
                self.logger.info(f"Processing message: {message.subject} from {message.sender}")

                # Save attachments
                saved_files = self.save_attachments(message)

                # Create action file
                if saved_files or message.body:
                    self.create_action_file(message, saved_files)
                    processed_count += 1

            self.logger.info(f"Processed {processed_count} messages")
            return processed_count

        except Exception as e:
            self.logger.error(f"Failed to process messages: {str(e)}")
            return 0

    def run_once(self, max_results: int = 10) -> int:
        """
        Run one iteration of Gmail processing.

        Args:
            max_results: Maximum number of messages to process

        Returns:
            Number of messages processed
        """
        try:
            # Authenticate if needed
            if not self.service:
                if not self.authenticate():
                    self.logger.error("Authentication failed, skipping this iteration")
                    return 0

            # Process messages
            return self.process_messages(max_results)

        except Exception as e:
            self.logger.error(f"Error in run_once: {str(e)}")
            return 0

    def run_forever(self, poll_interval: Optional[int] = None) -> None:
        """
        Run Gmail watcher continuously.

        Args:
            poll_interval: Polling interval in seconds (uses settings if None)
        """
        if poll_interval is None:
            poll_interval = self.settings.GMAIL_POLL_INTERVAL

        self._running = True
        self.logger.info(f"Starting Gmail watcher (poll interval: {poll_interval}s)")

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
            self.logger.info("KeyboardInterrupt received, stopping Gmail watcher")
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stop the Gmail watcher.
        """
        self.logger.info("Stopping Gmail watcher...")
        self._running = False

        self.logger.log_event(
            event_type="system_stop",
            detail="Gmail watcher stopped",
            result="success"
        )


def create_gmail_watcher(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> GmailWatcher:
    """
    Factory function to create a GmailWatcher instance.

    Args:
        settings: Optional settings instance
        logger: Optional logger instance

    Returns:
        Configured GmailWatcher instance
    """
    return GmailWatcher(settings, logger)


if __name__ == "__main__":
    # Example usage / testing
    print("Starting Gmail Watcher (Test Mode)...")

    settings = get_settings()
    logger = get_logger()

    watcher = create_gmail_watcher(settings, logger)

    # Test authentication
    if watcher.authenticate():
        print("✓ Authentication successful")

        # Test fetch
        messages = watcher.fetch_messages(max_results=5)
        print(f"✓ Fetched {len(messages)} messages")

        # Test processing
        processed = watcher.process_messages(max_results=5)
        print(f"✓ Processed {processed} messages")

        print("\nTo run continuously, use: python -m src.ai_employee_silver.main start gmail")
    else:
        print("✗ Authentication failed")
        print("  Please check your Gmail credentials in .env")
        print("  Run OAuth flow manually if needed")
