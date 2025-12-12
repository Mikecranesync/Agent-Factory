# Install Telegram Bot as Windows Service
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install_telegram_service.ps1

$serviceName = "AgentFactoryTelegramBot"
$displayName = "Agent Factory Telegram Bot"
$description = "Telegram bot for Agent Factory KB access (auto-starts on boot)"

# Get project directory
$projectDir = Split-Path -Parent $PSScriptRoot
$pythonPath = & poetry env info --path
$pythonExe = Join-Path $pythonPath "Scripts\python.exe"
$botScript = Join-Path $projectDir "agent_factory\integrations\telegram\__main__.py"

# Create NSSM service (Non-Sucking Service Manager)
# Download NSSM if not present
$nssmPath = Join-Path $projectDir "bin\nssm.exe"
$nssmDir = Join-Path $projectDir "bin"

if (-not (Test-Path $nssmPath)) {
    Write-Host "Downloading NSSM (service manager)..."
    New-Item -ItemType Directory -Force -Path $nssmDir | Out-Null

    # Download NSSM 2.24
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = Join-Path $env:TEMP "nssm.zip"

    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath $env:TEMP -Force

        # Copy 64-bit version
        $nssmExe = Join-Path $env:TEMP "nssm-2.24\win64\nssm.exe"
        Copy-Item $nssmExe $nssmPath -Force

        Remove-Item $nssmZip -Force
        Remove-Item (Join-Path $env:TEMP "nssm-2.24") -Recurse -Force

        Write-Host "[OK] NSSM installed to $nssmPath"
    } catch {
        Write-Host "[ERROR] Failed to download NSSM: $_"
        Write-Host "Manual install: Download from https://nssm.cc/download and place nssm.exe in $nssmDir"
        exit 1
    }
}

# Stop existing service if running
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Removing existing service..."
    & $nssmPath stop $serviceName
    & $nssmPath remove $serviceName confirm
    Start-Sleep -Seconds 2
}

# Install service
Write-Host "Installing service: $displayName"
& $nssmPath install $serviceName $pythonExe "-m" "agent_factory.integrations.telegram"

# Configure service
& $nssmPath set $serviceName AppDirectory $projectDir
& $nssmPath set $serviceName DisplayName $displayName
& $nssmPath set $serviceName Description $description
& $nssmPath set $serviceName Start SERVICE_AUTO_START
& $nssmPath set $serviceName AppStdout (Join-Path $projectDir "logs\telegram_bot.log")
& $nssmPath set $serviceName AppStderr (Join-Path $projectDir "logs\telegram_bot_error.log")
& $nssmPath set $serviceName AppRotateFiles 1
& $nssmPath set $serviceName AppRotateOnline 1
& $nssmPath set $serviceName AppRotateBytes 1048576  # 1MB

# Create logs directory
$logsDir = Join-Path $projectDir "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

# Start service
Write-Host "Starting service..."
& $nssmPath start $serviceName

Start-Sleep -Seconds 3

# Check status
$status = & $nssmPath status $serviceName
Write-Host ""
Write-Host "=========================================="
Write-Host "Service Status: $status"
Write-Host "=========================================="
Write-Host ""

if ($status -eq "SERVICE_RUNNING") {
    Write-Host "[OK] Telegram bot is now running 24/7!"
    Write-Host ""
    Write-Host "Service Details:"
    Write-Host "  Name: $serviceName"
    Write-Host "  Display: $displayName"
    Write-Host "  Auto-start: Yes (starts on Windows boot)"
    Write-Host "  Logs: $logsDir"
    Write-Host ""
    Write-Host "Service Commands:"
    Write-Host "  Start:   nssm start $serviceName"
    Write-Host "  Stop:    nssm stop $serviceName"
    Write-Host "  Restart: nssm restart $serviceName"
    Write-Host "  Status:  nssm status $serviceName"
    Write-Host "  Remove:  nssm remove $serviceName confirm"
    Write-Host ""
    Write-Host "Or use Windows Services (services.msc)"
} else {
    Write-Host "[ERROR] Service failed to start"
    Write-Host "Check logs in: $logsDir"
    Write-Host "Run: Get-EventLog -LogName Application -Source $serviceName -Newest 10"
}
