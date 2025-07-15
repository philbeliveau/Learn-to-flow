"""
Separate Excel Data Source - Market Research & Industry Data
Completely different data domain from manufacturing database
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class MarketResearchDataSource:
    """Generates market research and industry data in Excel format"""
    
    def __init__(self, export_path: str = "/app/market-data"):
        self.export_path = Path(export_path)
        self.export_path.mkdir(exist_ok=True)
        
        # Market research data configuration
        self.market_sectors = [
            'Automotive Manufacturing',
            'Aerospace & Defense',
            'Industrial Equipment',
            'Consumer Electronics',
            'Medical Devices',
            'Energy & Power',
            'Construction Materials',
            'Food & Beverage Processing'
        ]
        
        self.geographic_regions = [
            'North America',
            'Europe',
            'Asia-Pacific',
            'Latin America',
            'Middle East & Africa'
        ]
        
        self.market_indicators = [
            'Market Size (USD B)',
            'Growth Rate (%)',
            'Market Share (%)',
            'Price Index',
            'Demand Forecast',
            'Competition Level',
            'Regulatory Impact',
            'Technology Adoption'
        ]
        
        self.competitor_companies = [
            'Global Manufacturing Corp',
            'Precision Industries Ltd',
            'Advanced Systems Inc',
            'Industrial Solutions Group',
            'Manufacturing Excellence Co',
            'Innovative Production LLC',
            'Quality Manufacturing Inc',
            'Efficient Systems Corp'
        ]
    
    def generate_market_research_excel(self, date: datetime) -> str:
        """Generate comprehensive market research Excel file"""
        try:
            filename = f"market_research_data_{date.strftime('%Y%m%d')}.xlsx"
            filepath = self.export_path / filename
            
            # Generate all market research data
            market_data = {
                'market_overview': self._generate_market_overview(),
                'industry_trends': self._generate_industry_trends(date),
                'competitive_landscape': self._generate_competitive_landscape(),
                'economic_indicators': self._generate_economic_indicators(date),
                'technology_trends': self._generate_technology_trends(),
                'regulatory_updates': self._generate_regulatory_updates(),
                'supply_chain_insights': self._generate_supply_chain_insights(),
                'customer_insights': self._generate_customer_insights(),
                'forecast_models': self._generate_forecast_models(date)
            }
            
            # Create Excel file
            self._create_market_research_excel(filepath, market_data, date)
            
            # Create metadata
            self._create_market_metadata(filepath, market_data, date)
            
            logger.info(f"Market research Excel generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate market research Excel: {e}")
            raise
    
    def _generate_market_overview(self) -> List[Dict[str, Any]]:
        """Generate market overview data"""
        overview_data = []
        
        for sector in self.market_sectors:
            for region in self.geographic_regions:
                market_size = random.uniform(5.0, 250.0)  # Billion USD
                growth_rate = random.uniform(-2.0, 15.0)  # Percentage
                
                overview_data.append({
                    'sector': sector,
                    'region': region,
                    'market_size_usd_b': round(market_size, 2),
                    'growth_rate_percent': round(growth_rate, 1),
                    'maturity_level': random.choice(['Emerging', 'Growing', 'Mature', 'Declining']),
                    'key_drivers': random.choice([
                        'Technology Innovation',
                        'Government Regulations',
                        'Consumer Demand',
                        'Supply Chain Optimization',
                        'Economic Recovery'
                    ]),
                    'market_concentration': random.choice(['High', 'Medium', 'Low']),
                    'entry_barriers': random.choice(['High', 'Medium', 'Low'])
                })
        
        return overview_data
    
    def _generate_industry_trends(self, date: datetime) -> List[Dict[str, Any]]:
        """Generate industry trends data"""
        trends_data = []
        
        # Generate trends for past 30 days
        for i in range(30):
            trend_date = date - timedelta(days=i)
            
            trend_data = {
                'date': trend_date.strftime('%Y-%m-%d'),
                'automation_adoption_index': random.uniform(60, 85),
                'sustainability_score': random.uniform(40, 90),
                'digital_transformation_rate': random.uniform(30, 70),
                'supply_chain_resilience': random.uniform(50, 80),
                'workforce_skill_gap': random.uniform(20, 60),
                'innovation_investment': random.uniform(100, 500),  # Million USD
                'regulatory_compliance_cost': random.uniform(50, 200),  # Million USD
                'market_volatility_index': random.uniform(0.2, 0.8)
            }
            
            trends_data.append(trend_data)
        
        return trends_data
    
    def _generate_competitive_landscape(self) -> List[Dict[str, Any]]:
        """Generate competitive landscape data"""
        competitive_data = []
        
        for company in self.competitor_companies:
            revenue = random.uniform(500, 5000)  # Million USD
            market_share = random.uniform(5, 25)  # Percentage
            
            competitive_data.append({
                'company_name': company,
                'annual_revenue_usd_m': round(revenue, 1),
                'market_share_percent': round(market_share, 1),
                'geographic_presence': random.randint(15, 50),  # Number of countries
                'product_portfolio_size': random.randint(50, 300),
                'rd_investment_percent': round(random.uniform(3, 12), 1),
                'employee_count': random.randint(5000, 50000),
                'sustainability_rating': random.choice(['A+', 'A', 'B+', 'B', 'C+']),
                'innovation_score': random.uniform(60, 95),
                'customer_satisfaction': random.uniform(70, 95),
                'financial_stability': random.choice(['Excellent', 'Good', 'Fair', 'Poor'])
            })
        
        return competitive_data
    
    def _generate_economic_indicators(self, date: datetime) -> List[Dict[str, Any]]:
        """Generate economic indicators data"""
        indicators_data = []
        
        # Generate economic data for past 90 days
        for i in range(90):
            indicator_date = date - timedelta(days=i)
            
            indicator_data = {
                'date': indicator_date.strftime('%Y-%m-%d'),
                'manufacturing_pmi': random.uniform(45, 65),
                'industrial_production_index': random.uniform(95, 115),
                'commodity_price_index': random.uniform(80, 120),
                'steel_price_per_ton': random.uniform(600, 1200),
                'energy_cost_index': random.uniform(85, 130),
                'logistics_cost_index': random.uniform(90, 140),
                'labor_cost_index': random.uniform(98, 110),
                'inflation_rate': random.uniform(1.5, 6.0),
                'interest_rate': random.uniform(0.5, 8.0),
                'currency_exchange_rate': random.uniform(0.8, 1.3),
                'gdp_growth_rate': random.uniform(-2.0, 8.0)
            }
            
            indicators_data.append(indicator_data)
        
        return indicators_data
    
    def _generate_technology_trends(self) -> List[Dict[str, Any]]:
        """Generate technology trends data"""
        tech_trends = []
        
        technologies = [
            'Industry 4.0',
            'Artificial Intelligence',
            'Internet of Things (IoT)',
            'Robotics & Automation',
            'Additive Manufacturing',
            'Digital Twin Technology',
            'Predictive Maintenance',
            'Blockchain in Supply Chain',
            'Augmented Reality',
            'Edge Computing'
        ]
        
        for tech in technologies:
            tech_data = {
                'technology': tech,
                'adoption_rate_percent': random.uniform(20, 80),
                'investment_usd_b': random.uniform(1, 50),
                'maturity_level': random.choice(['Emerging', 'Growing', 'Mature']),
                'impact_score': random.uniform(60, 95),
                'implementation_difficulty': random.choice(['Low', 'Medium', 'High']),
                'roi_timeline_months': random.randint(6, 36),
                'market_leaders': random.choice([
                    'Microsoft, Google, Amazon',
                    'Siemens, GE, Schneider Electric',
                    'IBM, Oracle, SAP',
                    'Rockwell, Honeywell, ABB'
                ]),
                'key_challenges': random.choice([
                    'High Implementation Cost',
                    'Skilled Labor Shortage',
                    'Data Security Concerns',
                    'Integration Complexity',
                    'Regulatory Compliance'
                ])
            }
            
            tech_trends.append(tech_data)
        
        return tech_trends
    
    def _generate_regulatory_updates(self) -> List[Dict[str, Any]]:
        """Generate regulatory updates data"""
        regulatory_data = []
        
        regulations = [
            'Environmental Compliance Standards',
            'Product Safety Regulations',
            'Data Protection Laws',
            'Trade Tariff Changes',
            'Labor Safety Requirements',
            'Quality Certification Standards',
            'Import/Export Regulations',
            'Cybersecurity Mandates'
        ]
        
        for regulation in regulations:
            reg_data = {
                'regulation_name': regulation,
                'effective_date': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                'impact_level': random.choice(['High', 'Medium', 'Low']),
                'compliance_cost_usd_m': random.uniform(5, 100),
                'affected_regions': random.choice([
                    'Global',
                    'North America',
                    'Europe',
                    'Asia-Pacific',
                    'US Only',
                    'EU Only'
                ]),
                'industry_sectors': random.choice([
                    'All Manufacturing',
                    'Automotive Only',
                    'Electronics Only',
                    'Heavy Industry',
                    'Consumer Goods'
                ]),
                'preparation_time_months': random.randint(3, 18),
                'enforcement_strictness': random.choice(['Strict', 'Moderate', 'Lenient']),
                'penalties_description': random.choice([
                    'Financial Penalties',
                    'License Suspension',
                    'Operational Restrictions',
                    'Legal Action'
                ])
            }
            
            regulatory_data.append(reg_data)
        
        return regulatory_data
    
    def _generate_supply_chain_insights(self) -> List[Dict[str, Any]]:
        """Generate supply chain insights data"""
        supply_chain_data = []
        
        supply_chain_metrics = [
            'Raw Material Availability',
            'Supplier Performance',
            'Transportation Costs',
            'Inventory Levels',
            'Lead Times',
            'Quality Issues',
            'Geopolitical Risks',
            'Natural Disaster Impact'
        ]
        
        for metric in supply_chain_metrics:
            chain_data = {
                'metric': metric,
                'current_status': random.choice(['Good', 'Fair', 'Poor', 'Critical']),
                'trend_direction': random.choice(['Improving', 'Stable', 'Declining']),
                'risk_level': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'impact_score': random.uniform(1, 10),
                'recovery_time_weeks': random.randint(1, 12),
                'mitigation_strategies': random.choice([
                    'Diversify Suppliers',
                    'Increase Inventory',
                    'Alternative Transportation',
                    'Local Sourcing',
                    'Technology Solutions'
                ]),
                'cost_impact_percent': random.uniform(0, 25),
                'geographic_hotspots': random.choice([
                    'Southeast Asia',
                    'Eastern Europe',
                    'Middle East',
                    'Latin America',
                    'Global'
                ])
            }
            
            supply_chain_data.append(chain_data)
        
        return supply_chain_data
    
    def _generate_customer_insights(self) -> List[Dict[str, Any]]:
        """Generate customer insights data"""
        customer_data = []
        
        customer_segments = [
            'Large Enterprise',
            'Mid-Market',
            'Small Business',
            'Government',
            'International'
        ]
        
        for segment in customer_segments:
            insight_data = {
                'customer_segment': segment,
                'segment_size_percent': random.uniform(10, 30),
                'average_order_value_usd': random.uniform(10000, 500000),
                'purchase_frequency_months': random.randint(1, 12),
                'price_sensitivity': random.choice(['High', 'Medium', 'Low']),
                'quality_requirements': random.choice(['Premium', 'Standard', 'Basic']),
                'delivery_expectations': random.choice(['Same Day', 'Next Day', 'Standard', 'Flexible']),
                'digital_adoption_rate': random.uniform(30, 90),
                'sustainability_importance': random.choice(['Critical', 'Important', 'Nice to Have', 'Not Important']),
                'preferred_communication': random.choice(['Email', 'Phone', 'Digital Platform', 'In-Person']),
                'growth_potential': random.choice(['High', 'Medium', 'Low']),
                'retention_rate_percent': random.uniform(70, 95)
            }
            
            customer_data.append(insight_data)
        
        return customer_data
    
    def _generate_forecast_models(self, date: datetime) -> List[Dict[str, Any]]:
        """Generate forecast models data"""
        forecast_data = []
        
        # Generate forecasts for next 12 months
        for i in range(12):
            forecast_date = date + timedelta(days=30*i)
            
            forecast = {
                'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                'market_growth_percent': random.uniform(3, 12),
                'demand_forecast_index': random.uniform(95, 130),
                'price_forecast_change': random.uniform(-10, 15),
                'capacity_utilization': random.uniform(70, 95),
                'new_market_opportunities': random.randint(2, 8),
                'risk_probability': random.uniform(0.1, 0.4),
                'investment_requirement_usd_m': random.uniform(50, 500),
                'expected_roi_percent': random.uniform(8, 25),
                'confidence_level': random.uniform(60, 90),
                'scenario': random.choice(['Optimistic', 'Base Case', 'Pessimistic']),
                'key_assumptions': random.choice([
                    'Stable Economic Growth',
                    'Technology Adoption Continues',
                    'No Major Supply Disruptions',
                    'Regulatory Environment Stable',
                    'Customer Demand Sustained'
                ])
            }
            
            forecast_data.append(forecast)
        
        return forecast_data
    
    def _create_market_research_excel(self, filepath: Path, market_data: Dict[str, Any], date: datetime):
        """Create comprehensive market research Excel file"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # 1. Market Overview
            if market_data.get('market_overview'):
                overview_df = pd.DataFrame(market_data['market_overview'])
                overview_df.to_excel(writer, sheet_name='Market_Overview', index=False)
            
            # 2. Industry Trends
            if market_data.get('industry_trends'):
                trends_df = pd.DataFrame(market_data['industry_trends'])
                trends_df.to_excel(writer, sheet_name='Industry_Trends', index=False)
            
            # 3. Competitive Landscape
            if market_data.get('competitive_landscape'):
                competitive_df = pd.DataFrame(market_data['competitive_landscape'])
                competitive_df.to_excel(writer, sheet_name='Competitive_Landscape', index=False)
            
            # 4. Economic Indicators
            if market_data.get('economic_indicators'):
                economic_df = pd.DataFrame(market_data['economic_indicators'])
                economic_df.to_excel(writer, sheet_name='Economic_Indicators', index=False)
            
            # 5. Technology Trends
            if market_data.get('technology_trends'):
                tech_df = pd.DataFrame(market_data['technology_trends'])
                tech_df.to_excel(writer, sheet_name='Technology_Trends', index=False)
            
            # 6. Regulatory Updates
            if market_data.get('regulatory_updates'):
                regulatory_df = pd.DataFrame(market_data['regulatory_updates'])
                regulatory_df.to_excel(writer, sheet_name='Regulatory_Updates', index=False)
            
            # 7. Supply Chain Insights
            if market_data.get('supply_chain_insights'):
                supply_df = pd.DataFrame(market_data['supply_chain_insights'])
                supply_df.to_excel(writer, sheet_name='Supply_Chain_Insights', index=False)
            
            # 8. Customer Insights
            if market_data.get('customer_insights'):
                customer_df = pd.DataFrame(market_data['customer_insights'])
                customer_df.to_excel(writer, sheet_name='Customer_Insights', index=False)
            
            # 9. Forecast Models
            if market_data.get('forecast_models'):
                forecast_df = pd.DataFrame(market_data['forecast_models'])
                forecast_df.to_excel(writer, sheet_name='Forecast_Models', index=False)
            
            # 10. Executive Summary
            summary_data = self._generate_executive_summary(market_data)
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
    
    def _generate_executive_summary(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate executive summary data"""
        summary = []
        
        # Market size summary
        if market_data.get('market_overview'):
            total_market_size = sum(item['market_size_usd_b'] for item in market_data['market_overview'])
            avg_growth_rate = np.mean([item['growth_rate_percent'] for item in market_data['market_overview']])
            
            summary.extend([
                {'metric': 'Total Addressable Market', 'value': f'${total_market_size:.1f}B', 'category': 'Market Size'},
                {'metric': 'Average Growth Rate', 'value': f'{avg_growth_rate:.1f}%', 'category': 'Growth'},
                {'metric': 'Number of Sectors Analyzed', 'value': len(self.market_sectors), 'category': 'Coverage'},
                {'metric': 'Geographic Regions', 'value': len(self.geographic_regions), 'category': 'Coverage'}
            ])
        
        # Technology summary
        if market_data.get('technology_trends'):
            avg_adoption = np.mean([item['adoption_rate_percent'] for item in market_data['technology_trends']])
            total_investment = sum(item['investment_usd_b'] for item in market_data['technology_trends'])
            
            summary.extend([
                {'metric': 'Average Technology Adoption', 'value': f'{avg_adoption:.1f}%', 'category': 'Technology'},
                {'metric': 'Total Technology Investment', 'value': f'${total_investment:.1f}B', 'category': 'Investment'}
            ])
        
        # Competitive summary
        if market_data.get('competitive_landscape'):
            total_competitors = len(market_data['competitive_landscape'])
            avg_revenue = np.mean([item['annual_revenue_usd_m'] for item in market_data['competitive_landscape']])
            
            summary.extend([
                {'metric': 'Key Competitors Analyzed', 'value': total_competitors, 'category': 'Competition'},
                {'metric': 'Average Competitor Revenue', 'value': f'${avg_revenue:.1f}M', 'category': 'Competition'}
            ])
        
        return summary
    
    def _create_market_metadata(self, filepath: Path, market_data: Dict[str, Any], date: datetime):
        """Create metadata file for market research Excel"""
        metadata = {
            'file_info': {
                'filename': filepath.name,
                'filepath': str(filepath),
                'file_type': 'market_research_excel',
                'generated_date': date.strftime('%Y-%m-%d'),
                'generated_timestamp': datetime.now().isoformat()
            },
            'data_summary': {
                'total_sheets': len(market_data),
                'data_categories': list(market_data.keys()),
                'market_sectors_covered': len(self.market_sectors),
                'geographic_regions': len(self.geographic_regions),
                'competitor_companies': len(self.competitor_companies)
            },
            'processing_info': {
                'data_source': 'market_research_generator',
                'data_type': 'synthetic_market_data',
                'target_platform': 'ezbi_analytics',
                'processing_status': 'ready',
                'recommended_charts': [
                    'market_size_by_sector',
                    'growth_rate_comparison',
                    'competitive_landscape_matrix',
                    'technology_adoption_timeline',
                    'economic_indicators_trend'
                ]
            }
        }
        
        metadata_file = filepath.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Market research metadata created: {metadata_file}")
    
    def get_latest_market_research(self) -> Optional[Path]:
        """Get the most recent market research Excel file"""
        try:
            excel_files = list(self.export_path.glob("market_research_data_*.xlsx"))
            if not excel_files:
                return None
            
            excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return excel_files[0]
            
        except Exception as e:
            logger.error(f"Error finding latest market research file: {e}")
            return None
    
    def list_market_research_files(self, days: int = 30) -> List[Dict[str, Any]]:
        """List recent market research files"""
        try:
            excel_files = list(self.export_path.glob("market_research_data_*.xlsx"))
            
            file_list = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filepath in excel_files:
                stat = filepath.stat()
                if datetime.fromtimestamp(stat.st_mtime) >= cutoff_date:
                    
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
            
            file_list.sort(key=lambda x: x['modified'], reverse=True)
            return file_list
            
        except Exception as e:
            logger.error(f"Error listing market research files: {e}")
            return []

# Factory function
def create_market_research_source(export_path: str = "/app/market-data") -> MarketResearchDataSource:
    """Create market research data source instance"""
    return MarketResearchDataSource(export_path)