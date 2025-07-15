#!/usr/bin/env python3
"""
PostgreSQL Migration Script for EZBI Analytics Manufacturing Database
=================================================================

This script migrates the SQLite manufacturing database to PostgreSQL
with production-ready configuration including:
- Connection pooling
- Performance indexes
- Automated backups
- Data integrity validation
- Rollback procedures
"""

import sqlite3
import asyncio
import asyncpg
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import sys
import os
import hashlib
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgresql_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration for PostgreSQL migration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "ezbi_analytics"
    username: str = "postgres"
    password: str = "password"
    
    # Connection pool settings
    min_pool_size: int = 10
    max_pool_size: int = 20
    pool_timeout: int = 30
    
    # Performance settings
    shared_buffers: str = "256MB"
    effective_cache_size: str = "1GB"
    maintenance_work_mem: str = "64MB"
    checkpoint_completion_target: float = 0.9
    wal_buffers: str = "16MB"
    default_statistics_target: int = 100
    random_page_cost: float = 1.1
    effective_io_concurrency: int = 200

class PostgreSQLMigrator:
    """Comprehensive PostgreSQL migration utility."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.sqlite_path = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/data/ezbi_analytics.db"
        self.pool = None
        self.migration_start_time = datetime.now()
        self.validation_results = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_pool()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.pool:
            await self.pool.close()
    
    async def initialize_pool(self):
        """Initialize PostgreSQL connection pool."""
        logger.info("Initializing PostgreSQL connection pool...")
        
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                command_timeout=self.config.pool_timeout,
                server_settings={
                    'application_name': 'EZBI_Analytics_Migration',
                    'timezone': 'UTC',
                }
            )
            logger.info(f"Connection pool initialized with {self.config.min_pool_size}-{self.config.max_pool_size} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def get_manufacturing_tables(self) -> List[str]:
        """Get all manufacturing tables from SQLite database."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Filter for manufacturing tables
        manufacturing_tables = [
            table for table in all_tables
            if any(prefix in table for prefix in ['sales_', 'accounting_', 'operations_', 'finance_', 'hr_', 'expenses_'])
            and 'backup' not in table
        ]
        
        conn.close()
        return manufacturing_tables
    
    async def setup_postgresql_database(self):
        """Setup PostgreSQL database with optimized configuration."""
        logger.info("Setting up PostgreSQL database...")
        
        async with self.pool.acquire() as conn:
            # Create extensions
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")
            
            # Set performance configuration
            performance_settings = {
                'shared_buffers': self.config.shared_buffers,
                'effective_cache_size': self.config.effective_cache_size,
                'maintenance_work_mem': self.config.maintenance_work_mem,
                'checkpoint_completion_target': str(self.config.checkpoint_completion_target),
                'wal_buffers': self.config.wal_buffers,
                'default_statistics_target': str(self.config.default_statistics_target),
                'random_page_cost': str(self.config.random_page_cost),
                'effective_io_concurrency': str(self.config.effective_io_concurrency)
            }
            
            for setting, value in performance_settings.items():
                try:
                    await conn.execute(f"ALTER SYSTEM SET {setting} = '{value}'")
                    logger.info(f"Set {setting} = {value}")
                except Exception as e:
                    logger.warning(f"Could not set {setting}: {e}")
            
            # Reload configuration
            await conn.execute("SELECT pg_reload_conf()")
            
            logger.info("PostgreSQL database setup completed")
    
    def get_sqlite_schema(self, table_name: str) -> Dict[str, Any]:
        """Get SQLite table schema and convert to PostgreSQL equivalent."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        
        # Convert SQLite types to PostgreSQL types
        type_mapping = {
            'INTEGER': 'SERIAL',
            'TEXT': 'VARCHAR(255)',
            'REAL': 'DECIMAL(15,2)',
            'BLOB': 'BYTEA',
            'DATETIME': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME'
        }
        
        pg_columns = []
        for col in columns:
            col_name = col[1]
            col_type = col[2].upper()
            is_nullable = not col[3]
            default_value = col[4]
            is_pk = col[5]
            
            # Map SQLite type to PostgreSQL type
            pg_type = type_mapping.get(col_type, 'TEXT')
            
            # Handle primary key
            if is_pk and col_type == 'INTEGER':
                pg_type = 'SERIAL PRIMARY KEY'
            
            column_def = f"{col_name} {pg_type}"
            
            if not is_nullable and not is_pk:
                column_def += " NOT NULL"
            
            if default_value:
                column_def += f" DEFAULT '{default_value}'"
            
            pg_columns.append(column_def)
        
        # Get row count for migration planning
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'columns': pg_columns,
            'indexes': indexes,
            'row_count': row_count
        }
    
    async def create_postgresql_table(self, table_name: str, schema: Dict[str, Any]):
        """Create PostgreSQL table with optimized schema."""
        logger.info(f"Creating PostgreSQL table: {table_name}")
        
        async with self.pool.acquire() as conn:
            # Drop table if exists
            await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            # Create table
            columns_sql = ",\n  ".join(schema['columns'])
            create_sql = f"""
            CREATE TABLE {table_name} (
              {columns_sql}
            )
            """
            
            await conn.execute(create_sql)
            logger.info(f"Created table {table_name} with {len(schema['columns'])} columns")
            
            # Create performance indexes
            await self.create_performance_indexes(table_name)
    
    async def create_performance_indexes(self, table_name: str):
        """Create performance indexes for manufacturing tables."""
        logger.info(f"Creating performance indexes for {table_name}")
        
        async with self.pool.acquire() as conn:
            # Common indexes based on table patterns
            if 'sales_' in table_name:
                if 'customer' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_customer_id ON {table_name}(customer_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at)")
                elif 'invoices' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_customer_id ON {table_name}(customer_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date_issued ON {table_name}(date_issued)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_payment_date ON {table_name}(payment_date)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status)")
            
            elif 'accounting_' in table_name:
                if 'accounts_receivable' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_invoice_id ON {table_name}(invoice_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_customer_id ON {table_name}(customer_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_aging_bucket ON {table_name}(aging_bucket)")
                elif 'accounts_payable' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_vendor_id ON {table_name}(vendor_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_due_date ON {table_name}(due_date)")
            
            elif 'finance_' in table_name:
                if 'cash_ledger' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date_recorded ON {table_name}(date_recorded)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_transaction_type ON {table_name}(transaction_type)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_reference ON {table_name}(reference_id, reference_type)")
                elif 'debt_accounts' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_account_type ON {table_name}(account_type)")
            
            elif 'operations_' in table_name:
                if 'production_orders' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_product_id ON {table_name}(product_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_customer_id ON {table_name}(customer_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_start_date ON {table_name}(start_date)")
                elif 'products' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_product_code ON {table_name}(product_code)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_category ON {table_name}(category)")
            
            elif 'hr_' in table_name:
                if 'employees' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_employee_id ON {table_name}(employee_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_department ON {table_name}(department)")
                elif 'payroll' in table_name:
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_employee_id ON {table_name}(employee_id)")
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_payroll_date ON {table_name}(payroll_date)")
            
            elif 'expenses_' in table_name:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_expense_type ON {table_name}(expense_type)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date_incurred ON {table_name}(date_incurred)")
            
            logger.info(f"Created performance indexes for {table_name}")
    
    async def migrate_table_data(self, table_name: str, batch_size: int = 1000):
        """Migrate table data from SQLite to PostgreSQL with batching."""
        logger.info(f"Migrating data for table: {table_name}")
        
        # Get SQLite data
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Get total rows for progress tracking
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        
        if total_rows == 0:
            logger.info(f"No data to migrate for {table_name}")
            conn.close()
            return
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Migrate data in batches
        offset = 0
        migrated_rows = 0
        
        while offset < total_rows:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
            batch_data = cursor.fetchall()
            
            if not batch_data:
                break
            
            # Insert batch into PostgreSQL
            async with self.pool.acquire() as pg_conn:
                placeholders = ','.join(['$' + str(i) for i in range(1, len(columns) + 1)])
                insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                
                await pg_conn.executemany(insert_sql, batch_data)
                migrated_rows += len(batch_data)
                
                logger.info(f"Migrated {migrated_rows}/{total_rows} rows for {table_name}")
            
            offset += batch_size
        
        conn.close()
        logger.info(f"Completed migration for {table_name}: {migrated_rows} rows")
    
    async def validate_migration(self, table_name: str) -> Dict[str, Any]:
        """Validate data migration integrity."""
        logger.info(f"Validating migration for {table_name}")
        
        # Get SQLite row count and data sample
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        # Get data hash for integrity check
        sqlite_cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid")
        sqlite_data = sqlite_cursor.fetchall()
        sqlite_hash = hashlib.md5(str(sqlite_data).encode()).hexdigest()
        
        sqlite_conn.close()
        
        # Get PostgreSQL row count and data sample
        async with self.pool.acquire() as pg_conn:
            pg_count = await pg_conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            
            # Get data hash for integrity check
            pg_data = await pg_conn.fetch(f"SELECT * FROM {table_name} ORDER BY ctid")
            pg_hash = hashlib.md5(str(pg_data).encode()).hexdigest()
        
        validation_result = {
            'table_name': table_name,
            'sqlite_count': sqlite_count,
            'postgresql_count': pg_count,
            'count_match': sqlite_count == pg_count,
            'sqlite_hash': sqlite_hash,
            'postgresql_hash': pg_hash,
            'data_integrity': sqlite_hash == pg_hash,
            'validation_time': datetime.now().isoformat()
        }
        
        self.validation_results[table_name] = validation_result
        logger.info(f"Validation for {table_name}: Count match={validation_result['count_match']}, Data integrity={validation_result['data_integrity']}")
        
        return validation_result
    
    async def setup_automated_backups(self):
        """Setup automated backup strategy."""
        logger.info("Setting up automated backup strategy...")
        
        backup_script = f"""#!/bin/bash
# Automated PostgreSQL backup script for EZBI Analytics
# Generated by PostgreSQL migrator

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/ezbi_analytics"
DB_NAME="{self.config.database}"
DB_USER="{self.config.username}"
DB_HOST="{self.config.host}"
DB_PORT="{self.config.port}"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $BACKUP_DIR/full_backup_$DATE.sql

# Compressed backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/full_backup_$DATE.sql.gz

# Manufacturing tables backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t 'sales_*' -t 'accounting_*' -t 'operations_*' -t 'finance_*' -t 'hr_*' -t 'expenses_*' -f $BACKUP_DIR/manufacturing_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql*" -mtime +30 -delete

# Log backup completion
echo "$(date): Backup completed successfully" >> /var/log/ezbi_backup.log
"""
        
        # Write backup script
        backup_script_path = Path("postgresql_backup.sh")
        backup_script_path.write_text(backup_script)
        backup_script_path.chmod(0o755)
        
        logger.info("Automated backup script created: postgresql_backup.sh")
        
        # Create cron job suggestion
        cron_job = """
# Add this to your crontab (crontab -e) for daily backups at 2 AM
0 2 * * * /path/to/postgresql_backup.sh

# For hourly backups during business hours (9 AM - 5 PM)
0 9-17 * * * /path/to/postgresql_backup.sh
"""
        
        with open("cron_backup_setup.txt", "w") as f:
            f.write(cron_job)
        
        logger.info("Cron job configuration saved to cron_backup_setup.txt")
    
    async def setup_monitoring(self):
        """Setup database monitoring and health checks."""
        logger.info("Setting up database monitoring...")
        
        monitoring_script = f"""#!/usr/bin/env python3
# Database monitoring script for EZBI Analytics PostgreSQL
# Generated by PostgreSQL migrator

import asyncio
import asyncpg
import json
import logging
from datetime import datetime

async def check_database_health():
    \"\"\"Check database health and performance metrics.\"\"\"
    
    pool = await asyncpg.create_pool(
        host="{self.config.host}",
        port={self.config.port},
        database="{self.config.database}",
        user="{self.config.username}",
        password="{self.config.password}"
    )
    
    async with pool.acquire() as conn:
        # Check connection
        result = await conn.fetchval("SELECT 1")
        
        # Get database size
        db_size = await conn.fetchval(\"\"\"
            SELECT pg_size_pretty(pg_database_size(current_database()))
        \"\"\")
        
        # Get table sizes
        table_sizes = await conn.fetch(\"\"\"
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(tablename::regclass) DESC
        \"\"\")
        
        # Get connection stats
        connections = await conn.fetch(\"\"\"
            SELECT 
                state,
                COUNT(*) as count
            FROM pg_stat_activity
            WHERE datname = current_database()
            GROUP BY state
        \"\"\")
        
        # Get query performance
        slow_queries = await conn.fetch(\"\"\"
            SELECT 
                query,
                calls,
                total_time,
                mean_time
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY total_time DESC
            LIMIT 5
        \"\"\")
        
        metrics = {{
            'timestamp': datetime.now().isoformat(),
            'database_size': db_size,
            'table_sizes': [dict(row) for row in table_sizes],
            'connections': [dict(row) for row in connections],
            'slow_queries': [dict(row) for row in slow_queries]
        }}
        
        # Write metrics to file
        with open('/var/log/ezbi_db_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Database health check completed: {{metrics['timestamp']}}")
        print(f"Database size: {{db_size}}")
        print(f"Active connections: {{len(connections)}}")
        
    await pool.close()

if __name__ == "__main__":
    asyncio.run(check_database_health())
"""
        
        # Write monitoring script
        monitoring_script_path = Path("postgresql_monitoring.py")
        monitoring_script_path.write_text(monitoring_script)
        monitoring_script_path.chmod(0o755)
        
        logger.info("Database monitoring script created: postgresql_monitoring.py")
    
    async def create_rollback_procedures(self):
        """Create rollback procedures for migration."""
        logger.info("Creating rollback procedures...")
        
        rollback_script = f"""#!/bin/bash
# Rollback script for PostgreSQL migration
# Generated by PostgreSQL migrator

echo "Starting rollback procedure..."

# 1. Backup current PostgreSQL state
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/ezbi_analytics/rollback"
mkdir -p $BACKUP_DIR

pg_dump -h {self.config.host} -p {self.config.port} -U {self.config.username} -d {self.config.database} -f $BACKUP_DIR/pre_rollback_$DATE.sql

# 2. Drop PostgreSQL manufacturing tables
psql -h {self.config.host} -p {self.config.port} -U {self.config.username} -d {self.config.database} -c "
DROP TABLE IF EXISTS sales_customers CASCADE;
DROP TABLE IF EXISTS sales_invoices CASCADE;
DROP TABLE IF EXISTS accounting_vendors CASCADE;
DROP TABLE IF EXISTS accounting_purchases CASCADE;
DROP TABLE IF EXISTS accounting_accounts_receivable CASCADE;
DROP TABLE IF EXISTS accounting_accounts_payable CASCADE;
DROP TABLE IF EXISTS operations_products CASCADE;
DROP TABLE IF EXISTS operations_production_orders CASCADE;
DROP TABLE IF EXISTS finance_cash_ledger CASCADE;
DROP TABLE IF EXISTS finance_debt_accounts CASCADE;
DROP TABLE IF EXISTS expenses_fixed_costs CASCADE;
DROP TABLE IF EXISTS hr_employees CASCADE;
DROP TABLE IF EXISTS hr_payroll_log CASCADE;
"

# 3. Restore from SQLite if needed
echo "Manufacturing tables dropped from PostgreSQL"
echo "Original SQLite database is still available at: {self.sqlite_path}"
echo "Rollback completed at: $(date)"
"""
        
        # Write rollback script
        rollback_script_path = Path("postgresql_rollback.sh")
        rollback_script_path.write_text(rollback_script)
        rollback_script_path.chmod(0o755)
        
        logger.info("Rollback script created: postgresql_rollback.sh")
    
    async def run_migration(self):
        """Run the complete migration process."""
        logger.info("=== Starting PostgreSQL Migration ===")
        
        try:
            # 1. Setup PostgreSQL database
            await self.setup_postgresql_database()
            
            # 2. Get manufacturing tables
            tables = self.get_manufacturing_tables()
            logger.info(f"Found {len(tables)} manufacturing tables to migrate: {tables}")
            
            # 3. Migrate each table
            for table_name in tables:
                try:
                    # Get schema
                    schema = self.get_sqlite_schema(table_name)
                    
                    # Create PostgreSQL table
                    await self.create_postgresql_table(table_name, schema)
                    
                    # Migrate data
                    await self.migrate_table_data(table_name)
                    
                    # Validate migration
                    await self.validate_migration(table_name)
                    
                except Exception as e:
                    logger.error(f"Failed to migrate table {table_name}: {e}")
                    raise
            
            # 4. Setup automated backups
            await self.setup_automated_backups()
            
            # 5. Setup monitoring
            await self.setup_monitoring()
            
            # 6. Create rollback procedures
            await self.create_rollback_procedures()
            
            # 7. Generate migration report
            await self.generate_migration_report()
            
            logger.info("=== PostgreSQL Migration Completed Successfully ===")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def generate_migration_report(self):
        """Generate comprehensive migration report."""
        migration_end_time = datetime.now()
        migration_duration = migration_end_time - self.migration_start_time
        
        report = {
            'migration_summary': {
                'start_time': self.migration_start_time.isoformat(),
                'end_time': migration_end_time.isoformat(),
                'duration': str(migration_duration),
                'status': 'SUCCESS'
            },
            'database_config': {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'pool_size': f"{self.config.min_pool_size}-{self.config.max_pool_size}",
                'performance_optimized': True
            },
            'migrated_tables': list(self.validation_results.keys()),
            'validation_results': self.validation_results,
            'features_implemented': [
                'Connection pooling with optimized settings',
                'Performance indexes for all manufacturing tables',
                'Automated backup strategy',
                'Database monitoring and health checks',
                'Rollback procedures',
                'Data integrity validation',
                'PostgreSQL performance optimization'
            ],
            'files_created': [
                'postgresql_backup.sh',
                'postgresql_monitoring.py',
                'postgresql_rollback.sh',
                'cron_backup_setup.txt',
                'postgresql_migration.log'
            ]
        }
        
        # Write report
        report_path = Path("postgresql_migration_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Migration report saved to: {report_path}")
        
        # Print summary
        print("\n=== MIGRATION SUMMARY ===")
        print(f"Duration: {migration_duration}")
        print(f"Tables migrated: {len(self.validation_results)}")
        print(f"All validations passed: {all(r['count_match'] and r['data_integrity'] for r in self.validation_results.values())}")
        print(f"Report saved to: {report_path}")

async def main():
    """Main migration function."""
    # Database configuration
    config = DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'ezbi_analytics'),
        username=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    
    # Run migration
    async with PostgreSQLMigrator(config) as migrator:
        await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())