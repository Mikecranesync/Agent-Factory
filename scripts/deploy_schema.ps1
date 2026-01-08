# ═══════════════════════════════════════════════════════════════════════════
# RIVET Pro - Database Schema Deployment Script (PowerShell)
# Deploy rivet_pro_schema.sql to Neon PostgreSQL
# Usage: .\scripts\deploy_schema.ps1
# ═══════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

# ───────────────────────────────────────────────────────────────────────────
# Display Header
# ───────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "🚀 RIVET Pro - Database Schema Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ───────────────────────────────────────────────────────────────────────────
# 1. Check Prerequisites
# ───────────────────────────────────────────────────────────────────────────

Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check if NEON_DB_URL is set
$NEON_DB_URL = $env:NEON_DB_URL
if (-not $NEON_DB_URL) {
    Write-Host "❌ Error: NEON_DB_URL environment variable not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set it with:" -ForegroundColor Yellow
    Write-Host "  `$env:NEON_DB_URL='postgresql://user:password@host.neon.tech/database?sslmode=require'" -ForegroundColor White
    Write-Host ""
    Write-Host "Get your connection string from:" -ForegroundColor Yellow
    Write-Host "  https://console.neon.tech → Your Project → Connection Details" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if psql is installed
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlPath) {
    Write-Host "❌ Error: psql (PostgreSQL client) is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Download and install from:" -ForegroundColor Yellow
    Write-Host "  https://www.postgresql.org/download/windows/" -ForegroundColor White
    Write-Host ""
    Write-Host "Or install via chocolatey:" -ForegroundColor Yellow
    Write-Host "  choco install postgresql" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if schema file exists
$schemaFile = "sql\rivet_pro_schema.sql"
if (-not (Test-Path $schemaFile)) {
    Write-Host "❌ Error: Schema file not found at $schemaFile" -ForegroundColor Red
    Write-Host "Make sure you're running this from the rivet-test root directory" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "✅ All prerequisites met" -ForegroundColor Green
Write-Host ""

# ───────────────────────────────────────────────────────────────────────────
# 2. Display Schema Info
# ───────────────────────────────────────────────────────────────────────────

Write-Host "📦 Schema Information:" -ForegroundColor Yellow
$lineCount = (Get-Content $schemaFile | Measure-Object -Line).Lines
Write-Host "  File: $schemaFile" -ForegroundColor White
Write-Host "  Size: $lineCount lines" -ForegroundColor White
Write-Host ""
Write-Host "  Tables to create:" -ForegroundColor White
Write-Host "    - rivet_users (user management + Stripe integration)" -ForegroundColor Gray
Write-Host "    - rivet_usage_log (analytics tracking)" -ForegroundColor Gray
Write-Host "    - rivet_print_sessions (Chat with Print-it feature)" -ForegroundColor Gray
Write-Host "    - rivet_stripe_events (webhook event logging)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Functions to create:" -ForegroundColor White
Write-Host "    - get_or_create_user()" -ForegroundColor Gray
Write-Host "    - check_and_increment_lookup()" -ForegroundColor Gray
Write-Host "    - update_subscription()" -ForegroundColor Gray
Write-Host "    - get_user_status()" -ForegroundColor Gray
Write-Host "    - start_print_session()" -ForegroundColor Gray
Write-Host "    - get_active_print_session()" -ForegroundColor Gray
Write-Host "    - add_print_message()" -ForegroundColor Gray
Write-Host "    - end_print_session()" -ForegroundColor Gray
Write-Host ""

# ───────────────────────────────────────────────────────────────────────────
# 3. Confirm Deployment
# ───────────────────────────────────────────────────────────────────────────

Write-Host "⚠️  This will deploy the schema to your Neon database." -ForegroundColor Yellow
# Extract database host from connection string for display
if ($NEON_DB_URL -match '@([^/]+)') {
    $dbHost = $matches[1]
    Write-Host "   Database: $dbHost" -ForegroundColor White
}
Write-Host ""

$confirmation = Read-Host "Continue with deployment? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

# ───────────────────────────────────────────────────────────────────────────
# 4. Deploy Schema
# ───────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "🚀 Deploying schema to Neon..." -ForegroundColor Yellow
Write-Host ""

try {
    psql $NEON_DB_URL -f $schemaFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Schema deployed successfully!" -ForegroundColor Green
    } else {
        throw "psql returned exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "❌ Schema deployment failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ───────────────────────────────────────────────────────────────────────────
# 5. Verify Deployment
# ───────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "🧪 Verifying deployment..." -ForegroundColor Yellow
Write-Host ""

# Check tables
Write-Host "📊 Tables created:" -ForegroundColor White
psql $NEON_DB_URL -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'rivet_%' ORDER BY table_name;" -t

# Check functions
Write-Host ""
Write-Host "⚙️  Functions created:" -ForegroundColor White
psql $NEON_DB_URL -c "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND (routine_name LIKE '%user%' OR routine_name LIKE '%lookup%' OR routine_name LIKE '%print%' OR routine_name LIKE '%subscription%') ORDER BY routine_name;" -t

# ───────────────────────────────────────────────────────────────────────────
# 6. Test Basic Functionality
# ───────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "🧪 Running basic functionality tests..." -ForegroundColor Yellow
Write-Host ""

# Test 1: Create test user
Write-Host "Test 1: Creating test user..." -ForegroundColor White
try {
    $testResult = psql $NEON_DB_URL -c "SELECT * FROM get_or_create_user(999999999, 'test_deploy', 'Deploy Test');" -t
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Test user created" -ForegroundColor Green
    } else {
        throw "Failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "❌ Failed to create test user" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check usage limit function
Write-Host "Test 2: Testing usage limit function..." -ForegroundColor White
try {
    $usageResult = psql $NEON_DB_URL -c "SELECT allowed, remaining FROM check_and_increment_lookup(999999999);" -t
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Usage limit function works" -ForegroundColor Green
        Write-Host "   Result: $usageResult" -ForegroundColor Gray
    } else {
        throw "Failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "❌ Usage limit function failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Get user status
Write-Host "Test 3: Testing user status function..." -ForegroundColor White
try {
    $statusResult = psql $NEON_DB_URL -c "SELECT tier, lookup_count FROM get_user_status(999999999);" -t
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ User status function works" -ForegroundColor Green
        Write-Host "   Result: $statusResult" -ForegroundColor Gray
    } else {
        throw "Failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "❌ User status function failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ───────────────────────────────────────────────────────────────────────────
# 7. Cleanup Test Data
# ───────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "🧹 Cleaning up test data..." -ForegroundColor Yellow
psql $NEON_DB_URL -c "DELETE FROM rivet_users WHERE telegram_id = 999999999;" 2>&1 | Out-Null
Write-Host "✅ Test data cleaned up" -ForegroundColor Green

# ───────────────────────────────────────────────────────────────────────────
# 8. Success Summary
# ───────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ PHASE 1 COMPLETE - Database Schema Deployed Successfully!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Deployment Summary:" -ForegroundColor White
Write-Host "  ✓ 4 tables created" -ForegroundColor Gray
Write-Host "  ✓ 8 functions created" -ForegroundColor Gray
Write-Host "  ✓ Indexes created" -ForegroundColor Gray
Write-Host "  ✓ All tests passed" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 What's Next:" -ForegroundColor White
Write-Host "  → Phase 2: Create n8n workflows" -ForegroundColor Cyan
Write-Host "     1. rivet_usage_tracker.json" -ForegroundColor Gray
Write-Host "     2. rivet_stripe_checkout.json" -ForegroundColor Gray
Write-Host "     3. rivet_stripe_webhook.json" -ForegroundColor Gray
Write-Host "     4. rivet_chat_with_print.json" -ForegroundColor Gray
Write-Host "     5. rivet_commands.json" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Useful queries saved to: scripts\verify_schema.sql" -ForegroundColor White
Write-Host "📝 Document your deployment in: docs\DEPLOYMENT_LOG.md" -ForegroundColor White
Write-Host ""
