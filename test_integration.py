#!/usr/bin/env python3
"""
EZBI Analytics Integration Test
Test the real backend API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8004"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print("\n🔍 Testing login endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
            json={"email": "demo@ezbi.fr", "password": "demo123"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful: {data['user']['name']}")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_kpis(token):
    """Test KPIs endpoint"""
    print("\n🔍 Testing KPIs endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/company/kpis", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ KPIs retrieved: Cash position = €{data['financial']['cash_position']:,.2f}")
            return True
        else:
            print(f"❌ KPIs failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ KPIs error: {e}")
        return False

def test_prediction(token):
    """Test prediction endpoint"""
    print("\n🔍 Testing prediction endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/v1/predictions/cashflow", 
            headers=headers,
            json={
                "revenue": 150000,
                "expenses": 112500,
                "period_days": 30,
                "model": "prophet"
            })
        
        if response.status_code == 200:
            data = response.json()
            predicted_amount = data['prediction']['amount']
            confidence = data['confidence']
            print(f"✅ Prediction generated: €{predicted_amount:,.2f} (confidence: {confidence:.1%})")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False

def main():
    """Run integration tests"""
    print("🚀 EZBI Analytics Integration Test")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n❌ Backend not available. Make sure to run: python run.py")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Authentication failed")
        return
    
    # Test authenticated endpoints
    test_kpis(token)
    test_prediction(token)
    
    print("\n" + "=" * 50)
    print("🎉 Integration tests completed!")
    print("\n📋 Next steps:")
    print("1. Start backend: python run.py")
    print("2. Start frontend: cd ezbi-analytics/frontend && npm run dev")
    print("3. Visit: http://localhost:3000")
    print("4. Login with: demo@ezbi.fr / demo123")

if __name__ == "__main__":
    main()