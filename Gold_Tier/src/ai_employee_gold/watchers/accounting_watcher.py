"""Accounting Watcher for Gold Tier AI Employee.

This watcher monitors Odoo for accounting events and creates action files
when accounting activities are detected.

Monitored Events:
- New invoices created
- Payments received
- Overdue invoices
- Unusual expenses
- Bank statement reconciliations
"""
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_watcher import BaseWatcher
from .integrations.odoo_integration import odoo
from .core.vault import vault
from .core.audit_logger import audit_logger
from .core.error_recovery import health_monitor, HealthStatus

logger = logging.getLogger(__name__)


class AccountingWatcher(BaseWatcher):
    """Watcher for Odoo accounting events.
    
    This watcher periodically checks Odoo for:
    - New invoices (created in last check interval)
    - New payments received
    - Overdue invoices (> 30 days)
    - Large expenses (> threshold)
    
    When events are detected, action files are created in
    Needs_Action/Accounting/ for processing.
    """
    
    def __init__(
        self,
        check_interval: int = 300,  # 5 minutes
        enabled: bool = True,
        overdue_days_threshold: int = 30,
        expense_threshold: float = 2000.0
    ):
        """Initialize Accounting Watcher.
        
        Args:
            check_interval: Seconds between checks (default: 300 = 5 min)
            enabled: Whether watcher is enabled
            overdue_days_threshold: Days before invoice considered overdue
            expense_threshold: Amount threshold for flagging unusual expenses
        """
        super().__init__(
            check_interval=check_interval,
            enabled=enabled,
            domain="business",
            subdomain="accounting"
        )
        
        self.overdue_days_threshold = overdue_days_threshold
        self.expense_threshold = expense_threshold
        self.last_invoice_check = datetime.now()
        self.last_payment_check = datetime.now()
        
        logger.info(
            f"AccountingWatcher initialized: "
            f"check_interval={check_interval}s, "
            f"overdue_threshold={overdue_days_threshold} days, "
            f"expense_threshold=${expense_threshold:,.2f}"
        )
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check Odoo for accounting updates.
        
        Returns:
            List of accounting events to process
        """
        events = []
        
        try:
            # Check if Odoo is connected
            if not odoo.uid:
                logger.warning("Odoo not connected, skipping accounting check")
                health_monitor.record_health(
                    "accounting_watcher",
                    HealthStatus.DEGRADED,
                    "Odoo not connected"
                )
                return events
            
            # Check for new invoices
            new_invoices = self._check_new_invoices()
            events.extend(new_invoices)
            
            # Check for new payments
            new_payments = self._check_new_payments()
            events.extend(new_payments)
            
            # Check for overdue invoices
            overdue_invoices = self._check_overdue_invoices()
            events.extend(overdue_invoices)
            
            # Update last check time
            self.last_invoice_check = datetime.now()
            self.last_payment_check = datetime.now()
            
            logger.info(f"Accounting check complete: {len(events)} events found")
            
        except Exception as e:
            logger.error(f"Error checking for accounting updates: {e}")
            health_monitor.record_health(
                "accounting_watcher",
                HealthStatus.DEGRADED,
                str(e)
            )
        
        return events
    
    def _check_new_invoices(self) -> List[Dict[str, Any]]:
        """Check for new invoices since last check."""
        events = []
        
        try:
            # Calculate time since last check
            check_since = self.last_invoice_check.strftime("%Y-%m-%d")
            
            # Search for invoices created since last check
            domain = [
                ('invoice_date', '>=', check_since),
                ('move_type', '=', 'out_invoice')
            ]
            
            invoices = odoo.search_invoices(domain)
            
            for invoice in invoices:
                events.append({
                    "id": f"invoice_{invoice.get('id')}",
                    "type": "invoice_created",
                    "invoice_id": invoice.get('id'),
                    "invoice_number": invoice.get('name'),
                    "customer_id": invoice.get('partner_id')[0] if invoice.get('partner_id') else None,
                    "customer_name": invoice.get('partner_id')[1] if isinstance(invoice.get('partner_id'), list) else None,
                    "amount": invoice.get('amount_total', 0),
                    "due_date": invoice.get('invoice_date'),
                    "state": invoice.get('state'),
                    "timestamp": datetime.now().isoformat()
                })
            
            if invoices:
                logger.info(f"Found {len(invoices)} new invoices")
            
        except Exception as e:
            logger.error(f"Error checking new invoices: {e}")
        
        return events
    
    def _check_new_payments(self) -> List[Dict[str, Any]]:
        """Check for new payments received."""
        events = []
        
        try:
            # Search for recently paid invoices
            check_since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            domain = [
                ('invoice_date', '>=', check_since),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'paid')
            ]
            
            invoices = odoo.search_invoices(domain)
            
            for invoice in invoices:
                events.append({
                    "id": f"payment_{invoice.get('id')}",
                    "type": "payment_received",
                    "invoice_id": invoice.get('id'),
                    "invoice_number": invoice.get('name'),
                    "amount": invoice.get('amount_total', 0),
                    "payment_date": invoice.get('invoice_date'),
                    "timestamp": datetime.now().isoformat()
                })
            
            if invoices:
                logger.info(f"Found {len(invoices)} new payments")
            
        except Exception as e:
            logger.error(f"Error checking new payments: {e}")
        
        return events
    
    def _check_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Check for overdue invoices."""
        events = []
        
        try:
            # Calculate overdue date
            overdue_date = (datetime.now() - timedelta(days=self.overdue_days_threshold)).strftime("%Y-%m-%d")
            
            # Search for overdue unpaid invoices
            domain = [
                ('invoice_date', '<', overdue_date),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid'),
                ('state', '=', 'posted')
            ]
            
            invoices = odoo.search_invoices(domain)
            
            for invoice in invoices:
                # Calculate days overdue
                invoice_date = datetime.strptime(invoice.get('invoice_date', ''), "%Y-%m-%d")
                days_overdue = (datetime.now() - invoice_date).days
                
                events.append({
                    "id": f"overdue_{invoice.get('id')}",
                    "type": "overdue_invoice",
                    "invoice_id": invoice.get('id'),
                    "invoice_number": invoice.get('name'),
                    "customer_id": invoice.get('partner_id')[0] if invoice.get('partner_id') else None,
                    "customer_name": invoice.get('partner_id')[1] if isinstance(invoice.get('partner_id'), list) else None,
                    "amount": invoice.get('amount_residual', 0),
                    "original_amount": invoice.get('amount_total', 0),
                    "days_overdue": days_overdue,
                    "original_due_date": invoice.get('invoice_date'),
                    "timestamp": datetime.now().isoformat()
                })
            
            if invoices:
                logger.warning(f"Found {len(invoices)} overdue invoices")
            
        except Exception as e:
            logger.error(f"Error checking overdue invoices: {e}")
        
        return events
    
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """Create action file for accounting event.
        
        Args:
            item: Accounting event dictionary
            
        Returns:
            Path to created action file
        """
        event_type = item.get("type", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create category folder
        category_path = vault.paths.needs_action / "Accounting"
        category_path.mkdir(exist_ok=True)
        
        # Create action file based on event type
        if event_type == "invoice_created":
            content = self._create_invoice_action_file(item)
        elif event_type == "payment_received":
            content = self._create_payment_action_file(item)
        elif event_type == "overdue_invoice":
            content = self._create_overdue_action_file(item)
        else:
            content = self._create_generic_action_file(item)
        
        # Write file
        filename = f"ACCOUNTING_{event_type.upper()}_{timestamp}.md"
        file_path = category_path / filename
        file_path.write_text(content)
        
        logger.info(f"Accounting action file created: {file_path}")
        
        return file_path
    
    def _create_invoice_action_file(self, item: Dict[str, Any]) -> str:
        """Create action file for new invoice."""
        return f"""---
type: accounting
source: odoo
action_type: invoice_created
created: {datetime.now().isoformat()}
priority: normal
status: pending
domain: business
subdomain: accounting
invoice_id: {item.get('invoice_id')}
amount: {item.get('amount', 0)}
currency: PKR
customer_name: {item.get('customer_name', 'Unknown')}
due_date: {item.get('due_date')}
---

# New Invoice Created

## Invoice Information
- **Invoice Number**: {item.get('invoice_number', 'N/A')}
- **Customer**: {item.get('customer_name', 'Unknown')}
- **Amount**: PKR {item.get('amount', 0):,.2f}
- **Due Date**: {item.get('due_date', 'Net 30')}

## Suggested Actions
- [ ] Send invoice to customer
- [ ] Schedule payment follow-up
- [ ] Record in accounting ledger
- [ ] Add to accounts receivable tracking

## Customer Details
- **Customer ID**: {item.get('customer_id')}
- **Name**: {item.get('customer_name')}

---
*Generated by AccountingWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def _create_payment_action_file(self, item: Dict[str, Any]) -> str:
        """Create action file for payment received."""
        return f"""---
type: accounting
source: odoo
action_type: payment_received
created: {datetime.now().isoformat()}
priority: normal
status: pending
domain: business
subdomain: accounting
invoice_id: {item.get('invoice_id')}
amount: {item.get('amount', 0)}
currency: PKR
payment_date: {item.get('payment_date')}
---

# Payment Received

## Payment Information
- **Invoice Number**: {item.get('invoice_number', 'N/A')}
- **Amount**: PKR {item.get('amount', 0):,.2f}
- **Payment Date**: {item.get('payment_date')}
- **Status**: Paid in Full

## Suggested Actions
- [ ] Reconcile payment in bank statement
- [ ] Update accounts receivable
- [ ] Send payment confirmation to customer
- [ ] Move invoice to Done folder

---
*Generated by AccountingWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def _create_overdue_action_file(self, item: Dict[str, Any]) -> str:
        """Create action file for overdue invoice."""
        return f"""---
type: accounting
source: odoo
action_type: overdue_invoice
created: {datetime.now().isoformat()}
priority: high
status: pending
domain: business
subdomain: accounting
invoice_id: {item.get('invoice_id')}
amount: {item.get('amount', 0)}
original_amount: {item.get('original_amount', 0)}
currency: PKR
customer_name: {item.get('customer_name', 'Unknown')}
days_overdue: {item.get('days_overdue', 0)}
original_due_date: {item.get('original_due_date')}
---

# ⚠️ OVERDUE INVOICE

## Invoice Information
- **Invoice Number**: {item.get('invoice_number', 'N/A')}
- **Customer**: {item.get('customer_name', 'Unknown')}
- **Amount Due**: PKR {item.get('amount', 0):,.2f}
- **Original Amount**: PKR {item.get('original_amount', 0):,.2f}
- **Days Overdue**: {item.get('days_overdue', 0)} days
- **Original Due Date**: {item.get('original_due_date')}

## Urgency: HIGH
This invoice is **{item.get('days_overdue', 0)} days overdue**. Immediate action required.

## Suggested Actions
- [ ] Send payment reminder email to customer
- [ ] Call customer to follow up
- [ ] Consider late fees
- [ ] Escalate to collections if > 60 days
- [ ] Update cash flow forecast

## Customer Details
- **Customer ID**: {item.get('customer_id')}
- **Name**: {item.get('customer_name')}

## Recommended Email Template
```
Subject: Payment Reminder - Invoice {item.get('invoice_number', 'N/A')}

Dear {item.get('customer_name', 'Valued Customer')},

This is a friendly reminder that payment for invoice {item.get('invoice_number', 'N/A')} 
in the amount of PKR {item.get('amount', 0):,.2f} was due on {item.get('original_due_date')} 
and is now {item.get('days_overdue', 0)} days overdue.

Please arrange payment at your earliest convenience.

If you have already sent payment, please disregard this notice.

Thank you for your business.

Best regards,
Accounts Receivable Department
```

---
*Generated by AccountingWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def _create_generic_action_file(self, item: Dict[str, Any]) -> str:
        """Create generic action file for unknown event type."""
        return f"""---
type: accounting
source: odoo
action_type: {item.get('type', 'unknown')}
created: {datetime.now().isoformat()}
priority: normal
status: pending
domain: business
subdomain: accounting
---

# Accounting Event

## Event Details
- **Type**: {item.get('type', 'unknown')}
- **ID**: {item.get('id', 'N/A')}
- **Timestamp**: {item.get('timestamp', 'N/A')}

## Data
```json
{str(item)}
```

## Suggested Actions
- [ ] Review event details
- [ ] Take appropriate action
- [ ] Document in accounting records

---
*Generated by AccountingWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get watcher health status with additional accounting metrics."""
        base_status = super().get_health_status()
        
        # Add accounting-specific metrics
        base_status["accounting_metrics"] = {
            "overdue_days_threshold": self.overdue_days_threshold,
            "expense_threshold": self.expense_threshold,
            "last_invoice_check": self.last_invoice_check.isoformat() if self.last_invoice_check else None,
            "last_payment_check": self.last_payment_check.isoformat() if self.last_payment_check else None,
            "odoo_connected": bool(odoo.uid)
        }
        
        return base_status


# Global accounting watcher instance
accounting_watcher = AccountingWatcher(
    check_interval=300,  # 5 minutes
    enabled=True,
    overdue_days_threshold=30,
    expense_threshold=2000.0
)
