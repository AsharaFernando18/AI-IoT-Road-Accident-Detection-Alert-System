@echo off
echo.
echo ========================================
echo  RoadSafeNet System Startup
echo ========================================
echo.

echo [1/2] Stopping any existing services...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend Dashboard (Port 8050)...
echo.
echo Dashboard will open at: http://127.0.0.1:8050
echo Press Ctrl+C to stop the system
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
python -m flask --app frontend.app run --host 127.0.0.1 --port 8050 --debug

pause
