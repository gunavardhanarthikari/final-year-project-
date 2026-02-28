@echo off
REM TrueFace AI - Setup Script for Windows
REM This script sets up the development environment

echo ========================================
echo TrueFace AI - Setup Script
echo ========================================
echo.

REM Check Python installation
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [5/6] Installing dependencies...
echo This may take several minutes...
pip install -r requirements.txt
echo.

REM Initialize database
echo [6/6] Initializing database...
python backend\init_db.py
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To run the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run the server: python backend\app.py
echo   3. Open browser: http://localhost:5000
echo.
echo Note: On first run, DeepFace will download AI models (~200MB)
echo This is a one-time download and may take a few minutes.
echo.
pause
