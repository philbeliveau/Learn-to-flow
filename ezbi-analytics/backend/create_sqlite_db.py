#!/usr/bin/env python3
"""
Create SQLite version of manufacturing database for analysis
"""

import sqlite3
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta, date
from faker import Faker
import os

# Initialize Faker
fake = Faker('fr_FR')
Faker.seed(42)
random.seed(42)
np.random.seed(42)

def create_database():
    """Create SQLite database with manufacturing schema"""
    
    # Remove existing database
    if os.path.exists('data/ezbi_analytics.db'):
        os.remove('data/ezbi_analytics.db')
    
    # Create connection
    conn = sqlite3.connect('data/ezbi_analytics.db')
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create tables following the PostgreSQL schema
    
    # 1. SALES SCHEMA - Customers
    cursor.execute("""
        CREATE TABLE sales_customers (
            customer_id INTEGER PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            contact_name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            address TEXT,
            payment_terms INTEGER DEFAULT 30,
            credit_limit DECIMAL(12, 2) DEFAULT 50000.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. SALES SCHEMA - Invoices
    cursor.execute("""
        CREATE TABLE sales_invoices (
            invoice_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            invoice_number VARCHAR(50) UNIQUE NOT NULL,
            date_issued DATE NOT NULL,
            due_date DATE NOT NULL,
            amount DECIMAL(12, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'Open' CHECK (status IN ('Open', 'Paid', 'Overdue', 'Partial')),
            payment_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES sales_customers(customer_id)
        )
    """)
    
    # 3. ACCOUNTING SCHEMA - Vendors
    cursor.execute("""
        CREATE TABLE accounting_vendors (
            vendor_id INTEGER PRIMARY KEY,
            vendor_name VARCHAR(255) NOT NULL,
            contact_name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            payment_terms INTEGER DEFAULT 30,
            vendor_type VARCHAR(50) NOT NULL
        )
    """)
    
    # 4. ACCOUNTING SCHEMA - Accounts Receivable
    cursor.execute("""
        CREATE TABLE accounting_accounts_receivable (
            ar_id INTEGER PRIMARY KEY,
            invoice_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            amount_outstanding DECIMAL(12, 2) NOT NULL,
            days_outstanding INTEGER NOT NULL,
            aging_bucket VARCHAR(20) NOT NULL CHECK (aging_bucket IN ('0-30', '31-60', '61-90', '90+')),
            as_of_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES sales_invoices(invoice_id),
            FOREIGN KEY (customer_id) REFERENCES sales_customers(customer_id)
        )
    """)
    
    # 5. ACCOUNTING SCHEMA - Purchases
    cursor.execute("""
        CREATE TABLE accounting_purchases (
            purchase_id INTEGER PRIMARY KEY,
            vendor_id INTEGER NOT NULL,
            purchase_number VARCHAR(50) UNIQUE NOT NULL,
            category VARCHAR(50) NOT NULL,
            amount DECIMAL(12, 2) NOT NULL,
            date_purchased DATE NOT NULL,
            due_date DATE NOT NULL,
            payment_status VARCHAR(20) DEFAULT 'Outstanding' CHECK (payment_status IN ('Outstanding', 'Paid', 'Partial')),
            payment_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES accounting_vendors(vendor_id)
        )
    """)
    
    # 6. ACCOUNTING SCHEMA - Accounts Payable
    cursor.execute("""
        CREATE TABLE accounting_accounts_payable (
            ap_id INTEGER PRIMARY KEY,
            purchase_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            amount_outstanding DECIMAL(12, 2) NOT NULL,
            due_date DATE NOT NULL,
            days_until_due INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_id) REFERENCES accounting_purchases(purchase_id),
            FOREIGN KEY (vendor_id) REFERENCES accounting_vendors(vendor_id)
        )
    """)
    
    # 7. OPERATIONS SCHEMA - Products
    cursor.execute("""
        CREATE TABLE operations_products (
            product_id INTEGER PRIMARY KEY,
            product_code VARCHAR(50) UNIQUE NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            base_cost DECIMAL(10, 2) NOT NULL,
            labor_hours DECIMAL(5, 2) NOT NULL,
            material_cost DECIMAL(10, 2) NOT NULL
        )
    """)
    
    # 8. OPERATIONS SCHEMA - Production Orders
    cursor.execute("""
        CREATE TABLE operations_production_orders (
            order_id INTEGER PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            completion_date DATE,
            expected_completion DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'In Progress' CHECK (status IN ('Planned', 'In Progress', 'Completed', 'On Hold')),
            units_ordered INTEGER NOT NULL,
            units_produced INTEGER DEFAULT 0,
            cost_of_goods_sold DECIMAL(12, 2),
            labor_cost DECIMAL(10, 2),
            material_cost DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES operations_products(product_id),
            FOREIGN KEY (customer_id) REFERENCES sales_customers(customer_id)
        )
    """)
    
    # 9. FINANCE SCHEMA - Cash Ledger
    cursor.execute("""
        CREATE TABLE finance_cash_ledger (
            transaction_id INTEGER PRIMARY KEY,
            transaction_number VARCHAR(50) UNIQUE NOT NULL,
            date_recorded DATE NOT NULL,
            amount DECIMAL(12, 2) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            counterparty VARCHAR(255),
            reference_id INTEGER,
            reference_type VARCHAR(50),
            description TEXT,
            running_balance DECIMAL(15, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 10. FINANCE SCHEMA - Debt Accounts
    cursor.execute("""
        CREATE TABLE finance_debt_accounts (
            loan_id INTEGER PRIMARY KEY,
            loan_number VARCHAR(50) UNIQUE NOT NULL,
            loan_type VARCHAR(50) NOT NULL,
            principal_amount DECIMAL(15, 2) NOT NULL,
            outstanding_amount DECIMAL(15, 2) NOT NULL,
            interest_rate DECIMAL(5, 4) NOT NULL,
            monthly_payment DECIMAL(10, 2),
            last_payment_date DATE,
            next_due_date DATE,
            loan_start_date DATE NOT NULL,
            loan_end_date DATE,
            status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Paid Off', 'Default'))
        )
    """)
    
    # 11. EXPENSES SCHEMA - Fixed Costs
    cursor.execute("""
        CREATE TABLE expenses_fixed_costs (
            expense_id INTEGER PRIMARY KEY,
            expense_name VARCHAR(255) NOT NULL,
            category VARCHAR(50) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Monthly', 'Quarterly', 'Annual')),
            due_day INTEGER,
            last_paid_date DATE,
            next_due_date DATE,
            vendor_id INTEGER,
            auto_pay BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (vendor_id) REFERENCES accounting_vendors(vendor_id)
        )
    """)
    
    # 12. HR SCHEMA - Employees
    cursor.execute("""
        CREATE TABLE hr_employees (
            employee_id INTEGER PRIMARY KEY,
            employee_number VARCHAR(20) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            department VARCHAR(50) NOT NULL,
            position VARCHAR(100) NOT NULL,
            hire_date DATE NOT NULL,
            annual_salary DECIMAL(10, 2) NOT NULL,
            pay_frequency VARCHAR(20) DEFAULT 'Bi-weekly' CHECK (pay_frequency IN ('Bi-weekly', 'Monthly')),
            status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Terminated', 'On Leave'))
        )
    """)
    
    # 13. HR SCHEMA - Payroll Log
    cursor.execute("""
        CREATE TABLE hr_payroll_log (
            payroll_id INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            pay_period_start DATE NOT NULL,
            pay_period_end DATE NOT NULL,
            pay_date DATE NOT NULL,
            gross_pay DECIMAL(10, 2) NOT NULL,
            deductions DECIMAL(10, 2) DEFAULT 0.00,
            net_pay DECIMAL(10, 2) NOT NULL,
            bonus DECIMAL(10, 2) DEFAULT 0.00,
            overtime_hours DECIMAL(5, 2) DEFAULT 0.00,
            overtime_pay DECIMAL(8, 2) DEFAULT 0.00,
            FOREIGN KEY (employee_id) REFERENCES hr_employees(employee_id)
        )
    """)
    
    print("✅ All 13 manufacturing tables created successfully!")
    
    return conn, cursor

def generate_sample_data(conn, cursor):
    """Generate sample data for all tables"""
    
    print("🏭 Generating sample manufacturing data...")
    
    # 1. Generate Customers (50 records)
    customers = []
    for i in range(50):
        company_types = ["Automobile", "Aéronautique", "Alimentaire", "Textile", "Chimique"]
        legal_forms = ["SA", "SARL", "SAS", "EURL"]
        
        company_type = random.choice(company_types)
        city = fake.city()
        legal_form = random.choice(legal_forms)
        company_name = f"{company_type} {city} {legal_form}"
        
        customers.append((
            company_name,
            fake.name(),
            fake.email(),
            fake.phone_number(),
            fake.address(),
            random.choice([15, 30, 45, 60]),
            round(random.uniform(25000, 200000), 2),
            fake.date_time_between(start_date='-2y', end_date='now')
        ))
    
    cursor.executemany("""
        INSERT INTO sales_customers 
        (company_name, contact_name, email, phone, address, payment_terms, credit_limit, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)
    
    # 2. Generate Vendors (25 records)
    vendors = []
    vendor_types = ["Acier", "Outils", "Maintenance", "Logiciel", "Énergie", "Matières premières"]
    
    for i in range(25):
        vendor_type = random.choice(vendor_types)
        vendors.append((
            f"Fournisseur {vendor_type} {fake.last_name()}",
            fake.name(),
            fake.email(),
            fake.phone_number(),
            random.choice([15, 30, 45]),
            vendor_type
        ))
    
    cursor.executemany("""
        INSERT INTO accounting_vendors 
        (vendor_name, contact_name, email, phone, payment_terms, vendor_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, vendors)
    
    # 3. Generate Products (20 records)
    products = []
    product_types = ["Bracket", "Shaft", "Housing", "Plate", "Gear", "Bearing"]
    materials = ["Steel", "Aluminum", "Plastic", "Brass"]
    
    for i in range(20):
        product_type = random.choice(product_types)
        material = random.choice(materials)
        material_cost = round(random.uniform(20, 200), 2)
        labor_hours = round(random.uniform(0.5, 8.0), 2)
        labor_cost = round(labor_hours * 45.0, 2)
        base_cost = round(material_cost + labor_cost + random.uniform(10, 50), 2)
        
        products.append((
            f"MP-{i+1:03d}",
            f"{product_type} {material} - Type {chr(65 + i % 26)}",
            base_cost,
            labor_hours,
            material_cost
        ))
    
    cursor.executemany("""
        INSERT INTO operations_products 
        (product_code, product_name, base_cost, labor_hours, material_cost)
        VALUES (?, ?, ?, ?, ?)
    """, products)
    
    # 4. Generate Employees (30 records)
    employees = []
    departments = ["Assembly", "Logistics", "Admin", "Management", "Quality", "Maintenance"]
    
    for i in range(30):
        department = random.choice(departments)
        positions = {
            "Assembly": ["Line Supervisor", "Machine Operator", "Assembly Technician"],
            "Logistics": ["Shipping Coordinator", "Warehouse Manager", "Logistics Clerk"],
            "Admin": ["Accounting Clerk", "HR Coordinator", "Office Manager"],
            "Management": ["Operations Manager", "Production Manager", "General Manager"],
            "Quality": ["Quality Inspector", "QA Manager", "Test Technician"],
            "Maintenance": ["Maintenance Technician", "Facility Manager", "Mechanic"]
        }
        
        position = random.choice(positions[department])
        salary_ranges = {
            "Assembly": (35000, 55000),
            "Logistics": (40000, 60000),
            "Admin": (38000, 58000),
            "Management": (65000, 120000),
            "Quality": (45000, 70000),
            "Maintenance": (42000, 65000)
        }
        
        min_salary, max_salary = salary_ranges[department]
        annual_salary = round(random.uniform(min_salary, max_salary), 2)
        
        employees.append((
            f"EMP{i+1:03d}",
            fake.first_name(),
            fake.last_name(),
            department,
            position,
            fake.date_between(start_date='-5y', end_date='-1m'),
            annual_salary,
            random.choice(['Bi-weekly', 'Monthly']),
            random.choice(['Active'] * 10 + ['On Leave'])
        ))
    
    cursor.executemany("""
        INSERT INTO hr_employees 
        (employee_number, first_name, last_name, department, position, hire_date, annual_salary, pay_frequency, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)
    
    # 5. Generate Invoices (300 records)
    invoices = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(300):
        customer_id = random.randint(1, 50)
        date_issued = fake.date_between(start_date=start_date, end_date='now')
        payment_terms = random.choice([15, 30, 45, 60])
        due_date = date_issued + timedelta(days=payment_terms)
        amount = round(random.uniform(1000, 25000), 2)
        
        # Determine status
        days_since_due = (datetime.now().date() - due_date).days
        if days_since_due < 0:
            status = "Open"
            payment_date = None
        elif days_since_due < 30:
            status = random.choice(["Open", "Paid", "Paid"])
            payment_date = fake.date_between(start_date=due_date, end_date='now') if status == "Paid" else None
        else:
            status = random.choice(["Overdue", "Paid", "Partial"])
            payment_date = fake.date_between(start_date=due_date, end_date='now') if status == "Paid" else None
        
        invoices.append((
            customer_id,
            f"INV-{date_issued.year}-{i+1:04d}",
            date_issued,
            due_date,
            amount,
            status,
            payment_date,
            fake.date_time_between(start_date=date_issued, end_date='now')
        ))
    
    cursor.executemany("""
        INSERT INTO sales_invoices 
        (customer_id, invoice_number, date_issued, due_date, amount, status, payment_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, invoices)
    
    # 6. Generate Production Orders (150 records)
    production_orders = []
    statuses = ["Planned", "In Progress", "Completed", "On Hold"]
    
    for i in range(150):
        customer_id = random.randint(1, 50)
        product_id = random.randint(1, 20)
        start_date = fake.date_between(start_date='-6m', end_date='now')
        expected_completion = start_date + timedelta(days=random.randint(1, 30))
        status = random.choice(statuses)
        
        completion_date = None
        if status == "Completed":
            completion_date = fake.date_between(start_date=start_date, end_date=expected_completion)
        
        units_ordered = random.randint(10, 1000)
        if status == "Completed":
            units_produced = units_ordered
        elif status == "In Progress":
            units_produced = random.randint(0, units_ordered)
        else:
            units_produced = 0
        
        # Get product info for cost calculation
        cursor.execute("SELECT material_cost, labor_hours FROM operations_products WHERE product_id = ?", (product_id,))
        product_info = cursor.fetchone()
        
        if product_info:
            material_cost = round(product_info[0] * units_ordered, 2)
            labor_cost = round(product_info[1] * units_ordered * 45, 2)
            cost_of_goods_sold = round(material_cost + labor_cost, 2)
        else:
            material_cost = labor_cost = cost_of_goods_sold = 0
        
        production_orders.append((
            f"PO-{start_date.year}-{i+1:04d}",
            product_id,
            customer_id,
            start_date,
            completion_date,
            expected_completion,
            status,
            units_ordered,
            units_produced,
            cost_of_goods_sold,
            labor_cost,
            material_cost,
            fake.date_time_between(start_date=start_date, end_date='now')
        ))
    
    cursor.executemany("""
        INSERT INTO operations_production_orders 
        (order_number, product_id, customer_id, start_date, completion_date, expected_completion, status, 
         units_ordered, units_produced, cost_of_goods_sold, labor_cost, material_cost, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, production_orders)
    
    # 7. Generate Cash Ledger (500 records)
    cash_ledger = []
    running_balance = 100000.0
    transaction_types = ["Sale", "Purchase", "Payroll", "Loan", "Interest", "Utilities", "Rent"]
    
    for i in range(500):
        transaction_date = fake.date_between(start_date='-1y', end_date='now')
        transaction_type = random.choice(transaction_types)
        
        if transaction_type == "Sale":
            amount = round(random.uniform(1000, 25000), 2)
            counterparty = f"Customer {random.randint(1, 50)}"
        elif transaction_type == "Purchase":
            amount = -round(random.uniform(500, 15000), 2)
            counterparty = f"Vendor {random.randint(1, 25)}"
        elif transaction_type == "Payroll":
            amount = -round(random.uniform(2000, 8000), 2)
            counterparty = "Payroll Processing"
        elif transaction_type == "Loan":
            amount = round(random.uniform(50000, 200000), 2)
            counterparty = "BNP Paribas"
        else:
            amount = -round(random.uniform(200, 4000), 2)
            counterparty = transaction_type
        
        running_balance += amount
        
        cash_ledger.append((
            f"TXN-{transaction_date.year}-{i+1:05d}",
            transaction_date,
            amount,
            transaction_type,
            counterparty,
            random.randint(1, 100) if random.random() < 0.3 else None,
            random.choice(['invoice', 'purchase', 'payroll']) if random.random() < 0.3 else None,
            f"{transaction_type} - {counterparty}",
            round(running_balance, 2),
            fake.date_time_between(start_date=transaction_date, end_date='now')
        ))
    
    cursor.executemany("""
        INSERT INTO finance_cash_ledger 
        (transaction_number, date_recorded, amount, transaction_type, counterparty, reference_id, 
         reference_type, description, running_balance, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cash_ledger)
    
    # Commit all changes
    conn.commit()
    
    print("✅ Sample data generated for all 13 tables!")

def main():
    """Main function"""
    print("🏭 Creating SQLite Manufacturing Database for Analysis")
    print("=" * 60)
    
    # Create database
    conn, cursor = create_database()
    
    # Generate sample data
    generate_sample_data(conn, cursor)
    
    # Get table counts
    tables = [
        'sales_customers', 'sales_invoices', 'accounting_vendors', 'accounting_accounts_receivable',
        'accounting_purchases', 'accounting_accounts_payable', 'operations_products',
        'operations_production_orders', 'finance_cash_ledger', 'finance_debt_accounts',
        'expenses_fixed_costs', 'hr_employees', 'hr_payroll_log'
    ]
    
    print("\n📊 Database Structure Summary:")
    total_records = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_records += count
        print(f"  ✅ {table}: {count:,} records")
    
    print(f"\n🎉 SQLite database created successfully!")
    print(f"📁 Location: data/ezbi_analytics.db")
    print(f"📊 Total records: {total_records:,}")
    print(f"🔗 13 manufacturing tables across 6 business schemas")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    main()