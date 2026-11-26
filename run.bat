@echo off
title CogniLoad — Cognitive Load Analyzer
cd /d "%~dp0"

echo.
echo  ===================================
echo   CogniLoad — Cognitive Load Analyzer
echo   LGU AI Project
echo  ===================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist ".deps_installed" (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo installed > .deps_installed
    echo [INFO] Dependencies installed successfully.
)

echo [INFO] Starting CogniLoad...
echo [INFO] The app will appear in the system tray when minimized.
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] CogniLoad exited with an error. Check the output above.
    pause
)
