@echo off
color 0B
echo ===============================================
echo        HERMES - Setup Wizard
echo ===============================================
echo.

:: Check if Python is installed
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    echo Please install Python 3.7+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
) else (
    echo Python is installed. Proceeding with setup...
)

:: Check Python version
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYVER=%%a
echo Detected Python version: %PYVER%
echo.

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install requirements
echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo Setup completed successfully!
echo You can now run Hermes using start.bat
echo ===============================================
echo.
pause