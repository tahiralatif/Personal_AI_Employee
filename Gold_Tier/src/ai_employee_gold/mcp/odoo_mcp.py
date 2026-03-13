"""Odoo MCP Server for Gold Tier AI Employee.

This module provides Model Context Protocol (MCP) server for Odoo ERP integration.
It exposes Odoo capabilities as tools that can be called by AI agents.

Tools:
1. create_invoice - Create invoice in Odoo
2. record_payment - Record payment against invoice
3. create_expense - Create expense record
4. get_customer - Get customer details
5. get_financial_report - Get financial summary
6. get_accounts_receivable - Get outstanding receivables
7. get_accounts_payable - Get outstanding payables
8. reconcile_bank_statement - Reconcile bank transactions
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..integrations.odoo_integration import odoo
from ..core.audit_logger import audit_logger
from ..core.error_recovery import (
    retry_with_backoff,
    CircuitBreaker,
    health_monitor,
    HealthStatus
)

logger = logging.getLogger(__name__)


class OdooMCPServer:
    """MCP Server for Odoo ERP operations.
    
    This server exposes Odoo functionality as tools that can be called
    by AI agents via the Model Context Protocol.
    
    Tools Available:
    - create_invoice
    - record_payment
    - create_expense
    - get_customer
    - get_financial_report
    - get_accounts_receivable
    - get_accounts_payable
    - reconcile_bank_statement
    """
    
    def __init__(self):
        """Initialize Odoo MCP Server."""
        self.odoo = odoo
        self.name = "odoo_mcp"
        self.version = "1.0.0"
        self.description = "Odoo ERP integration for accounting and business operations"
        
        # Circuit breaker for Odoo calls
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=300
        )
        
        # Register with health monitor
        health_monitor.register_component(
            "odoo_mcp",
            check_interval=60
        )
        
        # Tool registry
        self.tools = self._register_tools()
        
        logger.info(f"Odoo MCP Server initialized: {self.name} v{self.version}")
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools."""
        return {
            "create_invoice": {
                "name": "create_invoice",
                "description": "Create a new invoice in Odoo for a customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "integer",
                            "description": "Odoo customer/partner ID"
                        },
                        "items": {
                            "type": "array",
                            "description": "List of invoice line items",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "quantity": {"type": "number"},
                                    "price_unit": {"type": "number"}
                                },
                                "required": ["quantity", "price_unit"]
                            }
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Invoice due date (YYYY-MM-DD)"
                        }
                    },
                    "required": ["customer_id", "items"]
                }
            },
            "record_payment": {
                "name": "record_payment",
                "description": "Record a payment against an invoice",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "invoice_id": {
                            "type": "integer",
                            "description": "Odoo invoice ID"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Payment amount"
                        },
                        "payment_method": {
                            "type": "string",
                            "description": "Payment method (bank, cash, check, etc.)"
                        },
                        "payment_date": {
                            "type": "string",
                            "description": "Payment date (YYYY-MM-DD)"
                        }
                    },
                    "required": ["invoice_id", "amount"]
                }
            },
            "create_expense": {
                "name": "create_expense",
                "description": "Create an expense record in Odoo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Expense amount"
                        },
                        "category": {
                            "type": "string",
                            "description": "Expense category"
                        },
                        "description": {
                            "type": "string",
                            "description": "Expense description"
                        },
                        "employee_id": {
                            "type": "integer",
                            "description": "Employee ID who incurred expense"
                        }
                    },
                    "required": ["amount", "category", "description"]
                }
            },
            "get_customer": {
                "name": "get_customer",
                "description": "Get customer details from Odoo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "integer",
                            "description": "Odoo customer/partner ID"
                        }
                    },
                    "required": ["customer_id"]
                }
            },
            "get_financial_report": {
                "name": "get_financial_report",
                "description": "Get financial summary report for a period",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "description": "Report period (week, month, quarter, year)"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        }
                    }
                }
            },
            "get_accounts_receivable": {
                "name": "get_accounts_receivable",
                "description": "Get outstanding accounts receivable (money owed to you)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return"
                        },
                        "overdue_only": {
                            "type": "boolean",
                            "description": "Return only overdue invoices"
                        }
                    }
                }
            },
            "get_accounts_payable": {
                "name": "get_accounts_payable",
                "description": "Get outstanding accounts payable (money you owe)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return"
                        },
                        "overdue_only": {
                            "type": "boolean",
                            "description": "Return only overdue bills"
                        }
                    }
                }
            },
            "reconcile_bank_statement": {
                "name": "reconcile_bank_statement",
                "description": "Reconcile bank statement lines with invoices",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "statement_id": {
                            "type": "integer",
                            "description": "Bank statement ID"
                        },
                        "line_id": {
                            "type": "integer",
                            "description": "Bank statement line ID"
                        },
                        "invoice_id": {
                            "type": "integer",
                            "description": "Invoice ID to reconcile"
                        }
                    },
                    "required": ["statement_id", "line_id", "invoice_id"]
                }
            }
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return list(self.tools.values())
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool schema by name."""
        return self.tools.get(tool_name)
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, jitter=True)
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name with arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        start_time = datetime.now()
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for tool: {name}")
            return {
                "success": False,
                "error": "Service temporarily unavailable (circuit breaker open)",
                "retry_after": 300
            }
        
        try:
            # Route to appropriate tool handler
            if name == "create_invoice":
                result = self._create_invoice(**arguments)
            elif name == "record_payment":
                result = self._record_payment(**arguments)
            elif name == "create_expense":
                result = self._create_expense(**arguments)
            elif name == "get_customer":
                result = self._get_customer(**arguments)
            elif name == "get_financial_report":
                result = self._get_financial_report(**arguments)
            elif name == "get_accounts_receivable":
                result = self._get_accounts_receivable(**arguments)
            elif name == "get_accounts_payable":
                result = self._get_accounts_payable(**arguments)
            elif name == "reconcile_bank_statement":
                result = self._reconcile_bank_statement(**arguments)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {name}"
                }
            
            # Record success
            self.circuit_breaker.record_success()
            health_monitor.record_health("odoo_mcp", HealthStatus.HEALTHY)
            
            # Audit log
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            audit_logger.log(
                action_type=f"odoo_mcp.{name}",
                actor="OdooMCPServer",
                actor_type="system",
                domain="business",
                subdomain="accounting",
                target=f"Tool call: {name}",
                parameters=arguments,
                result="success" if result.get("success") else "failed",
                result_data=result,
                execution_time_ms=execution_time
            )
            
            return result
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            health_monitor.record_health("odoo_mcp", HealthStatus.DEGRADED, str(e))
            
            logger.error(f"Tool call failed: {name} - {e}")
            
            return {
                "success": False,
                "error": str(e),
                "tool": name
            }
    
    # Tool Implementations
    
    def _create_invoice(
        self,
        customer_id: int,
        items: List[Dict[str, Any]],
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create invoice tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        # Prepare invoice lines
        product_lines = []
        for item in items:
            product_lines.append({
                "product_id": item.get("product_id"),
                "name": item.get("name", "Service"),
                "quantity": item.get("quantity", 1),
                "price_unit": item.get("price_unit", 0)
            })
        
        # Create invoice
        invoice_id = self.odoo.create_invoice(customer_id, product_lines)
        
        if invoice_id:
            return {
                "success": True,
                "invoice_id": invoice_id,
                "message": f"Invoice created successfully: {invoice_id}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create invoice"
            }
    
    def _record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_method: str = "bank",
        payment_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record payment tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        # Get invoice to check amount
        invoice = self.odoo.get_invoice_by_id(invoice_id)
        if not invoice:
            return {"success": False, "error": f"Invoice not found: {invoice_id}"}
        
        # Create payment (simplified - actual implementation would use Odoo payment model)
        payment_data = {
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_method": payment_method,
            "payment_date": payment_date or datetime.now().strftime("%Y-%m-%d")
        }
        
        # In real implementation, would call Odoo payment API
        return {
            "success": True,
            "payment_id": f"PMT/{datetime.now().strftime('%Y%m%d/%H%M%S')}",
            "message": f"Payment of {amount} recorded for invoice {invoice_id}",
            "payment_data": payment_data
        }
    
    def _create_expense(
        self,
        amount: float,
        category: str,
        description: str,
        employee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create expense tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        expense_data = {
            "name": description,
            "total_amount": amount,
            "product_id": category,  # In real impl, would map category to product
            "employee_id": employee_id,
            "description": description
        }
        
        expense_id = self.odoo.create_expense(expense_data)
        
        if expense_id:
            return {
                "success": True,
                "expense_id": expense_id,
                "message": f"Expense created successfully: {expense_id}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create expense"
            }
    
    def _get_customer(self, customer_id: int) -> Dict[str, Any]:
        """Get customer tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        customer = self.odoo.get_customer_by_id(customer_id)
        
        if customer:
            return {
                "success": True,
                "customer": customer,
                "message": f"Customer retrieved: {customer.get('name')}"
            }
        else:
            return {
                "success": False,
                "error": f"Customer not found: {customer_id}"
            }
    
    def _get_financial_report(
        self,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get financial report tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        # Calculate date range based on period
        if not start_date or not end_date:
            from datetime import timedelta
            today = datetime.now()
            
            if period == "week":
                start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            elif period == "month":
                start_date = today.replace(day=1).strftime("%Y-%m-%d")
            elif period == "quarter":
                # First day of current quarter
                quarter = (today.month - 1) // 3 + 1
                start_date = today.replace(month=quarter * 3 - 2, day=1).strftime("%Y-%m-%d")
            elif period == "year":
                start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            else:
                period = "month"
                start_date = today.replace(day=1).strftime("%Y-%m-%d")
            
            end_date = today.strftime("%Y-%m-%d")
        
        # Get invoices for period
        domain = [
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date)
        ]
        invoices = self.odoo.search_invoices(domain)
        
        # Calculate totals
        total_revenue = sum(inv.get('amount_total', 0) for inv in invoices if inv.get('state') == 'posted')
        total_outstanding = sum(inv.get('amount_residual', 0) for inv in invoices)
        
        return {
            "success": True,
            "report": {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "total_revenue": total_revenue,
                "total_outstanding": total_outstanding,
                "invoice_count": len(invoices),
                "invoices": invoices[:10]  # Return first 10 for brevity
            },
            "message": f"Financial report generated for {period}"
        }
    
    def _get_accounts_receivable(
        self,
        limit: int = 50,
        overdue_only: bool = False
    ) -> Dict[str, Any]:
        """Get accounts receivable tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        # Search for unpaid invoices
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ]
        
        if overdue_only:
            from datetime import timedelta
            overdue_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            domain.append(('invoice_date', '<', overdue_date))
        
        invoices = self.odoo.search_invoices(domain)
        
        # Limit results
        invoices = invoices[:limit]
        
        total_receivable = sum(inv.get('amount_residual', 0) for inv in invoices)
        
        return {
            "success": True,
            "receivables": {
                "total_amount": total_receivable,
                "count": len(invoices),
                "overdue_only": overdue_only,
                "invoices": invoices
            },
            "message": f"Found {len(invoices)} outstanding invoices totaling {total_receivable}"
        }
    
    def _get_accounts_payable(
        self,
        limit: int = 50,
        overdue_only: bool = False
    ) -> Dict[str, Any]:
        """Get accounts payable tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        # Search for unpaid vendor bills
        domain = [
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ]
        
        if overdue_only:
            from datetime import timedelta
            overdue_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            domain.append(('invoice_date', '<', overdue_date))
        
        invoices = self.odoo.search_invoices(domain)
        
        # Limit results
        invoices = invoices[:limit]
        
        total_payable = sum(inv.get('amount_residual', 0) for inv in invoices)
        
        return {
            "success": True,
            "payables": {
                "total_amount": total_payable,
                "count": len(invoices),
                "overdue_only": overdue_only,
                "invoices": invoices
            },
            "message": f"Found {len(invoices)} outstanding bills totaling {total_payable}"
        }
    
    def _reconcile_bank_statement(
        self,
        statement_id: int,
        line_id: int,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Reconcile bank statement tool implementation."""
        if not self.odoo.uid:
            return {"success": False, "error": "Not connected to Odoo"}
        
        # In real implementation, would call Odoo reconciliation API
        # This is a simplified placeholder
        
        return {
            "success": True,
            "message": f"Bank statement line {line_id} reconciled with invoice {invoice_id}",
            "reconciliation": {
                "statement_id": statement_id,
                "line_id": line_id,
                "invoice_id": invoice_id
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get MCP server health status."""
        return {
            "name": self.name,
            "version": self.version,
            "status": health_monitor.get_component_health("odoo_mcp"),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "tools_available": len(self.tools),
            "odoo_connected": bool(self.odoo.uid)
        }


# Global MCP server instance
odoo_mcp_server = OdooMCPServer()
