"""Create comprehensive manufacturing schema

Revision ID: 003_manufacturing_schema
Revises: 002_add_manufacturing_tables
Create Date: 2025-07-15 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers
revision = '003_manufacturing_schema'
down_revision = '002_add_manufacturing_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create comprehensive manufacturing business intelligence schema"""
    
    # Create schemas
    op.execute(text("CREATE SCHEMA IF NOT EXISTS sales"))
    op.execute(text("CREATE SCHEMA IF NOT EXISTS accounting"))
    op.execute(text("CREATE SCHEMA IF NOT EXISTS operations"))
    op.execute(text("CREATE SCHEMA IF NOT EXISTS finance"))
    op.execute(text("CREATE SCHEMA IF NOT EXISTS expenses"))
    op.execute(text("CREATE SCHEMA IF NOT EXISTS hr"))
    
    # ===============================
    # SALES SCHEMA
    # ===============================
    
    # Customers table
    op.create_table(
        'customers',
        sa.Column('customer_id', sa.Integer, primary_key=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('address', sa.Text),
        sa.Column('payment_terms', sa.Integer, default=30),
        sa.Column('credit_limit', sa.Numeric(12, 2), default=50000.00),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        schema='sales'
    )
    
    # Invoices table
    op.create_table(
        'invoices',
        sa.Column('invoice_id', sa.Integer, primary_key=True),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('sales.customers.customer_id'), nullable=False),
        sa.Column('invoice_number', sa.String(50), unique=True, nullable=False),
        sa.Column('date_issued', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.String(20), default='Open'),
        sa.Column('payment_date', sa.Date),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('Open', 'Paid', 'Overdue', 'Partial')", name='invoice_status_check'),
        schema='sales'
    )
    
    # ===============================
    # ACCOUNTING SCHEMA
    # ===============================
    
    # Vendors table
    op.create_table(
        'vendors',
        sa.Column('vendor_id', sa.Integer, primary_key=True),
        sa.Column('vendor_name', sa.String(255), nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('payment_terms', sa.Integer, default=30),
        sa.Column('vendor_type', sa.String(50), nullable=False),
        schema='accounting'
    )
    
    # Accounts Receivable table
    op.create_table(
        'accounts_receivable',
        sa.Column('ar_id', sa.Integer, primary_key=True),
        sa.Column('invoice_id', sa.Integer, sa.ForeignKey('sales.invoices.invoice_id'), nullable=False),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('sales.customers.customer_id'), nullable=False),
        sa.Column('amount_outstanding', sa.Numeric(12, 2), nullable=False),
        sa.Column('days_outstanding', sa.Integer, nullable=False),
        sa.Column('aging_bucket', sa.String(20), nullable=False),
        sa.Column('as_of_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("aging_bucket IN ('0-30', '31-60', '61-90', '90+')", name='ar_aging_check'),
        schema='accounting'
    )
    
    # Purchases table
    op.create_table(
        'purchases',
        sa.Column('purchase_id', sa.Integer, primary_key=True),
        sa.Column('vendor_id', sa.Integer, sa.ForeignKey('accounting.vendors.vendor_id'), nullable=False),
        sa.Column('purchase_number', sa.String(50), unique=True, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('date_purchased', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('payment_status', sa.String(20), default='Outstanding'),
        sa.Column('payment_date', sa.Date),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("payment_status IN ('Outstanding', 'Paid', 'Partial')", name='purchase_payment_check'),
        schema='accounting'
    )
    
    # Accounts Payable table
    op.create_table(
        'accounts_payable',
        sa.Column('ap_id', sa.Integer, primary_key=True),
        sa.Column('purchase_id', sa.Integer, sa.ForeignKey('accounting.purchases.purchase_id'), nullable=False),
        sa.Column('vendor_id', sa.Integer, sa.ForeignKey('accounting.vendors.vendor_id'), nullable=False),
        sa.Column('amount_outstanding', sa.Numeric(12, 2), nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('days_until_due', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        schema='accounting'
    )
    
    # ===============================
    # OPERATIONS SCHEMA
    # ===============================
    
    # Products table
    op.create_table(
        'products',
        sa.Column('product_id', sa.Integer, primary_key=True),
        sa.Column('product_code', sa.String(50), unique=True, nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('base_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('labor_hours', sa.Numeric(5, 2), nullable=False),
        sa.Column('material_cost', sa.Numeric(10, 2), nullable=False),
        schema='operations'
    )
    
    # Production Orders table
    op.create_table(
        'production_orders',
        sa.Column('order_id', sa.Integer, primary_key=True),
        sa.Column('order_number', sa.String(50), unique=True, nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('operations.products.product_id'), nullable=False),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('sales.customers.customer_id'), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('completion_date', sa.Date),
        sa.Column('expected_completion', sa.Date, nullable=False),
        sa.Column('status', sa.String(20), default='In Progress'),
        sa.Column('units_ordered', sa.Integer, nullable=False),
        sa.Column('units_produced', sa.Integer, default=0),
        sa.Column('cost_of_goods_sold', sa.Numeric(12, 2)),
        sa.Column('labor_cost', sa.Numeric(10, 2)),
        sa.Column('material_cost', sa.Numeric(10, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('Planned', 'In Progress', 'Completed', 'On Hold')", name='production_status_check'),
        schema='operations'
    )
    
    # ===============================
    # FINANCE SCHEMA
    # ===============================
    
    # Cash Ledger table
    op.create_table(
        'cash_ledger',
        sa.Column('transaction_id', sa.Integer, primary_key=True),
        sa.Column('transaction_number', sa.String(50), unique=True, nullable=False),
        sa.Column('date_recorded', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('counterparty', sa.String(255)),
        sa.Column('reference_id', sa.Integer),
        sa.Column('reference_type', sa.String(50)),
        sa.Column('description', sa.Text),
        sa.Column('running_balance', sa.Numeric(15, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        schema='finance'
    )
    
    # Debt Accounts table
    op.create_table(
        'debt_accounts',
        sa.Column('loan_id', sa.Integer, primary_key=True),
        sa.Column('loan_number', sa.String(50), unique=True, nullable=False),
        sa.Column('loan_type', sa.String(50), nullable=False),
        sa.Column('principal_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('outstanding_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('monthly_payment', sa.Numeric(10, 2)),
        sa.Column('last_payment_date', sa.Date),
        sa.Column('next_due_date', sa.Date),
        sa.Column('loan_start_date', sa.Date, nullable=False),
        sa.Column('loan_end_date', sa.Date),
        sa.Column('status', sa.String(20), default='Active'),
        sa.CheckConstraint("status IN ('Active', 'Paid Off', 'Default')", name='debt_status_check'),
        schema='finance'
    )
    
    # Debt Payments table
    op.create_table(
        'debt_payments',
        sa.Column('payment_id', sa.Integer, primary_key=True),
        sa.Column('loan_id', sa.Integer, sa.ForeignKey('finance.debt_accounts.loan_id'), nullable=False),
        sa.Column('payment_date', sa.Date, nullable=False),
        sa.Column('principal_payment', sa.Numeric(10, 2), nullable=False),
        sa.Column('interest_payment', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_payment', sa.Numeric(10, 2), nullable=False),
        sa.Column('remaining_balance', sa.Numeric(15, 2), nullable=False),
        schema='finance'
    )
    
    # ===============================
    # EXPENSES SCHEMA
    # ===============================
    
    # Fixed Costs table
    op.create_table(
        'fixed_costs',
        sa.Column('expense_id', sa.Integer, primary_key=True),
        sa.Column('expense_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('due_day', sa.Integer),
        sa.Column('last_paid_date', sa.Date),
        sa.Column('next_due_date', sa.Date),
        sa.Column('vendor_id', sa.Integer, sa.ForeignKey('accounting.vendors.vendor_id')),
        sa.Column('auto_pay', sa.Boolean, default=False),
        sa.CheckConstraint("frequency IN ('Monthly', 'Quarterly', 'Annual')", name='fixed_cost_frequency_check'),
        schema='expenses'
    )
    
    # Expense Log table
    op.create_table(
        'expense_log',
        sa.Column('log_id', sa.Integer, primary_key=True),
        sa.Column('expense_id', sa.Integer, sa.ForeignKey('expenses.fixed_costs.expense_id'), nullable=False),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('date_paid', sa.Date, nullable=False),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('notes', sa.Text),
        schema='expenses'
    )
    
    # ===============================
    # HR SCHEMA
    # ===============================
    
    # Employees table
    op.create_table(
        'employees',
        sa.Column('employee_id', sa.Integer, primary_key=True),
        sa.Column('employee_number', sa.String(20), unique=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('department', sa.String(50), nullable=False),
        sa.Column('position', sa.String(100), nullable=False),
        sa.Column('hire_date', sa.Date, nullable=False),
        sa.Column('annual_salary', sa.Numeric(10, 2), nullable=False),
        sa.Column('pay_frequency', sa.String(20), default='Bi-weekly'),
        sa.Column('status', sa.String(20), default='Active'),
        sa.CheckConstraint("status IN ('Active', 'Terminated', 'On Leave')", name='employee_status_check'),
        sa.CheckConstraint("pay_frequency IN ('Bi-weekly', 'Monthly')", name='employee_pay_frequency_check'),
        schema='hr'
    )
    
    # Payroll Log table
    op.create_table(
        'payroll_log',
        sa.Column('payroll_id', sa.Integer, primary_key=True),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('hr.employees.employee_id'), nullable=False),
        sa.Column('pay_period_start', sa.Date, nullable=False),
        sa.Column('pay_period_end', sa.Date, nullable=False),
        sa.Column('pay_date', sa.Date, nullable=False),
        sa.Column('gross_pay', sa.Numeric(10, 2), nullable=False),
        sa.Column('deductions', sa.Numeric(10, 2), default=0.00),
        sa.Column('net_pay', sa.Numeric(10, 2), nullable=False),
        sa.Column('bonus', sa.Numeric(10, 2), default=0.00),
        sa.Column('overtime_hours', sa.Numeric(5, 2), default=0.00),
        sa.Column('overtime_pay', sa.Numeric(8, 2), default=0.00),
        schema='hr'
    )
    
    # ===============================
    # INDEXES FOR PERFORMANCE
    # ===============================
    
    # Sales indexes
    op.create_index('idx_invoices_customer_date', 'invoices', ['customer_id', 'date_issued'], schema='sales')
    op.create_index('idx_invoices_status', 'invoices', ['status'], schema='sales')
    
    # Accounting indexes
    op.create_index('idx_ar_aging', 'accounts_receivable', ['aging_bucket', 'as_of_date'], schema='accounting')
    op.create_index('idx_purchases_vendor_date', 'purchases', ['vendor_id', 'date_purchased'], schema='accounting')
    
    # Operations indexes
    op.create_index('idx_production_status', 'production_orders', ['status', 'start_date'], schema='operations')
    
    # Finance indexes
    op.create_index('idx_cash_ledger_date', 'cash_ledger', ['date_recorded'], schema='finance')
    op.create_index('idx_cash_ledger_type', 'cash_ledger', ['transaction_type'], schema='finance')


def downgrade():
    """Drop comprehensive manufacturing schema"""
    
    # Drop all tables in reverse order to handle foreign key constraints
    op.drop_table('payroll_log', schema='hr')
    op.drop_table('employees', schema='hr')
    op.drop_table('expense_log', schema='expenses')
    op.drop_table('fixed_costs', schema='expenses')
    op.drop_table('debt_payments', schema='finance')
    op.drop_table('debt_accounts', schema='finance')
    op.drop_table('cash_ledger', schema='finance')
    op.drop_table('production_orders', schema='operations')
    op.drop_table('products', schema='operations')
    op.drop_table('accounts_payable', schema='accounting')
    op.drop_table('purchases', schema='accounting')
    op.drop_table('accounts_receivable', schema='accounting')
    op.drop_table('vendors', schema='accounting')
    op.drop_table('invoices', schema='sales')
    op.drop_table('customers', schema='sales')
    
    # Drop schemas
    op.execute(text("DROP SCHEMA IF EXISTS hr CASCADE"))
    op.execute(text("DROP SCHEMA IF EXISTS expenses CASCADE"))
    op.execute(text("DROP SCHEMA IF EXISTS finance CASCADE"))
    op.execute(text("DROP SCHEMA IF EXISTS operations CASCADE"))
    op.execute(text("DROP SCHEMA IF EXISTS accounting CASCADE"))
    op.execute(text("DROP SCHEMA IF EXISTS sales CASCADE"))