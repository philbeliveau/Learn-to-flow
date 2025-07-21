#!/usr/bin/env python3
"""
Production Database Migration Script
Migrates manufacturing database to Railway PostgreSQL
"""
import asyncio
import sys
import os
from pathlib import Path

# Add app root to path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import init_db, get_async_session
from alembic import command
from alembic.config import Config
import structlog

logger = structlog.get_logger()

async def migrate_database():
    """Run database migrations for production"""
    
    print("🔄 Starting Railway Database Migration...")
    print(f"📊 Target Database: {settings.DATABASE_URL}")
    
    try:
        # Check if running in Railway environment
        if "railway" in settings.DATABASE_URL.lower() or "postgres" in settings.DATABASE_URL:
            print("✅ Railway PostgreSQL environment detected")
        else:
            print("⚠️ Warning: Not running against Railway database")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled")
                return
        
        # Initialize database connection
        print("🔗 Initializing database connection...")
        await init_db()
        
        # Run Alembic migrations
        print("📋 Running Alembic migrations...")
        alembic_cfg = Config("alembic.ini")
        
        # Override database URL for production
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+aiosqlite", ""))
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database schema migration completed")
        
        # Test database connection
        print("🔍 Testing database connection...")
        async with get_async_session() as db:
            result = await db.execute(text("SELECT 1 as test"))
            test_row = result.fetchone()
            if test_row:
                print("✅ Database connection successful")
        
        # Import manufacturing data if needed
        from jobs.daily_data_generation import ManufacturingDataGenerator
        
        print("📊 Checking for existing manufacturing data...")
        async with get_async_session() as db:
            # Check if customers table has data
            customers_result = await db.execute(text("SELECT COUNT(*) FROM sales.customers"))
            customer_count = customers_result.scalar()
            
            if customer_count == 0:
                print("📊 No existing data found. Generating initial manufacturing data...")
                generator = ManufacturingDataGenerator()
                await generator.generate_initial_data()
                print("✅ Initial manufacturing data generated")
            else:
                print(f"✅ Found {customer_count} existing customers. Database populated.")
        
        print("🎉 Railway database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logger.error("Migration failed", error=str(e))
        sys.exit(1)

async def populate_sample_data():
    """Populate database with sample manufacturing data"""
    
    print("📊 Populating sample manufacturing data...")
    
    try:
        from jobs.daily_data_generation import ManufacturingDataGenerator
        
        generator = ManufacturingDataGenerator()
        
        # Generate 30 days of historical data
        print("📈 Generating 30 days of historical data...")
        for i in range(30):
            await generator.generate_daily_data()
            if i % 5 == 0:
                print(f"Progress: {i+1}/30 days generated...")
        
        print("✅ Sample data population completed")
        
    except Exception as e:
        print(f"❌ Data population failed: {e}")
        logger.error("Data population failed", error=str(e))

async def verify_migration():
    """Verify the migration was successful"""
    
    print("🔍 Verifying database migration...")
    
    try:
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # Check all manufacturing tables exist
            tables_to_check = [
                'sales.customers',
                'sales.invoices',
                'accounting.vendors',
                'accounting.accounts_receivable',
                'accounting.accounts_payable',
                'operations.products',
                'operations.production_orders',
                'finance.cash_ledger',
                'finance.debt_accounts',
                'expenses.fixed_costs',
                'hr.employees',
                'hr.payroll_log'
            ]
            
            print("🔍 Checking manufacturing tables...")
            for table in tables_to_check:
                try:
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"✅ {table}: {count} records")
                except Exception as e:
                    print(f"❌ {table}: Error - {e}")
            
        print("✅ Database verification completed")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        logger.error("Verification failed", error=str(e))

async def main():
    """Main migration function"""
    
    if len(sys.argv) > 1:
        command_arg = sys.argv[1]
        
        if command_arg == "migrate":
            await migrate_database()
        elif command_arg == "populate":
            await populate_sample_data()
        elif command_arg == "verify":
            await verify_migration()
        elif command_arg == "full":
            await migrate_database()
            await populate_sample_data()
            await verify_migration()
        else:
            print("Usage: python migrate_production.py [migrate|populate|verify|full]")
            sys.exit(1)
    else:
        # Default: full migration
        await migrate_database()
        await populate_sample_data()
        await verify_migration()

if __name__ == "__main__":
    asyncio.run(main())