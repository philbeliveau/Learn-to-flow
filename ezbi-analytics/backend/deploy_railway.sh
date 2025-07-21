#!/bin/bash
set -e

echo "🚀 EZBI Analytics - Railway Deployment Script"
echo "============================================="

# Check if we have Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check Railway authentication
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run:"
    echo "   railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Deploy to Railway
echo "🚀 Deploying to Railway..."

# First, let's check if the service is linked
if ! railway service &> /dev/null; then
    echo "🔗 Linking to Railway service..."
    # The service should auto-link during deployment
fi

# Build and deploy
echo "📦 Starting Railway deployment..."
railway up --detach

echo "⏳ Waiting for deployment to complete..."
sleep 30

# Get the deployment URL
RAILWAY_URL=$(railway status --json | jq -r '.deployments[0].url' 2>/dev/null || echo "")

if [ ! -z "$RAILWAY_URL" ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Backend URL: $RAILWAY_URL"
    
    # Test the health endpoint
    echo "🔍 Testing health endpoint..."
    if curl -f "$RAILWAY_URL/health" &> /dev/null; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check failed - may still be starting up"
    fi
    
    # Test manufacturing API
    echo "🔍 Testing manufacturing API..."
    if curl -f "$RAILWAY_URL/api/manufacturing/sales/kpis" &> /dev/null; then
        echo "✅ Manufacturing API ready"
    else
        echo "⚠️  Manufacturing API not ready - may still be migrating database"
    fi
    
    echo ""
    echo "🎉 Railway deployment completed!"
    echo "📊 Backend URL: $RAILWAY_URL"
    echo ""
    echo "Next steps:"
    echo "1. Update Vercel NEXT_PUBLIC_API_URL to: $RAILWAY_URL"
    echo "2. Deploy frontend to Vercel"
    
else
    echo "⚠️  Could not retrieve deployment URL"
    echo "Check Railway dashboard for deployment status"
fi

echo ""
echo "🔗 Railway Dashboard: https://railway.app/dashboard"