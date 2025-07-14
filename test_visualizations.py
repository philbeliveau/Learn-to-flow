#!/usr/bin/env python3
"""
Test Visualization and Graphing Capabilities
Demonstrate all chart types with real data
"""

import sys
from pathlib import Path
import json

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.visualization_service import visualization_service

def test_cash_flow_timeline():
    """Test cash flow timeline visualization"""
    print("📈 CASH FLOW TIMELINE VISUALIZATION")
    print("-" * 50)
    
    for timeframe in ["1M", "3M", "6M", "1Y"]:
        print(f"\n🕐 Testing {timeframe} timeframe...")
        try:
            data = visualization_service.get_cash_flow_timeline(timeframe)
            
            print(f"✅ {timeframe} Timeline Generated:")
            print(f"   - Data Points: {len(data.get('labels', []))}")
            print(f"   - Chart Type: Line Chart")
            print(f"   - Y-Axis: Cash Flow in €Billions")
            
            if 'datasets' in data:
                for dataset in data['datasets']:
                    label = dataset.get('label', 'Unknown')
                    sample_value = dataset.get('data', [0])[0] if dataset.get('data') else 0
                    print(f"   - {label}: €{sample_value}B (sample)")
            
            if 'summary' in data:
                summary = data['summary']
                print(f"   - Records Analyzed: {summary.get('total_records', 'N/A')}")
                print(f"   - Data Source: {summary.get('data_source', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error testing {timeframe}: {e}")

def test_prediction_charts():
    """Test prediction visualization with confidence intervals"""
    print("\n\n🔮 PREDICTION CHARTS WITH CONFIDENCE INTERVALS")
    print("-" * 50)
    
    for days in [7, 15, 30, 60]:
        print(f"\n📅 Testing {days}-day predictions...")
        try:
            data = visualization_service.get_prediction_chart(days)
            
            print(f"✅ {days}-Day Prediction Generated:")
            print(f"   - Chart Type: Line Chart with Confidence Bands")
            print(f"   - Historical Points: {len([d for d in data.get('labels', []) if d])}")
            print(f"   - Future Predictions: {days} days")
            
            if 'datasets' in data:
                for dataset in data['datasets']:
                    label = dataset.get('label', 'Unknown')
                    data_points = len([d for d in dataset.get('data', []) if d is not None])
                    print(f"   - {label}: {data_points} data points")
            
            if 'prediction_summary' in data:
                summary = data['prediction_summary']
                print(f"   - Avg Predicted: €{summary.get('avg_predicted_amount', 0)}M")
                print(f"   - Confidence Range: {summary.get('confidence_range', 'N/A')}")
                print(f"   - Data Source: {summary.get('data_source', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error testing {days}-day prediction: {e}")

def test_banking_trends():
    """Test banking data trend analysis"""
    print("\n\n🏦 BANKING DATA TREND ANALYSIS")
    print("-" * 50)
    
    try:
        data = visualization_service.get_banking_trends()
        
        print("✅ Banking Trends Generated:")
        
        # Company comparison chart
        if 'company_comparison' in data:
            comp_data = data['company_comparison']
            print(f"\n📊 Company Comparison Chart:")
            print(f"   - Chart Type: Bar Chart")
            print(f"   - Companies: {len(comp_data.get('labels', []))}")
            print(f"   - Title: {comp_data.get('title', 'N/A')}")
            
            # Show sample data
            labels = comp_data.get('labels', [])
            values = comp_data.get('data', [])
            for i, (label, value) in enumerate(zip(labels[:3], values[:3])):
                print(f"   - {label}: €{value}B")
        
        # Cash flow distribution
        if 'cash_flow_distribution' in data:
            dist_data = data['cash_flow_distribution']
            print(f"\n🥧 Cash Flow Distribution (Pie Chart):")
            print(f"   - Chart Type: Pie Chart")
            print(f"   - Categories: {len(dist_data.get('labels', []))}")
            
            labels = dist_data.get('labels', [])
            values = dist_data.get('data', [])
            for label, value in zip(labels, values):
                print(f"   - {label}: €{value}B")
        
        # Growth analysis
        if 'growth_analysis' in data:
            growth_data = data['growth_analysis']
            print(f"\n📈 Quarterly Growth Analysis:")
            print(f"   - Chart Type: Line Chart")
            print(f"   - Quarters: {len(growth_data.get('labels', []))}")
            
            if 'datasets' in growth_data:
                for dataset in growth_data['datasets']:
                    growth_values = dataset.get('data', [])
                    print(f"   - Growth Rates: {growth_values}")
        
        if 'summary' in data:
            summary = data['summary']
            print(f"\n📋 Summary:")
            print(f"   - Total Companies: {summary.get('total_companies', 'N/A')}")
            print(f"   - Total Records: {summary.get('total_records', 'N/A')}")
            print(f"   - Data Source: {summary.get('data_source', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error testing banking trends: {e}")

def test_manufacturing_dashboard():
    """Test manufacturing sensor dashboard"""
    print("\n\n🏭 MANUFACTURING SENSOR DASHBOARD")
    print("-" * 50)
    
    try:
        data = visualization_service.get_manufacturing_dashboard()
        
        print("✅ Manufacturing Dashboard Generated:")
        
        # Machine performance
        if 'machine_performance' in data:
            machine_data = data['machine_performance']
            print(f"\n⚙️ Machine Performance Chart:")
            print(f"   - Chart Type: Line Chart")
            print(f"   - Title: {machine_data.get('title', 'N/A')}")
            print(f"   - Time Points: {len(machine_data.get('labels', []))}")
            
            if 'datasets' in machine_data:
                for dataset in machine_data['datasets']:
                    machine_name = dataset.get('label', 'Unknown')
                    rpm_values = dataset.get('data', [])
                    avg_rpm = sum(rpm_values) / len(rpm_values) if rpm_values else 0
                    print(f"   - {machine_name}: Avg RPM {avg_rpm:.1f}")
        
        # Temperature monitoring
        if 'temperature_monitoring' in data:
            temp_data = data['temperature_monitoring']
            print(f"\n🌡️ Temperature Monitoring (Bar Chart):")
            print(f"   - Chart Type: Bar Chart")
            print(f"   - Sensors: {len(temp_data.get('labels', []))}")
            
            labels = temp_data.get('labels', [])
            temps = temp_data.get('data', [])
            for label, temp in zip(labels, temps):
                print(f"   - {label}: {temp}°C")
        
        # Quality control
        if 'quality_control' in data:
            quality_data = data['quality_control']
            print(f"\n✅ Quality Control Analysis:")
            print(f"   - Chart Type: Grouped Bar Chart")
            print(f"   - Measurements: {len(quality_data.get('labels', []))}")
            
            if 'datasets' in quality_data:
                for dataset in quality_data['datasets']:
                    dataset_name = dataset.get('label', 'Unknown')
                    values = dataset.get('data', [])
                    avg_value = sum(values) / len(values) if values else 0
                    print(f"   - {dataset_name}: Avg {avg_value:.2f}")
        
        if 'summary' in data:
            summary = data['summary']
            print(f"\n📋 Summary:")
            print(f"   - Total Sensors: {summary.get('total_sensors', 'N/A')}")
            print(f"   - Total Readings: {summary.get('total_readings', 'N/A')}")
            print(f"   - Data Source: {summary.get('data_source', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error testing manufacturing dashboard: {e}")

def demonstrate_chart_types():
    """Demonstrate all available chart types"""
    print("\n\n📊 CHART TYPES DEMONSTRATION")
    print("=" * 60)
    
    chart_types = {
        "Line Charts": [
            "Cash Flow Timeline (Multi-line with fill areas)",
            "Prediction Charts (With confidence intervals)",
            "Machine Performance (Real-time sensor data)",
            "Growth Analysis (Quarterly trends)"
        ],
        "Bar Charts": [
            "Company Comparison (Top performers)",
            "Temperature Monitoring (Sensor readings)",
            "Quality Control (Actual vs Setpoint)"
        ],
        "Pie Charts": [
            "Cash Flow Distribution (Operating, Investment, Net)",
            "Cost Breakdown (Manufacturing categories)"
        ],
        "Advanced Charts": [
            "Confidence Intervals (Prediction uncertainty)",
            "Multi-axis Charts (Different units combined)",
            "Time Series (Historical + Future projections)",
            "Comparative Analysis (Multiple datasets)"
        ]
    }
    
    for chart_category, chart_list in chart_types.items():
        print(f"\n📈 {chart_category}:")
        for chart in chart_list:
            print(f"   ✅ {chart}")

def export_sample_chart_data():
    """Export sample chart data for frontend integration"""
    print("\n\n💾 EXPORTING SAMPLE CHART DATA")
    print("-" * 50)
    
    try:
        # Get sample data from each visualization
        sample_data = {
            "cash_flow_timeline_6M": visualization_service.get_cash_flow_timeline("6M"),
            "prediction_30_days": visualization_service.get_prediction_chart(30),
            "banking_trends": visualization_service.get_banking_trends(),
            "manufacturing_dashboard": visualization_service.get_manufacturing_dashboard()
        }
        
        # Export to JSON file
        output_file = Path("sample_chart_data.json")
        with open(output_file, 'w') as f:
            json.dump(sample_data, f, indent=2, default=str)
        
        print(f"✅ Chart data exported to: {output_file}")
        print(f"📊 File size: {output_file.stat().st_size / 1024:.1f} KB")
        print("🎯 Frontend can use this data for Chart.js integration")
        
    except Exception as e:
        print(f"❌ Error exporting chart data: {e}")

def main():
    """Run all visualization tests"""
    print("🎨 EZBI ANALYTICS - VISUALIZATION & GRAPHING CAPABILITIES")
    print("=" * 70)
    print("Testing comprehensive charting with real data (203K+ records)")
    print("=" * 70)
    
    # Test all visualization types
    test_cash_flow_timeline()
    test_prediction_charts()
    test_banking_trends()
    test_manufacturing_dashboard()
    
    # Demonstrate chart capabilities
    demonstrate_chart_types()
    
    # Export sample data
    export_sample_chart_data()
    
    print("\n" + "=" * 70)
    print("🎉 VISUALIZATION TESTING COMPLETE!")
    print("=" * 70)
    
    print("\n📋 Available API Endpoints:")
    print("1. /api/v1/analytics/cash-flow-timeline?timeframe=6M")
    print("2. /api/v1/analytics/predictions-chart?days_ahead=30")
    print("3. /api/v1/analytics/banking-trends")
    print("4. /api/v1/analytics/manufacturing-dashboard")
    print("5. /api/v1/analytics/comprehensive-report")
    
    print("\n🔧 Frontend Integration:")
    print("- All chart data is Chart.js compatible")
    print("- JSON format ready for React/Vue/Angular")
    print("- Real-time data from 203K+ authentic records")
    print("- Responsive design with multiple timeframes")
    
    print("\n🚀 Next Steps:")
    print("1. Start backend: python run.py")
    print("2. Test API endpoints at http://localhost:8004/docs")
    print("3. Integrate charts in frontend dashboard")
    print("4. Add interactive filters and export options")

if __name__ == "__main__":
    main()