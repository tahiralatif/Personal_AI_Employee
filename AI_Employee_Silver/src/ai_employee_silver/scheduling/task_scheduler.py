"""
Task Scheduler for AI Employee Silver Tier.

This module implements cross-platform task scheduling using APScheduler.
Supports daily, weekly, monthly, and quarterly scheduled tasks.

Agent Skills:
    - scheduler.start() -> bool
    - scheduler.stop() -> bool
    - scheduler.schedule_task(name, cron_expr, callback) -> bool
    - scheduler.list_scheduled_tasks() -> list
    - scheduler.get_next_run(name) -> str
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    name: str
    description: str
    cron_expression: str
    callback_name: str
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    last_status: str = "pending"
    last_error: Optional[str] = None


class TaskScheduler:
    """
    Cross-platform Task Scheduler using APScheduler.
    
    This scheduler manages recurring tasks for the AI Employee system
    including daily briefings, weekly posts, monthly reports, and quarterly reviews.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Task Scheduler.
        
        Args:
            vault_path: Path to the AI Employee vault
            settings: Application settings
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        
        # Scheduler configuration
        self.scheduler = BackgroundScheduler(
            timezone=self.settings.SCHEDULER_TIMEZONE if hasattr(self.settings, 'SCHEDULER_TIMEZONE') else 'UTC'
        )
        
        # Tasks directory
        self.tasks_dir = self.vault_path / "Logs" / "scheduled_tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        
        # Task registry
        self.tasks: Dict[str, ScheduledTask] = {}
        self.callbacks: Dict[str, Callable] = {}
        
        # Load existing tasks
        self._load_tasks()
        
        # Register built-in callbacks
        self._register_builtin_callbacks()
        
        # Running state
        self._running = False
    
    def _register_builtin_callbacks(self) -> None:
        """Register built-in callback functions."""
        self.callbacks = {
            "daily_business_summary": self._daily_business_summary,
            "weekly_linkedin_post": self._weekly_linkedin_post,
            "monthly_expense_tracking": self._monthly_expense_tracking,
            "quarterly_review": self._quarterly_review,
            "health_monitoring": self._health_monitoring,
            "auto_check_expired_approvals": self._auto_check_expired_approvals,
            "dashboard_update": self._dashboard_update,
        }
    
    def _load_tasks(self) -> None:
        """Load scheduled tasks from disk."""
        try:
            tasks_file = self.tasks_dir / "scheduled_tasks.json"
            if tasks_file.exists():
                data = json.loads(tasks_file.read_text())
                for task_data in data.get("tasks", []):
                    task = ScheduledTask(**task_data)
                    self.tasks[task.name] = task
                self.logger.debug(f"Loaded {len(self.tasks)} scheduled tasks")
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
    
    def _save_tasks(self) -> None:
        """Save scheduled tasks to disk."""
        try:
            tasks_file = self.tasks_dir / "scheduled_tasks.json"
            data = {
                "tasks": [asdict(task) for task in self.tasks.values()],
                "last_updated": datetime.now().isoformat()
            }
            tasks_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    def start(self) -> Dict[str, Any]:
        """
        Start the scheduler.
        
        Agent Skill: scheduler.start
        
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if self._running:
                return {"success": False, "error": "Scheduler already running"}
            
            self.logger.info("Starting task scheduler...")
            
            # Start APScheduler
            self.scheduler.start()
            self._running = True
            
            # Schedule default tasks
            self._schedule_default_tasks()
            
            self.logger.info("Task scheduler started successfully")
            
            return {
                "success": True,
                "message": "Scheduler started",
                "tasks_scheduled": len(self.tasks)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            return {"success": False, "error": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop the scheduler.
        
        Agent Skill: scheduler.stop
        
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self._running:
                return {"success": False, "error": "Scheduler not running"}
            
            self.logger.info("Stopping task scheduler...")
            
            # Stop APScheduler
            self.scheduler.shutdown(wait=True)
            self._running = False
            
            # Save tasks
            self._save_tasks()
            
            self.logger.info("Task scheduler stopped")
            
            return {"success": True, "message": "Scheduler stopped"}
            
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_task(
        self,
        name: str,
        cron_expression: str,
        callback_name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Schedule a new task.
        
        Agent Skill: scheduler.schedule_task
        
        Args:
            name: Task name
            cron_expression: Cron expression (e.g., "0 8 * * *" for daily at 8 AM)
            callback_name: Name of callback function to execute
            description: Task description
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            self.logger.info(f"Scheduling task: {name}")
            
            # Validate callback exists
            if callback_name not in self.callbacks:
                return {
                    "success": False,
                    "error": f"Unknown callback: {callback_name}"
                }
            
            # Parse cron expression
            trigger = self._parse_cron_expression(cron_expression)
            
            # Create task
            task = ScheduledTask(
                name=name,
                description=description or name,
                cron_expression=cron_expression,
                callback_name=callback_name
            )
            
            # Add to scheduler
            self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                args=[name],
                id=name,
                replace_existing=True
            )
            
            # Update next run time
            job = self.scheduler.get_job(name)
            if job:
                task.next_run = job.next_run_time.isoformat() if job.next_run_time else None
            
            # Store task
            self.tasks[name] = task
            self._save_tasks()
            
            self.logger.info(f"Task scheduled: {name} (next run: {task.next_run})")
            
            return {
                "success": True,
                "task_name": name,
                "next_run": task.next_run
            }
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_cron_expression(self, cron_expr: str) -> CronTrigger:
        """
        Parse cron expression into APScheduler trigger.
        
        Args:
            cron_expr: Cron expression
            
        Returns:
            APScheduler CronTrigger
        """
        # Support special expressions
        if cron_expr == "@daily":
            return CronTrigger(hour=0, minute=0)
        elif cron_expr == "@hourly":
            return CronTrigger(minute=0)
        elif cron_expr == "@weekly":
            return CronTrigger(day_of_week="sun", hour=0, minute=0)
        elif cron_expr == "@monthly":
            return CronTrigger(day=1, hour=0, minute=0)
        
        # Parse standard cron expression (minute hour day month day_of_week)
        parts = cron_expr.split()
        
        if len(parts) == 5:
            return CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
        elif len(parts) == 6:
            return CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                year=parts[5]
            )
        else:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
    
    def _execute_task(self, task_name: str) -> None:
        """
        Execute a scheduled task.
        
        Args:
            task_name: Name of task to execute
        """
        try:
            self.logger.info(f"Executing scheduled task: {task_name}")
            
            if task_name not in self.tasks:
                self.logger.error(f"Task not found: {task_name}")
                return
            
            task = self.tasks[task_name]
            
            # Get callback
            if task.callback_name not in self.callbacks:
                self.logger.error(f"Callback not found: {task.callback_name}")
                return
            
            callback = self.callbacks[task.callback_name]
            
            # Execute callback
            result = callback()
            
            # Update task status
            task.last_run = datetime.now().isoformat()
            task.run_count += 1
            task.last_status = "success" if result.get("success", False) else "failed"
            task.last_error = result.get("error")
            
            # Update next run time
            job = self.scheduler.get_job(task_name)
            if job:
                task.next_run = job.next_run_time.isoformat() if job.next_run_time else None
            
            # Log execution
            self._log_task_execution(task, result)
            
            self.logger.info(f"Task executed: {task_name} (status: {task.last_status})")
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {task_name} - {e}")
            if task_name in self.tasks:
                self.tasks[task_name].last_status = "failed"
                self.tasks[task_name].last_error = str(e)
    
    def _log_task_execution(self, task: ScheduledTask, result: Dict[str, Any]) -> None:
        """Log task execution to file."""
        try:
            log_file = self.tasks_dir / f"{task.name}_log.jsonl"
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "task_name": task.name,
                "status": task.last_status,
                "run_count": task.run_count,
                "error": task.last_error,
                "result": result
            }
            
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to log task execution: {e}")
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        List all scheduled tasks.
        
        Agent Skill: scheduler.list_scheduled_tasks
        
        Returns:
            List of task info dictionaries
        """
        tasks = []
        
        for name, task in self.tasks.items():
            tasks.append({
                "name": task.name,
                "description": task.description,
                "cron_expression": task.cron_expression,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "next_run": task.next_run,
                "run_count": task.run_count,
                "last_status": task.last_status
            })
        
        return tasks
    
    def get_next_run(self, task_name: str) -> Dict[str, Any]:
        """
        Get next run time for a task.
        
        Agent Skill: scheduler.get_next_run
        
        Args:
            task_name: Task name
            
        Returns:
            dict with 'success' (bool) and 'next_run' (str) or 'error' (str)
        """
        try:
            if task_name not in self.tasks:
                return {"success": False, "error": f"Task not found: {task_name}"}
            
            task = self.tasks[task_name]
            
            # Get fresh next run time from scheduler
            job = self.scheduler.get_job(task_name)
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
            else:
                next_run = task.next_run
            
            return {
                "success": True,
                "task_name": task_name,
                "next_run": next_run,
                "cron_expression": task.cron_expression
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get next run: {e}")
            return {"success": False, "error": str(e)}
    
    def _schedule_default_tasks(self) -> None:
        """Schedule default tasks for AI Employee."""
        default_tasks = [
            {
                "name": "daily_business_summary",
                "cron": "0 8 * * *",  # Daily at 8 AM
                "callback": "daily_business_summary",
                "description": "Generate daily business summary briefing"
            },
            {
                "name": "weekly_linkedin_post",
                "cron": "0 9 * * 1",  # Weekly on Monday at 9 AM
                "callback": "weekly_linkedin_post",
                "description": "Schedule weekly LinkedIn post"
            },
            {
                "name": "health_monitoring",
                "cron": "*/30 * * * *",  # Every 30 minutes
                "callback": "health_monitoring",
                "description": "Monitor system health"
            },
            {
                "name": "auto_check_expired_approvals",
                "cron": "0 * * * *",  # Every hour
                "callback": "auto_check_expired_approvals",
                "description": "Check and auto-reject expired approvals"
            },
            {
                "name": "dashboard_update",
                "cron": "*/5 * * * *",  # Every 5 minutes
                "callback": "dashboard_update",
                "description": "Update dashboard metrics"
            }
        ]
        
        for task_config in default_tasks:
            try:
                self.schedule_task(
                    name=task_config["name"],
                    cron_expression=task_config["cron"],
                    callback_name=task_config["callback"],
                    description=task_config["description"]
                )
            except Exception as e:
                self.logger.error(f"Failed to schedule default task {task_config['name']}: {e}")
    
    # =========================================================================
    # Built-in Callback Functions
    # =========================================================================
    
    def _daily_business_summary(self) -> Dict[str, Any]:
        """Generate daily business summary."""
        try:
            self.logger.info("Generating daily business summary...")
            
            # Import dashboard manager
            from ..core.dashboard_manager import get_dashboard_manager
            dashboard = get_dashboard_manager()
            
            # Generate briefing
            result = dashboard.generate_briefing(period="daily")
            
            if result["success"]:
                # Save briefing to file
                briefing_file = self.vault_path / "Briefings" / f"daily_{datetime.now().strftime('%Y%m%d')}.md"
                briefing_file.parent.mkdir(parents=True, exist_ok=True)
                briefing_file.write_text(result["briefing"], encoding='utf-8')
                
                return {
                    "success": True,
                    "briefing_path": str(briefing_file)
                }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _weekly_linkedin_post(self) -> Dict[str, Any]:
        """Schedule weekly LinkedIn post."""
        try:
            self.logger.info("Scheduling weekly LinkedIn post...")
            
            # Import LinkedIn MCP server
            from ..mcp.linkedin_mcp import get_linkedin_server
            linkedin = get_linkedin_server()
            
            # Initialize and login
            if not linkedin.initialize():
                return {"success": False, "error": "Failed to initialize LinkedIn"}
            
            if not linkedin.login():
                return {"success": False, "error": "Failed to login to LinkedIn"}
            
            # Generate sales content
            content_result = linkedin.generate_sales_content(
                topic="AI Automation Services",
                services=["Consulting", "Implementation", "Training"],
                tone="professional"
            )
            
            if content_result["success"]:
                # Post to LinkedIn
                post_result = linkedin.post(
                    content=content_result["content"],
                    hashtags=["AIAutomation", "BusinessGrowth", "Innovation"]
                )
                
                linkedin.close()
                return post_result
            
            linkedin.close()
            return content_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _monthly_expense_tracking(self) -> Dict[str, Any]:
        """Track monthly expenses."""
        try:
            self.logger.info("Tracking monthly expenses...")
            
            # This would integrate with accounting system
            # For now, generate summary report
            report = {
                "month": datetime.now().strftime("%Y-%m"),
                "generated": datetime.now().isoformat(),
                "status": "Expense tracking not yet implemented"
            }
            
            # Save report
            report_file = self.vault_path / "Reports" / f"expenses_{datetime.now().strftime('%Y%m')}.md"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            report_file.write_text(
                f"# Monthly Expense Report\n\n## {report['month']}\n\n{report['status']}\n",
                encoding='utf-8'
            )
            
            return {"success": True, "report_path": str(report_file)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _quarterly_review(self) -> Dict[str, Any]:
        """Prepare quarterly review."""
        try:
            self.logger.info("Preparing quarterly review...")
            
            # Import dashboard manager
            from ..core.dashboard_manager import get_dashboard_manager
            dashboard = get_dashboard_manager()
            
            # Generate quarterly briefing
            result = dashboard.generate_briefing(period="monthly")  # Using monthly as approximation
            
            if result["success"]:
                # Save review
                quarter = (datetime.now().month - 1) // 3 + 1
                review_file = self.vault_path / "Briefings" / f"quarterly_Q{quarter}_{datetime.now().year}.md"
                review_file.parent.mkdir(parents=True, exist_ok=True)
                review_file.write_text(result["briefing"], encoding='utf-8')
                
                return {
                    "success": True,
                    "review_path": str(review_file)
                }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _health_monitoring(self) -> Dict[str, Any]:
        """Monitor system health."""
        try:
            self.logger.debug("Running health monitoring...")
            
            # Import dashboard manager
            from ..core.dashboard_manager import get_dashboard_manager
            dashboard = get_dashboard_manager()
            
            # Get health status
            health = dashboard.get_health_status()
            
            if health["success"]:
                # Log health status
                self.logger.info(f"System health: {health['status']}")
                
                return {
                    "success": True,
                    "health_status": health["status"],
                    "uptime_hours": health.get("uptime_hours", 0),
                    "error_count_24h": health.get("error_count_24h", 0)
                }
            
            return health
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _auto_check_expired_approvals(self) -> Dict[str, Any]:
        """Check and auto-reject expired approvals."""
        try:
            self.logger.debug("Checking expired approvals...")
            
            # Import approval workflow
            from ..core.approval_workflow import get_approval_workflow
            approval = get_approval_workflow()
            
            # Auto-check expired
            rejected_count = approval.auto_check_expired()
            
            if rejected_count > 0:
                self.logger.info(f"Auto-rejected {rejected_count} expired approvals")
            
            return {
                "success": True,
                "rejected_count": rejected_count
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _dashboard_update(self) -> Dict[str, Any]:
        """Update dashboard metrics."""
        try:
            self.logger.debug("Updating dashboard...")
            
            # Import dashboard manager
            from ..core.dashboard_manager import get_dashboard_manager
            dashboard = get_dashboard_manager()
            
            # Get current metrics
            stats = dashboard.get_statistics()
            
            if stats["success"]:
                # Update dashboard file
                dashboard._update_dashboard_file()
                
                return {
                    "success": True,
                    "task_metrics": stats["task_metrics"],
                    "watcher_metrics": stats["watcher_metrics"]
                }
            
            return stats
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this scheduler.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "scheduler.start": self.start,
            "scheduler.stop": self.stop,
            "scheduler.schedule_task": self.schedule_task,
            "scheduler.list_scheduled_tasks": self.list_scheduled_tasks,
            "scheduler.get_next_run": self.get_next_run,
        }


# Global instance
_task_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """Get or create global Task Scheduler instance."""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler(
            vault_path=get_settings().VAULT_PATH
        )
    return _task_scheduler


if __name__ == "__main__":
    # Test Task Scheduler
    print("=== Task Scheduler Test ===\n")
    
    settings = get_settings()
    scheduler = TaskScheduler(vault_path=settings.VAULT_PATH)
    
    # Start scheduler
    result = scheduler.start()
    if result["success"]:
        print(f"✓ Scheduler started ({result['tasks_scheduled']} tasks)")
        
        # List tasks
        tasks = scheduler.list_scheduled_tasks()
        print(f"\n✓ Scheduled tasks: {len(tasks)}")
        for task in tasks:
            print(f"  - {task['name']}: {task['description']}")
            print(f"    Cron: {task['cron_expression']}")
            print(f"    Next run: {task['next_run']}")
        
        # Test get next run
        next_run = scheduler.get_next_run("daily_business_summary")
        if next_run["success"]:
            print(f"\n✓ Daily summary next run: {next_run['next_run']}")
        
        # Stop scheduler
        result = scheduler.stop()
        if result["success"]:
            print(f"\n✓ Scheduler stopped")
    else:
        print(f"✗ Failed to start scheduler: {result.get('error')}")
