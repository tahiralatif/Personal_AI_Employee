"""
Tests for Odoo Integration (MCP Server and Agent).

Covers:
- Odoo MCP Server tools
- Odoo Agent skills
- Accounting Watcher
- Approval workflow
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_employee_gold.mcp.odoo_mcp import OdooMCPServer
from ai_employee_gold.agents.odoo_agent import OdooAgent


class TestOdooMCPServer:
    """Test Odoo MCP Server."""
    
    @pytest.fixture
    def mock_odoo(self):
        """Create mock Odoo integration."""
        mock = Mock()
        mock.uid = 1
        mock.db = "test_db"
        mock.username = "admin"
        mock.password = "admin"
        return mock
    
    @pytest.fixture
    def mcp_server(self, mock_odoo):
        """Create MCP server with mock Odoo."""
        with patch('ai_employee_gold.mcp.odoo_mcp.odoo', mock_odoo):
            server = OdooMCPServer()
            return server
    
    def test_server_initialization(self, mcp_server):
        """Test MCP server initialization."""
        assert mcp_server.name == "odoo_mcp"
        assert mcp_server.version == "1.0.0"
        assert len(mcp_server.tools) == 8
    
    def test_get_tools(self, mcp_server):
        """Test getting available tools."""
        tools = mcp_server.get_tools()
        
        assert len(tools) == 8
        
        tool_names = [t['name'] for t in tools]
        assert 'create_invoice' in tool_names
        assert 'record_payment' in tool_names
        assert 'create_expense' in tool_names
        assert 'get_customer' in tool_names
        assert 'get_financial_report' in tool_names
        assert 'get_accounts_receivable' in tool_names
        assert 'get_accounts_payable' in tool_names
        assert 'reconcile_bank_statement' in tool_names
    
    def test_get_tool_schema(self, mcp_server):
        """Test getting tool schema."""
        schema = mcp_server.get_tool_schema("create_invoice")
        
        assert schema is not None
        assert schema['name'] == "create_invoice"
        assert 'inputSchema' in schema
    
    def test_call_create_invoice(self, mcp_server, mock_odoo):
        """Test calling create_invoice tool."""
        mock_odoo.create_invoice.return_value = 123
        
        result = mcp_server.call_tool("create_invoice", {
            "customer_id": 456,
            "items": [
                {"name": "Service", "quantity": 1, "price_unit": 100}
            ]
        })
        
        assert result["success"] is True
        assert result["invoice_id"] == 123
        mock_odoo.create_invoice.assert_called_once()
    
    def test_call_record_payment(self, mcp_server, mock_odoo):
        """Test calling record_payment tool."""
        mock_odoo.get_invoice_by_id.return_value = {"id": 123, "amount_total": 500}
        
        result = mcp_server.call_tool("record_payment", {
            "invoice_id": 123,
            "amount": 500,
            "payment_method": "bank"
        })
        
        assert result["success"] is True
        assert "payment_id" in result
    
    def test_call_create_expense(self, mcp_server, mock_odoo):
        """Test calling create_expense tool."""
        mock_odoo.create_expense.return_value = 789
        
        result = mcp_server.call_tool("create_expense", {
            "amount": 250,
            "category": "Office Supplies",
            "description": "Printer paper"
        })
        
        assert result["success"] is True
        assert result["expense_id"] == 789
    
    def test_call_get_customer(self, mcp_server, mock_odoo):
        """Test calling get_customer tool."""
        mock_odoo.get_customer_by_id.return_value = {
            "id": 123,
            "name": "Test Customer",
            "email": "test@example.com"
        }
        
        result = mcp_server.call_tool("get_customer", {"customer_id": 123})
        
        assert result["success"] is True
        assert result["customer"]["name"] == "Test Customer"
    
    def test_call_get_financial_report(self, mcp_server, mock_odoo):
        """Test calling get_financial_report tool."""
        mock_odoo.search_invoices.return_value = [
            {"id": 1, "amount_total": 1000, "state": "posted"},
            {"id": 2, "amount_total": 500, "state": "posted"}
        ]
        
        result = mcp_server.call_tool("get_financial_report", {"period": "month"})
        
        assert result["success"] is True
        assert "report" in result
        assert result["report"]["invoice_count"] == 2
    
    def test_call_get_accounts_receivable(self, mcp_server, mock_odoo):
        """Test calling get_accounts_receivable tool."""
        mock_odoo.search_invoices.return_value = [
            {"id": 1, "amount_residual": 1000, "payment_state": "not_paid"}
        ]
        
        result = mcp_server.call_tool("get_accounts_receivable", {"limit": 10})
        
        assert result["success"] is True
        assert result["receivables"]["count"] == 1
    
    def test_call_get_accounts_payable(self, mcp_server, mock_odoo):
        """Test calling get_accounts_payable tool."""
        mock_odoo.search_invoices.return_value = [
            {"id": 1, "amount_residual": 500, "payment_state": "not_paid"}
        ]
        
        result = mcp_server.call_tool("get_accounts_payable", {"limit": 10})
        
        assert result["success"] is True
        assert result["payables"]["count"] == 1
    
    def test_call_unknown_tool(self, mcp_server):
        """Test calling unknown tool."""
        result = mcp_server.call_tool("unknown_tool", {})
        
        assert result["success"] is False
        assert "Unknown tool" in result["error"]
    
    def test_call_tool_not_connected(self):
        """Test calling tool when not connected to Odoo."""
        mock_odoo = Mock()
        mock_odoo.uid = None
        
        with patch('ai_employee_gold.mcp.odoo_mcp.odoo', mock_odoo):
            server = OdooMCPServer()
            result = server.call_tool("create_invoice", {
                "customer_id": 123,
                "items": []
            })
            
            assert result["success"] is False
            assert "Not connected" in result["error"]
    
    def test_get_health_status(self, mcp_server):
        """Test getting health status."""
        status = mcp_server.get_health_status()
        
        assert "name" in status
        assert "version" in status
        assert "circuit_breaker" in status
        assert "tools_available" in status


class TestOdooAgent:
    """Test Odoo Agent skills."""
    
    @pytest.fixture
    def mock_mcp_server(self):
        """Create mock MCP server."""
        mock = Mock()
        mock.call_tool.return_value = {"success": True, "invoice_id": 123}
        return mock
    
    @pytest.fixture
    def odoo_agent(self, mock_mcp_server):
        """Create agent with mock MCP server."""
        with patch('ai_employee_gold.agents.odoo_agent.odoo_mcp_server', mock_mcp_server):
            agent = OdooAgent()
            agent.mcp_server = mock_mcp_server
            return agent
    
    def test_agent_initialization(self, odoo_agent):
        """Test agent initialization."""
        assert odoo_agent.name == "OdooAgent"
        assert odoo_agent.version == "1.0.0"
        assert odoo_agent.domain == "business"
        assert odoo_agent.subdomain == "accounting"
    
    def test_create_invoice_skill(self, odoo_agent, mock_mcp_server):
        """Test create_invoice skill."""
        result = odoo_agent.create_invoice(
            customer_id=123,
            items=[{"name": "Service", "quantity": 1, "price_unit": 100}],
            requires_approval=False
        )
        
        assert result["success"] is True
        mock_mcp_server.call_tool.assert_called_once()
    
    def test_create_invoice_requires_approval(self, odoo_agent):
        """Test create_invoice with approval required."""
        # Set low threshold for testing
        odoo_agent.invoice_approval_threshold = 50
        
        result = odoo_agent.create_invoice(
            customer_id=123,
            items=[{"name": "Service", "quantity": 10, "price_unit": 100}],  # Total: 1000
            requires_approval=True
        )
        
        assert result["success"] is False
        assert result["requires_approval"] is True
        assert "approval_file" in result
    
    def test_record_payment_skill(self, odoo_agent, mock_mcp_server):
        """Test record_payment skill."""
        mock_mcp_server.call_tool.return_value = {"success": True, "payment_id": "PMT/123"}
        
        result = odoo_agent.record_payment(
            invoice_id=456,
            amount=500,
            requires_approval=False
        )
        
        assert result["success"] is True
    
    def test_record_payment_requires_approval(self, odoo_agent):
        """Test record_payment with approval required."""
        odoo_agent.payment_approval_threshold = 100
        
        result = odoo_agent.record_payment(
            invoice_id=456,
            amount=500,  # Above threshold
            requires_approval=True
        )
        
        assert result["success"] is False
        assert result["requires_approval"] is True
    
    def test_create_expense_skill(self, odoo_agent, mock_mcp_server):
        """Test create_expense skill."""
        mock_mcp_server.call_tool.return_value = {"success": True, "expense_id": 789}
        
        result = odoo_agent.create_expense(
            amount=250,
            category="Office Supplies",
            description="Printer paper"
        )
        
        assert result["success"] is True
    
    def test_get_financial_summary_skill(self, odoo_agent, mock_mcp_server):
        """Test get_financial_summary skill."""
        mock_mcp_server.call_tool.return_value = {
            "success": True,
            "report": {
                "total_revenue": 10000,
                "total_outstanding": 2000,
                "invoice_count": 15
            }
        }
        
        result = odoo_agent.get_financial_summary(period="month")
        
        assert result["success"] is True
        assert result["revenue"] == 10000
    
    def test_get_outstanding_invoices_skill(self, odoo_agent, mock_mcp_server):
        """Test get_outstanding_invoices skill."""
        mock_mcp_server.call_tool.return_value = {
            "success": True,
            "receivables": {
                "total_amount": 5000,
                "count": 5,
                "invoices": []
            }
        }
        
        result = odoo_agent.get_outstanding_invoices(limit=10)
        
        assert result["success"] is True
        assert result["total_amount"] == 5000
    
    def test_get_customer_details_skill(self, odoo_agent, mock_mcp_server):
        """Test get_customer_details skill."""
        mock_mcp_server.call_tool.return_value = {
            "success": True,
            "customer": {
                "id": 123,
                "name": "Test Customer",
                "email": "test@example.com"
            }
        }
        
        result = odoo_agent.get_customer_details(123)
        
        assert result["success"] is True
        assert result["customer"]["name"] == "Test Customer"
    
    def test_check_accounts_receivable_skill(self, odoo_agent, mock_mcp_server):
        """Test check_accounts_receivable skill."""
        mock_mcp_server.call_tool.return_value = {
            "success": True,
            "receivables": {"total_amount": 3000, "count": 3}
        }
        
        result = odoo_agent.check_accounts_receivable()
        
        assert result["success"] is True
    
    def test_check_accounts_payable_skill(self, odoo_agent, mock_mcp_server):
        """Test check_accounts_payable skill."""
        mock_mcp_server.call_tool.return_value = {
            "success": True,
            "payables": {"total_amount": 1500, "count": 2}
        }
        
        result = odoo_agent.check_accounts_payable()
        
        assert result["success"] is True
    
    def test_get_agent_status(self, odoo_agent):
        """Test getting agent status."""
        odoo_agent.total_actions = 10
        odoo_agent.successful_actions = 8
        odoo_agent.failed_actions = 2
        
        status = odoo_agent.get_agent_status()
        
        assert status["name"] == "OdooAgent"
        assert status["statistics"]["total_actions"] == 10
        assert status["statistics"]["success_rate"] == 0.8


class TestAccountingWatcher:
    """Test Accounting Watcher."""
    
    @pytest.fixture
    def mock_odoo(self):
        """Create mock Odoo integration."""
        mock = Mock()
        mock.uid = 1
        mock.search_invoices.return_value = [
            {
                "id": 123,
                "name": "INV/2026/001",
                "amount_total": 5000,
                "amount_residual": 5000,
                "state": "posted",
                "payment_state": "not_paid",
                "partner_id": [1, "Test Customer"],
                "invoice_date": "2026-02-01"
            }
        ]
        return mock
    
    @pytest.fixture
    def watcher(self, mock_odoo):
        """Create watcher with mock Odoo."""
        with patch('ai_employee_gold.watchers.accounting_watcher.odoo', mock_odoo):
            with patch('ai_employee_gold.watchers.accounting_watcher.BaseWatcher.__init__', return_value=None):
                from ai_employee_gold.watchers.accounting_watcher import AccountingWatcher
                w = AccountingWatcher.__new__(AccountingWatcher)
                w.odoo = mock_odoo
                w.check_interval = 300
                w.enabled = True
                w.domain = "business"
                w.subdomain = "accounting"
                w.overdue_days_threshold = 30
                w.expense_threshold = 2000
                w.last_invoice_check = datetime.now()
                w.last_payment_check = datetime.now()
                w.processed_ids = set()
                return w
    
    def test_check_for_updates(self, watcher, mock_odoo):
        """Test checking for accounting updates."""
        events = watcher.check_for_updates()
        
        assert isinstance(events, list)
    
    def test_check_new_invoices(self, watcher, mock_odoo):
        """Test checking for new invoices."""
        events = watcher._check_new_invoices()
        
        assert len(events) > 0
        assert events[0]["type"] == "invoice_created"
        assert events[0]["invoice_id"] == 123
    
    def test_check_overdue_invoices(self, watcher, mock_odoo):
        """Test checking for overdue invoices."""
        events = watcher._check_overdue_invoices()
        
        assert len(events) > 0
        assert events[0]["type"] == "overdue_invoice"
        assert events[0]["days_overdue"] > 30
    
    def test_create_action_file(self, watcher):
        """Test creating action file."""
        item = {
            "id": "invoice_123",
            "type": "invoice_created",
            "invoice_number": "INV/2026/001",
            "customer_name": "Test Customer",
            "amount": 5000
        }
        
        # Mock vault
        with patch('ai_employee_gold.watchers.accounting_watcher.vault') as mock_vault:
            mock_path = Mock()
            mock_path.__truediv__.return_value = mock_path
            mock_vault.paths.needs_action = mock_path
            
            file_path = watcher.create_action_file(item)
            
            assert file_path is not None
    
    def test_get_health_status(self, watcher):
        """Test getting health status."""
        watcher.health_status = Mock()
        watcher.health_status.value = "healthy"
        watcher.circuit_breaker = Mock()
        watcher.circuit_breaker.get_status.return_value = {"state": "closed"}
        watcher.total_processed = 10
        watcher.total_errors = 1
        watcher.start_time = datetime.now()
        
        status = watcher.get_health_status()
        
        assert "name" in status
        assert "status" in status
        assert "accounting_metrics" in status


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ai_employee_gold.mcp.odoo_mcp", "--cov=ai_employee_gold.agents.odoo_agent", "--cov-report=html"])
