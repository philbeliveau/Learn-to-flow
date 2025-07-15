"""
PostgreSQL Direct Data Extractor for EZBI Platform
Extracts manufacturing data directly from PostgreSQL database
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PostgreSQLConfig:
    """PostgreSQL connection configuration"""
    database_url: str
    connection_timeout: int = 30
    query_timeout: int = 60
    max_connections: int = 10

class PostgreSQLDirectExtractor:
    """Extracts data directly from PostgreSQL for EZBI platform"""
    
    def __init__(self, config: PostgreSQLConfig):
        self.config = config
        self.connection_pool = None
        
        # Define extraction queries
        self.extraction_queries = {
            'daily_cash_flow': """
                SELECT 
                    date_recorded,
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as daily_inflows,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as daily_outflows,
                    SUM(amount) as net_daily_flow,
                    COUNT(*) as transaction_count
                FROM finance.cash_ledger
                WHERE date_recorded >= $1 AND date_recorded <= $2
                GROUP BY date_recorded
                ORDER BY date_recorded
            """,
            
            'sales_metrics': """
                SELECT 
                    date_issued,
                    COUNT(*) as invoice_count,
                    SUM(amount) as total_sales,
                    AVG(amount) as avg_invoice_value,
                    COUNT(CASE WHEN status = 'Paid' THEN 1 END) as paid_invoices,
                    COUNT(CASE WHEN status = 'Open' THEN 1 END) as open_invoices,
                    COUNT(CASE WHEN status = 'Overdue' THEN 1 END) as overdue_invoices
                FROM sales.invoices
                WHERE date_issued >= $1 AND date_issued <= $2
                GROUP BY date_issued
                ORDER BY date_issued
            """,
            
            'ar_aging_current': """
                SELECT 
                    aging_bucket,
                    COUNT(*) as invoice_count,
                    SUM(amount_outstanding) as total_outstanding,
                    AVG(amount_outstanding) as avg_outstanding,
                    AVG(days_outstanding) as avg_days_outstanding
                FROM accounting.accounts_receivable
                WHERE as_of_date = $1
                GROUP BY aging_bucket
                ORDER BY 
                    CASE aging_bucket
                        WHEN '0-30' THEN 1
                        WHEN '31-60' THEN 2
                        WHEN '61-90' THEN 3
                        WHEN '90+' THEN 4
                    END
            """,
            
            'production_metrics': """
                SELECT 
                    start_date,
                    status,
                    COUNT(*) as order_count,
                    SUM(units_ordered) as total_units_ordered,
                    SUM(units_produced) as total_units_produced,
                    SUM(cost_of_goods_sold) as total_production_value,
                    AVG(cost_of_goods_sold) as avg_order_value,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_orders,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_orders
                FROM operations.production_orders
                WHERE start_date >= $1 AND start_date <= $2
                GROUP BY start_date, status
                ORDER BY start_date, status
            """,
            
            'vendor_spending': """
                SELECT 
                    date_purchased,
                    category,
                    COUNT(*) as purchase_count,
                    SUM(amount) as total_spent,
                    AVG(amount) as avg_purchase_value,
                    COUNT(CASE WHEN payment_status = 'Paid' THEN 1 END) as paid_purchases,
                    COUNT(CASE WHEN payment_status = 'Outstanding' THEN 1 END) as outstanding_purchases
                FROM accounting.purchases
                WHERE date_purchased >= $1 AND date_purchased <= $2
                GROUP BY date_purchased, category
                ORDER BY date_purchased, category
            """,
            
            'cash_position_trend': """
                SELECT 
                    date_recorded,
                    SUM(amount) OVER (ORDER BY date_recorded) as running_cash_balance,
                    amount as daily_change,
                    transaction_type,
                    COUNT(*) OVER (PARTITION BY date_recorded) as daily_transactions
                FROM finance.cash_ledger
                WHERE date_recorded >= $1 AND date_recorded <= $2
                ORDER BY date_recorded, transaction_id
            """,
            
            'customer_metrics': """
                SELECT 
                    c.company_name,
                    COUNT(i.invoice_id) as total_invoices,
                    SUM(i.amount) as total_sales,
                    AVG(i.amount) as avg_invoice_value,
                    SUM(CASE WHEN i.status = 'Paid' THEN i.amount ELSE 0 END) as paid_amount,
                    SUM(CASE WHEN i.status = 'Open' THEN i.amount ELSE 0 END) as outstanding_amount,
                    AVG(CASE WHEN i.status = 'Paid' THEN (i.payment_date - i.date_issued) END) as avg_payment_days
                FROM sales.customers c
                LEFT JOIN sales.invoices i ON c.customer_id = i.customer_id
                WHERE i.date_issued >= $1 AND i.date_issued <= $2
                GROUP BY c.customer_id, c.company_name
                HAVING COUNT(i.invoice_id) > 0
                ORDER BY total_sales DESC
            """,
            
            'operational_efficiency': """
                SELECT 
                    DATE_TRUNC('day', po.start_date) as date,
                    COUNT(po.order_id) as orders_started,
                    COUNT(CASE WHEN po.status = 'Completed' THEN 1 END) as orders_completed,
                    AVG(CASE WHEN po.completion_date IS NOT NULL 
                        THEN (po.completion_date - po.start_date) END) as avg_completion_days,
                    SUM(po.units_ordered) as total_units_ordered,
                    SUM(po.units_produced) as total_units_produced,
                    AVG(po.cost_of_goods_sold / po.units_ordered) as avg_unit_cost
                FROM operations.production_orders po
                WHERE po.start_date >= $1 AND po.start_date <= $2
                GROUP BY DATE_TRUNC('day', po.start_date)
                ORDER BY date
            """
        }
    
    async def initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.config.database_url,
                min_size=2,
                max_size=self.config.max_connections,
                command_timeout=self.config.query_timeout
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    async def close_connection_pool(self):
        """Close PostgreSQL connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def extract_dashboard_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Extract all dashboard data from PostgreSQL"""
        if not self.connection_pool:
            await self.initialize_connection_pool()
        
        dashboard_data = {
            'extraction_info': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'extracted_at': datetime.now().isoformat(),
                'data_source': 'postgresql_direct'
            },
            'financial_data': {},
            'operational_data': {},
            'customer_data': {},
            'kpis': [],
            'charts': []
        }
        
        try:
            async with self.connection_pool.acquire() as conn:
                # Extract financial data
                dashboard_data['financial_data'] = await self._extract_financial_data(conn, start_date, end_date)
                
                # Extract operational data
                dashboard_data['operational_data'] = await self._extract_operational_data(conn, start_date, end_date)
                
                # Extract customer data
                dashboard_data['customer_data'] = await self._extract_customer_data(conn, start_date, end_date)
                
                # Calculate KPIs
                dashboard_data['kpis'] = await self._calculate_kpis(conn, start_date, end_date)
                
                # Generate chart configurations
                dashboard_data['charts'] = await self._generate_chart_configs(dashboard_data)
            
            logger.info(f"Dashboard data extracted successfully for {start_date} to {end_date}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to extract dashboard data: {e}")
            raise
    
    async def _extract_financial_data(self, conn: asyncpg.Connection, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Extract financial data from PostgreSQL"""
        financial_data = {}
        
        # Daily cash flow
        cash_flow_rows = await conn.fetch(self.extraction_queries['daily_cash_flow'], start_date, end_date)
        financial_data['daily_cash_flow'] = [dict(row) for row in cash_flow_rows]
        
        # Cash position trend
        cash_position_rows = await conn.fetch(self.extraction_queries['cash_position_trend'], start_date, end_date)
        financial_data['cash_position_trend'] = [dict(row) for row in cash_position_rows]
        
        # AR aging current
        ar_aging_rows = await conn.fetch(self.extraction_queries['ar_aging_current'], end_date)
        financial_data['ar_aging_current'] = [dict(row) for row in ar_aging_rows]
        
        # Vendor spending
        vendor_spending_rows = await conn.fetch(self.extraction_queries['vendor_spending'], start_date, end_date)
        financial_data['vendor_spending'] = [dict(row) for row in vendor_spending_rows]
        
        return financial_data
    
    async def _extract_operational_data(self, conn: asyncpg.Connection, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Extract operational data from PostgreSQL"""
        operational_data = {}
        
        # Production metrics
        production_rows = await conn.fetch(self.extraction_queries['production_metrics'], start_date, end_date)
        operational_data['production_metrics'] = [dict(row) for row in production_rows]
        
        # Operational efficiency
        efficiency_rows = await conn.fetch(self.extraction_queries['operational_efficiency'], start_date, end_date)
        operational_data['operational_efficiency'] = [dict(row) for row in efficiency_rows]
        
        # Sales metrics
        sales_rows = await conn.fetch(self.extraction_queries['sales_metrics'], start_date, end_date)
        operational_data['sales_metrics'] = [dict(row) for row in sales_rows]
        
        return operational_data
    
    async def _extract_customer_data(self, conn: asyncpg.Connection, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Extract customer data from PostgreSQL"""
        customer_data = {}
        
        # Customer metrics
        customer_rows = await conn.fetch(self.extraction_queries['customer_metrics'], start_date, end_date)
        customer_data['customer_metrics'] = [dict(row) for row in customer_rows]
        
        return customer_data
    
    async def _calculate_kpis(self, conn: asyncpg.Connection, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate KPIs from extracted data"""
        kpis = []
        
        # Current cash balance
        cash_balance = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM finance.cash_ledger
            WHERE date_recorded <= $1
        """, end_date)
        
        kpis.append({
            'name': 'Current Cash Balance',
            'value': float(cash_balance),
            'format': 'currency',
            'trend': 'stable',
            'category': 'financial'
        })
        
        # Period sales total
        period_sales = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM sales.invoices
            WHERE date_issued >= $1 AND date_issued <= $2
        """, start_date, end_date)
        
        kpis.append({
            'name': 'Period Sales Total',
            'value': float(period_sales),
            'format': 'currency',
            'trend': 'up',
            'category': 'sales'
        })
        
        # Outstanding AR
        outstanding_ar = await conn.fetchval("""
            SELECT COALESCE(SUM(amount_outstanding), 0) FROM accounting.accounts_receivable
            WHERE as_of_date = $1
        """, end_date)
        
        kpis.append({
            'name': 'Outstanding Receivables',
            'value': float(outstanding_ar),
            'format': 'currency',
            'trend': 'stable',
            'category': 'collections'
        })
        
        # Production efficiency
        production_efficiency = await conn.fetchval("""
            SELECT COALESCE(
                SUM(units_produced)::float / NULLIF(SUM(units_ordered), 0) * 100, 
                0
            ) FROM operations.production_orders
            WHERE start_date >= $1 AND start_date <= $2
        """, start_date, end_date)
        
        kpis.append({
            'name': 'Production Efficiency',
            'value': float(production_efficiency),
            'format': 'percentage',
            'trend': 'up',
            'category': 'operations'
        })
        
        # Average payment days
        avg_payment_days = await conn.fetchval("""
            SELECT COALESCE(AVG(payment_date - date_issued), 0) 
            FROM sales.invoices
            WHERE payment_date IS NOT NULL 
            AND date_issued >= $1 AND date_issued <= $2
        """, start_date, end_date)
        
        kpis.append({
            'name': 'Average Payment Days',
            'value': float(avg_payment_days.days if avg_payment_days else 0),
            'format': 'integer',
            'trend': 'down',
            'category': 'collections'
        })
        
        return kpis
    
    async def _generate_chart_configs(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate chart configurations from extracted data"""
        charts = []
        
        # Cash flow trend chart
        if dashboard_data['financial_data'].get('daily_cash_flow'):
            cash_flow_data = dashboard_data['financial_data']['daily_cash_flow']
            
            charts.append({
                'type': 'line',
                'title': 'Daily Cash Flow Trend',
                'data': {
                    'labels': [item['date_recorded'].strftime('%Y-%m-%d') for item in cash_flow_data],
                    'datasets': [
                        {
                            'label': 'Inflows',
                            'data': [float(item['daily_inflows']) for item in cash_flow_data],
                            'borderColor': '#10B981',
                            'backgroundColor': 'rgba(16, 185, 129, 0.1)'
                        },
                        {
                            'label': 'Outflows',
                            'data': [float(item['daily_outflows']) for item in cash_flow_data],
                            'borderColor': '#EF4444',
                            'backgroundColor': 'rgba(239, 68, 68, 0.1)'
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Daily Cash Flow Trend'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'ticks': {
                                'callback': 'function(value) { return "$" + value.toLocaleString(); }'
                            }
                        }
                    }
                }
            })
        
        # AR aging chart
        if dashboard_data['financial_data'].get('ar_aging_current'):
            ar_aging_data = dashboard_data['financial_data']['ar_aging_current']
            
            charts.append({
                'type': 'doughnut',
                'title': 'Accounts Receivable Aging',
                'data': {
                    'labels': [item['aging_bucket'] for item in ar_aging_data],
                    'datasets': [{
                        'data': [float(item['total_outstanding']) for item in ar_aging_data],
                        'backgroundColor': ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'AR Aging Distribution'
                        },
                        'legend': {
                            'position': 'bottom'
                        }
                    }
                }
            })
        
        # Sales metrics chart
        if dashboard_data['operational_data'].get('sales_metrics'):
            sales_data = dashboard_data['operational_data']['sales_metrics']
            
            charts.append({
                'type': 'bar',
                'title': 'Daily Sales Performance',
                'data': {
                    'labels': [item['date_issued'].strftime('%Y-%m-%d') for item in sales_data],
                    'datasets': [{
                        'label': 'Total Sales',
                        'data': [float(item['total_sales']) for item in sales_data],
                        'backgroundColor': '#3B82F6'
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Daily Sales Performance'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'ticks': {
                                'callback': 'function(value) { return "$" + value.toLocaleString(); }'
                            }
                        }
                    }
                }
            })
        
        # Production efficiency chart
        if dashboard_data['operational_data'].get('operational_efficiency'):
            efficiency_data = dashboard_data['operational_data']['operational_efficiency']
            
            charts.append({
                'type': 'line',
                'title': 'Production Efficiency Trend',
                'data': {
                    'labels': [item['date'].strftime('%Y-%m-%d') for item in efficiency_data],
                    'datasets': [{
                        'label': 'Units Produced / Units Ordered (%)',
                        'data': [
                            (float(item['total_units_produced']) / float(item['total_units_ordered']) * 100) 
                            if item['total_units_ordered'] > 0 else 0 
                            for item in efficiency_data
                        ],
                        'borderColor': '#10B981',
                        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                        'fill': True
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Production Efficiency Trend'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'ticks': {
                                'callback': 'function(value) { return value + "%"; }'
                            }
                        }
                    }
                }
            })
        
        return charts
    
    async def extract_real_time_metrics(self) -> Dict[str, Any]:
        """Extract real-time metrics for live dashboard updates"""
        if not self.connection_pool:
            await self.initialize_connection_pool()
        
        try:
            async with self.connection_pool.acquire() as conn:
                # Current cash balance
                cash_balance = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM finance.cash_ledger
                """)
                
                # Today's sales
                today_sales = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM sales.invoices
                    WHERE date_issued = CURRENT_DATE
                """)
                
                # Outstanding invoices
                outstanding_invoices = await conn.fetchval("""
                    SELECT COUNT(*) FROM sales.invoices WHERE status = 'Open'
                """)
                
                # Active production orders
                active_production = await conn.fetchval("""
                    SELECT COUNT(*) FROM operations.production_orders
                    WHERE status IN ('Planned', 'In Progress')
                """)
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {
                        'cash_balance': float(cash_balance),
                        'today_sales': float(today_sales),
                        'outstanding_invoices': int(outstanding_invoices),
                        'active_production_orders': int(active_production)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to extract real-time metrics: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL connection health"""
        try:
            if not self.connection_pool:
                await self.initialize_connection_pool()
            
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                
                return {
                    'status': 'healthy',
                    'connection_pool_size': len(self.connection_pool._holders),
                    'database_responsive': result == 1,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Factory function
def create_postgres_extractor(database_url: str) -> PostgreSQLDirectExtractor:
    """Create PostgreSQL direct extractor instance"""
    config = PostgreSQLConfig(database_url=database_url)
    return PostgreSQLDirectExtractor(config)