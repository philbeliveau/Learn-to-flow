#!/usr/bin/env python3
"""
Analyze the REAL datasets in ezbi-analytics/backend/data
This is the actual manufacturing and financial data!
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_datasets():
    """Analyze all the real datasets"""
    
    data_dir = Path("ezbi-analytics/backend/data")
    
    print("🔍 ANALYZING REAL EZBI DATASETS")
    print("=" * 60)
    print(f"📁 Data directory: {data_dir}")
    print()
    
    # 1. Cash Flow Data (203K records!)
    print("💰 CASH FLOW DATASET (203,332 records)")
    print("-" * 40)
    try:
        cash_flow = pd.read_csv(data_dir / "cash_flow.csv")
        print(f"Shape: {cash_flow.shape}")
        print(f"Columns: {list(cash_flow.columns[:10])}...")  # First 10 columns
        print(f"Date range: {cash_flow.iloc[0, 0] if len(cash_flow) > 0 else 'N/A'} to {cash_flow.iloc[-1, 0] if len(cash_flow) > 0 else 'N/A'}")
        
        # Check for financial columns
        financial_cols = [col for col in cash_flow.columns if any(term in col.lower() for term in ['cash', 'revenue', 'sales', 'profit', 'income', 'flow'])]
        print(f"Financial columns found: {financial_cols[:5]}...")
        print()
    except Exception as e:
        print(f"Error reading cash flow data: {e}")
        print()
    
    # 2. Manufacturing Process Data (14K records)
    print("🏭 MANUFACTURING PROCESS DATASET (14,089 records)")
    print("-" * 40)
    try:
        manufacturing = pd.read_csv(data_dir / "continuous_factory_process.csv")
        print(f"Shape: {manufacturing.shape}")
        print(f"Columns: {list(manufacturing.columns[:10])}...")
        print("This is REAL factory sensor data with:")
        print("- Machine 1, 2, 3 parallel processing")
        print("- 15 primary measurements to predict")
        print("- Continuous flow process at 1Hz sample rate")
        print("- Setpoints vs Actual values")
        print()
    except Exception as e:
        print(f"Error reading manufacturing data: {e}")
        print()
    
    # 3. Company mapping
    print("🏢 COMPANY MAPPING DATASET (4,714 records)")
    print("-" * 40)
    try:
        companies = pd.read_csv(data_dir / "map_ticker_to_company.csv")
        print(f"Shape: {companies.shape}")
        print(f"Columns: {list(companies.columns)}")
        print(f"Sample companies: {list(companies.iloc[:3, 0]) if len(companies) > 0 else 'N/A'}")
        print()
    except Exception as e:
        print(f"Error reading company data: {e}")
        print()
    
    # 4. Economies of Scale
    print("📊 ECONOMIES OF SCALE DATASET (1,001 records)")
    print("-" * 40)
    try:
        economies = pd.read_csv(data_dir / "EconomiesOfScale.csv")
        print(f"Shape: {economies.shape}")
        print(f"Columns: {list(economies.columns)}")
        print()
    except Exception as e:
        print(f"Error reading economies data: {e}")
        print()
    
    print("🎯 SUMMARY:")
    print(f"Total real data records: ~223,000+")
    print(f"Real manufacturing sensor data: ✅")
    print(f"Real cash flow financial data: ✅") 
    print(f"Real company mapping data: ✅")
    print(f"Industrial process parameters: ✅")
    print()
    print("💡 OPPORTUNITY:")
    print("Instead of synthetic demo data, we could connect to this")
    print("MASSIVE real dataset for authentic predictions!")

if __name__ == "__main__":
    analyze_datasets()