"""
Excel Export Module for Manufacturing Data Simulator
Generates comprehensive Excel reports with multiple worksheets
"""

import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncpg
import xlsxwriter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import LineChart, BarChart, PieChart, Reference
import logging

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Handles Excel export functionality for manufacturing data"""
    
    def __init__(self):
        self.workbook_style = {
            'header_font': Font(name='Arial', size=12, bold=True, color='FFFFFF'),
            'header_fill': PatternFill(start_color='366092', end_color='366092', fill_type='solid'),
            'data_font': Font(name='Arial', size=10),
            'currency_format': '$#,##0.00',
            'date_format': 'mm/dd/yyyy',
            'percentage_format': '0.00%'
        }
    
    async def export_daily_data(self, db_connection: asyncpg.Connection, export_path: str, date: datetime) -> str:
        """Export all daily data to Excel with multiple worksheets"""
        try:
            # Generate filename with timestamp
            filename = f"manufacturing_data_{date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M')}.xlsx"
            filepath = os.path.join(export_path, filename)
            
            # Fetch all data for the specified date
            data = await self._fetch_daily_data(db_connection, date)
            
            # Create Excel workbook
            await self._create_workbook(filepath, data, date)
            
            logger.info(f"Excel export completed: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export daily data to Excel: {e}")
            raise
    
    async def export_historical_data(self, db_connection: asyncpg.Connection, export_path: str, 
                                   start_date: datetime, end_date: datetime) -> str:
        """Export historical data for a date range"""
        try:
            filename = f"manufacturing_historical_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
            filepath = os.path.join(export_path, filename)
            
            # Fetch historical data
            data = await self._fetch_historical_data(db_connection, start_date, end_date)
            
            # Create historical workbook
            await self._create_historical_workbook(filepath, data, start_date, end_date)
            
            logger.info(f"Historical Excel export completed: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export historical data to Excel: {e}")
            raise
    
    async def _fetch_daily_data(self, conn: asyncpg.Connection, date: datetime) -> Dict[str, pd.DataFrame]:
        """Fetch all data for a specific date"""
        data = {}
        
        # 1. Sales & Invoices
        invoices_query = """
            SELECT i.invoice_id, i.invoice_number, c.company_name as customer,
                   i.date_issued, i.due_date, i.amount, i.status, i.payment_date
            FROM sales.invoices i
            JOIN sales.customers c ON i.customer_id = c.customer_id
            WHERE i.date_issued = $1
            ORDER BY i.invoice_number
        """
        data['invoices'] = pd.DataFrame(await conn.fetch(invoices_query, date))
        
        # 2. Production Orders
        production_query = """
            SELECT po.order_number, p.product_name, c.company_name as customer,
                   po.start_date, po.expected_completion, po.units_ordered, 
                   po.cost_of_goods_sold, po.status
            FROM operations.production_orders po
            JOIN operations.products p ON po.product_id = p.product_id
            JOIN sales.customers c ON po.customer_id = c.customer_id
            WHERE po.start_date = $1
            ORDER BY po.order_number
        """
        data['production'] = pd.DataFrame(await conn.fetch(production_query, date))
        
        # 3. Purchases
        purchases_query = """
            SELECT p.purchase_number, v.vendor_name, p.category, p.amount,
                   p.date_purchased, p.due_date, p.payment_status, p.description
            FROM accounting.purchases p
            JOIN accounting.vendors v ON p.vendor_id = v.vendor_id
            WHERE p.date_purchased = $1
            ORDER BY p.purchase_number
        """
        data['purchases'] = pd.DataFrame(await conn.fetch(purchases_query, date))
        
        # 4. Cash Flow Transactions
        cash_flow_query = """
            SELECT transaction_number, date_recorded, amount, transaction_type,
                   counterparty, description, running_balance
            FROM finance.cash_ledger
            WHERE date_recorded = $1
            ORDER BY transaction_id
        """
        data['cash_flow'] = pd.DataFrame(await conn.fetch(cash_flow_query, date))
        
        # 5. Accounts Receivable Aging
        ar_aging_query = """
            SELECT c.company_name as customer, ar.amount_outstanding,
                   ar.days_outstanding, ar.aging_bucket
            FROM accounting.accounts_receivable ar
            JOIN sales.customers c ON ar.customer_id = c.customer_id
            WHERE ar.as_of_date = $1
            ORDER BY ar.days_outstanding DESC
        """
        data['ar_aging'] = pd.DataFrame(await conn.fetch(ar_aging_query, date))
        
        # 6. Accounts Payable
        ap_query = """
            SELECT v.vendor_name, ap.amount_outstanding, ap.due_date,
                   ap.days_until_due
            FROM accounting.accounts_payable ap
            JOIN accounting.vendors v ON ap.vendor_id = v.vendor_id
            ORDER BY ap.due_date
        """
        data['accounts_payable'] = pd.DataFrame(await conn.fetch(ap_query))
        
        # 7. Payroll (if any for the date)
        payroll_query = """
            SELECT e.employee_number, e.first_name, e.last_name, e.department,
                   pl.gross_pay, pl.deductions, pl.net_pay, pl.overtime_hours
            FROM hr.payroll_log pl
            JOIN hr.employees e ON pl.employee_id = e.employee_id
            WHERE pl.pay_date = $1
            ORDER BY e.employee_number
        """
        data['payroll'] = pd.DataFrame(await conn.fetch(payroll_query, date))
        
        return data
    
    async def _fetch_historical_data(self, conn: asyncpg.Connection, 
                                   start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for date range"""
        data = {}
        
        # Daily cash flow summary
        cash_summary_query = """
            SELECT date_recorded as date,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as inflows,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as outflows,
                   SUM(amount) as net_flow
            FROM finance.cash_ledger
            WHERE date_recorded BETWEEN $1 AND $2
            GROUP BY date_recorded
            ORDER BY date_recorded
        """
        data['daily_cash_summary'] = pd.DataFrame(await conn.fetch(cash_summary_query, start_date, end_date))
        
        # Sales trends
        sales_trends_query = """
            SELECT date_issued as date, COUNT(*) as invoice_count,
                   SUM(amount) as total_sales
            FROM sales.invoices
            WHERE date_issued BETWEEN $1 AND $2
            GROUP BY date_issued
            ORDER BY date_issued
        """
        data['sales_trends'] = pd.DataFrame(await conn.fetch(sales_trends_query, start_date, end_date))
        
        # Production trends
        production_trends_query = """
            SELECT start_date as date, COUNT(*) as orders_started,
                   SUM(cost_of_goods_sold) as total_production_value
            FROM operations.production_orders
            WHERE start_date BETWEEN $1 AND $2
            GROUP BY start_date
            ORDER BY start_date
        """
        data['production_trends'] = pd.DataFrame(await conn.fetch(production_trends_query, start_date, end_date))
        
        return data
    
    async def _create_workbook(self, filepath: str, data: Dict[str, pd.DataFrame], date: datetime):
        """Create comprehensive Excel workbook with multiple worksheets"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # 1. Dashboard/Summary Sheet
            self._create_dashboard_sheet(writer, data, date)
            
            # 2. Individual data sheets
            self._create_invoices_sheet(writer, data.get('invoices', pd.DataFrame()))
            self._create_production_sheet(writer, data.get('production', pd.DataFrame()))
            self._create_purchases_sheet(writer, data.get('purchases', pd.DataFrame()))
            self._create_cash_flow_sheet(writer, data.get('cash_flow', pd.DataFrame()))
            self._create_ar_aging_sheet(writer, data.get('ar_aging', pd.DataFrame()))
            self._create_ap_sheet(writer, data.get('accounts_payable', pd.DataFrame()))
            
            if not data.get('payroll', pd.DataFrame()).empty:
                self._create_payroll_sheet(writer, data.get('payroll', pd.DataFrame()))
        
        # Add charts and formatting using openpyxl
        await self._add_charts_and_formatting(filepath, data)
    
    def _create_dashboard_sheet(self, writer: pd.ExcelWriter, data: Dict[str, pd.DataFrame], date: datetime):
        """Create dashboard summary sheet"""
        # Calculate summary metrics
        total_invoices = len(data.get('invoices', pd.DataFrame()))
        total_sales = data.get('invoices', pd.DataFrame())['amount'].sum() if 'amount' in data.get('invoices', pd.DataFrame()).columns else 0
        total_production = len(data.get('production', pd.DataFrame()))
        total_purchases = data.get('purchases', pd.DataFrame())['amount'].sum() if 'amount' in data.get('purchases', pd.DataFrame()).columns else 0
        net_cash_flow = data.get('cash_flow', pd.DataFrame())['amount'].sum() if 'amount' in data.get('cash_flow', pd.DataFrame()).columns else 0
        
        # Create summary DataFrame
        summary_data = [
            ['Date', date.strftime('%Y-%m-%d')],
            [''],
            ['SALES METRICS', ''],
            ['Total Invoices Created', total_invoices],
            ['Total Sales Amount', f'${total_sales:,.2f}'],
            [''],
            ['PRODUCTION METRICS', ''],
            ['Production Orders Started', total_production],
            [''],
            ['PURCHASE METRICS', ''],
            ['Total Purchases', f'${total_purchases:,.2f}'],
            [''],
            ['CASH FLOW METRICS', ''],
            ['Net Cash Flow', f'${net_cash_flow:,.2f}'],
            [''],
            ['AR AGING SUMMARY', ''],
        ]
        
        # Add AR aging summary if available
        if not data.get('ar_aging', pd.DataFrame()).empty:
            ar_df = data['ar_aging']
            aging_summary = ar_df.groupby('aging_bucket')['amount_outstanding'].sum()
            for bucket, amount in aging_summary.items():
                summary_data.append([f'  {bucket} days', f'${amount:,.2f}'])
        
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Dashboard', index=False)
    
    def _create_invoices_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create invoices sheet with formatting"""
        if df.empty:
            pd.DataFrame([['No invoices created today']], columns=['Message']).to_excel(writer, sheet_name='Invoices', index=False)
            return
        
        # Format currency columns
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='Invoices', index=False)
    
    def _create_production_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create production orders sheet"""
        if df.empty:
            pd.DataFrame([['No production orders started today']], columns=['Message']).to_excel(writer, sheet_name='Production', index=False)
            return
        
        # Format currency columns
        if 'cost_of_goods_sold' in df.columns:
            df['cost_of_goods_sold'] = df['cost_of_goods_sold'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='Production', index=False)
    
    def _create_purchases_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create purchases sheet"""
        if df.empty:
            pd.DataFrame([['No purchases made today']], columns=['Message']).to_excel(writer, sheet_name='Purchases', index=False)
            return
        
        # Format currency columns
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='Purchases', index=False)
    
    def _create_cash_flow_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create cash flow transactions sheet"""
        if df.empty:
            pd.DataFrame([['No cash transactions today']], columns=['Message']).to_excel(writer, sheet_name='Cash Flow', index=False)
            return
        
        # Format currency columns
        currency_cols = ['amount', 'running_balance']
        for col in currency_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='Cash Flow', index=False)
    
    def _create_ar_aging_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create AR aging sheet with summary"""
        if df.empty:
            pd.DataFrame([['No outstanding receivables']], columns=['Message']).to_excel(writer, sheet_name='AR Aging', index=False)
            return
        
        # Format currency columns
        if 'amount_outstanding' in df.columns:
            df['amount_outstanding'] = df['amount_outstanding'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='AR Aging', index=False)
    
    def _create_ap_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create accounts payable sheet"""
        if df.empty:
            pd.DataFrame([['No outstanding payables']], columns=['Message']).to_excel(writer, sheet_name='Accounts Payable', index=False)
            return
        
        # Format currency columns
        if 'amount_outstanding' in df.columns:
            df['amount_outstanding'] = df['amount_outstanding'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='Accounts Payable', index=False)
    
    def _create_payroll_sheet(self, writer: pd.ExcelWriter, df: pd.DataFrame):
        """Create payroll sheet"""
        # Format currency columns
        currency_cols = ['gross_pay', 'deductions', 'net_pay']
        for col in currency_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
        
        df.to_excel(writer, sheet_name='Payroll', index=False)
    
    async def _create_historical_workbook(self, filepath: str, data: Dict[str, pd.DataFrame], 
                                        start_date: datetime, end_date: datetime):
        """Create historical analysis workbook"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Historical summary sheet
            summary_data = [
                ['Report Period', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"],
                ['Generated On', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                [''],
                ['PERIOD ANALYSIS', '']
            ]
            
            # Add period metrics
            if not data.get('daily_cash_summary', pd.DataFrame()).empty:
                cash_df = data['daily_cash_summary']
                total_inflows = cash_df['inflows'].sum()
                total_outflows = cash_df['outflows'].sum()
                net_flow = cash_df['net_flow'].sum()
                
                summary_data.extend([
                    ['Total Inflows', f'${total_inflows:,.2f}'],
                    ['Total Outflows', f'${total_outflows:,.2f}'],
                    ['Net Cash Flow', f'${net_flow:,.2f}']
                ])
            
            summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Data sheets
            for sheet_name, df in data.items():
                if not df.empty:
                    # Format currency columns
                    currency_cols = [col for col in df.columns if any(word in col.lower() for word in ['amount', 'flow', 'sales', 'value'])]
                    for col in currency_cols:
                        if df[col].dtype in ['float64', 'int64']:
                            df[col] = df[col].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '$0.00')
                    
                    df.to_excel(writer, sheet_name=sheet_name.replace('_', ' ').title(), index=False)
    
    async def _add_charts_and_formatting(self, filepath: str, data: Dict[str, pd.DataFrame]):
        """Add charts and advanced formatting to the workbook"""
        try:
            from openpyxl import load_workbook
            from openpyxl.chart import LineChart, BarChart, PieChart, Reference
            from openpyxl.chart.axis import DateAxis
            
            wb = load_workbook(filepath)
            
            # Add AR Aging Pie Chart if data exists
            if 'AR Aging' in wb.sheetnames and not data.get('ar_aging', pd.DataFrame()).empty:
                ws = wb['AR Aging']
                
                # Create pie chart for AR aging
                pie_chart = PieChart()
                pie_chart.title = "Accounts Receivable Aging"
                
                # This would require the data to be properly structured
                # Implementation depends on the specific data layout
                
            # Save the enhanced workbook
            wb.save(filepath)
            
        except Exception as e:
            logger.warning(f"Could not add charts to Excel file: {e}")
    
    def get_latest_export_file(self, export_path: str) -> Optional[str]:
        """Get the most recent Excel export file"""
        try:
            excel_files = [f for f in os.listdir(export_path) if f.endswith('.xlsx') and 'manufacturing_data_' in f]
            
            if not excel_files:
                return None
            
            # Sort by modification time
            excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(export_path, x)), reverse=True)
            
            return os.path.join(export_path, excel_files[0])
            
        except Exception as e:
            logger.error(f"Error finding latest Excel file: {e}")
            return None
    
    def list_export_files(self, export_path: str) -> List[Dict[str, Any]]:
        """List all Excel export files with metadata"""
        try:
            excel_files = [f for f in os.listdir(export_path) if f.endswith('.xlsx') and 'manufacturing_data_' in f]
            
            file_list = []
            for filename in excel_files:
                filepath = os.path.join(export_path, filename)
                stat = os.stat(filepath)
                
                file_list.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': filepath
                })
            
            # Sort by modification time (newest first)
            file_list.sort(key=lambda x: x['modified'], reverse=True)
            
            return file_list
            
        except Exception as e:
            logger.error(f"Error listing Excel files: {e}")
            return []

# Utility functions

def create_excel_exporter() -> ExcelExporter:
    """Create Excel exporter instance"""
    return ExcelExporter()

async def quick_export(db_connection: asyncpg.Connection, export_path: str, date: datetime = None) -> str:
    """Quick export function for immediate use"""
    if date is None:
        date = datetime.now().date()
    
    exporter = ExcelExporter()
    return await exporter.export_daily_data(db_connection, export_path, date)