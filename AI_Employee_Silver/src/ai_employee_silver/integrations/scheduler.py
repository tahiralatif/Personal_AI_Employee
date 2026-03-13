"""
Scheduler for Silver Tier AI Employee.

This module implements the ScheduleManager class that:
- Supports cron-style scheduling
- Creates recurring tasks at scheduled times
- Handles timezones and holidays
- Persists schedules across restarts
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from croniter import croniter
import pytz

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class ScheduledTask:
    """
    Represents a scheduled task.

    Attributes:
        task_id: Unique task identifier
        name: Task name
        cron_expression: Cron schedule
        timezone: Task timezone
        description: Task description
        priority: Task priority
        last_run: Last execution time
        next_run: Next scheduled time
        enabled: Whether task is enabled
    """

    def __init__(
        self,
        task_id: str,
        name: str,
        cron_expression: str,
        timezone: str = "UTC",
        description: str = "",
        priority: str = "medium",
        enabled: bool = True
    ) -> None:
        """Initialize ScheduledTask."""
        self.task_id = task_id
        self.name = name
        self.cron_expression = cron_expression
        self.timezone = pytz.timezone(timezone)
        self.description = description
        self.priority = priority
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run = self._calculate_next_run()

    def _calculate_next_run(self) -> datetime:
        """Calculate next run time based on cron expression."""
        try:
            now = datetime.now(self.timezone)
            cron = croniter(self.cron_expression, now)
            return cron.get_next(datetime)
        except Exception:
            return datetime.now(self.timezone)

    def is_due(self) -> bool:
        """Check if task is due to run."""
        if not self.enabled:
            return False
        now = datetime.now(self.timezone)
        return now >= self.next_run

    def mark_executed(self) -> None:
        """Mark task as executed and calculate next run."""
        self.last_run = datetime.now(self.timezone)
        self.next_run = self._calculate_next_run()


class ScheduleManager:
    """
    Manages scheduled tasks.

    Responsibilities:
    - Parse cron expressions
    - Create tasks at scheduled times
    - Handle timezones
    - Holiday detection
    - Schedule persistence
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """Initialize ScheduleManager."""
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # Configuration
        self.timezone = pytz.timezone(self.settings.SCHEDULER_TIMEZONE)
        self.holiday_detection = self.settings.SCHEDULER_HOLIDAY_DETECTION
        self.holiday_region = self.settings.SCHEDULER_HOLIDAY_REGION

        # Schedules file
        self.vault_path = Path(self.settings.VAULT_PATH).expanduser()
        self.schedules_file = self.vault_path / "Plans" / "schedules.json"
        self.needs_action_path = self.vault_path / "Needs_Action"

        # Loaded schedules
        self.schedules: Dict[str, ScheduledTask] = {}

        # Running state
        self._running = False

        # Load existing schedules
        self._load_schedules()

    def _load_schedules(self) -> None:
        """Load schedules from file."""
        try:
            import json

            if self.schedules_file.exists():
                content = self.schedules_file.read_text(encoding='utf-8')
                data = json.loads(content)

                for task_id, task_data in data.items():
                    task = ScheduledTask(
                        task_id=task_id,
                        name=task_data.get("name", ""),
                        cron_expression=task_data.get("cron", ""),
                        timezone=task_data.get("timezone", "UTC"),
                        description=task_data.get("description", ""),
                        priority=task_data.get("priority", "medium"),
                        enabled=task_data.get("enabled", True)
                    )

                    if task_data.get("last_run"):
                        task.last_run = datetime.fromisoformat(task_data["last_run"])
                    if task_data.get("next_run"):
                        task.next_run = datetime.fromisoformat(task_data["next_run"])

                    self.schedules[task_id] = task

                self.logger.info(f"Loaded {len(self.schedules)} schedules")

        except Exception as e:
            self.logger.error(f"Failed to load schedules: {str(e)}")

    def _save_schedules(self) -> None:
        """Save schedules to file."""
        try:
            import json

            self.schedules_file.parent.mkdir(parents=True, exist_ok=True)

            data = {}
            for task_id, task in self.schedules.items():
                data[task_id] = {
                    "name": task.name,
                    "cron": task.cron_expression,
                    "timezone": str(task.timezone),
                    "description": task.description,
                    "priority": task.priority,
                    "enabled": task.enabled,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None
                }

            content = json.dumps(data, indent=2)
            self.schedules_file.write_text(content, encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Failed to save schedules: {str(e)}")

    def add_schedule(
        self,
        task_id: str,
        name: str,
        cron_expression: str,
        description: str = "",
        priority: str = "medium",
        timezone: str = "UTC"
    ) -> bool:
        """
        Add a new schedule.

        Args:
            task_id: Unique task ID
            name: Task name
            cron_expression: Cron expression
            description: Task description
            priority: Task priority
            timezone: Timezone

        Returns:
            True if successful
        """
        try:
            # Validate cron expression
            croniter(cron_expression)

            task = ScheduledTask(
                task_id=task_id,
                name=name,
                cron_expression=cron_expression,
                timezone=timezone,
                description=description,
                priority=priority
            )

            self.schedules[task_id] = task
            self._save_schedules()

            self.logger.info(f"Added schedule: {task_id} ({name})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add schedule: {str(e)}")
            return False

    def remove_schedule(self, task_id: str) -> bool:
        """Remove a schedule."""
        try:
            if task_id in self.schedules:
                del self.schedules[task_id]
                self._save_schedules()
                self.logger.info(f"Removed schedule: {task_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove schedule: {str(e)}")
            return False

    def create_task_file(self, task: ScheduledTask) -> Optional[Path]:
        """
        Create task file in Needs_Action.

        Args:
            task: ScheduledTask to create

        Returns:
            Path to created file or None
        """
        try:
            self.needs_action_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SCHEDULED_{timestamp}_{task.task_id}.md"
            file_path = self.needs_action_path / filename

            # Build content
            content = self._build_task_content(task)

            file_path.write_text(content, encoding='utf-8')

            self.logger.info(f"Created scheduled task: {filename}")
            self.logger.log_event(
                event_type="scheduled_task_created",
                detail=f"Created task from schedule: {task.name}",
                result="success",
                file_reference=str(file_path)
            )

            return file_path

        except Exception as e:
            self.logger.error(f"Failed to create task file: {str(e)}")
            return None

    def _build_task_content(self, task: ScheduledTask) -> str:
        """Build task file content."""
        frontmatter = {
            "type": "scheduled_task",
            "schedule_id": task.task_id,
            "schedule_name": task.name,
            "cron": task.cron_expression,
            "timezone": str(task.timezone),
            "priority": task.priority,
            "created": datetime.now().isoformat(),
            "status": "pending"
        }

        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")

        body = f"""# Scheduled Task: {task.name}

## Schedule Information
- **Task ID:** {task.task_id}
- **Cron Expression:** {task.cron_expression}
- **Timezone:** {task.timezone}
- **Priority:** {task.priority}

## Description
{task.description if task.description else "Recurring scheduled task"}

## Execution History
- **Last Run:** {task.last_run.strftime('%Y-%m-%d %H:%M:%S') if task.last_run else "Never"}
- **Next Run:** {task.next_run.strftime('%Y-%m-%d %H:%M:%S')}

## Suggested Next Steps
- [ ] Review the task
- [ ] Execute required actions
- [ ] Create a plan in /Plans/
- [ ] Move to /Done/ when complete

---
*Automatically generated by AI Employee Silver Tier - Scheduler*
"""
        return "\n".join(fm_lines) + body

    def is_holiday(self, date: Optional[datetime] = None) -> bool:
        """
        Check if date is a holiday.

        Args:
            date: Date to check (defaults to today)

        Returns:
            True if holiday
        """
        if not self.holiday_detection:
            return False

        try:
            import holidays

            if date is None:
                date = datetime.now()

            # Create holiday calendar
            if self.holiday_region:
                country_holidays = holidays.country_holidays(self.holiday_region)
                return date in country_holidays
            else:
                # Default to US holidays
                country_holidays = holidays.country_holidays("US")
                return date in country_holidays

        except ImportError:
            self.logger.warning("holidays package not installed, skipping holiday detection")
            return False
        except Exception as e:
            self.logger.error(f"Failed to check holiday: {str(e)}")
            return False

    def run_once(self) -> int:
        """
        Run one iteration of schedule checking.

        Returns:
            Number of tasks created
        """
        try:
            created_count = 0

            for task_id, task in self.schedules.items():
                # Check if task is due
                if task.is_due():
                    # Check for holiday
                    if self.is_holiday(task.next_run):
                        self.logger.info(f"Skipping {task.name} - holiday")
                        task.mark_executed()
                        continue

                    # Create task file
                    if self.create_task_file(task):
                        created_count += 1
                        task.mark_executed()

            # Save updated schedules
            if created_count > 0:
                self._save_schedules()

            return created_count

        except Exception as e:
            self.logger.error(f"Error in run_once: {str(e)}")
            return 0

    def run_forever(self, check_interval: int = 60) -> None:
        """
        Run scheduler continuously.

        Args:
            check_interval: Check interval in seconds
        """
        self._running = True
        self.logger.info(f"Starting scheduler (check interval: {check_interval}s)")

        try:
            while self._running:
                try:
                    self.run_once()
                except Exception as e:
                    self.logger.error(f"Error in scheduling loop: {str(e)}")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received, stopping scheduler")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the scheduler."""
        self.logger.info("Stopping scheduler...")
        self._running = False
        self._save_schedules()
        self.logger.log_event(
            event_type="system_stop",
            detail="Scheduler stopped",
            result="success"
        )

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        status = {
            "running": self._running,
            "timezone": str(self.timezone),
            "holiday_detection": self.holiday_detection,
            "holiday_region": self.holiday_region,
            "schedules": []
        }

        for task_id, task in self.schedules.items():
            status["schedules"].append({
                "id": task_id,
                "name": task.name,
                "cron": task.cron_expression,
                "enabled": task.enabled,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None
            })

        return status


def create_scheduler(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> ScheduleManager:
    """Factory function to create ScheduleManager instance."""
    return ScheduleManager(settings, logger)


if __name__ == "__main__":
    print("Starting Scheduler (Test Mode)...")

    settings = get_settings()
    logger = get_logger()

    scheduler = create_scheduler(settings, logger)

    print(f"✓ Scheduler initialized (timezone: {settings.SCHEDULER_TIMEZONE})")

    # Add test schedule
    scheduler.add_schedule(
        task_id="daily_report",
        name="Daily Report",
        cron_expression="0 9 * * *",  # Every day at 9 AM
        description="Generate daily report",
        priority="high"
    )

    print(f"✓ Added test schedule")
    print(f"✓ Loaded {len(scheduler.schedules)} schedules")

    # Run once
    created = scheduler.run_once()
    print(f"✓ Created {created} tasks")

    print("\nTo run continuously: python -m src.ai_employee_silver.main start scheduler")
