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

# Start full manufacturing API with database
echo "🌟 Starting EZBI Analytics Manufacturing API..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 2 \
    --access-log \
    --log-level info