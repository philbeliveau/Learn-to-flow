-- Manufacturing Use Case - PostgreSQL Schema
-- Railway PostgreSQL Database Schema

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS accounting;
CREATE SCHEMA IF NOT EXISTS operations;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS expenses;
CREATE SCHEMA IF NOT EXISTS hr;

-- ===============================
-- 1. SALES & INVOICES
-- ===============================
CREATE TABLE sales.customers (
    customer_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    payment_terms INTEGER DEFAULT 30, -- Net-30
    credit_limit DECIMAL(12,2) DEFAULT 50000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales.invoices (
    invoice_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    date_issued DATE NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Open' CHECK (status IN ('Open', 'Paid', 'Overdue', 'Partial')),
    payment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 2. ACCOUNTS RECEIVABLE
-- ===============================
CREATE TABLE accounting.accounts_receivable (
    ar_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES sales.invoices(invoice_id),
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    amount_outstanding DECIMAL(12,2) NOT NULL,
    days_outstanding INTEGER NOT NULL,
    aging_bucket VARCHAR(20) NOT NULL CHECK (aging_bucket IN ('0-30', '31-60', '61-90', '90+')),
    as_of_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 3. PRODUCTION ORDERS
-- ===============================
CREATE TABLE operations.products (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    base_cost DECIMAL(10,2) NOT NULL,
    labor_hours DECIMAL(5,2) NOT NULL,
    material_cost DECIMAL(10,2) NOT NULL
);

CREATE TABLE operations.production_orders (
    order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    product_id INTEGER REFERENCES operations.products(product_id),
    customer_id INTEGER REFERENCES sales.customers(customer_id),
    start_date DATE NOT NULL,
    completion_date DATE,
    expected_completion DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'In Progress' CHECK (status IN ('Planned', 'In Progress', 'Completed', 'On Hold')),
    units_ordered INTEGER NOT NULL,
    units_produced INTEGER DEFAULT 0,
    cost_of_goods_sold DECIMAL(12,2),
    labor_cost DECIMAL(10,2),
    material_cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 4. PURCHASES & ACCOUNTS PAYABLE
-- ===============================
CREATE TABLE accounting.vendors (
    vendor_id SERIAL PRIMARY KEY,
    vendor_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    payment_terms INTEGER DEFAULT 30, -- Net-30
    vendor_type VARCHAR(50) NOT NULL -- Steel, Tools, Maintenance, Software
);

CREATE TABLE accounting.purchases (
    purchase_id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES accounting.vendors(vendor_id),
    purchase_number VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL, -- Raw Materials, Tools, Repairs, Software
    amount DECIMAL(12,2) NOT NULL,
    date_purchased DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'Outstanding' CHECK (payment_status IN ('Outstanding', 'Paid', 'Partial')),
    payment_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounting.accounts_payable (
    ap_id SERIAL PRIMARY KEY,
    purchase_id INTEGER REFERENCES accounting.purchases(purchase_id),
    vendor_id INTEGER REFERENCES accounting.vendors(vendor_id),
    amount_outstanding DECIMAL(12,2) NOT NULL,
    due_date DATE NOT NULL,
    days_until_due INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 5. CASH FLOW LEDGER
-- ===============================
CREATE TABLE finance.cash_ledger (
    transaction_id SERIAL PRIMARY KEY,
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    date_recorded DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL, -- Positive = inflow, Negative = outflow
    transaction_type VARCHAR(50) NOT NULL, -- Sale, Purchase, Payroll, Loan, Interest
    counterparty VARCHAR(255), -- Customer/Vendor/Employee name
    reference_id INTEGER, -- Links to invoice_id, purchase_id, etc.
    reference_type VARCHAR(50), -- invoice, purchase, payroll, loan
    description TEXT,
    running_balance DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 6. DEBT & FINANCING
-- ===============================
CREATE TABLE finance.debt_accounts (
    loan_id SERIAL PRIMARY KEY,
    loan_number VARCHAR(50) UNIQUE NOT NULL,
    loan_type VARCHAR(50) NOT NULL, -- Working Capital, Credit Line, Equipment
    principal_amount DECIMAL(15,2) NOT NULL,
    outstanding_amount DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,4) NOT NULL, -- 0.0750 = 7.5%
    monthly_payment DECIMAL(10,2),
    last_payment_date DATE,
    next_due_date DATE,
    loan_start_date DATE NOT NULL,
    loan_end_date DATE,
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Paid Off', 'Default'))
);

CREATE TABLE finance.debt_payments (
    payment_id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES finance.debt_accounts(loan_id),
    payment_date DATE NOT NULL,
    principal_payment DECIMAL(10,2) NOT NULL,
    interest_payment DECIMAL(10,2) NOT NULL,
    total_payment DECIMAL(10,2) NOT NULL,
    remaining_balance DECIMAL(15,2) NOT NULL
);

-- ===============================
-- 7. FIXED COSTS (OPEX)
-- ===============================
CREATE TABLE expenses.fixed_costs (
    expense_id SERIAL PRIMARY KEY,
    expense_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- Rent, Utilities, Software, Insurance
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(20) NOT NULL, -- Monthly, Quarterly, Annual
    due_day INTEGER, -- Day of month (1-31)
    last_paid_date DATE,
    next_due_date DATE,
    vendor_id INTEGER REFERENCES accounting.vendors(vendor_id),
    auto_pay BOOLEAN DEFAULT FALSE
);

CREATE TABLE expenses.expense_log (
    log_id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses.fixed_costs(expense_id),
    amount_paid DECIMAL(10,2) NOT NULL,
    date_paid DATE NOT NULL,
    payment_method VARCHAR(50),
    notes TEXT
);

-- ===============================
-- 8. HR & PAYROLL
-- ===============================
CREATE TABLE hr.employees (
    employee_id SERIAL PRIMARY KEY,
    employee_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL, -- Assembly, Logistics, Admin, Management
    position VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    annual_salary DECIMAL(10,2) NOT NULL,
    pay_frequency VARCHAR(20) DEFAULT 'Bi-weekly', -- Bi-weekly, Monthly
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Terminated', 'On Leave'))
);

CREATE TABLE hr.payroll_log (
    payroll_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES hr.employees(employee_id),
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    gross_pay DECIMAL(10,2) NOT NULL,
    deductions DECIMAL(10,2) DEFAULT 0.00,
    net_pay DECIMAL(10,2) NOT NULL,
    bonus DECIMAL(10,2) DEFAULT 0.00,
    overtime_hours DECIMAL(5,2) DEFAULT 0.00,
    overtime_pay DECIMAL(8,2) DEFAULT 0.00
);

-- ===============================
-- INDEXES FOR PERFORMANCE
-- ===============================
CREATE INDEX idx_invoices_customer_date ON sales.invoices(customer_id, date_issued);
CREATE INDEX idx_invoices_status ON sales.invoices(status);
CREATE INDEX idx_ar_aging ON accounting.accounts_receivable(aging_bucket, as_of_date);
CREATE INDEX idx_production_status ON operations.production_orders(status, start_date);
CREATE INDEX idx_cash_ledger_date ON finance.cash_ledger(date_recorded);
CREATE INDEX idx_cash_ledger_type ON finance.cash_ledger(transaction_type);
CREATE INDEX idx_purchases_vendor_date ON accounting.purchases(vendor_id, date_purchased);

-- ===============================
-- INITIAL SEED DATA
-- ===============================

-- Sample Customers
INSERT INTO sales.customers (company_name, contact_name, email, payment_terms, credit_limit) VALUES
('AutoParts Manufacturing', 'John Smith', 'jsmith@autoparts.com', 30, 75000.00),
('Industrial Solutions Ltd', 'Sarah Johnson', 'sarah@industrialsol.com', 45, 100000.00),
('Precision Tools Inc', 'Mike Chen', 'mchen@precisiontools.com', 30, 50000.00),
('MegaCorp Industries', 'Lisa Williams', 'lwilliams@megacorp.com', 15, 150000.00),
('Small Machine Shop', 'Bob Martinez', 'bob@smallmachine.com', 30, 25000.00);

-- Sample Products
INSERT INTO operations.products (product_code, product_name, base_cost, labor_hours, material_cost) VALUES
('MP-001', 'Custom Bracket - Type A', 125.00, 2.5, 75.00),
('MP-002', 'Precision Shaft - 10mm', 89.50, 1.8, 45.00),
('MP-003', 'Housing Assembly - Large', 275.00, 4.2, 180.00),
('MP-004', 'Connector Plate - Steel', 67.00, 1.2, 35.00),
('MP-005', 'Custom Gear - 24T', 156.00, 3.1, 95.00);

-- Sample Vendors
INSERT INTO accounting.vendors (vendor_name, contact_name, vendor_type, payment_terms) VALUES
('SteelCorp Supplies', 'Dave Wilson', 'Steel', 30),
('Industrial Tools Direct', 'Anna Clark', 'Tools', 15),
('MaintainPro Services', 'Carlos Rodriguez', 'Maintenance', 30),
('TechSoft Solutions', 'Jennifer Lee', 'Software', 30),
('PowerCo Utilities', 'System Billing', 'Utilities', 15);

-- Sample Employees
INSERT INTO hr.employees (employee_number, first_name, last_name, department, position, hire_date, annual_salary) VALUES
('EMP001', 'James', 'Thompson', 'Assembly', 'Line Supervisor', '2020-03-15', 65000.00),
('EMP002', 'Maria', 'Garcia', 'Assembly', 'Machine Operator', '2021-06-01', 48000.00),
('EMP003', 'David', 'Brown', 'Logistics', 'Shipping Coordinator', '2019-09-10', 52000.00),
('EMP004', 'Susan', 'Davis', 'Admin', 'Accounting Clerk', '2022-01-20', 45000.00),
('EMP005', 'Robert', 'Miller', 'Management', 'Operations Manager', '2018-05-01', 85000.00);

-- Fixed Costs Setup
INSERT INTO expenses.fixed_costs (expense_name, category, amount, frequency, due_day, next_due_date) VALUES
('Factory Rent', 'Rent', 12000.00, 'Monthly', 1, '2024-01-01'),
('Electricity', 'Utilities', 2800.00, 'Monthly', 15, '2024-01-15'),
('ERP Software License', 'Software', 1200.00, 'Monthly', 5, '2024-01-05'),
('General Insurance', 'Insurance', 4500.00, 'Quarterly', 1, '2024-01-01'),
('Internet & Phone', 'Utilities', 450.00, 'Monthly', 10, '2024-01-10');

-- Working Capital Loan
INSERT INTO finance.debt_accounts (loan_number, loan_type, principal_amount, outstanding_amount, interest_rate, monthly_payment, loan_start_date, next_due_date) VALUES
('WC-2023-001', 'Working Capital', 250000.00, 187500.00, 0.0825, 5200.00, '2023-01-15', '2024-01-15');