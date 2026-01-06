#!/bin/bash

# Intelligent Slides Generator - Development Server Startup Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting Intelligent Slides Generator..."
echo ""

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Backend .env file not found!"
    echo "Please create backend/.env with your OPENAI_API_KEY"
    echo "Run: cp backend/.env.example backend/.env"
    exit 1
fi

if [ ! -f ".env.local" ]; then
    echo "⚠️  Frontend .env.local file not found!"
    echo "Creating .env.local from .env.example..."
    cp .env.example .env.local
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start FastAPI backend
echo "📦 Starting FastAPI backend on http://localhost:8000..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 2

# Start Next.js frontend
echo "🎨 Starting Next.js frontend on http://localhost:3001..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started successfully!"
echo ""
echo "📍 Frontend: http://localhost:3001"
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait
