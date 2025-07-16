#!/usr/bin/env python3
"""
Manufacturing Database Population Script
Populates the 7 empty tables with realistic manufacturing data
"""

import sqlite3
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

def connect_db():
    """Connect to the manufacturing database"""
    return sqlite3.connect('data/ezbi_analytics.db')

def get_existing_data(conn):
    """Get existing data for foreign key relationships"""
    cursor = conn.cursor()
    
    # Get all invoices with their status
    cursor.execute("SELECT invoice_id, customer_id, amount, status, date_issued, due_date FROM sales_invoices")
    invoices = cursor.fetchall()
    
    # Get all customers
    cursor.execute("SELECT customer_id, company_name FROM sales_customers")
    customers = cursor.fetchall()
    
    # Get all vendors
    cursor.execute("SELECT vendor_id, vendor_name FROM accounting_vendors")
    vendors = cursor.fetchall()
    
    # Get all employees
    cursor.execute("SELECT employee_id, employee_number, annual_salary FROM hr_employees")
    employees = cursor.fetchall()
    
    return {
        'invoices': invoices,
        'customers': customers, 
        'vendors': vendors,
        'employees': employees
    }

def populate_accounts_receivable(conn, existing_data):
    """Populate accounting_accounts_receivable table"""
    print("Populating accounts_receivable...")
    
    cursor = conn.cursor()
    as_of_date = date(2025, 7, 15)  # Current analysis date
    
    ar_records = []
    
    for invoice in existing_data['invoices']:
        invoice_id, customer_id, amount, status, date_issued, due_date = invoice
        
        # Only create AR records for Open and Overdue invoices
        if status in ['Open', 'Overdue']:
            amount_outstanding = float(amount)
            
            # Calculate days outstanding
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            days_outstanding = (as_of_date - due_date_obj).days
            
            # Determine aging bucket
            if days_outstanding <= 30:
                aging_bucket = '0-30'
            elif days_outstanding <= 60:
                aging_bucket = '31-60'
            elif days_outstanding <= 90:
                aging_bucket = '61-90'
            else:
                aging_bucket = '90+'
            
            ar_records.append((
                invoice_id, customer_id, amount_outstanding, 
                days_outstanding, aging_bucket, as_of_date
            ))
        
        elif status == 'Partial':
            # Partial payments have some amount outstanding
            amount_outstanding = float(amount) * random.uniform(0.2, 0.7)  # 20-70% remaining
            
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            days_outstanding = (as_of_date - due_date_obj).days
            
            if days_outstanding <= 30:
                aging_bucket = '0-30'
            elif days_outstanding <= 60:
                aging_bucket = '31-60'
            elif days_outstanding <= 90:
                aging_bucket = '61-90'
            else:
                aging_bucket = '90+'
            
            ar_records.append((
                invoice_id, customer_id, round(amount_outstanding, 2),
                days_outstanding, aging_bucket, as_of_date
            ))
    
    # Insert AR records
    cursor.executemany(
        """INSERT INTO accounting_accounts_receivable 
           (invoice_id, customer_id, amount_outstanding, days_outstanding, aging_bucket, as_of_date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ar_records
    )
    
    print(f"Inserted {len(ar_records)} accounts receivable records")
    return len(ar_records)

def populate_purchases(conn, existing_data):
    """Populate accounting_purchases table"""
    print("Populating purchases...")
    
    cursor = conn.cursor()
    
    # Purchase categories for manufacturing
    categories = [
        'Raw Materials', 'Components', 'Tools & Equipment', 'Maintenance Supplies',
        'Office Supplies', 'Utilities', 'Professional Services', 'Insurance',
        'Software Licenses', 'Marketing', 'Travel', 'Training'
    ]
    
    purchases = []
    
    # Generate 200 purchase records over the last 12 months
    start_date = date(2024, 7, 15)
    end_date = date(2025, 7, 15)
    
    for i in range(1, 201):
        vendor_id = random.choice(existing_data['vendors'])[0]
        purchase_number = f"PO-2024-{i:04d}"
        category = random.choice(categories)
        
        # Different amount ranges by category
        if category in ['Raw Materials', 'Components']:
            amount = random.uniform(5000, 50000)
        elif category in ['Tools & Equipment']:
            amount = random.uniform(2000, 25000)
        elif category in ['Utilities', 'Insurance']:
            amount = random.uniform(1000, 8000)
        else:
            amount = random.uniform(200, 5000)
        
        # Random date within range
        random_days = random.randint(0, (end_date - start_date).days)
        date_purchased = start_date + timedelta(days=random_days)
        
        # Due date based on vendor payment terms (assume 30 days)
        due_date = date_purchased + timedelta(days=30)
        
        # Status based on due date - using correct schema values
        if due_date < date(2025, 7, 15):
            payment_status = random.choices(['Paid', 'Outstanding'], weights=[85, 15])[0]
            if payment_status == 'Paid':
                payment_date = due_date - timedelta(days=random.randint(-10, 10))
            else:
                payment_date = None
        else:
            payment_status = 'Outstanding'
            payment_date = None
        
        description = f"{category} purchase from vendor {vendor_id}"
        
        purchases.append((
            vendor_id, purchase_number, category, round(amount, 2),
            date_purchased, due_date, payment_status, payment_date, description
        ))
    
    # Insert purchases
    cursor.executemany(
        """INSERT INTO accounting_purchases 
           (vendor_id, purchase_number, category, amount, date_purchased, due_date, payment_status, payment_date, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        purchases
    )
    
    print(f"Inserted {len(purchases)} purchase records")
    return len(purchases)

def populate_accounts_payable(conn, existing_data):
    """Populate accounting_accounts_payable table"""
    print("Populating accounts_payable...")
    
    cursor = conn.cursor()
    
    # Get unpaid purchases to create AP records
    cursor.execute("""
        SELECT purchase_id, vendor_id, amount, due_date 
        FROM accounting_purchases 
        WHERE payment_status = 'Outstanding'
    """)
    unpaid_purchases = cursor.fetchall()
    
    as_of_date = date(2025, 7, 15)
    ap_records = []
    
    for purchase in unpaid_purchases:
        purchase_id, vendor_id, amount, due_date = purchase
        
        # Calculate days until due (negative if overdue)
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
        days_until_due = (due_date_obj - as_of_date).days
        
        ap_records.append((
            purchase_id, vendor_id, float(amount), due_date_obj, days_until_due
        ))
    
    # Insert AP records
    cursor.executemany(
        """INSERT INTO accounting_accounts_payable 
           (purchase_id, vendor_id, amount_outstanding, due_date, days_until_due)
           VALUES (?, ?, ?, ?, ?)""",
        ap_records
    )
    
    print(f"Inserted {len(ap_records)} accounts payable records")
    return len(ap_records)

def populate_debt_accounts(conn):
    """Populate finance_debt_accounts table"""
    print("Populating debt_accounts...")
    
    cursor = conn.cursor()
    
    # Manufacturing company debt accounts
    debt_accounts = [
        {
            'loan_number': 'TERM-2023-001',
            'loan_type': 'Term Loan',
            'principal_amount': 500000.00,
            'outstanding_amount': 425000.00,
            'interest_rate': 4.25,
            'monthly_payment': 9250.00,
            'last_payment_date': date(2025, 6, 15),
            'next_due_date': date(2025, 8, 15),
            'loan_start_date': date(2023, 3, 15),
            'loan_end_date': date(2028, 3, 15),
            'status': 'Active'
        },
        {
            'loan_number': 'LOC-2024-001',
            'loan_type': 'Line of Credit',
            'principal_amount': 200000.00,
            'outstanding_amount': 75000.00,
            'interest_rate': 6.50,
            'monthly_payment': 0.00,  # LOC has variable payments
            'last_payment_date': date(2025, 7, 1),
            'next_due_date': date(2025, 8, 1),
            'loan_start_date': date(2024, 1, 10),
            'loan_end_date': date(2027, 1, 10),
            'status': 'Active'
        },
        {
            'loan_number': 'SBA-2022-001',
            'loan_type': 'SBA Loan',
            'principal_amount': 350000.00,
            'outstanding_amount': 280000.00,
            'interest_rate': 5.75,
            'monthly_payment': 3850.00,
            'last_payment_date': date(2025, 6, 15),
            'next_due_date': date(2025, 8, 15),
            'loan_start_date': date(2022, 6, 1),
            'loan_end_date': date(2032, 6, 1),
            'status': 'Active'
        },
        {
            'loan_number': 'EQUIP-2024-002',
            'loan_type': 'Equipment Loan',
            'principal_amount': 150000.00,
            'outstanding_amount': 125000.00,
            'interest_rate': 3.95,
            'monthly_payment': 2775.00,
            'last_payment_date': date(2025, 6, 15),
            'next_due_date': date(2025, 8, 15),
            'loan_start_date': date(2024, 4, 1),
            'loan_end_date': date(2029, 4, 1),
            'status': 'Active'
        }
    ]
    
    debt_records = []
    for debt in debt_accounts:
        debt_records.append((
            debt['loan_number'], debt['loan_type'], debt['principal_amount'],
            debt['outstanding_amount'], debt['interest_rate'], debt['monthly_payment'],
            debt['last_payment_date'], debt['next_due_date'], debt['loan_start_date'],
            debt['loan_end_date'], debt['status']
        ))
    
    cursor.executemany(
        """INSERT INTO finance_debt_accounts 
           (loan_number, loan_type, principal_amount, outstanding_amount, 
            interest_rate, monthly_payment, last_payment_date, next_due_date,
            loan_start_date, loan_end_date, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        debt_records
    )
    
    print(f"Inserted {len(debt_records)} debt account records")
    return len(debt_records)

def populate_fixed_costs(conn):
    """Populate expenses_fixed_costs table"""
    print("Populating fixed_costs...")
    
    cursor = conn.cursor()
    
    # Monthly fixed costs for manufacturing facility
    fixed_costs = [
        ('Facility Rent', 'Facilities', 25000.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Electricity', 'Utilities', 8500.00, 'Monthly', 15, date(2025, 7, 15), date(2025, 8, 15), None, True),
        ('Natural Gas', 'Utilities', 3200.00, 'Monthly', 10, date(2025, 7, 10), date(2025, 8, 10), None, True),
        ('Water & Sewer', 'Utilities', 1100.00, 'Monthly', 20, date(2025, 7, 20), date(2025, 8, 20), None, False),
        ('Waste Management', 'Utilities', 850.00, 'Monthly', 5, date(2025, 7, 5), date(2025, 8, 5), None, True),
        ('Property Insurance', 'Insurance', 2800.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Liability Insurance', 'Insurance', 1950.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Workers Compensation', 'Insurance', 3400.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('ERP Software License', 'Software', 1200.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('CAD Software License', 'Software', 850.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Security Software', 'Software', 275.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Equipment Maintenance', 'Maintenance', 4500.00, 'Monthly', 15, date(2025, 7, 15), date(2025, 8, 15), None, False),
        ('Facility Maintenance', 'Maintenance', 1800.00, 'Monthly', 30, date(2025, 7, 30), date(2025, 8, 30), None, False),
        ('Internet & Phone', 'Communications', 450.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Security Services', 'Security', 1200.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, True),
        ('Quality Certifications', 'Compliance', 950.00, 'Monthly', 1, date(2025, 7, 1), date(2025, 8, 1), None, False),
    ]
    
    cursor.executemany(
        """INSERT INTO expenses_fixed_costs 
           (expense_name, category, amount, frequency, due_day, last_paid_date, next_due_date, vendor_id, auto_pay)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        fixed_costs
    )
    
    print(f"Inserted {len(fixed_costs)} fixed cost records")
    return len(fixed_costs)

def populate_payroll_log(conn, existing_data):
    """Populate hr_payroll_log table"""
    print("Populating payroll_log...")
    
    cursor = conn.cursor()
    
    payroll_records = []
    
    # Generate 12 months of payroll data
    for month_offset in range(12):
        pay_date = date(2024, 8, 15) + timedelta(days=month_offset * 30)
        pay_period_start = pay_date - timedelta(days=15)
        pay_period_end = pay_date - timedelta(days=1)
        
        for employee in existing_data['employees']:
            employee_id, employee_number, annual_salary = employee
            
            # Calculate monthly gross pay
            monthly_gross = float(annual_salary) / 12
            
            # Calculate deductions (approximate percentages for France)
            total_deductions = monthly_gross * 0.22  # French social contributions ~22%
            
            # Add some overtime for production workers (randomly)
            bonus = 0
            if random.random() < 0.2:  # 20% chance of bonus
                bonus = random.uniform(500, 2000)
            
            overtime_hours = 0
            overtime_pay = 0
            if random.random() < 0.3:  # 30% chance of overtime
                overtime_hours = random.uniform(5, 20)
                overtime_rate = (annual_salary / 2080) * 1.25  # 25% overtime premium
                overtime_pay = overtime_hours * overtime_rate
            
            # Calculate final amounts
            gross_pay = monthly_gross + overtime_pay + bonus
            net_pay = gross_pay - total_deductions
            
            payroll_records.append((
                employee_id, pay_period_start, pay_period_end, pay_date,
                round(gross_pay, 2), round(total_deductions, 2), round(net_pay, 2),
                round(bonus, 2), round(overtime_hours, 1), round(overtime_pay, 2)
            ))
    
    cursor.executemany(
        """INSERT INTO hr_payroll_log 
           (employee_id, pay_period_start, pay_period_end, pay_date, gross_pay,
            deductions, net_pay, bonus, overtime_hours, overtime_pay)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        payroll_records
    )
    
    print(f"Inserted {len(payroll_records)} payroll records")
    return len(payroll_records)

def main():
    """Main execution function"""
    print("Starting manufacturing database population...")
    print("=" * 50)
    
    # Connect to database
    conn = connect_db()
    
    try:
        # Get existing data for FK relationships
        existing_data = get_existing_data(conn)
        print(f"Found {len(existing_data['invoices'])} invoices, {len(existing_data['customers'])} customers")
        print(f"Found {len(existing_data['vendors'])} vendors, {len(existing_data['employees'])} employees")
        print()
        
        # Populate each empty table
        ar_count = populate_accounts_receivable(conn, existing_data)
        purchases_count = populate_purchases(conn, existing_data) 
        ap_count = populate_accounts_payable(conn, existing_data)
        debt_count = populate_debt_accounts(conn)
        fixed_costs_count = populate_fixed_costs(conn)
        payroll_count = populate_payroll_log(conn, existing_data)
        
        # Commit all changes
        conn.commit()
        
        print()
        print("=" * 50)
        print("DATABASE POPULATION COMPLETED!")
        print("=" * 50)
        print(f"✅ Accounts Receivable: {ar_count} records")
        print(f"✅ Purchases: {purchases_count} records")  
        print(f"✅ Accounts Payable: {ap_count} records")
        print(f"✅ Debt Accounts: {debt_count} records")
        print(f"✅ Fixed Costs: {fixed_costs_count} records")
        print(f"✅ Payroll Log: {payroll_count} records")
        print()
        print(f"Total new records: {ar_count + purchases_count + ap_count + debt_count + fixed_costs_count + payroll_count}")
        
    except Exception as e:
        print(f"Error during population: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()