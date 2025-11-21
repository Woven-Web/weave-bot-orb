#!/bin/bash
# Simple script to run the event scraper API

# Navigate to weave-bot-orb root so PYTHONPATH works
cd "$(dirname "$0")/.."

# Set the Python path to weave-bot-orb root
export PYTHONPATH="$(pwd)"

echo "Starting Event Scraper API..."
echo "PYTHONPATH: $PYTHONPATH"
echo ""
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the server
python3 agent/main.py
