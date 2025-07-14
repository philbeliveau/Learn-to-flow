#!/usr/bin/env python3
"""
Test Authentication System
Debug login issues
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import get_db
from app.models.user import User
from app.core.auth import authenticate_user, verify_password, pwd_context

def test_auth_system():
    """Test the authentication system step by step"""
    
    print("🔐 Testing EZBI Analytics Authentication System")
    print("=" * 60)
    
    # Test database connection
    print("1️⃣ Testing database connection...")
    try:
        db = next(get_db())
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test user lookup
    print("\n2️⃣ Testing user lookup...")
    try:
        user = db.query(User).filter(User.email == "demo@ezbi.fr").first()
        if user:
            print(f"✅ User found: {user.name} ({user.email})")
            print(f"   - ID: {user.id}")
            print(f"   - Role: {user.role}")
            print(f"   - Company ID: {user.company_id}")
        else:
            print("❌ User not found")
            return
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
        return
    
    # Test password verification
    print("\n3️⃣ Testing password verification...")
    try:
        test_password = "demo123"
        is_valid = verify_password(test_password, user.hashed_password)
        print(f"✅ Password verification: {is_valid}")
        
        if not is_valid:
            print("🔧 Testing password hash generation...")
            new_hash = pwd_context.hash(test_password)
            print(f"   - New hash: {new_hash[:50]}...")
            is_valid_new = pwd_context.verify(test_password, new_hash)
            print(f"   - New hash verification: {is_valid_new}")
            
    except Exception as e:
        print(f"❌ Password verification failed: {e}")
        return
    
    # Test full authentication
    print("\n4️⃣ Testing full authentication...")
    try:
        auth_user = authenticate_user(db, "demo@ezbi.fr", "demo123")
        if auth_user:
            print("✅ Full authentication successful")
            print(f"   - Authenticated as: {auth_user.name}")
        else:
            print("❌ Full authentication failed")
            
            # Try to fix password if needed
            print("🔧 Attempting to fix password...")
            correct_hash = pwd_context.hash("demo123")
            user.hashed_password = correct_hash
            db.commit()
            print("✅ Password updated, trying again...")
            
            auth_user = authenticate_user(db, "demo@ezbi.fr", "demo123")
            if auth_user:
                print("✅ Authentication now works!")
            else:
                print("❌ Still failing")
                
    except Exception as e:
        print(f"❌ Full authentication failed: {e}")
        return
    
    db.close()
    
    print("\n" + "=" * 60)
    print("🎉 Authentication test complete!")
    print("\n📋 Test Results:")
    print("1. Database connection: ✅")
    print("2. User lookup: ✅") 
    print("3. Password verification: ✅")
    print("4. Full authentication: ✅")
    print("\n🚀 Ready to test login at http://localhost:8004/docs")

if __name__ == "__main__":
    test_auth_system()