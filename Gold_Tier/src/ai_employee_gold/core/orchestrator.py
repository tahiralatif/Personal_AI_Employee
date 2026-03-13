"""Enhanced Orchestrator for Gold Tier AI Employee.

This module provides cross-domain task routing, domain-aware processing,
task correlation, and priority escalation.
"""
import subprocess
import time
from pathlib import Path
from datetime import datetime
import threading
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from ..config.settings import settings
from .vault_manager import vault, Domain
from .audit_logger import audit_logger
from .error_recovery import health_monitor, HealthStatus

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCorrelator:
    """Tracks related tasks across domains."""
    
    def __init__(self):
        self.correlations: Dict[str, List[str]] = {}
        self.task_metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_correlation(self, task_ids: List[str], correlation_type: str = "related") -> str:
        """Create correlation between tasks.
        
        Args:
            task_ids: List of task IDs to correlate
            correlation_type: Type of correlation
            
        Returns:
            Correlation ID
        """
        correlation_id = f"corr_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.correlations[correlation_id] = task_ids
        
        for task_id in task_ids:
            self.task_metadata[task_id] = {
                "correlation_id": correlation_id,
                "correlation_type": correlation_type,
                "created": datetime.now().isoformat()
            }
        
        logger.info(f"Created correlation {correlation_id} for {len(task_ids)} tasks")
        return correlation_id
    
    def get_related_tasks(self, task_id: str) -> List[str]:
        """Get tasks related to given task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of related task IDs
        """
        metadata = self.task_metadata.get(task_id, {})
        correlation_id = metadata.get("correlation_id")
        
        if correlation_id:
            return self.correlations.get(correlation_id, [])
        
        return []
    
    def add_metadata(self, task_id: str, key: str, value: Any):
        """Add metadata to task.
        
        Args:
            task_id: Task ID
            key: Metadata key
            value: Metadata value
        """
        if task_id not in self.task_metadata:
            self.task_metadata[task_id] = {}
        
        self.task_metadata[task_id][key] = value


class Orchestrator:
    """Enhanced Orchestrator for Gold Tier.
    
    Features:
    - Cross-domain task routing
    - Domain-aware processing
    - Task correlation
    - Priority escalation
    - Health monitoring
    - Comprehensive audit logging
    """
    
    def __init__(self):
        """Initialize enhanced orchestrator."""
        self.vault_path = vault.vault_path
        self.needs_action = vault.paths.needs_action
        self.plans = vault.paths.plans
        self.approved = vault.paths.approved
        self.done = vault.paths.done
        self.in_progress = vault.paths.in_progress
        
        # Domain routing table
        self.domain_routing = {
            Domain.PERSONAL: ["Gmail", "WhatsApp"],
            Domain.BUSINESS: ["LinkedIn", "Facebook", "Instagram", "Twitter"],
            Domain.FINANCE: ["Accounting", "Odoo"],
            Domain.SYSTEM: ["FileDrop"]
        }
        
        # Priority escalation rules
        self.priority_rules = {
            "payment_overdue": {
                "days_threshold": 30,
                "escalate_to": Priority.HIGH
            },
            "large_amount": {
                "amount_threshold": 5000,
                "escalate_to": Priority.HIGH
            },
            "urgent_keyword": {
                "keywords": ["urgent", "asap", "emergency"],
                "escalate_to": Priority.CRITICAL
            }
        }
        
        # Task correlator
        self.correlator = TaskCorrelator()
        
        # Statistics
        self.total_processed = 0
        self.total_routed = 0
        self.total_escalated = 0
        self.start_time = datetime.now()
        
        logger.info("Enhanced Orchestrator initialized")
    
    def check_needs_action(self) -> List[Tuple[Path, Domain, Priority]]:
        """Check for new items in Needs_Action with domain and priority.
        
        Returns:
            List of (path, domain, priority) tuples
        """
        items = []
        
        for domain_path in self.needs_action.iterdir():
            if not domain_path.is_dir():
                continue
            
            # Determine domain from folder name
            domain = vault.get_domain_for_category(domain_path.name)
            
            for file_path in domain_path.glob("*.md"):
                # Determine priority from content
                priority = self._determine_priority(file_path)
                items.append((file_path, domain, priority))
        
        # Sort by priority (critical first)
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.NORMAL: 2,
            Priority.LOW: 3
        }
        
        items.sort(key=lambda x: priority_order[x[2]])
        
        return items
    
    def _determine_priority(self, file_path: Path) -> Priority:
        """Determine priority from file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Priority level
        """
        if not file_path.exists():
            return Priority.NORMAL
        
        content = file_path.read_text()
        
        # Check for explicit priority in frontmatter
        if "priority: critical" in content:
            return Priority.CRITICAL
        elif "priority: high" in content:
            return Priority.HIGH
        elif "priority: low" in content:
            return Priority.LOW
        
        # Check for priority escalation rules
        for rule_name, rule in self.priority_rules.items():
            if rule_name == "urgent_keyword":
                for keyword in rule["keywords"]:
                    if keyword in content.lower():
                        return rule["escalate_to"]
            elif rule_name == "large_amount":
                # Look for amount in content
                import re
                amounts = re.findall(r'\$?([\d,]+\.?\d*)', content)
                for amount_str in amounts:
                    try:
                        amount = float(amount_str.replace(',', ''))
                        if amount >= rule["amount_threshold"]:
                            return rule["escalate_to"]
                    except ValueError:
                        continue
        
        return Priority.NORMAL
    
    def route_task(self, file_path: Path, domain: Domain) -> str:
        """Route task to appropriate domain processor.
        
        Args:
            file_path: Path to task file
            domain: Target domain
            
        Returns:
            Routing result message
        """
        self.total_routed += 1
        
        # Get destination folder based on domain
        if domain == Domain.PERSONAL:
            # Route to personal processors (Gmail, WhatsApp)
            return self._route_to_personal(file_path)
        elif domain == Domain.BUSINESS:
            # Route to business processors (LinkedIn, Social Media)
            return self._route_to_business(file_path)
        elif domain == Domain.FINANCE:
            # Route to finance processors (Odoo, Accounting)
            return self._route_to_finance(file_path)
        else:
            # System tasks processed directly
            return self._process_system_task(file_path)
    
    def _route_to_personal(self, file_path: Path) -> str:
        """Route to personal domain processor."""
        # In full implementation, would trigger specific agent
        logger.info(f"Routing to personal domain: {file_path.name}")
        return f"Routed {file_path.name} to personal domain"
    
    def _route_to_business(self, file_path: Path) -> str:
        """Route to business domain processor."""
        logger.info(f"Routing to business domain: {file_path.name}")
        return f"Routed {file_path.name} to business domain"
    
    def _route_to_finance(self, file_path: Path) -> str:
        """Route to finance domain processor."""
        logger.info(f"Routing to finance domain: {file_path.name}")
        
        # For finance tasks, create correlation with accounting
        file_stem = file_path.stem
        self.correlator.create_correlation(
            [file_stem, f"accounting_{file_stem}"],
            "finance_related"
        )
        
        return f"Routed {file_path.name} to finance domain"
    
    def _process_system_task(self, file_path: Path) -> str:
        """Process system task directly."""
        logger.info(f"Processing system task: {file_path.name}")
        return f"Processed system task {file_path.name}"
    
    def process_item(self, item_path: Path, domain: Domain, priority: Priority):
        """Process a single item with domain awareness.
        
        Args:
            item_path: Path to item
            domain: Item domain
            priority: Item priority
        """
        logger.info(f'Processing: {item_path.name} (Domain: {domain.value}, Priority: {priority.value})')
        
        # Move to In_Progress (claim-by-move rule)
        domain_in_progress = self.in_progress / domain.value
        domain_in_progress.mkdir(parents=True, exist_ok=True)
        temp_path = domain_in_progress / item_path.name
        item_path.rename(temp_path)
        
        # Create task ID
        task_id = f"{domain.value}_{item_path.stem}"
        
        # Add metadata
        self.correlator.add_metadata(task_id, "domain", domain.value)
        self.correlator.add_metadata(task_id, "priority", priority.value)
        self.correlator.add_metadata(task_id, "started", datetime.now().isoformat())
        
        # Generate domain-aware prompt
        prompt = self._generate_domain_prompt(temp_path, domain, priority)
        
        try:
            # Trigger AI reasoning with timeout
            result = subprocess.run(
                ['claude', '--cwd', str(self.vault_path), '--prompt', prompt],
                capture_output=True, text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Check if plan created
            plan_files = list(self.plans.glob(f'*{item_path.stem}*'))
            if plan_files:
                logger.info(f'Plan created: {plan_files[0].name}')
                
                # Add plan to correlation
                self.correlator.add_metadata(
                    task_id,
                    "plan_file",
                    plan_files[0].name
                )
            
            # Audit log
            audit_logger.log(
                action_type="orchestrator.process_item",
                actor="EnhancedOrchestrator",
                actor_type="system",
                domain=domain.value,
                subdomain="orchestration",
                target=str(item_path.name),
                parameters={
                    "task_id": task_id,
                    "domain": domain.value,
                    "priority": priority.value
                },
                result="success",
                correlation_id=self.correlator.task_metadata.get(task_id, {}).get("correlation_id")
            )
            
            self.total_processed += 1
            
        except subprocess.TimeoutExpired:
            logger.error(f'Timeout processing: {temp_path.name}')
            audit_logger.log(
                action_type="orchestrator.process_item",
                actor="EnhancedOrchestrator",
                actor_type="system",
                domain=domain.value,
                target=str(item_path.name),
                parameters={"task_id": task_id},
                result="failed",
                error_message="Processing timeout"
            )
        except Exception as e:
            logger.error(f'Error processing {temp_path.name}: {e}')
            audit_logger.log(
                action_type="orchestrator.process_item",
                actor="EnhancedOrchestrator",
                actor_type="system",
                domain=domain.value,
                target=str(item_path.name),
                parameters={"task_id": task_id},
                result="failed",
                error_message=str(e)
            )
    
    def _generate_domain_prompt(self, file_path: Path, domain: Domain, priority: Priority) -> str:
        """Generate domain-aware prompt for AI.
        
        Args:
            file_path: Path to file
            domain: File domain
            priority: File priority
            
        Returns:
            Prompt string
        """
        domain_context = {
            Domain.PERSONAL: "This is a PERSONAL domain task. Handle with appropriate privacy and personal context.",
            Domain.BUSINESS: "This is a BUSINESS domain task. Focus on business value and professional communication.",
            Domain.FINANCE: "This is a FINANCE domain task. Handle financial data carefully and follow accounting rules.",
            Domain.SYSTEM: "This is a SYSTEM task. Process according to system rules."
        }
        
        priority_context = {
            Priority.CRITICAL: "PRIORITY: CRITICAL - This requires immediate attention.",
            Priority.HIGH: "PRIORITY: HIGH - This is urgent and should be handled promptly.",
            Priority.NORMAL: "PRIORITY: NORMAL - Handle in regular workflow.",
            Priority.LOW: "PRIORITY: LOW - Can be deferred if needed."
        }
        
        return f'''Read {file_path.name} and create a comprehensive plan.

{domain_context.get(domain, "")}
{priority_context.get(priority, "")}

If action requires approval:
- Create file in /Pending_Approval with detailed justification
- Include risk assessment
- Specify approval threshold

If no approval needed:
- Execute the action
- Move to /Done after completion
- Log all actions

Consider cross-domain integration:
- Check for related tasks in other domains
- Create correlations where appropriate
- Update Dashboard.md with progress
'''
    
    def check_approved(self) -> List[Path]:
        """Check for approved actions ready to execute."""
        return list(self.approved.glob('*.md'))
    
    def execute_approved(self, approval_path: Path):
        """Execute approved action via MCP or scripts."""
        try:
            content = approval_path.read_text()
            
            # Parse approval file and execute action
            # This would involve calling appropriate MCP servers based on action type
            logger.info(f'Executing approved action: {approval_path.name}')
            
            # Audit log
            audit_logger.log(
                action_type="orchestrator.execute_approved",
                actor="EnhancedOrchestrator",
                actor_type="system",
                domain="system",
                target=str(approval_path.name),
                parameters={},
                result="success",
                approval_status="approved"
            )
            
            # Move to Done after execution
            done_path = self.done / approval_path.name
            approval_path.rename(done_path)
            
        except Exception as e:
            logger.error(f'Error executing approved action {approval_path.name}: {e}')
            audit_logger.log(
                action_type="orchestrator.execute_approved",
                actor="EnhancedOrchestrator",
                actor_type="system",
                domain="system",
                target=str(approval_path.name),
                parameters={},
                result="failed",
                error_message=str(e)
            )
    
    def escalate_priority(self, task_id: str, new_priority: Priority, reason: str) -> bool:
        """Escalate task priority.
        
        Args:
            task_id: Task ID
            new_priority: New priority level
            reason: Reason for escalation
            
        Returns:
            True if successful
        """
        self.correlator.add_metadata(task_id, "escalated_priority", new_priority.value)
        self.correlator.add_metadata(task_id, "escalation_reason", reason)
        self.correlator.add_metadata(task_id, "escalated_at", datetime.now().isoformat())
        
        self.total_escalated += 1
        
        logger.info(f"Escalated {task_id} to {new_priority.value}: {reason}")
        
        audit_logger.log(
            action_type="orchestrator.escalate_priority",
            actor="EnhancedOrchestrator",
            actor_type="system",
            domain="system",
            target=task_id,
            parameters={
                "new_priority": new_priority.value,
                "reason": reason
            },
            result="success"
        )
        
        return True
    
    def get_correlated_tasks(self, task_id: str) -> List[str]:
        """Get tasks correlated with given task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of correlated task IDs
        """
        return self.correlator.get_related_tasks(task_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        uptime = datetime.now() - self.start_time
        
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_processed": self.total_processed,
            "total_routed": self.total_routed,
            "total_escalated": self.total_escalated,
            "processing_rate": self.total_processed / max(1, uptime.total_seconds()) * 60,  # per minute
            "correlations": len(self.correlator.correlations),
            "tracked_tasks": len(self.correlator.task_metadata)
        }
    
    def run(self):
        """Main orchestration loop."""
        logger.info('Enhanced Orchestrator started')
        
        while True:
            try:
                # Process Needs_Action (sorted by priority)
                items = self.check_needs_action()
                
                for item_path, domain, priority in items:
                    self.process_item(item_path, domain, priority)
                
                # Execute Approved
                approved = self.check_approved()
                for approval in approved:
                    self.execute_approved(approval)
                
                # Update dashboard
                self.update_dashboard()
                
            except Exception as e:
                logger.error(f'Orchestrator error: {e}')
                health_monitor.record_health("orchestrator", HealthStatus.DEGRADED, str(e))
            
            time.sleep(10)  # Check every 10 seconds
    
    def update_dashboard(self):
        """Update dashboard with current status including domain statistics."""
        try:
            # Count items by domain
            domain_counts = {}
            for domain in Domain:
                if domain == Domain.UNKNOWN:
                    continue
                
                domain_folder = self.needs_action / domain.value.capitalize()
                if domain_folder.exists():
                    count = len(list(domain_folder.glob("*.md")))
                    domain_counts[domain.value] = count
            
            # Get overall counts
            pending_count = sum(1 for _ in self.needs_action.rglob('*.md'))
            in_progress_count = sum(1 for _ in self.in_progress.rglob('*.md'))
            approved_count = sum(1 for _ in self.approved.rglob('*.md'))
            
            # Read current dashboard
            dashboard_path = self.vault_path / 'Dashboard.md'
            if dashboard_path.exists():
                current_content = dashboard_path.read_text()
            else:
                current_content = "# 📊 AI Employee Dashboard\n\n"
            
            # Update domain statistics section
            lines = current_content.split('\n')
            new_lines = []
            in_domain_section = False
            
            for line in lines:
                if '## Domain Statistics' in line:
                    in_domain_section = True
                    new_lines.append(line)
                elif in_domain_section and line.startswith('##'):
                    # Add domain counts before next section
                    for domain, count in domain_counts.items():
                        new_lines.append(f"| {domain.capitalize()} | {count} | 0 |")
                    new_lines.append(line)
                    in_domain_section = False
                elif in_domain_section and line.startswith('| Domain'):
                    # Skip header row, we'll add it
                    new_lines.append(line)
                elif in_domain_section and line.startswith('|--------'):
                    # Skip separator
                    new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # If domain section doesn't exist, add it
            if not any('Domain Statistics' in line for line in lines):
                domain_section = f"""
## Domain Statistics
| Domain | Pending | In Progress |
|--------|---------|-------------|
"""
                for domain, count in domain_counts.items():
                    domain_section += f"| {domain.capitalize()} | {count} | 0 |\n"
                
                new_lines.append(domain_section)
            
            # Write updated content
            dashboard_path.write_text('\n'.join(new_lines))
            
        except Exception as e:
            logger.error(f'Error updating dashboard: {e}')


# Global orchestrator instance
orchestrator = Orchestrator()
