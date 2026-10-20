@echo off
REM EatUp Pro - Quick Start Script
REM Launch the disk cleanup tool

echo ================================================
echo    EATUP PRO - Disk Cleanup Tool
echo ================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
python -m pip show winshell psutil >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing required packages...
    python -m pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        echo Try running as Administrator
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
    echo.
)

echo Starting EatUp Pro...
echo.
echo Options:
echo   1. Open Web Interface (GUI application)
echo   2. Run Command Line Version
echo.

set /p choice="Enter your choice (1-2): "

if "%choice%"=="1" (
    echo.
    echo Opening web interface...
    start index.html
    timeout /t 2 >nul
    start app.html
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo Starting command line version...
    python cleaner.py
    goto :end
)

echo Invalid choice. Defaulting to web interface.
start index.html
timeout /t 2 >nul
start app.html

:end
echo.
echo ================================================
pause
