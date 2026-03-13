"""
Unit tests for Silver Tier Settings.
"""

import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestSettings(unittest.TestCase):
    """Unit tests for Settings class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary .env file for testing
        self.test_dir = tempfile.mkdtemp()
        self.env_file = Path(self.test_dir) / ".env"
        # Clear global settings cache before each test
        self._clear_settings_cache()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clear global settings cache after each test
        self._clear_settings_cache()

    def _clear_settings_cache(self) -> None:
        """Clear the global settings cache."""
        try:
            from src.ai_employee_silver.config import settings as settings_module
            settings_module._settings = None
        except Exception:
            pass

    def test_settings_loads_from_env_file(self) -> None:
        """Test that settings loads from .env file."""
        # Create test .env file with unique values
        env_content = """
VAULT_PATH=/tmp/test_vault_unique
WATCHED_FOLDER=/tmp/test_vault_unique/Inbox
LOG_LEVEL=DEBUG
GMAIL_CLIENT_ID=test-client-id-unique
GMAIL_CLIENT_SECRET=test-secret-unique
GMAIL_POLL_INTERVAL=30
"""
        self.env_file.write_text(env_content)

        # Import and test Settings with isolated environment
        from src.ai_employee_silver.config.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(str(self.env_file))

            self.assertEqual(settings.VAULT_PATH, "/tmp/test_vault_unique")
            self.assertEqual(settings.WATCHED_FOLDER, "/tmp/test_vault_unique/Inbox")
            self.assertEqual(settings.LOG_LEVEL, "DEBUG")
            self.assertEqual(settings.GMAIL_CLIENT_ID, "test-client-id-unique")
            self.assertEqual(settings.GMAIL_POLL_INTERVAL, 30)

    def test_settings_required_variable_missing(self) -> None:
        """Test that missing required variable raises ValueError."""
        # Create incomplete .env file (missing VAULT_PATH)
        env_content = """
WATCHED_FOLDER=/tmp/test_vault_unique/Inbox
"""
        self.env_file.write_text(env_content)

        from src.ai_employee_silver.config.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                Settings(str(self.env_file))

    def test_settings_parse_list(self) -> None:
        """Test that comma-separated lists are parsed correctly."""
        env_content = """
VAULT_PATH=/tmp/test_vault_unique
WATCHED_FOLDER=/tmp/test_vault_unique/Inbox
WHATSAPP_TASK_KEYWORDS=please,need,urgent,task
"""
        self.env_file.write_text(env_content)

        from src.ai_employee_silver.config.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(str(self.env_file))

            self.assertEqual(
                settings.WHATSAPP_TASK_KEYWORDS,
                ["please", "need", "urgent", "task"]
            )

    def test_settings_is_gmail_configured(self) -> None:
        """Test Gmail configuration check."""
        env_content = """
VAULT_PATH=/tmp/test_vault_unique
WATCHED_FOLDER=/tmp/test_vault_unique/Inbox
GMAIL_CLIENT_ID=test-id-unique
GMAIL_CLIENT_SECRET=test-secret-unique
"""
        self.env_file.write_text(env_content)

        from src.ai_employee_silver.config.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(str(self.env_file))
            self.assertTrue(settings.is_gmail_configured())

    def test_settings_is_gmail_configured_missing(self) -> None:
        """Test Gmail configuration check with missing credentials."""
        env_content = """
VAULT_PATH=/tmp/test_vault_unique
WATCHED_FOLDER=/tmp/test_vault_unique/Inbox
GMAIL_CLIENT_ID=test-id-unique
"""
        self.env_file.write_text(env_content)

        from src.ai_employee_silver.config.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(str(self.env_file))
            self.assertFalse(settings.is_gmail_configured())

    def test_settings_default_values(self) -> None:
        """Test that default values are applied correctly."""
        env_content = """
VAULT_PATH=/tmp/test_vault_unique
WATCHED_FOLDER=/tmp/test_vault_unique/Inbox
"""
        self.env_file.write_text(env_content)

        from src.ai_employee_silver.config.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(str(self.env_file))

            # Check defaults
            self.assertEqual(settings.LOG_LEVEL, "INFO")
            self.assertEqual(settings.GMAIL_POLL_INTERVAL, 60)
            self.assertEqual(settings.WHATSAPP_POLL_INTERVAL, 30)
            self.assertEqual(settings.SCHEDULER_TIMEZONE, "UTC")
            self.assertEqual(settings.MAX_RETRY_ATTEMPTS, 3)
            self.assertFalse(settings.MCP_ENABLED)


if __name__ == "__main__":
    unittest.main()
