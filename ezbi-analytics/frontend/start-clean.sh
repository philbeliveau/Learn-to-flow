#!/bin/bash

# Clean start script for EZBI Analytics Frontend
# This script ensures no conflicting processes are running before starting

echo "🧹 Cleaning up any existing Next.js processes..."

# Kill any existing Next.js processes on port 3000
EXISTING_PID=$(lsof -t -i:3000 2>/dev/null)
if [ ! -z "$EXISTING_PID" ]; then
    echo "Found existing process on port 3000 (PID: $EXISTING_PID), killing it..."
    kill $EXISTING_PID
    sleep 2
    echo "✅ Process killed"
else
    echo "✅ Port 3000 is already free"
fi

# Also clean up port 3001 just in case
EXISTING_PID_3001=$(lsof -t -i:3001 2>/dev/null)
if [ ! -z "$EXISTING_PID_3001" ]; then
    echo "Found existing process on port 3001 (PID: $EXISTING_PID_3001), killing it..."
    kill $EXISTING_PID_3001
    sleep 2
    echo "✅ Process killed"
fi

echo "🚀 Starting EZBI Analytics Frontend..."
echo "📍 Will start on: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "---"

# Start the development server
npm run dev