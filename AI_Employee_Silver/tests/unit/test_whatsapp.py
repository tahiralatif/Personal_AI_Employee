"""
Unit tests for WhatsAppMonitor integration.

Tests cover:
- WhatsAppMessage class
- WhatsAppMonitor class methods
- Message parsing
- Task keyword detection
- Media handling
- Task file creation
"""

import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call

from src.ai_employee_silver.integrations.whatsapp_monitor import (
    WhatsAppMessage,
    WhatsAppMonitor,
)
from src.ai_employee_silver.config.settings import Settings


class TestWhatsAppMessage(unittest.TestCase):
    """Unit tests for WhatsAppMessage class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.message = WhatsAppMessage(
            message_id="msg_123",
            from_number="+1234567890",
            from_name="John Doe",
            timestamp=datetime(2026, 2, 26, 10, 30, 0),
            text="Please send me the invoice",
            media_type="document",
            media_url="https://example.com/media",
            media_id="media_456"
        )

    def test_message_init(self) -> None:
        """Test WhatsAppMessage initialization."""
        self.assertEqual(self.message.message_id, "msg_123")
        self.assertEqual(self.message.from_number, "+1234567890")
        self.assertEqual(self.message.from_name, "John Doe")
        self.assertEqual(self.message.text, "Please send me the invoice")
        self.assertEqual(self.message.media_type, "document")
        self.assertEqual(self.message.media_id, "media_456")

    def test_has_media_true(self) -> None:
        """Test has_media() when message has media."""
        self.assertTrue(self.message.has_media())

    def test_has_media_false(self) -> None:
        """Test has_media() when message has no media."""
        msg_no_media = WhatsAppMessage(
            message_id="msg_789",
            from_number="+1234567890",
            from_name="Jane",
            timestamp=datetime.now(),
            text="Hello"
        )
        self.assertFalse(msg_no_media.has_media())

    def test_is_task_with_keywords(self) -> None:
        """Test is_task() with task keywords."""
        self.assertTrue(self.message.is_task())

    def test_is_task_without_keywords(self) -> None:
        """Test is_task() without task keywords."""
        msg_no_task = WhatsAppMessage(
            message_id="msg_999",
            from_number="+1234567890",
            from_name="Test",
            timestamp=datetime.now(),
            text="Hey, how are you?"
        )
        self.assertFalse(msg_no_task.is_task())

    def test_is_task_custom_keywords(self) -> None:
        """Test is_task() with custom keywords."""
        msg = WhatsAppMessage(
            message_id="msg_888",
            from_number="+1234567890",
            from_name="Test",
            timestamp=datetime.now(),
            text="URGENT: Call me back"
        )
        self.assertTrue(msg.is_task(["urgent", "call"]))


class TestWhatsAppMonitor(unittest.TestCase):
    """Unit tests for WhatsAppMonitor class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for test vault
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
        self.settings.is_whatsapp_configured = Mock(return_value=True)

        # Create monitor
        self.monitor = WhatsAppMonitor(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_monitor_init(self) -> None:
        """Test WhatsAppMonitor initialization."""
        self.assertEqual(self.monitor.business_account_id, "test_business_id")
        self.assertEqual(self.monitor.access_token, "test_token")
        self.assertEqual(self.monitor.phone_number_id, "test_phone_id")
        self.assertEqual(self.monitor.poll_interval, 30)
        self.assertFalse(self.monitor._running)

    def test_verify_webhook_success(self) -> None:
        """Test webhook verification success."""
        result = self.monitor.verify_webhook(
            mode="subscribe",
            token="test_verify_token",
            challenge="challenge_123"
        )
        self.assertEqual(result, "challenge_123")

    def test_verify_webhook_failure(self) -> None:
        """Test webhook verification failure."""
        result = self.monitor.verify_webhook(
            mode="subscribe",
            token="wrong_token",
            challenge="challenge_123"
        )
        self.assertIsNone(result)

    def test_handle_webhook_empty(self) -> None:
        """Test handling empty webhook payload."""
        payload = {}
        messages = self.monitor.handle_webhook(payload)
        self.assertEqual(len(messages), 0)

    def test_handle_webhook_with_messages(self) -> None:
        """Test handling webhook with messages."""
        payload = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "contacts": [{"wa_id": "+1234567890", "profile": {"name": "Test"}}],
                        "messages": [{
                            "id": "msg_1",
                            "from": "+1234567890",
                            "timestamp": "1708941000",
                            "text": {"body": "Please help me"}
                        }]
                    }
                }]
            }]
        }

        messages = self.monitor.handle_webhook(payload)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_id, "msg_1")
        self.assertEqual(messages[0].text, "Please help me")

    def test_parse_message_text(self) -> None:
        """Test parsing text message."""
        msg_data = {
            "id": "msg_1",
            "from": "+1234567890",
            "timestamp": "1708941000",
            "text": {"body": "Hello World"}
        }

        message = self.monitor._parse_message(msg_data, [])
        self.assertIsNotNone(message)
        self.assertEqual(message.text, "Hello World")
        self.assertEqual(message.from_number, "+1234567890")

    def test_parse_message_image(self) -> None:
        """Test parsing image message."""
        msg_data = {
            "id": "msg_2",
            "from": "+1234567890",
            "timestamp": "1708941000",
            "image": {"id": "image_123"}
        }

        message = self.monitor._parse_message(msg_data, [])
        self.assertIsNotNone(message)
        self.assertEqual(message.media_type, "image")
        self.assertEqual(message.media_id, "image_123")
        self.assertTrue(message.has_media())

    def test_parse_message_document(self) -> None:
        """Test parsing document message."""
        msg_data = {
            "id": "msg_3",
            "from": "+1234567890",
            "timestamp": "1708941000",
            "document": {"id": "doc_456", "filename": "invoice.pdf"}
        }

        message = self.monitor._parse_message(msg_data, [])
        self.assertIsNotNone(message)
        self.assertEqual(message.media_type, "document")
        self.assertEqual(message.media_id, "doc_456")

    def test_parse_message_audio(self) -> None:
        """Test parsing audio message."""
        msg_data = {
            "id": "msg_4",
            "from": "+1234567890",
            "timestamp": "1708941000",
            "audio": {"id": "audio_789"}
        }

        message = self.monitor._parse_message(msg_data, [])
        self.assertIsNotNone(message)
        self.assertEqual(message.media_type, "audio")

    def test_parse_message_video(self) -> None:
        """Test parsing video message."""
        msg_data = {
            "id": "msg_5",
            "from": "+1234567890",
            "timestamp": "1708941000",
            "video": {"id": "video_012"}
        }

        message = self.monitor._parse_message(msg_data, [])
        self.assertIsNotNone(message)
        self.assertEqual(message.media_type, "video")

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_poll_messages_empty(self, mock_retry: Mock) -> None:
        """Test polling messages when none available."""
        mock_retry.return_value = {}

        messages = self.monitor.poll_messages()
        self.assertEqual(len(messages), 0)

    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor._retry_request")
    def test_poll_messages_with_results(self, mock_retry: Mock) -> None:
        """Test polling messages with results."""
        mock_retry.return_value = {
            "messages": [
                {
                    "id": "msg_1",
                    "from": "+1234567890",
                    "timestamp": "1708941000",
                    "text": {"body": "Test message"}
                }
            ]
        }

        messages = self.monitor.poll_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, "Test message")

    def test_is_task_keyword_detection(self) -> None:
        """Test task keyword detection."""
        # Test with task keyword
        msg_task = WhatsAppMessage(
            message_id="msg_1",
            from_number="+1234567890",
            from_name="Test",
            timestamp=datetime.now(),
            text="I need your help please"
        )
        self.assertTrue(msg_task.is_task())

        # Test without task keyword
        msg_normal = WhatsAppMessage(
            message_id="msg_2",
            from_number="+1234567890",
            from_name="Test",
            timestamp=datetime.now(),
            text="Hey, good morning!"
        )
        self.assertFalse(msg_normal.is_task())

        # Test case insensitivity
        msg_upper = WhatsAppMessage(
            message_id="msg_3",
            from_number="+1234567890",
            from_name="Test",
            timestamp=datetime.now(),
            text="URGENT: Need this NOW"
        )
        self.assertTrue(msg_upper.is_task())

    def test_save_media_success(self) -> None:
        """Test saving media successfully."""
        media_content = b"fake media content"
        timestamp = datetime(2026, 2, 26, 10, 30, 0)

        file_path = self.monitor.save_media(
            media_content,
            "image",
            "+1234567890",
            timestamp
        )

        self.assertIsNotNone(file_path)
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.name.startswith("WHATSAPP_"))

        # Verify content
        with open(file_path, "rb") as f:
            content = f.read()
        self.assertEqual(content, media_content)

    def test_save_media_different_types(self) -> None:
        """Test saving different media types."""
        media_content = b"fake content"
        timestamp = datetime.now()

        # Test image
        img_path = self.monitor.save_media(media_content, "image", "+1234567890", timestamp)
        self.assertTrue(img_path.name.endswith(".jpg"))

        # Test document
        doc_path = self.monitor.save_media(media_content, "document", "+1234567890", timestamp)
        self.assertTrue(doc_path.name.endswith(".bin"))

        # Test audio
        audio_path = self.monitor.save_media(media_content, "audio", "+1234567890", timestamp)
        self.assertTrue(audio_path.name.endswith(".ogg"))

    def test_create_task_file_success(self) -> None:
        """Test creating task file successfully."""
        message = WhatsAppMessage(
            message_id="msg_123",
            from_number="+1234567890",
            from_name="John Doe",
            timestamp=datetime(2026, 2, 26, 10, 30, 0),
            text="Please complete this task"
        )

        task_file = self.monitor.create_task_file(message)

        self.assertIsNotNone(task_file)
        self.assertTrue(task_file.exists())
        self.assertTrue(task_file.name.startswith("WHATSAPP_"))
        self.assertTrue(task_file.name.endswith(".md"))

        # Verify content
        content = task_file.read_text()
        self.assertIn("---", content)  # YAML frontmatter
        self.assertIn("type: whatsapp_message", content)
        self.assertIn("John Doe", content)
        self.assertIn("Please complete this task", content)

    def test_create_task_file_with_media(self) -> None:
        """Test creating task file with media."""
        message = WhatsAppMessage(
            message_id="msg_123",
            from_number="+1234567890",
            from_name="Test",
            timestamp=datetime.now(),
            text="Check this image",
            media_type="image",
            media_id="media_123"  # Add media_id to trigger has_media
        )

        # Create dummy media file
        inbox_path = self.vault_path / "Inbox"
        media_file = inbox_path / "test_image.jpg"
        media_file.write_bytes(b"fake image")

        task_file = self.monitor.create_task_file(message, media_file)

        content = task_file.read_text()
        self.assertIn("test_image.jpg", content)
        # Note: has_media is based on media_id, not saved_media parameter
        self.assertIn("media_type: image", content)

    def test_process_messages_success(self) -> None:
        """Test processing messages successfully."""
        messages = [
            WhatsAppMessage(
                message_id="msg_1",
                from_number="+1234567890",
                from_name="Test1",
                timestamp=datetime.now(),
                text="Please help me"
            ),
            WhatsAppMessage(
                message_id="msg_2",
                from_number="+1234567891",
                from_name="Test2",
                timestamp=datetime.now(),
                text="Hey there"  # Not a task
            )
        ]

        processed = self.monitor.process_messages(messages)
        self.assertEqual(processed, 1)  # Only first message is a task

    def test_process_messages_with_media(self) -> None:
        """Test processing messages with media."""
        messages = [
            WhatsAppMessage(
                message_id="msg_1",
                from_number="+1234567890",
                from_name="Test",
                timestamp=datetime.now(),
                text="Check this",
                media_type="image",
                media_id="media_123"
            )
        ]

        # Mock download_media to return fake content
        with patch.object(self.monitor, 'download_media', return_value=b"fake media"):
            processed = self.monitor.process_messages(messages)
            self.assertEqual(processed, 1)

    def test_stop(self) -> None:
        """Test stopping the monitor."""
        self.monitor._running = True
        self.monitor.stop()
        self.assertFalse(self.monitor._running)

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.WhatsAppMonitor.run_once")
    def test_run_forever(self, mock_run_once: Mock, mock_sleep: Mock) -> None:
        """Test running monitor continuously."""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                self.monitor._running = False
            return 5

        mock_run_once.side_effect = side_effect

        # Run (will stop after 2 iterations)
        self.monitor.run_forever(poll_interval=1)

        # Verify
        self.assertEqual(call_count[0], 2)
        self.assertFalse(self.monitor._running)


class TestWhatsAppMonitorRetry(unittest.TestCase):
    """Unit tests for retry logic in WhatsAppMonitor."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "test_business_id"
        self.settings.WHATSAPP_ACCESS_TOKEN = "test_token"
        self.settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"
        self.settings.WHATSAPP_API_VERSION = "v18.0"
        self.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN = "test_verify_token"
        self.settings.WHATSAPP_POLL_INTERVAL = 30
        self.settings.WHATSAPP_TASK_KEYWORDS = ["please", "need", "urgent"]
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.RETRY_EXPONENTIAL_BACKOFF = True

        self.monitor = WhatsAppMonitor(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.requests.Session.request")
    def test_retry_request_success(self, mock_request: Mock, mock_sleep: Mock) -> None:
        """Test retry request that succeeds on first try."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.monitor._retry_request("GET", "https://api.example.com/test")

        self.assertEqual(result, {"success": True})
        mock_request.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.requests.Session.request")
    def test_retry_request_with_retries(self, mock_request: Mock, mock_sleep: Mock) -> None:
        """Test retry request that succeeds after failures."""
        import requests

        # Fail twice, succeed on third
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}
        mock_response_success.raise_for_status.return_value = None

        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_fail)

        mock_request.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        result = self.monitor._retry_request("GET", "https://api.example.com/test")

        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.whatsapp_monitor.requests.Session.request")
    def test_retry_rate_limit(self, mock_request: Mock, mock_sleep: Mock) -> None:
        """Test retry with rate limit (429)."""
        import requests

        mock_response_fail = Mock()
        mock_response_fail.status_code = 429
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_fail)

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}
        mock_response_success.raise_for_status.return_value = None

        mock_request.side_effect = [mock_response_fail, mock_response_success]

        result = self.monitor._retry_request("GET", "https://api.example.com/test")

        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
