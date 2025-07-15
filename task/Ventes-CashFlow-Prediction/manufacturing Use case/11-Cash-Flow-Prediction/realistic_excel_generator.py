"""
Realistic Excel Business Planning Data Generator
Creates authentic business planning files that manufacturing companies actually use
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class RealisticExcelGenerator:
    """Generates realistic Excel business planning files for manufacturing company"""
    
    def __init__(self, export_path: str = "/app/business-planning"):
        self.export_path = Path(export_path)
        self.export_path.mkdir(exist_ok=True)
        
        # Realistic business data
        self.suppliers = [
            {'name': 'SteelCorp Industries', 'category': 'Raw Materials', 'payment_terms': 30, 'credit_limit': 500000},
            {'name': 'Precision Tools Ltd', 'category': 'Tools & Equipment', 'payment_terms': 45, 'credit_limit': 150000},
            {'name': 'Industrial Chemicals Inc', 'category': 'Chemicals', 'payment_terms': 15, 'credit_limit': 200000},
            {'name': 'Logistics Solutions Corp', 'category': 'Transportation', 'payment_terms': 30, 'credit_limit': 100000},
            {'name': 'MaintainPro Services', 'category': 'Maintenance', 'payment_terms': 30, 'credit_limit': 75000},
            {'name': 'PowerCorp Utilities', 'category': 'Utilities', 'payment_terms': 15, 'credit_limit': 50000}
        ]
        
        self.customers = [
            {'name': 'AutoParts Manufacturing', 'category': 'Automotive', 'payment_terms': 30, 'credit_limit': 1000000, 'seasonal_factor': 1.2},
            {'name': 'Industrial Solutions Ltd', 'category': 'Industrial', 'payment_terms': 45, 'credit_limit': 750000, 'seasonal_factor': 1.0},
            {'name': 'Precision Components Inc', 'category': 'Precision', 'payment_terms': 30, 'credit_limit': 500000, 'seasonal_factor': 0.9},
            {'name': 'MegaCorp Manufacturing', 'category': 'Large Enterprise', 'payment_terms': 60, 'credit_limit': 2000000, 'seasonal_factor': 1.1},
            {'name': 'Regional Machine Shop', 'category': 'Regional', 'payment_terms': 30, 'credit_limit': 300000, 'seasonal_factor': 1.0}
        ]
        
        self.expense_categories = [
            {'category': 'Raw Materials', 'monthly_base': 150000, 'variability': 0.15},
            {'category': 'Labor', 'monthly_base': 180000, 'variability': 0.05},
            {'category': 'Utilities', 'monthly_base': 25000, 'variability': 0.10},
            {'category': 'Maintenance', 'monthly_base': 30000, 'variability': 0.20},
            {'category': 'Transportation', 'monthly_base': 40000, 'variability': 0.12},
            {'category': 'Insurance', 'monthly_base': 15000, 'variability': 0.02},
            {'category': 'Rent', 'monthly_base': 35000, 'variability': 0.00},
            {'category': 'Software & IT', 'monthly_base': 12000, 'variability': 0.05}
        ]
    
    def generate_supplier_contracts(self, year: int = 2024) -> str:
        """Generate realistic supplier contracts Excel file"""
        try:
            filename = f"supplier_contracts_{year}.xlsx"
            filepath = self.export_path / filename
            
            # Generate supplier contract data
            contracts_data = []
            
            for supplier in self.suppliers:
                # Generate multiple contracts per supplier
                num_contracts = random.randint(2, 5)
                
                for i in range(num_contracts):
                    # Contract period
                    start_date = datetime(year, random.randint(1, 6), random.randint(1, 28))
                    end_date = start_date + timedelta(days=random.randint(180, 365))
                    
                    # Contract values
                    annual_value = random.uniform(50000, supplier['credit_limit'] * 0.8)
                    monthly_value = annual_value / 12
                    
                    # Payment schedule
                    payment_day = random.randint(1, 28)
                    
                    contracts_data.append({
                        'contract_id': f"SUP-{year}-{supplier['name'][:3].upper()}-{i+1:03d}",
                        'supplier_name': supplier['name'],
                        'category': supplier['category'],
                        'contract_start': start_date.strftime('%Y-%m-%d'),
                        'contract_end': end_date.strftime('%Y-%m-%d'),
                        'annual_value': round(annual_value, 2),
                        'monthly_value': round(monthly_value, 2),
                        'payment_terms': supplier['payment_terms'],
                        'payment_day': payment_day,
                        'currency': 'USD',
                        'auto_renew': random.choice([True, False]),
                        'price_escalation': random.uniform(0.02, 0.05),  # 2-5% annual increase
                        'minimum_order': round(monthly_value * 0.5, 2),
                        'maximum_order': round(monthly_value * 2.0, 2),
                        'quality_requirements': random.choice(['ISO 9001', 'ISO 14001', 'AS9100', 'Standard']),
                        'delivery_terms': random.choice(['FOB Origin', 'FOB Destination', 'CIF', 'EXW']),
                        'contact_person': f"{random.choice(['John', 'Sarah', 'Mike', 'Lisa', 'David'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Davis'])}",
                        'phone': f"+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                        'email': f"{supplier['name'].lower().replace(' ', '').replace('&', '').replace(',', '')[:10]}@{supplier['name'].lower().split()[0]}.com",
                        'notes': f"Priority supplier for {supplier['category'].lower()}"
                    })
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main contracts sheet
                contracts_df = pd.DataFrame(contracts_data)
                contracts_df.to_excel(writer, sheet_name='Supplier_Contracts', index=False)
                
                # Payment schedule sheet
                payment_schedule = self._generate_payment_schedule(contracts_data, year)
                payment_df = pd.DataFrame(payment_schedule)
                payment_df.to_excel(writer, sheet_name='Payment_Schedule', index=False)
                
                # Supplier summary sheet
                supplier_summary = self._generate_supplier_summary(contracts_data)
                summary_df = pd.DataFrame(supplier_summary)
                summary_df.to_excel(writer, sheet_name='Supplier_Summary', index=False)
            
            logger.info(f"Supplier contracts generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate supplier contracts: {e}")
            raise
    
    def generate_customer_forecasts(self, year: int = 2024) -> str:
        """Generate realistic customer order forecasts Excel file"""
        try:
            filename = f"customer_forecasts_{year}.xlsx"
            filepath = self.export_path / filename
            
            # Generate customer forecast data
            forecasts_data = []
            
            for customer in self.customers:
                # Generate monthly forecasts
                for month in range(1, 13):
                    # Base monthly order value
                    base_value = random.uniform(50000, customer['credit_limit'] * 0.1)
                    
                    # Apply seasonal factor
                    seasonal_value = base_value * customer['seasonal_factor']
                    
                    # Add some month-specific variation
                    if month in [11, 12]:  # Holiday season
                        seasonal_value *= 1.3
                    elif month in [1, 2]:  # Post-holiday slowdown
                        seasonal_value *= 0.8
                    elif month in [6, 7, 8]:  # Summer production
                        seasonal_value *= 1.1
                    
                    # Number of orders
                    num_orders = random.randint(3, 12)
                    avg_order_value = seasonal_value / num_orders
                    
                    forecasts_data.append({
                        'customer_name': customer['name'],
                        'customer_category': customer['category'],
                        'forecast_month': f"{year}-{month:02d}",
                        'forecasted_orders': num_orders,
                        'avg_order_value': round(avg_order_value, 2),
                        'total_monthly_value': round(seasonal_value, 2),
                        'payment_terms': customer['payment_terms'],
                        'confidence_level': random.uniform(0.75, 0.95),
                        'growth_rate': random.uniform(-0.05, 0.15),
                        'risk_factor': random.choice(['Low', 'Medium', 'High']),
                        'seasonal_factor': customer['seasonal_factor'],
                        'product_mix': random.choice(['Standard', 'Custom', 'Mixed']),
                        'delivery_schedule': random.choice(['Weekly', 'Bi-weekly', 'Monthly']),
                        'quality_requirements': random.choice(['Standard', 'Premium', 'Critical']),
                        'price_sensitivity': random.choice(['Low', 'Medium', 'High']),
                        'contract_status': random.choice(['Active', 'Renewal Pending', 'New Negotiation']),
                        'notes': f"Q{(month-1)//3 + 1} forecast for {customer['category'].lower()} segment"
                    })
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main forecasts sheet
                forecasts_df = pd.DataFrame(forecasts_data)
                forecasts_df.to_excel(writer, sheet_name='Customer_Forecasts', index=False)
                
                # Quarterly summary
                quarterly_summary = self._generate_quarterly_summary(forecasts_data)
                quarterly_df = pd.DataFrame(quarterly_summary)
                quarterly_df.to_excel(writer, sheet_name='Quarterly_Summary', index=False)
                
                # Customer pipeline
                pipeline_data = self._generate_customer_pipeline(year)
                pipeline_df = pd.DataFrame(pipeline_data)
                pipeline_df.to_excel(writer, sheet_name='Sales_Pipeline', index=False)
            
            logger.info(f"Customer forecasts generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate customer forecasts: {e}")
            raise
    
    def generate_budget_planning(self, year: int = 2024) -> str:
        """Generate realistic budget planning Excel file"""
        try:
            filename = f"budget_planning_{year}.xlsx"
            filepath = self.export_path / filename
            
            # Generate budget data
            budget_data = []
            
            for month in range(1, 13):
                month_date = datetime(year, month, 1)
                
                for expense_cat in self.expense_categories:
                    # Calculate monthly budget with variability
                    base_amount = expense_cat['monthly_base']
                    variability = expense_cat['variability']
                    
                    # Add seasonal adjustments
                    seasonal_factor = 1.0
                    if expense_cat['category'] == 'Utilities':
                        if month in [12, 1, 2]:  # Winter
                            seasonal_factor = 1.4
                        elif month in [6, 7, 8]:  # Summer
                            seasonal_factor = 1.2
                    elif expense_cat['category'] == 'Raw Materials':
                        if month in [3, 4, 5, 9, 10]:  # Peak production
                            seasonal_factor = 1.2
                    
                    # Calculate final amount
                    monthly_amount = base_amount * seasonal_factor
                    variation = monthly_amount * variability * random.uniform(-1, 1)
                    final_amount = monthly_amount + variation
                    
                    budget_data.append({
                        'budget_month': month_date.strftime('%Y-%m'),
                        'category': expense_cat['category'],
                        'budgeted_amount': round(final_amount, 2),
                        'previous_year_actual': round(final_amount * random.uniform(0.9, 1.1), 2),
                        'variance_vs_previous': round((final_amount - (final_amount * random.uniform(0.9, 1.1))) / final_amount * 100, 1),
                        'cost_center': f"CC-{expense_cat['category'][:3].upper()}-001",
                        'approval_status': random.choice(['Approved', 'Pending', 'Under Review']),
                        'budget_type': random.choice(['Operating', 'Capital', 'Emergency']),
                        'payment_frequency': random.choice(['Monthly', 'Quarterly', 'Annual']),
                        'vendor_dependency': random.choice(['High', 'Medium', 'Low']),
                        'criticality': random.choice(['Critical', 'Important', 'Normal']),
                        'inflation_factor': random.uniform(0.02, 0.06),
                        'contingency_percent': random.uniform(0.05, 0.15),
                        'responsible_manager': random.choice(['Operations Manager', 'Finance Manager', 'Production Manager', 'Facilities Manager']),
                        'notes': f"Monthly budget allocation for {expense_cat['category'].lower()}"
                    })
            
            # Generate capital expenditure planning
            capex_data = []
            capex_items = [
                {'item': 'CNC Machine Upgrade', 'cost': 250000, 'timing': 'Q2'},
                {'item': 'Warehouse Expansion', 'cost': 180000, 'timing': 'Q3'},
                {'item': 'ERP System Implementation', 'cost': 120000, 'timing': 'Q1'},
                {'item': 'Quality Control Equipment', 'cost': 95000, 'timing': 'Q4'},
                {'item': 'Facility Security System', 'cost': 60000, 'timing': 'Q1'},
                {'item': 'Environmental Compliance', 'cost': 85000, 'timing': 'Q2'}
            ]
            
            for item in capex_items:
                capex_data.append({
                    'project_name': item['item'],
                    'planned_cost': item['cost'],
                    'timing': item['timing'],
                    'approval_status': random.choice(['Approved', 'Pending', 'Under Review']),
                    'business_case': random.choice(['Efficiency', 'Compliance', 'Growth', 'Maintenance']),
                    'roi_months': random.randint(12, 48),
                    'risk_level': random.choice(['Low', 'Medium', 'High']),
                    'funding_source': random.choice(['Cash', 'Loan', 'Lease', 'Grant']),
                    'implementation_months': random.randint(3, 12),
                    'responsible_department': random.choice(['Operations', 'IT', 'Facilities', 'Quality']),
                    'strategic_priority': random.choice(['High', 'Medium', 'Low'])
                })
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Operating budget sheet
                budget_df = pd.DataFrame(budget_data)
                budget_df.to_excel(writer, sheet_name='Operating_Budget', index=False)
                
                # Capital expenditure sheet
                capex_df = pd.DataFrame(capex_data)
                capex_df.to_excel(writer, sheet_name='Capital_Expenditure', index=False)
                
                # Monthly cash flow projection
                cash_flow_projection = self._generate_cash_flow_projection(budget_data, year)
                cash_flow_df = pd.DataFrame(cash_flow_projection)
                cash_flow_df.to_excel(writer, sheet_name='Cash_Flow_Projection', index=False)
                
                # Budget summary
                budget_summary = self._generate_budget_summary(budget_data)
                summary_df = pd.DataFrame(budget_summary)
                summary_df.to_excel(writer, sheet_name='Budget_Summary', index=False)
            
            logger.info(f"Budget planning generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate budget planning: {e}")
            raise
    
    def generate_inventory_planning(self, year: int = 2024) -> str:
        """Generate realistic inventory planning Excel file"""
        try:
            filename = f"inventory_planning_{year}.xlsx"
            filepath = self.export_path / filename
            
            # Raw materials inventory
            raw_materials = [
                {'material': 'Steel Sheets - 3mm', 'unit': 'Sheet', 'unit_cost': 45.00, 'lead_time': 14},
                {'material': 'Steel Rods - 10mm', 'unit': 'Meter', 'unit_cost': 12.50, 'lead_time': 10},
                {'material': 'Aluminum Plates', 'unit': 'Kg', 'unit_cost': 8.75, 'lead_time': 7},
                {'material': 'Cutting Fluid', 'unit': 'Liter', 'unit_cost': 25.00, 'lead_time': 5},
                {'material': 'Welding Electrodes', 'unit': 'Kg', 'unit_cost': 15.00, 'lead_time': 14},
                {'material': 'Protective Coating', 'unit': 'Liter', 'unit_cost': 35.00, 'lead_time': 21}
            ]
            
            inventory_data = []
            
            for material in raw_materials:
                # Generate monthly inventory planning
                for month in range(1, 13):
                    # Base consumption
                    base_consumption = random.uniform(500, 2000)
                    
                    # Seasonal adjustments
                    seasonal_factor = 1.0
                    if month in [3, 4, 5, 9, 10]:  # Peak production months
                        seasonal_factor = 1.3
                    elif month in [12, 1]:  # Holiday slowdown
                        seasonal_factor = 0.7
                    
                    monthly_consumption = base_consumption * seasonal_factor
                    
                    # Safety stock calculation
                    safety_stock = monthly_consumption * 0.25  # 25% safety stock
                    
                    # Economic order quantity (simplified)
                    eoq = np.sqrt(2 * monthly_consumption * 12 * 100 / (material['unit_cost'] * 0.2))
                    
                    # Reorder point
                    reorder_point = (monthly_consumption / 30) * material['lead_time'] + safety_stock
                    
                    inventory_data.append({
                        'material_name': material['material'],
                        'unit_of_measure': material['unit'],
                        'planning_month': f"{year}-{month:02d}",
                        'forecasted_consumption': round(monthly_consumption, 2),
                        'unit_cost': material['unit_cost'],
                        'total_cost': round(monthly_consumption * material['unit_cost'], 2),
                        'safety_stock': round(safety_stock, 2),
                        'economic_order_qty': round(eoq, 2),
                        'reorder_point': round(reorder_point, 2),
                        'lead_time_days': material['lead_time'],
                        'supplier_name': random.choice([s['name'] for s in self.suppliers if s['category'] == 'Raw Materials']),
                        'storage_location': random.choice(['Warehouse A', 'Warehouse B', 'Production Floor']),
                        'shelf_life_days': random.randint(90, 730) if 'Fluid' in material['material'] or 'Coating' in material['material'] else None,
                        'quality_grade': random.choice(['Grade A', 'Grade B', 'Premium']),
                        'minimum_order_qty': round(eoq * 0.5, 2),
                        'storage_cost_per_unit': round(material['unit_cost'] * 0.02, 2),
                        'obsolescence_risk': random.choice(['Low', 'Medium', 'High']),
                        'supplier_reliability': random.choice(['Excellent', 'Good', 'Fair']),
                        'price_volatility': random.choice(['Low', 'Medium', 'High']),
                        'strategic_importance': random.choice(['Critical', 'Important', 'Standard'])
                    })
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main inventory planning sheet
                inventory_df = pd.DataFrame(inventory_data)
                inventory_df.to_excel(writer, sheet_name='Inventory_Planning', index=False)
                
                # ABC analysis
                abc_analysis = self._generate_abc_analysis(inventory_data)
                abc_df = pd.DataFrame(abc_analysis)
                abc_df.to_excel(writer, sheet_name='ABC_Analysis', index=False)
                
                # Procurement schedule
                procurement_schedule = self._generate_procurement_schedule(inventory_data, year)
                procurement_df = pd.DataFrame(procurement_schedule)
                procurement_df.to_excel(writer, sheet_name='Procurement_Schedule', index=False)
            
            logger.info(f"Inventory planning generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate inventory planning: {e}")
            raise
    
    def _generate_payment_schedule(self, contracts_data: List[Dict], year: int) -> List[Dict]:
        """Generate monthly payment schedule from contracts"""
        schedule = []
        
        for month in range(1, 13):
            month_date = datetime(year, month, 1)
            
            for contract in contracts_data:
                start_date = datetime.strptime(contract['contract_start'], '%Y-%m-%d')
                end_date = datetime.strptime(contract['contract_end'], '%Y-%m-%d')
                
                # Check if contract is active this month
                if start_date <= month_date <= end_date:
                    # Calculate payment date
                    payment_date = datetime(year, month, min(contract['payment_day'], 28))
                    
                    schedule.append({
                        'payment_month': month_date.strftime('%Y-%m'),
                        'payment_date': payment_date.strftime('%Y-%m-%d'),
                        'supplier_name': contract['supplier_name'],
                        'contract_id': contract['contract_id'],
                        'payment_amount': contract['monthly_value'],
                        'payment_terms': contract['payment_terms'],
                        'category': contract['category'],
                        'status': 'Scheduled'
                    })
        
        return schedule
    
    def _generate_supplier_summary(self, contracts_data: List[Dict]) -> List[Dict]:
        """Generate supplier summary from contracts"""
        supplier_summary = {}
        
        for contract in contracts_data:
            supplier = contract['supplier_name']
            if supplier not in supplier_summary:
                supplier_summary[supplier] = {
                    'supplier_name': supplier,
                    'total_annual_value': 0,
                    'number_of_contracts': 0,
                    'categories': set(),
                    'average_payment_terms': 0,
                    'contact_person': contract['contact_person'],
                    'email': contract['email']
                }
            
            supplier_summary[supplier]['total_annual_value'] += contract['annual_value']
            supplier_summary[supplier]['number_of_contracts'] += 1
            supplier_summary[supplier]['categories'].add(contract['category'])
            supplier_summary[supplier]['average_payment_terms'] += contract['payment_terms']
        
        # Convert to list and finalize calculations
        summary_list = []
        for supplier, data in supplier_summary.items():
            data['categories'] = ', '.join(data['categories'])
            data['average_payment_terms'] = round(data['average_payment_terms'] / data['number_of_contracts'], 1)
            summary_list.append(data)
        
        return summary_list
    
    def _generate_quarterly_summary(self, forecasts_data: List[Dict]) -> List[Dict]:
        """Generate quarterly summary from forecasts"""
        quarterly_data = {}
        
        for forecast in forecasts_data:
            month = int(forecast['forecast_month'].split('-')[1])
            quarter = f"Q{(month - 1) // 3 + 1}"
            customer = forecast['customer_name']
            
            key = (quarter, customer)
            if key not in quarterly_data:
                quarterly_data[key] = {
                    'quarter': quarter,
                    'customer_name': customer,
                    'total_value': 0,
                    'total_orders': 0,
                    'customer_category': forecast['customer_category']
                }
            
            quarterly_data[key]['total_value'] += forecast['total_monthly_value']
            quarterly_data[key]['total_orders'] += forecast['forecasted_orders']
        
        return list(quarterly_data.values())
    
    def _generate_customer_pipeline(self, year: int) -> List[Dict]:
        """Generate customer pipeline data"""
        pipeline = []
        
        pipeline_customers = [
            {'name': 'TechCorp Manufacturing', 'value': 500000, 'probability': 0.8},
            {'name': 'Global Industries Ltd', 'value': 750000, 'probability': 0.6},
            {'name': 'Innovative Solutions', 'value': 300000, 'probability': 0.9},
            {'name': 'Future Tech Corp', 'value': 400000, 'probability': 0.7}
        ]
        
        for customer in pipeline_customers:
            pipeline.append({
                'prospect_name': customer['name'],
                'estimated_annual_value': customer['value'],
                'probability': customer['probability'],
                'expected_close_date': (datetime(year, random.randint(1, 12), random.randint(1, 28))).strftime('%Y-%m-%d'),
                'stage': random.choice(['Qualified', 'Proposal', 'Negotiation', 'Closing']),
                'sales_rep': random.choice(['Sarah Johnson', 'Mike Chen', 'Lisa Williams']),
                'product_interest': random.choice(['Standard Products', 'Custom Solutions', 'Mixed Portfolio']),
                'competition': random.choice(['None', 'Local Competitor', 'National Player']),
                'decision_timeline': random.choice(['Immediate', '30 days', '60 days', '90 days'])
            })
        
        return pipeline
    
    def _generate_cash_flow_projection(self, budget_data: List[Dict], year: int) -> List[Dict]:
        """Generate cash flow projection from budget"""
        projection = []
        
        # Group budget by month
        monthly_budget = {}
        for item in budget_data:
            month = item['budget_month']
            if month not in monthly_budget:
                monthly_budget[month] = 0
            monthly_budget[month] += item['budgeted_amount']
        
        # Generate projection
        for month in range(1, 13):
            month_key = f"{year}-{month:02d}"
            
            projection.append({
                'month': month_key,
                'projected_expenses': monthly_budget.get(month_key, 0),
                'projected_revenue': monthly_budget.get(month_key, 0) * random.uniform(1.2, 1.8),  # Revenue typically higher
                'net_cash_flow': monthly_budget.get(month_key, 0) * random.uniform(0.2, 0.8),
                'cumulative_cash_flow': 0,  # Would be calculated cumulatively
                'confidence_level': random.uniform(0.7, 0.9)
            })
        
        # Calculate cumulative
        cumulative = 0
        for item in projection:
            cumulative += item['net_cash_flow']
            item['cumulative_cash_flow'] = cumulative
        
        return projection
    
    def _generate_budget_summary(self, budget_data: List[Dict]) -> List[Dict]:
        """Generate budget summary by category"""
        summary = {}
        
        for item in budget_data:
            category = item['category']
            if category not in summary:
                summary[category] = {
                    'category': category,
                    'annual_budget': 0,
                    'monthly_average': 0,
                    'percentage_of_total': 0
                }
            summary[category]['annual_budget'] += item['budgeted_amount']
        
        # Calculate totals and percentages
        total_budget = sum(item['annual_budget'] for item in summary.values())
        
        summary_list = []
        for category, data in summary.items():
            data['annual_budget'] = round(data['annual_budget'], 2)
            data['monthly_average'] = round(data['annual_budget'] / 12, 2)
            data['percentage_of_total'] = round((data['annual_budget'] / total_budget) * 100, 1)
            summary_list.append(data)
        
        return summary_list
    
    def _generate_abc_analysis(self, inventory_data: List[Dict]) -> List[Dict]:
        """Generate ABC analysis for inventory"""
        # Calculate annual value for each material
        material_values = {}
        
        for item in inventory_data:
            material = item['material_name']
            if material not in material_values:
                material_values[material] = 0
            material_values[material] += item['total_cost']
        
        # Sort by value and assign ABC categories
        sorted_materials = sorted(material_values.items(), key=lambda x: x[1], reverse=True)
        total_value = sum(material_values.values())
        
        abc_analysis = []
        cumulative_value = 0
        
        for i, (material, value) in enumerate(sorted_materials):
            cumulative_value += value
            cumulative_percent = (cumulative_value / total_value) * 100
            
            # Assign ABC category
            if cumulative_percent <= 80:
                category = 'A'
            elif cumulative_percent <= 95:
                category = 'B'
            else:
                category = 'C'
            
            abc_analysis.append({
                'material_name': material,
                'annual_value': round(value, 2),
                'percentage_of_total': round((value / total_value) * 100, 1),
                'cumulative_percentage': round(cumulative_percent, 1),
                'abc_category': category,
                'management_priority': {'A': 'High', 'B': 'Medium', 'C': 'Low'}[category],
                'review_frequency': {'A': 'Weekly', 'B': 'Monthly', 'C': 'Quarterly'}[category]
            })
        
        return abc_analysis
    
    def _generate_procurement_schedule(self, inventory_data: List[Dict], year: int) -> List[Dict]:
        """Generate procurement schedule"""
        schedule = []
        
        for item in inventory_data:
            if item['planning_month'] == f"{year}-01":  # Only use January data for annual schedule
                # Calculate procurement dates based on consumption and lead time
                monthly_consumption = item['forecasted_consumption']
                lead_time = item['lead_time_days']
                eoq = item['economic_order_qty']
                
                # Calculate how many orders per year
                annual_consumption = monthly_consumption * 12
                orders_per_year = max(1, int(annual_consumption / eoq))
                
                # Generate procurement dates
                for order_num in range(orders_per_year):
                    procurement_date = datetime(year, 1, 1) + timedelta(days=(365 / orders_per_year) * order_num)
                    
                    schedule.append({
                        'material_name': item['material_name'],
                        'procurement_date': procurement_date.strftime('%Y-%m-%d'),
                        'order_quantity': eoq,
                        'unit_cost': item['unit_cost'],
                        'total_cost': round(eoq * item['unit_cost'], 2),
                        'supplier_name': item['supplier_name'],
                        'lead_time_days': lead_time,
                        'delivery_date': (procurement_date + timedelta(days=lead_time)).strftime('%Y-%m-%d'),
                        'order_type': random.choice(['Regular', 'Rush', 'Blanket']),
                        'payment_terms': random.choice(['Net 30', 'Net 45', 'COD']),
                        'quality_inspection': random.choice(['Required', 'Spot Check', 'Certified'])
                    })
        
        return sorted(schedule, key=lambda x: x['procurement_date'])
    
    def generate_all_business_files(self, year: int = 2024) -> List[str]:
        """Generate all business planning Excel files"""
        files = []
        
        try:
            # Generate all Excel files
            files.append(self.generate_supplier_contracts(year))
            files.append(self.generate_customer_forecasts(year))
            files.append(self.generate_budget_planning(year))
            files.append(self.generate_inventory_planning(year))
            
            logger.info(f"Generated {len(files)} business planning files")
            return files
            
        except Exception as e:
            logger.error(f"Failed to generate business files: {e}")
            raise

# Factory function
def create_realistic_excel_generator(export_path: str = "/app/business-planning") -> RealisticExcelGenerator:
    """Create realistic Excel generator instance"""
    return RealisticExcelGenerator(export_path)