"""
EZBI Platform Excel Data Reader
Reads Excel data sources and processes them for dashboard display
"""

import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import asyncio
import aiofiles
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ExcelDataSourceInfo:
    """Information about Excel data source file"""
    filename: str
    filepath: str
    size_bytes: int
    generated_date: str
    sheets: Dict[str, int]  # sheet_name -> record_count
    processing_status: str
    last_processed: Optional[datetime] = None

class EZBIExcelReader:
    """Reads and processes Excel data sources for EZBI platform"""
    
    def __init__(self, data_source_path: str = "/app/data-sources"):
        self.data_source_path = Path(data_source_path)
        self.data_source_path.mkdir(exist_ok=True)
        
        # Processing configuration
        self.processing_config = {
            'batch_size': 1000,
            'max_file_size_mb': 50,
            'supported_formats': ['.xlsx', '.xls'],
            'required_sheets': ['metadata', 'dashboard', 'kpis'],
            'optional_sheets': ['invoices', 'cash_flow', 'ar_aging', 'production', 'purchases', 'payroll']
        }
        
        # Data transformation mappings
        self.column_mappings = {
            'invoices': {
                'amount': 'sales_amount',
                'customer_name': 'customer',
                'date_issued': 'transaction_date',
                'days_overdue': 'overdue_days'
            },
            'cash_flow': {
                'amount': 'cash_amount',
                'flow_direction': 'direction',
                'date_recorded': 'transaction_date'
            },
            'ar_aging': {
                'amount_outstanding': 'outstanding_amount',
                'customer_name': 'customer',
                'aging_bucket': 'aging_category'
            }
        }
    
    async def process_excel_data_source(self, excel_file_path: str) -> Dict[str, Any]:
        """Process Excel data source file for EZBI platform"""
        try:
            filepath = Path(excel_file_path)
            
            # Validate file
            if not await self._validate_excel_file(filepath):
                raise ValueError(f"Invalid Excel data source file: {filepath}")
            
            # Read all sheets
            raw_data = await self._read_excel_sheets(filepath)
            
            # Process and transform data
            processed_data = await self._transform_data_for_ezbi(raw_data)
            
            # Generate dashboard-ready data
            dashboard_data = await self._generate_dashboard_data(processed_data)
            
            # Create processing report
            processing_report = {
                'file_info': {
                    'filename': filepath.name,
                    'processed_at': datetime.now().isoformat(),
                    'file_size': filepath.stat().st_size,
                    'status': 'success'
                },
                'data_summary': {
                    'total_records': sum(len(data) for data in processed_data.values() if isinstance(data, list)),
                    'sheets_processed': list(processed_data.keys()),
                    'dashboard_charts': len(dashboard_data.get('charts', [])),
                    'kpis_calculated': len(dashboard_data.get('kpis', []))
                },
                'raw_data': processed_data,
                'dashboard_data': dashboard_data
            }
            
            logger.info(f"Excel data source processed successfully: {filepath.name}")
            return processing_report
            
        except Exception as e:
            logger.error(f"Failed to process Excel data source: {e}")
            raise
    
    async def _validate_excel_file(self, filepath: Path) -> bool:
        """Validate Excel file for processing"""
        try:
            # Check file exists and size
            if not filepath.exists():
                logger.error(f"Excel file not found: {filepath}")
                return False
            
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            if file_size_mb > self.processing_config['max_file_size_mb']:
                logger.error(f"Excel file too large: {file_size_mb:.2f}MB")
                return False
            
            # Check file format
            if filepath.suffix not in self.processing_config['supported_formats']:
                logger.error(f"Unsupported file format: {filepath.suffix}")
                return False
            
            # Check required sheets exist
            try:
                excel_file = pd.ExcelFile(filepath)
                available_sheets = excel_file.sheet_names
                
                missing_sheets = [sheet for sheet in self.processing_config['required_sheets'] 
                                if sheet not in available_sheets]
                
                if missing_sheets:
                    logger.error(f"Missing required sheets: {missing_sheets}")
                    return False
                
            except Exception as e:
                logger.error(f"Error reading Excel file structure: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Excel file: {e}")
            return False
    
    async def _read_excel_sheets(self, filepath: Path) -> Dict[str, pd.DataFrame]:
        """Read all sheets from Excel file"""
        try:
            raw_data = {}
            
            # Read all sheets
            excel_file = pd.ExcelFile(filepath)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    raw_data[sheet_name] = df
                    logger.debug(f"Read sheet '{sheet_name}': {len(df)} rows")
                except Exception as e:
                    logger.warning(f"Error reading sheet '{sheet_name}': {e}")
                    continue
            
            return raw_data
            
        except Exception as e:
            logger.error(f"Error reading Excel sheets: {e}")
            raise
    
    async def _transform_data_for_ezbi(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Transform raw Excel data for EZBI platform consumption"""
        try:
            processed_data = {}
            
            # Process each sheet
            for sheet_name, df in raw_data.items():
                if sheet_name == 'metadata':
                    # Convert metadata to dict
                    processed_data[sheet_name] = self._process_metadata_sheet(df)
                
                elif sheet_name in ['dashboard', 'kpis']:
                    # Process dashboard and KPI data
                    processed_data[sheet_name] = self._process_metrics_sheet(df)
                
                elif sheet_name in ['invoices', 'cash_flow', 'ar_aging', 'production', 'purchases', 'payroll']:
                    # Process transaction data
                    processed_data[sheet_name] = self._process_transaction_sheet(df, sheet_name)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error transforming data for EZBI: {e}")
            raise
    
    def _process_metadata_sheet(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process metadata sheet into dictionary"""
        try:
            metadata = {}
            
            for _, row in df.iterrows():
                if len(row) >= 2:
                    key = str(row.iloc[0])
                    value = row.iloc[1]
                    
                    # Convert to appropriate type
                    if pd.isna(value):
                        metadata[key] = None
                    elif isinstance(value, (int, float)):
                        metadata[key] = value
                    else:
                        metadata[key] = str(value)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error processing metadata sheet: {e}")
            return {}
    
    def _process_metrics_sheet(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process dashboard/KPI metrics sheet"""
        try:
            metrics = []
            
            for _, row in df.iterrows():
                metric = {
                    'name': row.get('metric', row.get('kpi', 'unknown')),
                    'value': self._safe_numeric_conversion(row.get('value', 0)),
                    'date': self._safe_date_conversion(row.get('date')),
                    'category': row.get('category', 'general')
                }
                
                # Add any additional columns as metadata
                for col in df.columns:
                    if col not in ['metric', 'kpi', 'value', 'date', 'category']:
                        metric[col] = row.get(col)
                
                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error processing metrics sheet: {e}")
            return []
    
    def _process_transaction_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """Process transaction data sheets"""
        try:
            # Apply column mappings if available
            if sheet_name in self.column_mappings:
                df = df.rename(columns=self.column_mappings[sheet_name])
            
            # Convert DataFrame to list of dictionaries
            transactions = []
            
            for _, row in df.iterrows():
                transaction = {}
                
                for col in df.columns:
                    value = row[col]
                    
                    # Handle different data types
                    if pd.isna(value):
                        transaction[col] = None
                    elif 'amount' in col.lower() or 'value' in col.lower():
                        transaction[col] = self._safe_numeric_conversion(value)
                    elif 'date' in col.lower():
                        transaction[col] = self._safe_date_conversion(value)
                    elif isinstance(value, (int, float)):
                        transaction[col] = value
                    else:
                        transaction[col] = str(value)
                
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error processing transaction sheet '{sheet_name}': {e}")
            return []
    
    async def _generate_dashboard_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard-ready data from processed Excel data"""
        try:
            dashboard_data = {
                'charts': [],
                'kpis': [],
                'tables': [],
                'alerts': []
            }
            
            # 1. Generate KPI widgets
            if 'kpis' in processed_data:
                dashboard_data['kpis'] = self._generate_kpi_widgets(processed_data['kpis'])
            
            # 2. Generate chart configurations
            dashboard_data['charts'] = await self._generate_chart_configs(processed_data)
            
            # 3. Generate data tables
            dashboard_data['tables'] = self._generate_data_tables(processed_data)
            
            # 4. Generate alerts
            dashboard_data['alerts'] = self._generate_alerts(processed_data)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {'charts': [], 'kpis': [], 'tables': [], 'alerts': []}
    
    def _generate_kpi_widgets(self, kpis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate KPI widgets for dashboard"""
        try:
            widgets = []
            
            for kpi in kpis:
                widget = {
                    'type': 'kpi',
                    'title': kpi['name'].replace('_', ' ').title(),
                    'value': kpi['value'],
                    'category': kpi.get('category', 'general'),
                    'format': self._determine_value_format(kpi['name'], kpi['value']),
                    'trend': self._calculate_trend(kpi),
                    'color': self._determine_kpi_color(kpi['name'], kpi['value'])
                }
                widgets.append(widget)
            
            return widgets
            
        except Exception as e:
            logger.error(f"Error generating KPI widgets: {e}")
            return []
    
    async def _generate_chart_configs(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate chart configurations for dashboard"""
        try:
            charts = []
            
            # 1. Cash Flow Chart
            if 'cash_flow' in processed_data:
                charts.append(self._create_cash_flow_chart(processed_data['cash_flow']))
            
            # 2. AR Aging Chart
            if 'ar_aging' in processed_data:
                charts.append(self._create_ar_aging_chart(processed_data['ar_aging']))
            
            # 3. Sales Chart
            if 'invoices' in processed_data:
                charts.append(self._create_sales_chart(processed_data['invoices']))
            
            # 4. Production Chart
            if 'production' in processed_data:
                charts.append(self._create_production_chart(processed_data['production']))
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating chart configurations: {e}")
            return []
    
    def _create_cash_flow_chart(self, cash_flow_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create cash flow chart configuration"""
        try:
            # Group by flow direction
            inflows = [t for t in cash_flow_data if t.get('flow_direction') == 'Inflow']
            outflows = [t for t in cash_flow_data if t.get('flow_direction') == 'Outflow']
            
            total_inflows = sum(t.get('amount_abs', 0) for t in inflows)
            total_outflows = sum(t.get('amount_abs', 0) for t in outflows)
            
            return {
                'type': 'bar',
                'title': 'Daily Cash Flow',
                'data': {
                    'labels': ['Inflows', 'Outflows'],
                    'datasets': [{
                        'label': 'Cash Flow',
                        'data': [total_inflows, total_outflows],
                        'backgroundColor': ['#10B981', '#EF4444']
                    }]
                },
                'options': {
                    'responsive': True,
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'ticks': {
                                'callback': 'function(value) { return "$" + value.toLocaleString(); }'
                            }
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating cash flow chart: {e}")
            return {'type': 'bar', 'title': 'Cash Flow', 'data': {}}
    
    def _create_ar_aging_chart(self, ar_aging_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create AR aging chart configuration"""
        try:
            # Group by aging bucket
            aging_buckets = {}
            for record in ar_aging_data:
                bucket = record.get('aging_category', record.get('aging_bucket', 'Unknown'))
                amount = record.get('outstanding_amount', record.get('amount_outstanding', 0))
                aging_buckets[bucket] = aging_buckets.get(bucket, 0) + amount
            
            return {
                'type': 'doughnut',
                'title': 'Accounts Receivable Aging',
                'data': {
                    'labels': list(aging_buckets.keys()),
                    'datasets': [{
                        'data': list(aging_buckets.values()),
                        'backgroundColor': ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'position': 'bottom'
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating AR aging chart: {e}")
            return {'type': 'doughnut', 'title': 'AR Aging', 'data': {}}
    
    def _create_sales_chart(self, invoices_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create sales chart configuration"""
        try:
            # Calculate total sales
            total_sales = sum(inv.get('sales_amount', inv.get('amount', 0)) for inv in invoices_data)
            invoice_count = len(invoices_data)
            avg_invoice = total_sales / invoice_count if invoice_count > 0 else 0
            
            return {
                'type': 'line',
                'title': 'Daily Sales Performance',
                'data': {
                    'labels': ['Sales Total', 'Invoice Count', 'Average Invoice'],
                    'datasets': [{
                        'label': 'Sales Metrics',
                        'data': [total_sales, invoice_count, avg_invoice],
                        'borderColor': '#3B82F6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)'
                    }]
                },
                'options': {
                    'responsive': True,
                    'scales': {
                        'y': {
                            'beginAtZero': True
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating sales chart: {e}")
            return {'type': 'line', 'title': 'Sales Performance', 'data': {}}
    
    def _create_production_chart(self, production_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create production chart configuration"""
        try:
            # Group by status
            status_counts = {}
            for order in production_data:
                status = order.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'type': 'pie',
                'title': 'Production Orders by Status',
                'data': {
                    'labels': list(status_counts.keys()),
                    'datasets': [{
                        'data': list(status_counts.values()),
                        'backgroundColor': ['#F59E0B', '#10B981', '#EF4444', '#6B7280']
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'position': 'right'
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating production chart: {e}")
            return {'type': 'pie', 'title': 'Production Status', 'data': {}}
    
    def _generate_data_tables(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate data table configurations"""
        try:
            tables = []
            
            # Create table for each data type
            for data_type, data in processed_data.items():
                if data_type in ['invoices', 'cash_flow', 'ar_aging', 'production', 'purchases']:
                    if isinstance(data, list) and len(data) > 0:
                        table = {
                            'type': 'data_table',
                            'title': data_type.replace('_', ' ').title(),
                            'data': data[:50],  # Limit to first 50 rows
                            'columns': list(data[0].keys()) if data else [],
                            'pagination': True,
                            'search': True,
                            'export': True
                        }
                        tables.append(table)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error generating data tables: {e}")
            return []
    
    def _generate_alerts(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on data analysis"""
        try:
            alerts = []
            
            # Cash flow alerts
            if 'kpis' in processed_data:
                cash_flow_kpi = next((kpi for kpi in processed_data['kpis'] if kpi['name'] == 'net_cash_flow'), None)
                if cash_flow_kpi and cash_flow_kpi['value'] < 0:
                    alerts.append({
                        'type': 'warning',
                        'title': 'Negative Cash Flow',
                        'message': f'Daily cash flow is negative: ${cash_flow_kpi["value"]:,.2f}',
                        'priority': 'high'
                    })
            
            # AR aging alerts
            if 'ar_aging' in processed_data:
                overdue_amount = sum(
                    record.get('outstanding_amount', record.get('amount_outstanding', 0))
                    for record in processed_data['ar_aging']
                    if record.get('aging_category', record.get('aging_bucket', '')).startswith('9')
                )
                
                if overdue_amount > 10000:  # Alert if over $10k overdue
                    alerts.append({
                        'type': 'error',
                        'title': 'High Overdue Receivables',
                        'message': f'${overdue_amount:,.2f} in 90+ day overdue receivables',
                        'priority': 'critical'
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return []
    
    def _safe_numeric_conversion(self, value: Any) -> Union[float, int]:
        """Safely convert value to numeric type"""
        try:
            if pd.isna(value):
                return 0
            elif isinstance(value, (int, float)):
                return value
            elif isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = value.replace('$', '').replace(',', '').strip()
                return float(cleaned) if '.' in cleaned else int(cleaned)
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_date_conversion(self, value: Any) -> Optional[str]:
        """Safely convert value to date string"""
        try:
            if pd.isna(value):
                return None
            elif isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, str):
                # Try to parse as datetime
                parsed = pd.to_datetime(value)
                return parsed.strftime('%Y-%m-%d')
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def _determine_value_format(self, name: str, value: Any) -> str:
        """Determine appropriate format for KPI value"""
        if 'amount' in name.lower() or 'sales' in name.lower() or 'cash' in name.lower():
            return 'currency'
        elif 'percentage' in name.lower() or 'rate' in name.lower():
            return 'percentage'
        elif isinstance(value, float):
            return 'decimal'
        else:
            return 'integer'
    
    def _calculate_trend(self, kpi: Dict[str, Any]) -> str:
        """Calculate trend for KPI (placeholder - would need historical data)"""
        # This would require historical data comparison
        return 'stable'
    
    def _determine_kpi_color(self, name: str, value: Any) -> str:
        """Determine color for KPI based on name and value"""
        if 'cash' in name.lower() and value < 0:
            return 'red'
        elif 'sales' in name.lower() or 'revenue' in name.lower():
            return 'green'
        elif 'overdue' in name.lower() or 'aging' in name.lower():
            return 'orange'
        else:
            return 'blue'

# Factory function
def create_ezbi_excel_reader(data_source_path: str = "/app/data-sources") -> EZBIExcelReader:
    """Create EZBI Excel reader instance"""
    return EZBIExcelReader(data_source_path)