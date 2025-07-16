#!/usr/bin/env python3
"""
EZBI Analytics - Local Development Server
Entry point for backend API server with Manufacturing API integration
"""

import uvicorn
import sys
import os
import subprocess
import time
import threading
from pathlib import Path

# Try to import requests, install if not available
try:
    import requests
except ImportError:
    print("📦 Installing requests module...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def start_manufacturing_api():
    """Start the Manufacturing API in a separate process"""
    print("🏭 Starting Manufacturing API...")
    
    # Check if Manufacturing API is already running
    try:
        response = requests.get("http://localhost:8003/health", timeout=2)
        if response.status_code == 200:
            print("✅ Manufacturing API is already running on port 8003")
            return True
    except requests.exceptions.RequestException:
        pass
    
    # Start Manufacturing API
    try:
        # Set environment variables for Manufacturing API
        env = os.environ.copy()
        env['ENABLE_SCHEDULER'] = 'false'
        env['FLASK_ENV'] = 'development'
        
        # Start Flask app in background
        flask_process = subprocess.Popen(
            [sys.executable, 'app_flask.py'],
            cwd=backend_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for API to start
        print("⏳ Waiting for Manufacturing API to start...")
        for attempt in range(15):  # 15 seconds timeout
            try:
                response = requests.get("http://localhost:8003/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Manufacturing API started successfully on port 8003")
                    print("📊 Database: Connected with 13 manufacturing tables")
                    print("🔗 API Docs: http://localhost:8003/api/docs")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        print("❌ Manufacturing API failed to start within timeout")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start Manufacturing API: {e}")
        return False

def main():
    """Main entry point for local development"""
    print("🏭 EZBI Analytics - Starting Local Development Server")
    print("=" * 50)
    
    # Check if backend exists
    if not backend_path.exists():
        print("❌ Backend directory not found. Creating project structure...")
        create_backend_structure()
    
    # Start Manufacturing API first
    if not start_manufacturing_api():
        print("⚠️  Manufacturing API failed to start, continuing with FastAPI only...")
    
    try:
        # Import and run FastAPI app
        from app.main import app
        
        print("✅ Backend loaded successfully")
        print("🚀 Starting FastAPI server...")
        print("📖 FastAPI Documentation: http://localhost:8004/docs")
        print("🧪 FastAPI Test Interface: http://localhost:8004/test")
        print("🏭 Manufacturing API: http://localhost:8003")
        print("📊 Manufacturing Dashboard: http://localhost:8003/api/manufacturing/dashboard/overview")
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

def cleanup_processes():
    """Clean up any running processes on exit"""
    print("\n🧹 Cleaning up processes...")
    try:
        # Kill any Flask processes
        subprocess.run(["pkill", "-f", "app_flask.py"], check=False)
        print("✅ Manufacturing API processes cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

if __name__ == "__main__":
    import atexit
    import signal
    
    # Register cleanup function
    atexit.register(cleanup_processes)
    
    # Handle interrupt signals
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        cleanup_processes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        cleanup_processes()
        sys.exit(0)