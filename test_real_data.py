#!/usr/bin/env python3
"""
Test Real Data Integration
Test our real data service directly
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.real_data_service import real_data_service

def test_real_data_service():
    """Test the real data service directly"""
    
    print("🧪 Testing Real Data Service Integration")
    print("=" * 60)
    
    # Test cash flow data
    print("💰 Testing Cash Flow Data (203K records)...")
    try:
        cash_flow_summary = real_data_service.get_cash_flow_summary()
        print(f"✅ Cash Flow Data Loaded:")
        print(f"   - Cash Position: €{cash_flow_summary['cash_position']:,.2f}")
        print(f"   - Revenue: €{cash_flow_summary['revenue']:,.2f}")
        print(f"   - Records Analyzed: {cash_flow_summary['records_analyzed']}")
        print(f"   - Data Source: {cash_flow_summary['data_source']}")
        print()
    except Exception as e:
        print(f"❌ Cash Flow Error: {e}")
        print()
    
    # Test manufacturing data
    print("🏭 Testing Manufacturing Data (14K sensor records)...")
    try:
        manufacturing_kpis = real_data_service.get_manufacturing_kpis()
        print(f"✅ Manufacturing Data Loaded:")
        print(f"   - Efficiency: {manufacturing_kpis['efficiency']}%")
        print(f"   - Production Volume: {manufacturing_kpis['production_volume']}")
        print(f"   - Quality Rate: {manufacturing_kpis['quality_rate']}%")
        print(f"   - Sensor Readings: {manufacturing_kpis['sensor_readings']}")
        print(f"   - Data Source: {manufacturing_kpis['data_source']}")
        print()
    except Exception as e:
        print(f"❌ Manufacturing Error: {e}")
        print()
    
    # Test prediction data
    print("🔮 Testing Prediction Data...")
    try:
        prediction_data = real_data_service.get_cash_flow_prediction_data()
        print(f"✅ Prediction Data Loaded:")
        print(f"   - Data Points: {len(prediction_data)}")
        if prediction_data:
            print(f"   - Sample Amount: €{prediction_data[0]['amount']:,.2f}")
            print(f"   - Date Range: {prediction_data[0]['date']} to {prediction_data[-1]['date']}")
        print()
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        print()
    
    # Test economies data
    print("📊 Testing Economies of Scale Data...")
    try:
        economies_data = real_data_service.get_economies_of_scale_data()
        print(f"✅ Economies Data Loaded:")
        print(f"   - Scale Factor: {economies_data['scale_factor']}")
        print(f"   - Cost Reduction: {economies_data['cost_reduction']}%")
        print()
    except Exception as e:
        print(f"❌ Economies Error: {e}")
        print()
    
    print("=" * 60)
    print("🎉 Real Data Service Test Complete!")
    print()
    print("📋 Next Steps:")
    print("1. Start backend: python run.py")
    print("2. Visit: http://localhost:8004/docs")
    print("3. Test /api/v1/company/kpis endpoint")
    print("4. Test /api/v1/predictions/cashflow endpoint")

if __name__ == "__main__":
    test_real_data_service()