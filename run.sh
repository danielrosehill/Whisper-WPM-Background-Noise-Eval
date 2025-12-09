#!/usr/bin/env bash
# Run the Whisper WPM Eval recorder GUI

cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
    uv pip install -r requirements.txt
fi

# Run with uv
uv run python recorder.py
