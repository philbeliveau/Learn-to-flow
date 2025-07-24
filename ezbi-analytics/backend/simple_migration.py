#!/usr/bin/env python3
"""
Simple migration: Copy key manufacturing tables to PostgreSQL
Focus on the most important tables first
"""

import sqlite3
import psycopg2
from pathlib import Path

POSTGRES_URL = "postgresql://postgres:cnaAFVnruvkBnnzxCDxUEkfedixdbCHH@yamanote.proxy.rlwy.net:25571/railway"

def migrate_key_tables():
    """Migrate the most important manufacturing tables"""
    
    # Key tables with their expected record counts
    key_tables = {
        'sales_customers': 50,
        'sales_invoices': 300,
        'operations_products': 20,
        'finance_cash_ledger': 500,
        'hr_employees': 30,
        'accounting_vendors': 25,
        'operations_production_orders': 150
    }
    
    # Connect to databases
    sqlite_conn = sqlite3.connect("data/ezbi_analytics.db")
    postgres_conn = psycopg2.connect(POSTGRES_URL)
    postgres_conn.autocommit = True
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    print("🚀 Migrating Key Manufacturing Tables")
    print("=" * 40)
    
    for table_name, expected_count in key_tables.items():
        try:
            print(f"📊 Migrating {table_name}...")
            
            # Drop and recreate table
            postgres_cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            
            # Get SQLite data
            sqlite_cursor.execute(f"SELECT * FROM {table_name};")
            rows = sqlite_cursor.fetchall()
            
            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            if not rows:
                print(f"⚠️ No data in {table_name}")
                continue
            
            # Create simple table structure
            create_sql = f"CREATE TABLE {table_name} ("
            create_sql += ", ".join([f"{col} TEXT" for col in columns])
            create_sql += ");"
            
            postgres_cursor.execute(create_sql)
            
            # Insert data (all as TEXT to avoid type issues)
            placeholders = ','.join(['%s'] * len(columns))
            columns_str = ','.join(columns)
            
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            postgres_cursor.executemany(insert_query, rows)
            
            print(f"✅ Migrated {len(rows)} records to {table_name}")
            
        except Exception as e:
            print(f"❌ Error with {table_name}: {e}")
            continue
    
    print("\n🎉 Key tables migration complete!")
    
    # Verify migration
    print("\n📋 Verification:")
    for table_name in key_tables.keys():
        try:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = postgres_cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
        except:
            print(f"   - {table_name}: ❌ Not found")
    
    sqlite_conn.close()
    postgres_conn.close()

if __name__ == "__main__":
    migrate_key_tables()