@echo off
REM ============================================================
REM  Tactical Knowledge Assistant — Windows Setup Script
REM ============================================================

echo.
echo   Tactical Knowledge Assistant - Setup
echo   =====================================
echo.

REM Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found.
    echo         Download from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo [OK] Python found
python --version

REM Check Ollama
ollama --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ollama not found.
    echo         Download from https://ollama.ai/download
    pause
    exit /b 1
)
echo [OK] Ollama found

REM Create virtual environment
IF NOT EXIST ".venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
)
echo [OK] Virtual environment ready

REM Install dependencies
echo.
echo [*] Installing Python dependencies (this may take a few minutes)...
.venv\Scripts\pip install --upgrade pip -q
.venv\Scripts\pip install -r requirements.txt
echo [OK] Dependencies installed

REM Pull the Ollama model
echo.
echo [*] Downloading Ollama model qwen2.5:3b (~1.9 GB)...
echo     This may take several minutes depending on your internet speed.
ollama pull qwen2.5:3b
echo [OK] Model downloaded

REM Create required directories
IF NOT EXIST "data\vector_store" mkdir data\vector_store
IF NOT EXIST "logs" mkdir logs
echo [OK] Directories ready

echo.
echo   =====================================
echo   [OK] Setup complete!
echo.
echo   To start the application:
echo     1. Open a terminal and run:  ollama serve
echo     2. Open another terminal and run:
echo          .venv\Scripts\activate
echo          streamlit run main.py
echo   =====================================
echo.
pause
