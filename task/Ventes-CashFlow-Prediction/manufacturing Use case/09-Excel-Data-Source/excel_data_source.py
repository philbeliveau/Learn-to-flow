"""
Excel Data Source Module
Generates Excel files as structured data sources for EZBI platform consumption
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncpg
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ExcelDataSource:
    """Creates Excel files as structured data sources for EZBI platform"""
    
    def __init__(self, export_path: str = "/app/exports"):
        self.export_path = Path(export_path)
        self.export_path.mkdir(exist_ok=True)
        
        # Data source configuration
        self.data_source_config = {
            'version': '1.0.0',
            'format': 'xlsx',
            'sheets': {
                'metadata': 'File metadata and processing info',
                'dashboard': 'Summary metrics for dashboard',
                'invoices': 'Daily B2B sales transactions',
                'cash_flow': 'Daily cash flow transactions',
                'ar_aging': 'Accounts receivable aging analysis',
                'production': 'Manufacturing production orders',
                'purchases': 'Vendor purchases and expenses',
                'payroll': 'Employee payroll records',
                'kpis': 'Key performance indicators'
            }
        }
    
    async def generate_daily_data_source(self, db_connection: asyncpg.Connection, 
                                        date: datetime) -> str:
        """Generate Excel file as data source for EZBI platform"""
        try:
            # Generate filename with standardized format
            filename = f"manufacturing_data_source_{date.strftime('%Y%m%d')}.xlsx"
            filepath = self.export_path / filename
            
            # Fetch all data from database
            data = await self._fetch_all_data(db_connection, date)
            
            # Create Excel data source file
            await self._create_data_source_file(filepath, data, date)
            
            # Generate metadata file for EZBI platform
            await self._create_metadata_file(filepath, data, date)
            
            logger.info(f"Excel data source generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate Excel data source: {e}")
            raise
    
    async def _fetch_all_data(self, conn: asyncpg.Connection, date: datetime) -> Dict[str, Any]:
        """Fetch all data needed for EZBI platform"""
        data = {}
        
        # 1. Dashboard Summary (KPIs for EZBI)
        data['dashboard'] = await self._fetch_dashboard_data(conn, date)
        
        # 2. Invoices (for Sales Analytics)
        data['invoices'] = await self._fetch_invoices_data(conn, date)
        
        # 3. Cash Flow (for Financial Dashboard)
        data['cash_flow'] = await self._fetch_cash_flow_data(conn, date)
        
        # 4. AR Aging (for Collections Dashboard)
        data['ar_aging'] = await self._fetch_ar_aging_data(conn, date)
        
        # 5. Production (for Operations Dashboard)
        data['production'] = await self._fetch_production_data(conn, date)
        
        # 6. Purchases (for Expense Analytics)
        data['purchases'] = await self._fetch_purchases_data(conn, date)
        
        # 7. Payroll (for HR Analytics)
        data['payroll'] = await self._fetch_payroll_data(conn, date)
        
        # 8. KPIs (for Executive Dashboard)
        data['kpis'] = await self._calculate_kpis(conn, date)
        
        return data
    
    async def _fetch_dashboard_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch dashboard summary data for EZBI platform"""
        # Calculate key metrics
        metrics = []
        
        # Cash position
        cash_balance = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM finance.cash_ledger 
            WHERE date_recorded <= $1
        """, date)
        metrics.append({'metric': 'cash_balance', 'value': float(cash_balance), 'date': date})
        
        # Daily sales
        daily_sales = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM sales.invoices 
            WHERE date_issued = $1
        """, date)
        metrics.append({'metric': 'daily_sales', 'value': float(daily_sales), 'date': date})
        
        # Outstanding AR
        outstanding_ar = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM sales.invoices 
            WHERE status = 'Open' AND date_issued <= $1
        """, date)
        metrics.append({'metric': 'outstanding_ar', 'value': float(outstanding_ar), 'date': date})
        
        # Active production orders
        active_production = await conn.fetchval("""
            SELECT COUNT(*) FROM operations.production_orders 
            WHERE status IN ('Planned', 'In Progress') AND start_date <= $1
        """, date)
        metrics.append({'metric': 'active_production_orders', 'value': int(active_production), 'date': date})
        
        return metrics
    
    async def _fetch_invoices_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch invoices data for EZBI sales analytics"""
        query = """
            SELECT 
                i.invoice_id,
                i.invoice_number,
                c.company_name as customer_name,
                i.date_issued,
                i.due_date,
                i.amount,
                i.status,
                i.payment_date,
                (i.due_date - i.date_issued) as payment_terms_days,
                CASE 
                    WHEN i.status = 'Paid' THEN 0
                    ELSE ($1::date - i.due_date)
                END as days_overdue
            FROM sales.invoices i
            JOIN sales.customers c ON i.customer_id = c.customer_id
            WHERE i.date_issued = $1
            ORDER BY i.invoice_number
        """
        
        rows = await conn.fetch(query, date)
        return [dict(row) for row in rows]
    
    async def _fetch_cash_flow_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch cash flow data for EZBI financial dashboard"""
        query = """
            SELECT 
                transaction_id,
                transaction_number,
                date_recorded,
                amount,
                transaction_type,
                counterparty,
                description,
                CASE 
                    WHEN amount > 0 THEN 'Inflow'
                    ELSE 'Outflow'
                END as flow_direction,
                ABS(amount) as amount_abs
            FROM finance.cash_ledger
            WHERE date_recorded = $1
            ORDER BY transaction_id
        """
        
        rows = await conn.fetch(query, date)
        return [dict(row) for row in rows]
    
    async def _fetch_ar_aging_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch AR aging data for EZBI collections dashboard"""
        query = """
            SELECT 
                ar.aging_bucket,
                c.company_name as customer_name,
                ar.amount_outstanding,
                ar.days_outstanding,
                i.invoice_number,
                i.date_issued,
                i.due_date,
                CASE 
                    WHEN ar.aging_bucket = '0-30' THEN 1
                    WHEN ar.aging_bucket = '31-60' THEN 2
                    WHEN ar.aging_bucket = '61-90' THEN 3
                    ELSE 4
                END as aging_priority
            FROM accounting.accounts_receivable ar
            JOIN sales.customers c ON ar.customer_id = c.customer_id
            JOIN sales.invoices i ON ar.invoice_id = i.invoice_id
            WHERE ar.as_of_date = $1
            ORDER BY aging_priority, ar.days_outstanding DESC
        """
        
        rows = await conn.fetch(query, date)
        return [dict(row) for row in rows]
    
    async def _fetch_production_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch production data for EZBI operations dashboard"""
        query = """
            SELECT 
                po.order_number,
                p.product_name,
                c.company_name as customer_name,
                po.start_date,
                po.expected_completion,
                po.completion_date,
                po.status,
                po.units_ordered,
                po.units_produced,
                po.cost_of_goods_sold,
                (po.units_produced::float / po.units_ordered::float * 100) as completion_percentage,
                CASE 
                    WHEN po.completion_date IS NOT NULL THEN 
                        (po.completion_date - po.start_date)
                    ELSE 
                        ($1::date - po.start_date)
                END as days_in_production
            FROM operations.production_orders po
            JOIN operations.products p ON po.product_id = p.product_id
            JOIN sales.customers c ON po.customer_id = c.customer_id
            WHERE po.start_date = $1
            ORDER BY po.order_number
        """
        
        rows = await conn.fetch(query, date)
        return [dict(row) for row in rows]
    
    async def _fetch_purchases_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch purchases data for EZBI expense analytics"""
        query = """
            SELECT 
                p.purchase_number,
                v.vendor_name,
                p.category,
                p.amount,
                p.date_purchased,
                p.due_date,
                p.payment_status,
                p.payment_date,
                p.description,
                (p.due_date - p.date_purchased) as payment_terms_days,
                CASE 
                    WHEN p.payment_status = 'Paid' THEN 0
                    ELSE ($1::date - p.due_date)
                END as days_until_due
            FROM accounting.purchases p
            JOIN accounting.vendors v ON p.vendor_id = v.vendor_id
            WHERE p.date_purchased = $1
            ORDER BY p.purchase_number
        """
        
        rows = await conn.fetch(query, date)
        return [dict(row) for row in rows]
    
    async def _fetch_payroll_data(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Fetch payroll data for EZBI HR analytics"""
        query = """
            SELECT 
                e.employee_number,
                e.first_name,
                e.last_name,
                e.department,
                e.position,
                pl.pay_period_start,
                pl.pay_period_end,
                pl.pay_date,
                pl.gross_pay,
                pl.deductions,
                pl.net_pay,
                pl.overtime_hours,
                pl.overtime_pay,
                (pl.gross_pay - pl.deductions) as calculated_net_pay
            FROM hr.payroll_log pl
            JOIN hr.employees e ON pl.employee_id = e.employee_id
            WHERE pl.pay_date = $1
            ORDER BY e.employee_number
        """
        
        rows = await conn.fetch(query, date)
        return [dict(row) for row in rows]
    
    async def _calculate_kpis(self, conn: asyncpg.Connection, date: datetime) -> List[Dict]:
        """Calculate KPIs for EZBI executive dashboard"""
        kpis = []
        
        # 1. Cash Flow KPIs
        cash_flow_query = """
            SELECT 
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as total_inflows,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as total_outflows,
                COALESCE(SUM(amount), 0) as net_cash_flow
            FROM finance.cash_ledger
            WHERE date_recorded = $1
        """
        cash_flow = await conn.fetchrow(cash_flow_query, date)
        
        kpis.extend([
            {'kpi': 'daily_cash_inflows', 'value': float(cash_flow['total_inflows']), 'date': date, 'category': 'financial'},
            {'kpi': 'daily_cash_outflows', 'value': float(cash_flow['total_outflows']), 'date': date, 'category': 'financial'},
            {'kpi': 'net_cash_flow', 'value': float(cash_flow['net_cash_flow']), 'date': date, 'category': 'financial'}
        ])
        
        # 2. Sales KPIs
        sales_kpis_query = """
            SELECT 
                COUNT(*) as invoice_count,
                COALESCE(SUM(amount), 0) as total_sales,
                COALESCE(AVG(amount), 0) as avg_invoice_value
            FROM sales.invoices
            WHERE date_issued = $1
        """
        sales_kpis = await conn.fetchrow(sales_kpis_query, date)
        
        kpis.extend([
            {'kpi': 'daily_invoice_count', 'value': int(sales_kpis['invoice_count']), 'date': date, 'category': 'sales'},
            {'kpi': 'daily_sales_total', 'value': float(sales_kpis['total_sales']), 'date': date, 'category': 'sales'},
            {'kpi': 'avg_invoice_value', 'value': float(sales_kpis['avg_invoice_value']), 'date': date, 'category': 'sales'}
        ])
        
        # 3. Production KPIs
        production_kpis_query = """
            SELECT 
                COUNT(*) as orders_started,
                COALESCE(SUM(units_ordered), 0) as total_units_ordered,
                COALESCE(SUM(cost_of_goods_sold), 0) as total_production_value
            FROM operations.production_orders
            WHERE start_date = $1
        """
        production_kpis = await conn.fetchrow(production_kpis_query, date)
        
        kpis.extend([
            {'kpi': 'daily_production_orders', 'value': int(production_kpis['orders_started']), 'date': date, 'category': 'operations'},
            {'kpi': 'total_units_ordered', 'value': int(production_kpis['total_units_ordered']), 'date': date, 'category': 'operations'},
            {'kpi': 'total_production_value', 'value': float(production_kpis['total_production_value']), 'date': date, 'category': 'operations'}
        ])
        
        return kpis
    
    async def _create_data_source_file(self, filepath: Path, data: Dict[str, Any], date: datetime):
        """Create Excel file optimized for EZBI platform consumption"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # 1. Metadata sheet (for EZBI platform processing)
            metadata_df = pd.DataFrame([
                ['file_version', '1.0.0'],
                ['generated_date', date.strftime('%Y-%m-%d')],
                ['generated_timestamp', datetime.now().isoformat()],
                ['data_source', 'manufacturing_simulator'],
                ['platform_target', 'ezbi_analytics'],
                ['record_count', sum(len(data.get(key, [])) for key in data.keys())],
                ['sheets_included', ', '.join(data.keys())],
                ['processing_status', 'ready']
            ], columns=['property', 'value'])
            metadata_df.to_excel(writer, sheet_name='metadata', index=False)
            
            # 2. Dashboard data (summary metrics)
            if data.get('dashboard'):
                dashboard_df = pd.DataFrame(data['dashboard'])
                dashboard_df.to_excel(writer, sheet_name='dashboard', index=False)
            
            # 3. Invoices data (for sales analytics)
            if data.get('invoices'):
                invoices_df = pd.DataFrame(data['invoices'])
                # Format for EZBI platform
                invoices_df['amount'] = invoices_df['amount'].astype(float)
                invoices_df['days_overdue'] = invoices_df['days_overdue'].fillna(0)
                invoices_df.to_excel(writer, sheet_name='invoices', index=False)
            
            # 4. Cash flow data (for financial dashboard)
            if data.get('cash_flow'):
                cash_flow_df = pd.DataFrame(data['cash_flow'])
                cash_flow_df['amount'] = cash_flow_df['amount'].astype(float)
                cash_flow_df['amount_abs'] = cash_flow_df['amount_abs'].astype(float)
                cash_flow_df.to_excel(writer, sheet_name='cash_flow', index=False)
            
            # 5. AR aging data (for collections dashboard)
            if data.get('ar_aging'):
                ar_aging_df = pd.DataFrame(data['ar_aging'])
                ar_aging_df['amount_outstanding'] = ar_aging_df['amount_outstanding'].astype(float)
                ar_aging_df.to_excel(writer, sheet_name='ar_aging', index=False)
            
            # 6. Production data (for operations dashboard)
            if data.get('production'):
                production_df = pd.DataFrame(data['production'])
                if not production_df.empty:
                    production_df['cost_of_goods_sold'] = production_df['cost_of_goods_sold'].astype(float)
                    production_df['completion_percentage'] = production_df['completion_percentage'].fillna(0)
                production_df.to_excel(writer, sheet_name='production', index=False)
            
            # 7. Purchases data (for expense analytics)
            if data.get('purchases'):
                purchases_df = pd.DataFrame(data['purchases'])
                purchases_df['amount'] = purchases_df['amount'].astype(float)
                purchases_df['days_until_due'] = purchases_df['days_until_due'].fillna(0)
                purchases_df.to_excel(writer, sheet_name='purchases', index=False)
            
            # 8. Payroll data (for HR analytics)
            if data.get('payroll'):
                payroll_df = pd.DataFrame(data['payroll'])
                if not payroll_df.empty:
                    payroll_df['gross_pay'] = payroll_df['gross_pay'].astype(float)
                    payroll_df['net_pay'] = payroll_df['net_pay'].astype(float)
                    payroll_df['overtime_pay'] = payroll_df['overtime_pay'].astype(float)
                payroll_df.to_excel(writer, sheet_name='payroll', index=False)
            
            # 9. KPIs data (for executive dashboard)
            if data.get('kpis'):
                kpis_df = pd.DataFrame(data['kpis'])
                kpis_df['value'] = kpis_df['value'].astype(float)
                kpis_df.to_excel(writer, sheet_name='kpis', index=False)
    
    async def _create_metadata_file(self, filepath: Path, data: Dict[str, Any], date: datetime):
        """Create JSON metadata file for EZBI platform automation"""
        metadata = {
            'file_info': {
                'filename': filepath.name,
                'filepath': str(filepath),
                'size_bytes': filepath.stat().st_size if filepath.exists() else 0,
                'generated_date': date.strftime('%Y-%m-%d'),
                'generated_timestamp': datetime.now().isoformat()
            },
            'data_summary': {
                'total_records': sum(len(data.get(key, [])) for key in data.keys()),
                'sheets': {
                    sheet: len(data.get(sheet, [])) 
                    for sheet in ['dashboard', 'invoices', 'cash_flow', 'ar_aging', 'production', 'purchases', 'payroll', 'kpis']
                }
            },
            'processing_info': {
                'format': 'xlsx',
                'version': '1.0.0',
                'target_platform': 'ezbi_analytics',
                'processing_status': 'ready',
                'ezbi_endpoints': {
                    'data_ingestion': '/api/v1/data/excel/ingest',
                    'webhook_notification': '/api/v1/webhooks/data-source-updated'
                }
            }
        }
        
        metadata_file = filepath.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata file created: {metadata_file}")
    
    def get_latest_data_source(self) -> Optional[Path]:
        """Get the most recent Excel data source file"""
        try:
            excel_files = list(self.export_path.glob("manufacturing_data_source_*.xlsx"))
            if not excel_files:
                return None
            
            # Sort by modification time (newest first)
            excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return excel_files[0]
            
        except Exception as e:
            logger.error(f"Error finding latest data source: {e}")
            return None
    
    def list_data_sources(self, days: int = 30) -> List[Dict[str, Any]]:
        """List recent Excel data source files"""
        try:
            excel_files = list(self.export_path.glob("manufacturing_data_source_*.xlsx"))
            
            file_list = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filepath in excel_files:
                stat = filepath.stat()
                if datetime.fromtimestamp(stat.st_mtime) >= cutoff_date:
                    
                    # Try to find corresponding metadata
                    metadata_file = filepath.with_suffix('.json')
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    
                    file_list.append({
                        'filename': filepath.name,
                        'filepath': str(filepath),
                        'size_bytes': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'metadata': metadata
                    })
            
            # Sort by modification time (newest first)
            file_list.sort(key=lambda x: x['modified'], reverse=True)
            return file_list
            
        except Exception as e:
            logger.error(f"Error listing data sources: {e}")
            return []

# Factory function
def create_excel_data_source(export_path: str = "/app/exports") -> ExcelDataSource:
    """Create Excel data source instance"""
    return ExcelDataSource(export_path)