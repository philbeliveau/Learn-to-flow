"""
Database Connection and Utilities
AsyncPG-based database operations for manufacturing simulator
"""

import os
import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.connection: Optional[asyncpg.Connection] = None
        
    async def initialize_pool(self, min_size: int = 5, max_size: int = 20):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60
            )
            logger.info(f"Database pool initialized with {min_size}-{max_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if self.pool:
            async with self.pool.acquire() as conn:
                yield conn
        else:
            # Fallback to single connection
            if not self.connection:
                self.connection = await asyncpg.connect(self.database_url)
            yield self.connection
    
    async def execute_schema_file(self, schema_file_path: str):
        """Execute SQL schema file"""
        try:
            with open(schema_file_path, 'r') as file:
                schema_sql = file.read()
            
            async with self.get_connection() as conn:
                await conn.execute(schema_sql)
            
            logger.info(f"Schema file executed successfully: {schema_file_path}")
        except Exception as e:
            logger.error(f"Failed to execute schema file: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

async def init_database(database_url: str):
    """Initialize database connection"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    await db_manager.initialize_pool()
    return db_manager

async def get_database_connection():
    """Get database connection"""
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return await asyncpg.connect(db_manager.database_url)

async def close_database():
    """Close database connections"""
    if db_manager:
        await db_manager.close_pool()

# ===============================
# DATABASE QUERIES
# ===============================

class DatabaseQueries:
    """Collection of database queries for manufacturing simulator"""
    
    @staticmethod
    async def get_customers(conn: asyncpg.Connection, limit: int = None) -> List[Dict]:
        """Get customers from database"""
        query = "SELECT * FROM sales.customers WHERE 1=1"
        params = []
        
        if limit:
            query += " LIMIT $1"
            params.append(limit)
        
        return await conn.fetch(query, *params)
    
    @staticmethod
    async def get_customer_by_id(conn: asyncpg.Connection, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        query = "SELECT * FROM sales.customers WHERE customer_id = $1"
        return await conn.fetchrow(query, customer_id)
    
    @staticmethod
    async def create_invoice(conn: asyncpg.Connection, invoice_data: Dict) -> int:
        """Create new invoice"""
        query = """
            INSERT INTO sales.invoices 
            (customer_id, invoice_number, date_issued, due_date, amount, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING invoice_id
        """
        return await conn.fetchval(
            query,
            invoice_data['customer_id'],
            invoice_data['invoice_number'],
            invoice_data['date_issued'],
            invoice_data['due_date'],
            invoice_data['amount'],
            invoice_data['status']
        )
    
    @staticmethod
    async def get_open_invoices(conn: asyncpg.Connection, as_of_date: datetime = None) -> List[Dict]:
        """Get open invoices"""
        query = """
            SELECT i.*, c.company_name, c.payment_terms
            FROM sales.invoices i
            JOIN sales.customers c ON i.customer_id = c.customer_id
            WHERE i.status = 'Open'
        """
        params = []
        
        if as_of_date:
            query += " AND i.date_issued <= $1"
            params.append(as_of_date)
        
        query += " ORDER BY i.due_date"
        
        return await conn.fetch(query, *params)
    
    @staticmethod
    async def update_invoice_payment(conn: asyncpg.Connection, invoice_id: int, 
                                   payment_date: datetime, status: str = 'Paid') -> bool:
        """Update invoice payment status"""
        query = """
            UPDATE sales.invoices 
            SET status = $1, payment_date = $2
            WHERE invoice_id = $3
        """
        result = await conn.execute(query, status, payment_date, invoice_id)
        return result == "UPDATE 1"
    
    @staticmethod
    async def get_products(conn: asyncpg.Connection, limit: int = None) -> List[Dict]:
        """Get products from database"""
        query = "SELECT * FROM operations.products"
        params = []
        
        if limit:
            query += " LIMIT $1"
            params.append(limit)
        
        return await conn.fetch(query, *params)
    
    @staticmethod
    async def create_production_order(conn: asyncpg.Connection, order_data: Dict) -> int:
        """Create new production order"""
        query = """
            INSERT INTO operations.production_orders 
            (order_number, product_id, customer_id, start_date, expected_completion, 
             units_ordered, cost_of_goods_sold, labor_cost, material_cost, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING order_id
        """
        return await conn.fetchval(
            query,
            order_data['order_number'],
            order_data['product_id'],
            order_data['customer_id'],
            order_data['start_date'],
            order_data['expected_completion'],
            order_data['units_ordered'],
            order_data['cost_of_goods_sold'],
            order_data['labor_cost'],
            order_data['material_cost'],
            order_data['status']
        )
    
    @staticmethod
    async def get_vendors(conn: asyncpg.Connection, limit: int = None) -> List[Dict]:
        """Get vendors from database"""
        query = "SELECT * FROM accounting.vendors"
        params = []
        
        if limit:
            query += " LIMIT $1"
            params.append(limit)
        
        return await conn.fetch(query, *params)
    
    @staticmethod
    async def create_purchase(conn: asyncpg.Connection, purchase_data: Dict) -> int:
        """Create new purchase"""
        query = """
            INSERT INTO accounting.purchases 
            (vendor_id, purchase_number, category, amount, date_purchased, 
             due_date, payment_status, description)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING purchase_id
        """
        return await conn.fetchval(
            query,
            purchase_data['vendor_id'],
            purchase_data['purchase_number'],
            purchase_data['category'],
            purchase_data['amount'],
            purchase_data['date_purchased'],
            purchase_data['due_date'],
            purchase_data['payment_status'],
            purchase_data['description']
        )
    
    @staticmethod
    async def get_outstanding_purchases(conn: asyncpg.Connection, as_of_date: datetime = None) -> List[Dict]:
        """Get outstanding purchases"""
        query = """
            SELECT p.*, v.vendor_name, v.payment_terms
            FROM accounting.purchases p
            JOIN accounting.vendors v ON p.vendor_id = v.vendor_id
            WHERE p.payment_status = 'Outstanding'
        """
        params = []
        
        if as_of_date:
            query += " AND p.date_purchased <= $1"
            params.append(as_of_date)
        
        query += " ORDER BY p.due_date"
        
        return await conn.fetch(query, *params)
    
    @staticmethod
    async def update_purchase_payment(conn: asyncpg.Connection, purchase_id: int, 
                                    payment_date: datetime, status: str = 'Paid') -> bool:
        """Update purchase payment status"""
        query = """
            UPDATE accounting.purchases 
            SET payment_status = $1, payment_date = $2
            WHERE purchase_id = $3
        """
        result = await conn.execute(query, status, payment_date, purchase_id)
        return result == "UPDATE 1"
    
    @staticmethod
    async def create_cash_transaction(conn: asyncpg.Connection, transaction_data: Dict) -> int:
        """Create cash ledger transaction"""
        query = """
            INSERT INTO finance.cash_ledger 
            (transaction_number, date_recorded, amount, transaction_type, 
             counterparty, reference_id, reference_type, description)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING transaction_id
        """
        return await conn.fetchval(
            query,
            transaction_data['transaction_number'],
            transaction_data['date_recorded'],
            transaction_data['amount'],
            transaction_data['transaction_type'],
            transaction_data.get('counterparty'),
            transaction_data.get('reference_id'),
            transaction_data.get('reference_type'),
            transaction_data.get('description')
        )
    
    @staticmethod
    async def get_cash_balance(conn: asyncpg.Connection, as_of_date: datetime = None) -> float:
        """Get current cash balance"""
        query = "SELECT COALESCE(SUM(amount), 0) FROM finance.cash_ledger"
        params = []
        
        if as_of_date:
            query += " WHERE date_recorded <= $1"
            params.append(as_of_date)
        
        result = await conn.fetchval(query, *params)
        return float(result) if result else 0.0
    
    @staticmethod
    async def get_cash_transactions(conn: asyncpg.Connection, date: datetime = None, 
                                  limit: int = None) -> List[Dict]:
        """Get cash transactions"""
        query = "SELECT * FROM finance.cash_ledger WHERE 1=1"
        params = []
        
        if date:
            query += " AND date_recorded = $1"
            params.append(date)
        
        query += " ORDER BY date_recorded DESC, transaction_id DESC"
        
        if limit:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        
        return await conn.fetch(query, *params)
    
    @staticmethod
    async def get_ar_aging(conn: asyncpg.Connection, as_of_date: datetime) -> List[Dict]:
        """Get AR aging data"""
        query = """
            SELECT ar.*, c.company_name
            FROM accounting.accounts_receivable ar
            JOIN sales.customers c ON ar.customer_id = c.customer_id
            WHERE ar.as_of_date = $1
            ORDER BY ar.aging_bucket, ar.days_outstanding DESC
        """
        return await conn.fetch(query, as_of_date)
    
    @staticmethod
    async def update_ar_aging(conn: asyncpg.Connection, as_of_date: datetime):
        """Update AR aging buckets"""
        # Clear existing AR records for the date
        await conn.execute("DELETE FROM accounting.accounts_receivable WHERE as_of_date = $1", as_of_date)
        
        # Insert new AR aging records
        query = """
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
        """
        await conn.execute(query, as_of_date)
    
    @staticmethod
    async def get_employees(conn: asyncpg.Connection, status: str = 'Active') -> List[Dict]:
        """Get employees"""
        query = "SELECT * FROM hr.employees WHERE status = $1 ORDER BY employee_number"
        return await conn.fetch(query, status)
    
    @staticmethod
    async def create_payroll_record(conn: asyncpg.Connection, payroll_data: Dict) -> int:
        """Create payroll record"""
        query = """
            INSERT INTO hr.payroll_log 
            (employee_id, pay_period_start, pay_period_end, pay_date, 
             gross_pay, deductions, net_pay, overtime_hours, overtime_pay)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING payroll_id
        """
        return await conn.fetchval(
            query,
            payroll_data['employee_id'],
            payroll_data['pay_period_start'],
            payroll_data['pay_period_end'],
            payroll_data['pay_date'],
            payroll_data['gross_pay'],
            payroll_data['deductions'],
            payroll_data['net_pay'],
            payroll_data['overtime_hours'],
            payroll_data['overtime_pay']
        )
    
    @staticmethod
    async def get_fixed_expenses_due(conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Get fixed expenses due on a specific date"""
        query = """
            SELECT * FROM expenses.fixed_costs 
            WHERE next_due_date = $1 AND auto_pay = true
            ORDER BY expense_name
        """
        return await conn.fetch(query, date)
    
    @staticmethod
    async def create_expense_log(conn: asyncpg.Connection, expense_data: Dict) -> int:
        """Create expense log entry"""
        query = """
            INSERT INTO expenses.expense_log 
            (expense_id, amount_paid, date_paid, payment_method, notes)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING log_id
        """
        return await conn.fetchval(
            query,
            expense_data['expense_id'],
            expense_data['amount_paid'],
            expense_data['date_paid'],
            expense_data.get('payment_method'),
            expense_data.get('notes')
        )
    
    @staticmethod
    async def update_fixed_expense_schedule(conn: asyncpg.Connection, expense_id: int, 
                                          last_paid: datetime, next_due: datetime) -> bool:
        """Update fixed expense schedule"""
        query = """
            UPDATE expenses.fixed_costs 
            SET last_paid_date = $1, next_due_date = $2
            WHERE expense_id = $3
        """
        result = await conn.execute(query, last_paid, next_due, expense_id)
        return result == "UPDATE 1"
    
    @staticmethod
    async def get_data_summary(conn: asyncpg.Connection) -> Dict[str, Any]:
        """Get comprehensive data summary"""
        summary = {}
        
        # Count records in each table
        tables = [
            ('sales.invoices', 'total_invoices'),
            ('operations.production_orders', 'total_production_orders'),
            ('accounting.purchases', 'total_purchases'),
            ('finance.cash_ledger', 'total_cash_transactions'),
            ('hr.payroll_log', 'total_payroll_records')
        ]
        
        for table, key in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            summary[key] = count
        
        # Get financial metrics
        summary['current_cash_balance'] = await DatabaseQueries.get_cash_balance(conn)
        
        ar_total = await conn.fetchval("SELECT COALESCE(SUM(amount), 0) FROM sales.invoices WHERE status = 'Open'")
        summary['accounts_receivable_total'] = float(ar_total) if ar_total else 0.0
        
        ap_total = await conn.fetchval("SELECT COALESCE(SUM(amount_outstanding), 0) FROM accounting.accounts_payable")
        summary['accounts_payable_total'] = float(ap_total) if ap_total else 0.0
        
        summary['last_updated'] = datetime.utcnow()
        
        return summary

# ===============================
# UTILITY FUNCTIONS
# ===============================

async def execute_in_transaction(conn: asyncpg.Connection, operations: List[callable]):
    """Execute multiple operations in a transaction"""
    async with conn.transaction():
        results = []
        for operation in operations:
            result = await operation(conn)
            results.append(result)
        return results

async def bulk_insert(conn: asyncpg.Connection, table: str, columns: List[str], data: List[List]):
    """Bulk insert data into a table"""
    if not data:
        return
    
    placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    
    await conn.executemany(query, data)

def format_sql_in_clause(values: List[Any]) -> str:
    """Format values for SQL IN clause"""
    if not values:
        return "NULL"
    
    formatted = []
    for value in values:
        if isinstance(value, str):
            formatted.append(f"'{value}'")
        else:
            formatted.append(str(value))
    
    return ', '.join(formatted)

def build_where_clause(conditions: Dict[str, Any]) -> tuple[str, List[Any]]:
    """Build WHERE clause from conditions dictionary"""
    if not conditions:
        return "1=1", []
    
    clauses = []
    params = []
    param_counter = 1
    
    for key, value in conditions.items():
        if value is None:
            clauses.append(f"{key} IS NULL")
        elif isinstance(value, list):
            if value:
                placeholders = ', '.join([f'${param_counter + i}' for i in range(len(value))])
                clauses.append(f"{key} IN ({placeholders})")
                params.extend(value)
                param_counter += len(value)
        else:
            clauses.append(f"{key} = ${param_counter}")
            params.append(value)
            param_counter += 1
    
    return ' AND '.join(clauses), params