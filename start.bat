@echo off
title n8n Workflow Agent
cd /d "%~dp0"
echo.
echo  [n8n Workflow Agent] starting...
echo.
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Virtual environment not found at .venv\
    echo  Run: python -m venv .venv
    echo  Then: pip install -r requirements.txt
    pause
    exit /b 1
)
echo  API: http://127.0.0.1:8000
echo  UI:  http://localhost:8550
echo.
python main.py
if %errorlevel% neq 0 (
    echo.
    pause
)
