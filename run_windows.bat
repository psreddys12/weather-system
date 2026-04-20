@echo off
REM Quick Setup Script for Telangana Weather Dashboard (Windows)

echo.
echo ========================================
echo Telangana Weather Forecast Dashboard
echo Quick Setup for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/4] Python found: 
python --version
echo.

REM Create virtual environment
echo [2/4] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping creation
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo.

REM Activate virtual environment
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install requirements
echo [4/4] Installing dependencies (this may take 2-3 minutes)...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Launching Telangana Weather Dashboard...
echo Dashboard will open in your browser at: http://localhost:8501
echo.
echo To stop the dashboard, press Ctrl+C in this window
echo.

REM Run streamlit app
streamlit run telangana_weather_dashboard.py

pause
