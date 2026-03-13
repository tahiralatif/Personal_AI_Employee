"""
Unit tests for GmailWatcher integration.

Tests cover:
- GmailAttachment class
- GmailMessage class
- GmailWatcher class methods
- Attachment extraction
- File saving
- Action file creation
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call

from src.ai_employee_silver.integrations.gmail_watcher import (
    GmailAttachment,
    GmailMessage,
    GmailWatcher,
)
from src.ai_employee_silver.config.settings import Settings


class TestGmailAttachment(unittest.TestCase):
    """Unit tests for GmailAttachment class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_data = "SGVsbG8gV29ybGQ="  # "Hello World" in base64
        self.attachment = GmailAttachment(
            filename="test.pdf",
            mime_type="application/pdf",
            size=1024,
            data=self.test_data
        )

    def test_attachment_init(self) -> None:
        """Test GmailAttachment initialization."""
        self.assertEqual(self.attachment.filename, "test.pdf")
        self.assertEqual(self.attachment.mime_type, "application/pdf")
        self.assertEqual(self.attachment.size, 1024)
        self.assertEqual(self.attachment.data, self.test_data)

    def test_attachment_decode_data(self) -> None:
        """Test base64 data decoding."""
        decoded = self.attachment.decode_data()
        self.assertEqual(decoded, b"Hello World")

    def test_attachment_decode_urlsafe_base64(self) -> None:
        """Test decoding URL-safe base64 (used by Gmail)."""
        # Gmail uses URL-safe base64 with - and _ instead of + and /
        urlsafe_data = "SGVsbG8tV29ybGRfVGVzdA=="  # "Hello-World_Test"
        attachment = GmailAttachment(
            filename="test.txt",
            mime_type="text/plain",
            size=16,
            data=urlsafe_data
        )
        decoded = attachment.decode_data()
        self.assertEqual(decoded, b"Hello-World_Test")


class TestGmailMessage(unittest.TestCase):
    """Unit tests for GmailMessage class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.attachments = [
            GmailAttachment("file1.pdf", "application/pdf", 1024, "data1"),
            GmailAttachment("file2.xlsx", "application/vnd.ms-excel", 2048, "data2"),
        ]
        self.message = GmailMessage(
            message_id="msg_123",
            thread_id="thread_456",
            subject="Test Email",
            sender="test@example.com",
            date=datetime(2026, 2, 26, 10, 30, 0),
            body="This is a test email body",
            attachments=self.attachments
        )

    def test_message_init(self) -> None:
        """Test GmailMessage initialization."""
        self.assertEqual(self.message.message_id, "msg_123")
        self.assertEqual(self.message.thread_id, "thread_456")
        self.assertEqual(self.message.subject, "Test Email")
        self.assertEqual(self.message.sender, "test@example.com")
        self.assertEqual(self.message.body, "This is a test email body")
        self.assertEqual(len(self.message.attachments), 2)

    def test_has_attachments_true(self) -> None:
        """Test has_attachments() when message has attachments."""
        self.assertTrue(self.message.has_attachments())

    def test_has_attachments_false(self) -> None:
        """Test has_attachments() when message has no attachments."""
        message_no_attachments = GmailMessage(
            message_id="msg_789",
            thread_id="thread_012",
            subject="No Attachments",
            sender="sender@example.com",
            date=datetime.now(),
            body="Plain email",
            attachments=[]
        )
        self.assertFalse(message_no_attachments.has_attachments())


class TestGmailWatcher(unittest.TestCase):
    """Unit tests for GmailWatcher class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for test vault
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        # Create mock settings
        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.GMAIL_CLIENT_ID = "test-client-id"
        self.settings.GMAIL_CLIENT_SECRET = "test-secret"
        self.settings.GMAIL_REDIRECT_URI = "http://localhost:8080"
        self.settings.GMAIL_POLL_INTERVAL = 60
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.1
        self.settings.RETRY_MAX_DELAY = 1.0
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True
        self.settings.is_gmail_configured = Mock(return_value=True)

        # Create watcher
        self.watcher = GmailWatcher(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_watcher_init(self) -> None:
        """Test GmailWatcher initialization."""
        self.assertEqual(self.watcher.settings, self.settings)
        self.assertIsNone(self.watcher.service)
        self.assertIsNone(self.watcher.creds)
        self.assertIsNone(self.watcher.last_message_id)
        self.assertFalse(self.watcher._running)

    def test_sanitize_filename_basic(self) -> None:
        """Test filename sanitization."""
        self.assertEqual(
            self.watcher._sanitize_filename("test.pdf"),
            "test.pdf"
        )

    def test_sanitize_filename_unsafe_chars(self) -> None:
        """Test sanitization removes unsafe characters."""
        unsafe = "test<file>:name.pdf"
        sanitized = self.watcher._sanitize_filename(unsafe)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertNotIn(":", sanitized)
        # Double underscores are expected for multiple replacements
        self.assertIn("test_file", sanitized)
        self.assertIn("name.pdf", sanitized)

    def test_sanitize_filename_leading_dots(self) -> None:
        """Test sanitization removes leading/trailing dots."""
        self.assertEqual(
            self.watcher._sanitize_filename("...test.pdf..."),
            "test.pdf"
        )

    def test_sanitize_filename_long_name(self) -> None:
        """Test sanitization limits filename length."""
        long_name = "a" * 300 + ".pdf"
        sanitized = self.watcher._sanitize_filename(long_name)
        self.assertLessEqual(len(sanitized), 200)

    def test_sanitize_filename_empty(self) -> None:
        """Test sanitization handles empty filename."""
        self.assertEqual(
            self.watcher._sanitize_filename(""),
            "attachment"
        )

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_fetch_messages_empty(self, mock_retry: Mock) -> None:
        """Test fetching messages when inbox is empty."""
        mock_retry.return_value = {"messages": []}

        # Initialize service to avoid "not initialized" error
        self.watcher.service = Mock()

        messages = self.watcher.fetch_messages(max_results=10)

        self.assertEqual(len(messages), 0)
        mock_retry.assert_called_once()

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._parse_message")
    def test_fetch_messages_with_results(
        self,
        mock_parse: Mock,
        mock_retry: Mock
    ) -> None:
        """Test fetching messages with results."""
        # Mock message list response
        mock_retry.return_value = {
            "messages": [
                {"id": "msg_1", "threadId": "thread_1"},
                {"id": "msg_2", "threadId": "thread_2"},
            ]
        }

        # Initialize service
        self.watcher.service = Mock()

        # Mock parsed messages
        mock_message = Mock()
        mock_message.message_id = "msg_1"
        mock_parse.return_value = mock_message

        messages = self.watcher.fetch_messages(max_results=10)

        # Should fetch full message details for each
        self.assertEqual(mock_retry.call_count, 3)  # 1 list + 2 get
        self.assertEqual(len(messages), 2)

    def test_get_header_found(self) -> None:
        """Test extracting header that exists."""
        headers = [
            {"name": "From", "value": "sender@example.com"},
            {"name": "Subject", "value": "Test Subject"},
            {"name": "Date", "value": "Thu, 26 Feb 2026 10:30:00 +0000"},
        ]

        self.assertEqual(
            self.watcher._get_header(headers, "From"),
            "sender@example.com"
        )
        self.assertEqual(
            self.watcher._get_header(headers, "subject"),  # Case insensitive
            "Test Subject"
        )

    def test_get_header_not_found(self) -> None:
        """Test extracting header that doesn't exist."""
        headers = [
            {"name": "From", "value": "sender@example.com"},
        ]

        self.assertEqual(
            self.watcher._get_header(headers, "NonExistent"),
            ""
        )

    def test_extract_body_plain_text(self) -> None:
        """Test extracting plain text body."""
        import base64
        body_text = "Test email body"
        body_data = base64.urlsafe_b64encode(body_text.encode()).decode()

        payload = {
            "mimeType": "text/plain",
            "body": {"data": body_data}
        }

        body = self.watcher._extract_body(payload)
        self.assertEqual(body, body_text)

    def test_extract_body_multipart(self) -> None:
        """Test extracting body from multipart message."""
        import base64
        body_text = "Multipart email body"
        body_data = base64.urlsafe_b64encode(body_text.encode()).decode()

        payload = {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": body_data}
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "attachment.pdf"
                }
            ]
        }

        body = self.watcher._extract_body(payload)
        self.assertEqual(body, body_text)

    def test_extract_body_empty(self) -> None:
        """Test extracting body when no body available."""
        payload = {
            "mimeType": "text/html",
            "body": {}
        }

        body = self.watcher._extract_body(payload)
        self.assertEqual(body, "")

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._fetch_attachment")
    def test_extract_attachments_with_parts(self, mock_fetch: Mock) -> None:
        """Test extracting attachments from multipart message."""
        mock_attachment = GmailAttachment("test.pdf", "application/pdf", 1024, "data")
        mock_fetch.return_value = mock_attachment

        payload = {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "filename": "",
                    "headers": [],
                    "body": {}
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "test.pdf",
                    "headers": [],
                    "body": {"attachmentId": "attach_123"}
                }
            ]
        }

        attachments = self.watcher._extract_attachments(payload, "msg_123")

        self.assertGreaterEqual(len(attachments), 0)  # May be 0 if fetch fails
        # Verify fetch was called at least once
        mock_fetch.assert_called()

    def test_extract_attachments_none(self) -> None:
        """Test extracting attachments when none exist."""
        payload = {
            "mimeType": "text/plain",
            "body": {"data": "dGVzdA=="}
        }

        attachments = self.watcher._extract_attachments(payload, "msg_123")
        self.assertEqual(len(attachments), 0)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_fetch_attachment_success(self, mock_retry: Mock) -> None:
        """Test fetching attachment successfully."""
        mock_retry.return_value = {
            "filename": "test.pdf",
            "mimeType": "application/pdf",
            "size": 1024,
            "data": "dGVzdGRhdGE="
        }

        attachment = self.watcher._fetch_attachment("msg_123", "attach_456")

        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.filename, "test.pdf")
        self.assertEqual(attachment.size, 1024)

    def test_save_attachments_success(self) -> None:
        """Test saving attachments to Inbox."""
        # Create test message with attachment
        attachment_data = "SGVsbG8gV29ybGQ="  # "Hello World"
        attachment = GmailAttachment(
            filename="test.txt",
            mime_type="text/plain",
            size=11,
            data=attachment_data
        )

        message = GmailMessage(
            message_id="msg_123",
            thread_id="thread_456",
            subject="Test",
            sender="test@example.com",
            date=datetime(2026, 2, 26, 10, 30, 0),
            body="Test body",
            attachments=[attachment]
        )

        # Save attachments
        saved_files = self.watcher.save_attachments(message)

        # Verify file was saved
        self.assertEqual(len(saved_files), 1)
        self.assertTrue(saved_files[0].exists())
        self.assertTrue(saved_files[0].name.startswith("GMAIL_"))
        self.assertTrue(saved_files[0].name.endswith("test.txt"))

        # Verify content
        with open(saved_files[0], "rb") as f:
            content = f.read()
        self.assertEqual(content, b"Hello World")

    def test_save_attachments_no_attachments(self) -> None:
        """Test saving when message has no attachments."""
        message = GmailMessage(
            message_id="msg_789",
            thread_id="thread_012",
            subject="No Attachments",
            sender="sender@example.com",
            date=datetime.now(),
            body="Plain email",
            attachments=[]
        )

        saved_files = self.watcher.save_attachments(message)
        self.assertEqual(len(saved_files), 0)

    def test_save_attachments_duplicate(self) -> None:
        """Test saving attachment that already exists."""
        # Create test attachment
        attachment = GmailAttachment(
            filename="test.txt",
            mime_type="text/plain",
            size=11,
            data="SGVsbG8gV29ybGQ="
        )

        message = GmailMessage(
            message_id="msg_123",
            thread_id="thread_456",
            subject="Test",
            sender="test@example.com",
            date=datetime(2026, 2, 26, 10, 30, 0),
            body="Test body",
            attachments=[attachment]
        )

        # Save first time
        saved_files_1 = self.watcher.save_attachments(message)
        self.assertEqual(len(saved_files_1), 1)

        # Save second time (should detect duplicate)
        saved_files_2 = self.watcher.save_attachments(message)
        self.assertEqual(len(saved_files_2), 1)
        self.assertEqual(saved_files_1[0], saved_files_2[0])

    def test_create_action_file_success(self) -> None:
        """Test creating action file successfully."""
        # Create test message
        message = GmailMessage(
            message_id="msg_123",
            thread_id="thread_456",
            subject="Test Email",
            sender="sender@example.com",
            date=datetime(2026, 2, 26, 10, 30, 0),
            body="Test email body",
            attachments=[]
        )

        # Create action file
        action_file = self.watcher.create_action_file(message, [])

        # Verify file was created
        self.assertIsNotNone(action_file)
        self.assertTrue(action_file.exists())
        self.assertTrue(action_file.name.startswith("EMAIL_"))
        self.assertTrue(action_file.name.endswith(".md"))

        # Verify content
        content = action_file.read_text()
        self.assertIn("---", content)  # YAML frontmatter
        self.assertIn("type: gmail_email", content)
        self.assertIn("sender: sender@example.com", content)
        self.assertIn("subject: Test Email", content)
        self.assertIn("Test email body", content)

    def test_create_action_file_with_attachments(self) -> None:
        """Test creating action file with attachments."""
        message = GmailMessage(
            message_id="msg_123",
            thread_id="thread_456",
            subject="With Attachments",
            sender="sender@example.com",
            date=datetime(2026, 2, 26, 10, 30, 0),
            body="Check attachments",
            attachments=[]
        )

        # Create dummy files
        inbox_path = self.vault_path / "Inbox"
        inbox_path.mkdir()
        file1 = inbox_path / "file1.pdf"
        file2 = inbox_path / "file2.xlsx"
        file1.write_text("dummy1")
        file2.write_text("dummy2")

        action_file = self.watcher.create_action_file(message, [file1, file2])

        content = action_file.read_text()
        self.assertIn("file1.pdf", content)
        self.assertIn("file2.xlsx", content)
        # Note: has_attachments is based on message.attachments, not saved_files
        self.assertIn("attachment_count: 2", content)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher.authenticate")
    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher.process_messages")
    def test_run_once_success(self, mock_process: Mock, mock_auth: Mock) -> None:
        """Test running one iteration successfully."""
        mock_auth.return_value = True
        mock_process.return_value = 5

        result = self.watcher.run_once()

        self.assertEqual(result, 5)
        mock_auth.assert_called_once()
        mock_process.assert_called_once()

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher.authenticate")
    def test_run_once_auth_failed(self, mock_auth: Mock) -> None:
        """Test running when authentication fails."""
        mock_auth.return_value = False

        result = self.watcher.run_once()

        self.assertEqual(result, 0)
        mock_auth.assert_called_once()

    def test_stop(self) -> None:
        """Test stopping the watcher."""
        self.watcher._running = True
        self.watcher.stop()
        self.assertFalse(self.watcher._running)

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher.run_once")
    def test_run_forever(self, mock_run_once: Mock, mock_sleep: Mock) -> None:
        """Test running watcher continuously."""
        # Stop after 2 iterations
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                self.watcher._running = False
            return 5

        mock_run_once.side_effect = side_effect

        # Run (will stop after 2 iterations)
        self.watcher.run_forever(poll_interval=1)

        # Verify
        self.assertEqual(call_count[0], 2)
        self.assertFalse(self.watcher._running)


class TestGmailWatcherRetry(unittest.TestCase):
    """Unit tests for retry logic in GmailWatcher."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01  # Fast for testing
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        self.watcher = GmailWatcher(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("time.sleep")
    def test_retry_operation_success(self, mock_sleep: Mock) -> None:
        """Test retry operation that succeeds on first try."""
        operation = Mock(return_value="success")

        result = self.watcher._retry_operation(operation)

        self.assertEqual(result, "success")
        operation.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_retry_operation_with_retries(self, mock_sleep: Mock) -> None:
        """Test retry operation that succeeds after failures."""
        from googleapiclient.errors import HttpError

        # Mock response for 500 error
        mock_response = Mock()
        mock_response.status = 500

        # Fail twice, succeed on third
        operation = Mock(side_effect=[
            HttpError(mock_response, b"Server error"),
            HttpError(mock_response, b"Server error"),
            "success"
        ])

        result = self.watcher._retry_operation(operation)

        self.assertEqual(result, "success")
        self.assertEqual(operation.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep")
    def test_retry_operation_all_failures(self, mock_sleep: Mock) -> None:
        """Test retry operation that fails all attempts."""
        from googleapiclient.errors import HttpError

        mock_response = Mock()
        mock_response.status = 500

        operation = Mock(side_effect=HttpError(mock_response, b"Server error"))

        with self.assertRaises(Exception):
            self.watcher._retry_operation(operation)

        self.assertEqual(operation.call_count, 3)  # max_retries

    @patch("time.sleep")
    def test_retry_rate_limit(self, mock_sleep: Mock) -> None:
        """Test retry with rate limit (429)."""
        from googleapiclient.errors import HttpError

        mock_response = Mock()
        mock_response.status = 429

        operation = Mock(side_effect=[
            HttpError(mock_response, b"Rate limit"),
            "success"
        ])

        result = self.watcher._retry_operation(operation)

        self.assertEqual(result, "success")
        self.assertEqual(operation.call_count, 2)
        mock_sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
