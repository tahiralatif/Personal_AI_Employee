"""
Planning Engine for AI Employee Silver Tier.

This module implements the plan generation system that creates structured
action plans with YAML frontmatter, step-by-step execution, dependencies,
success criteria, and rollback plans.

Agent Skills:
    - planning.create_plan(task, steps, dependencies) -> str (plan path)
    - planning.validate_plan(plan_path) -> bool
    - planning.update_plan(plan_path, updates) -> bool
    - planning.get_plan_status(plan_path) -> dict
    - planning.complete_plan(plan_path) -> bool
"""

import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


class PlanStatus(Enum):
    """Plan status values."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanPriority(Enum):
    """Plan priority values."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PlanStep:
    """Represents a single step in a plan."""
    id: int
    description: str
    status: str = "pending"
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Plan:
    """Represents a complete action plan."""
    task_id: str
    title: str
    objective: str
    created: str
    status: str = "pending"
    priority: str = "medium"
    estimated_duration: int = 30  # minutes
    steps: List[PlanStep] = None
    dependencies: List[str] = None
    success_criteria: List[str] = None
    rollback_plan: Optional[str] = None
    approval_required: bool = False
    author: str = "ai_employee"
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.dependencies is None:
            self.dependencies = []
        if self.success_criteria is None:
            self.success_criteria = []


class PlanningEngine:
    """
    Planning Engine for generating and managing action plans.
    
    This engine creates structured plan files in the Plans/ folder
    with YAML frontmatter and markdown content.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Planning Engine.
        
        Args:
            vault_path: Path to the AI Employee vault
            settings: Application settings
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        
        # Plans directory
        self.plans_dir = self.vault_path / "Plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        # Plan tracking
        self.active_plans: Dict[str, Plan] = {}
    
    def create_plan(
        self,
        title: str,
        objective: str,
        steps: List[str],
        priority: str = "medium",
        estimated_duration: int = 30,
        dependencies: Optional[List[str]] = None,
        success_criteria: Optional[List[str]] = None,
        rollback_plan: Optional[str] = None,
        approval_required: bool = False,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new action plan.
        
        Agent Skill: planning.create_plan
        
        Args:
            title: Plan title
            objective: Plan objective statement
            steps: List of step descriptions
            priority: Plan priority (high, medium, low)
            estimated_duration: Estimated duration in minutes
            dependencies: List of dependent task IDs
            success_criteria: List of success criteria
            rollback_plan: Rollback plan description
            approval_required: Whether plan requires approval
            task_id: Optional task ID (auto-generated if None)
            
        Returns:
            dict with 'success' (bool) and 'plan_path' (str) or 'error' (str)
        """
        try:
            self.logger.info(f"Creating plan: {title}")
            
            # Generate task ID if not provided
            if not task_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_id = f"task_{timestamp}"
            
            # Create plan object
            plan = Plan(
                task_id=task_id,
                title=title,
                objective=objective,
                created=datetime.now().isoformat(),
                status=PlanStatus.PENDING.value,
                priority=priority,
                estimated_duration=estimated_duration,
                steps=[
                    PlanStep(id=i+1, description=step)
                    for i, step in enumerate(steps)
                ],
                dependencies=dependencies or [],
                success_criteria=success_criteria or [],
                rollback_plan=rollback_plan,
                approval_required=approval_required
            )
            
            # Generate plan file
            plan_path = self._write_plan_file(plan)
            
            # Track active plan
            self.active_plans[task_id] = plan
            
            self.logger.info(f"Plan created: {plan_path.name}")
            
            return {
                "success": True,
                "plan_path": str(plan_path),
                "task_id": task_id,
                "plan": plan
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create plan: {e}")
            return {"success": False, "error": str(e)}
    
    def _write_plan_file(self, plan: Plan) -> Path:
        """
        Write plan to markdown file with YAML frontmatter.
        
        Args:
            plan: Plan object
            
        Returns:
            Path to created file
        """
        # Generate filename
        safe_title = self._sanitize_filename(plan.title)
        filename = f"PLAN_{plan.task_id}_{safe_title}.md"
        filepath = self.plans_dir / filename
        
        # Build YAML frontmatter
        frontmatter = {
            "type": "action_plan",
            "task_id": plan.task_id,
            "created": plan.created,
            "status": plan.status,
            "priority": plan.priority,
            "estimated_duration": plan.estimated_duration,
            "author": plan.author,
            "approval_required": plan.approval_required
        }
        
        # Build markdown content
        content = self._build_plan_content(plan, frontmatter)
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        
        return filepath
    
    def _build_plan_content(self, plan: Plan, frontmatter: Dict[str, Any]) -> str:
        """
        Build complete plan markdown content.
        
        Args:
            plan: Plan object
            frontmatter: YAML frontmatter dictionary
            
        Returns:
            Complete markdown content string
        """
        # Format frontmatter
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}:")
                for item in value:
                    fm_lines.append(f"  - {item}")
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.extend(["---", ""])
        
        # Build body
        body = []
        
        # Title and objective
        body.append(f"# Action Plan: {plan.title}\n")
        body.append("## Objective\n")
        body.append(f"{plan.objective}\n")
        
        # Prerequisites
        if plan.dependencies:
            body.append("\n## Prerequisites\n")
            for dep in plan.dependencies:
                body.append(f"- [ ] Dependency: {dep}")
        
        # Steps
        body.append("\n## Steps\n")
        for step in plan.steps:
            body.append(f"{step.id}. [ ] {step.description}")
        
        # Dependencies
        if plan.dependencies:
            body.append("\n## Dependencies\n")
            for dep in plan.dependencies:
                body.append(f"- Task ID: {dep}")
        
        # Success Criteria
        if plan.success_criteria:
            body.append("\n## Success Criteria\n")
            for criterion in plan.success_criteria:
                body.append(f"- [ ] {criterion}")
        
        # Approval Required
        if plan.approval_required:
            body.append("\n## Approval Required\n")
            body.append("- [ ] Human approval needed for sensitive actions")
            body.append("- [ ] Move to /Approved/ folder after approval")
        
        # Rollback Plan
        if plan.rollback_plan:
            body.append("\n## Rollback Plan\n")
            body.append(plan.rollback_plan)
        
        # Execution Log
        body.append("\n## Execution Log\n")
        body.append("| Step | Status | Completed At | Notes |")
        body.append("|------|--------|--------------|-------|")
        for step in plan.steps:
            completed = step.completed_at or "-"
            notes = step.error or "-"
            body.append(f"| {step.id} | {step.status} | {completed} | {notes} |")
        
        # Footer
        body.append("\n---")
        body.append(f"*Generated by AI Employee Silver Tier - Planning Engine*")
        body.append(f"*Created: {plan.created}*")
        
        return "\n".join(fm_lines + body)
    
    def validate_plan(self, plan_path: str | Path) -> Dict[str, Any]:
        """
        Validate a plan file.
        
        Agent Skill: planning.validate_plan
        
        Args:
            plan_path: Path to plan file
            
        Returns:
            dict with 'success' (bool) and 'valid' (bool) or 'error' (str)
        """
        try:
            path = Path(plan_path)
            
            if not path.exists():
                return {"success": False, "error": "Plan file not found"}
            
            # Parse frontmatter
            content = path.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)
            
            # Validate required fields
            required_fields = ["task_id", "status", "objective"]
            missing = [f for f in required_fields if f not in frontmatter]
            
            if missing:
                return {
                    "success": True,
                    "valid": False,
                    "errors": [f"Missing required field: {f}" for f in missing]
                }
            
            # Validate status
            if frontmatter.get("status") not in [s.value for s in PlanStatus]:
                return {
                    "success": True,
                    "valid": False,
                    "errors": [f"Invalid status: {frontmatter.get('status')}"]
                }
            
            return {
                "success": True,
                "valid": True,
                "task_id": frontmatter.get("task_id"),
                "status": frontmatter.get("status")
            }
            
        except Exception as e:
            self.logger.error(f"Plan validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def update_plan(
        self,
        plan_path: str | Path,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a plan file.
        
        Agent Skill: planning.update_plan
        
        Args:
            plan_path: Path to plan file
            updates: Dictionary of updates to apply
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            path = Path(plan_path)
            
            if not path.exists():
                return {"success": False, "error": "Plan file not found"}
            
            # Read current content
            content = path.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)
            body = content.split("---", 2)[-1].strip()
            
            # Apply updates to frontmatter
            for key, value in updates.items():
                if key != "steps":  # Steps updated separately
                    frontmatter[key] = value
            
            # Rebuild file
            fm_lines = ["---"]
            for key, value in frontmatter.items():
                if isinstance(value, list):
                    fm_lines.append(f"{key}:")
                    for item in value:
                        fm_lines.append(f"  - {item}")
                else:
                    fm_lines.append(f"{key}: {value}")
            fm_lines.extend(["---", "", body])
            
            # Write updated file
            path.write_text("\n".join(fm_lines), encoding='utf-8')
            
            self.logger.info(f"Plan updated: {path.name}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Plan update failed: {e}")
            return {"success": False, "error": str(e)}
    
    def update_step_status(
        self,
        plan_path: str | Path,
        step_id: int,
        status: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update step status in plan.
        
        Args:
            plan_path: Path to plan file
            step_id: Step ID to update
            status: New status (pending, completed, failed)
            error: Optional error message
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            path = Path(plan_path)
            
            if not path.exists():
                return {"success": False, "error": "Plan file not found"}
            
            # Read content
            content = path.read_text(encoding='utf-8')
            lines = content.split("\n")
            
            # Update step in markdown table
            for i, line in enumerate(lines):
                if line.startswith(f"| {step_id} |"):
                    completed_at = datetime.now().isoformat() if status == "completed" else "-"
                    notes = error if error else "-"
                    lines[i] = f"| {step.id} | {status} | {completed_at} | {notes} |"
                    break
            
            # Write updated file
            path.write_text("\n".join(lines), encoding='utf-8')
            
            self.logger.info(f"Step {step_id} updated to {status}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Step update failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_plan_status(self, plan_path: str | Path) -> Dict[str, Any]:
        """
        Get plan status.
        
        Agent Skill: planning.get_plan_status
        
        Args:
            plan_path: Path to plan file
            
        Returns:
            dict with 'success' (bool) and status info or 'error' (str)
        """
        try:
            path = Path(plan_path)
            
            if not path.exists():
                return {"success": False, "error": "Plan file not found"}
            
            # Parse frontmatter
            content = path.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)
            
            # Count steps
            total_steps = frontmatter.get("estimated_duration", 0)
            
            return {
                "success": True,
                "task_id": frontmatter.get("task_id"),
                "status": frontmatter.get("status"),
                "priority": frontmatter.get("priority"),
                "created": frontmatter.get("created"),
                "approval_required": frontmatter.get("approval_required", False)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get plan status: {e}")
            return {"success": False, "error": str(e)}
    
    def complete_plan(
        self,
        plan_path: str | Path,
        move_to_done: bool = True
    ) -> Dict[str, Any]:
        """
        Mark plan as complete.
        
        Agent Skill: planning.complete_plan
        
        Args:
            plan_path: Path to plan file
            move_to_done: Whether to move file to Done folder
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            path = Path(plan_path)
            
            if not path.exists():
                return {"success": False, "error": "Plan file not found"}
            
            # Update status
            result = self.update_plan(path, {"status": PlanStatus.COMPLETED.value})
            
            if not result["success"]:
                return result
            
            # Move to Done folder if requested
            if move_to_done:
                done_dir = self.vault_path / "Done" / "Plans"
                done_dir.mkdir(parents=True, exist_ok=True)
                dest_path = done_dir / path.name
                path.rename(dest_path)
                self.logger.info(f"Plan moved to Done: {dest_path}")
            
            self.logger.info(f"Plan completed: {path.name}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to complete plan: {e}")
            return {"success": False, "error": str(e)}
    
    def fail_plan(
        self,
        plan_path: str | Path,
        reason: str
    ) -> Dict[str, Any]:
        """
        Mark plan as failed.
        
        Args:
            plan_path: Path to plan file
            reason: Failure reason
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            path = Path(plan_path)
            
            if not path.exists():
                return {"success": False, "error": "Plan file not found"}
            
            # Update status and add failure note
            result = self.update_plan(path, {
                "status": PlanStatus.FAILED.value,
                "failure_reason": reason
            })
            
            self.logger.warning(f"Plan failed: {path.name} - {reason}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to fail plan: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Markdown content with YAML frontmatter
            
        Returns:
            Dictionary of frontmatter values
        """
        try:
            # Extract frontmatter
            if not content.startswith("---"):
                return {}
            
            parts = content.split("---", 2)
            if len(parts) < 2:
                return {}
            
            fm_content = parts[1].strip()
            return yaml.safe_load(fm_content) or {}
            
        except Exception as e:
            self.logger.error(f"Failed to parse frontmatter: {e}")
            return {}
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize string for filename."""
        if not filename:
            return ""
        unsafe = '<>:"/\\|?*'
        for char in unsafe:
            filename = filename.replace(char, '_')
        return filename.strip(' _.')[:50]
    
    def get_all_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all plans, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of plan info dictionaries
        """
        plans = []
        
        for plan_file in self.plans_dir.glob("PLAN_*.md"):
            frontmatter = self._parse_frontmatter(plan_file.read_text())
            
            if status and frontmatter.get("status") != status:
                continue
            
            plans.append({
                "task_id": frontmatter.get("task_id"),
                "title": plan_file.stem,
                "status": frontmatter.get("status"),
                "priority": frontmatter.get("priority"),
                "created": frontmatter.get("created"),
                "path": str(plan_file)
            })
        
        return plans
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this engine.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "planning.create_plan": self.create_plan,
            "planning.validate_plan": self.validate_plan,
            "planning.update_plan": self.update_plan,
            "planning.get_plan_status": self.get_plan_status,
            "planning.complete_plan": self.complete_plan,
        }


# Global instance
_planning_engine: Optional[PlanningEngine] = None


def get_planning_engine() -> PlanningEngine:
    """Get or create global Planning Engine instance."""
    global _planning_engine
    if _planning_engine is None:
        _planning_engine = PlanningEngine(
            vault_path=get_settings().VAULT_PATH
        )
    return _planning_engine


if __name__ == "__main__":
    # Test Planning Engine
    print("=== Planning Engine Test ===\n")
    
    settings = get_settings()
    engine = PlanningEngine(vault_path=settings.VAULT_PATH)
    
    # Create a test plan
    result = engine.create_plan(
        title="Send Weekly Newsletter",
        objective="Create and send weekly newsletter to all subscribers",
        steps=[
            "Gather content from recent blog posts",
            "Design email template",
            "Write newsletter content",
            "Review and proofread",
            "Send to subscribers via email MCP"
        ],
        priority="high",
        estimated_duration=60,
        success_criteria=[
            "Newsletter sent to all subscribers",
            "No bounce-backs or errors",
            "Content approved by marketing team"
        ],
        rollback_plan="If send fails, revert to draft and investigate error",
        approval_required=True
    )
    
    if result["success"]:
        print(f"✓ Plan created: {result['plan_path']}")
        print(f"  Task ID: {result['task_id']}")
        
        # Validate plan
        validation = engine.validate_plan(result["plan_path"])
        if validation["success"] and validation["valid"]:
            print(f"✓ Plan validated successfully")
        
        # Get status
        status = engine.get_plan_status(result["plan_path"])
        if status["success"]:
            print(f"✓ Plan status: {status['status']}")
    else:
        print(f"✗ Failed to create plan: {result.get('error')}")
