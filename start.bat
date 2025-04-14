@echo off
color 0B
echo ===============================================
echo        HERMES TikTok Username Monitor
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    echo Please install Python 3.7+ and try again.
    echo.
    pause
    exit /b 1
)

:: Run the Hermes script
echo Starting Hermes...
echo.
python hermes.py
echo.
echo Hermes has closed.
pause