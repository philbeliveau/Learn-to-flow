#!/usr/bin/env python3
"""
EZBI Analytics - Import Synthetic Data to SQLite Database
Import all generated CSV files into the existing SQLite database
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
import glob

# Database path
DATABASE_PATH = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/data/ezbi_analytics.db"

def create_manufacturing_tables(conn):
    """Create all manufacturing tables in SQLite database"""
    cursor = conn.cursor()
    
    print("🏗️ Creating manufacturing tables...")
    
    # Sales schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_customers (
            customer_id INTEGER PRIMARY KEY,
            company_name TEXT NOT NULL,
            contact_name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            payment_terms INTEGER DEFAULT 30,
            credit_limit REAL DEFAULT 50000.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_invoices (
            invoice_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            invoice_number TEXT UNIQUE NOT NULL,
            date_issued DATE NOT NULL,
            due_date DATE NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'Open',
            payment_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES sales_customers (customer_id)
        )
    ''')
    
    # Accounting schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounting_vendors (
            vendor_id INTEGER PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            contact_name TEXT,
            email TEXT,
            phone TEXT,
            payment_terms INTEGER DEFAULT 30,
            vendor_type TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounting_purchases (
            purchase_id INTEGER PRIMARY KEY,
            vendor_id INTEGER NOT NULL,
            purchase_number TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date_purchased DATE NOT NULL,
            due_date DATE NOT NULL,
            payment_status TEXT DEFAULT 'Outstanding',
            payment_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES accounting_vendors (vendor_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounting_accounts_receivable (
            ar_id INTEGER PRIMARY KEY,
            invoice_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            amount_outstanding REAL NOT NULL,
            days_outstanding INTEGER NOT NULL,
            aging_bucket TEXT NOT NULL,
            as_of_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES sales_invoices (invoice_id),
            FOREIGN KEY (customer_id) REFERENCES sales_customers (customer_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounting_accounts_payable (
            ap_id INTEGER PRIMARY KEY,
            purchase_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            amount_outstanding REAL NOT NULL,
            due_date DATE NOT NULL,
            days_until_due INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_id) REFERENCES accounting_purchases (purchase_id),
            FOREIGN KEY (vendor_id) REFERENCES accounting_vendors (vendor_id)
        )
    ''')
    
    # Operations schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations_products (
            product_id INTEGER PRIMARY KEY,
            product_code TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            base_cost REAL NOT NULL,
            labor_hours REAL NOT NULL,
            material_cost REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations_production_orders (
            order_id INTEGER PRIMARY KEY,
            order_number TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            completion_date DATE,
            expected_completion DATE NOT NULL,
            status TEXT DEFAULT 'In Progress',
            units_ordered INTEGER NOT NULL,
            units_produced INTEGER DEFAULT 0,
            cost_of_goods_sold REAL,
            labor_cost REAL,
            material_cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES operations_products (product_id),
            FOREIGN KEY (customer_id) REFERENCES sales_customers (customer_id)
        )
    ''')
    
    # Finance schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance_cash_ledger (
            transaction_id INTEGER PRIMARY KEY,
            transaction_number TEXT UNIQUE NOT NULL,
            date_recorded DATE NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            counterparty TEXT,
            reference_id INTEGER,
            reference_type TEXT,
            description TEXT,
            running_balance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance_debt_accounts (
            loan_id INTEGER PRIMARY KEY,
            loan_number TEXT UNIQUE NOT NULL,
            loan_type TEXT NOT NULL,
            principal_amount REAL NOT NULL,
            outstanding_amount REAL NOT NULL,
            interest_rate REAL NOT NULL,
            monthly_payment REAL,
            last_payment_date DATE,
            next_due_date DATE,
            loan_start_date DATE NOT NULL,
            loan_end_date DATE,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # Expenses schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses_fixed_costs (
            expense_id INTEGER PRIMARY KEY,
            expense_name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL,
            due_day INTEGER,
            last_paid_date DATE,
            next_due_date DATE,
            vendor_id INTEGER,
            auto_pay BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (vendor_id) REFERENCES accounting_vendors (vendor_id)
        )
    ''')
    
    # HR schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hr_employees (
            employee_id INTEGER PRIMARY KEY,
            employee_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            hire_date DATE NOT NULL,
            annual_salary REAL NOT NULL,
            pay_frequency TEXT DEFAULT 'Bi-weekly',
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hr_payroll_log (
            payroll_id INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            pay_period_start DATE NOT NULL,
            pay_period_end DATE NOT NULL,
            pay_date DATE NOT NULL,
            gross_pay REAL NOT NULL,
            deductions REAL DEFAULT 0.00,
            net_pay REAL NOT NULL,
            bonus REAL DEFAULT 0.00,
            overtime_hours REAL DEFAULT 0.00,
            overtime_pay REAL DEFAULT 0.00,
            FOREIGN KEY (employee_id) REFERENCES hr_employees (employee_id)
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_customer ON sales_invoices(customer_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_status ON sales_invoices(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_production_status ON operations_production_orders(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_ledger_date ON finance_cash_ledger(date_recorded)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_ledger_type ON finance_cash_ledger(transaction_type)')
    
    conn.commit()
    print("✅ All manufacturing tables created successfully")

def import_csv_to_table(conn, csv_file, table_name, mapping=None):
    """Import CSV data into SQLite table"""
    if not os.path.exists(csv_file):
        print(f"⚠️  CSV file not found: {csv_file}")
        return 0
    
    df = pd.read_csv(csv_file)
    
    # Apply column mapping if provided
    if mapping:
        df = df.rename(columns=mapping)
    
    # Import data
    try:
        records_imported = df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"✅ Imported {len(df)} records into {table_name}")
        return len(df)
    except Exception as e:
        print(f"❌ Error importing {csv_file}: {e}")
        return 0

def main():
    """Main function to import all synthetic data"""
    print("🚀 EZBI Analytics - Importing Synthetic Data to SQLite Database")
    print("=" * 65)
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found: {DATABASE_PATH}")
        return
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # Create all manufacturing tables
        create_manufacturing_tables(conn)
        
        # Import all CSV files
        total_records = 0
        
        # CSV files directory
        csv_dir = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/backend/data/"
        
        # Sales data
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_customers.csv", "sales_customers")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_invoices.csv", "sales_invoices")
        
        # Accounting data
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_vendors.csv", "accounting_vendors")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_purchases.csv", "accounting_purchases")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_accounts_receivable.csv", "accounting_accounts_receivable")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_accounts_payable.csv", "accounting_accounts_payable")
        
        # Operations data
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_products.csv", "operations_products")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_production_orders.csv", "operations_production_orders")
        
        # Finance data
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_cash_ledger.csv", "finance_cash_ledger")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_debt_accounts.csv", "finance_debt_accounts")
        
        # Expenses data
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_fixed_costs.csv", "expenses_fixed_costs")
        
        # HR data
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_employees.csv", "hr_employees")
        total_records += import_csv_to_table(conn, f"{csv_dir}synthetic_payroll_log.csv", "hr_payroll_log")
        
        # Verify import
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_customers' OR name LIKE '%_invoices' OR name LIKE '%_vendors' OR name LIKE '%_products' OR name LIKE '%_employees' OR name LIKE '%_cash_ledger' OR name LIKE '%_production_orders' OR name LIKE '%_payroll_log' OR name LIKE '%_accounts_%' OR name LIKE '%_purchases' OR name LIKE '%_debt_accounts' OR name LIKE '%_fixed_costs'")
        
        tables = cursor.fetchall()
        
        print(f"\n📊 Import Summary:")
        print(f"✅ Total records imported: {total_records}")
        print(f"✅ Manufacturing tables created: {len(tables)}")
        
        print(f"\n📋 Manufacturing Tables in Database:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table[0]}: {count} records")
        
        # Show sample data from key tables
        print(f"\n🔍 Sample Data Verification:")
        
        # Sample customers
        cursor.execute("SELECT company_name, contact_name FROM sales_customers LIMIT 3")
        customers = cursor.fetchall()
        if customers:
            print(f"   👥 Sample Customers:")
            for customer in customers:
                print(f"      • {customer[0]} - {customer[1]}")
        
        # Sample invoices with amounts
        cursor.execute("SELECT invoice_number, amount, status FROM sales_invoices LIMIT 3")
        invoices = cursor.fetchall()
        if invoices:
            print(f"   📄 Sample Invoices:")
            for invoice in invoices:
                print(f"      • {invoice[0]}: €{invoice[1]:,.2f} ({invoice[2]})")
        
        # Sample cash ledger
        cursor.execute("SELECT transaction_type, amount, counterparty FROM finance_cash_ledger LIMIT 3")
        transactions = cursor.fetchall()
        if transactions:
            print(f"   💰 Sample Cash Transactions:")
            for tx in transactions:
                print(f"      • {tx[0]}: €{tx[1]:,.2f} - {tx[2]}")
        
        print(f"\n🎉 All synthetic data successfully imported to SQLite database!")
        print(f"📁 Database location: {DATABASE_PATH}")
        print(f"🔗 Platform can now access comprehensive manufacturing data")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()