#!/usr/bin/env python3
"""
EZBI Analytics - Manufacturing Data Generator
Generate comprehensive synthetic data for all manufacturing business intelligence tables
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta, date
from faker import Faker
import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize Faker with French locale
fake = Faker('fr_FR')
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# Database connection settings
DATABASE_URL = "postgresql://user:password@localhost:5432/ezbi_analytics"

class ManufacturingDataGenerator:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.customers = []
        self.vendors = []
        self.products = []
        self.employees = []
        self.invoices = []
        self.production_orders = []
        self.debt_accounts = []
        
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            print("💡 Using SQLite fallback for development")
            # For development, we'll work with CSV files instead
            self.conn = None
    
    async def generate_all_data(self):
        """Generate all synthetic manufacturing data"""
        print("🏭 Starting comprehensive manufacturing data generation...")
        
        # Generate base reference data
        await self.generate_customers(50)
        await self.generate_vendors(25)
        await self.generate_products(20)
        await self.generate_employees(30)
        
        # Generate transactional data
        await self.generate_invoices(500)
        await self.generate_production_orders(200)
        await self.generate_cash_ledger(1000)
        await self.generate_debt_accounts(5)
        await self.generate_fixed_costs(15)
        await self.generate_payroll_data(30)
        
        # Generate derived data
        await self.generate_accounts_receivable()
        await self.generate_purchases(300)
        await self.generate_accounts_payable()
        
        print("🎉 All manufacturing data generated successfully!")
    
    async def generate_customers(self, count: int):
        """Generate synthetic customer data"""
        print(f"👥 Generating {count} synthetic customers...")
        
        # French manufacturing customer types
        company_types = [
            "Automobile", "Aéronautique", "Alimentaire", "Textile", "Chimique",
            "Électronique", "Mécanique", "Plastique", "Métallurgie", "Énergie"
        ]
        
        legal_forms = ["SA", "SARL", "SAS", "EURL", "SNC"]
        
        for i in range(count):
            # Generate realistic French company name
            company_type = random.choice(company_types)
            city = fake.city()
            legal_form = random.choice(legal_forms)
            
            if random.random() < 0.3:
                company_name = f"{company_type} {city} {legal_form}"
            else:
                company_name = f"Société {company_type} {fake.last_name()} {legal_form}"
            
            customer = {
                'customer_id': i + 1,
                'company_name': company_name,
                'contact_name': fake.name(),
                'email': fake.email(),
                'phone': fake.phone_number(),
                'address': fake.address(),
                'payment_terms': random.choice([15, 30, 45, 60]),
                'credit_limit': round(random.uniform(25000, 200000), 2),
                'created_at': fake.date_time_between(start_date='-2y', end_date='now')
            }
            
            self.customers.append(customer)
        
        # Save to CSV for development
        df = pd.DataFrame(self.customers)
        df.to_csv('synthetic_customers.csv', index=False)
        print(f"✅ Generated {count} customers")
    
    async def generate_vendors(self, count: int):
        """Generate synthetic vendor data"""
        print(f"🏢 Generating {count} synthetic vendors...")
        
        vendor_types = [
            "Acier", "Outils", "Maintenance", "Logiciel", "Énergie",
            "Matières premières", "Équipement", "Services", "Transport"
        ]
        
        for i in range(count):
            vendor_type = random.choice(vendor_types)
            
            vendor = {
                'vendor_id': i + 1,
                'vendor_name': f"Fournisseur {vendor_type} {fake.last_name()}",
                'contact_name': fake.name(),
                'email': fake.email(),
                'phone': fake.phone_number(),
                'payment_terms': random.choice([15, 30, 45]),
                'vendor_type': vendor_type
            }
            
            self.vendors.append(vendor)
        
        df = pd.DataFrame(self.vendors)
        df.to_csv('synthetic_vendors.csv', index=False)
        print(f"✅ Generated {count} vendors")
    
    async def generate_products(self, count: int):
        """Generate synthetic product data"""
        print(f"🔧 Generating {count} synthetic products...")
        
        product_types = [
            "Bracket", "Shaft", "Housing", "Plate", "Gear", "Bearing",
            "Connector", "Valve", "Sensor", "Motor", "Pump", "Filter"
        ]
        
        materials = ["Steel", "Aluminum", "Plastic", "Brass", "Titanium"]
        
        for i in range(count):
            product_type = random.choice(product_types)
            material = random.choice(materials)
            
            # Generate realistic costs
            material_cost = round(random.uniform(20, 200), 2)
            labor_hours = round(random.uniform(0.5, 8.0), 2)
            labor_rate = 45.0  # €45/hour
            labor_cost = round(labor_hours * labor_rate, 2)
            base_cost = round(material_cost + labor_cost + random.uniform(10, 50), 2)
            
            product = {
                'product_id': i + 1,
                'product_code': f"MP-{i+1:03d}",
                'product_name': f"{product_type} {material} - Type {chr(65 + i % 26)}",
                'base_cost': base_cost,
                'labor_hours': labor_hours,
                'material_cost': material_cost
            }
            
            self.products.append(product)
        
        df = pd.DataFrame(self.products)
        df.to_csv('synthetic_products.csv', index=False)
        print(f"✅ Generated {count} products")
    
    async def generate_employees(self, count: int):
        """Generate synthetic employee data"""
        print(f"👨‍💼 Generating {count} synthetic employees...")
        
        departments = ["Assembly", "Logistics", "Admin", "Management", "Quality", "Maintenance"]
        positions = {
            "Assembly": ["Line Supervisor", "Machine Operator", "Assembly Technician"],
            "Logistics": ["Shipping Coordinator", "Warehouse Manager", "Logistics Clerk"],
            "Admin": ["Accounting Clerk", "HR Coordinator", "Office Manager"],
            "Management": ["Operations Manager", "Production Manager", "General Manager"],
            "Quality": ["Quality Inspector", "QA Manager", "Test Technician"],
            "Maintenance": ["Maintenance Technician", "Facility Manager", "Mechanic"]
        }
        
        for i in range(count):
            department = random.choice(departments)
            position = random.choice(positions[department])
            
            # Salary ranges by department
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
            
            employee = {
                'employee_id': i + 1,
                'employee_number': f"EMP{i+1:03d}",
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'department': department,
                'position': position,
                'hire_date': fake.date_between(start_date='-5y', end_date='-1m'),
                'annual_salary': annual_salary,
                'pay_frequency': random.choice(['Bi-weekly', 'Monthly']),
                'status': random.choice(['Active'] * 10 + ['On Leave'] * 1)  # 90% active
            }
            
            self.employees.append(employee)
        
        df = pd.DataFrame(self.employees)
        df.to_csv('synthetic_employees.csv', index=False)
        print(f"✅ Generated {count} employees")
    
    async def generate_invoices(self, count: int):
        """Generate synthetic invoice data"""
        print(f"📄 Generating {count} synthetic invoices...")
        
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(count):
            customer = random.choice(self.customers)
            date_issued = fake.date_between(start_date=start_date, end_date='now')
            
            payment_terms = customer['payment_terms']
            due_date = date_issued + timedelta(days=payment_terms)
            
            # Generate realistic invoice amounts
            amount = round(random.uniform(1000, 25000), 2)
            
            # Determine status based on due date
            days_since_due = (datetime.now().date() - due_date).days
            
            if days_since_due < 0:
                status = "Open"
                payment_date = None
            elif days_since_due < 30:
                status = random.choice(["Open", "Paid", "Paid"])  # 66% paid
                payment_date = fake.date_between(start_date=due_date, end_date='now') if status == "Paid" else None
            else:
                status = random.choice(["Overdue", "Paid", "Partial"])
                payment_date = fake.date_between(start_date=due_date, end_date='now') if status == "Paid" else None
            
            invoice = {
                'invoice_id': i + 1,
                'customer_id': customer['customer_id'],
                'invoice_number': f"INV-{date_issued.year}-{i+1:04d}",
                'date_issued': date_issued,
                'due_date': due_date,
                'amount': amount,
                'status': status,
                'payment_date': payment_date,
                'created_at': fake.date_time_between(start_date=date_issued, end_date='now')
            }
            
            self.invoices.append(invoice)
        
        df = pd.DataFrame(self.invoices)
        df.to_csv('synthetic_invoices.csv', index=False)
        print(f"✅ Generated {count} invoices")
    
    async def generate_production_orders(self, count: int):
        """Generate synthetic production order data"""
        print(f"🏭 Generating {count} synthetic production orders...")
        
        statuses = ["Planned", "In Progress", "Completed", "On Hold"]
        
        for i in range(count):
            customer = random.choice(self.customers)
            product = random.choice(self.products)
            
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
            
            # Calculate costs
            material_cost = round(product['material_cost'] * units_ordered, 2)
            labor_cost = round(product['labor_hours'] * units_ordered * 45, 2)  # €45/hour
            cost_of_goods_sold = round(material_cost + labor_cost, 2)
            
            order = {
                'order_id': i + 1,
                'order_number': f"PO-{start_date.year}-{i+1:04d}",
                'product_id': product['product_id'],
                'customer_id': customer['customer_id'],
                'start_date': start_date,
                'completion_date': completion_date,
                'expected_completion': expected_completion,
                'status': status,
                'units_ordered': units_ordered,
                'units_produced': units_produced,
                'cost_of_goods_sold': cost_of_goods_sold,
                'labor_cost': labor_cost,
                'material_cost': material_cost,
                'created_at': fake.date_time_between(start_date=start_date, end_date='now')
            }
            
            self.production_orders.append(order)
        
        df = pd.DataFrame(self.production_orders)
        df.to_csv('synthetic_production_orders.csv', index=False)
        print(f"✅ Generated {count} production orders")
    
    async def generate_cash_ledger(self, count: int):
        """Generate synthetic cash ledger data"""
        print(f"💰 Generating {count} synthetic cash ledger entries...")
        
        transaction_types = ["Sale", "Purchase", "Payroll", "Loan", "Interest", "Utilities", "Rent"]
        
        cash_ledger = []
        running_balance = 100000.0  # Starting balance
        
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(count):
            transaction_date = fake.date_between(start_date=start_date, end_date='now')
            transaction_type = random.choice(transaction_types)
            
            # Generate realistic amounts based on transaction type
            if transaction_type == "Sale":
                amount = round(random.uniform(1000, 25000), 2)
                counterparty = random.choice(self.customers)['company_name']
            elif transaction_type == "Purchase":
                amount = -round(random.uniform(500, 15000), 2)
                counterparty = random.choice(self.vendors)['vendor_name']
            elif transaction_type == "Payroll":
                amount = -round(random.uniform(2000, 8000), 2)
                counterparty = "Payroll Processing"
            elif transaction_type == "Loan":
                amount = round(random.uniform(50000, 200000), 2)
                counterparty = "BNP Paribas"
            elif transaction_type == "Interest":
                amount = -round(random.uniform(200, 2000), 2)
                counterparty = "Interest Payment"
            elif transaction_type == "Utilities":
                amount = -round(random.uniform(1500, 4000), 2)
                counterparty = "EDF"
            elif transaction_type == "Rent":
                amount = -round(random.uniform(8000, 15000), 2)
                counterparty = "Property Management"
            
            running_balance += amount
            
            entry = {
                'transaction_id': i + 1,
                'transaction_number': f"TXN-{transaction_date.year}-{i+1:05d}",
                'date_recorded': transaction_date,
                'amount': amount,
                'transaction_type': transaction_type,
                'counterparty': counterparty,
                'reference_id': random.randint(1, 100) if random.random() < 0.3 else None,
                'reference_type': random.choice(['invoice', 'purchase', 'payroll']) if random.random() < 0.3 else None,
                'description': f"{transaction_type} - {counterparty}",
                'running_balance': round(running_balance, 2),
                'created_at': fake.date_time_between(start_date=transaction_date, end_date='now')
            }
            
            cash_ledger.append(entry)
        
        df = pd.DataFrame(cash_ledger)
        df.to_csv('synthetic_cash_ledger.csv', index=False)
        print(f"✅ Generated {count} cash ledger entries")
    
    async def generate_debt_accounts(self, count: int):
        """Generate synthetic debt account data"""
        print(f"🏦 Generating {count} synthetic debt accounts...")
        
        loan_types = ["Working Capital", "Credit Line", "Equipment", "Real Estate"]
        
        for i in range(count):
            loan_type = random.choice(loan_types)
            principal_amount = round(random.uniform(50000, 500000), 2)
            
            # Calculate outstanding amount (0-90% of principal)
            outstanding_amount = round(principal_amount * random.uniform(0.1, 0.9), 2)
            
            interest_rate = round(random.uniform(0.035, 0.085), 4)  # 3.5% to 8.5%
            
            loan_start_date = fake.date_between(start_date='-3y', end_date='-1m')
            loan_end_date = loan_start_date + timedelta(days=random.randint(365, 1825))  # 1-5 years
            
            # Calculate monthly payment
            months = (loan_end_date - loan_start_date).days / 30
            monthly_payment = round(principal_amount / months * 1.2, 2)  # Include interest
            
            debt_account = {
                'loan_id': i + 1,
                'loan_number': f"LOAN-{loan_start_date.year}-{i+1:03d}",
                'loan_type': loan_type,
                'principal_amount': principal_amount,
                'outstanding_amount': outstanding_amount,
                'interest_rate': interest_rate,
                'monthly_payment': monthly_payment,
                'last_payment_date': fake.date_between(start_date=loan_start_date, end_date='now'),
                'next_due_date': fake.date_between(start_date='now', end_date='+1m'),
                'loan_start_date': loan_start_date,
                'loan_end_date': loan_end_date,
                'status': random.choice(['Active'] * 4 + ['Paid Off'] * 1)  # 80% active
            }
            
            self.debt_accounts.append(debt_account)
        
        df = pd.DataFrame(self.debt_accounts)
        df.to_csv('synthetic_debt_accounts.csv', index=False)
        print(f"✅ Generated {count} debt accounts")
    
    async def generate_fixed_costs(self, count: int):
        """Generate synthetic fixed costs data"""
        print(f"💸 Generating {count} synthetic fixed costs...")
        
        expense_categories = {
            'Rent': {'amount_range': (8000, 15000), 'frequency': 'Monthly'},
            'Utilities': {'amount_range': (2000, 5000), 'frequency': 'Monthly'},
            'Software': {'amount_range': (500, 3000), 'frequency': 'Monthly'},
            'Insurance': {'amount_range': (3000, 8000), 'frequency': 'Quarterly'},
            'Maintenance': {'amount_range': (1000, 4000), 'frequency': 'Monthly'},
            'Security': {'amount_range': (800, 2000), 'frequency': 'Monthly'},
            'Telecommunications': {'amount_range': (300, 1000), 'frequency': 'Monthly'},
            'Legal': {'amount_range': (2000, 5000), 'frequency': 'Quarterly'},
            'Audit': {'amount_range': (5000, 15000), 'frequency': 'Annual'}
        }
        
        fixed_costs = []
        
        for i, (category, config) in enumerate(expense_categories.items()):
            min_amount, max_amount = config['amount_range']
            frequency = config['frequency']
            
            amount = round(random.uniform(min_amount, max_amount), 2)
            
            # Set due day based on frequency
            if frequency == 'Monthly':
                due_day = random.randint(1, 28)
            elif frequency == 'Quarterly':
                due_day = 1
            else:  # Annual
                due_day = 1
            
            fixed_cost = {
                'expense_id': i + 1,
                'expense_name': f"{category} - {fake.company()}",
                'category': category,
                'amount': amount,
                'frequency': frequency,
                'due_day': due_day,
                'last_paid_date': fake.date_between(start_date='-3m', end_date='now'),
                'next_due_date': fake.date_between(start_date='now', end_date='+3m'),
                'vendor_id': random.choice(self.vendors)['vendor_id'] if random.random() < 0.7 else None,
                'auto_pay': random.choice([True, False])
            }
            
            fixed_costs.append(fixed_cost)
        
        df = pd.DataFrame(fixed_costs)
        df.to_csv('synthetic_fixed_costs.csv', index=False)
        print(f"✅ Generated {len(fixed_costs)} fixed costs")
    
    async def generate_payroll_data(self, payroll_periods: int):
        """Generate synthetic payroll data"""
        print(f"💰 Generating payroll data for {payroll_periods} pay periods...")
        
        payroll_log = []
        
        # Generate payroll for each pay period
        for period in range(payroll_periods):
            pay_date = datetime.now() - timedelta(weeks=period * 2)  # Bi-weekly
            pay_period_start = pay_date - timedelta(days=13)
            pay_period_end = pay_date - timedelta(days=1)
            
            for employee in self.employees:
                if employee['status'] != 'Active':
                    continue
                
                # Calculate pay based on frequency
                if employee['pay_frequency'] == 'Bi-weekly':
                    gross_pay = round(employee['annual_salary'] / 26, 2)
                else:  # Monthly
                    gross_pay = round(employee['annual_salary'] / 12, 2)
                
                # Add some variation for overtime
                if random.random() < 0.3:  # 30% chance of overtime
                    overtime_hours = round(random.uniform(1, 10), 2)
                    overtime_pay = round(overtime_hours * 50, 2)  # €50/hour overtime
                    gross_pay += overtime_pay
                else:
                    overtime_hours = 0
                    overtime_pay = 0
                
                # Calculate deductions (taxes, social security, etc.)
                deductions = round(gross_pay * random.uniform(0.25, 0.35), 2)
                net_pay = round(gross_pay - deductions, 2)
                
                # Occasional bonus
                bonus = round(random.uniform(0, 1000), 2) if random.random() < 0.05 else 0
                
                payroll_entry = {
                    'payroll_id': len(payroll_log) + 1,
                    'employee_id': employee['employee_id'],
                    'pay_period_start': pay_period_start.date(),
                    'pay_period_end': pay_period_end.date(),
                    'pay_date': pay_date.date(),
                    'gross_pay': gross_pay,
                    'deductions': deductions,
                    'net_pay': net_pay,
                    'bonus': bonus,
                    'overtime_hours': overtime_hours,
                    'overtime_pay': overtime_pay
                }
                
                payroll_log.append(payroll_entry)
        
        df = pd.DataFrame(payroll_log)
        df.to_csv('synthetic_payroll_log.csv', index=False)
        print(f"✅ Generated {len(payroll_log)} payroll entries")
    
    async def generate_accounts_receivable(self):
        """Generate synthetic accounts receivable data"""
        print("📊 Generating accounts receivable data...")
        
        ar_data = []
        
        # Process open invoices
        for invoice in self.invoices:
            if invoice['status'] in ['Open', 'Overdue', 'Partial']:
                days_outstanding = (datetime.now().date() - invoice['due_date']).days
                
                # Determine aging bucket
                if days_outstanding <= 30:
                    aging_bucket = '0-30'
                elif days_outstanding <= 60:
                    aging_bucket = '31-60'
                elif days_outstanding <= 90:
                    aging_bucket = '61-90'
                else:
                    aging_bucket = '90+'
                
                # Calculate outstanding amount
                if invoice['status'] == 'Partial':
                    amount_outstanding = round(invoice['amount'] * random.uniform(0.1, 0.8), 2)
                else:
                    amount_outstanding = invoice['amount']
                
                ar_entry = {
                    'ar_id': len(ar_data) + 1,
                    'invoice_id': invoice['invoice_id'],
                    'customer_id': invoice['customer_id'],
                    'amount_outstanding': amount_outstanding,
                    'days_outstanding': max(0, days_outstanding),
                    'aging_bucket': aging_bucket,
                    'as_of_date': datetime.now().date(),
                    'created_at': datetime.now()
                }
                
                ar_data.append(ar_entry)
        
        df = pd.DataFrame(ar_data)
        df.to_csv('synthetic_accounts_receivable.csv', index=False)
        print(f"✅ Generated {len(ar_data)} accounts receivable entries")
    
    async def generate_purchases(self, count: int):
        """Generate synthetic purchase data"""
        print(f"🛒 Generating {count} synthetic purchases...")
        
        categories = [
            "Raw Materials", "Tools", "Repairs", "Software", "Utilities",
            "Office Supplies", "Equipment", "Maintenance", "Services"
        ]
        
        purchases = []
        
        for i in range(count):
            vendor = random.choice(self.vendors)
            category = random.choice(categories)
            
            date_purchased = fake.date_between(start_date='-1y', end_date='now')
            due_date = date_purchased + timedelta(days=vendor['payment_terms'])
            
            amount = round(random.uniform(100, 10000), 2)
            
            # Determine payment status
            days_since_due = (datetime.now().date() - due_date).days
            
            if days_since_due < 0:
                payment_status = "Outstanding"
                payment_date = None
            elif days_since_due < 30:
                payment_status = random.choice(["Outstanding", "Paid", "Paid"])
                payment_date = fake.date_between(start_date=due_date, end_date='now') if payment_status == "Paid" else None
            else:
                payment_status = random.choice(["Outstanding", "Paid", "Partial"])
                payment_date = fake.date_between(start_date=due_date, end_date='now') if payment_status == "Paid" else None
            
            purchase = {
                'purchase_id': i + 1,
                'vendor_id': vendor['vendor_id'],
                'purchase_number': f"PUR-{date_purchased.year}-{i+1:04d}",
                'category': category,
                'amount': amount,
                'date_purchased': date_purchased,
                'due_date': due_date,
                'payment_status': payment_status,
                'payment_date': payment_date,
                'description': f"{category} from {vendor['vendor_name']}",
                'created_at': fake.date_time_between(start_date=date_purchased, end_date='now')
            }
            
            purchases.append(purchase)
        
        df = pd.DataFrame(purchases)
        df.to_csv('synthetic_purchases.csv', index=False)
        print(f"✅ Generated {count} purchases")
    
    async def generate_accounts_payable(self):
        """Generate synthetic accounts payable data"""
        print("📋 Generating accounts payable data...")
        
        # This would be generated from the purchases data
        # For now, we'll create a simple CSV file
        ap_data = []
        
        # Process outstanding purchases
        purchases_df = pd.read_csv('synthetic_purchases.csv')
        
        for _, purchase in purchases_df.iterrows():
            if purchase['payment_status'] in ['Outstanding', 'Partial']:
                due_date = pd.to_datetime(purchase['due_date']).date()
                days_until_due = (due_date - datetime.now().date()).days
                
                if purchase['payment_status'] == 'Partial':
                    amount_outstanding = round(purchase['amount'] * random.uniform(0.1, 0.8), 2)
                else:
                    amount_outstanding = purchase['amount']
                
                ap_entry = {
                    'ap_id': len(ap_data) + 1,
                    'purchase_id': purchase['purchase_id'],
                    'vendor_id': purchase['vendor_id'],
                    'amount_outstanding': amount_outstanding,
                    'due_date': due_date,
                    'days_until_due': days_until_due,
                    'created_at': datetime.now()
                }
                
                ap_data.append(ap_entry)
        
        df = pd.DataFrame(ap_data)
        df.to_csv('synthetic_accounts_payable.csv', index=False)
        print(f"✅ Generated {len(ap_data)} accounts payable entries")
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            print("🔌 Database connection closed")

async def main():
    """Main function to generate all manufacturing data"""
    print("🚀 EZBI Analytics - Manufacturing Data Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = ManufacturingDataGenerator(DATABASE_URL)
    
    try:
        # Connect to database
        await generator.connect()
        
        # Generate all data
        await generator.generate_all_data()
        
        print("\n📊 Data Generation Summary:")
        print(f"✅ Customers: {len(generator.customers)}")
        print(f"✅ Vendors: {len(generator.vendors)}")
        print(f"✅ Products: {len(generator.products)}")
        print(f"✅ Employees: {len(generator.employees)}")
        print(f"✅ Invoices: {len(generator.invoices)}")
        print(f"✅ Production Orders: {len(generator.production_orders)}")
        print(f"✅ Debt Accounts: {len(generator.debt_accounts)}")
        
        print("\n🎉 Manufacturing data generation completed successfully!")
        print("📁 All data saved to CSV files for import into database")
        
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await generator.close()

if __name__ == "__main__":
    asyncio.run(main())