#!/bin/bash
# Start ClawLayer with Gunicorn (production WSGI server) and Web UI

echo "Starting ClawLayer with Gunicorn..."
gunicorn -c gunicorn.conf.py wsgi:app &
BACKEND_PID=$!

echo "Starting Web UI..."
cd webui && npm run dev &
WEBUI_PID=$!

echo "ClawLayer backend PID: $BACKEND_PID"
echo "Web UI PID: $WEBUI_PID"
echo ""
echo "Backend API: http://localhost:11435"
echo "Web UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"

# Save PIDs to file for stop script
echo $BACKEND_PID > .backend.pid
echo $WEBUI_PID > .webui.pid

# Wait for both processes
wait
