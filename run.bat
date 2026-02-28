@echo off
REM TrueFace AI - Run Script for Windows

echo ========================================
echo TrueFace AI - Starting Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the application
echo Starting TrueFace AI server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python backend\app.py

pause
