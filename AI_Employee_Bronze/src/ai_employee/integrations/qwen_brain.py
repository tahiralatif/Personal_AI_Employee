"""
Qwen AI Brain Integration

This module provides integration with Qwen as the reasoning engine for the AI Employee system.
It handles communication with Qwen via CLI, processes tasks from Needs_Action,
creates plans, and manages the Ralph Wiggum loop for persistent task completion.

Usage:
    from ai_employee.integrations.claude_brain import QwenBrain
    
    brain = QwenBrain(vault_path="/path/to/vault")
    result = brain.process_needs_action()

Qwen CLI:
    claude --cwd "/path/to/vault" --prompt "Process tasks in Needs_Action"
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class QwenBrain:
    """
    Qwen AI Brain for processing tasks and generating plans.
    
    This class handles:
    - Communication with Qwen via CLI
    - Reading tasks from Needs_Action folder
    - Creating plans in Plans folder
    - Requesting human approval for sensitive actions
    - Moving completed tasks to Done folder
    
    Qwen is invoked via CLI:
        claude --cwd <vault_path> --prompt <prompt>
    """
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize the Qwen Brain.
        
        Args:
            vault_path: Path to the vault directory
            settings: Application settings
            logger: Application logger
        """
        self.settings = settings if settings else get_settings()
        self.vault_path = Path(vault_path or self.settings.VAULT_PATH).expanduser()
        self.logger = logger if logger else get_logger()
        
        # Qwen CLI command
        self.qwen_command = "claude"
        
        # Vault folders
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.plans_path = self.vault_path / "Plans"
        self.pending_approval_path = self.vault_path / "Pending_Approval"
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"
        self.in_progress_path = self.vault_path / "In_Progress"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # System prompt for Claude
        self.system_prompt = self._get_system_prompt()
        
        self.logger.info(f"Qwen Brain initialized. Vault: {self.vault_path}")
        self.logger.info(f"Claude CLI command: {self.qwen_command}")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for path in [
            self.needs_action_path,
            self.plans_path,
            self.pending_approval_path,
            self.approved_path,
            self.done_path,
            self.in_progress_path
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for Qwen.
        
        Returns:
            System prompt string
        """
        return """You are an AI Employee assistant working with a local Obsidian vault.
Your role is to:
1. Read task files from /Needs_Action/ folder
2. Analyze tasks and create action plans
3. For sensitive actions (payments, emails, deletions), create approval requests
4. For simple tasks, execute and move to /Done/
5. Update Dashboard.md with current status

Rules:
- NEVER send emails without human approval
- NEVER make payments without human approval  
- NEVER delete files without human approval
- Always log your actions
- Be concise and practical
- Follow the Company_Handbook.md guidelines

File Operations:
- Read files from any folder
- Create Plan.md files in /Plans/
- Create approval requests in /Pending_Approval/
- Move files to /Done/ when complete
- Update Dashboard.md after each action

Approval Threshold:
- Payments over PKR 1,000 require approval
- Email sending requires approval
- File deletion requires approval
- Unknown contacts require approval"""

    def _call_claude(self, prompt: str, cwd: Optional[str] = None) -> str:
        """
        Call Qwen via CLI.
        
        Args:
            prompt: Prompt to send to Qwen
            cwd: Working directory (vault path)
            
        Returns:
            Qwen's response
        """
        try:
            # Build command
            cmd = [
                self.qwen_command,
                "--cwd", str(cwd or self.vault_path),
                "--prompt", prompt
            ]
            
            self.logger.info(f"Calling Qwen CLI: {' '.join(cmd)}")
            
            # Run Qwen CLI
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Qwen responded successfully")
                return result.stdout
            else:
                error_msg = result.stderr or f"Exit code: {result.returncode}"
                self.logger.error(f"Qwen CLI error: {error_msg}")
                return f"Error: {error_msg}"
                
        except FileNotFoundError:
            error_msg = "Qwen CLI not found. Install with: npm install -g @anthropic/claude-code"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"
        except subprocess.TimeoutExpired:
            error_msg = "Qwen request timed out (5 minutes)"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            self.logger.error(f"Qwen CLI error: {str(e)}")
            return f"Error: {str(e)}"
    
    def read_needs_action(self) -> List[Path]:
        """
        Read all .md files from Needs_Action folder.
        
        Returns:
            List of file paths
        """
        try:
            if not self.needs_action_path.exists():
                return []
            
            files = list(self.needs_action_path.glob("*.md"))
            self.logger.info(f"Found {len(files)} files in Needs_Action")
            return files
            
        except Exception as e:
            self.logger.error(f"Error reading Needs_Action: {str(e)}")
            return []
    
    def process_task(self, task_file: Path) -> Tuple[bool, str]:
        """
        Process a single task file using Qwen.
        
        Args:
            task_file: Path to the task file
            
        Returns:
            Tuple of (success, result_message)
        """
        try:
            # Read task file
            content = task_file.read_text(encoding='utf-8')
            
            # Move to In_Progress (claim-by-move rule)
            agent_folder = self.in_progress_path / "qwen"
            agent_folder.mkdir(parents=True, exist_ok=True)
            temp_path = agent_folder / task_file.name
            
            try:
                task_file.rename(temp_path)
            except Exception:
                # If rename fails (cross-device), copy and delete
                import shutil
                shutil.copy2(task_file, temp_path)
                task_file.unlink()
            
            self.logger.info(f"Moved {task_file.name} to In_Progress/qwen/")
            
            # Create prompt for Qwen
            prompt = f"""{self.system_prompt}

Analyze this task and create an action plan.

Task File: {task_file.name}
Content:
{content}

Based on the task:
1. If it requires human approval (payment > PKR 1,000, email sending, file deletion), 
   create an approval request file in /Pending_Approval/
2. If it's a simple task that can be completed autonomously,
   create a Plan.md in /Plans/ and move the file to /Done/
3. Update the Dashboard.md with the current status

Respond with:
- ACTION: [APPROVAL_REQUIRED | AUTONOMOUS | REJECT]
- REASON: [Brief explanation]
- PLAN: [Detailed plan if autonomous]
- NEXT_STEP: [What should happen next]"""

            # Call Qwen
            self.logger.info("Calling Qwen for task analysis...")
            response = self._call_claude(prompt)
            
            # Parse response
            action = self._parse_action(response)
            
            if action["type"] == "APPROVAL_REQUIRED":
                # Create approval request
                approval_path = self._create_approval_request(task_file.name, action)
                if approval_path:
                    self.logger.info(f"Created approval request: {approval_path.name}")
                    return True, f"Approval required: {approval_path.name}"
                else:
                    return False, "Failed to create approval request"
            
            elif action["type"] == "AUTONOMOUS":
                # Create plan and move to done
                plan_path = self._create_plan(task_file.name, action)
                if plan_path:
                    # Move to Done
                    done_path = self.done_path / task_file.name
                    try:
                        temp_path.rename(done_path)
                    except Exception:
                        import shutil
                        shutil.copy2(temp_path, done_path)
                        temp_path.unlink()
                    
                    self.logger.info(f"Task completed: {task_file.name} -> Done/")
                    return True, f"Completed autonomously: {done_path.name}"
                else:
                    return False, "Failed to create plan"
            
            else:
                # Reject or unknown action
                self.logger.warning(f"Unknown action type: {action}")
                return False, f"Unknown action: {action}"
            
        except Exception as e:
            self.logger.error(f"Error processing task {task_file.name}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def _parse_action(self, response: str) -> Dict[str, str]:
        """
        Parse Qwen's response to extract action type and details.
        
        Args:
            response: Qwen's response text
            
        Returns:
            Dictionary with action details
        """
        action = {
            "type": "UNKNOWN",
            "reason": "",
            "plan": "",
            "next_step": ""
        }
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith("ACTION:"):
                action["type"] = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("REASON:"):
                action["reason"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("PLAN:"):
                action["plan"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("NEXT_STEP:"):
                action["next_step"] = line.split(":", 1)[1].strip()
        
        # Default to APPROVAL_REQUIRED if unknown (safer)
        if action["type"] not in ["APPROVAL_REQUIRED", "AUTONOMOUS", "REJECT"]:
            action["type"] = "APPROVAL_REQUIRED"
            action["reason"] = "Unable to parse action type, defaulting to approval required"
        
        return action
    
    def _create_approval_request(self, task_name: str, action: Dict[str, str]) -> Optional[Path]:
        """
        Create an approval request file.
        
        Args:
            task_name: Name of the task file
            action: Action details from Qwen
            
        Returns:
            Path to created approval file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            approval_filename = f"APPROVAL_{timestamp}_{Path(task_name).stem}.md"
            approval_path = self.pending_approval_path / approval_filename
            
            content = f"""---
type: approval_request
task_file: {task_name}
created: {datetime.now().isoformat()}
status: pending
action_type: {action.get('reason', 'Requires human approval')}
---

# Approval Request

## Task
{task_name}

## Reason for Approval
{action.get('reason', 'Requires human approval')}

## Suggested Plan
{action.get('plan', 'No plan provided')}

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.

---
*Generated by Qwen AI Brain*
"""
            
            approval_path.write_text(content, encoding='utf-8')
            return approval_path
            
        except Exception as e:
            self.logger.error(f"Error creating approval request: {str(e)}")
            return None
    
    def _create_plan(self, task_name: str, action: Dict[str, str]) -> Optional[Path]:
        """
        Create a plan file.
        
        Args:
            task_name: Name of the task file
            action: Action details from Qwen
            
        Returns:
            Path to created plan file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_filename = f"PLAN_{timestamp}_{Path(task_name).stem}.md"
            plan_path = self.plans_path / plan_filename
            
            content = f"""---
type: plan
task_file: {task_name}
created: {datetime.now().isoformat()}
status: ready_for_execution
---

# Action Plan

## Task
{task_name}

## Plan
{action.get('plan', 'No plan provided')}

## Next Step
{action.get('next_step', 'Execute plan and move to Done')}

---
*Generated by Qwen AI Brain*
"""
            
            plan_path.write_text(content, encoding='utf-8')
            return plan_path
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {str(e)}")
            return None
    
    def process_all_tasks(self) -> Dict[str, Any]:
        """
        Process all tasks in Needs_Action folder.
        
        Returns:
            Dictionary with processing results
        """
        results = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "approval_required": 0,
            "autonomous": 0,
            "errors": []
        }
        
        # Get all task files
        task_files = self.read_needs_action()
        results["total"] = len(task_files)
        
        if not task_files:
            self.logger.info("No tasks to process in Needs_Action")
            return results
        
        self.logger.info(f"Processing {len(task_files)} tasks...")
        
        # Process each task
        for task_file in task_files:
            results["processed"] += 1
            
            success, message = self.process_task(task_file)
            
            if success:
                results["success"] += 1
                if "Approval required" in message:
                    results["approval_required"] += 1
                elif "Completed autonomously" in message:
                    results["autonomous"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{task_file.name}: {message}")
            
            self.logger.info(f"Task {task_file.name}: {message}")
        
        # Update dashboard
        self._update_dashboard(results)
        
        return results
    
    def _update_dashboard(self, results: Dict[str, Any]) -> None:
        """
        Update Dashboard.md with processing results.
        
        Args:
            results: Processing results dictionary
        """
        try:
            dashboard_path = self.vault_path / "Dashboard.md"
            
            # Count files in each folder
            pending_count = len(list(self.needs_action_path.glob("*.md")))
            in_progress_count = len(list(self.in_progress_path.glob("**/*.md")))
            approval_count = len(list(self.pending_approval_path.glob("*.md")))
            done_count = len(list(self.done_path.glob("*.md")))
            
            content = f"""# AI Employee Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Status
- **System:** Active
- **Brain:** Qwen AI (CLI)
- **Vault Path:** {self.vault_path}

## Task Summary
- **Pending Tasks:** {pending_count}
- **In Progress:** {in_progress_count}
- **Awaiting Approval:** {approval_count}
- **Completed:** {done_count}

## Latest Processing Results
- **Total Processed:** {results.get('total', 0)}
- **Successful:** {results.get('success', 0)}
- **Approval Required:** {results.get('approval_required', 0)}
- **Autonomous:** {results.get('autonomous', 0)}
- **Failed:** {results.get('failed', 0)}

## Recent Activity
- {datetime.now().strftime('%Y-%m-%d %H:%M')} - Processed {results.get('processed', 0)} tasks

## Quick Links
- [Inbox](./Inbox/) - New unprocessed items
- [Needs_Action](./Needs_Action/) - Tasks ready for Qwen
- [In_Progress](./In_Progress/) - Currently being worked on
- [Pending_Approval](./Pending_Approval/) - Awaiting human approval
- [Approved](./Approved/) - Approved for execution
- [Done](./Done/) - Completed tasks
- [Plans](./Plans/) - AI-generated plans
- [Logs](./Logs/) - All action logs
- [Company Handbook](./Company_Handbook.md) - AI's rules

---
*Automatically updated by AI Employee Bronze Tier with Qwen Brain*
"""
            
            dashboard_path.write_text(content, encoding='utf-8')
            self.logger.info("Dashboard updated")
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {str(e)}")
    
    def read_needs_action(self) -> List[Path]:
        """
        Read all .md files from Needs_Action folder.
        
        Returns:
            List of file paths
        """
        try:
            if not self.needs_action_path.exists():
                return []
            
            files = list(self.needs_action_path.glob("*.md"))
            self.logger.info(f"Found {len(files)} files in Needs_Action")
            return files
            
        except Exception as e:
            self.logger.error(f"Error reading Needs_Action: {str(e)}")
            return []
    
    def process_task(self, task_file: Path) -> Tuple[bool, str]:
        """
        Process a single task file using Qwen.
        
        Args:
            task_file: Path to the task file
            
        Returns:
            Tuple of (success, result_message)
        """
        try:
            # Read task file
            content = task_file.read_text(encoding='utf-8')
            
            # Move to In_Progress (claim-by-move rule)
            agent_folder = self.in_progress_path / "qwen"
            agent_folder.mkdir(parents=True, exist_ok=True)
            temp_path = agent_folder / task_file.name
            
            try:
                task_file.rename(temp_path)
            except Exception:
                # If rename fails (cross-device), copy and delete
                import shutil
                shutil.copy2(task_file, temp_path)
                task_file.unlink()
            
            self.logger.info(f"Moved {task_file.name} to In_Progress/qwen/")
            
            # Create prompt for Qwen
            prompt = f"""Analyze this task and create an action plan.

Task File: {task_file.name}
Content:
{content}

Based on the task:
1. If it requires human approval (payment > PKR 1,000, email sending, file deletion), 
   create an approval request file in /Pending_Approval/
2. If it's a simple task that can be completed autonomously,
   create a Plan.md in /Plans/ and move the file to /Done/
3. Update the Dashboard.md with the current status

Respond with:
- ACTION: [APPROVAL_REQUIRED | AUTONOMOUS | REJECT]
- REASON: [Brief explanation]
- PLAN: [Detailed plan if autonomous]
- NEXT_STEP: [What should happen next]"""

            # Call Qwen
            self.logger.info("Calling Qwen for task analysis...")
            response = self._call_qwen(prompt)
            
            # Parse response
            action = self._parse_action(response)
            
            if action["type"] == "APPROVAL_REQUIRED":
                # Create approval request
                approval_path = self._create_approval_request(task_file.name, action)
                if approval_path:
                    self.logger.info(f"Created approval request: {approval_path.name}")
                    return True, f"Approval required: {approval_path.name}"
                else:
                    return False, "Failed to create approval request"
            
            elif action["type"] == "AUTONOMOUS":
                # Create plan and move to done
                plan_path = self._create_plan(task_file.name, action)
                if plan_path:
                    # Move to Done
                    done_path = self.done_path / task_file.name
                    try:
                        temp_path.rename(done_path)
                    except Exception:
                        import shutil
                        shutil.copy2(temp_path, done_path)
                        temp_path.unlink()
                    
                    self.logger.info(f"Task completed: {task_file.name} -> Done/")
                    return True, f"Completed autonomously: {done_path.name}"
                else:
                    return False, "Failed to create plan"
            
            else:
                # Reject or unknown action
                self.logger.warning(f"Unknown action type: {action}")
                return False, f"Unknown action: {action}"
            
        except Exception as e:
            self.logger.error(f"Error processing task {task_file.name}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def _parse_action(self, response: str) -> Dict[str, str]:
        """
        Parse Qwen's response to extract action type and details.
        
        Args:
            response: Qwen's response text
            
        Returns:
            Dictionary with action details
        """
        action = {
            "type": "UNKNOWN",
            "reason": "",
            "plan": "",
            "next_step": ""
        }
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith("ACTION:"):
                action["type"] = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("REASON:"):
                action["reason"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("PLAN:"):
                action["plan"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("NEXT_STEP:"):
                action["next_step"] = line.split(":", 1)[1].strip()
        
        # Default to APPROVAL_REQUIRED if unknown (safer)
        if action["type"] not in ["APPROVAL_REQUIRED", "AUTONOMOUS", "REJECT"]:
            action["type"] = "APPROVAL_REQUIRED"
            action["reason"] = "Unable to parse action type, defaulting to approval required"
        
        return action
    
    def _create_approval_request(self, task_name: str, action: Dict[str, str]) -> Optional[Path]:
        """
        Create an approval request file.
        
        Args:
            task_name: Name of the task file
            action: Action details from Qwen
            
        Returns:
            Path to created approval file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            approval_filename = f"APPROVAL_{timestamp}_{Path(task_name).stem}.md"
            approval_path = self.pending_approval_path / approval_filename
            
            content = f"""---
type: approval_request
task_file: {task_name}
created: {datetime.now().isoformat()}
status: pending
action_type: {action.get('reason', 'Requires human approval')}
---

# Approval Request

## Task
{task_name}

## Reason for Approval
{action.get('reason', 'Requires human approval')}

## Suggested Plan
{action.get('plan', 'No plan provided')}

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.

---
*Generated by Qwen AI Brain*
"""
            
            approval_path.write_text(content, encoding='utf-8')
            return approval_path
            
        except Exception as e:
            self.logger.error(f"Error creating approval request: {str(e)}")
            return None
    
    def _create_plan(self, task_name: str, action: Dict[str, str]) -> Optional[Path]:
        """
        Create a plan file.
        
        Args:
            task_name: Name of the task file
            action: Action details from Qwen
            
        Returns:
            Path to created plan file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_filename = f"PLAN_{timestamp}_{Path(task_name).stem}.md"
            plan_path = self.plans_path / plan_filename
            
            content = f"""---
type: plan
task_file: {task_name}
created: {datetime.now().isoformat()}
status: ready_for_execution
---

# Action Plan

## Task
{task_name}

## Plan
{action.get('plan', 'No plan provided')}

## Next Step
{action.get('next_step', 'Execute plan and move to Done')}

---
*Generated by Qwen AI Brain*
"""
            
            plan_path.write_text(content, encoding='utf-8')
            return plan_path
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {str(e)}")
            return None
    
    def process_all_tasks(self) -> Dict[str, Any]:
        """
        Process all tasks in Needs_Action folder.
        
        Returns:
            Dictionary with processing results
        """
        results = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "approval_required": 0,
            "autonomous": 0,
            "errors": []
        }
        
        # Get all task files
        task_files = self.read_needs_action()
        results["total"] = len(task_files)
        
        if not task_files:
            self.logger.info("No tasks to process in Needs_Action")
            return results
        
        self.logger.info(f"Processing {len(task_files)} tasks...")
        
        # Process each task
        for task_file in task_files:
            results["processed"] += 1
            
            success, message = self.process_task(task_file)
            
            if success:
                results["success"] += 1
                if "Approval required" in message:
                    results["approval_required"] += 1
                elif "Completed autonomously" in message:
                    results["autonomous"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{task_file.name}: {message}")
            
            self.logger.info(f"Task {task_file.name}: {message}")
        
        # Update dashboard
        self._update_dashboard(results)
        
        return results
    
    def _update_dashboard(self, results: Dict[str, Any]) -> None:
        """
        Update Dashboard.md with processing results.
        
        Args:
            results: Processing results dictionary
        """
        try:
            dashboard_path = self.vault_path / "Dashboard.md"
            
            # Count files in each folder
            pending_count = len(list(self.needs_action_path.glob("*.md")))
            in_progress_count = len(list(self.in_progress_path.glob("**/*.md")))
            approval_count = len(list(self.pending_approval_path.glob("*.md")))
            done_count = len(list(self.done_path.glob("*.md")))
            
            content = f"""# AI Employee Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Status
- **System:** Active
- **Brain:** Qwen AI (LM Studio)
- **Vault Path:** {self.vault_path}

## Task Summary
- **Pending Tasks:** {pending_count}
- **In Progress:** {in_progress_count}
- **Awaiting Approval:** {approval_count}
- **Completed:** {done_count}

## Latest Processing Results
- **Total Processed:** {results.get('total', 0)}
- **Successful:** {results.get('success', 0)}
- **Approval Required:** {results.get('approval_required', 0)}
- **Autonomous:** {results.get('autonomous', 0)}
- **Failed:** {results.get('failed', 0)}

## Recent Activity
- {datetime.now().strftime('%Y-%m-%d %H:%M')} - Processed {results.get('processed', 0)} tasks

## Quick Links
- [Inbox](./Inbox/) - New unprocessed items
- [Needs_Action](./Needs_Action/) - Tasks ready for Qwen
- [In_Progress](./In_Progress/) - Currently being worked on
- [Pending_Approval](./Pending_Approval/) - Awaiting human approval
- [Approved](./Approved/) - Approved for execution
- [Done](./Done/) - Completed tasks
- [Plans](./Plans/) - AI-generated plans
- [Logs](./Logs/) - All action logs
- [Company Handbook](./Company_Handbook.md) - AI's rules

---
*Automatically updated by AI Employee Bronze Tier with Qwen Brain*
"""
            
            dashboard_path.write_text(content, encoding='utf-8')
            self.logger.info("Dashboard updated")
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {str(e)}")


def create_qwen_brain(
    vault_path: Optional[str] = None,
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> QwenBrain:
    """
    Factory function to create a QwenBrain instance.
    
    Args:
        vault_path: Optional vault path
        settings: Optional settings
        logger: Optional logger
        
    Returns:
        QwenBrain instance
    """
    return QwenBrain(vault_path=vault_path, settings=settings, logger=logger)


if __name__ == "__main__":
    # Example usage
    print("Qwen Brain Test")
    print("=" * 50)
    
    brain = create_qwen_brain()
    
    # Test reading Needs_Action
    tasks = brain.read_needs_action()
    print(f"Found {len(tasks)} tasks in Needs_Action")
    
    # Test processing all tasks
    if tasks:
        results = brain.process_all_tasks()
        print(f"\nProcessing Results:")
        print(f"  Total: {results['total']}")
        print(f"  Processed: {results['processed']}")
        print(f"  Success: {results['success']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Approval Required: {results['approval_required']}")
        print(f"  Autonomous: {results['autonomous']}")
    else:
        print("No tasks to process. Add files to Needs_Action folder.")
