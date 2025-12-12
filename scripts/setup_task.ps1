# Create Telegram Bot Auto-Start Task

$taskName = "AgentFactoryTelegramBot"
$batFile = "C:\Users\hharp\OneDrive\Desktop\Agent Factory\scripts\start_telegram_bot.bat"

# Create task action
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batFile`""

# Create task trigger (at logon)
$trigger = New-ScheduledTaskTrigger -AtLogon

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0)

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register new task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null

Write-Host "[OK] Auto-start task created: $taskName"
Write-Host ""
Write-Host "The Telegram bot will now start automatically when you log in."
Write-Host ""
Write-Host "To verify: Get-ScheduledTask -TaskName '$taskName'"
