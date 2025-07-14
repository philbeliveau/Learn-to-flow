#!/usr/bin/env python3
"""
EZBI Analytics - Local Development Server
Entry point for backend API server
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """Main entry point for local development"""
    print("🏭 EZBI Analytics - Starting Local Development Server")
    print("=" * 50)
    
    # Check if backend exists
    if not backend_path.exists():
        print("❌ Backend directory not found. Creating project structure...")
        create_backend_structure()
    
    try:
        # Import and run FastAPI app
        from app.main import app
        
        print("✅ Backend loaded successfully")
        print("🚀 Starting FastAPI server...")
        print("📖 API Documentation: http://localhost:8004/docs")
        print("🧪 Test Interface: http://localhost:8004/test")
        print("=" * 50)
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8004,
            reload=True,
            reload_dirs=[str(backend_path)],
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Failed to import backend app: {e}")
        print("🔧 Run: pip install -r backend/requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

def create_backend_structure():
    """Create basic backend structure if it doesn't exist"""
    backend_path.mkdir(exist_ok=True)
    (backend_path / "app").mkdir(exist_ok=True)
    
    # Create basic __init__.py files
    (backend_path / "app" / "__init__.py").touch()
    
    print("📁 Backend structure created")

if __name__ == "__main__":
    main()