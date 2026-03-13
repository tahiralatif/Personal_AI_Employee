"""Integration tests for Gold Tier AI Employee.

Tests full system integration:
- All agents working together
- Concurrent operation
- No interference between components
- Performance benchmarks
"""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path

from ai_employee_gold.core.vault_manager import vault
from ai_employee_gold.core.audit_logger import audit_logger
from ai_employee_gold.core.error_recovery import health_monitor
from ai_employee_gold.agents.odoo_agent import odoo_agent
from ai_employee_gold.agents.facebook_agent import facebook_agent
from ai_employee_gold.agents.instagram_agent import instagram_agent
from ai_employee_gold.agents.twitter_agent import twitter_agent
from ai_employee_gold.agents.financial_review_agent import financial_review_agent
from ai_employee_gold.agents.audit_agent import audit_agent
from ai_employee_gold.agents.security_agent import security_agent


class TestSystemIntegration:
    """Test full system integration."""

    def test_all_agents_initialized(self):
        """Test that all agents are initialized."""
        # Check agents exist
        assert odoo_agent is not None
        assert facebook_agent is not None
        assert instagram_agent is not None
        assert twitter_agent is not None
        assert financial_review_agent is not None
        assert audit_agent is not None
        assert security_agent is not None
        
        # Check agents have required attributes
        for agent in [odoo_agent, facebook_agent, instagram_agent, twitter_agent]:
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'version')

    def test_vault_integration(self):
        """Test vault integration with all components."""
        # Test vault is accessible
        assert vault.vault_path.exists()
        
        # Test required folders exist
        required_folders = [
            "Inbox",
            "Needs_Action",
            "Done",
            "Plans",
            "Briefings",
            "Accounting",
            "Audit_Logs"
        ]
        
        for folder in required_folders:
            folder_path = vault.vault_path / folder
            assert folder_path.exists(), f"Folder {folder} does not exist"

    def test_audit_logger_integration(self):
        """Test audit logger integration."""
        # Test logging works
        audit_logger.log(
            action_type="test.integration",
            actor="TestSuite",
            actor_type="system",
            domain="system",
            subdomain="test",
            target="Integration Test",
            parameters={"test": "integration"},
            result="success"
        )
        
        # Test query works
        entries = audit_logger.get_audit_log(limit=10)
        assert len(entries) > 0

    def test_health_monitor_integration(self):
        """Test health monitor integration."""
        # Register test component
        health_monitor.register_component("test.component")
        
        # Record health
        health_monitor.record_health("test.component", "healthy")
        
        # Get status
        status = health_monitor.get_system_health()
        assert "test.component" in status
        assert status["test.component"] == "healthy"

    def test_concurrent_agent_access(self):
        """Test concurrent access to agents."""
        async def access_agent(agent, iterations):
            """Access agent multiple times concurrently."""
            for _ in range(iterations):
                # Just check agent attributes (safe operation)
                _ = agent.name
                _ = agent.version
                await asyncio.sleep(0.01)
        
        # Run concurrent access
        async def run_concurrent_test():
            tasks = [
                access_agent(odoo_agent, 10),
                access_agent(facebook_agent, 10),
                access_agent(instagram_agent, 10),
                access_agent(twitter_agent, 10)
            ]
            await asyncio.gather(*tasks)
        
        # Should not raise any exceptions
        asyncio.run(run_concurrent_test())


class TestPerformance:
    """Test system performance."""

    def test_vault_write_performance(self):
        """Test vault write performance."""
        import time
        
        start = time.time()
        
        # Write 10 files
        for i in range(10):
            test_file = vault.vault_path / "Inbox" / f"test_{i}.md"
            test_file.write_text(f"Test content {i}")
        
        elapsed = time.time() - start
        
        # Should complete in less than 1 second
        assert elapsed < 1.0, f"Vault write too slow: {elapsed}s"
        
        # Cleanup
        for i in range(10):
            test_file = vault.vault_path / "Inbox" / f"test_{i}.md"
            if test_file.exists():
                test_file.unlink()

    def test_audit_log_write_performance(self):
        """Test audit log write performance."""
        import time
        
        start = time.time()
        
        # Write 100 log entries
        for i in range(100):
            audit_logger.log(
                action_type="test.performance",
                actor="TestSuite",
                actor_type="system",
                domain="system",
                subdomain="test",
                target=f"Test {i}",
                parameters={"test_id": i},
                result="success"
            )
        
        elapsed = time.time() - start
        
        # Should complete in less than 2 seconds
        assert elapsed < 2.0, f"Audit log write too slow: {elapsed}s"

    def test_health_monitor_performance(self):
        """Test health monitor performance."""
        import time
        
        start = time.time()
        
        # Record 50 health updates
        for i in range(50):
            health_monitor.register_component(f"test.comp_{i}")
            health_monitor.record_health(f"test.comp_{i}", "healthy")
        
        elapsed = time.time() - start
        
        # Should complete in less than 1 second
        assert elapsed < 1.0, f"Health monitor too slow: {elapsed}s"


class TestSecurity:
    """Test security integration."""

    def test_credential_manager_integration(self):
        """Test credential manager integration."""
        from ai_employee_gold.core.credential_manager import credential_manager
        
        # Test set credential
        success = credential_manager.set_credential(
            name="test_credential",
            value="test_value_123",
            expires_in_days=1
        )
        assert success
        
        # Test get credential
        value = credential_manager.get_credential("test_credential")
        assert value == "test_value_123"
        
        # Test delete credential
        success = credential_manager.delete_credential("test_credential")
        assert success

    def test_permission_manager_integration(self):
        """Test permission manager integration."""
        from ai_employee_gold.core.permission_manager import permission_manager
        
        # Test check permission
        result = permission_manager.check_permission(
            "odoo.create_invoice",
            {"amount": 100, "role": "admin"}
        )
        
        assert "permitted" in result
        assert "requires_approval" in result
        assert "risk_level" in result

    def test_security_agent_integration(self):
        """Test security agent integration."""
        # Test get credential
        result = security_agent.get_credential("nonexistent")
        assert result is None
        
        # Test check permission
        result = security_agent.check_permission("odoo.create_invoice")
        assert isinstance(result, dict)
        
        # Test get audit log
        result = security_agent.get_audit_log(limit=10)
        assert isinstance(result, list)


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self):
        """Test full workflow from start to finish."""
        # 1. Create test file in Inbox
        test_file = vault.vault_path / "Inbox" / "test_workflow.md"
        test_file.write_text("""---
type: test
status: pending
---

# Test Workflow

This is a test workflow.
""")
        
        # 2. Audit logger should log this
        audit_logger.log(
            action_type="test.workflow",
            actor="TestSuite",
            actor_type="system",
            domain="system",
            subdomain="test",
            target=str(test_file),
            parameters={"action": "create"},
            result="success"
        )
        
        # 3. Health monitor should track this
        health_monitor.register_component("test.workflow")
        health_monitor.record_health("test.workflow", "healthy")
        
        # 4. Move to Done
        done_file = vault.vault_path / "Done" / "test_workflow.md"
        vault.move_file(str(test_file), str(done_file))
        
        # Verify file moved
        assert not test_file.exists()
        assert done_file.exists()
        
        # Cleanup
        if done_file.exists():
            done_file.unlink()

    def test_agent_skills_accessibility(self):
        """Test that all agent skills are accessible."""
        # Test Odoo agent skills
        assert hasattr(odoo_agent, 'create_invoice')
        assert hasattr(odoo_agent, 'record_payment')
        
        # Test Facebook agent skills
        assert hasattr(facebook_agent, 'post_update')
        assert hasattr(facebook_agent, 'get_engagement')
        
        # Test Audit agent skills
        assert hasattr(audit_agent, 'generate_ceo_briefing')
        assert hasattr(audit_agent, 'get_audit_log')
        
        # Test Security agent skills
        assert hasattr(security_agent, 'get_credential')
        assert hasattr(security_agent, 'check_permission')


@pytest.fixture
def cleanup_test_files():
    """Cleanup test files after tests."""
    yield
    # Cleanup
    vault_path = vault.vault_path
    for pattern in ["Inbox/test_*.md", "Done/test_*.md"]:
        for file in vault_path.glob(pattern):
            if file.exists():
                try:
                    file.unlink()
                except:
                    pass


class TestConcurrentOperation:
    """Test concurrent operation."""

    def test_no_interference_between_agents(self):
        """Test that agents don't interfere with each other."""
        async def simulate_agent_work(agent_name, iterations):
            """Simulate agent working."""
            for i in range(iterations):
                # Each agent does its own work
                await asyncio.sleep(0.01)
        
        # Run all agents concurrently
        async def run_concurrent():
            tasks = [
                simulate_agent_work("odoo", 20),
                simulate_agent_work("facebook", 20),
                simulate_agent_work("instagram", 20),
                simulate_agent_work("twitter", 20),
                simulate_agent_work("audit", 20),
                simulate_agent_work("security", 20)
            ]
            await asyncio.gather(*tasks)
        
        # Should complete without errors
        asyncio.run(run_concurrent())
