"""
Manufacturing Business Simulator
Generates realistic daily business transactions
"""

import random
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import asyncpg
import logging

from models import SimulationReport

logger = logging.getLogger(__name__)

class ManufacturingSimulator:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.db_connection = None
        
        # Business parameters
        self.daily_invoice_range = (1, 3)
        self.daily_production_range = (0, 2)
        self.daily_purchase_range = (2, 5)
        self.payment_delay_probability = 0.15  # 15% of payments are delayed
        self.overdue_probability = 0.05  # 5% go overdue
        
    async def connect_db(self):
        """Establish database connection"""
        if not self.db_connection:
            self.db_connection = await asyncpg.connect(self.database_url)
        return self.db_connection

    async def run_daily_simulation(self, simulation_date: datetime = None) -> SimulationReport:
        """Run complete daily business simulation"""
        if simulation_date is None:
            simulation_date = datetime.now().date()
            
        logger.info(f"Running simulation for {simulation_date}")
        
        conn = await self.connect_db()
        report = SimulationReport(simulation_date=simulation_date)
        
        try:
            async with conn.transaction():
                # 1. Generate new invoices
                invoices = await self._generate_daily_invoices(conn, simulation_date)
                report.invoices_created = len(invoices)
                
                # 2. Process production orders
                production_orders = await self._generate_production_orders(conn, simulation_date)
                report.production_orders_created = len(production_orders)
                
                # 3. Generate purchases
                purchases = await self._generate_daily_purchases(conn, simulation_date)
                report.purchases_created = len(purchases)
                
                # 4. Process payments (AR)
                payments_received = await self._process_ar_payments(conn, simulation_date)
                report.payments_received = payments_received
                
                # 5. Process vendor payments (AP)
                vendor_payments = await self._process_ap_payments(conn, simulation_date)
                report.vendor_payments_made = vendor_payments
                
                # 6. Process payroll (if payroll day)
                payroll_processed = await self._process_payroll(conn, simulation_date)
                report.payroll_processed = payroll_processed
                
                # 7. Process fixed expenses
                fixed_expenses = await self._process_fixed_expenses(conn, simulation_date)
                report.fixed_expenses_processed = fixed_expenses
                
                # 8. Update aging buckets
                await self._update_ar_aging(conn, simulation_date)
                await self._update_ap_aging(conn, simulation_date)
                
                # 9. Calculate cash position
                report.ending_cash_balance = await self._calculate_cash_position(conn, simulation_date)
                
                # 10. Update running totals
                report.total_transactions = (
                    report.invoices_created + 
                    report.production_orders_created + 
                    report.purchases_created + 
                    report.payments_received + 
                    report.vendor_payments_made
                )
                
                logger.info(f"Simulation complete: {report.total_transactions} transactions")
                return report
                
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
    
    async def _generate_daily_invoices(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Generate 1-3 new customer invoices"""
        num_invoices = random.randint(*self.daily_invoice_range)
        invoices = []
        
        # Get random customers
        customers = await conn.fetch("SELECT customer_id, payment_terms FROM sales.customers ORDER BY RANDOM() LIMIT $1", num_invoices)
        
        for customer in customers:
            # Generate invoice amount (1000-50000)
            amount = Decimal(random.uniform(1000, 50000)).quantize(Decimal('0.01'))
            
            # Calculate due date based on payment terms
            due_date = date + timedelta(days=customer['payment_terms'])
            
            # Generate invoice number
            invoice_number = f"INV-{date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            # Insert invoice
            invoice_id = await conn.fetchval("""
                INSERT INTO sales.invoices 
                (customer_id, invoice_number, date_issued, due_date, amount, status)
                VALUES ($1, $2, $3, $4, $5, 'Open')
                RETURNING invoice_id
            """, customer['customer_id'], invoice_number, date, due_date, amount)
            
            # Create cash ledger entry (for future payment)
            await conn.execute("""
                INSERT INTO finance.cash_ledger 
                (transaction_number, date_recorded, amount, transaction_type, counterparty, reference_id, reference_type, description)
                VALUES ($1, $2, $3, 'Sale', $4, $5, 'invoice', $6)
            """, f"TXN-{invoice_number}", date, amount, f"Customer-{customer['customer_id']}", invoice_id, f"Invoice {invoice_number}")
            
            invoices.append({
                'invoice_id': invoice_id,
                'amount': amount,
                'customer_id': customer['customer_id']
            })
        
        return invoices
    
    async def _generate_production_orders(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Generate 0-2 production orders"""
        num_orders = random.randint(*self.daily_production_range)
        orders = []
        
        if num_orders == 0:
            return orders
        
        # Get random products and customers
        products = await conn.fetch("SELECT product_id, base_cost, labor_hours, material_cost FROM operations.products ORDER BY RANDOM() LIMIT $1", num_orders)
        customers = await conn.fetch("SELECT customer_id FROM sales.customers ORDER BY RANDOM() LIMIT $1", num_orders)
        
        for i, product in enumerate(products):
            customer = customers[i % len(customers)]
            
            # Generate order details
            units = random.randint(5, 50)
            completion_days = random.randint(1, 5)
            expected_completion = date + timedelta(days=completion_days)
            
            # Calculate costs with some variation
            base_cost = product['base_cost']
            labor_cost = Decimal(product['labor_hours']) * Decimal(random.uniform(25, 35))  # $25-35/hour
            material_cost = product['material_cost'] * Decimal(random.uniform(0.9, 1.2))  # ±20% variation
            
            total_cogs = (base_cost + labor_cost + material_cost) * units
            
            order_number = f"PO-{date.strftime('%Y%m%d')}-{random.randint(100, 999)}"
            
            order_id = await conn.fetchval("""
                INSERT INTO operations.production_orders 
                (order_number, product_id, customer_id, start_date, expected_completion, 
                 units_ordered, cost_of_goods_sold, labor_cost, material_cost, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'In Progress')
                RETURNING order_id
            """, order_number, product['product_id'], customer['customer_id'], 
                date, expected_completion, units, total_cogs, labor_cost, material_cost)
            
            orders.append({
                'order_id': order_id,
                'total_cost': total_cogs,
                'units': units
            })
        
        return orders
    
    async def _generate_daily_purchases(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Generate 2-5 vendor purchases"""
        num_purchases = random.randint(*self.daily_purchase_range)
        purchases = []
        
        vendors = await conn.fetch("SELECT vendor_id, vendor_name, payment_terms FROM accounting.vendors ORDER BY RANDOM() LIMIT $1", num_purchases)
        
        categories = ['Raw Materials', 'Tools', 'Maintenance', 'Software', 'Utilities']
        
        for vendor in vendors:
            # Generate purchase amount based on category
            category = random.choice(categories)
            
            if category == 'Raw Materials':
                amount = Decimal(random.uniform(2000, 15000))
            elif category == 'Tools':
                amount = Decimal(random.uniform(500, 5000))
            elif category == 'Maintenance':
                amount = Decimal(random.uniform(800, 3000))
            else:
                amount = Decimal(random.uniform(200, 2000))
            
            amount = amount.quantize(Decimal('0.01'))
            
            due_date = date + timedelta(days=vendor['payment_terms'])
            purchase_number = f"PUR-{date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            purchase_id = await conn.fetchval("""
                INSERT INTO accounting.purchases 
                (vendor_id, purchase_number, category, amount, date_purchased, due_date, payment_status, description)
                VALUES ($1, $2, $3, $4, $5, $6, 'Outstanding', $7)
                RETURNING purchase_id
            """, vendor['vendor_id'], purchase_number, category, amount, date, due_date, f"{category} purchase from {vendor['vendor_name']}")
            
            # Add to accounts payable
            await conn.execute("""
                INSERT INTO accounting.accounts_payable 
                (purchase_id, vendor_id, amount_outstanding, due_date, days_until_due)
                VALUES ($1, $2, $3, $4, $5)
            """, purchase_id, vendor['vendor_id'], amount, due_date, vendor['payment_terms'])
            
            # Create cash ledger entry (outflow when paid)
            await conn.execute("""
                INSERT INTO finance.cash_ledger 
                (transaction_number, date_recorded, amount, transaction_type, counterparty, reference_id, reference_type, description)
                VALUES ($1, $2, $3, 'Purchase', $4, $5, 'purchase', $6)
            """, f"TXN-{purchase_number}", date, -amount, vendor['vendor_name'], purchase_id, f"Purchase {purchase_number}")
            
            purchases.append({
                'purchase_id': purchase_id,
                'amount': amount,
                'vendor_id': vendor['vendor_id']
            })
        
        return purchases
    
    async def _process_ar_payments(self, conn: asyncpg.Connection, date: datetime) -> int:
        """Process customer payments for due invoices"""
        # Get invoices due for payment (some may be early, on-time, or late)
        due_invoices = await conn.fetch("""
            SELECT invoice_id, customer_id, amount, due_date, date_issued
            FROM sales.invoices 
            WHERE status = 'Open' 
            AND due_date <= $1 + INTERVAL '5 days'  -- Include some early payments
            ORDER BY due_date
        """, date)
        
        payments_processed = 0
        
        for invoice in due_invoices:
            # Determine if payment is made (85% chance if due, decreasing probability if overdue)
            days_overdue = (date - invoice['due_date']).days
            
            if days_overdue <= 0:
                payment_probability = 0.85  # 85% chance of on-time payment
            elif days_overdue <= 30:
                payment_probability = 0.70  # 70% chance within 30 days overdue
            else:
                payment_probability = 0.40  # 40% chance if very overdue
            
            if random.random() < payment_probability:
                # Process payment
                await conn.execute("""
                    UPDATE sales.invoices 
                    SET status = 'Paid', payment_date = $1
                    WHERE invoice_id = $2
                """, date, invoice['invoice_id'])
                
                # Update cash ledger (inflow)
                await conn.execute("""
                    INSERT INTO finance.cash_ledger 
                    (transaction_number, date_recorded, amount, transaction_type, counterparty, reference_id, reference_type, description)
                    VALUES ($1, $2, $3, 'Payment Received', $4, $5, 'invoice', $6)
                """, f"PAY-{date.strftime('%Y%m%d')}-{invoice['invoice_id']}", date, invoice['amount'], 
                    f"Customer-{invoice['customer_id']}", invoice['invoice_id'], f"Payment for invoice {invoice['invoice_id']}")
                
                payments_processed += 1
        
        return payments_processed
    
    async def _process_ap_payments(self, conn: asyncpg.Connection, date: datetime) -> int:
        """Process vendor payments"""
        # Get purchases due for payment
        due_purchases = await conn.fetch("""
            SELECT p.purchase_id, p.vendor_id, p.amount, p.due_date, v.vendor_name
            FROM accounting.purchases p
            JOIN accounting.vendors v ON p.vendor_id = v.vendor_id
            WHERE p.payment_status = 'Outstanding' 
            AND p.due_date <= $1
            ORDER BY p.due_date
        """, date)
        
        payments_made = 0
        
        for purchase in due_purchases:
            # 95% chance of paying vendors on time (better than customer payments)
            if random.random() < 0.95:
                # Process payment
                await conn.execute("""
                    UPDATE accounting.purchases 
                    SET payment_status = 'Paid', payment_date = $1
                    WHERE purchase_id = $2
                """, date, purchase['purchase_id'])
                
                # Remove from accounts payable
                await conn.execute("""
                    DELETE FROM accounting.accounts_payable 
                    WHERE purchase_id = $1
                """, purchase['purchase_id'])
                
                # Update cash ledger (outflow)
                await conn.execute("""
                    INSERT INTO finance.cash_ledger 
                    (transaction_number, date_recorded, amount, transaction_type, counterparty, reference_id, reference_type, description)
                    VALUES ($1, $2, $3, 'Vendor Payment', $4, $5, 'purchase', $6)
                """, f"VPAY-{date.strftime('%Y%m%d')}-{purchase['purchase_id']}", date, -purchase['amount'], 
                    purchase['vendor_name'], purchase['purchase_id'], f"Payment to {purchase['vendor_name']}")
                
                payments_made += 1
        
        return payments_made
    
    async def _process_payroll(self, conn: asyncpg.Connection, date: datetime) -> bool:
        """Process bi-weekly payroll if it's a payroll day"""
        # Check if it's a Friday and bi-weekly from a reference date
        if date.weekday() != 4:  # Not Friday
            return False
        
        # Simple bi-weekly check (every other Friday)
        reference_date = datetime(2024, 1, 5).date()  # First Friday of 2024
        days_since_ref = (date - reference_date).days
        
        if days_since_ref % 14 != 0:  # Not a bi-weekly Friday
            return False
        
        # Process payroll for all active employees
        employees = await conn.fetch("""
            SELECT employee_id, first_name, last_name, annual_salary
            FROM hr.employees 
            WHERE status = 'Active'
        """)
        
        pay_period_start = date - timedelta(days=13)
        pay_period_end = date
        
        total_payroll = Decimal('0.00')
        
        for employee in employees:
            # Calculate bi-weekly pay (annual / 26 pay periods)
            gross_pay = Decimal(employee['annual_salary']) / Decimal('26')
            
            # Simple deductions (20% for taxes, benefits, etc.)
            deductions = gross_pay * Decimal('0.20')
            net_pay = gross_pay - deductions
            
            # Occasional overtime (10% chance)
            overtime_hours = Decimal('0.00')
            overtime_pay = Decimal('0.00')
            
            if random.random() < 0.10:
                overtime_hours = Decimal(random.uniform(2, 8))
                overtime_pay = overtime_hours * Decimal('50.00')  # $50/hour overtime
                gross_pay += overtime_pay
                net_pay += overtime_pay
            
            # Insert payroll record
            await conn.execute("""
                INSERT INTO hr.payroll_log 
                (employee_id, pay_period_start, pay_period_end, pay_date, 
                 gross_pay, deductions, net_pay, overtime_hours, overtime_pay)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, employee['employee_id'], pay_period_start, pay_period_end, date,
                gross_pay, deductions, net_pay, overtime_hours, overtime_pay)
            
            total_payroll += net_pay
        
        # Create cash ledger entry for total payroll
        if total_payroll > 0:
            await conn.execute("""
                INSERT INTO finance.cash_ledger 
                (transaction_number, date_recorded, amount, transaction_type, counterparty, description)
                VALUES ($1, $2, $3, 'Payroll', 'Employees', $4)
            """, f"PAYROLL-{date.strftime('%Y%m%d')}", date, -total_payroll, f"Bi-weekly payroll for {len(employees)} employees")
        
        return True
    
    async def _process_fixed_expenses(self, conn: asyncpg.Connection, date: datetime) -> int:
        """Process scheduled fixed expenses"""
        # Get expenses due today
        due_expenses = await conn.fetch("""
            SELECT expense_id, expense_name, amount, vendor_id
            FROM expenses.fixed_costs 
            WHERE next_due_date = $1 AND auto_pay = true
        """, date)
        
        expenses_processed = 0
        
        for expense in due_expenses:
            # Process payment
            await conn.execute("""
                INSERT INTO expenses.expense_log 
                (expense_id, amount_paid, date_paid, payment_method, notes)
                VALUES ($1, $2, $3, 'Auto-Pay', 'Automatic payment processed')
            """, expense['expense_id'], expense['amount'], date)
            
            # Update next due date (monthly for simplicity)
            next_due = date + timedelta(days=30)
            await conn.execute("""
                UPDATE expenses.fixed_costs 
                SET last_paid_date = $1, next_due_date = $2
                WHERE expense_id = $3
            """, date, next_due, expense['expense_id'])
            
            # Create cash ledger entry
            await conn.execute("""
                INSERT INTO finance.cash_ledger 
                (transaction_number, date_recorded, amount, transaction_type, counterparty, description)
                VALUES ($1, $2, $3, 'Fixed Expense', $4, $5)
            """, f"EXP-{date.strftime('%Y%m%d')}-{expense['expense_id']}", date, -expense['amount'], 
                expense['expense_name'], f"Monthly {expense['expense_name']}")
            
            expenses_processed += 1
        
        return expenses_processed
    
    async def _update_ar_aging(self, conn: asyncpg.Connection, date: datetime):
        """Update accounts receivable aging buckets"""
        # Clear existing AR records for today
        await conn.execute("DELETE FROM accounting.accounts_receivable WHERE as_of_date = $1", date)
        
        # Calculate new AR aging
        await conn.execute("""
            INSERT INTO accounting.accounts_receivable 
            (invoice_id, customer_id, amount_outstanding, days_outstanding, aging_bucket, as_of_date)
            SELECT 
                invoice_id,
                customer_id,
                amount,
                $1::date - due_date as days_outstanding,
                CASE 
                    WHEN $1::date - due_date <= 30 THEN '0-30'
                    WHEN $1::date - due_date <= 60 THEN '31-60'
                    WHEN $1::date - due_date <= 90 THEN '61-90'
                    ELSE '90+'
                END as aging_bucket,
                $1::date
            FROM sales.invoices 
            WHERE status = 'Open'
        """, date)
    
    async def _update_ap_aging(self, conn: asyncpg.Connection, date: datetime):
        """Update accounts payable aging"""
        await conn.execute("""
            UPDATE accounting.accounts_payable 
            SET days_until_due = due_date - $1::date
        """, date)
    
    async def _calculate_cash_position(self, conn: asyncpg.Connection, date: datetime) -> Decimal:
        """Calculate ending cash balance"""
        result = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) as balance
            FROM finance.cash_ledger 
            WHERE date_recorded <= $1
        """, date)
        
        return Decimal(result) if result else Decimal('0.00')
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get current data summary for API"""
        conn = await self.connect_db()
        
        summary = {}
        
        # Count records in each table
        tables = [
            ('sales.invoices', 'Total Invoices'),
            ('operations.production_orders', 'Production Orders'),
            ('accounting.purchases', 'Purchases'),
            ('finance.cash_ledger', 'Cash Transactions'),
            ('hr.payroll_log', 'Payroll Records')
        ]
        
        for table, label in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            summary[label.lower().replace(' ', '_')] = count
        
        # Get cash position
        cash_balance = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM finance.cash_ledger
        """)
        summary['current_cash_balance'] = float(cash_balance)
        
        # Get AR summary
        ar_total = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM sales.invoices WHERE status = 'Open'
        """)
        summary['accounts_receivable_total'] = float(ar_total)
        
        return summary