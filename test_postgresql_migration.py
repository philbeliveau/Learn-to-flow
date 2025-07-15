#!/usr/bin/env python3
"""
PostgreSQL Migration Test Suite
=============================

This script tests the PostgreSQL migration implementation
to ensure all components work correctly before production deployment.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from postgresql_migration import PostgreSQLMigrator, DatabaseConfig
    from postgresql_config import PostgreSQLConfig, EnhancedConnectionPool
    from postgresql_backup_system import PostgreSQLBackupSystem, BackupConfig
    from manufacturing_models import Base, get_table_schemas
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all migration files are in the same directory")
    sys.exit(1)

class MigrationTestSuite:
    """Test suite for PostgreSQL migration."""
    
    def __init__(self):
        self.test_results = []
        self.db_config = DatabaseConfig()
        self.backup_config = BackupConfig()
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {message}")
        
    async def test_database_connection(self):
        """Test database connection."""
        try:
            config = PostgreSQLConfig()
            pool = EnhancedConnectionPool(config)
            await pool.initialize()
            
            # Test basic connection
            async with pool.get_session() as session:
                await session.execute("SELECT 1")
            
            await pool.close()
            self.log_test("Database Connection", True, "Connection successful")
            
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
    
    async def test_table_schemas(self):
        """Test table schema definitions."""
        try:
            schemas = get_table_schemas()
            manufacturing_tables = [
                'sales_customers', 'sales_invoices', 'accounting_vendors',
                'accounting_purchases', 'accounting_accounts_receivable',
                'accounting_accounts_payable', 'operations_products',
                'operations_production_orders', 'finance_cash_ledger',
                'finance_debt_accounts', 'expenses_fixed_costs',
                'hr_employees', 'hr_payroll_log'
            ]
            
            for table in manufacturing_tables:
                if table not in schemas:
                    self.log_test("Table Schemas", False, f"Missing table: {table}")
                    return
            
            self.log_test("Table Schemas", True, f"All {len(manufacturing_tables)} tables defined")
            
        except Exception as e:
            self.log_test("Table Schemas", False, str(e))
    
    async def test_migration_system(self):
        """Test migration system initialization."""
        try:
            # Test migrator initialization
            migrator = PostgreSQLMigrator(self.db_config)
            await migrator.initialize_pool()
            
            # Test table discovery
            tables = migrator.get_manufacturing_tables()
            
            if migrator.pool:
                await migrator.pool.close()
            
            self.log_test("Migration System", True, f"Found {len(tables)} manufacturing tables")
            
        except Exception as e:
            self.log_test("Migration System", False, str(e))
    
    async def test_backup_system(self):
        """Test backup system initialization."""
        try:
            backup_system = PostgreSQLBackupSystem(self.backup_config)
            
            # Test directory creation
            backup_system._setup_directories()
            
            # Test connection check
            await backup_system._check_prerequisites()
            
            self.log_test("Backup System", True, "Backup system initialized")
            
        except Exception as e:
            self.log_test("Backup System", False, str(e))
    
    async def test_performance_queries(self):
        """Test performance monitoring queries."""
        try:
            from manufacturing_models import MANUFACTURING_PERFORMANCE_QUERIES
            
            query_count = len(MANUFACTURING_PERFORMANCE_QUERIES)
            
            # Verify query syntax (basic check)
            for query_name, query_sql in MANUFACTURING_PERFORMANCE_QUERIES.items():
                if not query_sql.strip():
                    self.log_test("Performance Queries", False, f"Empty query: {query_name}")
                    return
            
            self.log_test("Performance Queries", True, f"All {query_count} queries defined")
            
        except Exception as e:
            self.log_test("Performance Queries", False, str(e))
    
    def test_file_permissions(self):
        """Test file permissions and existence."""
        try:
            required_files = [
                'postgresql_migration.py',
                'postgresql_config.py',
                'manufacturing_models.py',
                'postgresql_backup_system.py',
                'deploy_postgresql_migration.sh'
            ]
            
            missing_files = []
            for file_name in required_files:
                file_path = Path(__file__).parent / file_name
                if not file_path.exists():
                    missing_files.append(file_name)
                elif not os.access(file_path, os.R_OK):
                    missing_files.append(f"{file_name} (not readable)")
            
            if missing_files:
                self.log_test("File Permissions", False, f"Missing files: {', '.join(missing_files)}")
            else:
                self.log_test("File Permissions", True, f"All {len(required_files)} files present")
                
        except Exception as e:
            self.log_test("File Permissions", False, str(e))
    
    def test_environment_variables(self):
        """Test environment variable configuration."""
        try:
            required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER']
            optional_vars = ['DB_PASSWORD', 'BACKUP_ROOT', 'ALERT_EMAIL']
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.log_test("Environment Variables", False, f"Missing: {', '.join(missing_vars)}")
            else:
                optional_count = sum(1 for var in optional_vars if os.getenv(var))
                self.log_test("Environment Variables", True, 
                            f"Required vars set, {optional_count}/{len(optional_vars)} optional vars set")
                
        except Exception as e:
            self.log_test("Environment Variables", False, str(e))
    
    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("PostgreSQL Migration Test Suite")
        print("=" * 60)
        
        # Run tests
        self.test_file_permissions()
        self.test_environment_variables()
        await self.test_table_schemas()
        await self.test_performance_queries()
        await self.test_database_connection()
        await self.test_migration_system()
        await self.test_backup_system()
        
        # Generate report
        self.generate_test_report()
        
        # Print summary
        self.print_summary()
        
        return all(result['status'] == 'PASS' for result in self.test_results)
    
    def generate_test_report(self):
        """Generate test report."""
        report = {
            'test_suite': 'PostgreSQL Migration Test Suite',
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'results': self.test_results
        }
        
        # Save report
        report_path = Path(__file__).parent / 'test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nTest report saved to: {report_path}")
    
    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\nRECOMMENDATIONS:")
        if failed == 0:
            print("  ✅ All tests passed! Ready for migration deployment.")
        else:
            print("  ⚠️  Fix failed tests before proceeding with migration.")
            print("  📖 Check the test report for detailed error information.")
            print("  🔧 Ensure database connection and environment variables are configured.")
        
        print("=" * 60)

async def main():
    """Main test function."""
    # Set default environment variables for testing
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '5432')
    os.environ.setdefault('DB_NAME', 'ezbi_analytics')
    os.environ.setdefault('DB_USER', 'postgres')
    os.environ.setdefault('DB_PASSWORD', 'password')
    
    test_suite = MigrationTestSuite()
    success = await test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())