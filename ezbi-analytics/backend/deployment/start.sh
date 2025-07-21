#!/bin/bash
set -e

echo "🚀 Starting EZBI Analytics Production Server..."

# Initialize logging
mkdir -p /app/logs
touch /app/logs/app.log

# Start cron daemon
echo "⏰ Starting cron daemon..."
service cron start

# Wait a moment for cron to fully start
sleep 2

# Verify cron is running
if pgrep cron > /dev/null; then
    echo "✅ Cron daemon started successfully"
else
    echo "❌ Failed to start cron daemon"
    exit 1
fi

# Initialize database if needed
if [ ! -f /app/data/ezbi_analytics.db ]; then
    echo "📊 Initializing manufacturing database..."
    python -c "
import sys
sys.path.append('/app')
try:
    from app.core.database import init_db
    init_db()
    print('✅ Database initialized')
except Exception as e:
    print(f'⚠️ Database initialization info: {e}')
" || echo "⚠️ Database initialization skipped (may already exist)"
fi

# Run initial health checks
echo "🔍 Running initial system checks..."

# Test Slack configuration if webhook is set
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    echo "✅ Slack webhook configured"
    python -c "
import asyncio
import sys
sys.path.append('/app')
from jobs.slack_notifier import SlackNotifier
async def test_slack():
    notifier = SlackNotifier()
    if notifier.test_configuration():
        await notifier.send_system_alert('info', 'EZBI Analytics production deployment started', {
            'version': '2.0.0',
            'environment': 'production',
            'timestamp': '$(date -Iseconds)'
        })
        print('✅ Slack notifications active')
    else:
        print('⚠️ Slack configuration issue')
asyncio.run(test_slack())
" 2>/dev/null || echo "⚠️ Slack test skipped"
else
    echo "⚠️ SLACK_WEBHOOK_URL not configured - notifications disabled"
fi

# Start the main FastAPI application
echo "🌟 Starting FastAPI server on port ${PORT:-8000}..."

# Use exec to replace the shell process with uvicorn
# This ensures proper signal handling for graceful shutdowns
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 2 \
    --access-log \
    --log-level info \
    --loop uvloop