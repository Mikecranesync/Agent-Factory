# Install Agent Factory Telegram Bot as Windows Service using NSSM
#
# NSSM (Non-Sucking Service Manager) is a service helper that wraps
# any executable as a Windows Service with:
# - Auto-restart on failure
# - Proper logging to Event Viewer
# - Prevents duplicate instances (service manager enforces singleton)
#
# Prerequisites:
#   1. Install NSSM: https://nssm.cc/download
#   2. Add NSSM to PATH or specify full path below
#
# Usage:
#   Run as Administrator:
#   PowerShell -ExecutionPolicy Bypass -File scripts\install_windows_service.ps1

param(
    [string]$ServiceName = "AgentFactoryTelegramBot",
    [string]$DisplayName = "Agent Factory Telegram Bot",
    [string]$Description = "AI-powered Telegram bot for industrial maintenance knowledge base and GitHub automation"
)

# Check if running as Administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then try again"
    exit 1
}

# Check if NSSM is installed
$NssmPath = Get-Command nssm.exe -ErrorAction SilentlyContinue
if (-not $NssmPath) {
    Write-Host "❌ ERROR: NSSM not found in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install NSSM:"
    Write-Host "  1. Download: https://nssm.cc/download"
    Write-Host "  2. Extract to C:\nssm"
    Write-Host "  3. Add to PATH or specify full path in this script"
    Write-Host ""
    Write-Host "Quick install with Chocolatey:"
    Write-Host "  choco install nssm"
    exit 1
}

Write-Host "=" * 60
Write-Host "Agent Factory Telegram Bot - Windows Service Installer"
Write-Host "=" * 60
Write-Host ""

# Project paths
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BotManagerScript = Join-Path $ProjectRoot "scripts\bot_manager.py"
$PythonExe = (Get-Command poetry -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    Write-Host "❌ ERROR: Poetry not found in PATH" -ForegroundColor Red
    Write-Host "Make sure Poetry is installed and in your PATH"
    exit 1
}

# Get Poetry's Python executable
$PoetryEnv = & poetry env info --path 2>$null
if ($PoetryEnv) {
    $PythonExe = Join-Path $PoetryEnv "Scripts\python.exe"
} else {
    $PythonExe = "python.exe"
}

Write-Host "Configuration:"
Write-Host "  Service Name:  $ServiceName"
Write-Host "  Display Name:  $DisplayName"
Write-Host "  Project Root:  $ProjectRoot"
Write-Host "  Bot Manager:   $BotManagerScript"
Write-Host "  Python Exe:    $PythonExe"
Write-Host ""

# Check if service already exists
$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($ExistingService) {
    Write-Host "⚠️ Service '$ServiceName' already exists" -ForegroundColor Yellow
    Write-Host ""
    $Confirm = Read-Host "Remove existing service and reinstall? (y/N)"
    if ($Confirm -ne 'y') {
        Write-Host "Installation cancelled"
        exit 0
    }

    Write-Host "Stopping and removing existing service..."
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
    Write-Host "✅ Removed existing service"
    Write-Host ""
}

# Install service
Write-Host "Installing service..."
Write-Host ""

# NSSM installation command
# Path to bot_manager.py wrapped in quotes
$AppPath = $PythonExe
$AppParameters = "`"$BotManagerScript`" start"
$AppDirectory = $ProjectRoot

# Install service
nssm install $ServiceName $AppPath $AppParameters

# Configure service
nssm set $ServiceName DisplayName $DisplayName
nssm set $ServiceName Description $Description
nssm set $ServiceName AppDirectory $AppDirectory

# Set startup type to automatic (delayed start)
nssm set $ServiceName Start SERVICE_DELAYED_AUTO_START

# Configure logging
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$StdOutLog = Join-Path $LogDir "telegram_bot_stdout.log"
$StdErrLog = Join-Path $LogDir "telegram_bot_stderr.log"

nssm set $ServiceName AppStdout $StdOutLog
nssm set $ServiceName AppStderr $StdErrLog

# Rotate logs daily (keep 30 days)
nssm set $ServiceName AppRotateFiles 1
nssm set $ServiceName AppRotateOnline 1
nssm set $ServiceName AppRotateSeconds 86400  # 1 day
nssm set $ServiceName AppRotateBytes 10485760  # 10MB max size

# Configure restart behavior
nssm set $ServiceName AppRestartDelay 5000  # Wait 5 seconds before restart
nssm set $ServiceName AppThrottle 10000  # Throttle if restarting too quickly

# Set exit actions (restart on failure)
nssm set $ServiceName AppExit Default Restart
nssm set $ServiceName AppExit 0 Exit  # Clean exit (0) = don't restart

Write-Host "✅ Service installed successfully!"
Write-Host ""

# Start service
Write-Host "Starting service..."
nssm start $ServiceName

# Wait for startup
Start-Sleep -Seconds 3

# Check status
$Status = nssm status $ServiceName
Write-Host "Service Status: $Status"
Write-Host ""

if ($Status -eq "SERVICE_RUNNING") {
    Write-Host "✅ Bot is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Logs:"
    Write-Host "  STDOUT: $StdOutLog"
    Write-Host "  STDERR: $StdErrLog"
    Write-Host ""
    Write-Host "Service Management:"
    Write-Host "  Start:   nssm start $ServiceName"
    Write-Host "  Stop:    nssm stop $ServiceName"
    Write-Host "  Restart: nssm restart $ServiceName"
    Write-Host "  Status:  nssm status $ServiceName"
    Write-Host "  Remove:  nssm remove $ServiceName confirm"
    Write-Host ""
    Write-Host "Or use Windows Services (services.msc)"
} else {
    Write-Host "⚠️ Service installed but not running" -ForegroundColor Yellow
    Write-Host "Check logs for errors:"
    Write-Host "  $StdErrLog"
}

Write-Host ""
Write-Host "=" * 60
