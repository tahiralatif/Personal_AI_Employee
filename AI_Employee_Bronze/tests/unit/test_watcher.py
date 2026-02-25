"""
Unit tests for the file watcher module.

Tests FileDropHandler and WatcherService classes.
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.ai_employee.handlers.file_watcher import (
    FileDropHandler,
    WatcherService,
    create_watcher_service,
)
from src.ai_employee.config.settings import Settings, get_settings
from src.ai_employee.utils.logger import VaultLogger, get_logger


class TestFileDropHandler(unittest.TestCase):
    """Test cases for FileDropHandler class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir(parents=True)

        # Create required directories
        for dir_name in ["Inbox", "Needs_Action", "Done", "Logs", "Quarantine"]:
            (self.vault_path / dir_name).mkdir()

        self.settings = get_settings()
        self.logger = get_logger()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_handler_created(self) -> None:
        """Test that FileDropHandler can be instantiated."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )
        self.assertIsInstance(handler, FileDropHandler)

    def test_is_in_inbox(self) -> None:
        """Test _is_in_inbox method."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        inbox_file = self.vault_path / "Inbox" / "test.txt"
        other_file = self.vault_path / "Done" / "test.txt"

        self.assertTrue(handler._is_in_inbox(inbox_file))
        self.assertFalse(handler._is_in_inbox(other_file))

    def test_build_frontmatter(self) -> None:
        """Test _build_frontmatter method."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        test_file = self.vault_path / "Inbox" / "test_document.pdf"
        test_file.touch()

        frontmatter = handler._build_frontmatter(test_file)

        self.assertIn("type", frontmatter)
        self.assertIn("original_name", frontmatter)
        self.assertIn("received", frontmatter)
        self.assertIn("priority", frontmatter)
        self.assertIn("status", frontmatter)

        self.assertEqual(frontmatter["type"], "file_drop")
        self.assertEqual(frontmatter["original_name"], "test_document.pdf")
        self.assertEqual(frontmatter["priority"], "medium")
        self.assertEqual(frontmatter["status"], "pending")

    def test_format_file_size(self) -> None:
        """Test _format_file_size method."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        self.assertEqual(handler._format_file_size(1024), "1.00 KB")
        self.assertEqual(handler._format_file_size(1048576), "1.00 MB")
        self.assertEqual(handler._format_file_size(512), "512.00 B")

    def test_create_action_file(self) -> None:
        """Test _create_action_file method."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        test_file = self.vault_path / "Inbox" / "test_input.txt"
        test_file.write_text("Test content")

        action_file_path = handler._create_action_file(test_file)

        self.assertIsNotNone(action_file_path)
        self.assertTrue(action_file_path.exists())
        self.assertTrue(str(action_file_path).startswith(str(self.vault_path / "Needs_Action")))

    def test_action_file_content(self) -> None:
        """Test that action file has correct content structure."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        test_file = self.vault_path / "Inbox" / "test_input.txt"
        test_file.write_text("Test content")

        action_file_path = handler._create_action_file(test_file)
        content = action_file_path.read_text()

        self.assertIn("---", content)  # YAML frontmatter
        self.assertIn("type: file_drop", content)
        self.assertIn("original_name: test_input.txt", content)
        self.assertIn("# Task: Process", content)


class TestWatcherService(unittest.TestCase):
    """Test cases for WatcherService class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir(parents=True)

        # Create required directories
        for dir_name in ["Inbox", "Needs_Action", "Done", "Logs"]:
            (self.vault_path / dir_name).mkdir()

        self.settings = get_settings()
        self.logger = get_logger()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_service_created(self) -> None:
        """Test that WatcherService can be instantiated."""
        service = WatcherService(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )
        self.assertIsInstance(service, WatcherService)

    def test_service_not_running_initially(self) -> None:
        """Test that service is not running initially."""
        service = WatcherService(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )
        self.assertFalse(service.is_running())

    def test_start_service(self) -> None:
        """Test starting the watcher service."""
        service = WatcherService(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        result = service.start()
        self.assertTrue(result)
        self.assertTrue(service.is_running())

        service.stop()

    def test_stop_service(self) -> None:
        """Test stopping the watcher service."""
        service = WatcherService(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )

        service.start()
        service.stop()

        self.assertFalse(service.is_running())

    def test_create_watcher_service_factory(self) -> None:
        """Test create_watcher_service factory function."""
        service = create_watcher_service(vault_path=str(self.vault_path))
        self.assertIsInstance(service, WatcherService)


if __name__ == "__main__":
    unittest.main()
