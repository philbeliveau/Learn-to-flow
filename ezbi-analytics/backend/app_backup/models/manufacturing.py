"""
Manufacturing Schema Models
Complete PostgreSQL schema implementation for manufacturing business intelligence
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import CheckConstraint

from app.core.database import Base

# ===============================
# SALES SCHEMA
# ===============================

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": "sales"}
    
    customer_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    payment_terms = Column(Integer, default=30)  # Net-30
    credit_limit = Column(Numeric(12, 2), default=50000.00)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoices = relationship("Invoice", back_populates="customer")
    production_orders = relationship("ProductionOrder", back_populates="customer")
    accounts_receivable = relationship("AccountsReceivable", back_populates="customer")

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("status IN ('Open', 'Paid', 'Overdue', 'Partial')", name="invoice_status_check"),
        {"schema": "sales"}
    )
    
    invoice_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("sales.customers.customer_id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    date_issued = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="Open")
    payment_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    accounts_receivable = relationship("AccountsReceivable", back_populates="invoice")

# ===============================
# ACCOUNTING SCHEMA
# ===============================

class AccountsReceivable(Base):
    __tablename__ = "accounts_receivable"
    __table_args__ = (
        CheckConstraint("aging_bucket IN ('0-30', '31-60', '61-90', '90+')", name="ar_aging_check"),
        {"schema": "accounting"}
    )
    
    ar_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("sales.invoices.invoice_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("sales.customers.customer_id"), nullable=False)
    amount_outstanding = Column(Numeric(12, 2), nullable=False)
    days_outstanding = Column(Integer, nullable=False)
    aging_bucket = Column(String(20), nullable=False)
    as_of_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="accounts_receivable")
    customer = relationship("Customer", back_populates="accounts_receivable")

class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = {"schema": "accounting"}
    
    vendor_id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    payment_terms = Column(Integer, default=30)  # Net-30
    vendor_type = Column(String(50), nullable=False)  # Steel, Tools, Maintenance, Software
    
    # Relationships
    purchases = relationship("Purchase", back_populates="vendor")
    accounts_payable = relationship("AccountsPayable", back_populates="vendor")
    fixed_costs = relationship("FixedCost", back_populates="vendor")

class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("payment_status IN ('Outstanding', 'Paid', 'Partial')", name="purchase_payment_check"),
        {"schema": "accounting"}
    )
    
    purchase_id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("accounting.vendors.vendor_id"), nullable=False)
    purchase_number = Column(String(50), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # Raw Materials, Tools, Repairs, Software
    amount = Column(Numeric(12, 2), nullable=False)
    date_purchased = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_status = Column(String(20), default="Outstanding")
    payment_date = Column(Date)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="purchases")
    accounts_payable = relationship("AccountsPayable", back_populates="purchase")

class AccountsPayable(Base):
    __tablename__ = "accounts_payable"
    __table_args__ = {"schema": "accounting"}
    
    ap_id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("accounting.purchases.purchase_id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("accounting.vendors.vendor_id"), nullable=False)
    amount_outstanding = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    days_until_due = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    purchase = relationship("Purchase", back_populates="accounts_payable")
    vendor = relationship("Vendor", back_populates="accounts_payable")

# ===============================
# OPERATIONS SCHEMA
# ===============================

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "operations"}
    
    product_id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    base_cost = Column(Numeric(10, 2), nullable=False)
    labor_hours = Column(Numeric(5, 2), nullable=False)
    material_cost = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    production_orders = relationship("ProductionOrder", back_populates="product")

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    __table_args__ = (
        CheckConstraint("status IN ('Planned', 'In Progress', 'Completed', 'On Hold')", name="production_status_check"),
        {"schema": "operations"}
    )
    
    order_id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("operations.products.product_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("sales.customers.customer_id"), nullable=False)
    start_date = Column(Date, nullable=False)
    completion_date = Column(Date)
    expected_completion = Column(Date, nullable=False)
    status = Column(String(20), default="In Progress")
    units_ordered = Column(Integer, nullable=False)
    units_produced = Column(Integer, default=0)
    cost_of_goods_sold = Column(Numeric(12, 2))
    labor_cost = Column(Numeric(10, 2))
    material_cost = Column(Numeric(10, 2))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="production_orders")
    customer = relationship("Customer", back_populates="production_orders")

# ===============================
# FINANCE SCHEMA
# ===============================

class CashLedger(Base):
    __tablename__ = "cash_ledger"
    __table_args__ = {"schema": "finance"}
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(50), unique=True, nullable=False)
    date_recorded = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)  # Positive = inflow, Negative = outflow
    transaction_type = Column(String(50), nullable=False)  # Sale, Purchase, Payroll, Loan, Interest
    counterparty = Column(String(255))  # Customer/Vendor/Employee name
    reference_id = Column(Integer)  # Links to invoice_id, purchase_id, etc.
    reference_type = Column(String(50))  # invoice, purchase, payroll, loan
    description = Column(Text)
    running_balance = Column(Numeric(15, 2))
    created_at = Column(DateTime, server_default=func.now())

class DebtAccount(Base):
    __tablename__ = "debt_accounts"
    __table_args__ = (
        CheckConstraint("status IN ('Active', 'Paid Off', 'Default')", name="debt_status_check"),
        {"schema": "finance"}
    )
    
    loan_id = Column(Integer, primary_key=True, index=True)
    loan_number = Column(String(50), unique=True, nullable=False)
    loan_type = Column(String(50), nullable=False)  # Working Capital, Credit Line, Equipment
    principal_amount = Column(Numeric(15, 2), nullable=False)
    outstanding_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 4), nullable=False)  # 0.0750 = 7.5%
    monthly_payment = Column(Numeric(10, 2))
    last_payment_date = Column(Date)
    next_due_date = Column(Date)
    loan_start_date = Column(Date, nullable=False)
    loan_end_date = Column(Date)
    status = Column(String(20), default="Active")
    
    # Relationships
    debt_payments = relationship("DebtPayment", back_populates="debt_account")

class DebtPayment(Base):
    __tablename__ = "debt_payments"
    __table_args__ = {"schema": "finance"}
    
    payment_id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("finance.debt_accounts.loan_id"), nullable=False)
    payment_date = Column(Date, nullable=False)
    principal_payment = Column(Numeric(10, 2), nullable=False)
    interest_payment = Column(Numeric(10, 2), nullable=False)
    total_payment = Column(Numeric(10, 2), nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)
    
    # Relationships
    debt_account = relationship("DebtAccount", back_populates="debt_payments")

# ===============================
# EXPENSES SCHEMA
# ===============================

class FixedCost(Base):
    __tablename__ = "fixed_costs"
    __table_args__ = (
        CheckConstraint("frequency IN ('Monthly', 'Quarterly', 'Annual')", name="fixed_cost_frequency_check"),
        {"schema": "expenses"}
    )
    
    expense_id = Column(Integer, primary_key=True, index=True)
    expense_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # Rent, Utilities, Software, Insurance
    amount = Column(Numeric(10, 2), nullable=False)
    frequency = Column(String(20), nullable=False)  # Monthly, Quarterly, Annual
    due_day = Column(Integer)  # Day of month (1-31)
    last_paid_date = Column(Date)
    next_due_date = Column(Date)
    vendor_id = Column(Integer, ForeignKey("accounting.vendors.vendor_id"))
    auto_pay = Column(Boolean, default=False)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="fixed_costs")
    expense_logs = relationship("ExpenseLog", back_populates="fixed_cost")

class ExpenseLog(Base):
    __tablename__ = "expense_log"
    __table_args__ = {"schema": "expenses"}
    
    log_id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.fixed_costs.expense_id"), nullable=False)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    date_paid = Column(Date, nullable=False)
    payment_method = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    fixed_cost = relationship("FixedCost", back_populates="expense_logs")

# ===============================
# HR SCHEMA
# ===============================

class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("status IN ('Active', 'Terminated', 'On Leave')", name="employee_status_check"),
        CheckConstraint("pay_frequency IN ('Bi-weekly', 'Monthly')", name="employee_pay_frequency_check"),
        {"schema": "hr"}
    )
    
    employee_id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)  # Assembly, Logistics, Admin, Management
    position = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    annual_salary = Column(Numeric(10, 2), nullable=False)
    pay_frequency = Column(String(20), default="Bi-weekly")
    status = Column(String(20), default="Active")
    
    # Relationships
    payroll_logs = relationship("PayrollLog", back_populates="employee")

class PayrollLog(Base):
    __tablename__ = "payroll_log"
    __table_args__ = {"schema": "hr"}
    
    payroll_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.employee_id"), nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    gross_pay = Column(Numeric(10, 2), nullable=False)
    deductions = Column(Numeric(10, 2), default=0.00)
    net_pay = Column(Numeric(10, 2), nullable=False)
    bonus = Column(Numeric(10, 2), default=0.00)
    overtime_hours = Column(Numeric(5, 2), default=0.00)
    overtime_pay = Column(Numeric(8, 2), default=0.00)
    
    # Relationships
    employee = relationship("Employee", back_populates="payroll_logs")