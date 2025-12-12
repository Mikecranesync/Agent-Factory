# Setup Windows Task Scheduler for 24/7 KB Automation
# Run as Administrator

param(
    [switch]$Force = $false
)

Write-Host "============================================================"
Write-Host "Agent Factory - Windows Task Scheduler Setup"
Write-Host "============================================================"
Write-Host ""
Write-Host "This will create 3 scheduled tasks for 24/7 automation:"
Write-Host "  1. Daily KB Building (2:00 AM)"
Write-Host "  2. Weekly Maintenance (Sunday 12:00 AM)"
Write-Host "  3. Health Monitor (every 15 minutes)"
Write-Host ""

# Check if running as Administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then try again"
    exit 1
}

# Get project root
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Write-Host "Project root: $ProjectRoot"
Write-Host ""

# Find Poetry executable
$PoetryExe = (Get-Command poetry -ErrorAction SilentlyContinue).Source
if (-not $PoetryExe) {
    Write-Host "❌ ERROR: Poetry not found in PATH" -ForegroundColor Red
    exit 1
}

# Get Poetry's Python executable
$PoetryEnv = & poetry env info --path 2>$null
if ($PoetryEnv) {
    $PythonExe = Join-Path $PoetryEnv "Scripts\python.exe"
} else {
    $PythonExe = "python.exe"
}

Write-Host "Python executable: $PythonExe"
Write-Host "Poetry executable: $PoetryExe"
Write-Host ""

# Confirm
if (-not $Force) {
    $Confirm = Read-Host "Continue with setup? (y/N)"
    if ($Confirm -ne 'y') {
        Write-Host "Setup cancelled"
        exit 0
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "TASK 1: Daily KB Building"
Write-Host "============================================================"
Write-Host ""

$TaskName1 = "AgentFactory_KB_Daily"
$ScriptPath1 = Join-Path $ProjectRoot "scripts\scheduler_kb_daily.py"
$Command1 = "`"$PoetryExe`" run python `"$ScriptPath1`""

# Check if task exists
$ExistingTask1 = schtasks /query /tn $TaskName1 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  Task '$TaskName1' already exists. Removing..." -ForegroundColor Yellow
    schtasks /delete /tn $TaskName1 /f
}

# Create task (runs daily at 2:00 AM)
schtasks /create `
    /tn $TaskName1 `
    /tr "cmd /c cd /d `"$ProjectRoot`" && $Command1" `
    /sc daily `
    /st 02:00 `
    /rl HIGHEST `
    /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Task '$TaskName1' created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create task '$TaskName1'" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================"
Write-Host "TASK 2: Weekly Maintenance"
Write-Host "============================================================"
Write-Host ""

$TaskName2 = "AgentFactory_KB_Weekly"
$ScriptPath2 = Join-Path $ProjectRoot "scripts\scheduler_kb_weekly.py"
$Command2 = "`"$PoetryExe`" run python `"$ScriptPath2`""

# Check if task exists
$ExistingTask2 = schtasks /query /tn $TaskName2 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  Task '$TaskName2' already exists. Removing..." -ForegroundColor Yellow
    schtasks /delete /tn $TaskName2 /f
}

# Create task (runs weekly on Sunday at 12:00 AM)
schtasks /create `
    /tn $TaskName2 `
    /tr "cmd /c cd /d `"$ProjectRoot`" && $Command2" `
    /sc weekly `
    /d SUN `
    /st 00:00 `
    /rl HIGHEST `
    /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Task '$TaskName2' created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create task '$TaskName2'" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================"
Write-Host "TASK 3: Health Monitor"
Write-Host "============================================================"
Write-Host ""

$TaskName3 = "AgentFactory_HealthMonitor"
$ScriptPath3 = Join-Path $ProjectRoot "scripts\health_monitor.py"
$Command3 = "`"$PoetryExe`" run python `"$ScriptPath3`""

# Check if task exists
$ExistingTask3 = schtasks /query /tn $TaskName3 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  Task '$TaskName3' already exists. Removing..." -ForegroundColor Yellow
    schtasks /delete /tn $TaskName3 /f
}

# Create task (runs every 15 minutes)
schtasks /create `
    /tn $TaskName3 `
    /tr "cmd /c cd /d `"$ProjectRoot`" && $Command3" `
    /sc minute `
    /mo 15 `
    /rl HIGHEST `
    /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Task '$TaskName3' created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create task '$TaskName3'" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Setup Complete"
Write-Host "============================================================"
Write-Host ""
Write-Host "✅ Created 3 scheduled tasks:"
Write-Host "  1. $TaskName1 (Daily 2:00 AM)"
Write-Host "  2. $TaskName2 (Sunday 12:00 AM)"
Write-Host "  3. $TaskName3 (Every 15 minutes)"
Write-Host ""
Write-Host "Verify tasks:"
Write-Host "  schtasks /query /tn $TaskName1"
Write-Host "  schtasks /query /tn $TaskName2"
Write-Host "  schtasks /query /tn $TaskName3"
Write-Host ""
Write-Host "Run tasks manually (for testing):"
Write-Host "  schtasks /run /tn $TaskName1"
Write-Host "  schtasks /run /tn $TaskName2"
Write-Host "  schtasks /run /tn $TaskName3"
Write-Host ""
Write-Host "View logs:"
Write-Host "  type data\logs\kb_daily_{date}.log"
Write-Host "  type data\logs\kb_weekly_week{week}.log"
Write-Host "  type data\logs\health_monitor.log"
Write-Host ""
Write-Host "Disable tasks (if needed):"
Write-Host "  schtasks /change /tn $TaskName1 /disable"
Write-Host "  schtasks /change /tn $TaskName2 /disable"
Write-Host "  schtasks /change /tn $TaskName3 /disable"
Write-Host ""
Write-Host "Delete tasks (if needed):"
Write-Host "  schtasks /delete /tn $TaskName1 /f"
Write-Host "  schtasks /delete /tn $TaskName2 /f"
Write-Host "  schtasks /delete /tn $TaskName3 /f"
Write-Host ""
Write-Host "🚀 24/7 automation is now running!"
Write-Host ""
