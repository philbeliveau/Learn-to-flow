#!/bin/bash

# EZBI Analytics - Manufacturing API Startup Script
# This script starts the Manufacturing API and ensures it stays running

echo "🏭 Starting EZBI Analytics Manufacturing API..."
echo "================================================="

# Check if API is already running
if pgrep -f "app_flask.py" > /dev/null; then
    echo "⚠️  API is already running. Stopping existing process..."
    pkill -f app_flask.py
    sleep 2
fi

# Set environment variables
export ENABLE_SCHEDULER=false
export FLASK_ENV=development

# Start the API in background
echo "🚀 Starting Flask API on port 8003..."
nohup python3 app_flask.py > flask_app.log 2>&1 &
API_PID=$!

# Wait for API to start
sleep 3

# Test API connectivity
echo "🔍 Testing API connectivity..."
if curl -s http://localhost:8003/health > /dev/null; then
    echo "✅ API is running successfully!"
    echo "📍 URL: http://localhost:8003"
    echo "📋 API Docs: http://localhost:8003/api/docs"
    echo "🏥 Health Check: http://localhost:8003/health"
    echo "📊 Dashboard: http://localhost:8003/api/manufacturing/dashboard/overview"
    echo ""
    echo "🔗 Main Endpoints:"
    echo "   • Sales: http://localhost:8003/api/manufacturing/sales/"
    echo "   • Accounting: http://localhost:8003/api/manufacturing/accounting/"
    echo "   • Operations: http://localhost:8003/api/manufacturing/operations/"
    echo "   • Finance: http://localhost:8003/api/manufacturing/finance/"
    echo "   • HR: http://localhost:8003/api/manufacturing/hr/"
    echo "   • Expenses: http://localhost:8003/api/manufacturing/expenses/"
    echo ""
    echo "📝 Process ID: $API_PID"
    echo "📄 Logs: flask_app.log"
    echo ""
    echo "To stop the API, run: pkill -f app_flask.py"
else
    echo "❌ API failed to start. Check flask_app.log for details."
    exit 1
fi

echo "================================================="
echo "🎉 Manufacturing API is ready for dashboard integration!"