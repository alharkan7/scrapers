#!/bin/bash

# Script to run the student submission scoring system
# This script activates the virtual environment and runs the scoring script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================="
echo "Student Submission Scoring System"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file in the project root with:"
    echo "GEMINI_API_KEY=your_api_key_here"
    echo ""
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "Installing dependencies..."
    "$PROJECT_ROOT/venv/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"
fi

# Activate virtual environment and run the script
echo "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

echo "Running scoring script..."
echo ""
python "$SCRIPT_DIR/score_submissions.py"

echo ""
echo "=================================="
echo "Done!"
echo "=================================="

