#!/usr/bin/env python3
"""
Simple Railway Database Migration
Sets up manufacturing schema in Railway PostgreSQL
"""
import os
import sys
import asyncio
from pathlib import Path
import asyncpg

# Manufacturing schema SQL
MANUFACTURING_SCHEMA_SQL = """
-- Create schemas
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS accounting;
CREATE SCHEMA IF NOT EXISTS operations;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS expenses;
CREATE SCHEMA IF NOT EXISTS hr;

-- SALES SCHEMA
CREATE TABLE IF NOT EXISTS sales.customers (
    customer_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    payment_terms INTEGER DEFAULT 30,
    credit_limit NUMERIC(12, 2) DEFAULT 50000.00,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales.invoices (
    invoice_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    date_issued DATE NOT NULL,
    due_date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Open',
    payment_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (status IN ('Open', 'Paid', 'Overdue', 'Partial'))
);

-- ACCOUNTING SCHEMA
CREATE TABLE IF NOT EXISTS accounting.vendors (
    vendor_id SERIAL PRIMARY KEY,
    vendor_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    payment_terms INTEGER DEFAULT 30,
    vendor_type VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS accounting.accounts_receivable (
    ar_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES sales.invoices(invoice_id),
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    amount_outstanding NUMERIC(12, 2) NOT NULL,
    days_outstanding INTEGER NOT NULL,
    aging_bucket VARCHAR(20) NOT NULL,
    as_of_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (aging_bucket IN ('0-30', '31-60', '61-90', '90+'))
);

CREATE TABLE IF NOT EXISTS accounting.purchases (
    purchase_id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES accounting.vendors(vendor_id),
    purchase_number VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    date_purchased DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'Outstanding',
    payment_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (payment_status IN ('Outstanding', 'Paid', 'Partial'))
);

CREATE TABLE IF NOT EXISTS accounting.accounts_payable (
    ap_id SERIAL PRIMARY KEY,
    purchase_id INTEGER REFERENCES accounting.purchases(purchase_id),
    vendor_id INTEGER REFERENCES accounting.vendors(vendor_id),
    amount_outstanding NUMERIC(12, 2) NOT NULL,
    due_date DATE NOT NULL,
    days_until_due INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OPERATIONS SCHEMA
CREATE TABLE IF NOT EXISTS operations.products (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    base_cost NUMERIC(10, 2) NOT NULL,
    labor_hours NUMERIC(5, 2) NOT NULL,
    material_cost NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS operations.production_orders (
    order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    product_id INTEGER REFERENCES operations.products(product_id),
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    start_date DATE NOT NULL,
    completion_date DATE,
    expected_completion DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'In Progress',
    units_ordered INTEGER NOT NULL,
    units_produced INTEGER DEFAULT 0,
    cost_of_goods_sold NUMERIC(12, 2),
    labor_cost NUMERIC(10, 2),
    material_cost NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (status IN ('Planned', 'In Progress', 'Completed', 'On Hold'))
);

-- FINANCE SCHEMA
CREATE TABLE IF NOT EXISTS finance.cash_ledger (
    transaction_id SERIAL PRIMARY KEY,
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    date_recorded DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    counterparty VARCHAR(255),
    reference_id INTEGER,
    reference_type VARCHAR(50),
    description TEXT,
    running_balance NUMERIC(15, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS finance.debt_accounts (
    loan_id SERIAL PRIMARY KEY,
    loan_number VARCHAR(50) UNIQUE NOT NULL,
    loan_type VARCHAR(50) NOT NULL,
    principal_amount NUMERIC(15, 2) NOT NULL,
    outstanding_amount NUMERIC(15, 2) NOT NULL,
    interest_rate NUMERIC(5, 4) NOT NULL,
    monthly_payment NUMERIC(10, 2),
    last_payment_date DATE,
    next_due_date DATE,
    loan_start_date DATE NOT NULL,
    loan_end_date DATE,
    status VARCHAR(20) DEFAULT 'Active',
    CHECK (status IN ('Active', 'Paid Off', 'Default'))
);

CREATE TABLE IF NOT EXISTS finance.debt_payments (
    payment_id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES finance.debt_accounts(loan_id),
    payment_date DATE NOT NULL,
    principal_payment NUMERIC(10, 2) NOT NULL,
    interest_payment NUMERIC(10, 2) NOT NULL,
    total_payment NUMERIC(10, 2) NOT NULL,
    remaining_balance NUMERIC(15, 2) NOT NULL
);

-- EXPENSES SCHEMA
CREATE TABLE IF NOT EXISTS expenses.fixed_costs (
    expense_id SERIAL PRIMARY KEY,
    expense_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    due_day INTEGER,
    last_paid_date DATE,
    next_due_date DATE,
    vendor_id INTEGER REFERENCES accounting.vendors(vendor_id),
    auto_pay BOOLEAN DEFAULT FALSE,
    CHECK (frequency IN ('Monthly', 'Quarterly', 'Annual'))
);

CREATE TABLE IF NOT EXISTS expenses.expense_log (
    log_id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses.fixed_costs(expense_id),
    amount_paid NUMERIC(10, 2) NOT NULL,
    date_paid DATE NOT NULL,
    payment_method VARCHAR(50),
    notes TEXT
);

-- HR SCHEMA
CREATE TABLE IF NOT EXISTS hr.employees (
    employee_id SERIAL PRIMARY KEY,
    employee_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    position VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    annual_salary NUMERIC(10, 2) NOT NULL,
    pay_frequency VARCHAR(20) DEFAULT 'Bi-weekly',
    status VARCHAR(20) DEFAULT 'Active',
    CHECK (status IN ('Active', 'Terminated', 'On Leave')),
    CHECK (pay_frequency IN ('Bi-weekly', 'Monthly'))
);

CREATE TABLE IF NOT EXISTS hr.payroll_log (
    payroll_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES hr.employees(employee_id),
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    gross_pay NUMERIC(10, 2) NOT NULL,
    deductions NUMERIC(10, 2) DEFAULT 0.00,
    net_pay NUMERIC(10, 2) NOT NULL,
    bonus NUMERIC(10, 2) DEFAULT 0.00,
    overtime_hours NUMERIC(5, 2) DEFAULT 0.00,
    overtime_pay NUMERIC(8, 2) DEFAULT 0.00
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoices_customer_date ON sales.invoices(customer_id, date_issued);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON sales.invoices(status);
CREATE INDEX IF NOT EXISTS idx_ar_aging ON accounting.accounts_receivable(aging_bucket, as_of_date);
CREATE INDEX IF NOT EXISTS idx_purchases_vendor_date ON accounting.purchases(vendor_id, date_purchased);
CREATE INDEX IF NOT EXISTS idx_production_status ON operations.production_orders(status, start_date);
CREATE INDEX IF NOT EXISTS idx_cash_ledger_date ON finance.cash_ledger(date_recorded);
CREATE INDEX IF NOT EXISTS idx_cash_ledger_type ON finance.cash_ledger(transaction_type);
"""

async def migrate_railway_database():
    """Migrate Railway PostgreSQL database"""
    
    # Get Railway database URL from environment
    database_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    
    if not database_url:
        print("❌ No DATABASE_URL environment variable found")
        print("Please set DATABASE_URL to your Railway PostgreSQL connection string")
        sys.exit(1)
    
    print("🔄 Starting Railway Database Migration...")
    print(f"📊 Database URL: {database_url[:50]}...")
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(database_url)
        
        print("✅ Connected to Railway PostgreSQL")
        
        # Execute schema creation
        print("📋 Creating manufacturing schemas and tables...")
        
        # Split and execute SQL statements
        statements = MANUFACTURING_SCHEMA_SQL.split(';')
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement:
                try:
                    await conn.execute(statement)
                    if i % 10 == 0:
                        print(f"Progress: {i}/{len(statements)} statements executed...")
                except Exception as e:
                    print(f"⚠️ Statement {i} warning: {e}")
                    # Continue execution even if some statements fail (like IF NOT EXISTS)
        
        print("✅ Schema migration completed")
        
        # Verify tables were created
        print("🔍 Verifying table creation...")
        
        tables_query = """
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname IN ('sales', 'accounting', 'operations', 'finance', 'expenses', 'hr')
        ORDER BY schemaname, tablename;
        """
        
        tables = await conn.fetch(tables_query)
        
        print(f"✅ Created {len(tables)} manufacturing tables:")
        for table in tables:
            print(f"  - {table['schemaname']}.{table['tablename']}")
        
        await conn.close()
        print("🎉 Railway database migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(migrate_railway_database())
    sys.exit(0 if success else 1)