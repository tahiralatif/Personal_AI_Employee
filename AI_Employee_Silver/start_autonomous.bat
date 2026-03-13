@echo off
REM AI Employee - Autonomous Mode
REM Double-click to start ALL agents automatically

echo.
echo ================================================================
echo    AI EMPLOYEE - AUTONOMOUS MODE
echo ================================================================
echo.
echo Starting ALL AI agents...
echo - Gmail Agent (emails)
echo - WhatsApp Agent (messages)
echo - LinkedIn Agent (posts)
echo.
echo All agents will run 24/7 automatically.
echo Press Ctrl+C to stop.
echo.
echo ================================================================
echo.

cd /d "%~dp0"

REM Run autonomous mode
python -m src.ai_employee_silver.autonomous_run

pause
