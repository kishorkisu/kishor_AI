@echo off
title Kishor AI Assistant Agent
color 0B
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       KISHOR AI ASSISTANT — Starting Agent...       ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Please install Python 3.8+
    echo  Download: https://python.org/downloads
    pause
    exit /b 1
)

:: Install requirements
echo  Installing/checking requirements...
pip install pyautogui Pillow psutil pyttsx3 -q

echo.
echo  Starting Kishor Agent...
echo.

:: Launch agent
python kishor_agent.py

pause
