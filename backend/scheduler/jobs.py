"""Daily data generation jobs"""

import sqlite3
import random
from datetime import datetime, timedelta, date
import uuid
import logging
from typing import Dict, List, Tuple
import os

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DATABASE_PATH', 'data/ezbi_analytics.db')

class DataGenerator:
    def __init__(self):
        self.db_path = DB_PATH
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def generate_daily_transactions(self):
        """Generate daily transactions for all companies"""
        logger.info("Starting daily transaction generation")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all companies
            cursor.execute("SELECT id, name FROM companies")
            companies = cursor.fetchall()
            
            transaction_types = ['income', 'expense', 'transfer', 'investment', 'loan_payment']
            total_generated = 0
            
            for company_id, company_name in companies:
                # Generate 5-20 transactions per company
                num_transactions = random.randint(5, 20)
                
                for _ in range(num_transactions):
                    trans_id = str(uuid.uuid4())
                    trans_type = random.choice(transaction_types)
                    
                    # Generate realistic amounts based on type
                    if trans_type == 'income':
                        amount = round(random.uniform(1000, 50000), 2)
                        client_name = f"Client {random.randint(1, 1000)}"
                    elif trans_type == 'expense':
                        amount = -round(random.uniform(100, 20000), 2)
                        client_name = None
                    elif trans_type == 'loan_payment':
                        amount = -round(random.uniform(1000, 10000), 2)
                        client_name = None
                    else:
                        amount = round(random.uniform(-10000, 10000), 2)
                        client_name = None
                    
                    description = f"{trans_type.title()} - Daily automated entry"
                    trans_date = datetime.now().date()
                    
                    cursor.execute("""
                        INSERT INTO transactions 
                        (id, company_id, amount, transaction_type, transaction_date, 
                         description, client_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (trans_id, company_id, amount, trans_type, trans_date,
                          description, client_name))
                    
                    total_generated += 1
            
            conn.commit()
            logger.info(f"Generated {total_generated} transactions for {len(companies)} companies")
            
        except Exception as e:
            logger.error(f"Error generating transactions: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def generate_daily_invoices(self):
        """Generate new sales invoices"""
        logger.info("Starting daily invoice generation")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get customers and products
            cursor.execute("SELECT customer_id, company_name FROM sales_customers")
            customers = cursor.fetchall()
            
            cursor.execute("SELECT product_id, base_cost FROM operations_products")
            products = cursor.fetchall()
            
            # Generate 10-30 invoices
            num_invoices = random.randint(10, 30)
            
            # Get max invoice number
            cursor.execute("SELECT MAX(CAST(SUBSTR(invoice_number, 5) AS INTEGER)) FROM sales_invoices")
            max_inv_num = cursor.fetchone()[0] or 1000
            
            for i in range(num_invoices):
                customer_id = random.choice(customers)[0]
                invoice_number = f"INV-{max_inv_num + i + 1}"
                date_issued = datetime.now().date()
                
                # Get payment terms for customer
                cursor.execute("SELECT payment_terms FROM sales_customers WHERE customer_id = ?", 
                             (customer_id,))
                payment_terms = cursor.fetchone()[0] or 30
                due_date = date_issued + timedelta(days=payment_terms)
                
                # Calculate invoice amount (1-5 products)
                amount = 0
                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)
                    quantity = random.randint(1, 10)
                    amount += product[1] * quantity * 1.3  # 30% markup
                
                amount = round(amount, 2)
                status = 'Open'
                
                cursor.execute("""
                    INSERT INTO sales_invoices 
                    (customer_id, invoice_number, date_issued, due_date, 
                     amount, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (customer_id, invoice_number, date_issued, due_date,
                      amount, status))
            
            conn.commit()
            logger.info(f"Generated {num_invoices} new invoices")
            
        except Exception as e:
            logger.error(f"Error generating invoices: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def update_accounts_receivable(self):
        """Update accounts receivable aging"""
        logger.info("Starting accounts receivable update")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clear existing AR records
            cursor.execute("DELETE FROM accounting_accounts_receivable")
            
            # Get all unpaid invoices
            cursor.execute("""
                SELECT invoice_id, customer_id, amount, date_issued, due_date, status 
                FROM sales_invoices 
                WHERE status IN ('Open', 'Overdue', 'Partial')
            """)
            unpaid_invoices = cursor.fetchall()
            
            today = datetime.now().date()
            
            for invoice in unpaid_invoices:
                invoice_id, customer_id, amount, date_issued, due_date, status = invoice
                
                # Calculate outstanding amount
                if status == 'Partial':
                    amount_outstanding = round(amount * random.uniform(0.2, 0.7), 2)
                else:
                    amount_outstanding = amount
                
                # Calculate days outstanding
                date_issued_obj = datetime.strptime(date_issued, '%Y-%m-%d').date()
                days_outstanding = (today - date_issued_obj).days
                
                # Update status if overdue
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                if status == 'Open' and today > due_date_obj:
                    cursor.execute("""
                        UPDATE sales_invoices 
                        SET status = 'Overdue' 
                        WHERE invoice_id = ?
                    """, (invoice_id,))
                
                # Determine aging bucket
                if days_outstanding <= 30:
                    aging_bucket = '0-30'
                elif days_outstanding <= 60:
                    aging_bucket = '31-60'
                elif days_outstanding <= 90:
                    aging_bucket = '61-90'
                else:
                    aging_bucket = '90+'
                
                cursor.execute("""
                    INSERT INTO accounting_accounts_receivable 
                    (invoice_id, customer_id, amount_outstanding, days_outstanding, 
                     aging_bucket, as_of_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, customer_id, amount_outstanding, days_outstanding,
                      aging_bucket, today))
            
            conn.commit()
            logger.info(f"Updated {len(unpaid_invoices)} accounts receivable records")
            
        except Exception as e:
            logger.error(f"Error updating accounts receivable: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def generate_daily_purchases(self):
        """Generate new purchase orders"""
        logger.info("Starting daily purchase generation")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT vendor_id, vendor_name FROM accounting_vendors")
            vendors = cursor.fetchall()
            
            categories = ['Raw Materials', 'Equipment', 'Services', 'Utilities', 
                         'Supplies', 'Marketing', 'IT Services']
            
            # Generate 5-15 purchases
            num_purchases = random.randint(5, 15)
            
            # Get max purchase number
            cursor.execute("SELECT MAX(CAST(SUBSTR(purchase_number, 4) AS INTEGER)) FROM accounting_purchases")
            max_po_num = cursor.fetchone()[0] or 2023999
            
            for i in range(num_purchases):
                vendor = random.choice(vendors)
                vendor_id = vendor[0]
                purchase_number = f"PO-{max_po_num + i + 1}"
                category = random.choice(categories)
                
                # Generate amount based on category
                if category == 'Equipment':
                    amount = round(random.uniform(5000, 50000), 2)
                elif category == 'Raw Materials':
                    amount = round(random.uniform(1000, 20000), 2)
                else:
                    amount = round(random.uniform(500, 10000), 2)
                
                date_purchased = datetime.now().date()
                due_date = date_purchased + timedelta(days=30)
                payment_status = 'Outstanding'
                description = f"{category} from {vendor[1]}"
                
                cursor.execute("""
                    INSERT INTO accounting_purchases 
                    (vendor_id, purchase_number, category, amount, date_purchased, 
                     due_date, payment_status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (vendor_id, purchase_number, category, amount, date_purchased,
                      due_date, payment_status, description))
            
            conn.commit()
            logger.info(f"Generated {num_purchases} new purchases")
            
        except Exception as e:
            logger.error(f"Error generating purchases: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def update_accounts_payable(self):
        """Update accounts payable"""
        logger.info("Starting accounts payable update")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clear existing AP records
            cursor.execute("DELETE FROM accounting_accounts_payable")
            
            # Get all unpaid purchases
            cursor.execute("""
                SELECT purchase_id, vendor_id, amount, due_date, payment_status 
                FROM accounting_purchases 
                WHERE payment_status IN ('Outstanding', 'Partial')
            """)
            unpaid_purchases = cursor.fetchall()
            
            today = datetime.now().date()
            
            for purchase in unpaid_purchases:
                purchase_id, vendor_id, amount, due_date_str, payment_status = purchase
                
                # Calculate outstanding amount
                if payment_status == 'Partial':
                    amount_outstanding = round(amount * random.uniform(0.2, 0.7), 2)
                else:
                    amount_outstanding = amount
                
                # Calculate days until due
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                days_until_due = (due_date - today).days
                
                cursor.execute("""
                    INSERT INTO accounting_accounts_payable 
                    (purchase_id, vendor_id, amount_outstanding, due_date, days_until_due)
                    VALUES (?, ?, ?, ?, ?)
                """, (purchase_id, vendor_id, amount_outstanding, due_date, days_until_due))
            
            conn.commit()
            logger.info(f"Updated {len(unpaid_purchases)} accounts payable records")
            
        except Exception as e:
            logger.error(f"Error updating accounts payable: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def process_payroll(self):
        """Process payroll for employees when due"""
        logger.info("Starting payroll processing")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT employee_id, annual_salary, pay_frequency 
                FROM hr_employees 
                WHERE status = 'Active'
            """)
            employees = cursor.fetchall()
            
            today = datetime.now().date()
            payroll_count = 0
            
            for employee_id, annual_salary, pay_frequency in employees:
                # Check last payroll date
                cursor.execute("""
                    SELECT MAX(pay_date) 
                    FROM hr_payroll_log 
                    WHERE employee_id = ?
                """, (employee_id,))
                last_pay = cursor.fetchone()[0]
                
                # Determine if payroll is due
                process_payroll = False
                
                if not last_pay:
                    process_payroll = True
                else:
                    last_pay_date = datetime.strptime(last_pay, '%Y-%m-%d').date()
                    days_since = (today - last_pay_date).days
                    
                    if pay_frequency == 'Bi-weekly' and days_since >= 14:
                        process_payroll = True
                    elif pay_frequency == 'Monthly' and days_since >= 28:
                        process_payroll = True
                
                if process_payroll:
                    # Calculate pay period
                    if pay_frequency == 'Bi-weekly':
                        period_days = 14
                        periods_per_year = 26
                    else:
                        period_days = 30
                        periods_per_year = 12
                    
                    pay_period_end = today - timedelta(days=1)
                    pay_period_start = pay_period_end - timedelta(days=period_days - 1)
                    
                    # Calculate pay
                    gross_per_period = round(annual_salary / periods_per_year, 2)
                    
                    # Random variations
                    overtime_hours = round(random.uniform(0, 10), 2) if random.random() > 0.7 else 0
                    overtime_rate = round(annual_salary / 2080 * 1.5, 2)
                    overtime_pay = round(overtime_hours * overtime_rate, 2)
                    
                    bonus = round(random.uniform(0, 2000), 2) if random.random() > 0.95 else 0
                    
                    # Calculate deductions
                    gross_total = gross_per_period + overtime_pay + bonus
                    deductions = round(gross_total * random.uniform(0.25, 0.30), 2)
                    net_pay = round(gross_total - deductions, 2)
                    
                    cursor.execute("""
                        INSERT INTO hr_payroll_log 
                        (employee_id, pay_period_start, pay_period_end, pay_date,
                         gross_pay, deductions, net_pay, bonus, overtime_hours, overtime_pay)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (employee_id, pay_period_start, pay_period_end, today,
                          gross_per_period, deductions, net_pay, bonus, overtime_hours, overtime_pay))
                    
                    payroll_count += 1
            
            conn.commit()
            logger.info(f"Processed payroll for {payroll_count} employees")
            
        except Exception as e:
            logger.error(f"Error processing payroll: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def update_cash_ledger(self):
        """Update cash ledger with daily entries"""
        logger.info("Starting cash ledger update")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get max transaction number
            cursor.execute("SELECT MAX(CAST(SUBSTR(transaction_number, 4) AS INTEGER)) FROM finance_cash_ledger")
            max_trans_num = cursor.fetchone()[0] or 1000
            
            trans_count = 1
            
            # Add invoice collections
            cursor.execute("""
                SELECT i.invoice_id, i.amount, c.company_name 
                FROM sales_invoices i 
                JOIN sales_customers c ON i.customer_id = c.customer_id
                WHERE i.status = 'Open' 
                AND DATE(i.due_date) <= DATE('now')
                ORDER BY RANDOM() 
                LIMIT 5
            """)
            due_invoices = cursor.fetchall()
            
            for invoice_id, amount, customer in due_invoices:
                # Mark as paid
                cursor.execute("""
                    UPDATE sales_invoices 
                    SET status = 'Paid', payment_date = ? 
                    WHERE invoice_id = ?
                """, (datetime.now().date(), invoice_id))
                
                # Add to cash ledger
                cursor.execute("""
                    INSERT INTO finance_cash_ledger 
                    (transaction_number, date_recorded, amount, transaction_type, 
                     description, source_reference)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"TN-{max_trans_num + trans_count}", datetime.now().date(),
                      amount, 'Deposit', f"Payment from {customer}", f"INV-{invoice_id}"))
                
                trans_count += 1
            
            # Add purchase payments
            cursor.execute("""
                SELECT p.purchase_id, p.amount, v.vendor_name 
                FROM accounting_purchases p 
                JOIN accounting_vendors v ON p.vendor_id = v.vendor_id
                WHERE p.payment_status = 'Outstanding' 
                AND DATE(p.due_date) <= DATE('now', '+7 days')
                ORDER BY RANDOM() 
                LIMIT 3
            """)
            due_purchases = cursor.fetchall()
            
            for purchase_id, amount, vendor in due_purchases:
                # Mark as paid
                cursor.execute("""
                    UPDATE accounting_purchases 
                    SET payment_status = 'Paid', payment_date = ? 
                    WHERE purchase_id = ?
                """, (datetime.now().date(), purchase_id))
                
                # Add to cash ledger
                cursor.execute("""
                    INSERT INTO finance_cash_ledger 
                    (transaction_number, date_recorded, amount, transaction_type, 
                     description, source_reference)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"TN-{max_trans_num + trans_count}", datetime.now().date(),
                      -amount, 'Withdrawal', f"Payment to {vendor}", f"PO-{purchase_id}"))
                
                trans_count += 1
            
            # Add payroll entries
            cursor.execute("""
                SELECT SUM(net_pay) 
                FROM hr_payroll_log 
                WHERE pay_date = ?
            """, (datetime.now().date(),))
            payroll_total = cursor.fetchone()[0]
            
            if payroll_total:
                cursor.execute("""
                    INSERT INTO finance_cash_ledger 
                    (transaction_number, date_recorded, amount, transaction_type, 
                     description, source_reference)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"TN-{max_trans_num + trans_count}", datetime.now().date(),
                      -payroll_total, 'Withdrawal', "Payroll processing", "PAYROLL"))
                trans_count += 1
            
            conn.commit()
            logger.info(f"Added {trans_count - 1} cash ledger entries")
            
        except Exception as e:
            logger.error(f"Error updating cash ledger: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def generate_production_orders(self):
        """Generate new production orders"""
        logger.info("Starting production order generation")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT product_id, product_name FROM operations_products")
            products = cursor.fetchall()
            
            cursor.execute("SELECT customer_id FROM sales_customers")
            customers = [c[0] for c in cursor.fetchall()]
            
            # Generate 3-10 production orders
            num_orders = random.randint(3, 10)
            
            # Get max order number
            cursor.execute("SELECT MAX(CAST(SUBSTR(order_number, 6) AS INTEGER)) FROM operations_production_orders")
            max_order_num = cursor.fetchone()[0] or 1000
            
            for i in range(num_orders):
                product = random.choice(products)
                product_id = product[0]
                customer_id = random.choice(customers)
                order_number = f"PROD-{max_order_num + i + 1}"
                
                start_date = datetime.now().date()
                expected_completion = start_date + timedelta(days=random.randint(5, 30))
                status = 'Planned'
                units_ordered = random.randint(10, 100)
                
                cursor.execute("""
                    INSERT INTO operations_production_orders 
                    (order_number, product_id, customer_id, start_date, 
                     expected_completion, status, units_ordered, units_produced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (order_number, product_id, customer_id, start_date,
                      expected_completion, status, units_ordered, 0))
            
            # Update some existing orders
            cursor.execute("""
                SELECT order_id, units_ordered 
                FROM operations_production_orders 
                WHERE status = 'In Progress'
                ORDER BY RANDOM() 
                LIMIT 5
            """)
            in_progress = cursor.fetchall()
            
            for order_id, units_ordered in in_progress:
                # Progress production
                units_produced = random.randint(int(units_ordered * 0.5), units_ordered)
                
                if units_produced >= units_ordered:
                    status = 'Completed'
                    completion_date = datetime.now().date()
                    
                    # Calculate costs
                    cursor.execute("""
                        SELECT p.base_cost, p.labor_hours, p.material_cost 
                        FROM operations_production_orders o 
                        JOIN operations_products p ON o.product_id = p.product_id 
                        WHERE o.order_id = ?
                    """, (order_id,))
                    
                    base_cost, labor_hours, material_cost = cursor.fetchone()
                    labor_cost = round(labor_hours * 35 * units_ordered, 2)  # $35/hour
                    total_material = round(material_cost * units_ordered, 2)
                    cogs = round((base_cost * units_ordered) + labor_cost + total_material, 2)
                    
                    cursor.execute("""
                        UPDATE operations_production_orders 
                        SET status = ?, units_produced = ?, completion_date = ?,
                            cost_of_goods_sold = ?, labor_cost = ?, material_cost = ?
                        WHERE order_id = ?
                    """, (status, units_produced, completion_date, cogs, 
                          labor_cost, total_material, order_id))
                else:
                    cursor.execute("""
                        UPDATE operations_production_orders 
                        SET units_produced = ? 
                        WHERE order_id = ?
                    """, (units_produced, order_id))
            
            conn.commit()
            logger.info(f"Generated {num_orders} new production orders and updated {len(in_progress)} existing")
            
        except Exception as e:
            logger.error(f"Error generating production orders: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def update_debt_payments(self):
        """Process monthly debt payments"""
        logger.info("Starting debt payment processing")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            
            cursor.execute("""
                SELECT loan_id, loan_number, monthly_payment, outstanding_amount, 
                       next_due_date, principal_amount
                FROM finance_debt_accounts 
                WHERE status = 'Active' 
                AND DATE(next_due_date) <= DATE(?)
            """, (today,))
            due_loans = cursor.fetchall()
            
            for loan in due_loans:
                loan_id, loan_number, monthly_payment, outstanding, next_due_str, principal = loan
                
                if outstanding > 0:
                    # Process payment
                    payment_amount = min(monthly_payment, outstanding)
                    new_outstanding = outstanding - payment_amount
                    
                    # Update loan
                    next_due = datetime.strptime(next_due_str, '%Y-%m-%d').date()
                    new_next_due = next_due + timedelta(days=30)
                    
                    status = 'Active' if new_outstanding > 0 else 'Paid Off'
                    
                    cursor.execute("""
                        UPDATE finance_debt_accounts 
                        SET outstanding_amount = ?, last_payment_date = ?, 
                            next_due_date = ?, status = ?
                        WHERE loan_id = ?
                    """, (new_outstanding, today, new_next_due, status, loan_id))
                    
                    # Add to cash ledger
                    cursor.execute("SELECT MAX(CAST(SUBSTR(transaction_number, 4) AS INTEGER)) FROM finance_cash_ledger")
                    max_trans_num = cursor.fetchone()[0] or 1000
                    
                    cursor.execute("""
                        INSERT INTO finance_cash_ledger 
                        (transaction_number, date_recorded, amount, transaction_type, 
                         description, source_reference)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (f"TN-{max_trans_num + 1}", today, -payment_amount, 
                          'Withdrawal', f"Loan payment - {loan_number}", loan_number))
            
            conn.commit()
            logger.info(f"Processed {len(due_loans)} debt payments")
            
        except Exception as e:
            logger.error(f"Error processing debt payments: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def generate_ai_predictions(self):
        """Generate AI predictions for next 30 days"""
        logger.info("Starting AI predictions generation")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete old predictions
            cursor.execute("""
                DELETE FROM predictions 
                WHERE DATE(target_date) < DATE('now')
            """)
            
            cursor.execute("SELECT id, sector FROM companies")
            companies = cursor.fetchall()
            
            model_types = ['linear_regression', 'random_forest', 'neural_network', 'xgboost']
            
            for company_id, sector in companies:
                # Get historical data for predictions
                cursor.execute("""
                    SELECT AVG(amount) as avg_amount, 
                           COUNT(*) as transaction_count
                    FROM transactions 
                    WHERE company_id = ? 
                    AND transaction_type = 'income'
                    AND DATE(transaction_date) >= DATE('now', '-30 days')
                """, (company_id,))
                
                result = cursor.fetchone()
                avg_income = result[0] if result[0] else 25000
                
                # Generate predictions for next 30 days
                for days_ahead in range(1, 31):
                    pred_id = str(uuid.uuid4())
                    target_date = today + timedelta(days=days_ahead)
                    
                    # Sector-based adjustments
                    if sector == 'Technology':
                        growth_factor = 1.02  # 2% daily growth
                    elif sector == 'Finance':
                        growth_factor = 1.01
                    else:
                        growth_factor = 1.005
                    
                    # Add seasonality
                    day_of_week = target_date.weekday()
                    if day_of_week in [5, 6]:  # Weekend
                        seasonality = 0.7
                    else:
                        seasonality = 1.1
                    
                    # Calculate prediction
                    base_prediction = avg_income * (growth_factor ** days_ahead) * seasonality
                    noise = random.uniform(0.9, 1.1)
                    predicted_value = round(base_prediction * noise, 2)
                    
                    # Confidence decreases with time
                    confidence = round(0.95 - (days_ahead * 0.01), 3)
                    
                    model_type = random.choice(model_types)
                    model_version = f"v2.{random.randint(0, 5)}"
                    features = "revenue_history,seasonal_patterns,market_trends,sector_analysis"
                    metadata = f'{{"training_samples": {random.randint(5000, 10000)}, "rmse": {round(random.uniform(0.03, 0.08), 3)}}}'
                    
                    cursor.execute("""
                        INSERT INTO predictions 
                        (id, company_id, target_date, predicted_value, confidence_score,
                         model_type, model_version, features_used, model_metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (pred_id, company_id, target_date, predicted_value, confidence,
                          model_type, model_version, features, metadata))
            
            conn.commit()
            logger.info(f"Generated predictions for {len(companies)} companies")
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def cleanup_old_data(self):
        """Archive old data beyond retention period"""
        logger.info("Starting data cleanup")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Keep 1 year of transaction data
            retention_date = datetime.now().date() - timedelta(days=365)
            
            cursor.execute("""
                DELETE FROM transactions 
                WHERE DATE(transaction_date) < ?
            """, (retention_date,))
            transactions_deleted = cursor.rowcount
            
            # Keep 2 years of invoice data
            invoice_retention = datetime.now().date() - timedelta(days=730)
            
            cursor.execute("""
                DELETE FROM sales_invoices 
                WHERE DATE(date_issued) < ? 
                AND status = 'Paid'
            """, (invoice_retention,))
            invoices_deleted = cursor.rowcount
            
            # Keep 6 months of predictions
            prediction_retention = datetime.now().date() - timedelta(days=180)
            
            cursor.execute("""
                DELETE FROM predictions 
                WHERE DATE(created_at) < ?
            """, (prediction_retention,))
            predictions_deleted = cursor.rowcount
            
            conn.commit()
            logger.info(f"Cleanup complete: {transactions_deleted} transactions, "
                       f"{invoices_deleted} invoices, {predictions_deleted} predictions deleted")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

# Instantiate the data generator
data_generator = DataGenerator()

# Job functions for scheduler
def generate_daily_transactions_job():
    """Scheduled job for daily transactions"""
    try:
        data_generator.generate_daily_transactions()
    except Exception as e:
        logger.error(f"Daily transaction job failed: {e}")

def generate_daily_invoices_job():
    """Scheduled job for daily invoices"""
    try:
        data_generator.generate_daily_invoices()
    except Exception as e:
        logger.error(f"Daily invoice job failed: {e}")

def update_accounts_receivable_job():
    """Scheduled job for AR update"""
    try:
        data_generator.update_accounts_receivable()
    except Exception as e:
        logger.error(f"AR update job failed: {e}")

def generate_daily_purchases_job():
    """Scheduled job for daily purchases"""
    try:
        data_generator.generate_daily_purchases()
    except Exception as e:
        logger.error(f"Daily purchase job failed: {e}")

def update_accounts_payable_job():
    """Scheduled job for AP update"""
    try:
        data_generator.update_accounts_payable()
    except Exception as e:
        logger.error(f"AP update job failed: {e}")

def process_payroll_job():
    """Scheduled job for payroll processing"""
    try:
        data_generator.process_payroll()
    except Exception as e:
        logger.error(f"Payroll job failed: {e}")

def update_cash_ledger_job():
    """Scheduled job for cash ledger update"""
    try:
        data_generator.update_cash_ledger()
    except Exception as e:
        logger.error(f"Cash ledger job failed: {e}")

def generate_production_orders_job():
    """Scheduled job for production orders"""
    try:
        data_generator.generate_production_orders()
    except Exception as e:
        logger.error(f"Production order job failed: {e}")

def update_debt_payments_job():
    """Scheduled job for debt payments"""
    try:
        data_generator.update_debt_payments()
    except Exception as e:
        logger.error(f"Debt payment job failed: {e}")

def generate_ai_predictions_job():
    """Scheduled job for AI predictions"""
    try:
        data_generator.generate_ai_predictions()
    except Exception as e:
        logger.error(f"AI prediction job failed: {e}")

def cleanup_old_data_job():
    """Scheduled job for data cleanup"""
    try:
        data_generator.cleanup_old_data()
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}")