"""Odoo Agent for Gold Tier AI Employee.

This module implements an autonomous Odoo accounting agent with full tool access.
The agent can create invoices, record payments, track expenses, and generate reports.

Agent Skills:
1. create_invoice - Create invoice in Odoo
2. record_payment - Record payment against invoice
3. create_expense - Create expense record
4. get_financial_summary - Get financial summary for period
5. get_outstanding_invoices - Get list of outstanding invoices
6. get_customer_details - Get customer information
7. check_accounts_receivable - Check money owed to business
8. check_accounts_payable - Check money owed by business
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..mcp.odoo_mcp import odoo_mcp_server
from ..core.vault import vault
from ..core.audit_logger import audit_logger
from ..core.error_recovery import health_monitor, HealthStatus
from ..config.settings import settings

logger = logging.getLogger(__name__)


class OdooAgent:
    """Autonomous Odoo Accounting Agent.
    
    This agent has full access to Odoo ERP tools and can:
    - Create and manage invoices
    - Record payments
    - Track expenses
    - Generate financial reports
    - Monitor accounts receivable/payable
    
    All actions are logged to the audit trail and require approval
    for sensitive operations (e.g., payments over threshold).
    """
    
    def __init__(self):
        """Initialize Odoo Agent."""
        self.name = "OdooAgent"
        self.version = "1.0.0"
        self.domain = "business"
        self.subdomain = "accounting"
        
        # MCP server
        self.mcp_server = odoo_mcp_server
        
        # Approval thresholds
        self.payment_approval_threshold = float(
            settings.ODOO_PAYMENT_APPROVAL_THRESHOLD
            if hasattr(settings, 'ODOO_PAYMENT_APPROVAL_THRESHOLD')
            else 1000.0
        )
        self.invoice_approval_threshold = float(
            settings.ODOO_INVOICE_APPROVAL_THRESHOLD
            if hasattr(settings, 'ODOO_INVOICE_APPROVAL_THRESHOLD')
            else 5000.0
        )
        
        # Statistics
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()
        
        logger.info(f"Odoo Agent initialized: {self.name} v{self.version}")
    
    # ==================== AGENT SKILLS ====================
    # All methods below are Agent Skills that can be called by AI
    
    def create_invoice(
        self,
        customer_id: int,
        items: List[Dict[str, Any]],
        due_date: Optional[str] = None,
        requires_approval: bool = True
    ) -> Dict[str, Any]:
        """Agent Skill: Create invoice in Odoo.
        
        Args:
            customer_id: Odoo customer/partner ID
            items: List of invoice line items
                Each item: {
                    "product_id": int (optional),
                    "name": str,
                    "quantity": number,
                    "price_unit": number
                }
            due_date: Invoice due date (YYYY-MM-DD)
            requires_approval: Whether approval is needed for large invoices
            
        Returns:
            Result dictionary with invoice_id or error
            
        Example:
            >>> agent.create_invoice(
            ...     customer_id=123,
            ...     items=[
            ...         {"name": "Consulting Services", "quantity": 10, "price_unit": 500}
            ...     ],
            ...     due_date="2026-04-01"
            ... )
        """
        self.total_actions += 1
        start_time = datetime.now()
        
        try:
            # Calculate total amount
            total_amount = sum(
                item.get("quantity", 1) * item.get("price_unit", 0)
                for item in items
            )
            
            # Check if approval needed
            if requires_approval and total_amount >= self.invoice_approval_threshold:
                logger.info(f"Invoice {total_amount} >= {self.invoice_approval_threshold}, requires approval")
                return self._request_invoice_approval(customer_id, items, due_date, total_amount)
            
            # Call MCP tool
            result = self.mcp_server.call_tool("create_invoice", {
                "customer_id": customer_id,
                "items": items,
                "due_date": due_date
            })
            
            if result.get("success"):
                self.successful_actions += 1
                
                # Audit log
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                audit_logger.log(
                    action_type="odoo_agent.create_invoice",
                    actor=self.name,
                    actor_type="agent",
                    domain=self.domain,
                    subdomain=self.subdomain,
                    target=f"Invoice for customer {customer_id}",
                    parameters={
                        "customer_id": customer_id,
                        "items": items,
                        "total_amount": total_amount
                    },
                    result="success",
                    result_data=result,
                    execution_time_ms=execution_time
                )
                
                logger.info(f"Invoice created: {result.get('invoice_id')}")
            else:
                self.failed_actions += 1
                logger.error(f"Failed to create invoice: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error in create_invoice: {e}")
            return {"success": False, "error": str(e)}
    
    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_method: str = "bank",
        payment_date: Optional[str] = None,
        requires_approval: bool = True
    ) -> Dict[str, Any]:
        """Agent Skill: Record payment against invoice.
        
        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            payment_method: Payment method (bank, cash, check, etc.)
            payment_date: Payment date (YYYY-MM-DD)
            requires_approval: Whether approval is needed for large payments
            
        Returns:
            Result dictionary with payment_id or error
            
        Example:
            >>> agent.record_payment(
            ...     invoice_id=456,
            ...     amount=5000,
            ...     payment_method="bank",
            ...     payment_date="2026-03-12"
            ... )
        """
        self.total_actions += 1
        start_time = datetime.now()
        
        try:
            # Check if approval needed
            if requires_approval and amount >= self.payment_approval_threshold:
                logger.info(f"Payment {amount} >= {self.payment_approval_threshold}, requires approval")
                return self._request_payment_approval(invoice_id, amount, payment_method, payment_date)
            
            # Call MCP tool
            result = self.mcp_server.call_tool("record_payment", {
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_method": payment_method,
                "payment_date": payment_date
            })
            
            if result.get("success"):
                self.successful_actions += 1
                
                # Audit log
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                audit_logger.log(
                    action_type="odoo_agent.record_payment",
                    actor=self.name,
                    actor_type="agent",
                    domain=self.domain,
                    subdomain=self.subdomain,
                    target=f"Payment for invoice {invoice_id}",
                    parameters={
                        "invoice_id": invoice_id,
                        "amount": amount,
                        "payment_method": payment_method
                    },
                    result="success",
                    result_data=result,
                    execution_time_ms=execution_time,
                    approval_status="auto" if amount < self.payment_approval_threshold else "approved"
                )
                
                logger.info(f"Payment recorded: {result.get('payment_id')}")
            else:
                self.failed_actions += 1
                logger.error(f"Failed to record payment: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error in record_payment: {e}")
            return {"success": False, "error": str(e)}
    
    def create_expense(
        self,
        amount: float,
        category: str,
        description: str,
        employee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Agent Skill: Create expense record in Odoo.
        
        Args:
            amount: Expense amount
            category: Expense category
            description: Expense description
            employee_id: Employee ID who incurred expense
            
        Returns:
            Result dictionary with expense_id or error
            
        Example:
            >>> agent.create_expense(
            ...     amount=500,
            ...     category="Office Supplies",
            ...     description="Printer paper and ink",
            ...     employee_id=1
            ... )
        """
        self.total_actions += 1
        start_time = datetime.now()
        
        try:
            # Call MCP tool
            result = self.mcp_server.call_tool("create_expense", {
                "amount": amount,
                "category": category,
                "description": description,
                "employee_id": employee_id
            })
            
            if result.get("success"):
                self.successful_actions += 1
                
                # Audit log
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                audit_logger.log(
                    action_type="odoo_agent.create_expense",
                    actor=self.name,
                    actor_type="agent",
                    domain=self.domain,
                    subdomain=self.subdomain,
                    target=f"Expense: {description}",
                    parameters={
                        "amount": amount,
                        "category": category,
                        "description": description
                    },
                    result="success",
                    result_data=result,
                    execution_time_ms=execution_time
                )
                
                logger.info(f"Expense created: {result.get('expense_id')}")
            else:
                self.failed_actions += 1
                logger.error(f"Failed to create expense: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error in create_expense: {e}")
            return {"success": False, "error": str(e)}
    
    def get_financial_summary(
        self,
        period: str = "month"
    ) -> Dict[str, Any]:
        """Agent Skill: Get financial summary for a period.
        
        Args:
            period: Report period (week, month, quarter, year)
            
        Returns:
            Financial summary dictionary
            
        Example:
            >>> agent.get_financial_summary(period="month")
        """
        try:
            # Call MCP tool
            result = self.mcp_server.call_tool("get_financial_report", {
                "period": period
            })
            
            if result.get("success"):
                report = result.get("report", {})
                
                logger.info(f"Financial summary for {period}: Revenue={report.get('total_revenue')}, Outstanding={report.get('total_outstanding')}")
                
                return {
                    "success": True,
                    "period": period,
                    "revenue": report.get("total_revenue", 0),
                    "outstanding": report.get("total_outstanding", 0),
                    "invoice_count": report.get("invoice_count", 0),
                    "recent_invoices": report.get("invoices", [])
                }
            else:
                logger.error(f"Failed to get financial summary: {result.get('error')}")
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Error in get_financial_summary: {e}")
            return {"success": False, "error": str(e)}
    
    def get_outstanding_invoices(
        self,
        limit: int = 50,
        overdue_only: bool = False
    ) -> Dict[str, Any]:
        """Agent Skill: Get list of outstanding invoices.
        
        Args:
            limit: Maximum number of invoices to return
            overdue_only: Return only overdue invoices
            
        Returns:
            List of outstanding invoices
            
        Example:
            >>> agent.get_outstanding_invoices(overdue_only=True)
        """
        try:
            # Get accounts receivable (money owed to you)
            result = self.mcp_server.call_tool("get_accounts_receivable", {
                "limit": limit,
                "overdue_only": overdue_only
            })
            
            if result.get("success"):
                receivables = result.get("receivables", {})
                
                return {
                    "success": True,
                    "total_amount": receivables.get("total_amount", 0),
                    "count": receivables.get("count", 0),
                    "overdue_only": overdue_only,
                    "invoices": receivables.get("invoices", [])
                }
            else:
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Error in get_outstanding_invoices: {e}")
            return {"success": False, "error": str(e)}
    
    def get_customer_details(self, customer_id: int) -> Dict[str, Any]:
        """Agent Skill: Get customer information.
        
        Args:
            customer_id: Odoo customer/partner ID
            
        Returns:
            Customer details dictionary
            
        Example:
            >>> agent.get_customer_details(123)
        """
        try:
            # Call MCP tool
            result = self.mcp_server.call_tool("get_customer", {
                "customer_id": customer_id
            })
            
            if result.get("success"):
                return {
                    "success": True,
                    "customer": result.get("customer", {})
                }
            else:
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Error in get_customer_details: {e}")
            return {"success": False, "error": str(e)}
    
    def check_accounts_receivable(
        self,
        limit: int = 50,
        overdue_only: bool = False
    ) -> Dict[str, Any]:
        """Agent Skill: Check money owed to business.
        
        Args:
            limit: Maximum number of records
            overdue_only: Only overdue invoices
            
        Returns:
            Accounts receivable summary
        """
        return self.get_outstanding_invoices(limit, overdue_only)
    
    def check_accounts_payable(
        self,
        limit: int = 50,
        overdue_only: bool = False
    ) -> Dict[str, Any]:
        """Agent Skill: Check money owed by business.
        
        Args:
            limit: Maximum number of records
            overdue_only: Only overdue bills
            
        Returns:
            Accounts payable summary
            
        Example:
            >>> agent.check_accounts_payable(overdue_only=True)
        """
        try:
            # Call MCP tool
            result = self.mcp_server.call_tool("get_accounts_payable", {
                "limit": limit,
                "overdue_only": overdue_only
            })
            
            if result.get("success"):
                payables = result.get("payables", {})
                
                return {
                    "success": True,
                    "total_amount": payables.get("total_amount", 0),
                    "count": payables.get("count", 0),
                    "overdue_only": overdue_only,
                    "bills": payables.get("invoices", [])
                }
            else:
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Error in check_accounts_payable: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== HELPER METHODS ====================
    
    def _request_invoice_approval(
        self,
        customer_id: int,
        items: List[Dict[str, Any]],
        due_date: Optional[str],
        total_amount: float
    ) -> Dict[str, Any]:
        """Request approval for large invoice."""
        # Create approval request file
        approval_content = f"""---
type: approval_request
action: odoo.create_invoice
created: {datetime.now().isoformat()}
expires: {datetime.now().replace(hour=23, minute=59, second=59).isoformat()}
status: pending
urgency: high
category: financial
risk_level: medium
estimated_amount: {total_amount}
---

# Invoice Approval Request

## Invoice Details
- **Customer ID**: {customer_id}
- **Total Amount**: ${total_amount:,.2f}
- **Due Date**: {due_date or 'Net 30'}
- **Items**: {len(items)} line items

## Line Items
"""
        for i, item in enumerate(items, 1):
            approval_content += f"\n{i}. {item.get('name', 'Service')} - {item.get('quantity', 1)} x ${item.get('price_unit', 0):,.2f}"
        
        approval_content += f"""

## Approval Required
This invoice exceeds the auto-approval threshold of ${self.invoice_approval_threshold:,.2f}

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.
"""
        
        # Write approval file
        approval_file = vault.paths.pending_approval / f"APPROVAL_INVOICE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        approval_file.write_text(approval_content)
        
        logger.info(f"Approval request created: {approval_file}")
        
        return {
            "success": False,
            "requires_approval": True,
            "approval_file": str(approval_file),
            "message": f"Invoice requires approval (amount ${total_amount:,.2f} >= threshold ${self.invoice_approval_threshold:,.2f})"
        }
    
    def _request_payment_approval(
        self,
        invoice_id: int,
        amount: float,
        payment_method: str,
        payment_date: Optional[str]
    ) -> Dict[str, Any]:
        """Request approval for large payment."""
        # Create approval request file
        approval_content = f"""---
type: approval_request
action: odoo.record_payment
created: {datetime.now().isoformat()}
expires: {datetime.now().replace(hour=23, minute=59, second=59).isoformat()}
status: pending
urgency: high
category: financial
risk_level: medium
estimated_amount: {amount}
---

# Payment Approval Request

## Payment Details
- **Invoice ID**: {invoice_id}
- **Amount**: ${amount:,.2f}
- **Payment Method**: {payment_method}
- **Payment Date**: {payment_date or datetime.now().strftime('%Y-%m-%d')}

## Approval Required
This payment exceeds the auto-approval threshold of ${self.payment_approval_threshold:,.2f}

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.
"""
        
        # Write approval file
        approval_file = vault.paths.pending_approval / f"APPROVAL_PAYMENT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        approval_file.write_text(approval_content)
        
        logger.info(f"Approval request created: {approval_file}")
        
        return {
            "success": False,
            "requires_approval": True,
            "approval_file": str(approval_file),
            "message": f"Payment requires approval (amount ${amount:,.2f} >= threshold ${self.payment_approval_threshold:,.2f})"
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        uptime = datetime.now() - self.start_time
        
        return {
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "uptime_seconds": int(uptime.total_seconds()),
            "statistics": {
                "total_actions": self.total_actions,
                "successful_actions": self.successful_actions,
                "failed_actions": self.failed_actions,
                "success_rate": self.successful_actions / max(1, self.total_actions)
            },
            "approval_thresholds": {
                "payment": self.payment_approval_threshold,
                "invoice": self.invoice_approval_threshold
            },
            "mcp_server": self.mcp_server.get_health_status(),
            "odoo_connected": bool(self.mcp_server.odoo.uid)
        }


# Global Odoo Agent instance
odoo_agent = OdooAgent()
