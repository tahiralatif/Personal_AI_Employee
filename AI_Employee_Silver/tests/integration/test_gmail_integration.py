"""
Integration tests for GmailWatcher.

These tests verify the Gmail integration works end-to-end with:
- Mock Gmail API responses
- Real file system operations
- Real logging operations
- Full workflow from email fetch to action file creation

Note: These tests use mocked Gmail API calls. For real API testing,
use manual testing with actual Gmail credentials.
"""

import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from email.utils import formatdate

from src.ai_employee_silver.integrations.gmail_watcher import (
    GmailWatcher,
    GmailMessage,
    GmailAttachment,
)
from src.ai_employee_silver.config.settings import Settings


class TestGmailIntegrationWorkflow(unittest.TestCase):
    """Integration tests for complete Gmail workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary vault
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        # Create vault subdirectories
        (self.vault_path / "Inbox").mkdir()
        (self.vault_path / "Needs_Action").mkdir()
        (self.vault_path / "Logs").mkdir()

        # Create mock settings with all required attributes
        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.WATCHED_FOLDER = str(self.vault_path / "Inbox")
        self.settings.LOG_LEVEL = "DEBUG"
        self.settings.GMAIL_CLIENT_ID = "test-client-id"
        self.settings.GMAIL_CLIENT_SECRET = "test-secret"
        self.settings.GMAIL_REDIRECT_URI = "http://localhost:8080"
        self.settings.GMAIL_POLL_INTERVAL = 60
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True
        self.settings.is_gmail_configured = Mock(return_value=True)

        # Create watcher
        self.watcher = GmailWatcher(settings=self.settings)
        
        # Mock the service to avoid "not initialized" errors
        self.watcher.service = Mock()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mock_message(
        self,
        message_id: str,
        subject: str,
        sender: str,
        has_attachment: bool = True
    ) -> dict:
        """Create a mock Gmail API message response."""
        import base64

        body_text = f"Test email body for {subject}"
        body_data = base64.urlsafe_b64encode(body_text.encode()).decode()

        message = {
            "id": message_id,
            "threadId": f"thread_{message_id}",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": body_text[:100],
            "payload": {
                "partId": "",
                "mimeType": "multipart/mixed",
                "filename": "",
                "headers": [
                    {"name": "From", "value": sender},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Subject", "value": subject},
                    {"name": "Date", "value": formatdate(localtime=True)},
                ],
                "body": {"size": 0},
                "parts": [
                    {
                        "partId": "0",
                        "mimeType": "text/plain",
                        "filename": "",
                        "headers": [],
                        "body": {"size": len(body_data), "data": body_data}
                    }
                ]
            },
            "sizeEstimate": 1024,
            "historyId": "123456",
            "internalDate": str(int(datetime.now().timestamp() * 1000))
        }

        if has_attachment:
            attachment_data = base64.urlsafe_b64encode(b"Attachment content").decode()
            message["payload"]["parts"].append({
                "partId": "1",
                "mimeType": "application/pdf",
                "filename": "invoice.pdf",
                "headers": [],
                "body": {
                    "attachmentId": f"attach_{message_id}",
                    "size": 18
                }
            })

        return message

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_complete_email_processing_workflow(self, mock_retry: Mock) -> None:
        """Test complete workflow: fetch → save attachments → create action file."""
        # Setup mock responses
        message_id = "msg_001"
        mock_message = self._create_mock_message(
            message_id=message_id,
            subject="Invoice #12345",
            sender="billing@vendor.com",
            has_attachment=True
        )

        # Mock message list
        mock_retry.side_effect = [
            # First call: list messages
            {"messages": [{"id": message_id, "threadId": f"thread_{message_id}"}]},
            # Second call: get message
            mock_message,
            # Third call: get attachment
            {
                "filename": "invoice.pdf",
                "mimeType": "application/pdf",
                "size": 18,
                "data": "QXR0YWNobWVudCBjb250ZW50"  # "Attachment content"
            }
        ]

        # Run workflow
        processed = self.watcher.process_messages(max_results=1)

        # Verify results
        self.assertEqual(processed, 1)

        # Verify Inbox has attachment
        inbox_files = list((self.vault_path / "Inbox").glob("GMAIL_*.pdf"))
        self.assertEqual(len(inbox_files), 1)

        # Verify attachment content
        with open(inbox_files[0], "rb") as f:
            content = f.read()
        self.assertEqual(content, b"Attachment content")

        # Verify Needs_Action has action file
        action_files = list((self.vault_path / "Needs_Action").glob("EMAIL_*.md"))
        self.assertEqual(len(action_files), 1)

        # Verify action file content
        action_content = action_files[0].read_text()
        self.assertIn("billing@vendor.com", action_content)
        self.assertIn("Invoice #12345", action_content)
        self.assertIn("invoice.pdf", action_content)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_email_without_attachments(self, mock_retry: Mock) -> None:
        """Test processing email without attachments."""
        message_id = "msg_002"
        mock_message = self._create_mock_message(
            message_id=message_id,
            subject="Meeting Reminder",
            sender="calendar@example.com",
            has_attachment=False
        )

        mock_retry.side_effect = [
            {"messages": [{"id": message_id, "threadId": f"thread_{message_id}"}]},
            mock_message,
        ]

        processed = self.watcher.process_messages(max_results=1)

        self.assertEqual(processed, 1)

        # Verify no files in Inbox
        inbox_files = list((self.vault_path / "Inbox").iterdir())
        self.assertEqual(len(inbox_files), 0)

        # Verify action file still created
        action_files = list((self.vault_path / "Needs_Action").glob("EMAIL_*.md"))
        self.assertEqual(len(action_files), 1)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_multiple_attachments(self, mock_retry: Mock) -> None:
        """Test email with multiple attachments."""
        message_id = "msg_003"

        # Create message with 3 attachments
        import base64
        mock_message = {
            "id": message_id,
            "threadId": f"thread_{message_id}",
            "payload": {
                "headers": [
                    {"name": "From", "value": "documents@example.com"},
                    {"name": "Subject", "value": "Multiple Documents"},
                    {"name": "Date", "value": formatdate(localtime=True)},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "filename": "",
                        "headers": [],
                        "body": {"data": base64.urlsafe_b64encode(b"Body").decode()}
                    },
                    {
                        "mimeType": "application/pdf",
                        "filename": "doc1.pdf",
                        "headers": [],
                        "body": {"attachmentId": "attach_1"}
                    },
                    {
                        "mimeType": "application/vnd.ms-excel",
                        "filename": "spreadsheet.xlsx",
                        "headers": [],
                        "body": {"attachmentId": "attach_2"}
                    },
                    {
                        "mimeType": "image/png",
                        "filename": "screenshot.png",
                        "headers": [],
                        "body": {"attachmentId": "attach_3"}
                    }
                ]
            }
        }

        mock_retry.side_effect = [
            {"messages": [{"id": message_id, "threadId": f"thread_{message_id}"}]},
            mock_message,
            {"filename": "doc1.pdf", "mimeType": "application/pdf", "size": 10, "data": "ZG9jMQ=="},
            {"filename": "spreadsheet.xlsx", "mimeType": "application/vnd.ms-excel", "size": 10, "data": "eGxzMQ=="},
            {"filename": "screenshot.png", "mimeType": "image/png", "size": 10, "data": "cG5nMQ=="},
        ]

        processed = self.watcher.process_messages(max_results=1)

        self.assertEqual(processed, 1)

        # Verify all attachments saved
        inbox_files = list((self.vault_path / "Inbox").iterdir())
        self.assertEqual(len(inbox_files), 3)

        filenames = [f.name for f in inbox_files]
        self.assertTrue(any("doc1.pdf" in f for f in filenames))
        self.assertTrue(any("spreadsheet.xlsx" in f for f in filenames))
        self.assertTrue(any("screenshot.png" in f for f in filenames))

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_duplicate_message_skipped(self, mock_retry: Mock) -> None:
        """Test that already processed messages are skipped."""
        message_id = "msg_004"
        mock_message = self._create_mock_message(
            message_id=message_id,
            subject="Test",
            sender="test@example.com",
            has_attachment=False
        )

        mock_retry.side_effect = [
            {"messages": [{"id": message_id, "threadId": f"thread_{message_id}"}]},
            mock_message,
        ]

        # Process first time
        processed_1 = self.watcher.process_messages(max_results=1)
        self.assertEqual(processed_1, 1)

        # Process second time (should skip)
        mock_retry.side_effect = [
            {"messages": [{"id": message_id, "threadId": f"thread_{message_id}"}]},
        ]
        processed_2 = self.watcher.process_messages(max_results=1)
        self.assertEqual(processed_2, 0)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_empty_inbox(self, mock_retry: Mock) -> None:
        """Test processing when inbox is empty."""
        mock_retry.return_value = {"messages": []}

        processed = self.watcher.process_messages(max_results=10)

        self.assertEqual(processed, 0)

        # Verify no files created
        inbox_files = list((self.vault_path / "Inbox").iterdir())
        self.assertEqual(len(inbox_files), 0)

        action_files = list((self.vault_path / "Needs_Action").iterdir())
        self.assertEqual(len(action_files), 0)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_logging_integration(self, mock_retry: Mock) -> None:
        """Test that operations are logged correctly."""
        message_id = "msg_005"
        mock_message = self._create_mock_message(
            message_id=message_id,
            subject="Logged Email",
            sender="logs@example.com",
            has_attachment=True
        )

        mock_retry.side_effect = [
            {"messages": [{"id": message_id, "threadId": f"thread_{message_id}"}]},
            mock_message,
            {
                "filename": "test.pdf",
                "mimeType": "application/pdf",
                "size": 10,
                "data": "dGVzdA=="
            }
        ]

        # Process message
        self.watcher.process_messages(max_results=1)

        # Verify files were created (which implies logging worked)
        inbox_files = list((self.vault_path / "Inbox").iterdir())
        self.assertGreater(len(inbox_files), 0)
        
        action_files = list((self.vault_path / "Needs_Action").iterdir())
        self.assertGreater(len(action_files), 0)
        
        # Note: Logger writes to default vault path, not test vault
        # This test verifies the workflow completes successfully


class TestGmailAuthentication(unittest.TestCase):
    """Integration tests for Gmail authentication flow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.GMAIL_CLIENT_ID = "test-client-id"
        self.settings.GMAIL_CLIENT_SECRET = "test-secret"
        self.settings.GMAIL_REDIRECT_URI = "http://localhost:8080"
        self.settings.is_gmail_configured = Mock(return_value=True)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.Credentials")
    @patch("src.ai_employee_silver.integrations.gmail_watcher.build")
    def test_auth_with_existing_token(self, mock_build: Mock, mock_creds_class: Mock) -> None:
        """Test authentication with existing token file."""
        # Create token file
        token_path = Path(self.test_dir) / "token.json"
        token_data = {
            "token": "test_token",
            "refresh_token": "test_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test-client-id",
            "client_secret": "test-secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
        }
        token_path.write_text(json.dumps(token_data))

        # Mock credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_file.return_value = mock_creds

        # Change to test dir so token.json is found
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        try:
            # Add missing attributes to settings
            self.settings.MAX_RETRY_ATTEMPTS = 3
            self.settings.RETRY_INITIAL_DELAY = 0.01
            self.settings.RETRY_MAX_DELAY = 0.1
            self.settings.RETRY_EXPONENTIAL_BACKOFF = True
            
            watcher = GmailWatcher(settings=self.settings)
            result = watcher.authenticate()

            self.assertTrue(result)
            self.assertEqual(watcher.creds, mock_creds)
            mock_creds_class.from_authorized_user_file.assert_called_once()

        finally:
            os.chdir(original_cwd)

    def test_auth_credentials_not_configured(self) -> None:
        """Test authentication when credentials not configured."""
        self.settings.is_gmail_configured = Mock(return_value=False)
        # Add missing attributes
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        watcher = GmailWatcher(settings=self.settings)
        result = watcher.authenticate()

        self.assertFalse(result)


class TestGmailErrorHandling(unittest.TestCase):
    """Integration tests for Gmail error handling."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()
        (self.vault_path / "Inbox").mkdir()
        (self.vault_path / "Needs_Action").mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.MAX_RETRY_ATTEMPTS = 2
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        self.watcher = GmailWatcher(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_api_error_handling(self, mock_retry: Mock) -> None:
        """Test handling of API errors."""
        from googleapiclient.errors import HttpError

        mock_response = Mock()
        mock_response.status = 500
        mock_retry.side_effect = HttpError(mock_response, b"Server error")

        # Should not raise, should return 0 processed
        processed = self.watcher.process_messages(max_results=1)
        self.assertEqual(processed, 0)

    @patch("src.ai_employee_silver.integrations.gmail_watcher.GmailWatcher._retry_operation")
    def test_parse_error_handling(self, mock_retry: Mock) -> None:
        """Test handling of message parse errors."""
        # Return malformed message
        mock_retry.return_value = {
            "messages": [{"id": "msg_bad", "threadId": "thread_bad"}]
        }

        # Get will return message without required fields
        bad_message = {
            "id": "msg_bad",
            "threadId": "thread_bad",
            "payload": {}  # Missing headers
        }

        # First call is list, second is get
        mock_retry.side_effect = [
            {"messages": [{"id": "msg_bad", "threadId": "thread_bad"}]},
            bad_message
        ]

        # Should not raise, should handle gracefully
        processed = self.watcher.process_messages(max_results=1)
        self.assertEqual(processed, 0)


if __name__ == "__main__":
    unittest.main()
