@echo off
title Kishor AI Desktop Agent
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║      KISHOR AI DESKTOP AGENT — Starting      ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found! Install from python.org
    pause
    exit /b 1
)

:: Install requirements
echo  [1/3] Installing required packages...
pip install -r requirements.txt -q
echo  [2/3] Packages ready.

:: Start the agent
echo  [3/3] Starting Kishor Agent...
echo.
python kishor_server.py

pause
