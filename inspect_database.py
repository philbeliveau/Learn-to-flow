#!/usr/bin/env python3
"""
Inspect the real data in our EZBI Analytics database
"""

import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

def inspect_database():
    """Inspect the SQLite database and show real data"""
    
    db_path = Path("data/ezbi_analytics.db")
    
    if not db_path.exists():
        print("❌ Database not found. Run backend first to create demo data.")
        return
    
    print("🔍 EZBI Analytics Database Inspection")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    
    # Show tables
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print(f"📊 Tables in database: {list(tables['name'])}")
    print()
    
    # Companies data
    print("🏭 COMPANIES DATA:")
    companies = pd.read_sql_query("SELECT * FROM companies;", conn)
    print(companies.to_string(index=False))
    print()
    
    # Users data
    print("👤 USERS DATA:")
    users = pd.read_sql_query("SELECT id, name, email, role, company_id FROM users;", conn)
    print(users.to_string(index=False))
    print()
    
    # Transactions data (sample)
    print("💰 TRANSACTIONS DATA (last 10 records):")
    transactions = pd.read_sql_query("""
        SELECT transaction_date, amount, transaction_type, description, client_name 
        FROM transactions 
        ORDER BY transaction_date DESC 
        LIMIT 10;
    """, conn)
    print(transactions.to_string(index=False))
    print()
    
    # Transaction summary
    print("📈 TRANSACTION SUMMARY:")
    summary = pd.read_sql_query("""
        SELECT 
            transaction_type,
            COUNT(*) as count,
            ROUND(SUM(amount), 2) as total_amount,
            ROUND(AVG(amount), 2) as avg_amount,
            MIN(transaction_date) as earliest_date,
            MAX(transaction_date) as latest_date
        FROM transactions 
        GROUP BY transaction_type;
    """, conn)
    print(summary.to_string(index=False))
    print()
    
    # Monthly sales trend
    print("📊 MONTHLY SALES TREND:")
    monthly = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m', transaction_date) as month,
            ROUND(SUM(amount), 2) as total_sales,
            COUNT(*) as transaction_count
        FROM transactions 
        WHERE transaction_type = 'sale'
        GROUP BY strftime('%Y-%m', transaction_date)
        ORDER BY month;
    """, conn)
    print(monthly.to_string(index=False))
    print()
    
    # KPIs calculation (what the API returns)
    print("🎯 REAL KPIs CALCULATION:")
    total_sales = pd.read_sql_query("SELECT SUM(amount) as total FROM transactions WHERE transaction_type = 'sale';", conn).iloc[0]['total']
    total_expenses = pd.read_sql_query("SELECT SUM(amount) as total FROM transactions WHERE transaction_type IN ('purchase', 'expense');", conn).iloc[0]['total'] or 0
    cash_position = total_sales - total_expenses
    transaction_count = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions;", conn).iloc[0]['count']
    
    print(f"Total Sales: €{total_sales:,.2f}")
    print(f"Total Expenses: €{total_expenses:,.2f}")
    print(f"Cash Position: €{cash_position:,.2f}")
    print(f"Total Transactions: {transaction_count}")
    print()
    
    # Predictions data (if any)
    print("🔮 PREDICTIONS DATA:")
    try:
        predictions = pd.read_sql_query("SELECT * FROM predictions ORDER BY created_at DESC LIMIT 5;", conn)
        if len(predictions) > 0:
            print(predictions.to_string(index=False))
        else:
            print("No predictions generated yet. Generate one via the API!")
    except:
        print("No predictions table yet.")
    
    conn.close()
    print("\n" + "=" * 50)
    print("✅ Database inspection complete!")

if __name__ == "__main__":
    inspect_database()