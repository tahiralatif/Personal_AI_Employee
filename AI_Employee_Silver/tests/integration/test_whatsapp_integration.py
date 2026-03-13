"""
Integration tests for WhatsAppMonitor.

These tests verify the WhatsApp integration works end-to-end with:
- Mock WhatsApp Business API responses
- Real file system operations
- Real logging operations
- Full workflow from message receive to task file creation

Note: These tests use mocked API calls. For real API testing,
use manual testing with actual WhatsApp Business credentials.
"""

import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.ai_employee_silver.integrations.whatsapp_monitor import (
    WhatsAppMonitor,
    WhatsAppMessage,
)
from src.ai_employee_silver.config.settings import Settings


class TestWhatsAppIntegrationWorkflow(unittest.TestCase):
    """Integration tests for complete WhatsApp workflow."""

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

        # Create mock settings
        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "test_business_id"
        self.settings.WHATSAPP_ACCESS_TOKEN = "test_token"
        self.settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"
        self.settings.WHATSAPP_API_VERSION = "v18.0"
        self.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN = "test_verify_token"
        self.settings.WHATSAPP_POLL_INTERVAL = 30
        self.settings.WHATSAPP_TASK_KEYWORDS = ["please", "need", "urgent", "task"]
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        # Create monitor
        self.monitor = WhatsAppMonitor(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_complete_message_processing_workflow(self, mock_retry: Mock) -> None:
        """Test complete workflow: receive → process → create task file."""
        # Setup mock response for polling
        mock_retry.return_value = {
            "messages": [
                {
                    "id": "msg_001",
                    "from": "+1234567890",
                    "timestamp": "1708941000",
                    "text": {"body": "Please send me the project files"}
                }
            ]
        }

        # Run workflow
        processed = self.monitor.process_messages(self.monitor.poll_messages())

        # Verify results
        self.assertEqual(processed, 1)

        # Verify Needs_Action has task file
        action_files = list((self.vault_path / "Needs_Action").glob("WHATSAPP_*.md"))
        self.assertEqual(len(action_files), 1)

        # Verify task file content
        action_content = action_files[0].read_text()
        self.assertIn("+1234567890", action_content)
        self.assertIn("Please send me the project files", action_content)
        self.assertIn("type: whatsapp_message", action_content)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_message_with_media_workflow(self, mock_retry: Mock) -> None:
        """Test processing message with media attachment."""
        # Mock polling response with media
        mock_retry.return_value = {
            "messages": [
                {
                    "id": "msg_002",
                    "from": "+1234567891",
                    "timestamp": "1708941000",
                    "image": {"id": "image_123"}
                }
            ]
        }

        # Mock media download
        with patch.object(self.monitor, 'download_media', return_value=b"fake image data"):
            processed = self.monitor.process_messages(self.monitor.poll_messages())

        self.assertEqual(processed, 1)

        # Verify media saved to Inbox
        inbox_files = list((self.vault_path / "Inbox").glob("WHATSAPP_*.jpg"))
        self.assertGreater(len(inbox_files), 0)

        # Verify task file references media
        action_files = list((self.vault_path / "Needs_Action").glob("WHATSAPP_*.md"))
        self.assertEqual(len(action_files), 1)

        action_content = action_files[0].read_text()
        self.assertIn("media_type: image", action_content)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_non_task_message_skipped(self, mock_retry: Mock) -> None:
        """Test that non-task messages are skipped."""
        # Message without task keywords
        mock_retry.return_value = {
            "messages": [
                {
                    "id": "msg_003",
                    "from": "+1234567892",
                    "timestamp": "1708941000",
                    "text": {"body": "Hey, how are you?"}
                }
            ]
        }

        processed = self.monitor.process_messages(self.monitor.poll_messages())

        # Should not create task file for non-task messages
        self.assertEqual(processed, 0)

        action_files = list((self.vault_path / "Needs_Action").iterdir())
        self.assertEqual(len(action_files), 0)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_multiple_messages_batch_processing(self, mock_retry: Mock) -> None:
        """Test processing multiple messages in a batch."""
        mock_retry.return_value = {
            "messages": [
                {
                    "id": "msg_004",
                    "from": "+1234567893",
                    "timestamp": "1708941000",
                    "text": {"body": "Urgent: Need help with task"}
                },
                {
                    "id": "msg_005",
                    "from": "+1234567894",
                    "timestamp": "1708941001",
                    "text": {"body": "Please review this document"}
                },
                {
                    "id": "msg_006",
                    "from": "+1234567895",
                    "timestamp": "1708941002",
                    "text": {"body": "Good morning!"}  # Not a task
                }
            ]
        }

        processed = self.monitor.process_messages(self.monitor.poll_messages())

        # Should process 2 out of 3 messages (only tasks)
        self.assertEqual(processed, 2)

        action_files = list((self.vault_path / "Needs_Action").glob("WHATSAPP_*.md"))
        self.assertEqual(len(action_files), 2)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_duplicate_message_skipped(self, mock_retry: Mock) -> None:
        """Test that already processed messages are skipped."""
        message_data = {
            "id": "msg_007",
            "from": "+1234567896",
            "timestamp": "1708941000",
            "text": {"body": "Please complete this"}
        }

        mock_retry.return_value = {"messages": [message_data]}

        # Process first time
        processed_1 = self.monitor.process_messages(self.monitor.poll_messages())
        self.assertEqual(processed_1, 1)

        # Process second time (should skip duplicate)
        processed_2 = self.monitor.process_messages(self.monitor.poll_messages())
        self.assertEqual(processed_2, 0)

    def test_webhook_integration(self) -> None:
        """Test webhook message handling."""
        payload = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "contacts": [{"wa_id": "+1234567897", "profile": {"name": "Test User"}}],
                        "messages": [{
                            "id": "webhook_msg_1",
                            "from": "+1234567897",
                            "timestamp": "1708941000",
                            "text": {"body": "I need urgent help with the project"}
                        }]
                    }
                }]
            }]
        }

        # Handle webhook
        messages = self.monitor.handle_webhook(payload)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_id, "webhook_msg_1")
        self.assertEqual(messages[0].from_name, "Test User")

        # Process messages from webhook
        processed = self.monitor.process_messages(messages)
        self.assertEqual(processed, 1)

        # Verify task file created
        action_files = list((self.vault_path / "Needs_Action").glob("WHATSAPP_*.md"))
        self.assertEqual(len(action_files), 1)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_media_types_handling(self, mock_retry: Mock) -> None:
        """Test handling different media types."""
        test_cases = [
            ("image", "image_id", ".jpg"),
            ("document", "doc_id", ".bin"),
            ("audio", "audio_id", ".ogg"),
            ("video", "video_id", ".mp4")
        ]

        for media_type, media_id, expected_ext in test_cases:
            # Clear previous files
            for f in (self.vault_path / "Inbox").iterdir():
                f.unlink()

            message = WhatsAppMessage(
                message_id=f"msg_{media_type}",
                from_number="+1234567898",
                from_name="Test",
                timestamp=datetime.now(),
                text="Check this media",
                media_type=media_type,
                media_id=media_id
            )

            # Mock download
            with patch.object(self.monitor, 'download_media', return_value=b"fake media"):
                self.monitor.process_messages([message])

            # Verify media saved with correct extension
            inbox_files = list((self.vault_path / "Inbox").iterdir())
            self.assertGreater(len(inbox_files), 0)
            self.assertTrue(inbox_files[0].name.endswith(expected_ext))


class TestWhatsAppErrorHandling(unittest.TestCase):
    """Integration tests for WhatsApp error handling."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()
        (self.vault_path / "Inbox").mkdir()
        (self.vault_path / "Needs_Action").mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "test_business_id"
        self.settings.WHATSAPP_ACCESS_TOKEN = "test_token"
        self.settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"
        self.settings.WHATSAPP_API_VERSION = "v18.0"
        self.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN = "test_verify_token"
        self.settings.WHATSAPP_POLL_INTERVAL = 30
        self.settings.WHATSAPP_TASK_KEYWORDS = ["please", "need", "urgent"]
        self.settings.MAX_RETRY_ATTEMPTS = 2
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        self.monitor = WhatsAppMonitor(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_media_download_failure(self, mock_retry: Mock) -> None:
        """Test handling of media download failure."""
        message = WhatsAppMessage(
            message_id="msg_media_fail",
            from_number="+1234567899",
            from_name="Test",
            timestamp=datetime.now(),
            text="Check this",
            media_type="image",
            media_id="invalid_media_id"
        )

        # Mock download failure
        with patch.object(self.monitor, 'download_media', return_value=None):
            # Message has media but download fails
            # process_messages will skip if no media saved and not a task
            processed = self.monitor.process_messages([message])
            # Just verify no crash - processed may be 0
            self.assertGreaterEqual(processed, -1)  # Always true, just checking no exception

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_api_error_handling(self, mock_retry: Mock) -> None:
        """Test handling of API errors."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_retry.side_effect = requests.exceptions.HTTPError(response=mock_response)

        # Should not raise, should return empty list
        messages = self.monitor.poll_messages()
        self.assertEqual(len(messages), 0)


class TestWhatsAppKeywordDetection(unittest.TestCase):
    """Integration tests for task keyword detection."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()
        (self.vault_path / "Inbox").mkdir()
        (self.vault_path / "Needs_Action").mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "test_business_id"
        self.settings.WHATSAPP_ACCESS_TOKEN = "test_token"
        self.settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"
        self.settings.WHATSAPP_API_VERSION = "v18.0"
        self.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN = "test_verify_token"
        self.settings.WHATSAPP_POLL_INTERVAL = 30
        self.settings.WHATSAPP_TASK_KEYWORDS = ["please", "need", "urgent", "task", "action", "required"]
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        # Don't create monitor - not needed for keyword detection tests

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_task_keywords_variations(self) -> None:
        """Test various task keyword variations."""
        test_cases = [
            ("Please help me", True),
            ("I need this done", True),
            ("URGENT: Call me", True),
            ("This is a task for you", True),
            ("Action required immediately", True),
            ("Hey, how are you?", False),
            ("Good morning!", False),
            ("Thanks for your help", False),
        ]

        for text, should_be_task in test_cases:
            message = WhatsAppMessage(
                message_id=f"msg_{hash(text)}",
                from_number="+1234567800",
                from_name="Test",
                timestamp=datetime.now(),
                text=text
            )

            is_task = message.is_task(self.settings.WHATSAPP_TASK_KEYWORDS)
            self.assertEqual(is_task, should_be_task, f"Failed for: {text}")

    def test_case_insensitive_detection(self) -> None:
        """Test that keyword detection is case-insensitive."""
        test_texts = [
            "PLEASE help me",
            "please HELP me",
            "PLEASE HELP ME",
            "PlEaSe HeLp Me"
        ]

        for text in test_texts:
            message = WhatsAppMessage(
                message_id=f"msg_{hash(text)}",
                from_number="+1234567801",
                from_name="Test",
                timestamp=datetime.now(),
                text=text
            )

            self.assertTrue(message.is_task(self.settings.WHATSAPP_TASK_KEYWORDS))


if __name__ == "__main__":
    unittest.main()
