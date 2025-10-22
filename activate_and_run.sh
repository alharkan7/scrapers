#!/bin/bash

# Helper script to activate virtual environment and run commands
# Usage: ./activate_and_run.sh <command>

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ $# -eq 0 ]; then
    echo "Virtual environment activated. Run your commands now."
    echo "To deactivate, type: deactivate"
    exec bash
else
    echo "Running: $@"
    exec "$@"
fi
