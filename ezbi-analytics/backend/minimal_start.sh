#!/bin/bash
set -e

echo "🚀 EZBI Analytics - Minimal Production Server"
echo "============================================="

# Create required directories
mkdir -p /app/logs /app/data /app/backup

# Simple database check
echo "📊 Database status check..."
if [ -f "/app/data/ezbi_analytics.db" ]; then
    echo "✅ Database file exists"
else
    echo "⚠️ No database file found"
fi

# Test Python environment
echo "🐍 Python environment check..."
python --version
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import uvicorn; print('Uvicorn: OK')"
python -c "import sys; sys.path.append('/app'); from app.main import app; print('App import: OK')"

# Start the server with minimal configuration
echo "🌟 Starting FastAPI server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --log-level info