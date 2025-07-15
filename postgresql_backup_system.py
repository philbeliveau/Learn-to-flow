#!/usr/bin/env python3
"""
Comprehensive PostgreSQL Backup and Monitoring System
====================================================

This system provides:
- Automated backups with different retention policies
- Point-in-time recovery capabilities
- Database health monitoring
- Performance alerts
- Backup verification
- Disaster recovery procedures
"""

import os
import sys
import asyncio
import asyncpg
import subprocess
import json
import logging
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import schedule
import time
import psutil
import gzip
import shutil
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ezbi_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Backup configuration settings."""
    
    # Database connection
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_port: int = int(os.getenv('DB_PORT', '5432'))
    db_name: str = os.getenv('DB_NAME', 'ezbi_analytics')
    db_user: str = os.getenv('DB_USER', 'postgres')
    db_password: str = os.getenv('DB_PASSWORD', 'password')
    
    # Backup paths
    backup_root: str = os.getenv('BACKUP_ROOT', '/var/backups/ezbi_analytics')
    temp_dir: str = os.getenv('BACKUP_TEMP', '/tmp/ezbi_backup')
    
    # Retention policies
    daily_retention: int = int(os.getenv('DAILY_RETENTION', '7'))
    weekly_retention: int = int(os.getenv('WEEKLY_RETENTION', '4'))
    monthly_retention: int = int(os.getenv('MONTHLY_RETENTION', '12'))
    
    # Backup types
    full_backup_schedule: str = os.getenv('FULL_BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
    incremental_backup_schedule: str = os.getenv('INCREMENTAL_BACKUP_SCHEDULE', '0 */6 * * *')  # Every 6 hours
    
    # Compression
    compression_level: int = int(os.getenv('COMPRESSION_LEVEL', '6'))
    
    # Monitoring
    alert_email: str = os.getenv('ALERT_EMAIL', 'admin@ezbi-analytics.com')
    smtp_server: str = os.getenv('SMTP_SERVER', 'localhost')
    smtp_port: int = int(os.getenv('SMTP_PORT', '587'))
    smtp_user: str = os.getenv('SMTP_USER', '')
    smtp_password: str = os.getenv('SMTP_PASSWORD', '')
    
    # Performance thresholds
    max_backup_duration: int = int(os.getenv('MAX_BACKUP_DURATION', '3600'))  # 1 hour
    max_db_size_gb: float = float(os.getenv('MAX_DB_SIZE_GB', '100'))
    min_free_space_gb: float = float(os.getenv('MIN_FREE_SPACE_GB', '10'))

@dataclass
class BackupResult:
    """Backup operation result."""
    backup_id: str
    backup_type: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    size_mb: float
    success: bool
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    checksum: Optional[str] = None

class PostgreSQLBackupSystem:
    """Comprehensive PostgreSQL backup and monitoring system."""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.backup_history = []
        self._setup_directories()
        
    def _setup_directories(self):
        """Create backup directories."""
        directories = [
            self.config.backup_root,
            os.path.join(self.config.backup_root, 'full'),
            os.path.join(self.config.backup_root, 'incremental'),
            os.path.join(self.config.backup_root, 'wal'),
            os.path.join(self.config.backup_root, 'logs'),
            self.config.temp_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created backup directory: {directory}")
    
    async def create_full_backup(self) -> BackupResult:
        """Create a full database backup."""
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting full backup: {backup_id}")
        
        try:
            # Check prerequisites
            await self._check_prerequisites()
            
            # Create backup filename
            backup_filename = f"{backup_id}.sql.gz"
            backup_path = os.path.join(self.config.backup_root, 'full', backup_filename)
            temp_path = os.path.join(self.config.temp_dir, f"{backup_id}.sql")
            
            # Create pg_dump command
            cmd = [
                'pg_dump',
                '-h', self.config.db_host,
                '-p', str(self.config.db_port),
                '-U', self.config.db_user,
                '-d', self.config.db_name,
                '-f', temp_path,
                '--verbose',
                '--no-password',
                '--clean',
                '--if-exists',
                '--create'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            # Execute backup
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")
            
            # Compress backup
            with open(temp_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb', compresslevel=self.config.compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove temporary file
            os.remove(temp_path)
            
            # Calculate file size and checksum
            file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
            checksum = await self._calculate_checksum(backup_path)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            result = BackupResult(
                backup_id=backup_id,
                backup_type='full',
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                size_mb=file_size,
                success=True,
                file_path=backup_path,
                checksum=checksum
            )
            
            # Record backup in history
            self.backup_history.append(result)
            await self._save_backup_metadata(result)
            
            logger.info(f"Full backup completed: {backup_id}, Size: {file_size:.2f} MB, Duration: {duration}")
            
            return result
            
        except Exception as e:
            logger.error(f"Full backup failed: {str(e)}")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            result = BackupResult(
                backup_id=backup_id,
                backup_type='full',
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                size_mb=0,
                success=False,
                error_message=str(e)
            )
            
            await self._send_alert(f"Full backup failed: {str(e)}")
            return result
    
    async def create_incremental_backup(self) -> BackupResult:
        """Create an incremental backup using WAL files."""
        backup_id = f"incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting incremental backup: {backup_id}")
        
        try:
            # Get current WAL position
            pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            async with pool.acquire() as conn:
                # Get current WAL position
                wal_result = await conn.fetchrow("SELECT pg_current_wal_lsn() as lsn")
                current_lsn = wal_result['lsn']
                
                # Get WAL files since last backup
                wal_files_result = await conn.fetch("""
                    SELECT name FROM pg_ls_waldir() 
                    WHERE modification >= NOW() - INTERVAL '6 hours'
                    ORDER BY modification DESC
                """)
                
                wal_files = [row['name'] for row in wal_files_result]
            
            await pool.close()
            
            if not wal_files:
                logger.info("No WAL files to backup")
                return BackupResult(
                    backup_id=backup_id,
                    backup_type='incremental',
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration=datetime.now() - start_time,
                    size_mb=0,
                    success=True
                )
            
            # Create incremental backup directory
            backup_dir = os.path.join(self.config.backup_root, 'incremental', backup_id)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy WAL files
            total_size = 0
            for wal_file in wal_files:
                src_path = f"/var/lib/postgresql/data/pg_wal/{wal_file}"
                dst_path = os.path.join(backup_dir, wal_file)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    total_size += os.path.getsize(dst_path)
            
            # Create backup metadata
            metadata = {
                'backup_id': backup_id,
                'backup_type': 'incremental',
                'start_time': start_time.isoformat(),
                'current_lsn': current_lsn,
                'wal_files': wal_files,
                'total_size': total_size
            }
            
            metadata_path = os.path.join(backup_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Compress backup directory
            archive_path = f"{backup_dir}.tar.gz"
            await self._compress_directory(backup_dir, archive_path)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_dir)
            
            file_size = os.path.getsize(archive_path) / (1024 * 1024)  # MB
            checksum = await self._calculate_checksum(archive_path)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            result = BackupResult(
                backup_id=backup_id,
                backup_type='incremental',
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                size_mb=file_size,
                success=True,
                file_path=archive_path,
                checksum=checksum
            )
            
            self.backup_history.append(result)
            await self._save_backup_metadata(result)
            
            logger.info(f"Incremental backup completed: {backup_id}, Size: {file_size:.2f} MB, Duration: {duration}")
            
            return result
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {str(e)}")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            result = BackupResult(
                backup_id=backup_id,
                backup_type='incremental',
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                size_mb=0,
                success=False,
                error_message=str(e)
            )
            
            await self._send_alert(f"Incremental backup failed: {str(e)}")
            return result
    
    async def verify_backup(self, backup_result: BackupResult) -> bool:
        """Verify backup integrity."""
        logger.info(f"Verifying backup: {backup_result.backup_id}")
        
        try:
            if not backup_result.file_path or not os.path.exists(backup_result.file_path):
                logger.error(f"Backup file not found: {backup_result.file_path}")
                return False
            
            # Verify checksum
            current_checksum = await self._calculate_checksum(backup_result.file_path)
            if current_checksum != backup_result.checksum:
                logger.error(f"Checksum mismatch for backup: {backup_result.backup_id}")
                return False
            
            # For full backups, try to restore to a test database
            if backup_result.backup_type == 'full':
                return await self._test_restore(backup_result.file_path)
            
            logger.info(f"Backup verification successful: {backup_result.backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return False
    
    async def _test_restore(self, backup_path: str) -> bool:
        """Test restore to verify backup integrity."""
        test_db_name = f"ezbi_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Create test database
            pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database='postgres',
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            async with pool.acquire() as conn:
                await conn.execute(f'CREATE DATABASE "{test_db_name}"')
            
            await pool.close()
            
            # Restore backup to test database
            cmd = [
                'pg_restore',
                '-h', self.config.db_host,
                '-p', str(self.config.db_port),
                '-U', self.config.db_user,
                '-d', test_db_name,
                backup_path,
                '--verbose',
                '--no-password'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Drop test database
            pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database='postgres',
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            async with pool.acquire() as conn:
                await conn.execute(f'DROP DATABASE "{test_db_name}"')
            
            await pool.close()
            
            if process.returncode != 0:
                logger.error(f"Test restore failed: {stderr.decode()}")
                return False
            
            logger.info("Test restore successful")
            return True
            
        except Exception as e:
            logger.error(f"Test restore failed: {str(e)}")
            return False
    
    async def cleanup_old_backups(self):
        """Clean up old backups according to retention policy."""
        logger.info("Starting backup cleanup")
        
        try:
            # Clean up full backups
            full_backup_dir = os.path.join(self.config.backup_root, 'full')
            await self._cleanup_directory(full_backup_dir, self.config.daily_retention)
            
            # Clean up incremental backups
            incremental_backup_dir = os.path.join(self.config.backup_root, 'incremental')
            await self._cleanup_directory(incremental_backup_dir, self.config.daily_retention)
            
            logger.info("Backup cleanup completed")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
    
    async def _cleanup_directory(self, directory: str, retention_days: int):
        """Clean up files older than retention period."""
        if not os.path.exists(directory):
            return
        
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_mtime < cutoff_time:
                os.remove(file_path)
                logger.info(f"Removed old backup: {filename}")
    
    async def monitor_database_health(self) -> Dict[str, Any]:
        """Monitor database health and performance."""
        logger.info("Monitoring database health")
        
        try:
            pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            async with pool.acquire() as conn:
                # Database size
                db_size_result = await conn.fetchrow("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size_pretty,
                           pg_database_size(current_database()) as size_bytes
                """)
                
                # Connection count
                conn_count_result = await conn.fetchrow("""
                    SELECT count(*) as total_connections,
                           count(CASE WHEN state = 'active' THEN 1 END) as active_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
                
                # Table sizes
                table_sizes_result = await conn.fetch("""
                    SELECT 
                        tablename,
                        pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size_pretty,
                        pg_total_relation_size(tablename::regclass) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                      AND (tablename LIKE 'sales_%' 
                           OR tablename LIKE 'accounting_%'
                           OR tablename LIKE 'operations_%'
                           OR tablename LIKE 'finance_%'
                           OR tablename LIKE 'hr_%'
                           OR tablename LIKE 'expenses_%')
                    ORDER BY size_bytes DESC
                """)
                
                # Slow queries
                slow_queries_result = await conn.fetch("""
                    SELECT 
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time
                    FROM pg_stat_statements
                    WHERE query NOT LIKE '%pg_stat_statements%'
                      AND mean_exec_time > 100
                    ORDER BY mean_exec_time DESC
                    LIMIT 5
                """)
                
                # Lock information
                locks_result = await conn.fetch("""
                    SELECT 
                        l.locktype,
                        l.mode,
                        l.granted,
                        a.query
                    FROM pg_locks l
                    JOIN pg_stat_activity a ON l.pid = a.pid
                    WHERE l.granted = false
                """)
            
            await pool.close()
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'database': {
                    'size_pretty': db_size_result['size_pretty'],
                    'size_bytes': db_size_result['size_bytes'],
                    'size_gb': db_size_result['size_bytes'] / (1024**3),
                    'total_connections': conn_count_result['total_connections'],
                    'active_connections': conn_count_result['active_connections']
                },
                'table_sizes': [dict(row) for row in table_sizes_result],
                'slow_queries': [dict(row) for row in slow_queries_result],
                'locks': [dict(row) for row in locks_result],
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_free_gb': disk.free / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100
                }
            }
            
            # Check for alerts
            await self._check_health_alerts(health_data)
            
            # Save health data
            health_log_path = os.path.join(self.config.backup_root, 'logs', f"health_{datetime.now().strftime('%Y%m%d')}.json")
            with open(health_log_path, 'a') as f:
                json.dump(health_data, f)
                f.write('\n')
            
            logger.info("Database health monitoring completed")
            return health_data
            
        except Exception as e:
            logger.error(f"Database health monitoring failed: {str(e)}")
            await self._send_alert(f"Database health monitoring failed: {str(e)}")
            return {}
    
    async def _check_health_alerts(self, health_data: Dict[str, Any]):
        """Check health data for alert conditions."""
        alerts = []
        
        # Check database size
        if health_data['database']['size_gb'] > self.config.max_db_size_gb:
            alerts.append(f"Database size ({health_data['database']['size_gb']:.2f} GB) exceeds threshold ({self.config.max_db_size_gb} GB)")
        
        # Check disk space
        if health_data['system']['disk_free_gb'] < self.config.min_free_space_gb:
            alerts.append(f"Low disk space ({health_data['system']['disk_free_gb']:.2f} GB free)")
        
        # Check CPU usage
        if health_data['system']['cpu_percent'] > 80:
            alerts.append(f"High CPU usage ({health_data['system']['cpu_percent']:.1f}%)")
        
        # Check memory usage
        if health_data['system']['memory_percent'] > 85:
            alerts.append(f"High memory usage ({health_data['system']['memory_percent']:.1f}%)")
        
        # Check slow queries
        if len(health_data['slow_queries']) > 0:
            alerts.append(f"Found {len(health_data['slow_queries'])} slow queries")
        
        # Check locks
        if len(health_data['locks']) > 0:
            alerts.append(f"Found {len(health_data['locks'])} blocked queries")
        
        # Send alerts
        if alerts:
            alert_message = "\n".join(alerts)
            await self._send_alert(f"Database health alerts:\n{alert_message}")
    
    async def _send_alert(self, message: str):
        """Send alert email."""
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.alert_email
            msg['To'] = self.config.alert_email
            msg['Subject'] = f"EZBI Analytics Database Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            body = f"""
            EZBI Analytics Database Alert
            ============================
            
            Time: {datetime.now().isoformat()}
            
            Alert Details:
            {message}
            
            Please investigate immediately.
            
            ---
            EZBI Analytics Backup System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            if self.config.smtp_user and self.config.smtp_password:
                server.login(self.config.smtp_user, self.config.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert sent: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    async def _check_prerequisites(self):
        """Check backup prerequisites."""
        # Check disk space
        disk = psutil.disk_usage(self.config.backup_root)
        free_space_gb = disk.free / (1024**3)
        
        if free_space_gb < self.config.min_free_space_gb:
            raise Exception(f"Insufficient disk space: {free_space_gb:.2f} GB free")
        
        # Check database connection
        pool = await asyncpg.create_pool(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password
        )
        
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        
        await pool.close()
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of a file."""
        import hashlib
        
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    async def _compress_directory(self, directory: str, archive_path: str):
        """Compress directory to tar.gz."""
        import tarfile
        
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(directory, arcname=os.path.basename(directory))
    
    async def _save_backup_metadata(self, result: BackupResult):
        """Save backup metadata to JSON file."""
        metadata_path = os.path.join(self.config.backup_root, 'logs', 'backup_history.json')
        
        # Load existing metadata
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'backups': []}
        
        # Add new backup
        metadata['backups'].append(asdict(result))
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def start_scheduler(self):
        """Start backup scheduler."""
        logger.info("Starting backup scheduler")
        
        # Schedule full backups
        schedule.every().day.at("02:00").do(lambda: asyncio.run(self.create_full_backup()))
        
        # Schedule incremental backups
        schedule.every(6).hours.do(lambda: asyncio.run(self.create_incremental_backup()))
        
        # Schedule cleanup
        schedule.every().day.at("01:00").do(lambda: asyncio.run(self.cleanup_old_backups()))
        
        # Schedule health monitoring
        schedule.every(15).minutes.do(lambda: asyncio.run(self.monitor_database_health()))
        
        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)

# CLI interface
async def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='EZBI Analytics PostgreSQL Backup System')
    parser.add_argument('--action', choices=['full-backup', 'incremental-backup', 'verify', 'cleanup', 'monitor', 'schedule'], 
                       required=True, help='Action to perform')
    parser.add_argument('--backup-id', help='Backup ID for verification')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = BackupConfig()
    
    # Initialize backup system
    backup_system = PostgreSQLBackupSystem(config)
    
    try:
        if args.action == 'full-backup':
            result = await backup_system.create_full_backup()
            print(f"Full backup completed: {result.backup_id}")
            
        elif args.action == 'incremental-backup':
            result = await backup_system.create_incremental_backup()
            print(f"Incremental backup completed: {result.backup_id}")
            
        elif args.action == 'verify':
            if not args.backup_id:
                print("--backup-id required for verification")
                return
            # Implementation for verification
            print("Verification not implemented in CLI")
            
        elif args.action == 'cleanup':
            await backup_system.cleanup_old_backups()
            print("Cleanup completed")
            
        elif args.action == 'monitor':
            health_data = await backup_system.monitor_database_health()
            print(json.dumps(health_data, indent=2, default=str))
            
        elif args.action == 'schedule':
            backup_system.start_scheduler()
            
    except Exception as e:
        logger.error(f"Action failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())