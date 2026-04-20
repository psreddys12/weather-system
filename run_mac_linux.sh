#!/bin/bash

# Quick Setup Script for Telangana Weather Dashboard (Mac/Linux)

echo ""
echo "========================================"
echo "Telangana Weather Forecast Dashboard"
echo "Quick Setup for Mac/Linux"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python from https://www.python.org/downloads/"
    echo "Or use: brew install python3 (on Mac)"
    exit 1
fi

echo "[1/4] Python found:"
python3 --version
echo ""

# Create virtual environment
echo "[2/4] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi
echo ""

# Activate virtual environment
echo "[3/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo ""

# Install requirements
echo "[4/4] Installing dependencies (this may take 2-3 minutes)..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Launching Telangana Weather Dashboard..."
echo "Dashboard will open in your browser at: http://localhost:8501"
echo ""
echo "To stop the dashboard, press Ctrl+C"
echo ""

# Run streamlit app
streamlit run telangana_weather_dashboard.py
