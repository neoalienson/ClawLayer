#!/bin/bash
# Stop ClawLayer production services

if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
fi

if [ -f .webui.pid ]; then
    WEBUI_PID=$(cat .webui.pid)
    echo "Stopping Web UI (PID: $WEBUI_PID)..."
    kill $WEBUI_PID 2>/dev/null
    rm .webui.pid
fi

echo "Services stopped"
