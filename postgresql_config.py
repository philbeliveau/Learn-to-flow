#!/usr/bin/env python3
"""
Production-Ready PostgreSQL Configuration for EZBI Analytics
==========================================================

This module provides enhanced database configuration with:
- Advanced connection pooling
- Performance optimization
- Monitoring capabilities
- Security enhancements
- Backup integration
"""

import os
import asyncio
import asyncpg
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from datetime import datetime
import json
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@dataclass
class PostgreSQLConfig:
    """Enhanced PostgreSQL configuration."""
    
    # Connection settings
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'ezbi_analytics')
    username: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', 'password')
    
    # Connection pool settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '20'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '40'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hour
    pool_pre_ping: bool = True
    
    # Performance settings
    echo: bool = os.getenv('DB_ECHO', 'false').lower() == 'true'
    echo_pool: bool = os.getenv('DB_ECHO_POOL', 'false').lower() == 'true'
    
    # SSL settings
    ssl_mode: str = os.getenv('DB_SSL_MODE', 'prefer')
    ssl_cert: Optional[str] = os.getenv('DB_SSL_CERT')
    ssl_key: Optional[str] = os.getenv('DB_SSL_KEY')
    ssl_ca: Optional[str] = os.getenv('DB_SSL_CA')
    
    # Query optimization
    statement_timeout: int = int(os.getenv('DB_STATEMENT_TIMEOUT', '30000'))  # 30 seconds
    idle_in_transaction_session_timeout: int = int(os.getenv('DB_IDLE_TIMEOUT', '60000'))  # 60 seconds
    
    @property
    def database_url(self) -> str:
        """Generate database URL with SSL parameters."""
        base_url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        ssl_params = []
        if self.ssl_mode:
            ssl_params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            ssl_params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            ssl_params.append(f"sslkey={self.ssl_key}")
        if self.ssl_ca:
            ssl_params.append(f"sslrootcert={self.ssl_ca}")
        
        if ssl_params:
            base_url += "?" + "&".join(ssl_params)
        
        return base_url
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")

class EnhancedConnectionPool:
    """Enhanced connection pool with monitoring and optimization."""
    
    def __init__(self, config: PostgreSQLConfig):
        self.config = config
        self.engine = None
        self.session_factory = None
        self.pool_stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'queries_executed': 0,
            'slow_queries': 0,
            'pool_timeouts': 0,
            'last_stats_reset': datetime.now()
        }
        
    async def initialize(self):
        """Initialize the enhanced connection pool."""
        logger.info("Initializing enhanced PostgreSQL connection pool", 
                   host=self.config.host, 
                   database=self.config.database)
        
        # Create engine with advanced configuration
        self.engine = create_async_engine(
            self.config.database_url,
            echo=self.config.echo,
            echo_pool=self.config.echo_pool,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            pool_reset_on_return='commit',
            connect_args={
                'server_settings': {
                    'application_name': 'EZBI_Analytics_Production',
                    'timezone': 'UTC',
                    'statement_timeout': str(self.config.statement_timeout),
                    'idle_in_transaction_session_timeout': str(self.config.idle_in_transaction_session_timeout),
                    'shared_preload_libraries': 'pg_stat_statements',
                    'log_statement': 'all',
                    'log_min_duration_statement': '1000',  # Log queries > 1 second
                }
            }
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
        
        # Setup connection pool events
        self._setup_pool_events()
        
        # Test connection
        await self._test_connection()
        
        logger.info("Enhanced connection pool initialized successfully")
    
    def _setup_pool_events(self):
        """Setup connection pool event handlers."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new connection creation."""
            self.pool_stats['connections_created'] += 1
            logger.debug("New database connection created", 
                        connection_id=id(dbapi_connection),
                        total_created=self.pool_stats['connections_created'])
        
        @event.listens_for(self.engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            """Handle connection closing."""
            self.pool_stats['connections_closed'] += 1
            logger.debug("Database connection closed", 
                        connection_id=id(dbapi_connection),
                        total_closed=self.pool_stats['connections_closed'])
        
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def on_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Handle query execution start."""
            context._query_start_time = datetime.now()
            self.pool_stats['queries_executed'] += 1
        
        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def on_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Handle query execution completion."""
            if hasattr(context, '_query_start_time'):
                duration = datetime.now() - context._query_start_time
                if duration.total_seconds() > 1.0:  # Slow query threshold
                    self.pool_stats['slow_queries'] += 1
                    logger.warning("Slow query detected", 
                                 duration=duration.total_seconds(),
                                 query=statement[:200])
    
    async def _test_connection(self):
        """Test database connection."""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        pool = self.engine.pool
        
        stats = {
            'pool_config': {
                'pool_size': self.config.pool_size,
                'max_overflow': self.config.max_overflow,
                'pool_timeout': self.config.pool_timeout,
                'pool_recycle': self.config.pool_recycle
            },
            'pool_status': {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            },
            'performance_stats': self.pool_stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        try:
            start_time = datetime.now()
            
            async with self.get_session() as session:
                # Basic connectivity test
                result = await session.execute(text("SELECT 1"))
                await result.fetchone()
                
                # Database version
                version_result = await session.execute(text("SELECT version()"))
                db_version = (await version_result.fetchone())[0]
                
                # Database size
                size_result = await session.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                ))
                db_size = (await size_result.fetchone())[0]
                
                # Active connections
                conn_result = await session.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                ))
                active_connections = (await conn_result.fetchone())[0]
                
                # Manufacturing tables status
                tables_result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_live_tup as row_count,
                        n_dead_tup as dead_rows
                    FROM pg_stat_user_tables 
                    WHERE tablename LIKE 'sales_%' 
                       OR tablename LIKE 'accounting_%'
                       OR tablename LIKE 'operations_%'
                       OR tablename LIKE 'finance_%'
                       OR tablename LIKE 'hr_%'
                       OR tablename LIKE 'expenses_%'
                    ORDER BY tablename
                """))
                
                manufacturing_tables = []
                for row in await tables_result.fetchall():
                    manufacturing_tables.append({
                        'schema': row[0],
                        'table': row[1],
                        'rows': row[2],
                        'dead_rows': row[3]
                    })
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'database_version': db_version,
                'database_size': db_size,
                'active_connections': active_connections,
                'manufacturing_tables': manufacturing_tables,
                'pool_stats': await self.get_pool_stats(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def optimize_queries(self):
        """Analyze and optimize slow queries."""
        logger.info("Starting query optimization analysis")
        
        async with self.get_session() as session:
            # Get slow queries from pg_stat_statements
            slow_queries_result = await session.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    stddev_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat_statements%'
                  AND query NOT LIKE '%information_schema%'
                  AND mean_exec_time > 100  -- Queries taking more than 100ms on average
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """))
            
            slow_queries = []
            for row in await slow_queries_result.fetchall():
                slow_queries.append({
                    'query': row[0][:200] + '...' if len(row[0]) > 200 else row[0],
                    'calls': row[1],
                    'total_time': row[2],
                    'mean_time': row[3],
                    'stddev_time': row[4],
                    'rows': row[5],
                    'hit_percent': row[6]
                })
            
            # Get index usage statistics
            index_usage_result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                  AND (tablename LIKE 'sales_%' 
                       OR tablename LIKE 'accounting_%'
                       OR tablename LIKE 'operations_%'
                       OR tablename LIKE 'finance_%'
                       OR tablename LIKE 'hr_%'
                       OR tablename LIKE 'expenses_%')
                ORDER BY idx_scan DESC
            """))
            
            index_usage = []
            for row in await index_usage_result.fetchall():
                index_usage.append({
                    'schema': row[0],
                    'table': row[1],
                    'index': row[2],
                    'scans': row[3],
                    'tuples_read': row[4],
                    'tuples_fetched': row[5]
                })
            
            # Get table statistics
            table_stats_result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                  AND (tablename LIKE 'sales_%' 
                       OR tablename LIKE 'accounting_%'
                       OR tablename LIKE 'operations_%'
                       OR tablename LIKE 'finance_%'
                       OR tablename LIKE 'hr_%'
                       OR tablename LIKE 'expenses_%')
                ORDER BY n_live_tup DESC
            """))
            
            table_stats = []
            for row in await table_stats_result.fetchall():
                table_stats.append({
                    'schema': row[0],
                    'table': row[1],
                    'inserts': row[2],
                    'updates': row[3],
                    'deletes': row[4],
                    'live_tuples': row[5],
                    'dead_tuples': row[6],
                    'last_vacuum': row[7],
                    'last_autovacuum': row[8],
                    'last_analyze': row[9],
                    'last_autoanalyze': row[10]
                })
            
            optimization_report = {
                'timestamp': datetime.now().isoformat(),
                'slow_queries': slow_queries,
                'index_usage': index_usage,
                'table_statistics': table_stats,
                'recommendations': self._generate_optimization_recommendations(slow_queries, index_usage, table_stats)
            }
            
            # Save optimization report
            with open('postgresql_optimization_report.json', 'w') as f:
                json.dump(optimization_report, f, indent=2, default=str)
            
            logger.info("Query optimization analysis completed", 
                       slow_queries_count=len(slow_queries),
                       report_saved='postgresql_optimization_report.json')
            
            return optimization_report
    
    def _generate_optimization_recommendations(self, slow_queries: List[Dict], 
                                             index_usage: List[Dict], 
                                             table_stats: List[Dict]) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Slow query recommendations
        if slow_queries:
            recommendations.append(f"Found {len(slow_queries)} slow queries - consider query optimization")
            
            # Check for missing indexes
            for query in slow_queries:
                if 'WHERE' in query['query'] and query['hit_percent'] and query['hit_percent'] < 95:
                    recommendations.append(f"Query may benefit from additional indexes (cache hit ratio: {query['hit_percent']:.1f}%)")
        
        # Index usage recommendations
        unused_indexes = [idx for idx in index_usage if idx['scans'] == 0]
        if unused_indexes:
            recommendations.append(f"Found {len(unused_indexes)} unused indexes - consider dropping them")
        
        # Table maintenance recommendations
        for table in table_stats:
            dead_ratio = table['dead_tuples'] / (table['live_tuples'] + table['dead_tuples']) if table['live_tuples'] + table['dead_tuples'] > 0 else 0
            if dead_ratio > 0.2:  # More than 20% dead tuples
                recommendations.append(f"Table {table['table']} has high dead tuple ratio ({dead_ratio:.1%}) - consider VACUUM")
            
            if not table['last_analyze']:
                recommendations.append(f"Table {table['table']} has never been analyzed - run ANALYZE")
        
        # General recommendations
        recommendations.extend([
            "Enable pg_stat_statements for better query monitoring",
            "Consider implementing query result caching for frequently accessed data",
            "Monitor connection pool usage and adjust pool size if needed",
            "Set up automated VACUUM and ANALYZE schedules",
            "Consider partitioning large tables (> 1M rows)",
            "Implement read replicas for read-heavy workloads"
        ])
        
        return recommendations
    
    async def close(self):
        """Close the connection pool."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Connection pool closed")

# Global connection pool instance
_connection_pool: Optional[EnhancedConnectionPool] = None

async def get_connection_pool() -> EnhancedConnectionPool:
    """Get or create the global connection pool."""
    global _connection_pool
    
    if _connection_pool is None:
        config = PostgreSQLConfig()
        _connection_pool = EnhancedConnectionPool(config)
        await _connection_pool.initialize()
    
    return _connection_pool

async def get_database_session():
    """Get database session from the global pool."""
    pool = await get_connection_pool()
    async with pool.get_session() as session:
        yield session

async def close_connection_pool():
    """Close the global connection pool."""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None

# Database utilities for manufacturing operations
class ManufacturingQueries:
    """Optimized queries for manufacturing operations."""
    
    @staticmethod
    async def get_cash_flow_summary(session: AsyncSession, company_id: str, days: int = 30) -> Dict[str, Any]:
        """Get cash flow summary for manufacturing operations."""
        result = await session.execute(text("""
            WITH cash_flow AS (
                SELECT 
                    date_recorded::date as date,
                    SUM(CASE WHEN transaction_type = 'inflow' THEN amount ELSE -amount END) as daily_flow,
                    SUM(SUM(CASE WHEN transaction_type = 'inflow' THEN amount ELSE -amount END)) 
                        OVER (ORDER BY date_recorded::date) as running_balance
                FROM finance_cash_ledger
                WHERE date_recorded >= CURRENT_DATE - INTERVAL ':days days'
                GROUP BY date_recorded::date
                ORDER BY date_recorded::date
            )
            SELECT 
                date,
                daily_flow,
                running_balance,
                LAG(running_balance, 1) OVER (ORDER BY date) as previous_balance
            FROM cash_flow
        """), {"days": days})
        
        return [dict(row) for row in await result.fetchall()]
    
    @staticmethod
    async def get_production_efficiency(session: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """Get production efficiency metrics."""
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total_orders,
                AVG(units_produced::float / NULLIF(units_ordered, 0)) as avg_efficiency,
                SUM(units_produced) as total_produced,
                SUM(units_ordered) as total_ordered,
                AVG(labor_cost + material_cost) as avg_cost_per_order,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                COUNT(CASE WHEN completion_date > expected_completion THEN 1 END) as delayed_orders
            FROM operations_production_orders
            WHERE start_date >= CURRENT_DATE - INTERVAL ':days days'
        """), {"days": days})
        
        return dict(await result.fetchone())
    
    @staticmethod
    async def get_accounts_receivable_aging(session: AsyncSession) -> List[Dict[str, Any]]:
        """Get accounts receivable aging analysis."""
        result = await session.execute(text("""
            SELECT 
                aging_bucket,
                COUNT(*) as invoice_count,
                SUM(amount_outstanding) as total_outstanding,
                AVG(amount_outstanding) as avg_outstanding,
                AVG(days_outstanding) as avg_days_outstanding
            FROM accounting_accounts_receivable
            WHERE amount_outstanding > 0
            GROUP BY aging_bucket
            ORDER BY 
                CASE aging_bucket
                    WHEN '0-30' THEN 1
                    WHEN '31-60' THEN 2
                    WHEN '61-90' THEN 3
                    WHEN '90+' THEN 4
                    ELSE 5
                END
        """))
        
        return [dict(row) for row in await result.fetchall()]

# Example usage and testing
async def test_connection_pool():
    """Test the enhanced connection pool."""
    pool = await get_connection_pool()
    
    # Test basic connectivity
    health = await pool.health_check()
    print(f"Database health: {health['status']}")
    
    # Test query optimization
    optimization = await pool.optimize_queries()
    print(f"Optimization analysis completed: {len(optimization['slow_queries'])} slow queries found")
    
    # Test manufacturing queries
    async with pool.get_session() as session:
        cash_flow = await ManufacturingQueries.get_cash_flow_summary(session, "test_company")
        print(f"Cash flow data points: {len(cash_flow)}")
        
        production = await ManufacturingQueries.get_production_efficiency(session)
        print(f"Production efficiency: {production}")
        
        ar_aging = await ManufacturingQueries.get_accounts_receivable_aging(session)
        print(f"AR aging buckets: {len(ar_aging)}")

if __name__ == "__main__":
    asyncio.run(test_connection_pool())