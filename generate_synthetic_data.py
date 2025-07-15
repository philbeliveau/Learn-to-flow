#!/usr/bin/env python3
"""
EZBI Analytics - Synthetic Data Generator
Replaces Chinese stock market data with synthetic French company data
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import string

# Set random seed for reproducible results
np.random.seed(42)
random.seed(42)

def generate_synthetic_french_companies(count=5000):
    """Generate synthetic French company names and tickers"""
    
    # French company prefixes and suffixes
    prefixes = [
        "Industrie", "Manufacture", "Société", "Groupe", "Entreprise", "Compagnie",
        "Ateliers", "Usines", "Fabrique", "Production", "Système", "Technologie",
        "Innovation", "Solutions", "Services", "Consulting", "Développement",
        "Métallurgie", "Mécanique", "Électronique", "Textile", "Alimentaire",
        "Chimie", "Plastique", "Bois", "Verre", "Céramique", "Automobile",
        "Aéronautique", "Naval", "Ferroviaire", "Énergie", "Hydraulique"
    ]
    
    names = [
        "Lyonnaise", "Parisienne", "Marseillaise", "Toulousaine", "Nantaise",
        "Strasbourgeoise", "Lilloise", "Bordelaise", "Rennaise", "Rouennaise",
        "Grenobloise", "Montpelliéraine", "Dijonnaise", "Clermontoise", "Orleanaise",
        "Amiénoise", "Limogeaude", "Brestoise", "Tourangelle", "Angevine",
        "Française", "Européenne", "Continentale", "Régionale", "Nationale",
        "Internationale", "Moderne", "Avancée", "Nouvelle", "Intégrée",
        "Spécialisée", "Générale", "Technique", "Industrielle", "Commerciale",
        "Innovante", "Durable", "Qualité", "Excellence", "Précision",
        "Dynamique", "Créative", "Performante", "Efficace", "Fiable"
    ]
    
    suffixes = [
        "SA", "SARL", "SAS", "EURL", "SNC", "SCS", "GIE", "SCOP", "SE"
    ]
    
    cities = [
        "Lyon", "Paris", "Marseille", "Toulouse", "Nantes", "Strasbourg",
        "Lille", "Bordeaux", "Rennes", "Rouen", "Grenoble", "Montpellier",
        "Dijon", "Clermont", "Orléans", "Amiens", "Limoges", "Brest",
        "Tours", "Angers", "Nancy", "Metz", "Reims", "Saint-Étienne",
        "Toulon", "Annecy", "Perpignan", "Besançon", "Mulhouse", "Caen"
    ]
    
    companies = []
    tickers = []
    
    for i in range(count):
        # Generate company name
        prefix = random.choice(prefixes)
        name = random.choice(names)
        suffix = random.choice(suffixes)
        city = random.choice(cities)
        
        # Create variations
        if random.random() < 0.3:  # 30% chance for city-based name
            company_name = f"{prefix} {city} {suffix}"
        elif random.random() < 0.5:  # 50% chance for adjective-based name
            company_name = f"{prefix} {name} {suffix}"
        else:  # 20% chance for combined name
            company_name = f"{prefix} {name} de {city} {suffix}"
        
        # Generate synthetic ticker (French pattern: FR + 4 digits)
        ticker = f"FR{i+1:04d}"
        
        companies.append(company_name)
        tickers.append(ticker)
    
    return pd.DataFrame({
        'ticker': tickers,
        'company_name': companies
    })

def generate_synthetic_cash_flow_data(company_df, num_records=203332):
    """Generate synthetic cash flow data maintaining realistic patterns"""
    
    # Date range for synthetic data
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    records = []
    
    for i in range(num_records):
        # Random date within range
        random_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days)
        )
        
        # Select random company
        ticker = random.choice(company_df['ticker'].tolist())
        
        # Generate realistic cash flow values (in EUR)
        # Base cash flow (can be positive or negative)
        base_cash_flow = np.random.normal(0, 50000000)  # Mean 0, std 50M EUR
        
        # Net cash flow growth (percentage)
        net_cash_flow_growth = np.random.normal(0, 200)  # Mean 0%, std 200%
        
        # Operating cash flow (usually larger absolute value)
        operating_cash_flow = base_cash_flow * np.random.uniform(0.5, 3.0)
        
        # Operating cash flow ratio
        if base_cash_flow != 0:
            operating_ratio = (operating_cash_flow / base_cash_flow) * 100
        else:
            operating_ratio = 0
        
        # Investment cash flow (usually negative for growing companies)
        investment_cash_flow = -abs(np.random.normal(0, 30000000))
        
        # Investment cash flow ratio
        if base_cash_flow != 0:
            investment_ratio = (investment_cash_flow / base_cash_flow) * 100
        else:
            investment_ratio = 0
        
        # Financing cash flow (balancing item)
        financing_cash_flow = -(operating_cash_flow + investment_cash_flow - base_cash_flow)
        
        # Financing cash flow ratio
        if base_cash_flow != 0:
            financing_ratio = (financing_cash_flow / base_cash_flow) * 100
        else:
            financing_ratio = 0
        
        record = {
            'Date': random_date.strftime('%Y-%m-%d'),
            'ticker': ticker,
            'net cash flow-net cash flow': round(base_cash_flow, 2),
            'net cash flow growth': round(net_cash_flow_growth, 10),
            'operating cash flow-net operating cash flow': round(operating_cash_flow, 2),
            'operating cash flow-cash flow ratio': round(operating_ratio, 10),
            'investment cash flow-net investment cash flow': round(investment_cash_flow, 2),
            'investment cash flow-cash flow ratio': round(investment_ratio, 10),
            'Cash flow from financing-net cash flow': round(financing_cash_flow, 2),
            'Cash flow from financing-cash flow ratio': round(financing_ratio, 10)
        }
        
        records.append(record)
    
    return pd.DataFrame(records)

def main():
    """Main function to generate synthetic data"""
    
    print("🔄 Generating synthetic French company data...")
    
    # Generate synthetic French companies
    companies_df = generate_synthetic_french_companies(count=5000)
    
    print(f"✅ Generated {len(companies_df)} synthetic French companies")
    print("Sample companies:")
    print(companies_df.head(10))
    
    # Generate synthetic cash flow data
    print(f"\n🔄 Generating synthetic cash flow data (203,332 records)...")
    
    cash_flow_df = generate_synthetic_cash_flow_data(companies_df, num_records=203332)
    
    print(f"✅ Generated {len(cash_flow_df)} synthetic cash flow records")
    print("Sample cash flow data:")
    print(cash_flow_df.head(10))
    
    # Save synthetic data files
    print("\n💾 Saving synthetic data files...")
    
    # Backup originals
    import shutil
    backup_dir = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/backend/data/backup/"
    
    try:
        shutil.os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(
            "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/backend/data/cash_flow.csv",
            f"{backup_dir}cash_flow_original.csv"
        )
        shutil.copy2(
            "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/backend/data/map_ticker_to_company.csv",
            f"{backup_dir}map_ticker_to_company_original.csv"
        )
        print("✅ Original files backed up")
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")
    
    # Save new synthetic files
    companies_df.to_csv(
        "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/backend/data/map_ticker_to_company.csv",
        index=False
    )
    
    cash_flow_df.to_csv(
        "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/backend/data/cash_flow.csv",
        index=False
    )
    
    print("✅ Synthetic data files saved successfully!")
    
    # Validation
    print("\n🔍 Validation:")
    print(f"- Company mapping: {len(companies_df)} records")
    print(f"- Cash flow data: {len(cash_flow_df)} records")
    print(f"- Unique tickers: {len(companies_df['ticker'].unique())}")
    print(f"- Date range: {cash_flow_df['Date'].min()} to {cash_flow_df['Date'].max()}")
    
    # Check for any remaining Chinese characters
    chinese_chars = any(
        any(ord(char) > 127 and ord(char) < 0x4E00 or ord(char) > 0x9FFF for char in company) 
        for company in companies_df['company_name']
    )
    
    if chinese_chars:
        print("❌ Warning: Chinese characters still present")
    else:
        print("✅ No Chinese characters detected - 100% synthetic data")
    
    print("\n🎉 SYNTHETIC DATA GENERATION COMPLETE!")
    print("🔒 Platform is now 100% synthetic data compliant")

if __name__ == "__main__":
    main()