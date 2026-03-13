"""
Tests for Audit Logging System.

Covers:
- Audit log entry creation
- Hash chain verification
- Query functionality
- Export functions
- Tamper detection
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_employee_gold.core.audit_logger import AuditLogger, AuditLogEntry


class TestAuditLogEntry:
    """Test audit log entry data structure."""
    
    def test_create_entry(self):
        """Test creating audit log entry."""
        entry = AuditLogEntry(
            timestamp="2026-03-12T10:30:00",
            action_type="test.action",
            actor="TestActor",
            actor_type="agent",
            domain="business",
            subdomain="test",
            target="Test Target",
            parameters={"key": "value"},
            approval_status="auto",
            approved_by=None,
            approved_at=None,
            approval_file=None,
            result="success",
            result_data={"id": 123},
            error_message=None,
            error_code=None,
            execution_time_ms=100,
            retry_count=0,
            fallback_used=False,
            session_id="session_123",
            correlation_id="corr_456",
            previous_hash="",
            current_hash="abc123"
        )
        
        assert entry.action_type == "test.action"
        assert entry.result == "success"
        assert entry.execution_time_ms == 100
    
    def test_entry_to_dict(self):
        """Test converting entry to dictionary."""
        entry = AuditLogEntry(
            timestamp="2026-03-12T10:30:00",
            action_type="test.action",
            actor="TestActor",
            actor_type="agent",
            domain="business",
            subdomain="test",
            target="Test Target",
            parameters={},
            approval_status="auto",
            approved_by=None,
            approved_at=None,
            approval_file=None,
            result="success",
            result_data=None,
            error_message=None,
            error_code=None,
            execution_time_ms=100,
            retry_count=0,
            fallback_used=False,
            session_id="session_123",
            correlation_id="corr_456",
            previous_hash="",
            current_hash="abc123"
        )
        
        entry_dict = entry.to_dict()
        
        assert isinstance(entry_dict, dict)
        assert entry_dict["action_type"] == "test.action"
        assert "timestamp" in entry_dict
    
    def test_entry_to_json(self):
        """Test converting entry to JSON."""
        entry = AuditLogEntry(
            timestamp="2026-03-12T10:30:00",
            action_type="test.action",
            actor="TestActor",
            actor_type="agent",
            domain="business",
            subdomain="test",
            target="Test Target",
            parameters={},
            approval_status="auto",
            approved_by=None,
            approved_at=None,
            approval_file=None,
            result="success",
            result_data=None,
            error_message=None,
            error_code=None,
            execution_time_ms=100,
            retry_count=0,
            fallback_used=False,
            session_id="session_123",
            correlation_id="corr_456",
            previous_hash="",
            current_hash="abc123"
        )
        
        json_str = entry.to_json()
        
        assert isinstance(json_str, str)
        assert "test.action" in json_str


class TestAuditLogger:
    """Test audit logger functionality."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_initialize_logger(self, temp_vault):
        """Test logger initialization."""
        logger = AuditLogger(vault_path=temp_vault)
        
        assert logger.vault_path == Path(temp_vault)
        assert logger.audit_logs_dir.exists()
        assert logger.audit_logs_dir.name == "Audit_Logs"
    
    def test_log_entry_creation(self, temp_vault):
        """Test creating log entries."""
        logger = AuditLogger(vault_path=temp_vault)
        
        entry = logger.log(
            action_type="test.action",
            actor="TestActor",
            target="Test Target",
            parameters={"key": "value"},
            result="success"
        )
        
        assert entry is not None
        assert entry.action_type == "test.action"
        assert entry.result == "success"
        assert entry.current_hash is not None
        assert entry.previous_hash is not None
    
    def test_hash_chain(self, temp_vault):
        """Test hash chain integrity."""
        logger = AuditLogger(vault_path=temp_vault)
        
        # Create multiple entries
        entry1 = logger.log(
            action_type="action1",
            actor="Actor",
            target="Target1",
            result="success"
        )
        
        entry2 = logger.log(
            action_type="action2",
            actor="Actor",
            target="Target2",
            result="success"
        )
        
        # Second entry should include hash of first
        assert entry2.previous_hash == entry1.current_hash
    
    def test_verify_hash_chain_valid(self, temp_vault):
        """Test hash chain verification (valid)."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="action1", actor="Actor", target="Target1", result="success")
        logger.log(action_type="action2", actor="Actor", target="Target2", result="success")
        
        # Flush to disk
        logger.flush()
        
        # Verify chain
        today = datetime.now().strftime("%Y-%m-%d")
        is_valid = logger.verify_hash_chain(today)
        
        assert is_valid
    
    def test_query_by_action_type(self, temp_vault):
        """Test querying logs by action type."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="odoo.create_invoice", actor="Actor", target="Target", result="success")
        logger.log(action_type="odoo.record_payment", actor="Actor", target="Target", result="success")
        logger.log(action_type="odoo.create_invoice", actor="Actor", target="Target", result="success")
        
        logger.flush()
        
        # Query by action type
        results = logger.query(action_type="odoo.create_invoice")
        
        assert len(results) == 2
    
    def test_query_by_result(self, temp_vault):
        """Test querying logs by result."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="action1", actor="Actor", target="Target", result="success")
        logger.log(action_type="action2", actor="Actor", target="Target", result="failed")
        logger.log(action_type="action3", actor="Actor", target="Target", result="success")
        
        logger.flush()
        
        # Query by result
        results = logger.query(result="failed")
        
        assert len(results) == 1
    
    def test_query_by_actor(self, temp_vault):
        """Test querying logs by actor."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="action1", actor="Actor1", target="Target", result="success")
        logger.log(action_type="action2", actor="Actor2", target="Target", result="success")
        
        logger.flush()
        
        # Query by actor
        results = logger.query(actor="Actor1")
        
        assert len(results) == 1
    
    def test_query_limit(self, temp_vault):
        """Test query with limit."""
        logger = AuditLogger(vault_path=temp_vault)
        
        for i in range(10):
            logger.log(action_type=f"action{i}", actor="Actor", target="Target", result="success")
        
        logger.flush()
        
        # Query with limit
        results = logger.query(limit=5)
        
        assert len(results) <= 5
    
    def test_export_json(self, temp_vault):
        """Test JSON export."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="action1", actor="Actor", target="Target", result="success")
        logger.log(action_type="action2", actor="Actor", target="Target", result="success")
        
        logger.flush()
        
        # Export to JSON
        output_path = Path(temp_vault) / "export.json"
        logger.export_json(str(output_path))
        
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_export_csv(self, temp_vault):
        """Test CSV export."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="action1", actor="Actor", target="Target", result="success")
        logger.log(action_type="action2", actor="Actor", target="Target", result="success")
        
        logger.flush()
        
        # Export to CSV
        output_path = Path(temp_vault) / "export.csv"
        logger.export_csv(str(output_path))
        
        assert output_path.exists()
        
        # Verify CSV has content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) >= 2  # Header + at least 1 data row
    
    def test_get_summary(self, temp_vault):
        """Test getting summary statistics."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="odoo.create_invoice", actor="Actor", target="Target", result="success")
        logger.log(action_type="odoo.create_invoice", actor="Actor", target="Target", result="success")
        logger.log(action_type="odoo.record_payment", actor="Actor", target="Target", result="failed")
        
        logger.flush()
        
        # Get summary
        today = datetime.now().strftime("%Y-%m-%d")
        summary = logger.get_summary(today)
        
        assert summary["total_entries"] == 3
        assert summary["by_result"]["success"] == 2
        assert summary["by_result"]["failed"] == 1
        assert summary["error_count"] == 1
    
    def test_flush_buffer(self, temp_vault):
        """Test manual flush."""
        logger = AuditLogger(vault_path=temp_vault)
        
        # Log without flush
        logger.log(action_type="action1", actor="Actor", target="Target", result="success", flush=False)
        
        # Check file doesn't exist yet
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = logger.audit_logs_dir / f"{today}.jsonl"
        
        # Flush manually
        logger.flush()
        
        # Now file should exist
        assert log_file.exists()
    
    def test_auto_flush_on_buffer_size(self, temp_vault):
        """Test automatic flush when buffer is full."""
        logger = AuditLogger(vault_path=temp_vault)
        logger.buffer_size = 3  # Small buffer for testing
        
        # Log more than buffer size
        for i in range(5):
            logger.log(action_type=f"action{i}", actor="Actor", target="Target", result="success")
        
        # Buffer should have been flushed
        assert len(logger.buffer) < logger.buffer_size
    
    def test_correlation_id_tracking(self, temp_vault):
        """Test correlation ID in logs."""
        logger = AuditLogger(vault_path=temp_vault)
        
        correlation_id = "test_corr_123"
        
        entry = logger.log(
            action_type="action1",
            actor="Actor",
            target="Target",
            result="success",
            correlation_id=correlation_id
        )
        
        assert entry.correlation_id == correlation_id
    
    def test_session_id_generation(self, temp_vault):
        """Test session ID generation."""
        logger1 = AuditLogger(vault_path=temp_vault)
        logger2 = AuditLogger(vault_path=temp_vault)
        
        # Different instances should have different session IDs
        assert logger1.session_id != logger2.session_id


class TestTamperDetection:
    """Test tamper-evident logging."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_detect_modified_entry(self, temp_vault):
        """Test detection of modified log entry."""
        logger = AuditLogger(vault_path=temp_vault)
        
        logger.log(action_type="action1", actor="Actor", target="Target", result="success")
        logger.log(action_type="action2", actor="Actor", target="Target", result="success")
        
        logger.flush()
        
        # Tamper with log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = logger.audit_logs_dir / f"{today}.jsonl"
        
        content = log_file.read_text()
        lines = content.strip().split('\n')
        
        # Modify first entry
        first_entry = json.loads(lines[0])
        first_entry["result"] = "failed"  # Tamper!
        lines[0] = json.dumps(first_entry)
        
        log_file.write_text('\n'.join(lines))
        
        # Create new logger to verify
        logger2 = AuditLogger(vault_path=temp_vault)
        
        # Verification should fail
        is_valid = logger2.verify_hash_chain(today)
        
        assert not is_valid


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ai_employee_gold.core.audit_logger", "--cov-report=html"])
