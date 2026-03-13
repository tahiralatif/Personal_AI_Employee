"""
Orchestrator for AI Employee System

This module orchestrates the entire AI Employee system, coordinating between:
- File Watcher (perception layer)
- Qwen Brain / Silver Agents (reasoning layer)
- Approval Workflow (human-in-the-loop)
- Vault Management (memory)

Usage:
    python main.py orchestrate    # Run one orchestration cycle
    python main.py run            # Run continuously with Ralph Wiggum loop
"""

import time
import signal
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config.settings import Settings, get_settings
from .utils.logger import VaultLogger, get_logger
from .core.vault import VaultManager, DashboardManager
from .handlers.file_watcher import WatcherService, create_watcher_service
from .integrations.qwen_brain import QwenBrain, create_qwen_brain
from .integrations.ralph_loop import RalphWiggumLoop, ralph_loop

# =====================================================================
# IMPORT EXISTING AGENTS (already configured with tools)
# =====================================================================

# Import existing agents from Silver Tier
try:
    from ai_employee_silver.agents.gmail_agent import run_gmail_agent
    from ai_employee_silver.agents.whatsapp_agent import run_whatsapp_agent
    from ai_employee_silver.agents.linkedin_agent import run_linkedin_agent
    SILVER_AGENTS_AVAILABLE = True
except ImportError:
    SILVER_AGENTS_AVAILABLE = False
    run_gmail_agent = None
    run_whatsapp_agent = None
    run_linkedin_agent = None


class Orchestrator:
    """
    Master Orchestrator for the AI Employee system.
    
    Responsibilities:
    - Coordinate all system components
    - Manage lifecycle of watchers and brain
    - Handle approved actions execution
    - Update dashboard and logs
    """
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize the Orchestrator.
        
        Args:
            vault_path: Path to the vault directory
            settings: Application settings
            logger: Application logger
        """
        self.settings = settings if settings else get_settings()
        self.vault_path = Path(vault_path or self.settings.VAULT_PATH).expanduser()
        self.logger = logger if logger else get_logger()
        
        # Initialize components
        self.vault_manager = VaultManager(str(self.vault_path))
        self.dashboard_manager = DashboardManager(str(self.vault_path))
        self.brain = create_qwen_brain(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )
        
        # Vault folders
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"
        self.rejected_path = self.vault_path / "Rejected"
        self.in_progress_path = self.vault_path / "In_Progress"
        
        # State
        self._running = False
        self._watcher_service: Optional[WatcherService] = None
        
        self.logger.info(f"Orchestrator initialized for vault: {self.vault_path}")
    
    def start_watcher(self) -> bool:
        """
        Start the file system watcher.
        
        Returns:
            True if started successfully
        """
        try:
            self.logger.info("Starting file watcher...")
            
            self._watcher_service = create_watcher_service(
                vault_path=str(self.vault_path),
                settings=self.settings,
                logger=self.logger
            )
            
            if self._watcher_service.start():
                self.logger.info("File watcher started")
                return True
            else:
                self.logger.error("Failed to start file watcher")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting watcher: {str(e)}")
            return False
    
    def stop_watcher(self) -> None:
        """Stop the file system watcher."""
        try:
            if self._watcher_service:
                self.logger.info("Stopping file watcher...")
                self._watcher_service.stop()
                self._watcher_service = None
                self.logger.info("File watcher stopped")
        except Exception as e:
            self.logger.error(f"Error stopping watcher: {str(e)}")
    
    def check_approved(self) -> List[Path]:
        """
        Check for approved actions ready to execute.
        
        Returns:
            List of approved file paths
        """
        try:
            if not self.approved_path.exists():
                return []
            
            approved_files = list(self.approved_path.glob("*.md"))
            self.logger.info(f"Found {len(approved_files)} approved actions")
            return approved_files
            
        except Exception as e:
            self.logger.error(f"Error checking approved: {str(e)}")
            return []
    
    def execute_approved(self, approval_path: Path) -> bool:
        """
        Execute an approved action.
        
        Args:
            approval_path: Path to approved file
            
        Returns:
            True if executed successfully
        """
        try:
            content = approval_path.read_text(encoding='utf-8')
            
            # Parse approval file to determine action type
            # For now, just move to Done as a placeholder
            # In Silver/Gold tier, this would execute actual actions
            
            self.logger.info(f"Executing approved action: {approval_path.name}")
            
            # Move to Done
            done_path = self.done_path / approval_path.name
            try:
                approval_path.rename(done_path)
            except Exception:
                import shutil
                shutil.copy2(approval_path, done_path)
                approval_path.unlink()
            
            self.logger.info(f"Approved action completed: {done_path.name}")
            
            # Update dashboard
            self.dashboard_manager.update_dashboard(
                last_action=f"Executed: {approval_path.name}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing approved action: {str(e)}")
            return False
    
    def orchestrate_cycle(self, enable_silver_agents: bool = True) -> Dict[str, Any]:
        """
        Run one orchestration cycle.

        Args:
            enable_silver_agents: Whether to run Silver Tier agents

        Returns:
            Dictionary with cycle results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks_processed": 0,
            "silver_agents_run": False,
            "approved_executed": 0,
            "errors": []
        }

        self.logger.info("Starting orchestration cycle...")

        # Step 1: Run Silver Tier Agents (if available and enabled)
        if enable_silver_agents and SILVER_AGENTS_AVAILABLE:
            try:
                self.logger.info("🤖 Running Silver Tier autonomous agents...")
                agent_results = self.run_silver_agents()
                results["silver_agents_run"] = True
                results["agents_successful"] = agent_results.get("agents_successful", 0)
                results["agents_failed"] = agent_results.get("agents_failed", 0)
            except Exception as e:
                self.logger.error(f"Error running Silver agents: {str(e)}")
                results["errors"].append(f"Silver agents error: {str(e)}")
                results["silver_agents_run"] = False

        # Step 2: Process tasks with Qwen Brain (Bronze Tier fallback)
        try:
            self.logger.info("🧠 Processing tasks with Qwen Brain...")
            qwen_results = self.brain.process_all_tasks()
            results["tasks_processed"] = qwen_results.get("processed", 0)
        except Exception as e:
            self.logger.error(f"Error in Qwen processing: {str(e)}")
            results["errors"].append(f"Qwen error: {str(e)}")

        # Step 3: Execute approved actions
        try:
            approved_files = self.check_approved()
            for approval_file in approved_files:
                if self.execute_approved(approval_file):
                    results["approved_executed"] += 1
        except Exception as e:
            self.logger.error(f"Error executing approved: {str(e)}")
            results["errors"].append(f"Execution error: {str(e)}")

        # Step 4: Update dashboard
        try:
            dashboard_summary = (
                f"Orchestrated: {results['tasks_processed']} tasks, "
                f"{results['approved_executed']} approved"
            )
            if results["silver_agents_run"]:
                dashboard_summary += (
                    f", {results.get('agents_successful', 0)} agents successful"
                )
            self.dashboard_manager.update_dashboard(last_action=dashboard_summary)
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {str(e)}")
            results["errors"].append(f"Dashboard error: {str(e)}")

        self.logger.info(
            f"Orchestration cycle complete: {results['tasks_processed']} tasks, "
            f"{results['approved_executed']} approved, "
            f"silver_agents={results['silver_agents_run']}"
        )

        return results
    
    def run_continuous(self, cycle_interval: int = 30) -> None:
        """
        Run orchestration continuously.
        
        Args:
            cycle_interval: Seconds between cycles
        """
        self._running = True
        
        self.logger.info("Starting continuous orchestration...")
        print("\n🤖 AI Employee Orchestrator - Running Continuously")
        print("=" * 60)
        
        cycle_count = 0
        
        while self._running:
            cycle_count += 1
            
            print(f"\n🔄 Cycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Run orchestration cycle
            results = self.orchestrate_cycle()
            
            # Print summary
            print(f"   Tasks Processed: {results['tasks_processed']}")
            print(f"   Approved Executed: {results['approved_executed']}")
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
            
            # Wait for next cycle
            if self._running:
                print(f"   Next cycle in {cycle_interval}s...")
                time.sleep(cycle_interval)
        
        self.logger.info("Continuous orchestration stopped")
    
    def stop(self) -> None:
        """Stop the orchestrator."""
        self._running = False
        self.stop_watcher()
        self.logger.info("Orchestrator stopped")
    
    def run_ralph_loop(self, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run Ralph Wiggum loop for persistent task processing.

        Args:
            max_iterations: Maximum number of iterations

        Returns:
            Dictionary with loop results
        """
        self.logger.info("Starting Ralph Wiggum loop...")

        results = ralph_loop(
            vault_path=str(self.vault_path),
            max_iterations=max_iterations,
            check_interval=5
        )

        # Final dashboard update
        self.dashboard_manager.update_dashboard(
            last_action=f"Ralph Loop: {results['total_processed']} tasks processed"
        )

        return results

    # =====================================================================
    # SILVER TIER AGENT HANDOFF
    # =====================================================================

    def run_silver_agents(self) -> Dict[str, Any]:
        """
        Run all available Silver Tier autonomous agents.

        This method hands off control to the Silver Tier agents:
        - Gmail Agent: Monitors Gmail for emails with attachments
        - WhatsApp Agent: Monitors WhatsApp for task keywords
        - LinkedIn Agent: Manages LinkedIn posts and engagement

        Returns:
            Dictionary with agent execution results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "agents_run": [],
            "agents_successful": 0,
            "agents_failed": 0,
            "errors": []
        }

        if not SILVER_AGENTS_AVAILABLE:
            self.logger.warning("Silver Tier agents not available (install ai-employee-silver)")
            results["errors"].append("Silver Tier agents not installed")
            return results

        self.logger.info("Starting Silver Tier autonomous agents...")

        # Run Gmail Agent
        try:
            self.logger.info("📧 Running Gmail Agent...")
            asyncio.run(run_gmail_agent())
            results["agents_run"].append("gmail")
            results["agents_successful"] += 1
        except Exception as e:
            self.logger.error(f"❌ Gmail Agent failed: {str(e)}")
            results["agents_failed"] += 1
            results["errors"].append(f"Gmail Agent: {str(e)}")

        # Run WhatsApp Agent
        try:
            self.logger.info("💬 Running WhatsApp Agent...")
            asyncio.run(run_whatsapp_agent())
            results["agents_run"].append("whatsapp")
            results["agents_successful"] += 1
        except Exception as e:
            self.logger.error(f"❌ WhatsApp Agent failed: {str(e)}")
            results["agents_failed"] += 1
            results["errors"].append(f"WhatsApp Agent: {str(e)}")

        # Run LinkedIn Agent
        try:
            self.logger.info("💼 Running LinkedIn Agent...")
            asyncio.run(run_linkedin_agent())
            results["agents_run"].append("linkedin")
            results["agents_successful"] += 1
        except Exception as e:
            self.logger.error(f"❌ LinkedIn Agent failed: {str(e)}")
            results["agents_failed"] += 1
            results["errors"].append(f"LinkedIn Agent: {str(e)}")

        self.logger.info(
            f"Silver Tier agents complete: {results['agents_successful']} successful, "
            f"{results['agents_failed']} failed"
        )

        # Update dashboard
        self.dashboard_manager.update_dashboard(
            last_action=f"Silver Agents: {results['agents_successful']} run successfully"
        )

        return results

    def run_agent_handoff(self, agent_type: str = "all") -> Dict[str, Any]:
        """
        Hand off task processing to specific Silver Tier agent.

        Args:
            agent_type: Type of agent to run ("gmail", "whatsapp", "linkedin", "all")

        Returns:
            Dictionary with agent execution results
        """
        if not SILVER_AGENTS_AVAILABLE:
            return {"error": "Silver Tier agents not available"}

        results = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": agent_type,
            "success": False,
            "error": None
        }

        try:
            if agent_type == "gmail" or agent_type == "all":
                self.logger.info("📧 Handing off to Gmail Agent...")
                asyncio.run(run_gmail_agent())
                results["success"] = True

            if agent_type == "whatsapp" or agent_type == "all":
                self.logger.info("💬 Handing off to WhatsApp Agent...")
                asyncio.run(run_whatsapp_agent())
                results["success"] = True

            if agent_type == "linkedin" or agent_type == "all":
                self.logger.info("💼 Handing off to LinkedIn Agent...")
                asyncio.run(run_linkedin_agent())
                results["success"] = True

        except Exception as e:
            self.logger.error(f"Agent handoff failed: {str(e)}")
            results["success"] = False
            results["error"] = str(e)

        return results


class ApprovalWorkflow:
    """
    Human-in-the-Loop Approval Workflow.
    
    Manages the approval process for sensitive actions:
    - Create approval requests
    - Check for approved/rejected files
    - Execute approved actions
    - Handle rejections
    """
    
    def __init__(
        self,
        vault_path: str,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize the Approval Workflow.
        
        Args:
            vault_path: Path to the vault directory
            logger: Application logger
        """
        self.vault_path = Path(vault_path).expanduser()
        self.logger = logger if logger else get_logger()
        
        # Folders
        self.pending_path = self.vault_path / "Pending_Approval"
        self.approved_path = self.vault_path / "Approved"
        self.rejected_path = self.vault_path / "Rejected"
        self.done_path = self.vault_path / "Done"
        
        # Ensure directories exist
        for path in [self.pending_path, self.approved_path, self.rejected_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Approval Workflow initialized")
    
    def request_approval(
        self,
        action_type: str,
        task_file: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        Create an approval request.
        
        Args:
            action_type: Type of action (payment, email, delete, etc.)
            task_file: Name of the task file
            reason: Reason approval is required
            details: Additional details
            
        Returns:
            Path to created approval request, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"APPROVAL_{timestamp}_{action_type.upper()}.md"
            approval_path = self.pending_path / filename
            
            details_text = ""
            if details:
                details_text = "\n".join([f"- **{k}**: {v}" for k, v in details.items()])
            
            content = f"""---
type: approval_request
action_type: {action_type}
task_file: {task_file}
created: {datetime.now().isoformat()}
status: pending
---

# Approval Request

## Action Type
{action_type.title()}

## Task
{task_file}

## Reason for Approval
{reason}

{details_text}

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.

---
*Generated by AI Employee Approval Workflow*
"""
            
            approval_path.write_text(content, encoding='utf-8')
            self.logger.info(f"Created approval request: {filename}")
            return approval_path
            
        except Exception as e:
            self.logger.error(f"Error creating approval request: {str(e)}")
            return None
    
    def check_pending(self) -> List[Path]:
        """
        Check for pending approval requests.
        
        Returns:
            List of pending approval file paths
        """
        try:
            if not self.pending_path.exists():
                return []
            
            return list(self.pending_path.glob("*.md"))
            
        except Exception as e:
            self.logger.error(f"Error checking pending: {str(e)}")
            return []
    
    def check_approved(self) -> List[Path]:
        """
        Check for approved actions.
        
        Returns:
            List of approved file paths
        """
        try:
            if not self.approved_path.exists():
                return []
            
            return list(self.approved_path.glob("*.md"))
            
        except Exception as e:
            self.logger.error(f"Error checking approved: {str(e)}")
            return []
    
    def check_rejected(self) -> List[Path]:
        """
        Check for rejected actions.
        
        Returns:
            List of rejected file paths
        """
        try:
            if not self.rejected_path.exists():
                return []
            
            return list(self.rejected_path.glob("*.md"))
            
        except Exception as e:
            self.logger.error(f"Error checking rejected: {str(e)}")
            return []
    
    def approve(self, approval_path: Path) -> bool:
        """
        Move an approval request to approved.
        
        Args:
            approval_path: Path to approval request
            
        Returns:
            True if approved successfully
        """
        try:
            dest_path = self.approved_path / approval_path.name
            
            try:
                approval_path.rename(dest_path)
            except Exception:
                import shutil
                shutil.copy2(approval_path, dest_path)
                approval_path.unlink()
            
            self.logger.info(f"Approved: {approval_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error approving: {str(e)}")
            return False
    
    def reject(self, approval_path: Path, reason: str = "") -> bool:
        """
        Reject an approval request.
        
        Args:
            approval_path: Path to approval request
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        try:
            # Add rejection reason to file
            content = approval_path.read_text(encoding='utf-8')
            content += f"\n\n## Rejection Reason\n{reason}\n\n*Rejected at {datetime.now().isoformat()}*"
            approval_path.write_text(content, encoding='utf-8')
            
            # Move to Rejected
            dest_path = self.rejected_path / approval_path.name
            
            try:
                approval_path.rename(dest_path)
            except Exception:
                import shutil
                shutil.copy2(approval_path, dest_path)
                approval_path.unlink()
            
            self.logger.info(f"Rejected: {approval_path.name} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rejecting: {str(e)}")
            return False


def create_orchestrator(
    vault_path: Optional[str] = None,
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> Orchestrator:
    """
    Factory function to create an Orchestrator instance.
    
    Args:
        vault_path: Optional vault path
        settings: Optional settings
        logger: Optional logger
        
    Returns:
        Orchestrator instance
    """
    return Orchestrator(
        vault_path=vault_path,
        settings=settings,
        logger=logger
    )


if __name__ == "__main__":
    # Example usage
    print("AI Employee Orchestrator")
    print("=" * 50)
    
    orchestrator = create_orchestrator()
    
    # Run one cycle
    print("\nRunning orchestration cycle...")
    results = orchestrator.orchestrate_cycle()
    
    print(f"\nResults:")
    print(f"  Tasks Processed: {results['tasks_processed']}")
    print(f"  Approved Executed: {results['approved_executed']}")
    if results['errors']:
        print(f"  Errors: {results['errors']}")
