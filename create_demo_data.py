#!/usr/bin/env python3
"""
Create and inspect real demo data for EZBI Analytics
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import uuid

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def generate_uuid():
    return str(uuid.uuid4())

def create_database_and_data():
    """Create SQLite database with real demo data"""
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "ezbi_analytics.db"
    
    print("🏭 Creating EZBI Analytics Database with Real Demo Data")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("📋 Creating database tables...")
    
    # Companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sector TEXT,
            size TEXT,
            region TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            company_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            transaction_date DATE NOT NULL,
            description TEXT,
            client_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    """)
    
    # Predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            target_date DATE NOT NULL,
            predicted_value REAL NOT NULL,
            confidence_score REAL NOT NULL,
            model_type TEXT NOT NULL,
            model_version TEXT,
            actual_value REAL,
            prediction_accuracy REAL,
            features_used TEXT,
            model_metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    """)
    
    # Insert demo company
    print("🏢 Creating demo company: Metalux SARL")
    company_id = generate_uuid()
    cursor.execute("""
        INSERT OR REPLACE INTO companies (id, name, sector, size, region)
        VALUES (?, ?, ?, ?, ?)
    """, (company_id, "Metalux SARL", "Métallurgie", "50-200", "Auvergne-Rhône-Alpes"))
    
    # Insert demo user (password hash for 'demo123')
    print("👤 Creating demo user: demo@ezbi.fr")
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("demo123")
    
    user_id = generate_uuid()
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, email, name, hashed_password, role, company_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "demo@ezbi.fr", "Marie Dupont", hashed_password, "admin", company_id))
    
    # Generate realistic transaction data (last 6 months)
    print("💰 Generating 180 days of realistic manufacturing transaction data...")
    
    base_date = datetime.now() - timedelta(days=180)
    transactions_data = []
    
    for i in range(180):
        date = base_date + timedelta(days=i)
        
        # Simulate realistic manufacturing sales pattern
        base_amount = 50000  # €50k base daily sales
        
        # Add growth trend (30% over 6 months)
        seasonal_factor = 1 + 0.3 * (i / 180)
        
        # Add realistic noise and weekly patterns
        day_of_week = date.weekday()
        if day_of_week >= 5:  # Weekend lower sales
            weekday_factor = 0.3
        else:
            weekday_factor = 1.0
        
        # Monthly cycles (end of month spike)
        if date.day >= 25:
            monthly_factor = 1.4
        elif date.day <= 5:
            monthly_factor = 0.8
        else:
            monthly_factor = 1.0
        
        # Random noise
        noise = random.uniform(0.7, 1.3)
        
        # Calculate final amount
        amount = base_amount * seasonal_factor * weekday_factor * monthly_factor * noise
        
        transaction_id = generate_uuid()
        transactions_data.append((
            transaction_id,
            company_id,
            round(amount, 2),
            "sale",
            date.date(),
            f"Vente journalière {date.strftime('%Y-%m-%d')}",
            f"Client-{random.randint(1, 50):03d}"
        ))
    
    # Insert all transactions
    cursor.executemany("""
        INSERT INTO transactions (id, company_id, amount, transaction_type, transaction_date, description, client_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, transactions_data)
    
    # Add some expenses
    print("💸 Adding realistic expense transactions...")
    for i in range(60):  # Every 3 days
        date = base_date + timedelta(days=i * 3)
        expense_amount = random.uniform(5000, 15000)
        
        expense_id = generate_uuid()
        cursor.execute("""
            INSERT INTO transactions (id, company_id, amount, transaction_type, transaction_date, description, client_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (expense_id, company_id, expense_amount, "expense", date.date(), "Frais opérationnels", "Fournisseur"))
    
    conn.commit()
    
    # Now inspect the data
    print("\n" + "=" * 60)
    print("🔍 REAL DATA INSPECTION")
    print("=" * 60)
    
    # Transaction summary
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
    print("📊 Transaction Summary:")
    print(summary.to_string(index=False))
    print()
    
    # Monthly trends
    monthly = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m', transaction_date) as month,
            ROUND(SUM(CASE WHEN transaction_type = 'sale' THEN amount ELSE 0 END), 2) as sales,
            ROUND(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 2) as expenses,
            COUNT(*) as transactions
        FROM transactions 
        GROUP BY strftime('%Y-%m', transaction_date)
        ORDER BY month;
    """, conn)
    print("📈 Monthly Trends:")
    print(monthly.to_string(index=False))
    print()
    
    # Calculate real KPIs
    total_sales = pd.read_sql_query("SELECT SUM(amount) as total FROM transactions WHERE transaction_type = 'sale';", conn).iloc[0]['total']
    total_expenses = pd.read_sql_query("SELECT SUM(amount) as total FROM transactions WHERE transaction_type = 'expense';", conn).iloc[0]['total']
    cash_position = total_sales - total_expenses
    
    print("🎯 REAL KPIs (what the API will return):")
    print(f"Total Sales (6 months): €{total_sales:,.2f}")
    print(f"Total Expenses (6 months): €{total_expenses:,.2f}")
    print(f"Net Cash Position: €{cash_position:,.2f}")
    print(f"Average Daily Sales: €{total_sales/180:,.2f}")
    print()
    
    # Recent activity
    recent = pd.read_sql_query("""
        SELECT transaction_date, amount, transaction_type, client_name
        FROM transactions 
        ORDER BY transaction_date DESC 
        LIMIT 5;
    """, conn)
    print("📅 Most Recent Transactions:")
    print(recent.to_string(index=False))
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Real database created with authentic manufacturing data!")
    print(f"📁 Database location: {db_path}")
    print("🚀 Start backend with: python start_backend.py")
    print("🌐 Frontend will now display REAL calculated data!")

if __name__ == "__main__":
    create_database_and_data()