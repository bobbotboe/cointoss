#!/bin/bash
# CoinToss — start both API and UI for local development

set -e

echo "🪙 CoinToss — Starting..."

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copy .env.example and add your ANTHROPIC_API_KEY"
    exit 1
fi

# Init database if needed
source .venv/bin/activate 2>/dev/null || { echo "Creating venv..."; python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"; }

echo "📦 Initialising database..."
python3 -m cointoss.cli init

echo "📡 Importing latest US lottery data..."
python3 -m cointoss.cli import-us 2>/dev/null &

echo ""
echo "🚀 Starting API server on http://localhost:3005"
python3 -m uvicorn cointoss.api.main:app --port 3005 --reload &
API_PID=$!

echo "🎨 Starting UI on http://localhost:5177"
cd ui && npm run dev &
UI_PID=$!

echo ""
echo "═══════════════════════════════════════"
echo "  🪙 CoinToss is running!"
echo "  API:  http://localhost:3005"
echo "  UI:   http://localhost:5177"
echo "  Docs: http://localhost:3005/docs"
echo "═══════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $API_PID $UI_PID 2>/dev/null; exit 0" INT TERM
wait
