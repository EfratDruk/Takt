@echo off
cd /d "%~dp0"
start "Takt Web App" cmd /k "python web_app.py"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000"
