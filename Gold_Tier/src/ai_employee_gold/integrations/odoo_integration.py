"""Odoo integration module for Gold Tier AI Employee system."""
import xmlrpc.client
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from ..config.settings import settings


class OdooIntegration:
    """Integration with Odoo ERP system using JSON-RPC APIs."""

    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USERNAME
        self.password = settings.ODOO_PASSWORD
        self.api_key = settings.ODOO_API_KEY
        self.common = None
        self.models = None
        self.uid = None
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.url and self.db and self.username and self.password:
            self.connect()

    def connect(self) -> bool:
        """Connect to Odoo instance."""
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            if self.uid:
                self.logger.info("Successfully connected to Odoo")
                return True
            else:
                self.logger.error("Failed to authenticate with Odoo")
                return False
        except Exception as e:
            self.logger.error(f"Error connecting to Odoo: {e}")
            return False

    def create_invoice(self, partner_id: int, product_lines: List[Dict[str, Any]]) -> Optional[int]:
        """Create an invoice in Odoo."""
        try:
            # Create invoice
            invoice_vals = {
                'partner_id': partner_id,
                'move_type': 'out_invoice',
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            }

            invoice_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'create',
                [invoice_vals]
            )

            # Add invoice lines
            for line in product_lines:
                line_vals = {
                    'move_id': invoice_id,
                    'product_id': line['product_id'],
                    'quantity': line['quantity'],
                    'price_unit': line['price_unit'],
                }
                self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'account.move.line', 'create',
                    [line_vals]
                )

            self.logger.info(f"Invoice created successfully: {invoice_id}")
            return invoice_id
        except Exception as e:
            self.logger.error(f"Error creating invoice: {e}")
            return None

    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """Create a customer in Odoo."""
        try:
            partner_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'create',
                [customer_data]
            )
            self.logger.info(f"Customer created successfully: {partner_id}")
            return partner_id
        except Exception as e:
            self.logger.error(f"Error creating customer: {e}")
            return None

    def search_customers(self, domain: List[List[Any]]) -> List[Dict[str, Any]]:
        """Search for customers in Odoo."""
        try:
            customer_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'search',
                [domain]
            )
            customers = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'read',
                [customer_ids, ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id']]
            )
            return customers
        except Exception as e:
            self.logger.error(f"Error searching customers: {e}")
            return []

    def create_sale_order(self, order_data: Dict[str, Any]) -> Optional[int]:
        """Create a sale order in Odoo."""
        try:
            order_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'sale.order', 'create',
                [order_data]
            )
            self.logger.info(f"Sale order created successfully: {order_id}")
            return order_id
        except Exception as e:
            self.logger.error(f"Error creating sale order: {e}")
            return None

    def create_expense(self, expense_data: Dict[str, Any]) -> Optional[int]:
        """Create an expense in Odoo."""
        try:
            expense_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'hr.expense', 'create',
                [expense_data]
            )
            self.logger.info(f"Expense created successfully: {expense_id}")
            return expense_id
        except Exception as e:
            self.logger.error(f"Error creating expense: {e}")
            return None

    def get_account_balance(self, account_id: int) -> Optional[float]:
        """Get account balance in Odoo."""
        try:
            account = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.account', 'read',
                [[account_id], ['balance']]
            )
            if account:
                return account[0]['balance']
            return None
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            return None

    def create_purchase_order(self, order_data: Dict[str, Any]) -> Optional[int]:
        """Create a purchase order in Odoo."""
        try:
            order_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'purchase.order', 'create',
                [order_data]
            )
            self.logger.info(f"Purchase order created successfully: {order_id}")
            return order_id
        except Exception as e:
            self.logger.error(f"Error creating purchase order: {e}")
            return None

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice details by ID."""
        try:
            invoices = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'read',
                [[invoice_id], ['id', 'name', 'state', 'amount_total', 'partner_id', 'invoice_date']]
            )
            return invoices[0] if invoices else None
        except Exception as e:
            self.logger.error(f"Error getting invoice: {e}")
            return None

    def search_invoices(self, domain: List[List[Any]]) -> List[Dict[str, Any]]:
        """Search for invoices in Odoo."""
        try:
            invoice_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'search',
                [domain]
            )
            invoices = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'read',
                [invoice_ids, ['id', 'name', 'state', 'amount_total', 'partner_id', 'invoice_date']]
            )
            return invoices
        except Exception as e:
            self.logger.error(f"Error searching invoices: {e}")
            return []

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Get customer details by ID."""
        try:
            customers = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'read',
                [[customer_id], ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id']]
            )
            return customers[0] if customers else None
        except Exception as e:
            self.logger.error(f"Error getting customer: {e}")
            return None


# Global Odoo instance
odoo = OdooIntegration()