#!/bin/sh
set -e

# Init database and import data on first run
python3 -m cointoss.cli init
echo "Database initialised."

# Start API server (serves both API and static frontend)
exec python3 -m uvicorn cointoss.api.main:app --host 0.0.0.0 --port 3005
