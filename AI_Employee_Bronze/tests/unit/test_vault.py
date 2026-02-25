"""
Unit tests for the vault management module.

Tests VaultManager, DashboardManager, and CompanyHandbookManager classes.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.ai_employee.core.vault import (
    VaultManager,
    DashboardManager,
    CompanyHandbookManager,
    initialize_vault,
)


class TestVaultManager(unittest.TestCase):
    """Test cases for VaultManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_vault_initializer_created(self) -> None:
        """Test that VaultManager can be instantiated."""
        vault_manager = VaultManager(str(self.vault_path))
        self.assertIsInstance(vault_manager, VaultManager)

    def test_create_vault_structure(self) -> None:
        """Test vault structure creation."""
        vault_manager = VaultManager(str(self.vault_path))
        result = vault_manager.create_vault_structure()

        self.assertTrue(result)
        self.assertTrue(self.vault_path.exists())

    def test_required_directories_created(self) -> None:
        """Test that all required directories are created."""
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

        required_dirs = ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]
        for dir_name in required_dirs:
            dir_path = self.vault_path / dir_name
            self.assertTrue(dir_path.exists(), f"{dir_name} directory not created")
            self.assertTrue(dir_path.is_dir(), f"{dir_name} is not a directory")

    def test_dashboard_created(self) -> None:
        """Test that Dashboard.md is created."""
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

        dashboard_path = self.vault_path / "Dashboard.md"
        self.assertTrue(dashboard_path.exists())

    def test_handbook_created(self) -> None:
        """Test that Company_Handbook.md is created."""
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

        handbook_path = self.vault_path / "Company_Handbook.md"
        self.assertTrue(handbook_path.exists())

    def test_vault_exists(self) -> None:
        """Test vault_exists method."""
        vault_manager = VaultManager(str(self.vault_path))

        # Should not exist before creation
        self.assertFalse(vault_manager.vault_exists())

        # Should exist after creation
        vault_manager.create_vault_structure()
        self.assertTrue(vault_manager.vault_exists())

    def test_vault_exists_partial(self) -> None:
        """Test vault_exists with partial structure."""
        vault_manager = VaultManager(str(self.vault_path))

        # Create only the main directory
        self.vault_path.mkdir(parents=True)

        # Should return False (missing subdirectories)
        self.assertFalse(vault_manager.vault_exists())

    def test_get_vault_stats(self) -> None:
        """Test get_vault_stats method."""
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

        stats = vault_manager.get_vault_stats()

        self.assertIn('path', stats)
        self.assertIn('exists', stats)
        self.assertIn('directories', stats)
        self.assertIn('files', stats)
        self.assertTrue(stats['exists'])

    def test_initialize_vault_function(self) -> None:
        """Test the initialize_vault convenience function."""
        result = initialize_vault(str(self.vault_path))
        self.assertTrue(result)
        self.assertTrue(self.vault_path.exists())


class TestDashboardManager(unittest.TestCase):
    """Test cases for DashboardManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dashboard_manager_created(self) -> None:
        """Test that DashboardManager can be instantiated."""
        dm = DashboardManager(str(self.vault_path))
        self.assertIsInstance(dm, DashboardManager)

    def test_count_pending_tasks_empty(self) -> None:
        """Test counting pending tasks when folder is empty."""
        dm = DashboardManager(str(self.vault_path))
        count = dm.count_pending_tasks()
        self.assertEqual(count, 0)

    def test_count_pending_tasks_with_files(self) -> None:
        """Test counting pending tasks with files present."""
        dm = DashboardManager(str(self.vault_path))

        # Create test files
        needs_action_path = self.vault_path / "Needs_Action"
        (needs_action_path / "task1.md").touch()
        (needs_action_path / "task2.md").touch()
        (needs_action_path / "task3.md").touch()

        count = dm.count_pending_tasks()
        self.assertEqual(count, 3)

    def test_count_completed_tasks_empty(self) -> None:
        """Test counting completed tasks when folder is empty."""
        dm = DashboardManager(str(self.vault_path))
        count = dm.count_completed_tasks()
        self.assertEqual(count, 0)

    def test_count_completed_tasks_with_files(self) -> None:
        """Test counting completed tasks with files present."""
        dm = DashboardManager(str(self.vault_path))

        # Create test files
        done_path = self.vault_path / "Done"
        (done_path / "completed1.md").touch()
        (done_path / "completed2.md").touch()

        count = dm.count_completed_tasks()
        self.assertEqual(count, 2)

    def test_get_task_summary(self) -> None:
        """Test getting task summary."""
        dm = DashboardManager(str(self.vault_path))

        # Create test files
        needs_action_path = self.vault_path / "Needs_Action"
        done_path = self.vault_path / "Done"
        (needs_action_path / "pending.md").touch()
        (done_path / "completed.md").touch()

        summary = dm.get_task_summary()

        self.assertEqual(summary["pending"], 1)
        self.assertEqual(summary["completed"], 1)

    def test_update_dashboard(self) -> None:
        """Test updating dashboard."""
        dm = DashboardManager(str(self.vault_path))
        result = dm.update_dashboard(last_action="Test action", status="active")

        self.assertTrue(result)
        self.assertTrue(dm.dashboard_path.exists())

    def test_dashboard_content_format(self) -> None:
        """Test that dashboard content has correct format."""
        dm = DashboardManager(str(self.vault_path))
        dm.update_dashboard(last_action="Test action", status="active")

        content = dm.dashboard_path.read_text()

        self.assertIn("# AI Employee Dashboard", content)
        self.assertIn("## Status", content)
        self.assertIn("## Task Summary", content)
        self.assertIn("## Quick Links", content)
        self.assertIn("Test action", content)


class TestCompanyHandbookManager(unittest.TestCase):
    """Test cases for CompanyHandbookManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        vault_manager = VaultManager(str(self.vault_path))
        vault_manager.create_vault_structure()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_handbook_manager_created(self) -> None:
        """Test that CompanyHandbookManager can be instantiated."""
        chm = CompanyHandbookManager(str(self.vault_path))
        self.assertIsInstance(chm, CompanyHandbookManager)

    def test_handbook_exists(self) -> None:
        """Test handbook_exists method."""
        chm = CompanyHandbookManager(str(self.vault_path))
        # Handbook is created by VaultManager
        self.assertTrue(chm.handbook_exists())

    def test_get_handbook_content(self) -> None:
        """Test getting handbook content."""
        chm = CompanyHandbookManager(str(self.vault_path))
        content = chm.get_handbook_content()

        self.assertIsNotNone(content)
        self.assertIn("# Company Handbook for AI Employee", content)

    def test_update_handbook(self) -> None:
        """Test updating handbook."""
        chm = CompanyHandbookManager(str(self.vault_path))
        custom_content = "# Custom Handbook\n\nCustom content here."
        result = chm.update_handbook(custom_content)

        self.assertTrue(result)
        self.assertEqual(chm.get_handbook_content(), custom_content)

    def test_handbook_template_sections(self) -> None:
        """Test that handbook template has all required sections."""
        chm = CompanyHandbookManager(str(self.vault_path))
        content = chm.get_handbook_content()

        required_sections = [
            "Authorized Actions",
            "Prohibited Actions",
            "Escalation Procedures",
            "Security Guidelines",
        ]

        for section in required_sections:
            self.assertIn(section, content, f"Missing section: {section}")


if __name__ == "__main__":
    unittest.main()
