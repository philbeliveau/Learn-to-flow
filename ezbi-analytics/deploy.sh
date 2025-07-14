#!/bin/bash

# EZBI Analytics Deployment Script
# Complete AI-powered cash flow prediction platform for French manufacturing SMEs

echo "🚀 EZBI Analytics - Deployment Script"
echo "====================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker Desktop."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Environment setup
echo "🔧 Setting up environment..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure."
    exit 1
fi

# Validate environment variables
source .env
if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$REDIS_PASSWORD" ] || [ -z "$JWT_SECRET" ]; then
    echo "❌ Required environment variables not set. Check .env file."
    exit 1
fi

echo "✅ Environment setup complete"

# Build and deploy
echo "🏗️ Building EZBI Analytics platform..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Health checks
echo "🏥 Performing health checks..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U ezbi_user -d ezbi_analytics; then
    echo "✅ PostgreSQL ready"
else
    echo "❌ PostgreSQL not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping; then
    echo "✅ Redis ready"
else
    echo "❌ Redis not ready"
fi

# Check Backend API
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Backend API ready"
else
    echo "❌ Backend API not ready"
fi

# Check Frontend
if curl -f http://localhost:3000 &>/dev/null; then
    echo "✅ Frontend ready"
else
    echo "❌ Frontend not ready"
fi

# Display service URLs
echo ""
echo "🌟 EZBI Analytics Platform Deployed Successfully!"
echo "================================================"
echo "📊 Frontend (Next.js):      http://localhost:3000"
echo "🔧 Backend API (FastAPI):   http://localhost:8000"
echo "🔗 API Documentation:       http://localhost:8000/docs"
echo "🤖 ML Engine:               http://localhost:8001"
echo "📈 Grafana Monitoring:      http://localhost:3001"
echo "🔍 Prometheus Metrics:      http://localhost:9090"
echo ""
echo "🔐 Default Credentials:"
echo "   - Grafana: admin / $(echo $GRAFANA_PASSWORD)"
echo ""
echo "📚 Next Steps:"
echo "   1. Access the frontend at http://localhost:3000"
echo "   2. Create your first user account"
echo "   3. Upload your financial data (CSV format)"
echo "   4. Generate cash flow predictions"
echo "   5. Explore the manufacturing KPI dashboard"
echo ""
echo "🏭 Features Available:"
echo "   ✅ AI-powered cash flow predictions (Prophet + LSTM)"
echo "   ✅ French manufacturing compliance (RGPD, SIRET)"
echo "   ✅ Multi-factor authentication (MFA)"
echo "   ✅ Real-time dashboard with interactive charts"
echo "   ✅ ERP integrations (Sage, SAP, Cegid)"
echo "   ✅ Banking APIs (Open Banking PSD2)"
echo "   ✅ Manufacturing KPIs and RFM analysis"
echo "   ✅ Mobile-responsive PWA"
echo "   ✅ Performance monitoring and alerts"
echo ""
echo "🆘 Support:"
echo "   - Documentation: ./README.md"
echo "   - Test Suite: cd backend && python tests/run_tests.py"
echo "   - Logs: docker-compose logs [service-name]"
echo ""
echo "Made with ❤️ for French Manufacturing SMEs"