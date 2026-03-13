"""
Unit tests for LinkedInPoster.

Tests cover:
- LinkedInPost class
- LinkedInPoster class methods
- Post parsing
- Post publishing
- Engagement metrics
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from src.ai_employee_silver.integrations.linkedin_poster import (
    LinkedInPost,
    LinkedInPoster,
)
from src.ai_employee_silver.config.settings import Settings


class TestLinkedInPost(unittest.TestCase):
    """Unit tests for LinkedInPost class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.post = LinkedInPost(
            post_id="post_123",
            content="Test post content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            image_path="/path/to/image.jpg",
            status="pending"
        )

    def test_post_init(self) -> None:
        """Test LinkedInPost initialization."""
        self.assertEqual(self.post.post_id, "post_123")
        self.assertEqual(self.post.content, "Test post content")
        self.assertEqual(self.post.status, "pending")
        self.assertEqual(self.post.image_path, "/path/to/image.jpg")

    def test_post_default_values(self) -> None:
        """Test LinkedInPost default values."""
        post = LinkedInPost(
            post_id="post_456",
            content="Simple post",
            scheduled_time=datetime.now()
        )
        self.assertIsNone(post.image_path)
        self.assertEqual(post.status, "pending")
        self.assertIsNone(post.published_url)
        self.assertEqual(post.engagement, {"likes": 0, "comments": 0, "shares": 0})


class TestLinkedInPoster(unittest.TestCase):
    """Unit tests for LinkedInPoster class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for test vault
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        # Create vault subdirectories
        (self.vault_path / "Plans").mkdir()
        (self.vault_path / "Done").mkdir()
        (self.vault_path / "Needs_Action").mkdir()

        # Create mock settings
        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.LINKEDIN_CLIENT_ID = "test_client_id"
        self.settings.LINKEDIN_CLIENT_SECRET = "test_secret"
        self.settings.LINKEDIN_ACCESS_TOKEN = "test_token"
        self.settings.LINKEDIN_ORGANIZATION_ID = "test_org_id"
        self.settings.LINKEDIN_API_VERSION = "202402"
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1
        self.settings.is_linkedin_configured = Mock(return_value=True)

        # Create poster
        self.poster = LinkedInPoster(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_poster_init(self) -> None:
        """Test LinkedInPoster initialization."""
        self.assertEqual(self.poster.organization_id, "test_org_id")
        self.assertEqual(self.poster.api_version, "202402")
        self.assertFalse(self.poster._running)

    def test_authenticate_success(self) -> None:
        """Test authentication success."""
        with patch.object(self.poster, '_retry_request', return_value={"id": "user123"}):
            result = self.poster.authenticate()
            self.assertTrue(result)

    def test_authenticate_failure(self) -> None:
        """Test authentication failure."""
        with patch.object(self.poster, '_retry_request', return_value=None):
            result = self.poster.authenticate()
            self.assertFalse(result)

    def test_read_scheduled_posts_empty(self) -> None:
        """Test reading scheduled posts when folder is empty."""
        posts = self.poster.read_scheduled_posts()
        self.assertEqual(len(posts), 0)

    def test_read_scheduled_posts_with_files(self) -> None:
        """Test reading scheduled posts with post files."""
        # Create test post file
        post_file = self.vault_path / "Plans" / "test_post.md"
        post_file.write_text("""---
type: linkedin_post
scheduled_time: 2026-02-27T09:00:00
status: pending
---

# Test Post Content

This is a test LinkedIn post.
""")

        posts = self.poster.read_scheduled_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].post_id, "test_post")

    def test_parse_post_file_success(self) -> None:
        """Test parsing post file successfully."""
        post_file = self.vault_path / "Plans" / "parsed_post.md"
        post_file.write_text("""---
type: linkedin_post
scheduled_time: 2026-02-27T10:00:00
status: pending
image_path: /path/to/image.jpg
---

# Amazing News

We're launching something great!
""")

        post = self.poster._parse_post_file(post_file)
        self.assertIsNotNone(post)
        self.assertEqual(post.post_id, "parsed_post")
        self.assertIn("Amazing News", post.content)
        self.assertEqual(post.image_path, "/path/to/image.jpg")

    def test_parse_post_file_invalid(self) -> None:
        """Test parsing invalid post file."""
        post_file = self.vault_path / "Plans" / "invalid.md"
        post_file.write_text("# Just a regular markdown file")

        post = self.poster._parse_post_file(post_file)
        self.assertIsNone(post)

    def test_parse_post_file_wrong_type(self) -> None:
        """Test parsing post file with wrong type."""
        post_file = self.vault_path / "Plans" / "wrong_type.md"
        post_file.write_text("""---
type: whatsapp_message
status: pending
---

Not a LinkedIn post.
""")

        post = self.poster._parse_post_file(post_file)
        self.assertIsNone(post)

    @patch("src.ai_employee_silver.integrations.linkedin_poster.LinkedInPoster._retry_request")
    def test_publish_post_success(self, mock_retry: Mock) -> None:
        """Test publishing post successfully."""
        mock_retry.return_value = {
            "id": "share_123",
            "permalink": "https://linkedin.com/posts/test"
        }

        post = LinkedInPost(
            post_id="publish_test",
            content="Test content",
            scheduled_time=datetime.now() - timedelta(minutes=1),  # In the past
            status="pending"
        )

        # Create post file
        post_file = self.vault_path / "Plans" / "publish_test.md"
        post_file.write_text(f"""---
type: linkedin_post
scheduled_time: {post.scheduled_time.isoformat()}
status: pending
---

{post.content}
""")

        result = self.poster.publish_post(post)
        self.assertTrue(result)
        self.assertEqual(post.status, "published")

    @patch("src.ai_employee_silver.integrations.linkedin_poster.LinkedInPoster._retry_request")
    def test_publish_post_failure(self, mock_retry: Mock) -> None:
        """Test publishing post failure."""
        mock_retry.return_value = None

        post = LinkedInPost(
            post_id="fail_test",
            content="Test content",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            status="pending"
        )

        # Create post file
        post_file = self.vault_path / "Plans" / "fail_test.md"
        post_file.write_text(f"""---
type: linkedin_post
scheduled_time: {post.scheduled_time.isoformat()}
status: pending
---

{post.content}
""")

        result = self.poster.publish_post(post)
        self.assertFalse(result)
        self.assertEqual(post.status, "failed")

    def test_publish_post_not_yet_scheduled(self) -> None:
        """Test publishing post before scheduled time."""
        post = LinkedInPost(
            post_id="future_test",
            content="Future post",
            scheduled_time=datetime.now() + timedelta(hours=1),
            status="pending"
        )

        result = self.poster.publish_post(post)
        self.assertFalse(result)

    def test_create_post_payload(self) -> None:
        """Test creating post payload."""
        post = LinkedInPost(
            post_id="payload_test",
            content="Test post content" * 10,  # Long content
            scheduled_time=datetime.now()
        )

        payload = self.poster._create_post_payload(post)

        self.assertIn("owner", payload)
        self.assertIn("text", payload)
        self.assertIn("visibility", payload)
        # Check content truncation
        self.assertLessEqual(len(payload["text"]["text"]), 1300)

    def test_get_engagement_metrics(self) -> None:
        """Test getting engagement metrics."""
        with patch.object(self.poster, '_retry_request', return_value={
            "elements": [
                {"actionType": "LIKE", "total": {"count": 10}},
                {"actionType": "COMMENT", "total": {"count": 5}},
                {"actionType": "SHARE", "total": {"count": 2}}
            ]
        }):
            metrics = self.poster.get_engagement_metrics("share_123")
            self.assertEqual(metrics["likes"], 10)
            self.assertEqual(metrics["comments"], 5)
            self.assertEqual(metrics["shares"], 2)

    def test_move_to_done(self) -> None:
        """Test moving published post to Done folder."""
        # Create post file in Plans
        post_file = self.vault_path / "Plans" / "move_test.md"
        post_file.write_text("---\ntype: linkedin_post\n---\nContent")

        post = LinkedInPost(
            post_id="move_test",
            content="Test",
            scheduled_time=datetime.now()
        )

        self.poster._move_to_done(post)

        # Check file moved
        done_file = self.vault_path / "Done" / "move_test.md"
        self.assertTrue(done_file.exists())
        self.assertFalse(post_file.exists())

    def test_move_to_needs_action(self) -> None:
        """Test moving failed post to Needs_Action folder."""
        # Create post file in Plans
        post_file = self.vault_path / "Plans" / "fail_move_test.md"
        post_file.write_text("---\ntype: linkedin_post\n---\nContent")

        post = LinkedInPost(
            post_id="fail_move_test",
            content="Test",
            scheduled_time=datetime.now()
        )

        self.poster._move_to_needs_action(post, "Test error message")

        # Check file moved with error
        needs_action_file = self.vault_path / "Needs_Action" / "fail_move_test.md"
        self.assertTrue(needs_action_file.exists())
        content = needs_action_file.read_text()
        self.assertIn("Test error message", content)

    def test_run_once(self) -> None:
        """Test running one iteration."""
        # Create scheduled post (in the past)
        post_file = self.vault_path / "Plans" / "run_test.md"
        past_time = datetime.now() - timedelta(minutes=1)
        post_file.write_text(f"""---
type: linkedin_post
scheduled_time: {past_time.isoformat()}
status: pending
---

Test content
""")

        with patch.object(self.poster, '_retry_request', return_value={
            "id": "share_123",
            "permalink": "https://linkedin.com/posts/test"
        }):
            published = self.poster.run_once()
            self.assertGreaterEqual(published, 0)

    def test_stop(self) -> None:
        """Test stopping the poster."""
        self.poster._running = True
        self.poster.stop()
        self.assertFalse(self.poster._running)


class TestLinkedInPosterRetry(unittest.TestCase):
    """Unit tests for LinkedInPoster retry logic."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.LINKEDIN_CLIENT_ID = "test_client"
        self.settings.LINKEDIN_CLIENT_SECRET = "test_secret"
        self.settings.LINKEDIN_ACCESS_TOKEN = "test_token"
        self.settings.LINKEDIN_ORGANIZATION_ID = "test_org"
        self.settings.LINKEDIN_API_VERSION = "202402"
        self.settings.MAX_RETRY_ATTEMPTS = 3
        self.settings.RETRY_INITIAL_DELAY = 0.01
        self.settings.RETRY_MAX_DELAY = 0.1

        self.poster = LinkedInPoster(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.linkedin_poster.requests.Session.request")
    def test_retry_request_success(self, mock_request: Mock, mock_sleep: Mock) -> None:
        """Test retry request that succeeds on first try."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.poster._retry_request("GET", "https://api.linkedin.com/test")
        self.assertEqual(result, {"success": True})
        mock_request.assert_called_once()

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.linkedin_poster.requests.Session.request")
    def test_retry_with_retries(self, mock_request: Mock, mock_sleep: Mock) -> None:
        """Test retry request that succeeds after failures."""
        import requests

        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_fail)

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}
        mock_response_success.raise_for_status.return_value = None

        mock_request.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        result = self.poster._retry_request("GET", "https://api.linkedin.com/test")
        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_request.call_count, 3)

    @patch("time.sleep")
    @patch("src.ai_employee_silver.integrations.linkedin_poster.requests.Session.request")
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

        result = self.poster._retry_request("GET", "https://api.linkedin.com/test")
        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
