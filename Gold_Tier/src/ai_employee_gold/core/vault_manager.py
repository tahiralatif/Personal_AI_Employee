"""Enhanced Vault Manager for Gold Tier AI Employee.

This module extends Silver Tier vault management with:
- Cross-domain file routing
- Domain tagging (PERSONAL, BUSINESS, FINANCE)
- Enhanced folder structure
- Domain-aware file operations
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..config.settings import settings


class Domain(Enum):
    """Domain types for cross-domain routing."""
    PERSONAL = "personal"
    BUSINESS = "business"
    FINANCE = "finance"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class VaultPaths:
    """Defines all vault paths for the AI Employee system."""

    vault_path: Path
    inbox: Path
    needs_action: Path
    in_progress: Path
    plans: Path
    pending_approval: Path
    approved: Path
    rejected: Path
    done: Path
    logs: Path
    accounting: Path
    updates: Path
    signals: Path
    briefings: Path
    audit_logs: Path
    dashboard_md: Path
    company_handbook_md: Path
    business_goals_md: Path


class VaultManager:
    """Enhanced Vault Manager for Gold Tier.
    
    Extends Silver Tier vault management with:
    - Domain tagging and routing
    - Cross-domain file operations
    - Enhanced folder structure
    - Domain-aware statistics
    """
    
    def __init__(self, vault_path: Optional[str] = None):
        """Initialize enhanced vault manager.
        
        Args:
            vault_path: Path to vault root directory
        """
        self.vault_path = Path(vault_path or settings.VAULT_PATH)
        self.paths = self._setup_paths()
        self._ensure_directories()
        
        # Domain routing rules
        self.domain_routing = {
            "Gmail": Domain.PERSONAL,
            "WhatsApp": Domain.PERSONAL,
            "LinkedIn": Domain.BUSINESS,
            "Facebook": Domain.BUSINESS,
            "Instagram": Domain.BUSINESS,
            "Twitter": Domain.BUSINESS,
            "Accounting": Domain.FINANCE,
            "Odoo": Domain.FINANCE,
            "FileDrop": Domain.SYSTEM
        }
    
    def _setup_paths(self) -> VaultPaths:
        """Setup all required vault paths."""
        return VaultPaths(
            vault_path=self.vault_path,
            inbox=self.vault_path / "Inbox",
            needs_action=self.vault_path / "Needs_Action",
            in_progress=self.vault_path / "In_Progress",
            plans=self.vault_path / "Plans",
            pending_approval=self.vault_path / "Pending_Approval",
            approved=self.vault_path / "Approved",
            rejected=self.vault_path / "Rejected",
            done=self.vault_path / "Done",
            logs=self.vault_path / "Logs",
            accounting=self.vault_path / "Accounting",
            updates=self.vault_path / "Updates",
            signals=self.vault_path / "Signals",
            briefings=self.vault_path / "Briefings",
            audit_logs=self.vault_path / "Audit_Logs",
            dashboard_md=self.vault_path / "Dashboard.md",
            company_handbook_md=self.vault_path / "Company_Handbook.md",
            business_goals_md=self.vault_path / "Business_Goals.md"
        )
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.paths.inbox,
            self.paths.needs_action,
            self.paths.in_progress,
            self.paths.plans,
            self.paths.pending_approval,
            self.paths.approved,
            self.paths.rejected,
            self.paths.done,
            self.paths.logs,
            self.paths.accounting,
            self.paths.updates,
            self.paths.signals,
            self.paths.briefings,
            self.paths.audit_logs
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create domain-specific subfolders in Needs_Action
        for domain in ["Gmail", "WhatsApp", "LinkedIn", "Facebook", "Instagram", "Twitter", "Accounting", "Finance", "FileDrop"]:
            (self.paths.needs_action / domain).mkdir(exist_ok=True)
    
    # ==================== DOMAIN TAGGING ====================
    
    def get_domain_for_category(self, category: str) -> Domain:
        """Get domain for a category.
        
        Args:
            category: Category name (e.g., "Gmail", "Accounting")
            
        Returns:
            Domain enum value
        """
        return self.domain_routing.get(category, Domain.UNKNOWN)
    
    def get_domain_for_file(self, file_path: Path) -> Domain:
        """Get domain for a file based on its path.
        
        Args:
            file_path: Path to file
            
        Returns:
            Domain enum value
        """
        # Check parent folder
        parent_name = file_path.parent.name
        domain = self.get_domain_for_category(parent_name)
        
        if domain != Domain.UNKNOWN:
            return domain
        
        # Check file content for domain hints
        if file_path.exists():
            content = file_path.read_text()
            
            if "domain: business" in content or "domain: \"business\"" in content:
                return Domain.BUSINESS
            elif "domain: finance" in content or "domain: \"finance\"" in content:
                return Domain.FINANCE
            elif "domain: personal" in content or "domain: \"personal\"" in content:
                return Domain.PERSONAL
        
        return Domain.UNKNOWN
    
    def add_domain_tag(self, file_path: Path, domain: Domain) -> bool:
        """Add domain tag to file frontmatter.
        
        Args:
            file_path: Path to file
            domain: Domain to tag
            
        Returns:
            True if successful
        """
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        
        # Check if domain already tagged
        if "domain:" in content:
            return False
        
        # Add domain to frontmatter
        lines = content.split('\n')
        new_lines = []
        in_frontmatter = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            if line.startswith('---') and i == 0:
                in_frontmatter = True
            elif line.startswith('---') and in_frontmatter and i > 0:
                # Insert domain before closing ---
                new_lines.insert(-1, f"domain: {domain.value}")
                break
        
        file_path.write_text('\n'.join(new_lines))
        return True
    
    # ==================== CROSS-DOMAIN ROUTING ====================
    
    def route_file_to_domain(self, file_path: Path) -> Optional[Path]:
        """Route file to domain-specific folder.
        
        Args:
            file_path: Path to file
            
        Returns:
            New path if moved, None if not applicable
        """
        if not file_path.exists():
            return None
        
        # Get domain
        domain = self.get_domain_for_file(file_path)
        
        if domain == Domain.UNKNOWN:
            return None
        
        # Create domain folder if needed
        domain_folder = self.paths.needs_action / domain.value.capitalize()
        domain_folder.mkdir(exist_ok=True)
        
        # Move file if not already in domain folder
        if file_path.parent != domain_folder:
            new_path = domain_folder / file_path.name
            file_path.rename(new_path)
            return new_path
        
        return None
    
    def get_domain_statistics(self, domain: Domain) -> Dict[str, Any]:
        """Get statistics for a domain.
        
        Args:
            domain: Domain to get statistics for
            
        Returns:
            Statistics dictionary
        """
        domain_folder = self.paths.needs_action / domain.value.capitalize()
        
        if not domain_folder.exists():
            return {
                "domain": domain.value,
                "total_files": 0,
                "folders": []
            }
        
        # Count files
        files = list(domain_folder.glob("*.md"))
        folders = [f.name for f in domain_folder.iterdir() if f.is_dir()]
        
        return {
            "domain": domain.value,
            "total_files": len(files),
            "folders": folders,
            "recent_files": [f.name for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]]
        }
    
    # ==================== ENHANCED FILE OPERATIONS ====================
    
    def create_action_file(
        self,
        category: str,
        filename: str,
        content: str,
        priority: str = "normal",
        domain: Optional[Domain] = None
    ) -> Path:
        """Create an action file with domain tagging.
        
        Args:
            category: Category (Gmail, WhatsApp, etc.)
            filename: File name
            content: File content
            priority: Priority level
            domain: Optional domain (auto-detected if not provided)
            
        Returns:
            Path to created file
        """
        # Get domain from category if not provided
        if domain is None:
            domain = self.get_domain_for_category(category)
        
        # Create category folder
        category_path = self.paths.needs_action / category
        category_path.mkdir(exist_ok=True)
        
        # Add domain tag to content if not present
        if "domain:" not in content:
            # Insert domain in frontmatter
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('---') and i > 0:
                    lines.insert(i, f"domain: {domain.value}")
                    break
            content = '\n'.join(lines)
        
        # Write file
        file_path = category_path / filename
        file_path.write_text(content, encoding='utf-8')
        
        return file_path
    
    def move_file(self, source: Path, destination_folder: str) -> Path:
        """Move a file to a destination folder.
        
        Args:
            source: Source file path
            destination_folder: Destination folder name
            
        Returns:
            New file path
        """
        dest_path = getattr(self.paths, destination_folder, None)
        
        if dest_path is None:
            dest_path = self.vault_path / destination_folder
        
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)
        
        dest_file = dest_path / source.name
        source.rename(dest_file)
        
        return dest_file
    
    def read_file(self, file_path: Path) -> str:
        """Read file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content
        """
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return ""
    
    def write_file(self, file_path: Path, content: str) -> bool:
        """Write content to file.
        
        Args:
            file_path: Path to file
            content: Content to write
            
        Returns:
            True if successful
        """
        try:
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception:
            return False
    
    # ==================== DASHBOARD & INITIALIZATION ====================
    
    def initialize_vault(self):
        """Initialize the vault with required files."""
        self.create_dashboard_if_missing()
        self.create_company_handbook_if_missing()
        self.create_business_goals_if_missing()
    
    def create_dashboard_if_missing(self):
        """Create Dashboard.md if it doesn't exist."""
        if not self.paths.dashboard_md.exists():
            content = f"""# 📊 AI Employee Dashboard

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: 🟢 Running

## Quick Stats
| Metric | Value |
|--------|-------|
| Pending Items | 0 |
| In Progress | 0 |
| Awaiting Approval | 0 |
| Completed Today | 0 |

## Domain Statistics
| Domain | Pending | In Progress |
|--------|---------|-------------|
| Personal | 0 | 0 |
| Business | 0 | 0 |
| Finance | 0 | 0 |

## Recent Activity
- [{datetime.now().strftime("%Y-%m-%d %H:%M")}] System started

## Pending Approvals
None

## Active Projects
None

## Alerts
- ℹ️ System operational

---
*Generated by AI Employee v0.3.0*
"""
            self.paths.dashboard_md.write_text(content, encoding='utf-8')
    
    def create_company_handbook_if_missing(self):
        """Create Company_Handbook.md if it doesn't exist."""
        if not self.paths.company_handbook_md.exists():
            content = """# 📖 Company Handbook - Rules of Engagement

**Last Updated**: 2026-03-12

## Communication Rules
1. Always be polite and professional
2. Response time target: < 24 hours
3. Flag urgent messages immediately
4. Never send bulk emails without approval

## Financial Rules
1. Auto-approve payments < $50 to known recipients
2. Always require approval for:
   - New recipients
   - Payments > $100
   - Recurring payments > $50/month
3. Flag transactions > $500 for review

## Social Media Rules
1. Auto-post scheduled content
2. Require approval for:
   - Replies to comments
   - Direct messages
   - Sensitive topics

## Privacy Rules
1. Never share credentials
2. Log all actions
3. Encrypt sensitive data
4. Review logs weekly

## Escalation Rules
1. Unknown sender + large amount = Alert immediately
2. Legal/medical topics = Require human review
3. Emotional content = Flag for human handling
"""
            self.paths.company_handbook_md.write_text(content, encoding='utf-8')
    
    def create_business_goals_if_missing(self):
        """Create Business_Goals.md if it doesn't exist."""
        if not self.paths.business_goals_md.exists():
            content = """# 🎯 Business Goals - Q1 2026

**Last Updated**: 2026-03-12
**Review Frequency**: Weekly

## Revenue Targets
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Monthly Revenue | $10,000 | $0 | 🔴 0% |
| MTD | $0 | $0 | 🔴 Not Started |

## Key Metrics to Track
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

## Active Projects
None

## Subscription Audit Rules
Flag for review if:
- No login in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool
"""
            self.paths.business_goals_md.write_text(content, encoding='utf-8')
    
    # ==================== AGENT SKILLS ====================
    # All methods below are Agent Skills
    
    def move_file_skill(self, source_path: str, destination_folder: str) -> Dict[str, Any]:
        """Agent Skill: Move file to destination folder.
        
        Args:
            source_path: Source file path
            destination_folder: Destination folder name
            
        Returns:
            Result dictionary
        """
        try:
            source = Path(source_path)
            if not source.exists():
                return {"success": False, "error": f"File not found: {source_path}"}
            
            dest = self.move_file(source, destination_folder)
            return {
                "success": True,
                "source": str(source),
                "destination": str(dest),
                "message": f"Moved to {destination_folder}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_file_skill(self, file_path: str) -> Dict[str, Any]:
        """Agent Skill: Read file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content
        """
        try:
            content = self.read_file(Path(file_path))
            if content:
                return {"success": True, "content": content}
            else:
                return {"success": False, "error": f"File not found: {file_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_file_skill(self, file_path: str, content: str) -> Dict[str, Any]:
        """Agent Skill: Write content to file.
        
        Args:
            file_path: Path to file
            content: Content to write
            
        Returns:
            Result dictionary
        """
        try:
            success = self.write_file(Path(file_path), content)
            if success:
                return {"success": True, "message": f"Written to {file_path}"}
            else:
                return {"success": False, "error": "Failed to write file"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_domain_skill(self, file_path: str) -> Dict[str, Any]:
        """Agent Skill: Get domain for file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Domain information
        """
        try:
            domain = self.get_domain_for_file(Path(file_path))
            return {
                "success": True,
                "domain": domain.value,
                "file": file_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_domain_statistics_skill(self, domain_name: str) -> Dict[str, Any]:
        """Agent Skill: Get statistics for domain.
        
        Args:
            domain_name: Domain name (personal, business, finance)
            
        Returns:
            Domain statistics
        """
        try:
            domain = Domain(domain_name)
            stats = self.get_domain_statistics(domain)
            return {"success": True, "statistics": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global vault instance
vault = VaultManager()
