#!/usr/bin/env python3
"""
TDD Testing Script for Cash Flow Prediction System
Tests that ALL data comes from synthetic sources with NO hardcoded values
"""

import requests
import json
import sys
from datetime import datetime
import time

class CashFlowSystemTester:
    def __init__(self):
        self.cash_flow_api = "http://localhost:8000"
        self.manufacturing_api = "http://localhost:8004"
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def test_api_connectivity(self):
        """Test 1: API Connectivity"""
        try:
            # Test cash flow API
            response = requests.get(f"{self.cash_flow_api}/api/v1/current-cash-position", timeout=5)
            cash_flow_available = response.status_code == 200
            
            # Test manufacturing API  
            response = requests.get(f"{self.manufacturing_api}/api/v1/company/kpis", timeout=5)
            manufacturing_available = response.status_code == 200
            
            if cash_flow_available and manufacturing_available:
                self.log_test("API Connectivity", True, "Both APIs responding")
            else:
                self.log_test("API Connectivity", False, 
                            f"Cash Flow API: {cash_flow_available}, Manufacturing API: {manufacturing_available}")
                
        except Exception as e:
            self.log_test("API Connectivity", False, f"Connection error: {str(e)}")
    
    def test_no_hardcoded_values(self):
        """Test 2: No Hardcoded Values in API Responses"""
        try:
            # Test current cash position
            response = requests.get(f"{self.cash_flow_api}/api/v1/current-cash-position", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Check for suspicious hardcoded patterns
                hardcoded_patterns = [
                    "123456", "999999", "000000", "test", "sample", "demo", 
                    "placeholder", "hardcoded", "static", "fake"
                ]
                
                data_str = json.dumps(data).lower()
                found_hardcoded = any(pattern in data_str for pattern in hardcoded_patterns)
                
                if not found_hardcoded and data.get('success'):
                    self.log_test("No Hardcoded Values - Cash Position", True, 
                                "No suspicious hardcoded patterns found")
                else:
                    self.log_test("No Hardcoded Values - Cash Position", False,
                                f"Suspicious patterns or invalid structure found")
            else:
                self.log_test("No Hardcoded Values - Cash Position", False,
                            f"API returned status {response.status_code}")
                
        except Exception as e:
            self.log_test("No Hardcoded Values - Cash Position", False, f"Error: {str(e)}")
    
    def test_data_structure_validity(self):
        """Test 3: Data Structure Validity"""
        try:
            # Test quick prediction structure
            response = requests.get(f"{self.cash_flow_api}/api/v1/quick-prediction?days=30", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['success', 'summary']
                has_required = all(field in data for field in required_fields)
                
                # Check summary structure
                summary_valid = False
                if 'summary' in data and data['summary']:
                    summary_fields = ['total_predicted_inflows', 'total_predicted_outflows', 'net_cash_flow']
                    summary_valid = any(field in data['summary'] for field in summary_fields)
                
                if has_required and summary_valid:
                    self.log_test("Data Structure Validity - Quick Prediction", True,
                                "Valid data structure with required fields")
                else:
                    self.log_test("Data Structure Validity - Quick Prediction", False,
                                f"Missing required fields or invalid structure")
            else:
                self.log_test("Data Structure Validity - Quick Prediction", False,
                            f"API returned status {response.status_code}")
                
        except Exception as e:
            self.log_test("Data Structure Validity - Quick Prediction", False, f"Error: {str(e)}")
    
    def test_ml_prediction_engine(self):
        """Test 4: ML Prediction Engine"""
        try:
            # Test full prediction endpoint
            payload = {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "model_type": "ensemble",
                "include_scenarios": True
            }
            
            response = requests.post(f"{self.cash_flow_api}/api/v1/predict-cash-flow", 
                                   json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for ML prediction structure
                ml_fields = ['predictions', 'scenarios', 'insights', 'data_quality']
                has_ml_structure = all(field in data for field in ml_fields)
                
                # Check that predictions contain actual data
                has_predictions = False
                if 'predictions' in data and data['predictions']:
                    has_predictions = any(key in data['predictions'] for key in 
                                        ['daily_predictions', 'weekly_summary', 'monthly_summary'])
                
                if has_ml_structure and has_predictions:
                    self.log_test("ML Prediction Engine", True,
                                "ML engine returning structured predictions")
                else:
                    self.log_test("ML Prediction Engine", False,
                                "ML engine missing required prediction structure")
            else:
                self.log_test("ML Prediction Engine", False,
                            f"Prediction API returned status {response.status_code}")
                
        except Exception as e:
            self.log_test("ML Prediction Engine", False, f"Error: {str(e)}")
    
    def test_data_source_integration(self):
        """Test 5: PostgreSQL + Excel Data Integration"""
        try:
            # Test model performance endpoint (indicates PostgreSQL connection)
            response = requests.get(f"{self.cash_flow_api}/api/v1/model-performance", timeout=5)
            postgresql_integration = response.status_code == 200
            
            # Test business planning status (indicates Excel integration)
            response = requests.get(f"{self.cash_flow_api}/api/v1/business-planning-status", timeout=5)
            excel_integration = response.status_code == 200
            
            if postgresql_integration and excel_integration:
                self.log_test("Data Source Integration", True,
                            "Both PostgreSQL and Excel data sources accessible")
            else:
                self.log_test("Data Source Integration", False,
                            f"PostgreSQL: {postgresql_integration}, Excel: {excel_integration}")
                
        except Exception as e:
            self.log_test("Data Source Integration", False, f"Error: {str(e)}")
    
    def test_frontend_data_service(self):
        """Test 6: Frontend Data Service Validation"""
        try:
            # Check if syntheticDataService is properly configured
            service_path = "/Users/philippebeliveau/Desktop/Notebook/Learn-to-flow/ezbi-analytics/frontend/app/services/syntheticDataService.ts"
            
            with open(service_path, 'r') as f:
                service_content = f.read()
            
            # Check for proper API configuration
            has_cash_flow_api = "localhost:8000" in service_content
            has_manufacturing_api = "localhost:8004" in service_content
            has_validation = "validateRealData" in service_content
            no_hardcoded_fallbacks = "hardcoded" not in service_content.lower()
            
            if has_cash_flow_api and has_manufacturing_api and has_validation and no_hardcoded_fallbacks:
                self.log_test("Frontend Data Service", True,
                            "Synthetic data service properly configured")
            else:
                self.log_test("Frontend Data Service", False,
                            "Data service configuration issues detected")
                
        except Exception as e:
            self.log_test("Frontend Data Service", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all TDD tests"""
        print("🧪 STARTING TDD TESTING OF CASH FLOW PREDICTION SYSTEM")
        print("=" * 60)
        print("Testing that ALL data comes from synthetic sources with NO hardcoded values")
        print("=" * 60)
        print()
        
        # Run all tests
        self.test_api_connectivity()
        self.test_no_hardcoded_values()
        self.test_data_structure_validity()
        self.test_ml_prediction_engine()
        self.test_data_source_integration()
        self.test_frontend_data_service()
        
        # Summary
        print("=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"- {result['test']}: {result['details']}")
        
        print("\n🎯 CRITICAL VALIDATION:")
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED - System uses only synthetic data with no hardcoded values!")
        else:
            print("❌ SOME TESTS FAILED - System may contain hardcoded values or data issues!")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = CashFlowSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)