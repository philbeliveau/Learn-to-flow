#!/bin/bash

echo "🚀 EZBI Analytics - Quick Local Test"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 found"

# Install FastAPI if not available
echo "📦 Installing required packages..."
pip3 install fastapi uvicorn pydantic

echo ""
echo "🎯 Starting EZBI Analytics API..."
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Test Frontend: file://$(pwd)/frontend/simple_test.html"
echo ""
echo "Demo credentials:"
echo "   Email: demo@ezbi.fr"
echo "   Password: demo123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API
cd backend
python3 simple_app.py