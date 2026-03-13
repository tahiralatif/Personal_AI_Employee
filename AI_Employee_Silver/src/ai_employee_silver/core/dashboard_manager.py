"""
Enhanced Dashboard Manager for AI Employee Silver Tier.

This module implements dashboard updates with performance metrics,
task completion analytics, and system health monitoring.

Agent Skills:
    - dashboard.update_status(metrics) -> bool
    - dashboard.get_statistics() -> dict
    - dashboard.get_health_status() -> dict
    - dashboard.generate_briefing() -> str
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


@dataclass
class TaskMetrics:
    """Task completion metrics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    completion_rate: float = 0.0
    avg_completion_time: float = 0.0  # minutes


@dataclass
class WatcherMetrics:
    """Watcher performance metrics."""
    gmail_processed: int = 0
    whatsapp_processed: int = 0
    linkedin_processed: int = 0
    filesystem_processed: int = 0
    total_processed: int = 0


@dataclass
class MCPMetrics:
    """MCP server usage metrics."""
    email_actions: int = 0
    browser_actions: int = 0
    linkedin_actions: int = 0
    total_actions: int = 0


@dataclass
class SystemHealth:
    """System health status."""
    status: str = "healthy"  # healthy, degraded, critical
    uptime_hours: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[str] = None
    error_count_24h: int = 0
    watchers_active: int = 0
    mcp_servers_active: int = 0


class DashboardManager:
    """
    Enhanced Dashboard Manager for AI Employee system.
    
    This manager updates Dashboard.md with real-time statistics,
    performance metrics, and system health monitoring.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Dashboard Manager.
        
        Args:
            vault_path: Path to the AI Employee vault
            settings: Application settings
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        
        # Dashboard file
        self.dashboard_path = self.vault_path / "Dashboard.md"
        
        # Metrics storage
        self.metrics_path = self.vault_path / "Logs" / "metrics.json"
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics
        self.task_metrics = TaskMetrics()
        self.watcher_metrics = WatcherMetrics()
        self.mcp_metrics = MCPMetrics()
        self.system_health = SystemHealth()
        
        # Load existing metrics
        self._load_metrics()
        
        # System start time
        self.start_time = datetime.now()
    
    def _load_metrics(self) -> None:
        """Load metrics from storage."""
        try:
            if self.metrics_path.exists():
                data = json.loads(self.metrics_path.read_text())
                
                if "task_metrics" in data:
                    self.task_metrics = TaskMetrics(**data["task_metrics"])
                if "watcher_metrics" in data:
                    self.watcher_metrics = WatcherMetrics(**data["watcher_metrics"])
                if "mcp_metrics" in data:
                    self.mcp_metrics = MCPMetrics(**data["mcp_metrics"])
                if "system_health" in data:
                    self.system_health = SystemHealth(**data["system_health"])
                    
                self.logger.debug("Metrics loaded from storage")
        except Exception as e:
            self.logger.error(f"Failed to load metrics: {e}")
    
    def _save_metrics(self) -> None:
        """Save metrics to storage."""
        try:
            data = {
                "task_metrics": asdict(self.task_metrics),
                "watcher_metrics": asdict(self.watcher_metrics),
                "mcp_metrics": asdict(self.mcp_metrics),
                "system_health": asdict(self.system_health),
                "last_updated": datetime.now().isoformat()
            }
            
            self.metrics_path.write_text(json.dumps(data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    def update_status(
        self,
        task_metrics: Optional[Dict[str, Any]] = None,
        watcher_metrics: Optional[Dict[str, Any]] = None,
        mcp_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update dashboard status with new metrics.
        
        Agent Skill: dashboard.update_status
        
        Args:
            task_metrics: Optional task metrics update
            watcher_metrics: Optional watcher metrics update
            mcp_metrics: Optional MCP metrics update
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            # Update metrics
            if task_metrics:
                for key, value in task_metrics.items():
                    if hasattr(self.task_metrics, key):
                        setattr(self.task_metrics, key, value)
            
            if watcher_metrics:
                for key, value in watcher_metrics.items():
                    if hasattr(self.watcher_metrics, key):
                        setattr(self.watcher_metrics, key, value)
            
            if mcp_metrics:
                for key, value in mcp_metrics.items():
                    if hasattr(self.mcp_metrics, key):
                        setattr(self.mcp_metrics, key, value)
            
            # Recalculate totals
            self._recalculate_metrics()
            
            # Save metrics
            self._save_metrics()
            
            # Update dashboard file
            self._update_dashboard_file()
            
            self.logger.info("Dashboard status updated")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
            return {"success": False, "error": str(e)}
    
    def _recalculate_metrics(self) -> None:
        """Recalculate derived metrics."""
        # Task completion rate
        total = self.task_metrics.total_tasks
        if total > 0:
            self.task_metrics.completion_rate = (
                self.task_metrics.completed_tasks / total
            ) * 100
        
        # Watcher totals
        self.watcher_metrics.total_processed = (
            self.watcher_metrics.gmail_processed +
            self.watcher_metrics.whatsapp_processed +
            self.watcher_metrics.linkedin_processed +
            self.watcher_metrics.filesystem_processed
        )
        
        # MCP totals
        self.mcp_metrics.total_actions = (
            self.mcp_metrics.email_actions +
            self.mcp_metrics.browser_actions +
            self.mcp_metrics.linkedin_actions
        )
        
        # System health
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        self.system_health.uptime_hours = round(uptime, 2)
        
        # Determine health status
        if self.system_health.error_count_24h > 10:
            self.system_health.status = "critical"
        elif self.system_health.error_count_24h > 5:
            self.system_health.status = "degraded"
        else:
            self.system_health.status = "healthy"
    
    def _update_dashboard_file(self) -> None:
        """Update Dashboard.md file."""
        try:
            content = self._generate_dashboard_content()
            
            if self.dashboard_path.exists():
                self.dashboard_path.write_text(content, encoding='utf-8')
            else:
                self.dashboard_path.write_text(content, encoding='utf-8')
                
        except Exception as e:
            self.logger.error(f"Failed to update dashboard file: {e}")
    
    def _generate_dashboard_content(self) -> str:
        """
        Generate Dashboard.md content.
        
        Returns:
            Complete markdown content string
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""---
type: dashboard
last_updated: {now}
version: 2.0
---

# 🤖 AI Employee Dashboard - Silver Tier

**Last Updated:** {now}  
**System Status:** {self._get_status_badge(self.system_health.status)}  
**Uptime:** {self.system_health.uptime_hours} hours

---

## 📊 Quick Statistics

| Metric | Value |
|--------|-------|
| Total Tasks | {self.task_metrics.total_tasks} |
| Completion Rate | {self.task_metrics.completion_rate:.1f}% |
| Items Processed | {self.watcher_metrics.total_processed} |
| Actions Executed | {self.mcp_metrics.total_actions} |

---

## 📈 Task Analytics

### Task Status Breakdown

```
Completed:  {self._progress_bar(self.task_metrics.completed_tasks, self.task_metrics.total_tasks)} {self.task_metrics.completed_tasks}
Failed:     {self._progress_bar(self.task_metrics.failed_tasks, self.task_metrics.total_tasks)} {self.task_metrics.failed_tasks}
Pending:    {self._progress_bar(self.task_metrics.pending_tasks, self.task_metrics.total_tasks)} {self.task_metrics.pending_tasks}
```

**Average Completion Time:** {self.task_metrics.avg_completion_time:.1f} minutes

---

## 👁️ Watcher Performance

| Watcher | Items Processed |
|---------|-----------------|
| Gmail | {self.watcher_metrics.gmail_processed} |
| WhatsApp | {self.watcher_metrics.whatsapp_processed} |
| LinkedIn | {self.watcher_metrics.linkedin_processed} |
| File System | {self.watcher_metrics.filesystem_processed} |
| **Total** | **{self.watcher_metrics.total_processed}** |

---

## 🤖 MCP Server Actions

| Server | Actions |
|--------|---------|
| Email | {self.mcp_metrics.email_actions} |
| Browser | {self.mcp_metrics.browser_actions} |
| LinkedIn | {self.mcp_metrics.linkedin_actions} |
| **Total** | **{self.mcp_metrics.total_actions}** |

---

## 💚 System Health

| Metric | Value |
|--------|-------|
| Status | {self._get_status_badge(self.system_health.status)} |
| Uptime | {self.system_health.uptime_hours} hours |
| Active Watchers | {self.system_health.watchers_active} |
| Active MCP Servers | {self.system_health.mcp_servers_active} |
| Errors (24h) | {self.system_health.error_count_24h} |

**Last Error:** {self.system_health.last_error or "None"}  
**Last Error Time:** {self.system_health.last_error_time or "N/A"}

---

## 📅 Recent Activity

*Activity log is updated in real-time as tasks are processed.*

| Time | Type | Description | Status |
|------|------|-------------|--------|
| - | - | - | - |

---

## 🎯 Today's Goals

- [ ] Process all pending items in Needs_Action/
- [ ] Execute all approved plans
- [ ] Generate daily briefing
- [ ] Update performance metrics

---

## 🔗 Quick Links

- [Needs_Action/](Needs_Action/) - Items requiring processing
- [Plans/](Plans/) - Active and completed plans
- [Pending_Approval/](Pending_Approval/) - Awaiting approval
- [Done/](Done/) - Completed tasks
- [Logs/](Logs/) - System logs

---

*Generated by AI Employee Silver Tier - Dashboard Manager v2.0*
"""
        return content
    
    def _get_status_badge(self, status: str) -> str:
        """Get status badge emoji."""
        badges = {
            "healthy": "🟢 Healthy",
            "degraded": "🟡 Degraded",
            "critical": "🔴 Critical"
        }
        return badges.get(status, "⚪ Unknown")
    
    def _progress_bar(self, value: int, total: int, width: int = 20) -> str:
        """Generate text progress bar."""
        if total == 0:
            return "░" * width
        
        filled = int((value / total) * width)
        return "█" * filled + "░" * (width - filled)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Agent Skill: dashboard.get_statistics
        
        Returns:
            dict with 'success' (bool) and statistics or 'error' (str)
        """
        try:
            return {
                "success": True,
                "task_metrics": asdict(self.task_metrics),
                "watcher_metrics": asdict(self.watcher_metrics),
                "mcp_metrics": asdict(self.mcp_metrics),
                "system_health": asdict(self.system_health)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Agent Skill: dashboard.get_health_status
        
        Returns:
            dict with 'success' (bool) and health info or 'error' (str)
        """
        try:
            return {
                "success": True,
                "status": self.system_health.status,
                "uptime_hours": self.system_health.uptime_hours,
                "error_count_24h": self.system_health.error_count_24h,
                "watchers_active": self.system_health.watchers_active,
                "mcp_servers_active": self.system_health.mcp_servers_active,
                "last_error": self.system_health.last_error,
                "last_error_time": self.system_health.last_error_time
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_briefing(self, period: str = "daily") -> Dict[str, Any]:
        """
        Generate briefing report.
        
        Agent Skill: dashboard.generate_briefing
        
        Args:
            period: Briefing period (daily, weekly, monthly)
            
        Returns:
            dict with 'success' (bool) and 'briefing' (str) or 'error' (str)
        """
        try:
            now = datetime.now()
            
            if period == "daily":
                title = "Daily Briefing"
                period_start = now - timedelta(days=1)
            elif period == "weekly":
                title = "Weekly Briefing"
                period_start = now - timedelta(weeks=1)
            elif period == "monthly":
                title = "Monthly Briefing"
                period_start = now - timedelta(days=30)
            else:
                return {"success": False, "error": f"Unknown period: {period}"}
            
            briefing = f"""# {title}

**Generated:** {now.strftime("%Y-%m-%d %H:%M:%S")}  
**Period:** {period_start.strftime("%Y-%m-%d")} to {now.strftime("%Y-%m-%d")}

## Executive Summary

- **Total Tasks Processed:** {self.task_metrics.total_tasks}
- **Completion Rate:** {self.task_metrics.completion_rate:.1f}%
- **Items Processed by Watchers:** {self.watcher_metrics.total_processed}
- **Actions Executed:** {self.mcp_metrics.total_actions}
- **System Status:** {self.system_health.status}

## Task Breakdown

- ✅ Completed: {self.task_metrics.completed_tasks}
- ❌ Failed: {self.task_metrics.failed_tasks}
- ⏳ Pending: {self.task_metrics.pending_tasks}

## Watcher Activity

| Watcher | Processed |
|---------|-----------|
| Gmail | {self.watcher_metrics.gmail_processed} |
| WhatsApp | {self.watcher_metrics.whatsapp_processed} |
| LinkedIn | {self.watcher_metrics.linkedin_processed} |
| File System | {self.watcher_metrics.filesystem_processed} |

## MCP Server Usage

| Server | Actions |
|--------|---------|
| Email | {self.mcp_metrics.email_actions} |
| Browser | {self.mcp_metrics.browser_actions} |
| LinkedIn | {self.mcp_metrics.linkedin_actions} |

## System Health

- **Status:** {self.system_health.status}
- **Uptime:** {self.system_health.uptime_hours} hours
- **Errors (24h):** {self.system_health.error_count_24h}

## Recommendations

{self._generate_recommendations()}

---
*Generated by AI Employee Silver Tier - Dashboard Manager*
"""
            
            return {
                "success": True,
                "briefing": briefing,
                "period": period
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate briefing: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_recommendations(self) -> str:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        if self.task_metrics.completion_rate < 80:
            recommendations.append(
                "- ⚠️ Task completion rate is below 80%. Review failed tasks for patterns."
            )
        
        if self.system_health.error_count_24h > 5:
            recommendations.append(
                "- ⚠️ High error count in last 24 hours. Check system logs."
            )
        
        if self.watcher_metrics.total_processed == 0:
            recommendations.append(
                "- ℹ️ No items processed by watchers. Verify watcher configuration."
            )
        
        if self.mcp_metrics.total_actions == 0:
            recommendations.append(
                "- ℹ️ No MCP actions executed. Review pending plans."
            )
        
        if not recommendations:
            recommendations.append(
                "- ✅ System is operating normally. No issues detected."
            )
        
        return "\n".join(recommendations)
    
    def record_error(self, error_message: str) -> None:
        """
        Record system error.
        
        Args:
            error_message: Error message to record
        """
        self.system_health.last_error = error_message
        self.system_health.last_error_time = datetime.now().isoformat()
        self.system_health.error_count_24h += 1
        
        # Update health status
        if self.system_health.error_count_24h > 10:
            self.system_health.status = "critical"
        elif self.system_health.error_count_24h > 5:
            self.system_health.status = "degraded"
        
        self._save_metrics()
    
    def record_task_completion(
        self,
        completion_time: float,
        success: bool = True
    ) -> None:
        """
        Record task completion.
        
        Args:
            completion_time: Time taken to complete task (minutes)
            success: Whether task succeeded
        """
        self.task_metrics.total_tasks += 1
        
        if success:
            self.task_metrics.completed_tasks += 1
        else:
            self.task_metrics.failed_tasks += 1
        
        # Update average completion time
        total_completed = self.task_metrics.completed_tasks
        if total_completed > 0:
            current_avg = self.task_metrics.avg_completion_time
            self.task_metrics.avg_completion_time = (
                (current_avg * (total_completed - 1) + completion_time) / total_completed
            )
        
        self._save_metrics()
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this manager.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "dashboard.update_status": self.update_status,
            "dashboard.get_statistics": self.get_statistics,
            "dashboard.get_health_status": self.get_health_status,
            "dashboard.generate_briefing": self.generate_briefing,
        }


# Global instance
_dashboard_manager: Optional[DashboardManager] = None


def get_dashboard_manager() -> DashboardManager:
    """Get or create global Dashboard Manager instance."""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager(
            vault_path=get_settings().VAULT_PATH
        )
    return _dashboard_manager


if __name__ == "__main__":
    # Test Dashboard Manager
    print("=== Dashboard Manager Test ===\n")
    
    settings = get_settings()
    manager = DashboardManager(vault_path=settings.VAULT_PATH)
    
    # Update metrics
    manager.update_status(
        task_metrics={
            "total_tasks": 100,
            "completed_tasks": 85,
            "failed_tasks": 5,
            "pending_tasks": 10,
            "avg_completion_time": 12.5
        },
        watcher_metrics={
            "gmail_processed": 50,
            "whatsapp_processed": 30,
            "linkedin_processed": 10,
            "filesystem_processed": 25
        },
        mcp_metrics={
            "email_actions": 40,
            "browser_actions": 20,
            "linkedin_actions": 15
        }
    )
    
    # Get statistics
    stats = manager.get_statistics()
    if stats["success"]:
        print("✓ Statistics retrieved")
        print(f"  Completion rate: {stats['task_metrics']['completion_rate']:.1f}%")
    
    # Get health
    health = manager.get_health_status()
    if health["success"]:
        print(f"✓ System health: {health['status']}")
    
    # Generate briefing
    briefing = manager.generate_briefing(period="daily")
    if briefing["success"]:
        print("✓ Daily briefing generated")
        print(briefing["briefing"][:500] + "...")
