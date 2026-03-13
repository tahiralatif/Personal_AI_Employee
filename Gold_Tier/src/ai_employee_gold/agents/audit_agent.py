"""Audit Agent for Gold Tier AI Employee.

This agent provides audit and compliance capabilities:
- Generate CEO Briefing
- Get audit log
- Export audit log
- Check compliance

Part of the Weekly Business Audit system.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv

from .ceo_briefing import ceo_briefing
from .audit_logger import audit_logger
from .vault_manager import vault
from ..config.settings import settings

logger = logging.getLogger(__name__)


class AuditAgent:
    """Autonomous Audit Agent.

    This agent specializes in compliance and audit tasks:
    - Generate comprehensive CEO briefings
    - Retrieve and query audit logs
    - Export audit logs in multiple formats
    - Check compliance with policies

    All audit actions are logged for accountability.
    """

    def __init__(self):
        """Initialize Audit Agent."""
        self.name = "AuditAgent"
        self.version = "1.0.0"
        self.domain = "system"
        self.subdomain = "audit_compliance"

        # Components
        self.briefing_generator = ceo_briefing
        self.audit_logger_instance = audit_logger
        self.vault = vault

        # Compliance rules
        self.compliance_rules = self._load_compliance_rules()

        # Statistics
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()

        logger.info(f"Audit Agent initialized: {self.name} v{self.version}")

    # ==================== AGENT SKILLS ====================

    def generate_ceo_briefing(
        self,
        period: str = "week",
        include_social: bool = True,
        save_to_vault: bool = True
    ) -> Dict[str, Any]:
        """Agent Skill: Generate comprehensive CEO briefing.

        Args:
            period: Time period for analysis ("week", "month", "quarter")
            include_social: Whether to include social media performance
            save_to_vault: Whether to save briefing to vault

        Returns:
            Briefing dictionary with all sections

        Example:
            >>> agent.generate_ceo_briefing(period="week")
            {
                "metadata": {...},
                "executive_summary": {...},
                "revenue_analysis": {...},
                "expense_analysis": {...},
                "social_media_performance": {...},
                "proactive_suggestions": [...]
            }
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Generating CEO briefing for period: {period}")

            # Generate briefing
            briefing = self.briefing_generator.generate_briefing(
                period=period,
                include_social=include_social
            )

            # Save to vault if requested
            filepath = None
            if save_to_vault:
                filepath = self.briefing_generator.save_briefing(briefing)

            # Log success
            self.successful_actions += 1
            self.audit_logger_instance.log(
                action_type="audit.generate_ceo_briefing",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="CEO Briefing",
                parameters={
                    "period": period,
                    "include_social": include_social,
                    "save_to_vault": save_to_vault
                },
                result="success",
                result_data={
                    "filepath": filepath,
                    "sections": len(briefing)
                },
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"CEO briefing generated successfully: {filepath}")
            return briefing

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error generating CEO briefing: {e}")
            self.audit_logger_instance.log(
                action_type="audit.generate_ceo_briefing",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="CEO Briefing",
                parameters={"period": period},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            raise

    def get_audit_log(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_type: Optional[str] = None,
        actor: Optional[str] = None,
        domain: Optional[str] = None,
        result: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Agent Skill: Query audit log with filters.

        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)
            action_type: Filter by action type
            actor: Filter by actor (agent name)
            domain: Filter by domain (business, personal, system)
            result: Filter by result (success, failed)
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries matching filters

        Example:
            >>> agent.get_audit_log(action_type="odoo.create_invoice", result="success")
            [
                {
                    "timestamp": "2026-03-13T10:30:00",
                    "action_type": "odoo.create_invoice",
                    "actor": "OdooAgent",
                    "target": "Invoice INV/2026/001",
                    "result": "success"
                }
            ]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info("Querying audit log")

            # Set default date range
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()

            # Read audit log files
            audit_logs_dir = Path(self.vault.vault_path) / "Audit_Logs"
            entries = []

            # Get log files in date range
            current_date = start_date
            while current_date <= end_date:
                log_file = audit_logs_dir / f"{current_date.strftime('%Y-%m-%d')}.jsonl"
                if log_file.exists():
                    try:
                        with open(log_file, 'r') as f:
                            for line in f:
                                if line.strip():
                                    entry = json.loads(line)
                                    entries.append(entry)
                    except Exception as e:
                        logger.error(f"Error reading log file {log_file}: {e}")
                current_date += timedelta(days=1)

            # Apply filters
            filtered_entries = []
            for entry in entries:
                # Filter by action_type
                if action_type and entry.get("action_type") != action_type:
                    continue
                # Filter by actor
                if actor and entry.get("actor") != actor:
                    continue
                # Filter by domain
                if domain and entry.get("domain") != domain:
                    continue
                # Filter by result
                if result and entry.get("result") != result:
                    continue
                # Filter by date range
                entry_date = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_date < start_date or entry_date > end_date:
                    continue

                filtered_entries.append(entry)

                # Apply limit
                if len(filtered_entries) >= limit:
                    break

            # Sort by timestamp (newest first)
            filtered_entries.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

            # Log success
            self.successful_actions += 1
            self.audit_logger_instance.log(
                action_type="audit.get_audit_log",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Audit Log Query",
                parameters={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "action_type": action_type,
                    "actor": actor,
                    "domain": domain,
                    "result": result,
                    "limit": limit
                },
                result="success",
                result_data={"entries_returned": len(filtered_entries)},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Retrieved {len(filtered_entries)} audit log entries")
            return filtered_entries

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error querying audit log: {e}")
            self.audit_logger_instance.log(
                action_type="audit.get_audit_log",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Audit Log Query",
                parameters={},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return []

    def export_audit_log(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_path: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Agent Skill: Export audit log to file.

        Args:
            format: Export format ("json", "csv", "pdf")
            start_date: Start of date range
            end_date: End of date range
            output_path: Output file path (default: Auto-generated)
            filters: Additional filters (action_type, actor, domain, result)

        Returns:
            Path to exported file, or None if failed

        Example:
            >>> agent.export_audit_log(format="csv", start_date=datetime(2026, 3, 1))
            "/path/to/vault/Audit_Logs/exports/2026-03-13_audit_export.csv"
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Exporting audit log to {format} format")

            # Get filtered entries
            filters = filters or {}
            entries = self.get_audit_log(
                start_date=start_date,
                end_date=end_date,
                **filters,
                limit=10000  # Higher limit for exports
            )

            if not entries:
                logger.warning("No audit log entries to export")
                return None

            # Generate output path
            if not output_path:
                exports_dir = Path(self.vault.vault_path) / "Audit_Logs" / "exports"
                exports_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                output_path = exports_dir / f"{timestamp}_audit_export.{format}"
            else:
                output_path = Path(output_path)

            # Export based on format
            if format.lower() == "json":
                self._export_json(entries, output_path)
            elif format.lower() == "csv":
                self._export_csv(entries, output_path)
            elif format.lower() == "pdf":
                self._export_pdf(entries, output_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            # Log success
            self.successful_actions += 1
            self.audit_logger_instance.log(
                action_type="audit.export_audit_log",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target=str(output_path),
                parameters={
                    "format": format,
                    "entries_count": len(entries)
                },
                result="success",
                result_data={"filepath": str(output_path)},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Audit log exported successfully: {output_path}")
            return str(output_path)

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error exporting audit log: {e}")
            self.audit_logger_instance.log(
                action_type="audit.export_audit_log",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Audit Log Export",
                parameters={"format": format},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return None

    def check_compliance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        check_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Agent Skill: Check compliance with policies.

        Args:
            start_date: Start of audit period
            end_date: End of audit period
            check_type: Specific compliance check ("approval", "data_retention", "security", "all")

        Returns:
            Compliance report with violations and recommendations

        Example:
            >>> agent.check_compliance(check_type="approval")
            {
                "status": "compliant",
                "violations": [],
                "recommendations": [...]
            }
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info(f"Running compliance check: {check_type or 'all'}")

            # Set default date range (last 30 days)
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()

            violations = []
            recommendations = []

            # Check approval workflow adherence
            if check_type in [None, "all", "approval"]:
                approval_violations = self._check_approval_compliance(start_date, end_date)
                violations.extend(approval_violations.get("violations", []))
                recommendations.extend(approval_violations.get("recommendations", []))

            # Check data retention policy
            if check_type in [None, "all", "data_retention"]:
                retention_violations = self._check_data_retention_compliance(start_date, end_date)
                violations.extend(retention_violations.get("violations", []))
                recommendations.extend(retention_violations.get("recommendations", []))

            # Check security policies
            if check_type in [None, "all", "security"]:
                security_violations = self._check_security_compliance(start_date, end_date)
                violations.extend(security_violations.get("violations", []))
                recommendations.extend(security_violations.get("recommendations", []))

            # Determine overall status
            if not violations:
                status = "compliant"
            elif any(v.get("severity") == "critical" for v in violations):
                status = "non_compliant"
            else:
                status = "partially_compliant"

            report = {
                "status": status,
                "check_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "check_type": check_type or "all",
                "violations": violations,
                "violations_count": len(violations),
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat()
            }

            # Log success
            self.successful_actions += 1
            self.audit_logger_instance.log(
                action_type="audit.check_compliance",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Compliance Check",
                parameters={
                    "check_type": check_type,
                    "period_days": (end_date - start_date).days
                },
                result="success",
                result_data={
                    "status": status,
                    "violations_count": len(violations)
                },
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Compliance check complete: {status}, {len(violations)} violations found")
            return report

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error checking compliance: {e}")
            self.audit_logger_instance.log(
                action_type="audit.check_compliance",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Compliance Check",
                parameters={},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return {
                "status": "error",
                "error": str(e),
                "violations": [],
                "recommendations": ["Resolve system error and retry compliance check"]
            }

    # ==================== HELPER METHODS ====================

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules."""
        return {
            "approval": {
                "require_approval_for": [
                    "odoo.create_invoice",
                    "odoo.record_payment",
                    "odoo.create_expense"
                ],
                "thresholds": {
                    "odoo.create_invoice": 500,
                    "odoo.record_payment": 1000,
                    "odoo.create_expense": 200
                }
            },
            "data_retention": {
                "audit_logs_days": 365,
                "briefings_days": 90,
                "action_files_days": 30
            },
            "security": {
                "max_failed_logins": 5,
                "credential_rotation_days": 90,
                "session_timeout_minutes": 60
            }
        }

    def _check_approval_compliance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Check approval workflow compliance."""
        violations = []
        recommendations = []

        # Get all actions that require approval
        actions_requiring_approval = self.get_audit_log(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        # Check each action
        for action in actions_requiring_approval:
            action_type = action.get("action_type", "")
            approval_status = action.get("approval_status", "auto")

            # Check if action required approval
            if action_type in self.compliance_rules["approval"]["require_approval_for"]:
                if approval_status not in ["approved", "auto"]:
                    violations.append({
                        "type": "approval_violation",
                        "severity": "high",
                        "action": action_type,
                        "timestamp": action.get("timestamp"),
                        "actor": action.get("actor"),
                        "description": f"Action {action_type} executed without approval",
                        "recommendation": "Review and implement approval workflow enforcement"
                    })

        if not violations:
            recommendations.append("✅ Approval workflow functioning correctly")
        else:
            recommendations.append(f"Review {len(violations)} approval violations")

        return {
            "violations": violations,
            "recommendations": recommendations
        }

    def _check_data_retention_compliance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Check data retention policy compliance."""
        violations = []
        recommendations = []

        # Check audit log age
        audit_logs_dir = Path(self.vault.vault_path) / "Audit_Logs"
        retention_days = self.compliance_rules["data_retention"]["audit_logs_days"]
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        if audit_logs_dir.exists():
            for log_file in audit_logs_dir.glob("*.jsonl"):
                try:
                    # Parse date from filename
                    file_date_str = log_file.stem
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    if file_date < cutoff_date:
                        violations.append({
                            "type": "data_retention_violation",
                            "severity": "low",
                            "file": str(log_file),
                            "age_days": (datetime.now() - file_date).days,
                            "description": f"Audit log older than {retention_days} days",
                            "recommendation": "Archive or delete old audit logs per policy"
                        })
                except Exception:
                    pass

        if not violations:
            recommendations.append("✅ Data retention policy compliant")
        else:
            recommendations.append(f"Review {len(violations)} old files for archival")

        return {
            "violations": violations,
            "recommendations": recommendations
        }

    def _check_security_compliance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Check security policy compliance."""
        violations = []
        recommendations = []

        # Check for repeated failures (potential brute force)
        failed_actions = self.get_audit_log(
            start_date=start_date,
            end_date=end_date,
            result="failed",
            limit=1000
        )

        # Group by actor
        actor_failures = {}
        for action in failed_actions:
            actor = action.get("actor", "unknown")
            actor_failures[actor] = actor_failures.get(actor, 0) + 1

        # Check for actors with many failures
        max_failures = self.compliance_rules["security"]["max_failed_logins"]
        for actor, count in actor_failures.items():
            if count > max_failures:
                violations.append({
                    "type": "security_concern",
                    "severity": "medium",
                    "actor": actor,
                    "failure_count": count,
                    "description": f"Actor {actor} has {count} failed actions",
                    "recommendation": "Review actor activity and consider temporary suspension"
                })

        if not violations:
            recommendations.append("✅ Security policies compliant")
        else:
            recommendations.append(f"Investigate {len(violations)} security concerns")

        return {
            "violations": violations,
            "recommendations": recommendations
        }

    def _export_json(self, entries: List[Dict[str, Any]], output_path: Path) -> None:
        """Export entries to JSON format."""
        with open(output_path, 'w') as f:
            json.dump(entries, f, indent=2)
        logger.info(f"Exported {len(entries)} entries to JSON: {output_path}")

    def _export_csv(self, entries: List[Dict[str, Any]], output_path: Path) -> None:
        """Export entries to CSV format."""
        if not entries:
            return

        # Get all unique keys
        fieldnames = set()
        for entry in entries:
            fieldnames.update(entry.keys())
        fieldnames = sorted(list(fieldnames))

        # Write CSV
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)

        logger.info(f"Exported {len(entries)} entries to CSV: {output_path}")

    def _export_pdf(self, entries: List[Dict[str, Any]], output_path: Path) -> None:
        """Export entries to PDF format (simplified text-based PDF)."""
        # Simple text-based PDF export
        # In production, use a proper PDF library like reportlab or fpdf
        content = "AUDIT LOG EXPORT\n"
        content += "=" * 80 + "\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Entries: {len(entries)}\n\n"
        content += "=" * 80 + "\n\n"

        for entry in entries:
            content += f"Timestamp: {entry.get('timestamp', 'N/A')}\n"
            content += f"Action: {entry.get('action_type', 'N/A')}\n"
            content += f"Actor: {entry.get('actor', 'N/A')}\n"
            content += f"Target: {entry.get('target', 'N/A')}\n"
            content += f"Result: {entry.get('result', 'N/A')}\n"
            content += "-" * 40 + "\n"

        with open(output_path, 'w') as f:
            f.write(content)

        logger.info(f"Exported {len(entries)} entries to PDF: {output_path}")


# Global audit agent instance
audit_agent = AuditAgent()
