@echo off
REM Windows 24/7 Orchestrator Launcher
REM Run this to start the MasterOrchestratorAgent

echo ======================================================================
echo MASTER ORCHESTRATOR - 24/7 STARTUP
echo ======================================================================
echo.
echo Starting autonomous video production system...
echo Press Ctrl+C to stop
echo.
echo ======================================================================

cd /d "%~dp0\.."

REM Activate poetry environment and run
poetry run python agents/orchestration/master_orchestrator_agent.py

pause
