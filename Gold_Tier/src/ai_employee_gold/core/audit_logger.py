"""Audit logging system for Gold Tier AI Employee.

This module provides:
- JSONL append-only logging
- Hash chain for tamper-evidence
- Log query functionality
- Log export (JSON, CSV, PDF)
"""
import json
import hashlib
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    """Represents a single audit log entry."""
    
    timestamp: str
    action_type: str
    actor: str
    actor_type: str  # "agent", "human", "system"
    domain: str  # "business", "personal", "system"
    subdomain: Optional[str]
    target: str
    parameters: Dict[str, Any]
    approval_status: str  # "approved", "auto", "pending", "rejected"
    approved_by: Optional[str]
    approved_at: Optional[str]
    approval_file: Optional[str]
    result: str  # "success", "failed", "partial"
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_code: Optional[str]
    execution_time_ms: int
    retry_count: int
    fallback_used: bool
    session_id: str
    correlation_id: str
    previous_hash: str
    current_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """Append-only audit logger with hash chain for tamper-evidence.
    
    Usage:
        logger = AuditLogger(vault_path="/path/to/vault")
        logger.log(
            action_type="odoo.create_invoice",
            actor="OdooAgent",
            target="Invoice INV/2026/001",
            parameters={"customer_id": 123},
            result="success"
        )
    """
    
    def __init__(self, vault_path: Optional[str] = None):
        """Initialize audit logger.
        
        Args:
            vault_path: Path to vault root directory
        """
        self.vault_path = Path(vault_path or settings.VAULT_PATH)
        self.audit_logs_dir = self.vault_path / "Audit_Logs"
        self.audit_logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_log_file: Optional[Path] = None
        self.last_hash: Optional[str] = None
        self.session_id = self._generate_session_id()
        self.buffer: List[AuditLogEntry] = []
        self.buffer_size = 10  # Flush after N entries
        
        self._initialize_daily_log()
        logger.info(f"Audit logger initialized: {self.audit_logs_dir}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}_{os.getpid()}"
    
    def _get_today_file(self) -> Path:
        """Get today's log file path."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.audit_logs_dir / f"{today}.jsonl"
    
    def _initialize_daily_log(self):
        """Initialize or load today's log file."""
        self.current_log_file = self._get_today_file()
        
        # Load last hash from existing file
        if self.current_log_file.exists():
            try:
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        self.last_hash = last_entry.get("current_hash")
                        logger.debug(f"Loaded last hash from existing log")
            except Exception as e:
                logger.warning(f"Could not load existing log: {e}")
                self.last_hash = None
        else:
            self.last_hash = None
    
    def _calculate_hash(self, entry_dict: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of entry."""
        # Create deterministic JSON string
        entry_json = json.dumps(entry_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(entry_json.encode('utf-8')).hexdigest()
    
    def log(
        self,
        action_type: str,
        actor: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None,
        result: str = "success",
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        execution_time_ms: int = 0,
        retry_count: int = 0,
        fallback_used: bool = False,
        correlation_id: Optional[str] = None,
        approval_status: str = "auto",
        approved_by: Optional[str] = None,
        approved_at: Optional[str] = None,
        approval_file: Optional[str] = None,
        domain: str = "business",
        subdomain: Optional[str] = None,
        actor_type: str = "agent",
        flush: bool = True
    ) -> AuditLogEntry:
        """Log an action to the audit trail.
        
        Args:
            action_type: Type of action (e.g., "odoo.create_invoice")
            actor: Name of actor (e.g., "OdooAgent", "human_user")
            target: Target of action (e.g., "Invoice INV/2026/001")
            parameters: Action parameters
            result: Result status ("success", "failed", "partial")
            result_data: Result data
            error_message: Error message if failed
            error_code: Error code if failed
            execution_time_ms: Execution time in milliseconds
            retry_count: Number of retries attempted
            fallback_used: Whether fallback was used
            correlation_id: Correlation ID for tracking related actions
            approval_status: Approval status
            approved_by: Who approved (if applicable)
            approved_at: When approved (if applicable)
            approval_file: Approval file path (if applicable)
            domain: Domain (business, personal, system)
            subdomain: Subdomain (accounting, social, etc.)
            actor_type: Actor type (agent, human, system)
            flush: Whether to flush to disk immediately
            
        Returns:
            Created audit log entry
        """
        # Check if we need to start a new day's log
        today_file = self._get_today_file()
        if today_file != self.current_log_file:
            self.current_log_file = today_file
            self.last_hash = None
        
        # Create entry without hash
        timestamp = datetime.now().isoformat()
        entry_dict = {
            "timestamp": timestamp,
            "action_type": action_type,
            "actor": actor,
            "actor_type": actor_type,
            "domain": domain,
            "subdomain": subdomain,
            "target": target,
            "parameters": parameters or {},
            "approval_status": approval_status,
            "approved_by": approved_by,
            "approved_at": approved_at,
            "approval_file": approval_file,
            "result": result,
            "result_data": result_data,
            "error_message": error_message,
            "error_code": error_code,
            "execution_time_ms": execution_time_ms,
            "retry_count": retry_count,
            "fallback_used": fallback_used,
            "session_id": self.session_id,
            "correlation_id": correlation_id or self._generate_correlation_id(),
            "previous_hash": self.last_hash or ""
        }
        
        # Calculate current hash (includes previous hash for chain)
        current_hash = self._calculate_hash(entry_dict)
        entry_dict["current_hash"] = current_hash
        
        # Create entry object
        entry = AuditLogEntry(**entry_dict)
        self.buffer.append(entry)
        
        # Update last hash
        self.last_hash = current_hash
        
        logger.debug(f"Audit log entry created: {action_type} - {result}")
        
        # Flush if buffer is full or requested
        if flush or len(self.buffer) >= self.buffer_size:
            self.flush()
        
        return entry
    
    def flush(self):
        """Flush buffered entries to disk."""
        if not self.buffer:
            return
        
        try:
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                for entry in self.buffer:
                    f.write(json.dumps(entry.to_dict()) + "\n")
            
            logger.debug(f"Flushed {len(self.buffer)} audit log entries")
            self.buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush audit log: {e}")
            raise
    
    def _generate_correlation_id(self) -> str:
        """Generate correlation ID for tracking related actions."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"corr_{timestamp}_{os.getpid()}"
    
    def query(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        action_type: Optional[str] = None,
        actor: Optional[str] = None,
        result: Optional[str] = None,
        domain: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditLogEntry]:
        """Query audit log entries.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            action_type: Filter by action type
            actor: Filter by actor
            result: Filter by result
            domain: Filter by domain
            correlation_id: Filter by correlation ID
            limit: Maximum entries to return
            
        Returns:
            List of matching audit log entries
        """
        results = []
        
        # Determine which files to search
        if start_date and end_date:
            from datetime import date
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
            delta = end - start
            
            files = []
            for i in range(delta.days + 1):
                day = start + timedelta(days=i)
                file = self.audit_logs_dir / f"{day.isoformat()}.jsonl"
                if file.exists():
                    files.append(file)
        elif start_date:
            file = self.audit_logs_dir / f"{start_date}.jsonl"
            files = [file] if file.exists() else []
        else:
            # Search today's file
            files = [self._get_today_file()]
        
        # Search files
        for file in files:
            if not file.exists():
                continue
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(results) >= limit:
                            break
                        
                        try:
                            entry_dict = json.loads(line)
                            
                            # Apply filters
                            if action_type and entry_dict.get("action_type") != action_type:
                                continue
                            if actor and entry_dict.get("actor") != actor:
                                continue
                            if result and entry_dict.get("result") != result:
                                continue
                            if domain and entry_dict.get("domain") != domain:
                                continue
                            if correlation_id and entry_dict.get("correlation_id") != correlation_id:
                                continue
                            
                            # Create entry object
                            entry = AuditLogEntry(**entry_dict)
                            results.append(entry)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in audit log: {file}")
                            continue
            except Exception as e:
                logger.error(f"Error reading audit log {file}: {e}")
        
        return results
    
    def verify_hash_chain(self, date: Optional[str] = None) -> bool:
        """Verify integrity of hash chain.
        
        Args:
            date: Date to verify (YYYY-MM-DD), defaults to today
            
        Returns:
            True if chain is valid, False otherwise
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = self.audit_logs_dir / f"{date}.jsonl"
        if not log_file.exists():
            logger.warning(f"Audit log not found: {log_file}")
            return True  # No file = nothing to verify
        
        try:
            previous_hash = ""
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line)
                        current_hash = entry.get("current_hash", "")
                        entry_previous_hash = entry.get("previous_hash", "")
                        
                        # Verify previous hash matches
                        if entry_previous_hash != previous_hash:
                            logger.error(
                                f"Hash chain broken at line {line_num}: "
                                f"expected '{previous_hash}', got '{entry_previous_hash}'"
                            )
                            return False
                        
                        # Verify current hash
                        entry_copy = entry.copy()
                        del entry_copy["current_hash"]
                        calculated_hash = self._calculate_hash(entry_copy)
                        
                        if calculated_hash != current_hash:
                            logger.error(
                                f"Hash mismatch at line {line_num}: "
                                f"calculated '{calculated_hash}', stored '{current_hash}'"
                            )
                            return False
                        
                        previous_hash = current_hash
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON at line {line_num}")
                        return False
            
            logger.info(f"Hash chain verified for {date}: OK")
            return True
        except Exception as e:
            logger.error(f"Error verifying hash chain: {e}")
            return False
    
    def export_json(self, output_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Export audit log to JSON file.
        
        Args:
            output_path: Output file path
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        entries = self.query(start_date=start_date, end_date=end_date, limit=100000)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([e.to_dict() for e in entries], f, indent=2)
        
        logger.info(f"Exported {len(entries)} entries to JSON: {output_path}")
    
    def export_csv(self, output_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Export audit log to CSV file.
        
        Args:
            output_path: Output file path
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        entries = self.query(start_date=start_date, end_date=end_date, limit=100000)
        
        if not entries:
            logger.warning("No entries to export")
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            # Get field names from first entry
            fieldnames = list(entries[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_dict())
        
        logger.info(f"Exported {len(entries)} entries to CSV: {output_path}")
    
    def get_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for a date.
        
        Args:
            date: Date to summarize (YYYY-MM-DD), defaults to today
            
        Returns:
            Summary statistics
        """
        entries = self.query(start_date=date, end_date=date, limit=100000)
        
        if not entries:
            return {
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "total_entries": 0,
                "by_result": {},
                "by_action_type": {},
                "by_actor": {},
                "by_domain": {},
                "avg_execution_time_ms": 0,
                "error_count": 0
            }
        
        # Calculate statistics
        by_result = {}
        by_action_type = {}
        by_actor = {}
        by_domain = {}
        total_execution_time = 0
        error_count = 0
        
        for entry in entries:
            # By result
            by_result[entry.result] = by_result.get(entry.result, 0) + 1
            
            # By action type
            by_action_type[entry.action_type] = by_action_type.get(entry.action_type, 0) + 1
            
            # By actor
            by_actor[entry.actor] = by_actor.get(entry.actor, 0) + 1
            
            # By domain
            by_domain[entry.domain] = by_domain.get(entry.domain, 0) + 1
            
            # Execution time
            total_execution_time += entry.execution_time_ms
            
            # Errors
            if entry.result == "failed":
                error_count += 1
        
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "total_entries": len(entries),
            "by_result": by_result,
            "by_action_type": by_action_type,
            "by_actor": by_actor,
            "by_domain": by_domain,
            "avg_execution_time_ms": total_execution_time / len(entries) if entries else 0,
            "error_count": error_count,
            "error_rate": error_count / len(entries) if entries else 0
        }


# Import timedelta for query
from datetime import timedelta


# Global audit logger instance
audit_logger = AuditLogger()
