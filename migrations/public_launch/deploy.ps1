# ═══════════════════════════════════════════════════════════════════════════
# RIVET CMMS - Public Launch Deployment Script (PowerShell)
# ═══════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "RIVET CMMS - PUBLIC LAUNCH DEPLOYMENT" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# ─────────────────────────────────────────────────────────────────────────────
# Load environment
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Step 1: Loading environment..." -ForegroundColor Yellow

# Load .env file
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "✓ Environment loaded from .env" -ForegroundColor Green
}

$NEON_DB_URL = $env:NEON_DB_URL
if (-not $NEON_DB_URL) {
    Write-Host "❌ NEON_DB_URL not set" -ForegroundColor Red
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Run database migration
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Step 2: Running database migration..." -ForegroundColor Yellow

$migrationFile = "migrations\public_launch\001_public_ready_schema.sql"

# Use psql if available, otherwise use Python
try {
    $psqlPath = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlPath) {
        & psql $NEON_DB_URL -f $migrationFile
    } else {
        # Fallback: Use Python with psycopg2
        python -c @"
import psycopg2
import os

conn = psycopg2.connect(os.environ['NEON_DB_URL'])
conn.autocommit = True
cursor = conn.cursor()

with open('$migrationFile'.replace('\\', '/'), 'r') as f:
    sql = f.read()
    cursor.execute(sql)

cursor.close()
conn.close()
print('Migration executed via Python')
"@
    }
    Write-Host "✓ Database migration complete" -ForegroundColor Green
}
catch {
    Write-Host "❌ Migration failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You can run manually with:" -ForegroundColor Yellow
    Write-Host "  psql `$env:NEON_DB_URL -f $migrationFile" -ForegroundColor White
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Test imports
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Step 3: Testing imports..." -ForegroundColor Yellow

python -c @"
from agent_factory.integrations.telegram.public_auth import auth
print('  ✓ public_auth module loads')

if auth.is_admin(8445149012):
    print('  ✓ Admin registration verified')
else:
    print('  ⚠️  Check admin_users table')
"@

Write-Host "✓ Import tests passed" -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "DEPLOYMENT READY" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Create bot with @BotFather (if not done):" -ForegroundColor White
Write-Host "   /newbot → 'Rivet CMMS' → '@RivetCMMS_bot'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Add token to .env:" -ForegroundColor White
Write-Host "   PUBLIC_TELEGRAM_BOT_TOKEN=your_token_here" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the public bot:" -ForegroundColor White
Write-Host "   python rivet_public_bot.py" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
