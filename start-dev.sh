#!/bin/bash

# Start ClawLayer with Web UI

echo "🦅 Starting ClawLayer..."
echo ""
echo "Backend API: http://localhost:11435"
echo "Web UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Start Python backend in background
cd "$(dirname "$0")"
python run.py -v &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Node.js web UI
cd webui
npm run dev &
WEBUI_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $WEBUI_PID 2>/dev/null" EXIT

# Wait for both processes
wait
