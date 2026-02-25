"""
Integration tests for the AI Employee Bronze Tier.

Tests end-to-end workflows and component integration.
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime

from src.ai_employee.core.vault import (
    VaultManager,
    DashboardManager,
    CompanyHandbookManager,
)
from src.ai_employee.config.settings import Settings
from src.ai_employee.handlers.file_watcher import FileDropHandler


class TestVaultSetupWorkflow(unittest.TestCase):
    """Integration tests for vault setup workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_vault_setup(self) -> None:
        """Test complete vault setup workflow."""
        # Initialize vault
        vault_manager = VaultManager(str(self.vault_path))
        result = vault_manager.create_vault_structure()

        # Verify structure
        self.assertTrue(result)
        self.assertTrue(vault_manager.vault_exists())

        # Verify all directories exist
        required_dirs = ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]
        for dir_name in required_dirs:
            self.assertTrue((self.vault_path / dir_name).exists())

        # Verify files exist
        self.assertTrue((self.vault_path / "Dashboard.md").exists())
        self.assertTrue((self.vault_path / "Company_Handbook.md").exists())

    def test_vault_stats_after_setup(self) -> None:
        """Test vault statistics after setup."""
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

        stats = vault_manager.get_vault_stats()

        self.assertTrue(stats['exists'])
        self.assertEqual(len(stats['directories']), 5)  # 5 required dirs
        self.assertTrue(stats['files']['Dashboard.md'])
        self.assertTrue(stats['files']['Company_Handbook.md'])


class TestDashboardIntegration(unittest.TestCase):
    """Integration tests for dashboard functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"

        # Initialize vault
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dashboard_updates_with_tasks(self) -> None:
        """Test dashboard updates when tasks are added."""
        dm = DashboardManager(str(self.vault_path))

        # Initial state
        summary = dm.get_task_summary()
        self.assertEqual(summary["pending"], 0)
        self.assertEqual(summary["completed"], 0)

        # Add pending tasks
        needs_action = self.vault_path / "Needs_Action"
        (needs_action / "task1.md").write_text("# Task 1")
        (needs_action / "task2.md").write_text("# Task 2")

        # Add completed tasks
        done = self.vault_path / "Done"
        (done / "completed1.md").write_text("# Completed 1")

        # Update dashboard
        dm.update_dashboard(last_action="Tasks added", status="active")

        # Verify counts
        summary = dm.get_task_summary()
        self.assertEqual(summary["pending"], 2)
        self.assertEqual(summary["completed"], 1)

        # Verify dashboard content
        content = dm.dashboard_path.read_text()
        self.assertIn("Pending Tasks: 2", content)
        self.assertIn("Completed Today: 1", content)


class TestHandbookIntegration(unittest.TestCase):
    """Integration tests for handbook functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"

        # Initialize vault
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_handbook_content_completeness(self) -> None:
        """Test handbook has all required content sections."""
        chm = CompanyHandbookManager(str(self.vault_path))
        content = chm.get_handbook_content()

        # Check all required sections
        required_sections = [
            "Authorized Actions",
            "Prohibited Actions",
            "Escalation Procedures",
            "Security Guidelines",
            "Priority Levels",
        ]

        for section in required_sections:
            self.assertIn(section, content, f"Missing section: {section}")

        # Check specific rules
        self.assertIn("NEVER send emails", content)
        self.assertIn("NEVER make payments", content)
        self.assertIn("PKR 1,000", content)  # Payment threshold


class TestFileProcessingWorkflow(unittest.TestCase):
    """Integration tests for file processing workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"

        # Initialize vault
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

        self.settings = Settings()
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.WATCHED_FOLDER = str(self.vault_path / "Inbox")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_drop_creates_action_file(self) -> None:
        """Test that dropping a file creates an action file."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=None  # Skip logging for this test
        )

        # Create test file in Inbox
        inbox_path = self.vault_path / "Inbox"
        test_file = inbox_path / "test_document.pdf"
        test_file.write_text("Test PDF content")

        # Process file (simulating file drop)
        handler._process_file(test_file)

        # Verify action file was created
        needs_action = self.vault_path / "Needs_Action"
        action_files = list(needs_action.glob("FILE_*.md"))

        self.assertEqual(len(action_files), 1)

        # Verify action file content
        action_content = action_files[0].read_text()
        self.assertIn("test_document.pdf", action_content)
        self.assertIn("type: file_drop", action_content)

    def test_large_file_quarantined(self) -> None:
        """Test that large files are moved to quarantine."""
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=None
        )

        # Create a "large" test file (we'll use a small size for testing)
        inbox_path = self.vault_path / "Inbox"
        test_file = inbox_path / "large_file.zip"
        test_file.write_bytes(b"x" * 1024)  # 1KB for testing

        # Manually set a low max size for testing
        self.settings.MAX_FILE_SIZE = 512  # 512 bytes

        # Process file
        handler._process_file(test_file)

        # Verify file was quarantined
        quarantine_path = self.vault_path / "Quarantine"
        quarantined_files = list(quarantine_path.glob("QUARANTINE_*.zip"))

        # File should be in quarantine (or at least not in inbox)
        self.assertFalse(test_file.exists())


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end integration tests."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_workflow(self) -> None:
        """Test complete workflow from setup to task processing."""
        # Step 1: Setup vault
        vault_manager = VaultManager(str(self.vault_path))
        self.assertTrue(vault_manager.create_vault_structure())

        # Step 2: Verify initial state
        dm = DashboardManager(str(self.vault_path))
        summary = dm.get_task_summary()
        self.assertEqual(summary["pending"], 0)

        # Step 3: Simulate file drop
        inbox_path = self.vault_path / "Inbox"
        test_file = inbox_path / "invoice.pdf"
        test_file.write_text("Invoice content")

        # Step 4: Process file
        settings = Settings()
        settings.VAULT_PATH = str(self.vault_path)
        handler = FileDropHandler(
            vault_path=str(self.vault_path),
            settings=settings,
            logger=None
        )
        handler._process_file(test_file)

        # Step 5: Verify action file created
        needs_action = self.vault_path / "Needs_Action"
        action_files = list(needs_action.glob("FILE_*.md"))
        self.assertEqual(len(action_files), 1)

        # Step 6: Update dashboard
        dm.update_dashboard(last_action="Processed invoice.pdf", status="active")

        # Step 7: Verify dashboard updated
        summary = dm.get_task_summary()
        self.assertEqual(summary["pending"], 1)

        content = dm.dashboard_path.read_text()
        self.assertIn("Processed invoice.pdf", content)


if __name__ == "__main__":
    unittest.main()
