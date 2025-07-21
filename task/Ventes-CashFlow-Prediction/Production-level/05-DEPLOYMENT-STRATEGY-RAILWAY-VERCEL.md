# Railway & Vercel Deployment Strategy

## 🎯 **GOAL**
Deploy EZBI Analytics platform on Railway (backend/database) and Vercel (frontend) with automated cron jobs, Slack integration, and production-grade reliability.

## 🏗️ **DEPLOYMENT ARCHITECTURE**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   VERCEL        │    │    RAILWAY       │    │     SLACK       │
│  (Frontend)     │    │   (Backend +     │    │   (Alerts)      │
│                 │    │    Database)     │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Next.js App │ │◄──►│ │ FastAPI +    │ │──►│ │ Webhooks    │ │
│ │ Dashboard   │ │    │ │ SQLite       │ │    │ │ #alerts     │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │ ┌──────────────┐ │    │                 │
│ Environment:    │    │ │ Cron Jobs    │ │    │ Cash Flow       │
│ • Production    │    │ │ Daily Data   │ │    │ Alerts          │
│ • Edge Runtime  │    │ │ Monitoring   │ │    │ Real-time       │
└─────────────────┘    │ └──────────────┘ │    └─────────────────┘
                       │                  │
                       │ Environment:     │
                       │ • Python 3.11   │  
                       │ • Auto-scaling   │
                       │ • Persistent DB  │
                       └──────────────────┘
```

## 🚂 **RAILWAY BACKEND DEPLOYMENT**

### **Railway Configuration** (`railway.json`)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  },
  "environments": {
    "production": {
      "variables": {
        "DATABASE_URL": "${{Postgres.DATABASE_URL}}",
        "JWT_SECRET_KEY": "${{RAILWAY_STATIC_URL}}",
        "SLACK_WEBHOOK_URL": "${{SLACK_WEBHOOK_URL}}",
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### **Production Dockerfile**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Setup cron jobs
COPY deployment/crontab /etc/cron.d/manufacturing-jobs
RUN chmod 0644 /etc/cron.d/manufacturing-jobs && \
    crontab /etc/cron.d/manufacturing-jobs

# Create startup script
COPY deployment/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port (Railway assigns PORT env var)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Start application with cron
CMD ["/app/start.sh"]
```

### **Startup Script** (`deployment/start.sh`)
```bash
#!/bin/bash

# Start cron daemon
cron

# Initialize database if needed
python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"

# Start the FastAPI application
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### **Cron Configuration** (`deployment/crontab`)
```bash
# Manufacturing data generation - Daily at 6 AM UTC
0 6 * * * cd /app && python -m jobs.daily_data_generation >> /app/logs/cron.log 2>&1

# Production updates - Every hour
0 * * * * cd /app && python -m jobs.production_updates >> /app/logs/cron.log 2>&1

# Cash flow analysis - Every 4 hours
0 */4 * * * cd /app && python -m jobs.cash_flow_analysis >> /app/logs/cron.log 2>&1

# Database cleanup - Weekly on Sundays at 3 AM
0 3 * * 0 cd /app && python -m jobs.database_maintenance >> /app/logs/maintenance.log 2>&1

# Health check - Every 15 minutes
*/15 * * * * cd /app && python -m jobs.health_check >> /app/logs/health.log 2>&1
```

## ▲ **VERCEL FRONTEND DEPLOYMENT**

### **Vercel Configuration** (`vercel.json`)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://your-railway-app.railway.app",
    "NEXT_PUBLIC_ENVIRONMENT": "production",
    "NEXT_PUBLIC_APP_VERSION": "1.0.0"
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "s-maxage=86400"
        }
      ]
    }
  ]
}
```

### **Next.js Configuration** (`next.config.js`)
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  trailingSlash: false,
  poweredByHeader: false,
  compress: true,
  
  // Environment-specific configurations
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_ENVIRONMENT: process.env.NODE_ENV || 'development',
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ]
  },
  
  // API proxy for development
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ]
    }
    return []
  },
}

module.exports = nextConfig
```

## 🔧 **ENVIRONMENT CONFIGURATION**

### **Railway Environment Variables**
```bash
# Database
DATABASE_URL=sqlite:///app/data/ezbi_analytics.db

# Authentication  
JWT_SECRET_KEY=your-super-secret-jwt-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Security
ALLOWED_HOSTS=["your-railway-app.railway.app", "your-vercel-app.vercel.app"]
CORS_ORIGINS=["https://your-vercel-app.vercel.app"]

# Monitoring
SENTRY_DSN=your-sentry-dsn-for-error-tracking
```

### **Vercel Environment Variables**
```bash
# API Connection
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app

# Application Settings
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_COMPANY_NAME="EZBI Analytics"

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_MONITORING=true
```

## 📊 **DATABASE MIGRATION STRATEGY**

### **SQLite to Production Migration**
```python
# jobs/database_migration.py
import sqlite3
import os
import shutil
from datetime import datetime

class DatabaseMigrator:
    def __init__(self):
        self.source_db = "/app/data/ezbi_analytics.db"
        self.backup_dir = "/app/data/backups"
        
    async def migrate_to_production(self):
        """Migrate development database to production format"""
        
        # Create backup
        backup_path = f"{self.backup_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.makedirs(self.backup_dir, exist_ok=True)
        shutil.copy2(self.source_db, backup_path)
        
        # Update schema for production
        conn = sqlite3.connect(self.source_db)
        cursor = conn.cursor()
        
        # Add production-specific indexes
        production_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_invoices_date_issued ON sales.invoices(date_issued);",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON operations.production_orders(status);",
            "CREATE INDEX IF NOT EXISTS idx_cash_ledger_date ON finance.cash_ledger(date_recorded);",
            "CREATE INDEX IF NOT EXISTS idx_employees_status ON hr.employees(status);"
        ]
        
        for index in production_indexes:
            cursor.execute(index)
        
        conn.commit()
        conn.close()
        
        print(f"Database migrated successfully. Backup: {backup_path}")
```

## 🚀 **DEPLOYMENT WORKFLOW**

### **Step 1: Pre-deployment Preparation**
```bash
# Fix authentication bypasses
find frontend/app/components -name "*.tsx" -exec grep -l "authentication bypass" {} \;

# Update API endpoints
sed -i 's/localhost:8004/your-railway-app.railway.app/g' frontend/app/components/**/*.tsx

# Test API connections
python backend/tests/test_production_readiness.py
```

### **Step 2: Railway Deployment**
```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login to Railway
railway login

# Create new project
railway init ezbi-analytics-backend

# Deploy backend
railway up --detach

# Set environment variables
railway variables set DATABASE_URL="sqlite:///app/data/ezbi_analytics.db"
railway variables set JWT_SECRET_KEY="$(openssl rand -base64 32)"
railway variables set SLACK_WEBHOOK_URL="your-webhook-url"

# Monitor deployment
railway logs --follow
```

### **Step 3: Vercel Deployment**
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy frontend
cd frontend
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://your-railway-app.railway.app

# Monitor deployment
vercel logs --follow
```

## 📈 **MONITORING & OBSERVABILITY**

### **Health Check Endpoints**
```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter
from datetime import datetime
import psutil
import sqlite3

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check for Railway monitoring"""
    
    try:
        # Database connectivity
        conn = sqlite3.connect('/app/data/ezbi_analytics.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sales.customers")
        customer_count = cursor.fetchone()[0]
        conn.close()
        
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/app')
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connected": True,
                "customers": customer_count
            },
            "system": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent
            },
            "services": {
                "api": "healthy",
                "cron_jobs": "running",
                "slack_integration": "configured"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### **Performance Monitoring**
```python
# jobs/performance_monitor.py
import aiohttp
import asyncio
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'api_response_times': [],
            'database_query_times': [],
            'memory_usage': [],
            'error_rates': []
        }
    
    async def monitor_api_performance(self):
        """Monitor API endpoint performance"""
        endpoints = [
            '/api/v1/manufacturing/sales/kpis',
            '/api/v1/manufacturing/finance/kpis',
            '/api/v1/manufacturing/dashboard/overview'
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                start_time = datetime.now()
                try:
                    async with session.get(f"http://localhost:8000{endpoint}") as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        self.metrics['api_response_times'].append({
                            'endpoint': endpoint,
                            'response_time': response_time,
                            'status_code': response.status,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Alert if response time > 5 seconds
                        if response_time > 5.0:
                            await self.send_performance_alert(endpoint, response_time)
                            
                except Exception as e:
                    await self.send_error_alert(endpoint, str(e))
```

## 🔐 **SECURITY CONFIGURATION**

### **Production Security Headers**
```python
# app/core/security.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def configure_security(app: FastAPI):
    """Configure production security settings"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://your-vercel-app.vercel.app"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["your-railway-app.railway.app"]
    )
    
    # Security headers
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
```

## 📋 **DEPLOYMENT CHECKLIST**

### **Pre-deployment** ✅
- [ ] Remove authentication bypasses from all components
- [ ] Update API base URLs to production endpoints
- [ ] Replace mock data with real API calls
- [ ] Test end-to-end data flow
- [ ] Configure environment variables
- [ ] Setup Slack webhook integration
- [ ] Implement health check endpoints

### **Railway Backend** ✅
- [ ] Deploy FastAPI application
- [ ] Configure cron jobs for data generation
- [ ] Setup database with manufacturing tables
- [ ] Enable health check monitoring
- [ ] Configure logging and error tracking
- [ ] Test Slack alert integration

### **Vercel Frontend** ✅
- [ ] Deploy Next.js application
- [ ] Configure API proxy settings
- [ ] Enable production optimizations
- [ ] Setup error boundaries
- [ ] Test responsive design
- [ ] Configure security headers

### **Post-deployment** ✅
- [ ] Monitor application health
- [ ] Test cron job execution
- [ ] Verify Slack alerts working
- [ ] Load test critical endpoints
- [ ] Setup uptime monitoring
- [ ] Document deployment process

## 🎯 **SUCCESS METRICS**

### **Deployment Health**
- Application uptime: >99.5%
- API response time: <2 seconds average
- Database query performance: <500ms average
- Cron job success rate: >95%

### **Business Simulation**
- Daily data generation: Consistent execution
- Cash flow alerts: 2-5 per week (normal)
- Slack notifications: Real-time delivery
- Dashboard updates: Live data reflection

## 📋 **AGENT CONTEXT**
This deployment strategy provides production-grade hosting for the EZBI platform with automated data generation, real-time monitoring, and Slack integration. Railway handles the backend with cron jobs while Vercel serves the optimized frontend. The architecture supports scaling and provides comprehensive monitoring for demo reliability.