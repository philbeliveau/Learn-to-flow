#!/bin/bash

echo "🚀 Deploying EZBI Analytics Backend to Railway"
echo "=============================================="

# Check if we're logged in
echo "📋 Checking Railway authentication..."
railway whoami

# Check current project status
echo "📊 Current Railway project status..."
railway status

# Try to deploy
echo "🚀 Attempting deployment..."
railway up

echo "✅ Deployment script completed"