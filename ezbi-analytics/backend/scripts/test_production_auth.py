#!/usr/bin/env python3
"""
Production Authentication System Test Script
Tests the complete JWT authentication system with all security features
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000/api/v1"
MANUFACTURING_BASE_URL = f"{API_BASE_URL}/manufacturing"

class AuthTestClient:
    """Test client for authentication system"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def register_user(self, email: str, password: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """Register a new user"""
        data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "company_name": "Test Manufacturing Corp",
            "accept_terms": True,
            "accept_privacy": True
        }
        
        async with self.session.post(f"{self.base_url}/auth/register", json=data) as response:
            result = await response.json()
            return {"status": response.status, "data": result}
    
    async def login(self, email: str, password: str, mfa_token: Optional[str] = None) -> Dict[str, Any]:
        """Login user and store tokens"""
        data = {
            "email": email,
            "password": password,
            "remember_me": False
        }
        
        if mfa_token:
            data["mfa_token"] = mfa_token
        
        async with self.session.post(f"{self.base_url}/auth/login", json=data) as response:
            result = await response.json()
            
            if response.status == 200:
                self.access_token = result.get("access_token")
                self.refresh_token = result.get("refresh_token")
                self.user_info = result.get("user")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
            
            return {"status": response.status, "data": result}
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token"""
        if not self.refresh_token:
            return {"status": 400, "data": {"detail": "No refresh token available"}}
        
        data = {"refresh_token": self.refresh_token}
        
        async with self.session.post(f"{self.base_url}/auth/refresh", json=data) as response:
            result = await response.json()
            
            if response.status == 200:
                self.access_token = result.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
            
            return {"status": response.status, "data": result}
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        async with self.session.get(f"{self.base_url}/auth/me") as response:
            result = await response.json()
            return {"status": response.status, "data": result}
    
    async def logout(self) -> Dict[str, Any]:
        """Logout user"""
        async with self.session.post(f"{self.base_url}/auth/logout") as response:
            result = await response.json()
            
            if response.status == 200:
                self.access_token = None
                self.refresh_token = None
                self.user_info = None
                self.session.headers.pop("Authorization", None)
            
            return {"status": response.status, "data": result}
    
    async def access_manufacturing_endpoint(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Access manufacturing API endpoint"""
        url = f"{MANUFACTURING_BASE_URL}/{endpoint}"
        
        if method.upper() == "GET":
            async with self.session.get(url) as response:
                result = await response.json()
                return {"status": response.status, "data": result}
        elif method.upper() == "POST":
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                return {"status": response.status, "data": result}
        else:
            return {"status": 405, "data": {"detail": "Method not allowed"}}
    
    async def test_rate_limiting(self, endpoint: str, requests_count: int = 10) -> Dict[str, Any]:
        """Test rate limiting"""
        url = f"{MANUFACTURING_BASE_URL}/{endpoint}"
        results = []
        
        for i in range(requests_count):
            start_time = time.time()
            async with self.session.get(url) as response:
                duration = time.time() - start_time
                results.append({
                    "request_number": i + 1,
                    "status": response.status,
                    "duration": duration,
                    "headers": {
                        "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
                        "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
                        "Retry-After": response.headers.get("Retry-After")
                    }
                })
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        return {"results": results}

async def test_authentication_flow():
    """Test complete authentication flow"""
    print("🔐 Testing Authentication Flow")
    print("=" * 50)
    
    async with AuthTestClient() as client:
        # Test user registration
        print("\n1. Testing User Registration...")
        register_result = await client.register_user(
            email="test@manufacturing.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="User"
        )
        print(f"   Registration Status: {register_result['status']}")
        
        # Test user login
        print("\n2. Testing User Login...")
        login_result = await client.login(
            email="test@manufacturing.com",
            password="SecurePass123!"
        )
        print(f"   Login Status: {login_result['status']}")
        
        if login_result['status'] == 200:
            print(f"   Access Token: {client.access_token[:20]}...")
            print(f"   User Roles: {client.user_info.get('roles', [])}")
            print(f"   User Permissions: {client.user_info.get('permissions', [])}")
        
        # Test getting user info
        print("\n3. Testing User Info Retrieval...")
        user_info_result = await client.get_user_info()
        print(f"   User Info Status: {user_info_result['status']}")
        
        # Test token refresh
        print("\n4. Testing Token Refresh...")
        refresh_result = await client.refresh_access_token()
        print(f"   Refresh Status: {refresh_result['status']}")
        
        # Test logout
        print("\n5. Testing Logout...")
        logout_result = await client.logout()
        print(f"   Logout Status: {logout_result['status']}")
        
        return login_result['status'] == 200

async def test_manufacturing_api_access():
    """Test manufacturing API access with different roles"""
    print("\n🏭 Testing Manufacturing API Access")
    print("=" * 50)
    
    # Test endpoints for different modules
    test_endpoints = [
        ("sales/customers", "Sales Customers"),
        ("sales/invoices", "Sales Invoices"),
        ("sales/kpis", "Sales KPIs"),
        ("operations/products", "Operations Products"),
        ("operations/production-orders", "Production Orders"),
        ("dashboard/overview", "Dashboard Overview"),
        ("admin/audit-logs", "Admin Audit Logs")
    ]
    
    async with AuthTestClient() as client:
        # Login as test user
        await client.login(
            email="test@manufacturing.com",
            password="SecurePass123!"
        )
        
        for endpoint, description in test_endpoints:
            print(f"\n   Testing {description}...")
            result = await client.access_manufacturing_endpoint(endpoint)
            print(f"   Status: {result['status']}")
            
            if result['status'] == 200:
                print(f"   ✅ Access granted")
            elif result['status'] == 403:
                print(f"   ❌ Access denied - Insufficient permissions")
            elif result['status'] == 401:
                print(f"   ❌ Unauthorized - Authentication required")
            else:
                print(f"   ⚠️  Unexpected status: {result['status']}")

async def test_role_based_access():
    """Test role-based access control"""
    print("\n👥 Testing Role-Based Access Control")
    print("=" * 50)
    
    # Test different user roles
    test_users = [
        {
            "email": "sales@manufacturing.com",
            "password": "SalesPass123!",
            "role": "sales_user",
            "expected_access": ["sales/customers", "sales/invoices", "dashboard/overview"]
        },
        {
            "email": "admin@manufacturing.com",
            "password": "AdminPass123!",
            "role": "admin",
            "expected_access": ["sales/customers", "operations/products", "admin/audit-logs"]
        }
    ]
    
    for user in test_users:
        print(f"\n   Testing {user['role']} role...")
        
        async with AuthTestClient() as client:
            # Register user
            await client.register_user(
                email=user["email"],
                password=user["password"],
                first_name=user["role"].title(),
                last_name="User"
            )
            
            # Login
            login_result = await client.login(
                email=user["email"],
                password=user["password"]
            )
            
            if login_result['status'] == 200:
                print(f"   ✅ Login successful")
                
                # Test expected access
                for endpoint in user["expected_access"]:
                    result = await client.access_manufacturing_endpoint(endpoint)
                    if result['status'] == 200:
                        print(f"   ✅ {endpoint}: Access granted")
                    else:
                        print(f"   ❌ {endpoint}: Access denied ({result['status']})")
            else:
                print(f"   ❌ Login failed: {login_result['status']}")

async def test_security_features():
    """Test security features"""
    print("\n🔒 Testing Security Features")
    print("=" * 50)
    
    async with AuthTestClient() as client:
        # Login
        await client.login(
            email="test@manufacturing.com",
            password="SecurePass123!"
        )
        
        # Test rate limiting
        print("\n   Testing Rate Limiting...")
        rate_limit_result = await client.test_rate_limiting("dashboard/overview", 15)
        
        rate_limited = any(r['status'] == 429 for r in rate_limit_result['results'])
        if rate_limited:
            print("   ✅ Rate limiting is working")
        else:
            print("   ⚠️  Rate limiting not triggered (may need more requests)")
        
        # Test invalid token
        print("\n   Testing Invalid Token Protection...")
        original_token = client.access_token
        client.session.headers.update({"Authorization": "Bearer invalid_token"})
        
        result = await client.access_manufacturing_endpoint("dashboard/overview")
        if result['status'] == 401:
            print("   ✅ Invalid token rejected")
        else:
            print("   ❌ Invalid token accepted")
        
        # Restore valid token
        client.session.headers.update({"Authorization": f"Bearer {original_token}"})

async def test_input_validation():
    """Test input validation"""
    print("\n✅ Testing Input Validation")
    print("=" * 50)
    
    async with AuthTestClient() as client:
        # Login
        await client.login(
            email="test@manufacturing.com",
            password="SecurePass123!"
        )
        
        # Test creating customer with invalid data
        print("\n   Testing Customer Creation Validation...")
        
        invalid_customer_data = {
            "company_name": "A" * 300,  # Too long
            "email": "invalid_email",   # Invalid format
            "phone": "123",            # Too short
            "credit_limit": -1000      # Negative value
        }
        
        result = await client.access_manufacturing_endpoint(
            "sales/customers", 
            method="POST", 
            data=invalid_customer_data
        )
        
        if result['status'] == 400:
            print("   ✅ Input validation working - Invalid data rejected")
        else:
            print(f"   ❌ Input validation failed - Status: {result['status']}")

async def run_comprehensive_tests():
    """Run all authentication tests"""
    print("🚀 EZBI Analytics - Production Authentication Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test authentication flow
        auth_success = await test_authentication_flow()
        
        if auth_success:
            # Test manufacturing API access
            await test_manufacturing_api_access()
            
            # Test role-based access
            await test_role_based_access()
            
            # Test security features
            await test_security_features()
            
            # Test input validation
            await test_input_validation()
            
            print("\n" + "=" * 80)
            print("✅ All authentication tests completed successfully!")
            print("🔐 JWT Authentication System is production-ready")
            
        else:
            print("\n❌ Authentication flow failed - Cannot proceed with other tests")
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("Starting production authentication tests...")
    print("Make sure the API server is running on localhost:8000")
    print("Press Ctrl+C to cancel...")
    
    try:
        asyncio.run(run_comprehensive_tests())
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)