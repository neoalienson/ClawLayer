#!/bin/bash

# Stop ClawLayer backend and web UI

echo "🛑 Stopping ClawLayer..."

# Kill Python backend (run.py)
pkill -f "python run.py"

# Kill Node.js web UI (vite)
pkill -f "vite"

echo "✅ ClawLayer stopped"
