# 🚀 STRATÉGIE DE DÉPLOIEMENT - EZBI ANALYTICS

## 🎯 APPROCHE DEPLOYMENT

### Philosophie DevOps
```
🔄 "Continuous Intelligence Delivery"

Principes Directeurs:
├── Zero-Downtime Deployment: Disponibilité 99.9%
├── Automated Pipeline: CI/CD intelligent
├── Infrastructure as Code: Reproductibilité totale
├── Monitoring First: Observabilité complète
└── Security by Design: Sécurité intégrée
```

### Stratégie Multi-Environnements
```
🌍 Environment Strategy

Development (dev)
├── Local development
├── Feature branches
├── Unit tests
└── Rapid iteration

Staging (staging)
├── Production-like data
├── Integration tests
├── Performance tests
└── Stakeholder validation

Production (prod)
├── Blue-green deployment
├── Canary releases
├── Real user monitoring
└── Incident response
```

---

## 🏗️ ARCHITECTURE DE DÉPLOIEMENT

### Infrastructure Overview
```
☁️ Cloud-Native Deployment Architecture

┌─────────────────────────────────────────────────────────────┐
│                        USERS                                │
│         Web App    │    Mobile App    │    API Clients     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    CDN LAYER                                │
│  Cloudflare/AWS CloudFront                                  │
│  - Global edge locations                                    │
│  - DDoS protection                                          │
│  - SSL termination                                          │
│  - Static asset caching                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  LOAD BALANCER                              │
│  AWS ALB / Cloudflare Load Balancer                        │
│  - Traffic distribution                                     │
│  - Health checks                                            │
│  - SSL termination                                          │
│  - Request routing                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│  FRONTEND  │ │   API GW   │ │  ML SERVICE│
│  (Vercel)  │ │ (Railway)  │ │ (Railway)  │
│            │ │            │ │            │
│ - Next.js  │ │ - FastAPI  │ │ - ML Models│
│ - Static   │ │ - Auth     │ │ - Training │
│ - SSG/SSR  │ │ - Business │ │ - Inference│
│ - Edge     │ │ - Logic    │ │ - GPU Opt  │
└────────────┘ └─────┬──────┘ └─────┬──────┘
                     │               │
              ┌──────▼──────┐ ┌─────▼──────┐
              │  DATABASE   │ │   STORAGE  │
              │(PostgreSQL) │ │   (S3/R2)  │
              │             │ │            │
              │ - User Data │ │ - Files    │
              │ - Trans.    │ │ - Models   │
              │ - Pred.     │ │ - Exports  │
              │ - Backup    │ │ - Logs     │
              └─────────────┘ └────────────┘
```

### Choix Technologiques de Déploiement

#### Frontend - Vercel
```yaml
# 🌐 Frontend Deployment Configuration

# vercel.json
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
      "src": "/api/(.*)",
      "dest": "https://api.ezbi.fr/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.ezbi.fr",
    "NEXT_PUBLIC_APP_ENV": "production"
  },
  "functions": {
    "pages/api/**": {
      "runtime": "nodejs18.x",
      "regions": ["cdg1"]
    }
  },
  "regions": ["cdg1"],
  "framework": "nextjs"
}

# Performance Optimizations
{
  "trailingSlash": false,
  "cleanUrls": true,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    },
    {
      "source": "/static/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

#### Backend - Railway
```yaml
# 🚂 Railway Deployment Configuration

# railway.toml
[build]
builder = "dockerfile"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[environments.production]
variables = [
  "DATABASE_URL=${{ Postgres.DATABASE_URL }}",
  "REDIS_URL=${{ Redis.REDIS_URL }}",
  "JWT_SECRET=${{ secrets.JWT_SECRET }}",
  "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}",
  "SLACK_WEBHOOK_URL=${{ secrets.SLACK_WEBHOOK }}",
  "AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY }}",
  "AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_KEY }}",
  "SENTRY_DSN=${{ secrets.SENTRY_DSN }}"
]

[environments.staging]
variables = [
  "DATABASE_URL=${{ Postgres.STAGING_DATABASE_URL }}",
  "REDIS_URL=${{ Redis.STAGING_REDIS_URL }}",
  "APP_ENV=staging"
]

# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
```

---

## 🔄 PIPELINE CI/CD

### GitHub Actions Workflow
```yaml
# 🔄 Complete CI/CD Pipeline

# .github/workflows/deploy.yml
name: EZBI Analytics CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: 18
  PYTHON_VERSION: 3.11

jobs:
  # Frontend Testing & Build
  frontend-ci:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'npm'
        cache-dependency-path: 'frontend/package-lock.json'
        
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
      
    - name: Run TypeScript checks
      working-directory: ./frontend
      run: npm run type-check
      
    - name: Run ESLint
      working-directory: ./frontend
      run: npm run lint
      
    - name: Run unit tests
      working-directory: ./frontend
      run: npm run test:unit -- --coverage
      
    - name: Run component tests
      working-directory: ./frontend
      run: npm run test:component
      
    - name: Build application
      working-directory: ./frontend
      run: npm run build
      
    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: frontend-build
        path: frontend/.next/

  # Backend Testing & Build
  backend-ci:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: ezbi_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
        
    - name: Install dependencies
      working-directory: ./backend
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        
    - name: Run code formatting checks
      working-directory: ./backend
      run: |
        black --check .
        isort --check-only .
        
    - name: Run linting
      working-directory: ./backend
      run: |
        flake8 .
        mypy .
        
    - name: Run unit tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/ezbi_test
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/unit/ -v --cov=./ --cov-report=xml --cov-report=html
        
    - name: Run integration tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/ezbi_test
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/integration/ -v
        
    - name: Run ML model tests
      working-directory: ./backend
      run: |
        pytest tests/ml/ -v --timeout=300
        
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        
  # Security Scanning
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
        
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
        
    - name: Semgrep Security Scan
      uses: returntocorp/semgrep-action@v1
      with:
        config: auto
        
  # End-to-End Testing
  e2e-tests:
    runs-on: ubuntu-latest
    needs: [frontend-ci, backend-ci]
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        
    - name: Install Playwright
      run: |
        npm install -g @playwright/test
        playwright install
        
    - name: Run E2E tests
      env:
        BASE_URL: https://staging.ezbi.fr
      run: |
        npx playwright test --config=playwright.config.ts
        
    - name: Upload E2E test results
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: e2e-test-results
        path: test-results/

  # Performance Testing
  performance-tests:
    runs-on: ubuntu-latest
    needs: [frontend-ci, backend-ci]
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Run Lighthouse CI
      uses: treosh/lighthouse-ci-action@v10
      with:
        urls: |
          https://staging.ezbi.fr
          https://staging.ezbi.fr/dashboard
        configPath: './lighthouserc.json'
        uploadArtifacts: true
        temporaryPublicStorage: true
        
    - name: Run load testing with k6
      uses: grafana/k6-action@v0.3.1
      with:
        filename: tests/performance/load-test.js
        flags: --out influxdb=http://localhost:8086/k6

  # Deployment to Staging
  deploy-staging:
    runs-on: ubuntu-latest
    needs: [frontend-ci, backend-ci, security-scan]
    if: github.ref == 'refs/heads/develop'
    
    environment:
      name: staging
      url: https://staging.ezbi.fr
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Deploy to Vercel (Staging)
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        working-directory: ./frontend
        alias-domains: staging.ezbi.fr
        
    - name: Deploy to Railway (Staging)
      uses: railway-deploy/railway-deploy@v1
      with:
        service: ezbi-api-staging
        environment: staging
        railway-token: ${{ secrets.RAILWAY_TOKEN }}

  # Deployment to Production
  deploy-production:
    runs-on: ubuntu-latest
    needs: [frontend-ci, backend-ci, security-scan, e2e-tests, performance-tests]
    if: github.ref == 'refs/heads/main'
    
    environment:
      name: production
      url: https://ezbi.fr
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: v${{ github.run_number }}
        release_name: Release v${{ github.run_number }}
        draft: false
        prerelease: false
        
    - name: Deploy to Vercel (Production)
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        vercel-args: '--prod'
        working-directory: ./frontend
        
    - name: Deploy to Railway (Production)
      uses: railway-deploy/railway-deploy@v1
      with:
        service: ezbi-api-production
        environment: production
        railway-token: ${{ secrets.RAILWAY_TOKEN }}
        
    - name: Run post-deployment health checks
      run: |
        curl -f https://api.ezbi.fr/health || exit 1
        curl -f https://ezbi.fr || exit 1
        
    - name: Notify Slack on success
      uses: 8398a7/action-slack@v3
      with:
        status: success
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        message: '🚀 EZBI Analytics v${{ github.run_number }} déployé en production avec succès!'

  # Post-deployment monitoring
  post-deployment:
    runs-on: ubuntu-latest
    needs: [deploy-production]
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Wait for deployment stabilization
      run: sleep 60
      
    - name: Run smoke tests
      run: |
        # API Health checks
        curl -f https://api.ezbi.fr/health
        curl -f https://api.ezbi.fr/metrics
        
        # Frontend checks
        curl -f https://ezbi.fr
        
        # ML Service checks
        curl -f https://api.ezbi.fr/ml/health
        
    - name: Update monitoring dashboards
      run: |
        curl -X POST "https://api.datadog.com/api/v1/events" \
        -H "Content-Type: application/json" \
        -H "DD-API-KEY: ${{ secrets.DATADOG_API_KEY }}" \
        -d '{
          "title": "EZBI Production Deployment",
          "text": "Version ${{ github.run_number }} deployed successfully",
          "tags": ["deployment", "production", "ezbi"]
        }'
```

---

## 🌊 STRATÉGIES DE DÉPLOIEMENT

### Blue-Green Deployment
```yaml
# 🔵🟢 Blue-Green Deployment Strategy

# Railway Blue-Green Configuration
production:
  services:
    - name: ezbi-api-blue
      branch: main
      environment: production-blue
      replicas: 3
      
    - name: ezbi-api-green
      branch: main
      environment: production-green
      replicas: 3
      active: false

deployment_strategy:
  type: blue_green
  steps:
    1. Deploy to Green environment
    2. Run health checks on Green
    3. Run smoke tests on Green
    4. Switch traffic to Green (0% → 100%)
    5. Monitor metrics for 10 minutes
    6. If stable: decommission Blue
    7. If issues: instant rollback to Blue

# Traffic switching script
switch_traffic_to_green() {
  # Update load balancer configuration
  railway config set ACTIVE_ENVIRONMENT=production-green
  
  # Wait for propagation
  sleep 30
  
  # Verify switch
  curl -f https://api.ezbi.fr/health
  
  # Monitor key metrics
  monitor_metrics_for_minutes 10
  
  if [[ $? -eq 0 ]]; then
    echo "✅ Green deployment successful"
    decommission_blue_environment
  else
    echo "❌ Issues detected, rolling back to Blue"
    railway config set ACTIVE_ENVIRONMENT=production-blue
  fi
}
```

### Canary Releases
```yaml
# 🐤 Canary Release Strategy

canary_deployment:
  stages:
    - name: canary_5_percent
      traffic_percentage: 5
      duration: 30m
      success_criteria:
        - error_rate < 0.5%
        - response_time_p95 < 2000ms
        - user_satisfaction > 4.5/5
        
    - name: canary_25_percent
      traffic_percentage: 25
      duration: 60m
      success_criteria:
        - error_rate < 0.3%
        - response_time_p95 < 1500ms
        - conversion_rate >= baseline
        
    - name: canary_50_percent
      traffic_percentage: 50
      duration: 120m
      success_criteria:
        - error_rate < 0.2%
        - response_time_p95 < 1200ms
        - no_critical_alerts
        
    - name: full_rollout
      traffic_percentage: 100
      monitoring_duration: 24h

# Automated canary monitoring
monitor_canary_metrics() {
  while [[ $canary_active == true ]]; do
    # Check error rates
    error_rate=$(get_error_rate_last_5min)
    if (( $(echo "$error_rate > 0.5" | bc -l) )); then
      trigger_automatic_rollback "High error rate: $error_rate%"
      return 1
    fi
    
    # Check response times
    p95_latency=$(get_p95_latency_last_5min)
    if (( $(echo "$p95_latency > 2000" | bc -l) )); then
      trigger_automatic_rollback "High latency: ${p95_latency}ms"
      return 1
    fi
    
    # Check ML model accuracy
    ml_accuracy=$(get_ml_accuracy_last_hour)
    if (( $(echo "$ml_accuracy < 0.85" | bc -l) )); then
      trigger_automatic_rollback "ML accuracy degraded: $ml_accuracy"
      return 1
    fi
    
    sleep 60
  done
}
```

### Feature Flags
```typescript
// 🎛️ Feature Flag Implementation

interface FeatureFlags {
  enableNewMLModel: boolean;
  enableAdvancedAnalytics: boolean;
  enableSlackIntegration: boolean;
  enableBetaFeatures: boolean;
  maintenanceMode: boolean;
}

class FeatureFlagService {
  private flags: FeatureFlags;
  private environment: string;
  
  constructor(environment: string) {
    this.environment = environment;
    this.loadFlags();
  }
  
  private async loadFlags() {
    // Load from external service (LaunchDarkly, Split.io, etc.)
    const response = await fetch(`https://api.featureflags.io/ezbi/${this.environment}`);
    this.flags = await response.json();
    
    // Local overrides for development
    if (this.environment === 'development') {
      this.flags = {
        ...this.flags,
        enableBetaFeatures: true,
        enableAdvancedAnalytics: true
      };
    }
  }
  
  isEnabled(flagName: keyof FeatureFlags): boolean {
    return this.flags[flagName] ?? false;
  }
  
  // Gradual rollout
  isEnabledForUser(flagName: keyof FeatureFlags, userId: string): boolean {
    const baseEnabled = this.isEnabled(flagName);
    if (!baseEnabled) return false;
    
    // Hash-based rollout (consistent per user)
    const hash = this.hashUserId(userId);
    const rolloutPercentage = this.getRolloutPercentage(flagName);
    
    return hash % 100 < rolloutPercentage;
  }
  
  private getRolloutPercentage(flagName: keyof FeatureFlags): number {
    const rolloutConfig = {
      enableNewMLModel: 25,      // 25% rollout
      enableAdvancedAnalytics: 50, // 50% rollout
      enableSlackIntegration: 100, // Full rollout
      enableBetaFeatures: 10,     // 10% rollout
      maintenanceMode: 0          // Disabled
    };
    
    return rolloutConfig[flagName] ?? 0;
  }
  
  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
}

// Usage in components
export function usePredictionModel() {
  const featureFlags = useFeatureFlags();
  const user = useUser();
  
  const shouldUseNewModel = featureFlags.isEnabledForUser('enableNewMLModel', user.id);
  
  return {
    modelType: shouldUseNewModel ? 'ensemble-v2' : 'ensemble-v1',
    isExperimental: shouldUseNewModel
  };
}
```

---

## 📊 MONITORING & OBSERVABILITÉ

### Métriques Clés
```python
# 📈 Production Monitoring Setup

import structlog
import sentry_sdk
from prometheus_client import Counter, Histogram, Gauge
from datadog import initialize, statsd

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ML_PREDICTION_ACCURACY = Gauge('ml_prediction_accuracy', 'ML model accuracy', ['model_type'])
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
CASH_FLOW_PREDICTIONS = Counter('cash_flow_predictions_total', 'Total predictions generated')

# Application Metrics
class MetricsCollector:
    def __init__(self):
        self.logger = structlog.get_logger()
        
        # Initialize Sentry for error tracking
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            environment=os.getenv('APP_ENV'),
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        
        # Initialize Datadog
        initialize(
            api_key=os.getenv('DATADOG_API_KEY'),
            app_key=os.getenv('DATADOG_APP_KEY')
        )
    
    def track_prediction_request(self, user_id: str, model_type: str, processing_time: float):
        """Track ML prediction metrics"""
        
        # Prometheus
        CASH_FLOW_PREDICTIONS.inc()
        REQUEST_DURATION.observe(processing_time)
        
        # Datadog
        statsd.increment('ezbi.predictions.requested', tags=[
            f'model_type:{model_type}',
            f'user_id:{user_id}'
        ])
        
        statsd.histogram('ezbi.predictions.processing_time', processing_time, tags=[
            f'model_type:{model_type}'
        ])
        
        # Structured logging
        self.logger.info("prediction_requested", 
            user_id=user_id,
            model_type=model_type,
            processing_time=processing_time
        )
    
    def track_model_accuracy(self, model_type: str, accuracy: float):
        """Track ML model accuracy"""
        
        # Prometheus
        ML_PREDICTION_ACCURACY.labels(model_type=model_type).set(accuracy)
        
        # Datadog
        statsd.gauge('ezbi.ml.accuracy', accuracy, tags=[f'model_type:{model_type}'])
        
        # Alert if accuracy drops
        if accuracy < 0.85:
            sentry_sdk.capture_message(
                f"ML accuracy below threshold: {accuracy:.3f} for {model_type}",
                level='warning'
            )
    
    def track_user_activity(self, user_id: str, action: str, metadata: dict = None):
        """Track user behavior"""
        
        statsd.increment('ezbi.user.activity', tags=[
            f'action:{action}',
            f'user_id:{user_id}'
        ])
        
        self.logger.info("user_activity",
            user_id=user_id,
            action=action,
            metadata=metadata or {}
        )
    
    def track_business_metrics(self, metric_name: str, value: float, tags: list = None):
        """Track business KPIs"""
        
        statsd.gauge(f'ezbi.business.{metric_name}', value, tags=tags or [])
        
        # Important business metrics
        if metric_name == 'monthly_recurring_revenue':
            self.logger.info("mrr_update", mrr=value)
        
        elif metric_name == 'customer_churn_rate':
            if value > 0.05:  # 5% monthly churn threshold
                sentry_sdk.capture_message(
                    f"High churn rate detected: {value:.2%}",
                    level='warning'
                )

# Health Check Endpoints
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/deep")
async def deep_health_check():
    """Comprehensive health check"""
    
    checks = {}
    overall_healthy = True
    
    # Database check
    try:
        await check_database_connection()
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Redis check
    try:
        await check_redis_connection()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # ML models check
    try:
        model_status = await check_ml_models()
        checks["ml_models"] = model_status
        if not all(model["loaded"] for model in model_status.values()):
            overall_healthy = False
    except Exception as e:
        checks["ml_models"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # External services check
    try:
        await check_external_services()
        checks["external_services"] = {"status": "healthy"}
    except Exception as e:
        checks["external_services"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    status_code = 200 if overall_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### Alerting Configuration
```yaml
# 🚨 Alerting Rules Configuration

# Datadog Monitors
datadog_monitors:
  - name: "EZBI API High Error Rate"
    type: metric alert
    query: "avg(last_5m):sum:ezbi.api.errors{*}.as_rate() > 0.05"
    message: |
      🚨 High error rate detected in EZBI API
      Error rate: {{value}}%
      
      Runbook: https://docs.ezbi.fr/runbooks/high-error-rate
      
      @slack-#incidents @pagerduty-ezbi-oncall
    
    thresholds:
      critical: 0.05  # 5%
      warning: 0.02   # 2%
    
    notify_no_data: true
    no_data_timeframe: 10  # minutes

  - name: "EZBI ML Model Accuracy Degradation"
    type: metric alert
    query: "avg(last_30m):avg:ezbi.ml.accuracy{*} < 0.85"
    message: |
      🧠 ML model accuracy below threshold
      Current accuracy: {{value}}
      Threshold: 85%
      
      This may indicate:
      - Data drift
      - Model degradation
      - Training pipeline issues
      
      Immediate actions:
      1. Check recent prediction quality
      2. Review training data
      3. Consider model retraining
      
      @slack-#ml-alerts @email-ml-team@ezbi.fr
    
    thresholds:
      critical: 0.85
      warning: 0.90

  - name: "EZBI Response Time P95 High"
    type: metric alert
    query: "avg(last_10m):p95:ezbi.api.response_time{*} > 2000"
    message: |
      ⏱️ API response time P95 above threshold
      Current P95: {{value}}ms
      Threshold: 2000ms
      
      Check:
      - Database performance
      - ML model inference time
      - External service latency
      
      @slack-#performance-alerts
    
    thresholds:
      critical: 2000  # 2s
      warning: 1500   # 1.5s

# PagerDuty Integration
pagerduty_services:
  - name: "EZBI Production Critical"
    escalation_policy: "Engineering Escalation"
    alert_creation: "create_alerts_and_incidents"
    
  - name: "EZBI ML Models"
    escalation_policy: "Data Science Escalation"
    alert_creation: "create_incidents_only"

# Slack Notifications
slack_channels:
  - name: "#incidents"
    alerts: ["critical", "high"]
    
  - name: "#ml-alerts"
    alerts: ["ml_accuracy", "model_errors"]
    
  - name: "#deployments"
    alerts: ["deployment_success", "deployment_failure"]
    
  - name: "#performance"
    alerts: ["latency", "throughput"]
```

---

## 🔧 GESTION DES SECRETS

### Vault Configuration
```yaml
# 🔐 Secret Management Strategy

# HashiCorp Vault (Alternative to Railway secrets)
vault_config:
  secrets_engine: "kv-v2"
  mount_path: "ezbi"
  
  policies:
    - name: "ezbi-production"
      permissions:
        - path: "ezbi/data/production/*"
          capabilities: ["read"]
        - path: "ezbi/data/shared/*"
          capabilities: ["read"]
    
    - name: "ezbi-staging"
      permissions:
        - path: "ezbi/data/staging/*"
          capabilities: ["read"]
        - path: "ezbi/data/shared/*"
          capabilities: ["read"]

# Secret rotation policy
secret_rotation:
  jwt_secret:
    frequency: "90d"
    type: "automatic"
    
  database_passwords:
    frequency: "30d"
    type: "manual"
    
  api_keys:
    frequency: "180d"
    type: "automatic"
    notification: ["#security", "security@ezbi.fr"]

# Environment-specific secrets
secrets:
  shared:
    - SENTRY_DSN
    - DATADOG_API_KEY
    - OPENAI_API_KEY
    
  production:
    - DATABASE_URL
    - REDIS_URL
    - JWT_SECRET
    - SLACK_WEBHOOK_URL
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    
  staging:
    - STAGING_DATABASE_URL
    - STAGING_REDIS_URL
    - STAGING_JWT_SECRET
    - STAGING_SLACK_WEBHOOK_URL
```

Cette stratégie de déploiement complète assure une mise en production sécurisée, scalable et monitorée pour EZBI Analytics, avec des pratiques DevOps modernes et une observabilité maximale.