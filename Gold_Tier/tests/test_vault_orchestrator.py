"""
Tests for Vault Manager and Orchestrator.

Covers:
- Domain tagging
- Cross-domain routing
- File operations
- Task correlation
- Priority escalation
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_employee_gold.core.vault_manager import VaultManager, Domain
from ai_employee_gold.core.orchestrator import Orchestrator, Priority, TaskCorrelator


class TestDomainEnum:
    """Test Domain enum."""
    
    def test_domain_values(self):
        """Test domain enum values."""
        assert Domain.PERSONAL.value == "personal"
        assert Domain.BUSINESS.value == "business"
        assert Domain.FINANCE.value == "finance"
        assert Domain.SYSTEM.value == "system"
        assert Domain.UNKNOWN.value == "unknown"


class TestVaultManager:
    """Test vault manager functionality."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_initialize_vault(self, temp_vault):
        """Test vault initialization."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Check directories created
        assert (vault.vault_path / "Needs_Action").exists()
        assert (vault.vault_path / "Plans").exists()
        assert (vault.vault_path / "Done").exists()
        assert (vault.vault_path / "Audit_Logs").exists()
        assert (vault.vault_path / "Briefings").exists()
    
    def test_get_domain_for_category(self, temp_vault):
        """Test domain lookup by category."""
        vault = VaultManager(vault_path=temp_vault)
        
        assert vault.get_domain_for_category("Gmail") == Domain.PERSONAL
        assert vault.get_domain_for_category("WhatsApp") == Domain.PERSONAL
        assert vault.get_domain_for_category("LinkedIn") == Domain.BUSINESS
        assert vault.get_domain_for_category("Accounting") == Domain.FINANCE
        assert vault.get_domain_for_category("Unknown") == Domain.UNKNOWN
    
    def test_get_domain_for_file(self, temp_vault):
        """Test domain detection from file path."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Create test file in Gmail folder
        gmail_file = vault.paths.needs_action / "Gmail" / "test.md"
        gmail_file.parent.mkdir(parents=True, exist_ok=True)
        gmail_file.write_text("test content")
        
        domain = vault.get_domain_for_file(gmail_file)
        assert domain == Domain.PERSONAL
    
    def test_add_domain_tag(self, temp_vault):
        """Test adding domain tag to file."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Create file with frontmatter
        test_file = vault.paths.needs_action / "test.md"
        test_file.write_text("""---
type: test
created: 2026-03-12
---

Content here
""")
        
        # Add domain tag
        success = vault.add_domain_tag(test_file, Domain.BUSINESS)
        
        assert success
        
        # Verify tag added
        content = test_file.read_text()
        assert "domain: business" in content
    
    def test_create_action_file_with_domain(self, temp_vault):
        """Test creating action file with domain tagging."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Create action file
        file_path = vault.create_action_file(
            category="Gmail",
            filename="EMAIL_001.md",
            content="""---
type: email
from: test@example.com
---

Email content
""",
            priority="high"
        )
        
        assert file_path.exists()
        
        # Verify domain tag added
        content = file_path.read_text()
        assert "domain: personal" in content
    
    def test_move_file(self, temp_vault):
        """Test file moving."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Create source file
        source = vault.paths.inbox / "test.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("test content")
        
        # Move file
        dest = vault.move_file(source, "done")
        
        assert not source.exists()
        assert dest.exists()
        assert dest.parent.name == "Done"
    
    def test_read_write_file(self, temp_vault):
        """Test file read/write operations."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Write file
        test_file = vault.paths.plans / "test.md"
        success = vault.write_file(test_file, "test content")
        
        assert success
        assert test_file.exists()
        
        # Read file
        content = vault.read_file(test_file)
        assert content == "test content"
    
    def test_get_domain_statistics(self, temp_vault):
        """Test domain statistics."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Create some files in business domain
        business_folder = vault.paths.needs_action / "Business"
        business_folder.mkdir(exist_ok=True)
        
        for i in range(3):
            (business_folder / f"file{i}.md").write_text(f"content {i}")
        
        # Get statistics
        stats = vault.get_domain_statistics(Domain.BUSINESS)
        
        assert stats["domain"] == "business"
        assert stats["total_files"] == 3
    
    def test_route_file_to_domain(self, temp_vault):
        """Test cross-domain file routing."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Create file in root needs_action
        test_file = vault.paths.needs_action / "test.md"
        test_file.write_text("""---
type: test
domain: finance
---

Content
""")
        
        # Route file
        new_path = vault.route_file_to_domain(test_file)
        
        # Should be moved to Finance folder
        assert new_path is not None
        assert "Finance" in str(new_path)
    
    def test_agent_skills(self, temp_vault):
        """Test vault agent skills."""
        vault = VaultManager(vault_path=temp_vault)
        vault.initialize_vault()
        
        # Test move_file_skill
        source = vault.paths.inbox / "test.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("test")
        
        result = vault.move_file_skill(str(source), "done")
        assert result["success"] is True
        
        # Test read_file_skill
        dest = vault.paths.done / "test.md"
        result = vault.read_file_skill(str(dest))
        assert result["success"] is True
        assert "test" in result["content"]
        
        # Test get_domain_skill
        result = vault.get_domain_skill(str(dest))
        assert result["success"] is True
        assert "domain" in result


class TestTaskCorrelator:
    """Test task correlation."""
    
    def test_create_correlation(self):
        """Test creating task correlation."""
        correlator = TaskCorrelator()
        
        task_ids = ["task1", "task2", "task3"]
        corr_id = correlator.create_correlation(task_ids, "related")
        
        assert corr_id.startswith("corr_")
        assert len(correlator.correlations) == 1
        assert correlator.correlations[corr_id] == task_ids
    
    def test_get_related_tasks(self):
        """Test getting related tasks."""
        correlator = TaskCorrelator()
        
        task_ids = ["task1", "task2"]
        corr_id = correlator.create_correlation(task_ids)
        
        related = correlator.get_related_tasks("task1")
        
        assert len(related) == 2
        assert "task2" in related
    
    def test_add_metadata(self):
        """Test adding task metadata."""
        correlator = TaskCorrelator()
        
        correlator.add_metadata("task1", "domain", "business")
        correlator.add_metadata("task1", "priority", "high")
        
        assert correlator.task_metadata["task1"]["domain"] == "business"
        assert correlator.task_metadata["task1"]["priority"] == "high"


class TestPriority:
    """Test Priority enum."""
    
    def test_priority_values(self):
        """Test priority enum values."""
        assert Priority.LOW.value == "low"
        assert Priority.NORMAL.value == "normal"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"


class TestOrchestrator:
    """Test orchestrator functionality."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up environment
            import os
            old_vault = os.environ.get('VAULT_PATH')
            os.environ['VAULT_PATH'] = tmpdir
            
            yield tmpdir
            
            # Restore
            if old_vault:
                os.environ['VAULT_PATH'] = old_vault
            else:
                os.environ.pop('VAULT_PATH', None)
    
    def test_determine_priority_normal(self, temp_vault):
        """Test priority detection (normal)."""
        orch = Orchestrator()
        
        # Create test file
        test_file = Path(temp_vault) / "Needs_Action" / "Gmail" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""---
type: email
priority: normal
---

Normal email
""")
        
        priority = orch._determine_priority(test_file)
        assert priority == Priority.NORMAL
    
    def test_determine_priority_high(self, temp_vault):
        """Test priority detection (high)."""
        orch = Orchestrator()
        
        test_file = Path(temp_vault) / "Needs_Action" / "Gmail" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""---
type: email
priority: high
---

Urgent email
""")
        
        priority = orch._determine_priority(test_file)
        assert priority == Priority.HIGH
    
    def test_determine_priority_urgent_keyword(self, temp_vault):
        """Test priority detection (urgent keyword)."""
        orch = Orchestrator()
        
        test_file = Path(temp_vault) / "Needs_Action" / "Gmail" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""---
type: email
---

This is URGENT and needs immediate attention!
""")
        
        priority = orch._determine_priority(test_file)
        assert priority == Priority.CRITICAL
    
    def test_escalate_priority(self, temp_vault):
        """Test priority escalation."""
        orch = Orchestrator()
        
        success = orch.escalate_priority("task_123", Priority.CRITICAL, "Customer complaint")
        
        assert success
        assert orch.total_escalated == 1
    
    def test_get_correlated_tasks(self, temp_vault):
        """Test getting correlated tasks."""
        orch = Orchestrator()
        
        # Create correlation
        orch.correlator.create_correlation(["task1", "task2", "task3"])
        
        related = orch.get_correlated_tasks("task1")
        
        assert len(related) == 3
    
    def test_get_statistics(self, temp_vault):
        """Test orchestrator statistics."""
        orch = Orchestrator()
        
        # Simulate some processing
        orch.total_processed = 10
        orch.total_routed = 15
        orch.total_escalated = 2
        
        stats = orch.get_statistics()
        
        assert "uptime_seconds" in stats
        assert stats["total_processed"] == 10
        assert stats["total_routed"] == 15
        assert stats["total_escalated"] == 2
    
    def test_route_task_to_finance(self, temp_vault):
        """Test routing task to finance domain."""
        orch = Orchestrator()
        
        test_file = Path(temp_vault) / "Needs_Action" / "Accounting" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")
        
        result = orch._route_to_finance(test_file)
        
        assert "finance" in result.lower()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ai_employee_gold.core.vault_manager", "--cov=ai_employee_gold.core.orchestrator", "--cov-report=html"])
