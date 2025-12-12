# Setup Telegram Bot Auto-Start via Task Scheduler

$TaskName = "AgentFactoryTelegramBot"
$ScriptPath = "C:\Users\hharp\OneDrive\Desktop\Agent Factory\scripts\start_telegram_bot.bat"

# Delete existing task if it exists
schtasks /delete /TN $TaskName /F 2>$null

# Create new task that runs at logon
$action = New-ScheduledTaskAction -Execute $ScriptPath
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "SUCCESS: Telegram bot will now auto-start on login"
Write-Host "Task Name: $TaskName"
Write-Host "Script: $ScriptPath"
