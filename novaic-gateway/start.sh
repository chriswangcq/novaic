#!/bin/bash
# NovAIC Gateway Startup Script

set -e

# Change to gateway directory
cd "$(dirname "$0")"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Set environment variables
export NOVAIC_HOST="${NOVAIC_HOST:-127.0.0.1}"
export NOVAIC_PORT="${NOVAIC_PORT:-19999}"

echo "Starting NovAIC Gateway on http://$NOVAIC_HOST:$NOVAIC_PORT"
python main.py
