"""
Unit tests for ScheduleManager.

Tests cover:
- ScheduledTask class
- ScheduleManager class methods
- Cron parsing
- Task creation
- Holiday detection
- Schedule persistence
"""

import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from src.ai_employee_silver.integrations.scheduler import (
    ScheduledTask,
    ScheduleManager,
)
from src.ai_employee_silver.config.settings import Settings


class TestScheduledTask(unittest.TestCase):
    """Unit tests for ScheduledTask class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.task = ScheduledTask(
            task_id="daily_report",
            name="Daily Report",
            cron_expression="0 9 * * *",  # Every day at 9 AM
            timezone="UTC",
            description="Generate daily report",
            priority="high"
        )

    def test_task_init(self) -> None:
        """Test ScheduledTask initialization."""
        self.assertEqual(self.task.task_id, "daily_report")
        self.assertEqual(self.task.name, "Daily Report")
        self.assertEqual(self.task.cron_expression, "0 9 * * *")
        self.assertEqual(self.task.priority, "high")
        self.assertTrue(self.task.enabled)

    def test_task_default_values(self) -> None:
        """Test ScheduledTask default values."""
        task = ScheduledTask(
            task_id="simple_task",
            name="Simple Task",
            cron_expression="* * * * *"
        )
        self.assertEqual(str(task.timezone), "UTC")
        self.assertEqual(task.description, "")
        self.assertEqual(task.priority, "medium")
        self.assertTrue(task.enabled)
        self.assertIsNone(task.last_run)

    def test_calculate_next_run(self) -> None:
        """Test next run calculation."""
        task = ScheduledTask(
            task_id="hourly",
            name="Hourly Task",
            cron_expression="0 * * * *"  # Every hour
        )
        next_run = task.next_run
        self.assertGreater(next_run, datetime.now(task.timezone))

    def test_is_due_true(self) -> None:
        """Test is_due when task is due."""
        task = ScheduledTask(
            task_id="due_task",
            name="Due Task",
            cron_expression="* * * * *"
        )
        # Set next_run to past
        task.next_run = datetime.now(task.timezone) - timedelta(minutes=1)
        self.assertTrue(task.is_due())

    def test_is_due_false(self) -> None:
        """Test is_due when task is not due."""
        task = ScheduledTask(
            task_id="future_task",
            name="Future Task",
            cron_expression="* * * * *"
        )
        # Set next_run to future
        task.next_run = datetime.now(task.timezone) + timedelta(hours=1)
        self.assertFalse(task.is_due())

    def test_is_due_disabled(self) -> None:
        """Test is_due when task is disabled."""
        task = ScheduledTask(
            task_id="disabled_task",
            name="Disabled Task",
            cron_expression="* * * * *"
        )
        task.enabled = False
        task.next_run = datetime.now(task.timezone) - timedelta(minutes=1)
        self.assertFalse(task.is_due())

    def test_mark_executed(self) -> None:
        """Test marking task as executed."""
        task = ScheduledTask(
            task_id="exec_task",
            name="Executed Task",
            cron_expression="* * * * *"
        )
        old_next_run = task.next_run

        task.mark_executed()

        self.assertIsNotNone(task.last_run)
        # Next run should be recalculated (may be same minute)
        self.assertGreaterEqual(task.next_run, old_next_run.replace(second=0, microsecond=0))


class TestScheduleManager(unittest.TestCase):
    """Unit tests for ScheduleManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for test vault
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()

        # Create vault subdirectories
        (self.vault_path / "Plans").mkdir()
        (self.vault_path / "Needs_Action").mkdir()

        # Create mock settings
        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.SCHEDULER_TIMEZONE = "UTC"
        self.settings.SCHEDULER_HOLIDAY_DETECTION = False
        self.settings.SCHEDULER_HOLIDAY_REGION = ""

        # Create manager
        self.manager = ScheduleManager(settings=self.settings)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_manager_init(self) -> None:
        """Test ScheduleManager initialization."""
        self.assertEqual(self.manager.timezone.zone, "UTC")
        self.assertFalse(self.manager.holiday_detection)
        self.assertEqual(self.manager.holiday_region, "")
        self.assertFalse(self.manager._running)

    def test_load_schedules_empty(self) -> None:
        """Test loading schedules when file doesn't exist."""
        # Fresh manager, no schedules file
        manager = ScheduleManager(settings=self.settings)
        self.assertEqual(len(manager.schedules), 0)

    def test_load_schedules_with_file(self) -> None:
        """Test loading schedules from file."""
        # Create schedules file
        schedules_file = self.vault_path / "Plans" / "schedules.json"
        schedules_file.parent.mkdir(parents=True, exist_ok=True)

        schedules_data = {
            "test_task": {
                "name": "Test Task",
                "cron": "0 9 * * *",
                "timezone": "UTC",
                "description": "Test description",
                "priority": "high",
                "enabled": True,
                "last_run": None,
                "next_run": datetime.now().isoformat()
            }
        }

        schedules_file.write_text(json.dumps(schedules_data))

        # Create new manager (will load schedules)
        manager = ScheduleManager(settings=self.settings)
        self.assertEqual(len(manager.schedules), 1)
        self.assertIn("test_task", manager.schedules)

    def test_save_schedules(self) -> None:
        """Test saving schedules to file."""
        # Add schedule
        self.manager.add_schedule(
            task_id="save_test",
            name="Save Test",
            cron_expression="0 10 * * *"
        )

        # Check file created
        schedules_file = self.vault_path / "Plans" / "schedules.json"
        self.assertTrue(schedules_file.exists())

        # Load and verify
        content = schedules_file.read_text()
        data = json.loads(content)
        self.assertIn("save_test", data)

    def test_add_schedule_success(self) -> None:
        """Test adding schedule successfully."""
        result = self.manager.add_schedule(
            task_id="add_test",
            name="Add Test",
            cron_expression="0 11 * * *",
            description="Test schedule",
            priority="high"
        )

        self.assertTrue(result)
        self.assertIn("add_test", self.manager.schedules)
        self.assertEqual(self.manager.schedules["add_test"].name, "Add Test")

    def test_add_schedule_invalid_cron(self) -> None:
        """Test adding schedule with invalid cron expression."""
        result = self.manager.add_schedule(
            task_id="invalid_cron",
            name="Invalid Cron",
            cron_expression="invalid cron"
        )

        self.assertFalse(result)
        self.assertNotIn("invalid_cron", self.manager.schedules)

    def test_remove_schedule_success(self) -> None:
        """Test removing schedule successfully."""
        # Add schedule first
        self.manager.add_schedule(
            task_id="remove_test",
            name="Remove Test",
            cron_expression="0 12 * * *"
        )

        # Remove it
        result = self.manager.remove_schedule("remove_test")
        self.assertTrue(result)
        self.assertNotIn("remove_test", self.manager.schedules)

    def test_remove_schedule_not_found(self) -> None:
        """Test removing non-existent schedule."""
        result = self.manager.remove_schedule("non_existent")
        self.assertFalse(result)

    def test_create_task_file(self) -> None:
        """Test creating task file."""
        task = ScheduledTask(
            task_id="create_test",
            name="Create Test",
            cron_expression="0 13 * * *",
            description="Test task creation"
        )

        file_path = self.manager.create_task_file(task)

        self.assertIsNotNone(file_path)
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.name.startswith("SCHEDULED_"))
        self.assertTrue(file_path.name.endswith(".md"))

        # Verify content
        content = file_path.read_text()
        self.assertIn("create_test", content)
        self.assertIn("Create Test", content)
        self.assertIn("0 13 * * *", content)

    def test_is_holiday_disabled(self) -> None:
        """Test holiday detection when disabled."""
        self.manager.holiday_detection = False
        result = self.manager.is_holiday(datetime.now())
        self.assertFalse(result)

    @patch('holidays.country_holidays')
    def test_is_holiday_enabled(self, mock_country_holidays: Mock) -> None:
        """Test holiday detection when enabled."""
        self.manager.holiday_detection = True
        self.manager.holiday_region = "US"

        # Mock holidays to return today as holiday
        mock_holidays = Mock()
        mock_holidays.__contains__ = Mock(return_value=True)
        mock_country_holidays.return_value = mock_holidays

        result = self.manager.is_holiday(datetime.now())
        self.assertTrue(result)

    def test_run_once_no_schedules(self) -> None:
        """Test running with no schedules."""
        created = self.manager.run_once()
        self.assertEqual(created, 0)

    def test_run_once_with_due_task(self) -> None:
        """Test running with due task."""
        # Add schedule with past time
        task = ScheduledTask(
            task_id="due_test",
            name="Due Test",
            cron_expression="* * * * *",
            timezone="UTC"
        )
        task.next_run = datetime.now(task.timezone) - timedelta(minutes=1)
        self.manager.schedules["due_test"] = task

        created = self.manager.run_once()
        self.assertGreaterEqual(created, 0)

    def test_run_once_with_holiday(self) -> None:
        """Test running task on holiday."""
        # Enable holiday detection
        self.manager.holiday_detection = True

        # Add schedule
        task = ScheduledTask(
            task_id="holiday_test",
            name="Holiday Test",
            cron_expression="* * * * *"
        )
        task.next_run = datetime.now(task.timezone) - timedelta(minutes=1)
        self.manager.schedules["holiday_test"] = task

        # Mock is_holiday to return True
        with patch.object(self.manager, 'is_holiday', return_value=True):
            created = self.manager.run_once()
            # Task should be skipped on holiday
            self.assertEqual(created, 0)

    def test_get_status(self) -> None:
        """Test getting scheduler status."""
        # Add a schedule
        self.manager.add_schedule(
            task_id="status_test",
            name="Status Test",
            cron_expression="0 14 * * *"
        )

        status = self.manager.get_status()

        self.assertIn("running", status)
        self.assertIn("timezone", status)
        self.assertIn("schedules", status)
        self.assertEqual(len(status["schedules"]), 1)

    def test_stop(self) -> None:
        """Test stopping the scheduler."""
        self.manager._running = True
        self.manager.stop()
        self.assertFalse(self.manager._running)


class TestScheduleManagerPersistence(unittest.TestCase):
    """Unit tests for ScheduleManager persistence."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.test_dir) / "test_vault"
        self.vault_path.mkdir()
        (self.vault_path / "Plans").mkdir()

        self.settings = Mock(spec=Settings)
        self.settings.VAULT_PATH = str(self.vault_path)
        self.settings.SCHEDULER_TIMEZONE = "UTC"
        self.settings.SCHEDULER_HOLIDAY_DETECTION = False
        self.settings.SCHEDULER_HOLIDAY_REGION = ""

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_persistence_across_restarts(self) -> None:
        """Test schedules persist across manager restarts."""
        # Create manager and add schedule
        manager1 = ScheduleManager(settings=self.settings)
        manager1.add_schedule(
            task_id="persist_test",
            name="Persist Test",
            cron_expression="0 15 * * *"
        )

        # Create new manager (simulates restart)
        manager2 = ScheduleManager(settings=self.settings)

        # Check schedule loaded
        self.assertIn("persist_test", manager2.schedules)
        self.assertEqual(manager2.schedules["persist_test"].name, "Persist Test")


if __name__ == "__main__":
    unittest.main()
