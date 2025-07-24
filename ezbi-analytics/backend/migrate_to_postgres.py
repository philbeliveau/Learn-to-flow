#!/usr/bin/env python3
"""
Migrate ezbi_analytics.db (SQLite) to Railway PostgreSQL database
Transfers all 15 manufacturing tables with complete data
"""

import sqlite3
import psycopg2
import os
from pathlib import Path
import sys

# Railway PostgreSQL connection
POSTGRES_URL = "postgresql://postgres:cnaAFVnruvkBnnzxCDxUEkfedixdbCHH@yamanote.proxy.rlwy.net:25571/railway"

def get_sqlite_connection():
    """Get SQLite connection to local database"""
    sqlite_path = Path("data/ezbi_analytics.db")
    if not sqlite_path.exists():
        print(f"❌ SQLite database not found at {sqlite_path}")
        return None
    
    return sqlite3.connect(sqlite_path)

def get_postgres_connection():
    """Get PostgreSQL connection to Railway database"""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def get_table_schema(sqlite_cursor, table_name):
    """Get CREATE TABLE statement from SQLite"""
    sqlite_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    result = sqlite_cursor.fetchone()
    return result[0] if result else None

def convert_sqlite_to_postgres_schema(sqlite_schema):
    """Convert SQLite schema to PostgreSQL compatible schema"""
    # Basic conversions
    postgres_schema = sqlite_schema.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
    postgres_schema = postgres_schema.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')
    postgres_schema = postgres_schema.replace('TEXT', 'VARCHAR')
    postgres_schema = postgres_schema.replace('REAL', 'DECIMAL')
    postgres_schema = postgres_schema.replace('DATETIME', 'TIMESTAMP')
    postgres_schema = postgres_schema.replace('BOOLEAN', 'BOOLEAN')
    
    return postgres_schema

def convert_sqlite_row_data(row, columns, sqlite_cursor, table_name):
    """Convert SQLite row data to PostgreSQL compatible format"""
    # Get column types
    sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
    column_info = {col[1]: col[2] for col in sqlite_cursor.fetchall()}
    
    converted_row = []
    for i, value in enumerate(row):
        column_name = columns[i]
        column_type = column_info.get(column_name, '').upper()
        
        # Convert boolean values
        if 'BOOLEAN' in column_type and value is not None:
            converted_row.append(bool(value))
        else:
            converted_row.append(value)
    
    return tuple(converted_row)

def migrate_table(sqlite_cursor, postgres_cursor, table_name):
    """Migrate a single table from SQLite to PostgreSQL"""
    print(f"📊 Migrating table: {table_name}")
    
    try:
        # Get table schema
        schema = get_table_schema(sqlite_cursor, table_name)
        if not schema:
            print(f"❌ Could not get schema for {table_name}")
            return False
        
        # Convert schema to PostgreSQL
        postgres_schema = convert_sqlite_to_postgres_schema(schema)
        
        # Drop table if exists and create new one
        postgres_cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        postgres_cursor.execute(postgres_schema)
        
        # Get all data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name};")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"⚠️ No data in {table_name}")
            return True
        
        # Get column names
        sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        # Convert data for PostgreSQL compatibility
        converted_rows = [convert_sqlite_row_data(row, columns, sqlite_cursor, table_name) for row in rows]
        
        # Insert data into PostgreSQL
        placeholders = ','.join(['%s'] * len(columns))
        columns_str = ','.join(columns)
        
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        postgres_cursor.executemany(insert_query, converted_rows)
        
        print(f"✅ Migrated {len(rows)} records to {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating {table_name}: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # Connect to databases
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        sys.exit(1)
    
    postgres_conn = get_postgres_connection()
    if not postgres_conn:
        sys.exit(1)
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables to migrate:")
        for table in tables:
            print(f"   - {table}")
        
        print("\n🔄 Starting migration...")
        
        successful_migrations = 0
        
        # Migrate each table
        for table in tables:
            if migrate_table(sqlite_cursor, postgres_cursor, table):
                successful_migrations += 1
            
        # Commit all changes
        postgres_conn.commit()
        
        print("\n" + "=" * 50)
        print(f"✅ Migration Complete!")
        print(f"📊 Successfully migrated {successful_migrations}/{len(tables)} tables")
        print(f"🗄️ PostgreSQL database ready at Railway")
        
        if successful_migrations == len(tables):
            print("🎉 All manufacturing data successfully migrated!")
        else:
            print(f"⚠️ {len(tables) - successful_migrations} tables had issues")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        postgres_conn.rollback()
        sys.exit(1)
        
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    main()