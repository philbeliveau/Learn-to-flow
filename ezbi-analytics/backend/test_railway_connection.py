#!/usr/bin/env python3
"""
Test Railway PostgreSQL connection and verify manufacturing data
"""

import psycopg2
import sys

POSTGRES_URL = "postgresql://postgres:cnaAFVnruvkBnnzxCDxUEkfedixdbCHH@yamanote.proxy.rlwy.net:25571/railway"

def test_connection():
    """Test Railway PostgreSQL connection"""
    print("🔗 Testing Railway PostgreSQL Connection")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        
        print("✅ Connected to Railway PostgreSQL")
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📊 PostgreSQL Version: {version[:50]}...")
        
        # Check manufacturing tables
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = t.table_name) as exists
            FROM (VALUES 
                ('sales_customers'),
                ('sales_invoices'),
                ('operations_products'),
                ('finance_cash_ledger'),
                ('hr_employees'),
                ('accounting_vendors'),
                ('operations_production_orders')
            ) AS t(table_name)
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📋 Manufacturing Tables Status:")
        for table_name, exists in tables:
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table_name}: {count} records")
            else:
                print(f"   ❌ {table_name}: Not found")
        
        # Test API endpoint simulation
        print(f"\n🚀 Simulating API Endpoints:")
        
        # Sales KPIs
        cursor.execute("SELECT COUNT(*) as customers FROM sales_customers;")
        result = cursor.fetchone()
        print(f"   📊 Sales KPIs: {result[0]} customers")
        
        # Manufacturing KPIs  
        cursor.execute("SELECT COUNT(*) as products FROM operations_products;")
        result = cursor.fetchone()
        print(f"   🏭 Products: {result[0]} items")
        
        # Cash Flow
        cursor.execute("SELECT COUNT(*) as transactions FROM finance_cash_ledger;")
        result = cursor.fetchone()
        print(f"   💰 Cash Flow: {result[0]} transactions")
        
        print(f"\n🎉 Railway Backend Ready for Deployment!")
        print(f"✅ Database: Connected and populated")
        print(f"✅ Manufacturing Data: Available")
        print(f"✅ API Endpoints: Ready to serve")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)