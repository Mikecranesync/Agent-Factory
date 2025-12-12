@echo off
REM Create scheduled task for Telegram bot auto-start

schtasks /Create /SC ONLOGON /TN "AgentFactoryTelegramBot" /TR "cmd /c \"C:\Users\hharp\OneDrive\Desktop\Agent Factory\scripts\start_telegram_bot.bat\"" /RL HIGHEST /F

if %errorlevel% equ 0 (
    echo [OK] Auto-start task created successfully!
    echo.
    echo The Telegram bot will now start automatically when you log in.
    echo.
    echo To check status: schtasks /Query /TN "AgentFactoryTelegramBot"
    echo To run now: schtasks /Run /TN "AgentFactoryTelegramBot"
) else (
    echo [ERROR] Failed to create task (Error code: %errorlevel%)
)

pause
