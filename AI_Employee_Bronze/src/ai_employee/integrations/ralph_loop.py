"""
Ralph Wiggum Loop Implementation for Qwen Brain

This module implements the Ralph Wiggum pattern - keeping Qwen AI working
persistently until all tasks are complete. It re-injects context on each
iteration and stops when all tasks are processed or max iterations reached.

Usage:
    from ai_employee.integrations.ralph_loop import ralph_loop
    
    ralph_loop(
        vault_path="/path/to/vault",
        max_iterations=10,
        check_interval=5
    )
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger
from .qwen_brain import QwenBrain, create_qwen_brain


class RalphWiggumLoop:
    """
    Ralph Wiggum Loop for persistent task processing.
    
    This class keeps Qwen AI working until all tasks are complete by:
    1. Processing all tasks in Needs_Action
    2. Checking if tasks remain
    3. Re-injecting context if tasks remain
    4. Repeating until complete or max iterations reached
    """
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None,
        max_iterations: int = 10,
        check_interval: int = 5
    ) -> None:
        """
        Initialize the Ralph Wiggum Loop.
        
        Args:
            vault_path: Path to the vault directory
            settings: Application settings
            logger: Application logger
            max_iterations: Maximum number of iterations
            check_interval: Seconds between iterations
        """
        self.settings = settings if settings else get_settings()
        self.vault_path = Path(vault_path or self.settings.VAULT_PATH).expanduser()
        self.logger = logger if logger else get_logger()
        self.max_iterations = max_iterations
        self.check_interval = check_interval
        
        # Initialize Qwen Brain
        self.brain = create_qwen_brain(
            vault_path=str(self.vault_path),
            settings=self.settings,
            logger=self.logger
        )
        
        # Vault folders
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.in_progress_path = self.vault_path / "In_Progress"
        
        self.logger.info(
            f"Ralph Wiggum Loop initialized. Max iterations: {max_iterations}"
        )
    
    def count_remaining_tasks(self) -> int:
        """
        Count remaining tasks in Needs_Action and In_Progress folders.
        
        Returns:
            Number of remaining tasks
        """
        try:
            needs_action_count = len(list(self.needs_action_path.glob("*.md")))
            in_progress_count = len(list(self.in_progress_path.glob("**/*.md")))
            return needs_action_count + in_progress_count
        except Exception as e:
            self.logger.error(f"Error counting tasks: {str(e)}")
            return 0
    
    def run(self, initial_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the Ralph Wiggum Loop.
        
        Args:
            initial_prompt: Optional initial prompt for Qwen
            
        Returns:
            Dictionary with loop results
        """
        results = {
            "started_at": datetime.now().isoformat(),
            "iterations": 0,
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_approval_required": 0,
            "total_autonomous": 0,
            "completed": False,
            "reason": "",
            "errors": []
        }
        
        self.logger.info("=" * 60)
        self.logger.info("🔄 Starting Ralph Wiggum Loop...")
        self.logger.info("=" * 60)
        
        print("\n" + "=" * 60)
        print("🔄 RALPH WIGGUM LOOP - Qwen Brain")
        print("=" * 60)
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            results["iterations"] = iteration
            
            # Count remaining tasks
            remaining = self.count_remaining_tasks()
            
            print(f"\n📊 Iteration {iteration}/{self.max_iterations}")
            print(f"   Remaining tasks: {remaining}")
            
            self.logger.info(
                f"Iteration {iteration}/{self.max_iterations} - "
                f"Remaining tasks: {remaining}"
            )
            
            # Check if complete
            if remaining == 0:
                results["completed"] = True
                results["reason"] = "All tasks processed successfully"
                
                print(f"\n✅ All tasks complete!")
                self.logger.info("✅ All tasks complete!")
                break
            
            # Process tasks
            print(f"   Processing tasks with Qwen...")
            iteration_results = self.brain.process_all_tasks()
            
            # Aggregate results
            results["total_processed"] += iteration_results.get("processed", 0)
            results["total_success"] += iteration_results.get("success", 0)
            results["total_failed"] += iteration_results.get("failed", 0)
            results["total_approval_required"] += iteration_results.get("approval_required", 0)
            results["total_autonomous"] += iteration_results.get("autonomous", 0)
            results["errors"].extend(iteration_results.get("errors", []))
            
            # Print summary
            print(f"   Processed: {iteration_results.get('processed', 0)}")
            print(f"   Success: {iteration_results.get('success', 0)}")
            print(f"   Approval Required: {iteration_results.get('approval_required', 0)}")
            print(f"   Autonomous: {iteration_results.get('autonomous', 0)}")
            print(f"   Failed: {iteration_results.get('failed', 0)}")
            
            # Check if progress was made
            if iteration_results.get("processed", 0) == 0:
                results["completed"] = False
                results["reason"] = "No progress made in this iteration"
                
                print(f"\n⚠️ No progress made. Stopping loop.")
                self.logger.warning("No progress made. Stopping loop.")
                break
            
            # Wait before next iteration
            if iteration < self.max_iterations:
                print(f"   Waiting {self.check_interval}s before next iteration...")
                time.sleep(self.check_interval)
        
        # Final status
        results["ended_at"] = datetime.now().isoformat()
        
        if iteration >= self.max_iterations:
            results["completed"] = False
            results["reason"] = f"Max iterations ({self.max_iterations}) reached"
            
            print(f"\n⚠️ Max iterations reached. Tasks may be incomplete.")
            self.logger.warning(f"Max iterations reached. Tasks may be incomplete.")
        
        # Print final summary
        print("\n" + "=" * 60)
        print("📊 RALPH WIGGUM LOOP - FINAL SUMMARY")
        print("=" * 60)
        print(f"Completed: {'✅ Yes' if results['completed'] else '❌ No'}")
        print(f"Reason: {results['reason']}")
        print(f"Iterations: {results['iterations']}")
        print(f"Total Processed: {results['total_processed']}")
        print(f"Total Success: {results['total_success']}")
        print(f"Total Approval Required: {results['total_approval_required']}")
        print(f"Total Autonomous: {results['total_autonomous']}")
        print(f"Total Failed: {results['total_failed']}")
        print("=" * 60 + "\n")
        
        self.logger.info("=" * 60)
        self.logger.info(f"Ralph Wiggum Loop completed: {results['reason']}")
        self.logger.info("=" * 60)
        
        return results


def ralph_loop(
    vault_path: Optional[str] = None,
    max_iterations: int = 10,
    check_interval: int = 5,
    initial_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run the Ralph Wiggum Loop.
    
    Args:
        vault_path: Path to the vault directory
        max_iterations: Maximum number of iterations
        check_interval: Seconds between iterations
        initial_prompt: Optional initial prompt
        
    Returns:
        Dictionary with loop results
    """
    loop = RalphWiggumLoop(
        vault_path=vault_path,
        max_iterations=max_iterations,
        check_interval=check_interval
    )
    return loop.run(initial_prompt=initial_prompt)


if __name__ == "__main__":
    # Example usage / testing
    print("Ralph Wiggum Loop Test")
    print("=" * 50)
    
    # Run the loop
    results = ralph_loop(
        max_iterations=5,
        check_interval=3
    )
    
    # Print results
    print("\nResults:")
    print(f"  Completed: {results['completed']}")
    print(f"  Iterations: {results['iterations']}")
    print(f"  Total Processed: {results['total_processed']}")
    print(f"  Reason: {results['reason']}")
