"""
Cash Flow Prediction Engine for Manufacturing Company
Combines PostgreSQL operational data with Excel business planning data for accurate cash flow forecasting
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
from dataclasses import dataclass
import json
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import asyncpg

from realistic_excel_generator import RealisticExcelGenerator

logger = logging.getLogger(__name__)

@dataclass
class CashFlowPredictionConfig:
    """Configuration for cash flow prediction engine"""
    database_url: str
    excel_data_path: str = "/app/business-planning"
    prediction_horizon_days: int = 90
    confidence_interval: float = 0.95
    model_type: str = "ensemble"  # 'linear', 'random_forest', 'ensemble'
    retrain_frequency_days: int = 7

class CashFlowPredictionEngine:
    """Predicts cash flow by combining operational data (PostgreSQL) with business planning data (Excel)"""
    
    def __init__(self, config: CashFlowPredictionConfig):
        self.config = config
        self.excel_generator = RealisticExcelGenerator(config.excel_data_path)
        self.connection_pool = None
        self.models = {}
        self.last_training_date = None
        
        # Prediction components
        self.prediction_components = {
            'inflows': {
                'customer_payments': 'postgresql',  # From AR aging and payment patterns
                'new_orders': 'excel',             # From customer forecasts
                'seasonal_adjustments': 'excel'    # From customer forecasts
            },
            'outflows': {
                'supplier_payments': 'excel',      # From supplier contracts
                'payroll': 'postgresql',           # From HR data
                'operating_expenses': 'excel',     # From budget planning
                'capital_expenditure': 'excel',    # From budget planning
                'inventory_purchases': 'excel'     # From inventory planning
            }
        }
    
    async def initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.config.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Cash flow prediction engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    async def predict_cash_flow(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive cash flow predictions"""
        if not self.connection_pool:
            await self.initialize_connection_pool()
        
        try:
            # Step 1: Extract operational data from PostgreSQL
            operational_data = await self._extract_operational_data(start_date, end_date)
            
            # Step 2: Load business planning data from Excel
            planning_data = await self._load_business_planning_data(start_date, end_date)
            
            # Step 3: Generate historical cash flow patterns
            historical_data = await self._generate_historical_cash_flow_data(start_date - timedelta(days=180), start_date)
            
            # Step 4: Train prediction models (if needed)
            if self._should_retrain_models():
                await self._train_prediction_models(historical_data, operational_data, planning_data)
            
            # Step 5: Generate predictions
            predictions = await self._generate_predictions(operational_data, planning_data, start_date, end_date)
            
            # Step 6: Calculate confidence intervals and scenarios
            scenarios = await self._calculate_scenarios(predictions, operational_data, planning_data)
            
            # Step 7: Generate insights and recommendations
            insights = await self._generate_insights(predictions, scenarios, operational_data, planning_data)
            
            return {
                'prediction_info': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'generated_at': datetime.now().isoformat(),
                    'model_type': self.config.model_type,
                    'confidence_interval': self.config.confidence_interval,
                    'data_sources': ['postgresql_operational', 'excel_business_planning']
                },
                'historical_data': historical_data,
                'predictions': predictions,
                'scenarios': scenarios,
                'insights': insights,
                'data_quality': await self._assess_data_quality(operational_data, planning_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate cash flow prediction: {e}")
            raise
    
    async def _extract_operational_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Extract operational data from PostgreSQL"""
        operational_data = {}
        
        async with self.connection_pool.acquire() as conn:
            # Historical cash flow patterns
            cash_flow_query = """
                SELECT 
                    date_recorded,
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as daily_inflows,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as daily_outflows,
                    SUM(amount) as net_daily_flow
                FROM finance.cash_ledger
                WHERE date_recorded >= $1 AND date_recorded <= $2
                GROUP BY date_recorded
                ORDER BY date_recorded
            """
            cash_flow_rows = await conn.fetch(cash_flow_query, start_date - timedelta(days=180), end_date)
            operational_data['historical_cash_flow'] = [dict(row) for row in cash_flow_rows]
            
            # Customer payment patterns
            payment_patterns_query = """
                SELECT 
                    c.company_name,
                    AVG(i.payment_date - i.date_issued) as avg_payment_days,
                    STDDEV(i.payment_date - i.date_issued) as payment_variability,
                    COUNT(*) as payment_count,
                    SUM(i.amount) as total_payments,
                    AVG(i.amount) as avg_payment_amount
                FROM sales.customers c
                JOIN sales.invoices i ON c.customer_id = i.customer_id
                WHERE i.payment_date IS NOT NULL
                AND i.date_issued >= $1
                GROUP BY c.customer_id, c.company_name
                ORDER BY total_payments DESC
            """
            payment_rows = await conn.fetch(payment_patterns_query, start_date - timedelta(days=180))
            operational_data['customer_payment_patterns'] = [dict(row) for row in payment_rows]
            
            # Current accounts receivable
            ar_query = """
                SELECT 
                    aging_bucket,
                    SUM(amount_outstanding) as total_outstanding,
                    COUNT(*) as invoice_count,
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
            """
            ar_rows = await conn.fetch(ar_query, start_date)
            operational_data['accounts_receivable'] = [dict(row) for row in ar_rows]
            
            # Payroll patterns
            payroll_query = """
                SELECT 
                    DATE_TRUNC('month', pay_date) as pay_month,
                    SUM(gross_pay) as total_gross_pay,
                    COUNT(*) as employee_count,
                    AVG(gross_pay) as avg_gross_pay
                FROM hr.payroll_records
                WHERE pay_date >= $1
                GROUP BY DATE_TRUNC('month', pay_date)
                ORDER BY pay_month
            """
            payroll_rows = await conn.fetch(payroll_query, start_date - timedelta(days=180))
            operational_data['payroll_patterns'] = [dict(row) for row in payroll_rows]
            
            # Vendor payment patterns
            vendor_payment_query = """
                SELECT 
                    v.vendor_name,
                    AVG(p.payment_date - p.date_purchased) as avg_payment_days,
                    SUM(p.amount) as total_payments,
                    COUNT(*) as payment_count,
                    p.category
                FROM accounting.vendors v
                JOIN accounting.purchases p ON v.vendor_id = p.vendor_id
                WHERE p.payment_date IS NOT NULL
                AND p.date_purchased >= $1
                GROUP BY v.vendor_id, v.vendor_name, p.category
                ORDER BY total_payments DESC
            """
            vendor_rows = await conn.fetch(vendor_payment_query, start_date - timedelta(days=180))
            operational_data['vendor_payment_patterns'] = [dict(row) for row in vendor_rows]
        
        return operational_data
    
    async def _load_business_planning_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Load business planning data from Excel files"""
        planning_data = {}
        
        try:
            # Generate fresh business planning files
            year = start_date.year
            
            # Generate all business planning files
            supplier_contracts_file = self.excel_generator.generate_supplier_contracts(year)
            customer_forecasts_file = self.excel_generator.generate_customer_forecasts(year)
            budget_planning_file = self.excel_generator.generate_budget_planning(year)
            inventory_planning_file = self.excel_generator.generate_inventory_planning(year)
            
            # Load supplier contracts
            supplier_contracts_df = pd.read_excel(supplier_contracts_file, sheet_name='Supplier_Contracts')
            payment_schedule_df = pd.read_excel(supplier_contracts_file, sheet_name='Payment_Schedule')
            
            planning_data['supplier_contracts'] = supplier_contracts_df.to_dict('records')
            planning_data['payment_schedule'] = payment_schedule_df.to_dict('records')
            
            # Load customer forecasts
            customer_forecasts_df = pd.read_excel(customer_forecasts_file, sheet_name='Customer_Forecasts')
            sales_pipeline_df = pd.read_excel(customer_forecasts_file, sheet_name='Sales_Pipeline')
            
            planning_data['customer_forecasts'] = customer_forecasts_df.to_dict('records')
            planning_data['sales_pipeline'] = sales_pipeline_df.to_dict('records')
            
            # Load budget planning
            operating_budget_df = pd.read_excel(budget_planning_file, sheet_name='Operating_Budget')
            capex_df = pd.read_excel(budget_planning_file, sheet_name='Capital_Expenditure')
            cash_flow_projection_df = pd.read_excel(budget_planning_file, sheet_name='Cash_Flow_Projection')
            
            planning_data['operating_budget'] = operating_budget_df.to_dict('records')
            planning_data['capital_expenditure'] = capex_df.to_dict('records')
            planning_data['budget_cash_flow_projection'] = cash_flow_projection_df.to_dict('records')
            
            # Load inventory planning
            inventory_planning_df = pd.read_excel(inventory_planning_file, sheet_name='Inventory_Planning')
            procurement_schedule_df = pd.read_excel(inventory_planning_file, sheet_name='Procurement_Schedule')
            
            planning_data['inventory_planning'] = inventory_planning_df.to_dict('records')
            planning_data['procurement_schedule'] = procurement_schedule_df.to_dict('records')
            
            logger.info("Business planning data loaded successfully")
            return planning_data
            
        except Exception as e:
            logger.error(f"Failed to load business planning data: {e}")
            raise
    
    async def _generate_historical_cash_flow_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate historical cash flow data for model training"""
        historical_data = {
            'daily_cash_flow': [],
            'weekly_patterns': [],
            'monthly_patterns': [],
            'seasonal_patterns': []
        }
        
        async with self.connection_pool.acquire() as conn:
            # Daily cash flow
            daily_query = """
                SELECT 
                    date_recorded,
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as daily_inflows,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as daily_outflows,
                    SUM(amount) as net_daily_flow,
                    EXTRACT(DOW FROM date_recorded) as day_of_week,
                    EXTRACT(DAY FROM date_recorded) as day_of_month,
                    EXTRACT(MONTH FROM date_recorded) as month,
                    EXTRACT(QUARTER FROM date_recorded) as quarter
                FROM finance.cash_ledger
                WHERE date_recorded >= $1 AND date_recorded <= $2
                GROUP BY date_recorded
                ORDER BY date_recorded
            """
            daily_rows = await conn.fetch(daily_query, start_date, end_date)
            historical_data['daily_cash_flow'] = [dict(row) for row in daily_rows]
            
            # Weekly patterns
            weekly_query = """
                SELECT 
                    EXTRACT(DOW FROM date_recorded) as day_of_week,
                    AVG(CASE WHEN amount > 0 THEN amount ELSE 0 END) as avg_inflows,
                    AVG(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as avg_outflows,
                    AVG(amount) as avg_net_flow,
                    COUNT(*) as transaction_count
                FROM finance.cash_ledger
                WHERE date_recorded >= $1 AND date_recorded <= $2
                GROUP BY EXTRACT(DOW FROM date_recorded)
                ORDER BY day_of_week
            """
            weekly_rows = await conn.fetch(weekly_query, start_date, end_date)
            historical_data['weekly_patterns'] = [dict(row) for row in weekly_rows]
            
            # Monthly patterns
            monthly_query = """
                SELECT 
                    EXTRACT(MONTH FROM date_recorded) as month,
                    AVG(CASE WHEN amount > 0 THEN amount ELSE 0 END) as avg_inflows,
                    AVG(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as avg_outflows,
                    AVG(amount) as avg_net_flow,
                    COUNT(*) as transaction_count
                FROM finance.cash_ledger
                WHERE date_recorded >= $1 AND date_recorded <= $2
                GROUP BY EXTRACT(MONTH FROM date_recorded)
                ORDER BY month
            """
            monthly_rows = await conn.fetch(monthly_query, start_date, end_date)
            historical_data['monthly_patterns'] = [dict(row) for row in monthly_rows]
        
        return historical_data
    
    def _should_retrain_models(self) -> bool:
        """Check if models need retraining"""
        if self.last_training_date is None:
            return True
        
        days_since_training = (datetime.now() - self.last_training_date).days
        return days_since_training >= self.config.retrain_frequency_days
    
    async def _train_prediction_models(self, historical_data: Dict[str, Any], operational_data: Dict[str, Any], planning_data: Dict[str, Any]):
        """Train prediction models using historical and planning data"""
        try:
            # Prepare training data
            training_features, training_targets = self._prepare_training_data(historical_data, operational_data, planning_data)
            
            if len(training_features) < 30:  # Need minimum data for training
                logger.warning("Insufficient data for model training, using rule-based predictions")
                return
            
            # Train models based on configuration
            if self.config.model_type == 'linear' or self.config.model_type == 'ensemble':
                linear_model = LinearRegression()
                linear_model.fit(training_features, training_targets)
                self.models['linear'] = linear_model
            
            if self.config.model_type == 'random_forest' or self.config.model_type == 'ensemble':
                rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
                rf_model.fit(training_features, training_targets)
                self.models['random_forest'] = rf_model
            
            self.last_training_date = datetime.now()
            logger.info(f"Models trained successfully with {len(training_features)} data points")
            
        except Exception as e:
            logger.error(f"Failed to train prediction models: {e}")
            # Fall back to rule-based predictions
    
    def _prepare_training_data(self, historical_data: Dict[str, Any], operational_data: Dict[str, Any], planning_data: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for machine learning models"""
        features = []
        targets = []
        
        daily_data = historical_data.get('daily_cash_flow', [])
        
        for i, day_data in enumerate(daily_data):
            if i < 7:  # Need at least 7 days of history for features
                continue
            
            # Features: last 7 days of data + day of week + month + seasonal indicators
            feature_row = []
            
            # Historical cash flow features (last 7 days)
            for j in range(7):
                prev_day = daily_data[i - j - 1]
                feature_row.extend([
                    float(prev_day.get('daily_inflows', 0)),
                    float(prev_day.get('daily_outflows', 0)),
                    float(prev_day.get('net_daily_flow', 0))
                ])
            
            # Time-based features
            feature_row.extend([
                float(day_data.get('day_of_week', 0)),
                float(day_data.get('day_of_month', 0)),
                float(day_data.get('month', 0)),
                float(day_data.get('quarter', 0))
            ])
            
            # Seasonal indicators
            feature_row.extend([
                1.0 if day_data.get('month') in [11, 12, 1] else 0.0,  # Holiday season
                1.0 if day_data.get('month') in [3, 4, 5] else 0.0,     # Spring
                1.0 if day_data.get('month') in [6, 7, 8] else 0.0,     # Summer
                1.0 if day_data.get('month') in [9, 10] else 0.0        # Fall
            ])
            
            features.append(feature_row)
            targets.append(float(day_data.get('net_daily_flow', 0)))
        
        return np.array(features), np.array(targets)
    
    async def _generate_predictions(self, operational_data: Dict[str, Any], planning_data: Dict[str, Any], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate cash flow predictions"""
        predictions = {
            'daily_predictions': [],
            'weekly_summary': [],
            'monthly_summary': [],
            'cumulative_cash_flow': []
        }
        
        # Generate daily predictions
        current_date = start_date
        cumulative_balance = await self._get_current_cash_balance()
        
        while current_date <= end_date:
            # Predict inflows
            predicted_inflows = await self._predict_daily_inflows(current_date, operational_data, planning_data)
            
            # Predict outflows
            predicted_outflows = await self._predict_daily_outflows(current_date, operational_data, planning_data)
            
            # Calculate net flow
            net_flow = predicted_inflows - predicted_outflows
            cumulative_balance += net_flow
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(predicted_inflows, predicted_outflows, current_date)
            
            daily_prediction = {
                'date': current_date.strftime('%Y-%m-%d'),
                'predicted_inflows': round(predicted_inflows, 2),
                'predicted_outflows': round(predicted_outflows, 2),
                'net_cash_flow': round(net_flow, 2),
                'cumulative_balance': round(cumulative_balance, 2),
                'confidence_intervals': confidence_intervals,
                'prediction_components': {
                    'customer_payments': await self._predict_customer_payments(current_date, operational_data),
                    'supplier_payments': await self._predict_supplier_payments(current_date, planning_data),
                    'payroll_payments': await self._predict_payroll_payments(current_date, operational_data),
                    'operating_expenses': await self._predict_operating_expenses(current_date, planning_data),
                    'capital_expenditure': await self._predict_capital_expenditure(current_date, planning_data)
                }
            }
            
            predictions['daily_predictions'].append(daily_prediction)
            current_date += timedelta(days=1)
        
        # Generate weekly and monthly summaries
        predictions['weekly_summary'] = self._generate_weekly_summary(predictions['daily_predictions'])
        predictions['monthly_summary'] = self._generate_monthly_summary(predictions['daily_predictions'])
        
        return predictions
    
    async def _predict_daily_inflows(self, date: datetime, operational_data: Dict[str, Any], planning_data: Dict[str, Any]) -> float:
        """Predict daily cash inflows"""
        total_inflows = 0.0
        
        # Customer payments (from AR aging and payment patterns)
        customer_payments = await self._predict_customer_payments(date, operational_data)
        total_inflows += customer_payments
        
        # New orders (from customer forecasts)
        new_order_payments = await self._predict_new_order_payments(date, planning_data)
        total_inflows += new_order_payments
        
        return total_inflows
    
    async def _predict_daily_outflows(self, date: datetime, operational_data: Dict[str, Any], planning_data: Dict[str, Any]) -> float:
        """Predict daily cash outflows"""
        total_outflows = 0.0
        
        # Supplier payments
        supplier_payments = await self._predict_supplier_payments(date, planning_data)
        total_outflows += supplier_payments
        
        # Payroll payments
        payroll_payments = await self._predict_payroll_payments(date, operational_data)
        total_outflows += payroll_payments
        
        # Operating expenses
        operating_expenses = await self._predict_operating_expenses(date, planning_data)
        total_outflows += operating_expenses
        
        # Capital expenditure
        capex = await self._predict_capital_expenditure(date, planning_data)
        total_outflows += capex
        
        return total_outflows
    
    async def _predict_customer_payments(self, date: datetime, operational_data: Dict[str, Any]) -> float:
        """Predict customer payments based on AR aging and payment patterns"""
        predicted_payments = 0.0
        
        # Get AR aging data
        ar_data = operational_data.get('accounts_receivable', [])
        payment_patterns = operational_data.get('customer_payment_patterns', [])
        
        # Calculate expected payments based on aging buckets
        for ar_bucket in ar_data:
            bucket = ar_bucket['aging_bucket']
            outstanding = float(ar_bucket['total_outstanding'])
            
            # Payment probability based on aging
            if bucket == '0-30':
                payment_probability = 0.05  # 5% daily payment rate
            elif bucket == '31-60':
                payment_probability = 0.08  # Higher urgency
            elif bucket == '61-90':
                payment_probability = 0.10  # Even higher urgency
            else:  # 90+
                payment_probability = 0.03  # Lower probability due to disputes
            
            predicted_payments += outstanding * payment_probability
        
        # Add seasonality adjustments
        if date.month in [11, 12]:  # Holiday season - slower payments
            predicted_payments *= 0.8
        elif date.month in [1, 2]:  # Post-holiday - faster payments
            predicted_payments *= 1.2
        
        return predicted_payments
    
    async def _predict_new_order_payments(self, date: datetime, planning_data: Dict[str, Any]) -> float:
        """Predict payments from new orders based on customer forecasts"""
        predicted_payments = 0.0
        
        # Get customer forecasts
        forecasts = planning_data.get('customer_forecasts', [])
        
        for forecast in forecasts:
            forecast_month = forecast.get('forecast_month', '')
            if forecast_month.startswith(date.strftime('%Y-%m')):
                monthly_value = float(forecast.get('total_monthly_value', 0))
                payment_terms = int(forecast.get('payment_terms', 30))
                
                # Assume orders are spread evenly throughout the month
                # and payments come based on payment terms
                daily_orders = monthly_value / 30
                
                # Payment comes after payment terms (simplified)
                payment_date = date + timedelta(days=payment_terms)
                order_date = date - timedelta(days=payment_terms)
                
                if order_date.month == date.month:
                    predicted_payments += daily_orders
        
        return predicted_payments
    
    async def _predict_supplier_payments(self, date: datetime, planning_data: Dict[str, Any]) -> float:
        """Predict supplier payments based on contracts and payment schedule"""
        predicted_payments = 0.0
        
        # Get payment schedule
        payment_schedule = planning_data.get('payment_schedule', [])
        
        for payment in payment_schedule:
            payment_date_str = payment.get('payment_date', '')
            if payment_date_str == date.strftime('%Y-%m-%d'):
                payment_amount = float(payment.get('payment_amount', 0))
                predicted_payments += payment_amount
        
        return predicted_payments
    
    async def _predict_payroll_payments(self, date: datetime, operational_data: Dict[str, Any]) -> float:
        """Predict payroll payments based on historical patterns"""
        predicted_payments = 0.0
        
        # Get payroll patterns
        payroll_patterns = operational_data.get('payroll_patterns', [])
        
        # Assume bi-weekly payroll (every 2 weeks)
        if date.weekday() == 4:  # Friday
            week_of_year = date.isocalendar()[1]
            if week_of_year % 2 == 0:  # Every other week
                if payroll_patterns:
                    latest_payroll = payroll_patterns[-1]
                    total_payroll = float(latest_payroll.get('total_gross_pay', 0))
                    # Convert monthly to bi-weekly
                    predicted_payments = total_payroll / 2
        
        return predicted_payments
    
    async def _predict_operating_expenses(self, date: datetime, planning_data: Dict[str, Any]) -> float:
        """Predict operating expenses based on budget planning"""
        predicted_expenses = 0.0
        
        # Get operating budget
        operating_budget = planning_data.get('operating_budget', [])
        
        for budget_item in operating_budget:
            budget_month = budget_item.get('budget_month', '')
            if budget_month == date.strftime('%Y-%m'):
                monthly_budget = float(budget_item.get('budgeted_amount', 0))
                # Spread expenses evenly throughout the month
                daily_expense = monthly_budget / 30
                predicted_expenses += daily_expense
        
        return predicted_expenses
    
    async def _predict_capital_expenditure(self, date: datetime, planning_data: Dict[str, Any]) -> float:
        """Predict capital expenditure based on capex planning"""
        predicted_capex = 0.0
        
        # Get capital expenditure
        capex_data = planning_data.get('capital_expenditure', [])
        
        for capex in capex_data:
            timing = capex.get('timing', '')
            planned_cost = float(capex.get('planned_cost', 0))
            
            # Map quarters to months
            quarter_months = {
                'Q1': [1, 2, 3],
                'Q2': [4, 5, 6],
                'Q3': [7, 8, 9],
                'Q4': [10, 11, 12]
            }
            
            if timing in quarter_months:
                if date.month in quarter_months[timing]:
                    # Spread capex evenly over the quarter
                    daily_capex = planned_cost / (3 * 30)  # 3 months, 30 days each
                    predicted_capex += daily_capex
        
        return predicted_capex
    
    def _calculate_confidence_intervals(self, predicted_inflows: float, predicted_outflows: float, date: datetime) -> Dict[str, float]:
        """Calculate confidence intervals for predictions"""
        # Simplified confidence interval calculation
        # In a real implementation, this would use model uncertainty
        
        inflow_std = predicted_inflows * 0.2  # 20% standard deviation
        outflow_std = predicted_outflows * 0.15  # 15% standard deviation
        
        # 95% confidence interval (approximately 2 standard deviations)
        z_score = 1.96
        
        return {
            'inflows_lower': round(predicted_inflows - z_score * inflow_std, 2),
            'inflows_upper': round(predicted_inflows + z_score * inflow_std, 2),
            'outflows_lower': round(predicted_outflows - z_score * outflow_std, 2),
            'outflows_upper': round(predicted_outflows + z_score * outflow_std, 2)
        }
    
    def _generate_weekly_summary(self, daily_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate weekly summary from daily predictions"""
        weekly_summary = []
        
        # Group by week
        current_week = None
        week_data = []
        
        for day in daily_predictions:
            date = datetime.strptime(day['date'], '%Y-%m-%d')
            week_number = date.isocalendar()[1]
            
            if current_week != week_number:
                if week_data:
                    weekly_summary.append(self._summarize_week(week_data))
                current_week = week_number
                week_data = []
            
            week_data.append(day)
        
        if week_data:
            weekly_summary.append(self._summarize_week(week_data))
        
        return weekly_summary
    
    def _summarize_week(self, week_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize a week of predictions"""
        total_inflows = sum(day['predicted_inflows'] for day in week_data)
        total_outflows = sum(day['predicted_outflows'] for day in week_data)
        net_flow = total_inflows - total_outflows
        
        return {
            'week_start': week_data[0]['date'],
            'week_end': week_data[-1]['date'],
            'total_inflows': round(total_inflows, 2),
            'total_outflows': round(total_outflows, 2),
            'net_cash_flow': round(net_flow, 2),
            'ending_balance': week_data[-1]['cumulative_balance'],
            'average_daily_flow': round(net_flow / len(week_data), 2)
        }
    
    def _generate_monthly_summary(self, daily_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate monthly summary from daily predictions"""
        monthly_summary = []
        
        # Group by month
        current_month = None
        month_data = []
        
        for day in daily_predictions:
            date = datetime.strptime(day['date'], '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')
            
            if current_month != month_key:
                if month_data:
                    monthly_summary.append(self._summarize_month(month_data))
                current_month = month_key
                month_data = []
            
            month_data.append(day)
        
        if month_data:
            monthly_summary.append(self._summarize_month(month_data))
        
        return monthly_summary
    
    def _summarize_month(self, month_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize a month of predictions"""
        total_inflows = sum(day['predicted_inflows'] for day in month_data)
        total_outflows = sum(day['predicted_outflows'] for day in month_data)
        net_flow = total_inflows - total_outflows
        
        return {
            'month': month_data[0]['date'][:7],
            'total_inflows': round(total_inflows, 2),
            'total_outflows': round(total_outflows, 2),
            'net_cash_flow': round(net_flow, 2),
            'ending_balance': month_data[-1]['cumulative_balance'],
            'average_daily_flow': round(net_flow / len(month_data), 2),
            'days_with_negative_flow': sum(1 for day in month_data if day['net_cash_flow'] < 0)
        }
    
    async def _calculate_scenarios(self, predictions: Dict[str, Any], operational_data: Dict[str, Any], planning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate different scenarios (optimistic, pessimistic, base case)"""
        scenarios = {
            'base_case': predictions,
            'optimistic': self._adjust_predictions(predictions, 1.2, 0.9),  # 20% more inflows, 10% less outflows
            'pessimistic': self._adjust_predictions(predictions, 0.8, 1.1),  # 20% less inflows, 10% more outflows
            'stress_test': self._adjust_predictions(predictions, 0.6, 1.3)   # 40% less inflows, 30% more outflows
        }
        
        return scenarios
    
    def _adjust_predictions(self, predictions: Dict[str, Any], inflow_multiplier: float, outflow_multiplier: float) -> Dict[str, Any]:
        """Adjust predictions for scenario analysis"""
        adjusted_predictions = {
            'daily_predictions': [],
            'weekly_summary': [],
            'monthly_summary': []
        }
        
        cumulative_balance = 0
        for day in predictions['daily_predictions']:
            if len(adjusted_predictions['daily_predictions']) == 0:
                # First day - use original starting balance
                cumulative_balance = day['cumulative_balance'] - day['net_cash_flow']
            
            adjusted_inflows = day['predicted_inflows'] * inflow_multiplier
            adjusted_outflows = day['predicted_outflows'] * outflow_multiplier
            adjusted_net_flow = adjusted_inflows - adjusted_outflows
            cumulative_balance += adjusted_net_flow
            
            adjusted_day = {
                'date': day['date'],
                'predicted_inflows': round(adjusted_inflows, 2),
                'predicted_outflows': round(adjusted_outflows, 2),
                'net_cash_flow': round(adjusted_net_flow, 2),
                'cumulative_balance': round(cumulative_balance, 2)
            }
            
            adjusted_predictions['daily_predictions'].append(adjusted_day)
        
        # Regenerate summaries
        adjusted_predictions['weekly_summary'] = self._generate_weekly_summary(adjusted_predictions['daily_predictions'])
        adjusted_predictions['monthly_summary'] = self._generate_monthly_summary(adjusted_predictions['daily_predictions'])
        
        return adjusted_predictions
    
    async def _generate_insights(self, predictions: Dict[str, Any], scenarios: Dict[str, Any], operational_data: Dict[str, Any], planning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights and recommendations"""
        insights = {
            'key_insights': [],
            'risk_factors': [],
            'opportunities': [],
            'recommendations': []
        }
        
        # Analyze cash flow patterns
        daily_predictions = predictions['daily_predictions']
        
        # Check for cash flow problems
        negative_days = [day for day in daily_predictions if day['cumulative_balance'] < 0]
        if negative_days:
            insights['risk_factors'].append({
                'type': 'negative_cash_flow',
                'description': f'Negative cash balance predicted for {len(negative_days)} days',
                'first_occurrence': negative_days[0]['date'],
                'minimum_balance': min(day['cumulative_balance'] for day in negative_days),
                'severity': 'high'
            })
        
        # Check for large outflows
        large_outflows = [day for day in daily_predictions if day['predicted_outflows'] > 50000]
        if large_outflows:
            insights['key_insights'].append({
                'type': 'large_outflows',
                'description': f'Large outflows (>$50K) predicted for {len(large_outflows)} days',
                'total_amount': sum(day['predicted_outflows'] for day in large_outflows),
                'impact': 'medium'
            })
        
        # Seasonal patterns
        monthly_summary = predictions['monthly_summary']
        if len(monthly_summary) > 1:
            best_month = max(monthly_summary, key=lambda x: x['net_cash_flow'])
            worst_month = min(monthly_summary, key=lambda x: x['net_cash_flow'])
            
            insights['key_insights'].append({
                'type': 'seasonal_patterns',
                'description': f'Best month: {best_month["month"]} (+${best_month["net_cash_flow"]:,.2f}), Worst month: {worst_month["month"]} (${worst_month["net_cash_flow"]:,.2f})',
                'impact': 'medium'
            })
        
        # Scenario analysis insights
        base_case_ending = daily_predictions[-1]['cumulative_balance']
        pessimistic_ending = scenarios['pessimistic']['daily_predictions'][-1]['cumulative_balance']
        
        if pessimistic_ending < 0:
            insights['risk_factors'].append({
                'type': 'scenario_risk',
                'description': f'Pessimistic scenario shows negative ending balance: ${pessimistic_ending:,.2f}',
                'severity': 'high'
            })
        
        # Recommendations
        if negative_days:
            insights['recommendations'].append({
                'type': 'cash_flow_management',
                'description': 'Consider negotiating extended payment terms with suppliers',
                'priority': 'high'
            })
            
            insights['recommendations'].append({
                'type': 'collections',
                'description': 'Accelerate collections from customers with outstanding invoices',
                'priority': 'high'
            })
        
        insights['recommendations'].append({
            'type': 'monitoring',
            'description': 'Monitor daily cash position and update forecasts weekly',
            'priority': 'medium'
        })
        
        return insights
    
    async def _assess_data_quality(self, operational_data: Dict[str, Any], planning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of data used for predictions"""
        quality_assessment = {
            'overall_score': 0,
            'operational_data_quality': {},
            'planning_data_quality': {},
            'data_completeness': {},
            'recommendations': []
        }
        
        # Assess operational data quality
        ar_data = operational_data.get('accounts_receivable', [])
        payment_patterns = operational_data.get('customer_payment_patterns', [])
        
        operational_score = 0
        if ar_data:
            operational_score += 25
        if payment_patterns:
            operational_score += 25
        if len(payment_patterns) > 5:
            operational_score += 25
        if operational_data.get('historical_cash_flow'):
            operational_score += 25
        
        quality_assessment['operational_data_quality'] = {
            'score': operational_score,
            'ar_data_available': bool(ar_data),
            'payment_patterns_available': bool(payment_patterns),
            'historical_data_available': bool(operational_data.get('historical_cash_flow'))
        }
        
        # Assess planning data quality
        planning_score = 0
        if planning_data.get('supplier_contracts'):
            planning_score += 25
        if planning_data.get('customer_forecasts'):
            planning_score += 25
        if planning_data.get('operating_budget'):
            planning_score += 25
        if planning_data.get('procurement_schedule'):
            planning_score += 25
        
        quality_assessment['planning_data_quality'] = {
            'score': planning_score,
            'supplier_contracts_available': bool(planning_data.get('supplier_contracts')),
            'customer_forecasts_available': bool(planning_data.get('customer_forecasts')),
            'budget_available': bool(planning_data.get('operating_budget')),
            'procurement_schedule_available': bool(planning_data.get('procurement_schedule'))
        }
        
        # Overall score
        quality_assessment['overall_score'] = (operational_score + planning_score) / 2
        
        # Recommendations for improvement
        if operational_score < 75:
            quality_assessment['recommendations'].append(
                "Improve operational data collection, especially customer payment patterns"
            )
        
        if planning_score < 75:
            quality_assessment['recommendations'].append(
                "Enhance business planning data with more detailed forecasts and budgets"
            )
        
        return quality_assessment
    
    async def _get_current_cash_balance(self) -> float:
        """Get current cash balance from database"""
        async with self.connection_pool.acquire() as conn:
            balance = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0) FROM finance.cash_ledger
            """)
            return float(balance)
    
    async def close(self):
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()

# Factory function
def create_cash_flow_prediction_engine(database_url: str, excel_data_path: str = "/app/business-planning") -> CashFlowPredictionEngine:
    """Create cash flow prediction engine instance"""
    config = CashFlowPredictionConfig(
        database_url=database_url,
        excel_data_path=excel_data_path
    )
    return CashFlowPredictionEngine(config)