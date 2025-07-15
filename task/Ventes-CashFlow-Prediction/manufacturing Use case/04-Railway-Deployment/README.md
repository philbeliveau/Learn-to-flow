# Railway Deployment Guide

## 🚂 Railway Setup Instructions

### 1. Project Creation
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway create manufacturing-data-simulator

# Link to existing project (if already created)
railway link
```

### 2. Environment Variables Setup

**Required Environment Variables:**
```env
# Database Connection
DATABASE_URL=postgresql://username:password@host:port/database

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application Configuration
PORT=8000
ENVIRONMENT=production
SIMULATION_SCHEDULE=0 6 * * *
RUN_INITIAL_SIMULATION=true
LOG_LEVEL=INFO

# Optional: EZBI Platform Integration
EZBI_API_URL=https://your-ezbi-platform.vercel.app/api
EZBI_API_KEY=your-api-key-here
```

### 3. Database Setup

**Option A: Railway PostgreSQL Service**
```bash
# Add PostgreSQL service to your project
railway add postgresql

# The DATABASE_URL will be automatically set
```

**Option B: External PostgreSQL**
Set `DATABASE_URL` manually in Railway dashboard.

### 4. Deployment Commands

```bash
# Deploy to Railway
railway up

# Deploy with specific service
railway up --service manufacturing-simulator

# Check deployment status
railway status

# View logs
railway logs

# Open deployed application
railway open
```

### 5. Volume Configuration

**For Excel exports (Railway Volumes):**
```json
{
  "volumes": [
    {
      "name": "exports",
      "mountPath": "/app/exports"
    }
  ]
}
```

### 6. Custom Domain Setup

```bash
# Add custom domain
railway domain add your-domain.com

# Generate SSL certificate (automatic)
```

## 📊 Railway Dashboard Configuration

### Services Architecture
```
manufacturing-data-simulator/
├── 🐍 Python Service (main app)
├── 🗄️ PostgreSQL Database  
└── 📁 Volume (Excel exports)
```

### Monitoring Setup
- **Health Check**: `/health` endpoint
- **Metrics**: Built-in Railway monitoring
- **Logs**: Accessible via Railway CLI or dashboard
- **Alerts**: Configure via Railway webhooks

### Scaling Configuration
```json
{
  "deploy": {
    "replicas": 1,
    "resources": {
      "cpu": "1000m",
      "memory": "1Gi"
    }
  }
}
```

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
railway run python -c "import asyncpg; print('Connection test')"
```

**2. Scheduling Issues**
```bash
# Check logs for scheduler status
railway logs --tail

# Verify timezone settings
railway run python -c "from datetime import datetime; print(datetime.now())"
```

**3. Excel Export Problems**
```bash
# Check volume mount
railway run ls -la /app/exports

# Test write permissions
railway run touch /app/exports/test.txt
```

## 🚀 Production Checklist

- [ ] Database schema deployed and seeded
- [ ] Environment variables configured
- [ ] Slack webhook URL tested
- [ ] Health check endpoint responding
- [ ] Daily simulation schedule verified
- [ ] Excel export directory writable
- [ ] Logs configured and accessible
- [ ] Custom domain configured (optional)
- [ ] Backup strategy implemented

## 📈 Performance Optimization

### Railway-Specific Optimizations
```python
# In main.py - optimize for Railway
import os

# Use Railway's internal networking
if os.getenv("RAILWAY_ENVIRONMENT"):
    DATABASE_URL = os.getenv("DATABASE_PRIVATE_URL") or os.getenv("DATABASE_URL")
```

### Resource Limits
- **CPU**: 1 vCPU (sufficient for daily simulation)
- **Memory**: 1GB (handles all data processing)
- **Storage**: 10GB volume for Excel exports
- **Network**: Railway's built-in CDN

## 🔗 Integration Endpoints

### EZBI Platform Integration
```python
# Add to main.py for platform integration
@app.get("/api/v1/data/latest")
async def get_latest_data():
    """Endpoint for EZBI platform to fetch latest data"""
    return await simulator.get_data_summary()

@app.webhook("/webhook/simulation-complete")
async def simulation_webhook(data: dict):
    """Webhook to notify EZBI platform of completed simulation"""
    # Notify EZBI platform
    pass
```

### Slack Integration Test
```bash
# Test Slack webhook
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-type: application/json' \
  -d '{"text":"Railway deployment test from manufacturing simulator"}'
```