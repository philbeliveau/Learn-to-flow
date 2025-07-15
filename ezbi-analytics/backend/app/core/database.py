from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine, event, text
from contextlib import asynccontextmanager
import structlog
from typing import AsyncGenerator, Optional, Dict, Any, List
from datetime import datetime
import json
import os

from app.core.config import settings

# Configure logger
logger = structlog.get_logger()

# Create async engine with enhanced configuration
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DATABASE_ECHO,
    echo_pool=bool(os.getenv('DB_ECHO_POOL', 'false').lower() == 'true'),
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hour for production
    pool_reset_on_return='commit',
    connect_args={
        'server_settings': {
            'application_name': 'EZBI_Analytics_Production',
            'timezone': 'UTC',
            'statement_timeout': '30000',  # 30 seconds
            'idle_in_transaction_session_timeout': '60000',  # 60 seconds
            'log_statement': 'all',
            'log_min_duration_statement': '1000',  # Log queries > 1 second
        }
    }
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.sync_database_url,
    echo=settings.DATABASE_ECHO,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_reset_on_return='commit',
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Create sync session maker for migrations
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Database models base class
Base = declarative_base()

# Database connection events
@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(async_engine.sync_engine, "engine_connect")
def receive_engine_connect(dbapi_connection, connection_record):
    """Log database connections."""
    logger.info("Database connection established")

@event.listens_for(async_engine.sync_engine, "engine_dispose")
def receive_engine_dispose(dbapi_connection, connection_record):
    """Log database disconnections."""
    logger.info("Database connection disposed")

# Session dependency
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()

def get_sync_session() -> Session:
    """Get sync database session (for migrations)."""
    return SessionLocal()

# Database context manager
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database transaction error", error=str(e))
            raise
        finally:
            await session.close()

# Database initialization
async def init_db() -> None:
    """Initialize database tables."""
    try:
        logger.info("Initializing database")
        
        # Import all models to ensure they are registered
        from app.models import (
            user,
            company,
            financial_data,
            prediction,
            file_upload,
            audit_log,
            notification,
            integration,
            session,
        )
        
        # Create tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

# Database health check
async def check_db_health() -> bool:
    """Check database connectivity."""
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False

# Transaction decorator
def db_transaction(func):
    """Decorator for database transactions."""
    async def wrapper(*args, **kwargs):
        async with get_db_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper

# Database utilities
class DatabaseUtils:
    """Database utility functions."""
    
    @staticmethod
    async def execute_raw_sql(sql: str, params: Optional[dict] = None) -> list:
        """Execute raw SQL query."""
        async with get_db_session() as session:
            result = await session.execute(sql, params or {})
            return result.fetchall()
    
    @staticmethod
    async def get_table_info(table_name: str) -> dict:
        """Get table information."""
        async with get_db_session() as session:
            # This is PostgreSQL specific
            sql = """
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
            result = await session.execute(sql, {"table_name": table_name})
            return result.fetchall()
    
    @staticmethod
    async def get_database_size() -> dict:
        """Get database size information."""
        async with get_db_session() as session:
            # PostgreSQL specific
            sql = """
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
            """
            result = await session.execute(sql)
            return result.first()

# Connection pool monitoring
class ConnectionPoolMonitor:
    """Monitor database connection pool."""
    
    @staticmethod
    def get_pool_status() -> dict:
        """Get connection pool status."""
        pool = async_engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    @staticmethod
    async def warm_up_pool() -> None:
        """Warm up the connection pool."""
        logger.info("Warming up database connection pool")
        
        # Create some connections to warm up the pool
        sessions = []
        try:
            for _ in range(3):
                session = AsyncSessionLocal()
                sessions.append(session)
                await session.execute("SELECT 1")
        finally:
            for session in sessions:
                await session.close()
        
        logger.info("Database connection pool warmed up")

# Database metrics
class DatabaseMetrics:
    """Database performance metrics."""
    
    @staticmethod
    async def get_query_stats() -> dict:
        """Get query statistics (PostgreSQL specific)."""
        async with get_db_session() as session:
            sql = text("""
            SELECT 
                query,
                calls,
                total_exec_time as total_time,
                mean_exec_time as mean_time,
                rows
            FROM pg_stat_statements 
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY total_exec_time DESC 
            LIMIT 10
            """)
            result = await session.execute(sql)
            return [dict(row) for row in result.fetchall()]
    
    @staticmethod
    async def get_table_stats() -> dict:
        """Get table statistics."""
        async with get_db_session() as session:
            sql = text("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
            """)
            result = await session.execute(sql)
            return [dict(row) for row in result.fetchall()]
    
    @staticmethod
    async def get_manufacturing_stats() -> dict:
        """Get manufacturing-specific statistics."""
        async with get_db_session() as session:
            stats = {}
            
            # Manufacturing table row counts
            tables = ['sales_customers', 'sales_invoices', 'accounting_accounts_receivable',
                     'finance_cash_ledger', 'operations_production_orders', 'hr_employees']
            
            for table in tables:
                sql = text(f"SELECT COUNT(*) as count FROM {table}")
                result = await session.execute(sql)
                stats[f"{table}_count"] = result.scalar()
            
            # Cash flow summary
            sql = text("""
                SELECT 
                    SUM(CASE WHEN transaction_type = 'inflow' THEN amount ELSE 0 END) as total_inflow,
                    SUM(CASE WHEN transaction_type = 'outflow' THEN amount ELSE 0 END) as total_outflow,
                    MAX(running_balance) as max_balance,
                    MIN(running_balance) as min_balance
                FROM finance_cash_ledger
                WHERE date_recorded >= CURRENT_DATE - INTERVAL '30 days'
            """)
            result = await session.execute(sql)
            cash_flow = result.fetchone()
            if cash_flow:
                stats.update(dict(cash_flow))
            
            # Production efficiency
            sql = text("""
                SELECT 
                    AVG(units_produced::float / NULLIF(units_ordered, 0)) as avg_efficiency,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                    COUNT(*) as total_orders
                FROM operations_production_orders
                WHERE start_date >= CURRENT_DATE - INTERVAL '30 days'
            """)
            result = await session.execute(sql)
            production = result.fetchone()
            if production:
                stats.update(dict(production))
            
            return stats
