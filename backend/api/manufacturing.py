"""
Manufacturing Analytics API - All Business Intelligence Endpoints
Complete API for all 13 manufacturing tables with analytics and KPIs
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

manufacturing_bp = Blueprint('manufacturing', __name__, url_prefix='/api/manufacturing')

DATABASE_PATH = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/data/ezbi_analytics.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===================
# SALES ANALYTICS
# ===================

@manufacturing_bp.route('/sales/customers', methods=['GET'])
def get_customers():
    """Get all customers with analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get customers with invoice summaries
    cursor.execute("""
        SELECT 
            c.*,
            COUNT(i.invoice_id) as total_invoices,
            COALESCE(SUM(i.amount), 0) as total_revenue,
            COALESCE(AVG(i.amount), 0) as avg_invoice_value
        FROM sales_customers c
        LEFT JOIN sales_invoices i ON c.customer_id = i.customer_id
        GROUP BY c.customer_id
        ORDER BY total_revenue DESC
    """)
    
    customers = []
    for row in cursor.fetchall():
        customers.append({
            'customer_id': row['customer_id'],
            'company_name': row['company_name'],
            'contact_name': row['contact_name'],
            'email': row['email'],
            'phone': row['phone'],
            'address': row['address'],
            'payment_terms': row['payment_terms'],
            'credit_limit': row['credit_limit'],
            'total_invoices': row['total_invoices'],
            'total_revenue': row['total_revenue'],
            'avg_invoice_value': row['avg_invoice_value']
        })
    
    conn.close()
    return jsonify({'customers': customers, 'total': len(customers)})

@manufacturing_bp.route('/sales/invoices', methods=['GET'])
def get_invoices():
    """Get all invoices with customer details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            i.*,
            c.company_name,
            c.contact_name
        FROM sales_invoices i
        JOIN sales_customers c ON i.customer_id = c.customer_id
        ORDER BY i.date_issued DESC
    """)
    
    invoices = []
    for row in cursor.fetchall():
        invoices.append({
            'invoice_id': row['invoice_id'],
            'customer_id': row['customer_id'],
            'company_name': row['company_name'],
            'contact_name': row['contact_name'],
            'invoice_number': row['invoice_number'],
            'date_issued': row['date_issued'],
            'due_date': row['due_date'],
            'amount': row['amount'],
            'status': row['status'],
            'payment_date': row['payment_date']
        })
    
    conn.close()
    return jsonify({'invoices': invoices, 'total': len(invoices)})

@manufacturing_bp.route('/sales/kpis', methods=['GET'])
def get_sales_kpis():
    """Get sales KPIs and analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total sales metrics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_invoices,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_invoice_value,
            COUNT(DISTINCT customer_id) as active_customers
        FROM sales_invoices
    """)
    totals = cursor.fetchone()
    
    # Status breakdown
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM sales_invoices
        GROUP BY status
    """)
    status_breakdown = [dict(row) for row in cursor.fetchall()]
    
    # Monthly revenue trend
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', date_issued) as month,
            SUM(amount) as revenue,
            COUNT(*) as invoice_count
        FROM sales_invoices
        GROUP BY month
        ORDER BY month
    """)
    monthly_trend = [dict(row) for row in cursor.fetchall()]
    
    # Top customers
    cursor.execute("""
        SELECT 
            c.company_name,
            SUM(i.amount) as total_revenue,
            COUNT(i.invoice_id) as invoice_count
        FROM sales_customers c
        JOIN sales_invoices i ON c.customer_id = i.customer_id
        GROUP BY c.customer_id
        ORDER BY total_revenue DESC
        LIMIT 10
    """)
    top_customers = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'totals': dict(totals),
        'status_breakdown': status_breakdown,
        'monthly_trend': monthly_trend,
        'top_customers': top_customers
    })

# ===================
# ACCOUNTING ANALYTICS
# ===================

@manufacturing_bp.route('/accounting/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors with purchase summaries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            v.*,
            COUNT(p.purchase_id) as total_purchases,
            COALESCE(SUM(p.amount), 0) as total_spent,
            COALESCE(AVG(p.amount), 0) as avg_purchase_value
        FROM accounting_vendors v
        LEFT JOIN accounting_purchases p ON v.vendor_id = p.vendor_id
        GROUP BY v.vendor_id
        ORDER BY total_spent DESC
    """)
    
    vendors = []
    for row in cursor.fetchall():
        vendors.append({
            'vendor_id': row['vendor_id'],
            'vendor_name': row['vendor_name'],
            'contact_name': row['contact_name'],
            'email': row['email'],
            'phone': row['phone'],
            'payment_terms': row['payment_terms'],
            'vendor_type': row['vendor_type'],
            'total_purchases': row['total_purchases'],
            'total_spent': row['total_spent'],
            'avg_purchase_value': row['avg_purchase_value']
        })
    
    conn.close()
    return jsonify({'vendors': vendors, 'total': len(vendors)})

@manufacturing_bp.route('/accounting/purchases', methods=['GET'])
def get_purchases():
    """Get all purchases with vendor details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.*,
            v.vendor_name,
            v.vendor_type
        FROM accounting_purchases p
        JOIN accounting_vendors v ON p.vendor_id = v.vendor_id
        ORDER BY p.date_purchased DESC
    """)
    
    purchases = []
    for row in cursor.fetchall():
        purchases.append({
            'purchase_id': row['purchase_id'],
            'vendor_id': row['vendor_id'],
            'vendor_name': row['vendor_name'],
            'vendor_type': row['vendor_type'],
            'purchase_number': row['purchase_number'],
            'category': row['category'],
            'amount': row['amount'],
            'date_purchased': row['date_purchased'],
            'due_date': row['due_date'],
            'payment_status': row['payment_status'],
            'payment_date': row['payment_date'],
            'description': row['description']
        })
    
    conn.close()
    return jsonify({'purchases': purchases, 'total': len(purchases)})

@manufacturing_bp.route('/accounting/accounts-receivable', methods=['GET'])
def get_accounts_receivable():
    """Get accounts receivable with aging analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ar.*,
            c.company_name,
            i.invoice_number,
            i.date_issued
        FROM accounting_accounts_receivable ar
        JOIN sales_customers c ON ar.customer_id = c.customer_id
        JOIN sales_invoices i ON ar.invoice_id = i.invoice_id
        ORDER BY ar.days_outstanding DESC
    """)
    
    receivables = []
    for row in cursor.fetchall():
        receivables.append({
            'ar_id': row['ar_id'],
            'invoice_id': row['invoice_id'],
            'customer_id': row['customer_id'],
            'company_name': row['company_name'],
            'invoice_number': row['invoice_number'],
            'date_issued': row['date_issued'],
            'amount_outstanding': row['amount_outstanding'],
            'days_outstanding': row['days_outstanding'],
            'aging_bucket': row['aging_bucket'],
            'as_of_date': row['as_of_date']
        })
    
    conn.close()
    return jsonify({'receivables': receivables, 'total': len(receivables)})

@manufacturing_bp.route('/accounting/accounts-payable', methods=['GET'])
def get_accounts_payable():
    """Get accounts payable with vendor details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ap.*,
            v.vendor_name,
            p.purchase_number,
            p.category
        FROM accounting_accounts_payable ap
        JOIN accounting_vendors v ON ap.vendor_id = v.vendor_id
        JOIN accounting_purchases p ON ap.purchase_id = p.purchase_id
        ORDER BY ap.due_date ASC
    """)
    
    payables = []
    for row in cursor.fetchall():
        payables.append({
            'ap_id': row['ap_id'],
            'purchase_id': row['purchase_id'],
            'vendor_id': row['vendor_id'],
            'vendor_name': row['vendor_name'],
            'purchase_number': row['purchase_number'],
            'category': row['category'],
            'amount_outstanding': row['amount_outstanding'],
            'due_date': row['due_date'],
            'days_until_due': row['days_until_due']
        })
    
    conn.close()
    return jsonify({'payables': payables, 'total': len(payables)})

@manufacturing_bp.route('/accounting/kpis', methods=['GET'])
def get_accounting_kpis():
    """Get accounting KPIs and analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # AR aging analysis
    cursor.execute("""
        SELECT 
            aging_bucket,
            COUNT(*) as invoice_count,
            SUM(amount_outstanding) as total_amount
        FROM accounting_accounts_receivable
        GROUP BY aging_bucket
        ORDER BY 
            CASE aging_bucket
                WHEN 'Current' THEN 1
                WHEN '1-30 days' THEN 2
                WHEN '31-60 days' THEN 3
                WHEN '61-90 days' THEN 4
                WHEN '90+ days' THEN 5
            END
    """)
    ar_aging = [dict(row) for row in cursor.fetchall()]
    
    # AP summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_payables,
            SUM(amount_outstanding) as total_amount,
            AVG(days_until_due) as avg_days_until_due
        FROM accounting_accounts_payable
    """)
    ap_summary = dict(cursor.fetchone())
    
    # Purchase categories
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as purchase_count,
            SUM(amount) as total_amount
        FROM accounting_purchases
        GROUP BY category
        ORDER BY total_amount DESC
    """)
    purchase_categories = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'ar_aging': ar_aging,
        'ap_summary': ap_summary,
        'purchase_categories': purchase_categories
    })

# ===================
# OPERATIONS ANALYTICS
# ===================

@manufacturing_bp.route('/operations/products', methods=['GET'])
def get_products():
    """Get all products with production statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.*,
            COUNT(po.order_id) as total_orders,
            COALESCE(SUM(po.units_ordered), 0) as total_units_ordered,
            COALESCE(SUM(po.units_produced), 0) as total_units_produced
        FROM operations_products p
        LEFT JOIN operations_production_orders po ON p.product_id = po.product_id
        GROUP BY p.product_id
        ORDER BY total_units_produced DESC
    """)
    
    products = []
    for row in cursor.fetchall():
        products.append({
            'product_id': row['product_id'],
            'product_code': row['product_code'],
            'product_name': row['product_name'],
            'base_cost': row['base_cost'],
            'labor_hours': row['labor_hours'],
            'material_cost': row['material_cost'],
            'total_orders': row['total_orders'],
            'total_units_ordered': row['total_units_ordered'],
            'total_units_produced': row['total_units_produced']
        })
    
    conn.close()
    return jsonify({'products': products, 'total': len(products)})

@manufacturing_bp.route('/operations/production-orders', methods=['GET'])
def get_production_orders():
    """Get all production orders with product and customer details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            po.*,
            p.product_name,
            p.product_code,
            c.company_name
        FROM operations_production_orders po
        JOIN operations_products p ON po.product_id = p.product_id
        JOIN sales_customers c ON po.customer_id = c.customer_id
        ORDER BY po.start_date DESC
    """)
    
    orders = []
    for row in cursor.fetchall():
        orders.append({
            'order_id': row['order_id'],
            'order_number': row['order_number'],
            'product_id': row['product_id'],
            'product_name': row['product_name'],
            'product_code': row['product_code'],
            'customer_id': row['customer_id'],
            'company_name': row['company_name'],
            'start_date': row['start_date'],
            'completion_date': row['completion_date'],
            'expected_completion': row['expected_completion'],
            'status': row['status'],
            'units_ordered': row['units_ordered'],
            'units_produced': row['units_produced'],
            'cost_of_goods_sold': row['cost_of_goods_sold'],
            'labor_cost': row['labor_cost'],
            'material_cost': row['material_cost']
        })
    
    conn.close()
    return jsonify({'orders': orders, 'total': len(orders)})

@manufacturing_bp.route('/operations/kpis', methods=['GET'])
def get_operations_kpis():
    """Get operations KPIs and analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Production efficiency
    cursor.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(units_ordered) as total_units_ordered,
            SUM(units_produced) as total_units_produced,
            AVG(CASE WHEN units_ordered > 0 THEN (units_produced * 100.0 / units_ordered) END) as avg_efficiency
        FROM operations_production_orders
    """)
    efficiency = dict(cursor.fetchone())
    
    # Status breakdown
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as order_count,
            SUM(units_ordered) as units_ordered,
            SUM(units_produced) as units_produced
        FROM operations_production_orders
        GROUP BY status
    """)
    status_breakdown = [dict(row) for row in cursor.fetchall()]
    
    # Top products by volume
    cursor.execute("""
        SELECT 
            p.product_name,
            SUM(po.units_produced) as total_produced,
            COUNT(po.order_id) as order_count
        FROM operations_products p
        JOIN operations_production_orders po ON p.product_id = po.product_id
        GROUP BY p.product_id
        ORDER BY total_produced DESC
        LIMIT 10
    """)
    top_products = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'efficiency': efficiency,
        'status_breakdown': status_breakdown,
        'top_products': top_products
    })

# ===================
# FINANCE ANALYTICS
# ===================

@manufacturing_bp.route('/finance/cash-ledger', methods=['GET'])
def get_cash_ledger():
    """Get cash ledger with transaction details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT *
        FROM finance_cash_ledger
        ORDER BY date_recorded DESC
    """)
    
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            'transaction_id': row['transaction_id'],
            'transaction_number': row['transaction_number'],
            'date_recorded': row['date_recorded'],
            'amount': row['amount'],
            'transaction_type': row['transaction_type'],
            'counterparty': row['counterparty'],
            'reference_id': row['reference_id'],
            'reference_type': row['reference_type'],
            'description': row['description'],
            'running_balance': row['running_balance']
        })
    
    conn.close()
    return jsonify({'transactions': transactions, 'total': len(transactions)})

@manufacturing_bp.route('/finance/debt-accounts', methods=['GET'])
def get_debt_accounts():
    """Get all debt accounts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT *
        FROM finance_debt_accounts
        ORDER BY outstanding_amount DESC
    """)
    
    debts = []
    for row in cursor.fetchall():
        debts.append({
            'loan_id': row['loan_id'],
            'loan_number': row['loan_number'],
            'loan_type': row['loan_type'],
            'principal_amount': row['principal_amount'],
            'outstanding_amount': row['outstanding_amount'],
            'interest_rate': row['interest_rate'],
            'monthly_payment': row['monthly_payment'],
            'last_payment_date': row['last_payment_date'],
            'next_due_date': row['next_due_date'],
            'loan_start_date': row['loan_start_date'],
            'loan_end_date': row['loan_end_date'],
            'status': row['status']
        })
    
    conn.close()
    return jsonify({'debts': debts, 'total': len(debts)})

@manufacturing_bp.route('/finance/kpis', methods=['GET'])
def get_finance_kpis():
    """Get financial KPIs and analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cash flow analysis
    cursor.execute("""
        SELECT 
            transaction_type,
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount
        FROM finance_cash_ledger
        GROUP BY transaction_type
        ORDER BY total_amount DESC
    """)
    cash_flow_by_type = [dict(row) for row in cursor.fetchall()]
    
    # Monthly cash flow
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', date_recorded) as month,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as inflow,
            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as outflow,
            SUM(amount) as net_flow
        FROM finance_cash_ledger
        GROUP BY month
        ORDER BY month
    """)
    monthly_cash_flow = [dict(row) for row in cursor.fetchall()]
    
    # Debt summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_loans,
            SUM(principal_amount) as total_principal,
            SUM(outstanding_amount) as total_outstanding,
            AVG(interest_rate) as avg_interest_rate,
            SUM(monthly_payment) as total_monthly_payments
        FROM finance_debt_accounts
        WHERE status = 'Active'
    """)
    debt_summary = dict(cursor.fetchone())
    
    conn.close()
    return jsonify({
        'cash_flow_by_type': cash_flow_by_type,
        'monthly_cash_flow': monthly_cash_flow,
        'debt_summary': debt_summary
    })

# ===================
# HR ANALYTICS
# ===================

@manufacturing_bp.route('/hr/employees', methods=['GET'])
def get_employees():
    """Get all employees with payroll summaries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            e.*,
            COUNT(p.payroll_id) as total_pay_periods,
            COALESCE(SUM(p.gross_pay), 0) as total_gross_pay,
            COALESCE(SUM(p.net_pay), 0) as total_net_pay,
            COALESCE(AVG(p.gross_pay), 0) as avg_gross_pay
        FROM hr_employees e
        LEFT JOIN hr_payroll_log p ON e.employee_id = p.employee_id
        GROUP BY e.employee_id
        ORDER BY total_gross_pay DESC
    """)
    
    employees = []
    for row in cursor.fetchall():
        employees.append({
            'employee_id': row['employee_id'],
            'employee_number': row['employee_number'],
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'department': row['department'],
            'position': row['position'],
            'hire_date': row['hire_date'],
            'annual_salary': row['annual_salary'],
            'pay_frequency': row['pay_frequency'],
            'status': row['status'],
            'total_pay_periods': row['total_pay_periods'],
            'total_gross_pay': row['total_gross_pay'],
            'total_net_pay': row['total_net_pay'],
            'avg_gross_pay': row['avg_gross_pay']
        })
    
    conn.close()
    return jsonify({'employees': employees, 'total': len(employees)})

@manufacturing_bp.route('/hr/payroll', methods=['GET'])
def get_payroll():
    """Get payroll records with employee details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.*,
            e.first_name,
            e.last_name,
            e.department,
            e.position
        FROM hr_payroll_log p
        JOIN hr_employees e ON p.employee_id = e.employee_id
        ORDER BY p.pay_date DESC
    """)
    
    payroll = []
    for row in cursor.fetchall():
        payroll.append({
            'payroll_id': row['payroll_id'],
            'employee_id': row['employee_id'],
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'department': row['department'],
            'position': row['position'],
            'pay_period_start': row['pay_period_start'],
            'pay_period_end': row['pay_period_end'],
            'pay_date': row['pay_date'],
            'gross_pay': row['gross_pay'],
            'deductions': row['deductions'],
            'net_pay': row['net_pay'],
            'bonus': row['bonus'],
            'overtime_hours': row['overtime_hours'],
            'overtime_pay': row['overtime_pay']
        })
    
    conn.close()
    return jsonify({'payroll': payroll, 'total': len(payroll)})

@manufacturing_bp.route('/hr/kpis', methods=['GET'])
def get_hr_kpis():
    """Get HR KPIs and analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Employee summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_employees,
            AVG(annual_salary) as avg_salary,
            COUNT(DISTINCT department) as departments
        FROM hr_employees
        WHERE status = 'Active'
    """)
    employee_summary = dict(cursor.fetchone())
    
    # Department breakdown
    cursor.execute("""
        SELECT 
            department,
            COUNT(*) as employee_count,
            AVG(annual_salary) as avg_salary
        FROM hr_employees
        WHERE status = 'Active'
        GROUP BY department
        ORDER BY employee_count DESC
    """)
    department_breakdown = [dict(row) for row in cursor.fetchall()]
    
    # Monthly payroll costs
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', pay_date) as month,
            SUM(gross_pay) as total_gross,
            SUM(deductions) as total_deductions,
            SUM(net_pay) as total_net,
            SUM(overtime_pay) as total_overtime
        FROM hr_payroll_log
        GROUP BY month
        ORDER BY month
    """)
    monthly_payroll = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'employee_summary': employee_summary,
        'department_breakdown': department_breakdown,
        'monthly_payroll': monthly_payroll
    })

# ===================
# EXPENSES ANALYTICS
# ===================

@manufacturing_bp.route('/expenses/fixed-costs', methods=['GET'])
def get_fixed_costs():
    """Get all fixed costs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            fc.*,
            v.vendor_name
        FROM expenses_fixed_costs fc
        LEFT JOIN accounting_vendors v ON fc.vendor_id = v.vendor_id
        ORDER BY fc.amount DESC
    """)
    
    expenses = []
    for row in cursor.fetchall():
        expenses.append({
            'expense_id': row['expense_id'],
            'expense_name': row['expense_name'],
            'category': row['category'],
            'amount': row['amount'],
            'frequency': row['frequency'],
            'due_day': row['due_day'],
            'last_paid_date': row['last_paid_date'],
            'next_due_date': row['next_due_date'],
            'vendor_id': row['vendor_id'],
            'vendor_name': row['vendor_name'],
            'auto_pay': row['auto_pay']
        })
    
    conn.close()
    return jsonify({'expenses': expenses, 'total': len(expenses)})

@manufacturing_bp.route('/expenses/kpis', methods=['GET'])
def get_expenses_kpis():
    """Get expense KPIs and analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Expense summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_expenses,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount
        FROM expenses_fixed_costs
    """)
    expense_summary = dict(cursor.fetchone())
    
    # Category breakdown
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as expense_count,
            SUM(amount) as total_amount
        FROM expenses_fixed_costs
        GROUP BY category
        ORDER BY total_amount DESC
    """)
    category_breakdown = [dict(row) for row in cursor.fetchall()]
    
    # Frequency breakdown
    cursor.execute("""
        SELECT 
            frequency,
            COUNT(*) as expense_count,
            SUM(amount) as total_amount
        FROM expenses_fixed_costs
        GROUP BY frequency
        ORDER BY total_amount DESC
    """)
    frequency_breakdown = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'expense_summary': expense_summary,
        'category_breakdown': category_breakdown,
        'frequency_breakdown': frequency_breakdown
    })

# ===================
# COMPREHENSIVE DASHBOARD
# ===================

@manufacturing_bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get comprehensive dashboard overview with all KPIs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Overall business metrics
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM sales_customers) as total_customers,
            (SELECT SUM(amount) FROM sales_invoices) as total_revenue,
            (SELECT COUNT(*) FROM operations_production_orders) as total_orders,
            (SELECT SUM(units_produced) FROM operations_production_orders) as total_units_produced,
            (SELECT COUNT(*) FROM hr_employees WHERE status = 'Active') as active_employees,
            (SELECT SUM(amount) FROM expenses_fixed_costs) as monthly_fixed_costs,
            (SELECT SUM(outstanding_amount) FROM finance_debt_accounts WHERE status = 'Active') as total_debt,
            (SELECT SUM(amount_outstanding) FROM accounting_accounts_receivable) as total_receivables
    """)
    
    overview = dict(cursor.fetchone())
    
    # Recent activity
    cursor.execute("""
        SELECT 'Invoice' as type, invoice_number as reference, amount, date_issued as date
        FROM sales_invoices
        ORDER BY date_issued DESC
        LIMIT 5
    """)
    recent_invoices = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT 'Production Order' as type, order_number as reference, 
               (cost_of_goods_sold + labor_cost + material_cost) as amount, start_date as date
        FROM operations_production_orders
        ORDER BY start_date DESC
        LIMIT 5
    """)
    recent_orders = [dict(row) for row in cursor.fetchall()]
    
    recent_activity = recent_invoices + recent_orders
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    
    conn.close()
    return jsonify({
        'overview': overview,
        'recent_activity': recent_activity[:10]
    })

if __name__ == '__main__':
    print("Manufacturing Analytics API - All endpoints loaded")
    print("Available endpoints:")
    print("  Sales: /api/manufacturing/sales/")
    print("  Accounting: /api/manufacturing/accounting/")
    print("  Operations: /api/manufacturing/operations/")
    print("  Finance: /api/manufacturing/finance/")
    print("  HR: /api/manufacturing/hr/")
    print("  Expenses: /api/manufacturing/expenses/")
    print("  Dashboard: /api/manufacturing/dashboard/")