#!/usr/bin/env python3
"""
Production-Ready Manufacturing Models for PostgreSQL
==================================================

This module contains SQLAlchemy models for all manufacturing tables
optimized for PostgreSQL with proper indexing, constraints, and relationships.
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Time, Text, Boolean,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, date
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()

class TimestampMixin:
    """Mixin for adding timestamp columns."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SalesCustomer(Base, TimestampMixin):
    """Sales customers table with enhanced constraints."""
    __tablename__ = 'sales_customers'
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    payment_terms = Column(Integer, default=30, nullable=False)  # Days
    credit_limit = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Relationships
    invoices = relationship("SalesInvoice", back_populates="customer")
    production_orders = relationship("OperationsProductionOrder", back_populates="customer")
    accounts_receivable = relationship("AccountingAccountsReceivable", back_populates="customer")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('payment_terms > 0', name='check_payment_terms_positive'),
        CheckConstraint('credit_limit >= 0', name='check_credit_limit_non_negative'),
        Index('idx_sales_customers_company_name', 'company_name'),
        Index('idx_sales_customers_email', 'email'),
        Index('idx_sales_customers_created_at', 'created_at'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        if email and '@' not in email:
            raise ValueError('Invalid email format')
        return email

class SalesInvoice(Base, TimestampMixin):
    """Sales invoices table with payment tracking."""
    __tablename__ = 'sales_invoices'
    
    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('sales_customers.customer_id'), nullable=False)
    invoice_number = Column(String(100), nullable=False, unique=True)
    date_issued = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    payment_date = Column(Date, nullable=True)
    
    # Relationships
    customer = relationship("SalesCustomer", back_populates="invoices")
    accounts_receivable = relationship("AccountingAccountsReceivable", back_populates="invoice")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
        CheckConstraint("status IN ('pending', 'paid', 'overdue', 'cancelled')", name='check_status_valid'),
        CheckConstraint('due_date >= date_issued', name='check_due_date_after_issued'),
        Index('idx_sales_invoices_customer_id', 'customer_id'),
        Index('idx_sales_invoices_date_issued', 'date_issued'),
        Index('idx_sales_invoices_due_date', 'due_date'),
        Index('idx_sales_invoices_payment_date', 'payment_date'),
        Index('idx_sales_invoices_status', 'status'),
        Index('idx_sales_invoices_invoice_number', 'invoice_number'),
    )

class AccountingVendor(Base, TimestampMixin):
    """Accounting vendors table."""
    __tablename__ = 'accounting_vendors'
    
    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    payment_terms = Column(Integer, default=30, nullable=False)
    tax_id = Column(String(50), nullable=True)
    
    # Relationships
    purchases = relationship("AccountingPurchase", back_populates="vendor")
    accounts_payable = relationship("AccountingAccountsPayable", back_populates="vendor")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('payment_terms > 0', name='check_vendor_payment_terms_positive'),
        Index('idx_accounting_vendors_vendor_name', 'vendor_name'),
        Index('idx_accounting_vendors_email', 'email'),
        Index('idx_accounting_vendors_tax_id', 'tax_id'),
    )

class AccountingPurchase(Base, TimestampMixin):
    """Accounting purchases table."""
    __tablename__ = 'accounting_purchases'
    
    purchase_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey('accounting_vendors.vendor_id'), nullable=False)
    purchase_order_number = Column(String(100), nullable=False)
    date_ordered = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), default='ordered', nullable=False)
    delivery_date = Column(Date, nullable=True)
    
    # Relationships
    vendor = relationship("AccountingVendor", back_populates="purchases")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_purchase_amount_positive'),
        CheckConstraint("status IN ('ordered', 'delivered', 'cancelled')", name='check_purchase_status_valid'),
        Index('idx_accounting_purchases_vendor_id', 'vendor_id'),
        Index('idx_accounting_purchases_date_ordered', 'date_ordered'),
        Index('idx_accounting_purchases_status', 'status'),
        Index('idx_accounting_purchases_po_number', 'purchase_order_number'),
    )

class AccountingAccountsReceivable(Base, TimestampMixin):
    """Accounts receivable with aging analysis."""
    __tablename__ = 'accounting_accounts_receivable'
    
    ar_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('sales_invoices.invoice_id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('sales_customers.customer_id'), nullable=False)
    amount_outstanding = Column(Numeric(15, 2), nullable=False)
    days_outstanding = Column(Integer, nullable=False)
    aging_bucket = Column(String(20), nullable=False)
    as_of_date = Column(Date, nullable=False)
    
    # Relationships
    invoice = relationship("SalesInvoice", back_populates="accounts_receivable")
    customer = relationship("SalesCustomer", back_populates="accounts_receivable")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount_outstanding >= 0', name='check_ar_amount_non_negative'),
        CheckConstraint('days_outstanding >= 0', name='check_days_outstanding_non_negative'),
        CheckConstraint("aging_bucket IN ('0-30', '31-60', '61-90', '90+')", name='check_aging_bucket_valid'),
        Index('idx_ar_invoice_id', 'invoice_id'),
        Index('idx_ar_customer_id', 'customer_id'),
        Index('idx_ar_aging_bucket', 'aging_bucket'),
        Index('idx_ar_as_of_date', 'as_of_date'),
        Index('idx_ar_days_outstanding', 'days_outstanding'),
    )

class AccountingAccountsPayable(Base, TimestampMixin):
    """Accounts payable tracking."""
    __tablename__ = 'accounting_accounts_payable'
    
    ap_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey('accounting_vendors.vendor_id'), nullable=False)
    purchase_id = Column(Integer, ForeignKey('accounting_purchases.purchase_id'), nullable=True)
    amount_outstanding = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    days_until_due = Column(Integer, nullable=False)
    
    # Relationships
    vendor = relationship("AccountingVendor", back_populates="accounts_payable")
    purchase = relationship("AccountingPurchase")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount_outstanding >= 0', name='check_ap_amount_non_negative'),
        Index('idx_ap_vendor_id', 'vendor_id'),
        Index('idx_ap_due_date', 'due_date'),
        Index('idx_ap_days_until_due', 'days_until_due'),
    )

class OperationsProduct(Base, TimestampMixin):
    """Operations products catalog."""
    __tablename__ = 'operations_products'
    
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(100), nullable=False, unique=True)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    cost_per_unit = Column(Numeric(15, 2), nullable=False)
    
    # Relationships
    production_orders = relationship("OperationsProductionOrder", back_populates="product")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('unit_price > 0', name='check_unit_price_positive'),
        CheckConstraint('cost_per_unit >= 0', name='check_cost_per_unit_non_negative'),
        Index('idx_operations_products_product_code', 'product_code'),
        Index('idx_operations_products_category', 'category'),
        Index('idx_operations_products_product_name', 'product_name'),
    )

class OperationsProductionOrder(Base, TimestampMixin):
    """Operations production orders with cost tracking."""
    __tablename__ = 'operations_production_orders'
    
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(100), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey('operations_products.product_id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('sales_customers.customer_id'), nullable=False)
    start_date = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)
    expected_completion = Column(Date, nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    units_ordered = Column(Integer, nullable=False)
    units_produced = Column(Integer, default=0, nullable=False)
    cost_of_goods_sold = Column(Numeric(15, 2), default=0, nullable=False)
    labor_cost = Column(Numeric(15, 2), default=0, nullable=False)
    material_cost = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Relationships
    product = relationship("OperationsProduct", back_populates="production_orders")
    customer = relationship("SalesCustomer", back_populates="production_orders")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('units_ordered > 0', name='check_units_ordered_positive'),
        CheckConstraint('units_produced >= 0', name='check_units_produced_non_negative'),
        CheckConstraint('units_produced <= units_ordered', name='check_units_produced_not_exceed_ordered'),
        CheckConstraint('cost_of_goods_sold >= 0', name='check_cogs_non_negative'),
        CheckConstraint('labor_cost >= 0', name='check_labor_cost_non_negative'),
        CheckConstraint('material_cost >= 0', name='check_material_cost_non_negative'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name='check_production_status_valid'),
        CheckConstraint('expected_completion >= start_date', name='check_expected_completion_after_start'),
        Index('idx_operations_production_orders_product_id', 'product_id'),
        Index('idx_operations_production_orders_customer_id', 'customer_id'),
        Index('idx_operations_production_orders_status', 'status'),
        Index('idx_operations_production_orders_start_date', 'start_date'),
        Index('idx_operations_production_orders_expected_completion', 'expected_completion'),
        Index('idx_operations_production_orders_order_number', 'order_number'),
    )

class FinanceCashLedger(Base, TimestampMixin):
    """Finance cash ledger with transaction tracking."""
    __tablename__ = 'finance_cash_ledger'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_number = Column(String(100), nullable=False, unique=True)
    date_recorded = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    counterparty = Column(String(255), nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    running_balance = Column(Numeric(15, 2), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount != 0', name='check_amount_not_zero'),
        CheckConstraint("transaction_type IN ('inflow', 'outflow')", name='check_transaction_type_valid'),
        Index('idx_finance_cash_ledger_date_recorded', 'date_recorded'),
        Index('idx_finance_cash_ledger_transaction_type', 'transaction_type'),
        Index('idx_finance_cash_ledger_reference', 'reference_id', 'reference_type'),
        Index('idx_finance_cash_ledger_transaction_number', 'transaction_number'),
        Index('idx_finance_cash_ledger_counterparty', 'counterparty'),
    )

class FinanceDebtAccount(Base, TimestampMixin):
    """Finance debt accounts tracking."""
    __tablename__ = 'finance_debt_accounts'
    
    debt_id = Column(Integer, primary_key=True, autoincrement=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    principal_balance = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 4), nullable=False)
    maturity_date = Column(Date, nullable=True)
    monthly_payment = Column(Numeric(15, 2), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('principal_balance >= 0', name='check_principal_balance_non_negative'),
        CheckConstraint('interest_rate >= 0', name='check_interest_rate_non_negative'),
        CheckConstraint('monthly_payment >= 0', name='check_monthly_payment_non_negative'),
        CheckConstraint("account_type IN ('loan', 'credit_line', 'mortgage', 'bond')", name='check_account_type_valid'),
        Index('idx_finance_debt_accounts_account_type', 'account_type'),
        Index('idx_finance_debt_accounts_maturity_date', 'maturity_date'),
        Index('idx_finance_debt_accounts_account_name', 'account_name'),
    )

class ExpensesFixedCost(Base, TimestampMixin):
    """Expenses fixed costs tracking."""
    __tablename__ = 'expenses_fixed_costs'
    
    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    expense_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    frequency = Column(String(50), default='monthly', nullable=False)
    date_incurred = Column(Date, nullable=False)
    vendor_name = Column(String(255), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_expense_amount_positive'),
        CheckConstraint("frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'annually')", name='check_frequency_valid'),
        Index('idx_expenses_fixed_costs_expense_type', 'expense_type'),
        Index('idx_expenses_fixed_costs_date_incurred', 'date_incurred'),
        Index('idx_expenses_fixed_costs_frequency', 'frequency'),
        Index('idx_expenses_fixed_costs_vendor_name', 'vendor_name'),
    )

class HREmployee(Base, TimestampMixin):
    """HR employees table."""
    __tablename__ = 'hr_employees'
    
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_number = Column(String(50), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    salary = Column(Numeric(15, 2), nullable=False)
    employment_status = Column(String(50), default='active', nullable=False)
    
    # Relationships
    payroll_records = relationship("HRPayrollLog", back_populates="employee")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('salary > 0', name='check_salary_positive'),
        CheckConstraint("employment_status IN ('active', 'inactive', 'terminated')", name='check_employment_status_valid'),
        Index('idx_hr_employees_employee_number', 'employee_number'),
        Index('idx_hr_employees_department', 'department'),
        Index('idx_hr_employees_employment_status', 'employment_status'),
        Index('idx_hr_employees_hire_date', 'hire_date'),
        Index('idx_hr_employees_full_name', 'first_name', 'last_name'),
    )

class HRPayrollLog(Base, TimestampMixin):
    """HR payroll log with detailed tracking."""
    __tablename__ = 'hr_payroll_log'
    
    payroll_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('hr_employees.employee_id'), nullable=False)
    payroll_date = Column(Date, nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    gross_pay = Column(Numeric(15, 2), nullable=False)
    deductions = Column(Numeric(15, 2), default=0, nullable=False)
    net_pay = Column(Numeric(15, 2), nullable=False)
    overtime_hours = Column(Numeric(5, 2), default=0, nullable=False)
    overtime_pay = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Relationships
    employee = relationship("HREmployee", back_populates="payroll_records")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('gross_pay > 0', name='check_gross_pay_positive'),
        CheckConstraint('deductions >= 0', name='check_deductions_non_negative'),
        CheckConstraint('net_pay > 0', name='check_net_pay_positive'),
        CheckConstraint('overtime_hours >= 0', name='check_overtime_hours_non_negative'),
        CheckConstraint('overtime_pay >= 0', name='check_overtime_pay_non_negative'),
        CheckConstraint('pay_period_end >= pay_period_start', name='check_pay_period_valid'),
        CheckConstraint('net_pay = gross_pay - deductions', name='check_net_pay_calculation'),
        Index('idx_hr_payroll_log_employee_id', 'employee_id'),
        Index('idx_hr_payroll_log_payroll_date', 'payroll_date'),
        Index('idx_hr_payroll_log_pay_period', 'pay_period_start', 'pay_period_end'),
    )

# Database initialization and utility functions
def create_all_tables(engine):
    """Create all manufacturing tables."""
    Base.metadata.create_all(bind=engine)

def get_table_schemas():
    """Get all table schemas for documentation."""
    schemas = {}
    for table in Base.metadata.tables.values():
        schemas[table.name] = {
            'columns': [
                {
                    'name': col.name,
                    'type': str(col.type),
                    'nullable': col.nullable,
                    'primary_key': col.primary_key,
                    'foreign_key': col.foreign_keys
                }
                for col in table.columns
            ],
            'indexes': [
                {
                    'name': idx.name,
                    'columns': [col.name for col in idx.columns],
                    'unique': idx.unique
                }
                for idx in table.indexes
            ],
            'constraints': [
                {
                    'name': const.name,
                    'type': type(const).__name__
                }
                for const in table.constraints
            ]
        }
    return schemas

# Performance monitoring queries
MANUFACTURING_PERFORMANCE_QUERIES = {
    'cash_flow_summary': """
        SELECT 
            DATE_TRUNC('day', date_recorded) as date,
            SUM(CASE WHEN transaction_type = 'inflow' THEN amount ELSE -amount END) as daily_flow,
            SUM(SUM(CASE WHEN transaction_type = 'inflow' THEN amount ELSE -amount END)) 
                OVER (ORDER BY DATE_TRUNC('day', date_recorded)) as running_balance
        FROM finance_cash_ledger
        WHERE date_recorded >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', date_recorded)
        ORDER BY date;
    """,
    
    'production_efficiency': """
        SELECT 
            COUNT(*) as total_orders,
            AVG(units_produced::float / NULLIF(units_ordered, 0)) as avg_efficiency,
            SUM(units_produced) as total_produced,
            SUM(units_ordered) as total_ordered,
            AVG(labor_cost + material_cost) as avg_cost_per_order
        FROM operations_production_orders
        WHERE start_date >= CURRENT_DATE - INTERVAL '30 days';
    """,
    
    'ar_aging_analysis': """
        SELECT 
            aging_bucket,
            COUNT(*) as invoice_count,
            SUM(amount_outstanding) as total_outstanding,
            AVG(amount_outstanding) as avg_outstanding
        FROM accounting_accounts_receivable
        WHERE amount_outstanding > 0
        GROUP BY aging_bucket
        ORDER BY 
            CASE aging_bucket
                WHEN '0-30' THEN 1
                WHEN '31-60' THEN 2
                WHEN '61-90' THEN 3
                WHEN '90+' THEN 4
            END;
    """,
    
    'top_customers_by_revenue': """
        SELECT 
            c.company_name,
            c.customer_id,
            COUNT(i.invoice_id) as invoice_count,
            SUM(i.amount) as total_revenue,
            AVG(i.amount) as avg_invoice_amount
        FROM sales_customers c
        JOIN sales_invoices i ON c.customer_id = i.customer_id
        WHERE i.date_issued >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY c.customer_id, c.company_name
        ORDER BY total_revenue DESC
        LIMIT 10;
    """,
    
    'employee_cost_analysis': """
        SELECT 
            e.department,
            COUNT(e.employee_id) as employee_count,
            SUM(e.salary) as total_salaries,
            AVG(e.salary) as avg_salary,
            SUM(p.gross_pay) as total_gross_pay,
            SUM(p.overtime_pay) as total_overtime
        FROM hr_employees e
        LEFT JOIN hr_payroll_log p ON e.employee_id = p.employee_id
            AND p.payroll_date >= CURRENT_DATE - INTERVAL '30 days'
        WHERE e.employment_status = 'active'
        GROUP BY e.department
        ORDER BY total_salaries DESC;
    """
}

if __name__ == "__main__":
    # Example usage
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create engine (replace with your actual database URL)
    engine = create_engine('postgresql://username:password@localhost/ezbi_analytics')
    
    # Create all tables
    create_all_tables(engine)
    
    # Get table schemas
    schemas = get_table_schemas()
    
    print(f"Created {len(schemas)} manufacturing tables:")
    for table_name in schemas.keys():
        print(f"  - {table_name}")
    
    print("\nPerformance queries available:")
    for query_name in MANUFACTURING_PERFORMANCE_QUERIES.keys():
        print(f"  - {query_name}")