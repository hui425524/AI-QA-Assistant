@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Python environment not found.
  echo Run: py -m venv .venv
  echo Then: .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
  pause
  exit /b 1
)

start "AI QA Assistant Server" /min ".venv\Scripts\python.exe" run.py
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000"

endlocal
