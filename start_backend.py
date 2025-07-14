#!/usr/bin/env python3
"""
EZBI Analytics - New Backend Launcher
Start the real FastAPI backend
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """Start the real EZBI backend"""
    print("🏭 EZBI Analytics - REAL Backend Starting...")
    print("=" * 50)
    
    try:
        # Import and run FastAPI app
        from app.main import app
        
        print("✅ Real backend loaded successfully")
        print("🚀 Starting FastAPI server on port 8004...")
        print("📖 API Documentation: http://localhost:8004/docs")
        print("🧪 Health Check: http://localhost:8004/health")
        print("=" * 50)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8004,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Failed to import backend app: {e}")
        print("🔧 Run: pip install -r backend/requirements-simple.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()