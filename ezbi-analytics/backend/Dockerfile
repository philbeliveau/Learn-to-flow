# Multi-stage Dockerfile for EZBI Analytics Backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ezbi && useradd -r -g ezbi ezbi

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-basic.txt .
RUN pip install --no-cache-dir -r requirements-basic.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install debugpy pytest-xdist

# Copy source code
COPY . .
RUN chown -R ezbi:ezbi /app

USER ezbi

# Expose port
EXPOSE 8000

# Command for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install cron for job scheduling
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . .

# Create Railway-compatible startup script with database migration
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starting EZBI Analytics Production Server..."\n\
mkdir -p /app/logs /app/data /app/backup\n\
\n\
# Database Migration Logic\n\
if [ ! -z "$DATABASE_URL" ] && [[ "$DATABASE_URL" == *"postgres"* ]]; then\n\
    echo "📊 Railway PostgreSQL detected - running migration..."\n\
    python /app/railway_migrate.py || echo "⚠️ Migration completed with warnings"\n\
    echo "✅ PostgreSQL migration completed"\n\
elif [ ! -f /app/data/ezbi_analytics.db ]; then\n\
    echo "📊 Initializing SQLite database..."\n\
    python -c "\n\
import sys\n\
sys.path.append(\"/app\")\n\
try:\n\
    from app.core.database import init_db\n\
    import asyncio\n\
    asyncio.run(init_db())\n\
    print(\"✅ SQLite database initialized\")\n\
except Exception as e:\n\
    print(f\"⚠️ Database initialization info: {e}\")\n\
" || echo "⚠️ Database initialization skipped (may already exist)"\n\
fi\n\
\n\
# Setup cron jobs\n\
if [ -f /app/deployment/crontab ]; then\n\
    echo "⏰ Setting up cron jobs..."\n\
    crontab /app/deployment/crontab\n\
    service cron start\n\
    echo "✅ Cron jobs configured"\n\
else\n\
    echo "⚠️ No crontab file found, skipping cron setup"\n\
fi\n\
\n\
echo "🌟 Starting FastAPI server on port ${PORT:-8000}..."\n\
exec uvicorn app.main:app \\\n\
    --host 0.0.0.0 \\\n\
    --port ${PORT:-8000} \\\n\
    --workers 2 \\\n\
    --access-log \\\n\
    --log-level info' > /app/start.sh && chmod +x /app/start.sh

# Create necessary directories  
RUN mkdir -p /app/logs /app/uploads /app/static /app/data && \
    chown -R ezbi:ezbi /app

# Switch to non-root user
USER ezbi

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for production
CMD ["/app/start.sh"]