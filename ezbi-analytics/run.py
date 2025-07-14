#!/usr/bin/env python3
"""
EZBI Analytics Backend Server
Simple development server runner
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the EZBI Analytics backend server"""
    
    # Get the current directory
    project_root = Path(__file__).parent
    backend_path = project_root / "backend"
    
    # Set environment variables
    os.environ.setdefault("PYTHONPATH", str(backend_path))
    os.environ.setdefault("DATABASE_URL", "postgresql://ezbi_user:ezbi_password@localhost:5434/ezbi_db")
    os.environ.setdefault("ENVIRONMENT", "development")
    
    print("🚀 Starting EZBI Analytics Backend Server...")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {backend_path}")
    print("🔗 Database: postgresql://localhost:5434/ezbi_db")
    print("🌐 Server will start on: http://localhost:8000")
    print("-" * 50)
    
    try:
        # Check if we have the simple server (faster startup)
        simple_server = project_root / "backend" / "simple_app.py"
        if simple_server.exists():
            print("📦 Using simple FastAPI server for faster development...")
            subprocess.run([
                sys.executable, 
                str(simple_server)
            ], cwd=backend_path, check=True)
        else:
            # Use the full application
            print("🏭 Starting full EZBI Analytics application...")
            subprocess.run([
                "uvicorn", 
                "app.main:app", 
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload",
                "--reload-dir", "app"
            ], cwd=backend_path, check=True)
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down EZBI Analytics Backend...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        return 1
    except FileNotFoundError:
        print("❌ Error: uvicorn not found. Please install requirements:")
        print("pip install -r backend/requirements.txt")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())