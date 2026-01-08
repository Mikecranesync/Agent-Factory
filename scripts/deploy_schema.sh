#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# RIVET Pro - Database Schema Deployment Script
# Deploy rivet_pro_schema.sql to Neon PostgreSQL
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 RIVET Pro - Database Schema Deployment${NC}"
echo "=========================================="
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 1. Check Prerequisites
# ───────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if NEON_DB_URL is set
if [ -z "$NEON_DB_URL" ]; then
    echo -e "${RED}❌ Error: NEON_DB_URL environment variable not set${NC}"
    echo ""
    echo "Please set it with:"
    echo "  export NEON_DB_URL='postgresql://user:password@host.neon.tech/database?sslmode=require'"
    echo ""
    echo "Get your connection string from:"
    echo "  https://console.neon.tech → Your Project → Connection Details"
    exit 1
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ Error: psql (PostgreSQL client) is not installed${NC}"
    echo ""
    echo "Install instructions:"
    echo "  macOS:   brew install postgresql"
    echo "  Ubuntu:  sudo apt install postgresql-client"
    echo "  Windows: Use PowerShell script (deploy_schema.ps1) or install from https://www.postgresql.org/download/"
    exit 1
fi

# Check if schema file exists
SCHEMA_FILE="sql/rivet_pro_schema.sql"
if [ ! -f "$SCHEMA_FILE" ]; then
    echo -e "${RED}❌ Error: Schema file not found at $SCHEMA_FILE${NC}"
    echo "Make sure you're running this from the rivet-test root directory"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 2. Display Schema Info
# ───────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}📦 Schema Information:${NC}"
echo "  File: $SCHEMA_FILE"
echo "  Size: $(wc -l < $SCHEMA_FILE) lines"
echo ""
echo "  Tables to create:"
echo "    - rivet_users (user management + Stripe integration)"
echo "    - rivet_usage_log (analytics tracking)"
echo "    - rivet_print_sessions (Chat with Print-it feature)"
echo "    - rivet_stripe_events (webhook event logging)"
echo ""
echo "  Functions to create:"
echo "    - get_or_create_user()"
echo "    - check_and_increment_lookup()"
echo "    - update_subscription()"
echo "    - get_user_status()"
echo "    - start_print_session()"
echo "    - get_active_print_session()"
echo "    - add_print_message()"
echo "    - end_print_session()"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 3. Confirm Deployment
# ───────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}⚠️  This will deploy the schema to your Neon database.${NC}"
echo "   Database: $(echo $NEON_DB_URL | sed 's/postgresql:\/\/\([^:]*\):\([^@]*\)@\(.*\)/\3/')"
echo ""
read -p "Continue with deployment? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# ───────────────────────────────────────────────────────────────────────────
# 4. Deploy Schema
# ───────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${YELLOW}🚀 Deploying schema to Neon...${NC}"
echo ""

if psql "$NEON_DB_URL" -f "$SCHEMA_FILE"; then
    echo ""
    echo -e "${GREEN}✅ Schema deployed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Schema deployment failed${NC}"
    echo "Check the error messages above for details"
    exit 1
fi

# ───────────────────────────────────────────────────────────────────────────
# 5. Verify Deployment
# ───────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${YELLOW}🧪 Verifying deployment...${NC}"
echo ""

# Check tables
echo "📊 Tables created:"
psql "$NEON_DB_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'rivet_%' ORDER BY table_name;" -t

# Check functions
echo ""
echo "⚙️  Functions created:"
psql "$NEON_DB_URL" -c "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name LIKE '%user%' OR routine_name LIKE '%lookup%' OR routine_name LIKE '%print%' OR routine_name LIKE '%subscription%' ORDER BY routine_name;" -t

# ───────────────────────────────────────────────────────────────────────────
# 6. Test Basic Functionality
# ───────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${YELLOW}🧪 Running basic functionality tests...${NC}"
echo ""

# Test 1: Create test user
echo "Test 1: Creating test user..."
TEST_RESULT=$(psql "$NEON_DB_URL" -c "SELECT * FROM get_or_create_user(999999999, 'test_deploy', 'Deploy Test');" -t)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test user created${NC}"
else
    echo -e "${RED}❌ Failed to create test user${NC}"
    exit 1
fi

# Test 2: Check usage limit function
echo "Test 2: Testing usage limit function..."
USAGE_RESULT=$(psql "$NEON_DB_URL" -c "SELECT allowed, remaining FROM check_and_increment_lookup(999999999);" -t)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Usage limit function works${NC}"
    echo "   Result: $USAGE_RESULT"
else
    echo -e "${RED}❌ Usage limit function failed${NC}"
    exit 1
fi

# Test 3: Get user status
echo "Test 3: Testing user status function..."
STATUS_RESULT=$(psql "$NEON_DB_URL" -c "SELECT tier, lookup_count FROM get_user_status(999999999);" -t)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ User status function works${NC}"
    echo "   Result: $STATUS_RESULT"
else
    echo -e "${RED}❌ User status function failed${NC}"
    exit 1
fi

# ───────────────────────────────────────────────────────────────────────────
# 7. Cleanup Test Data
# ───────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${YELLOW}🧹 Cleaning up test data...${NC}"
psql "$NEON_DB_URL" -c "DELETE FROM rivet_users WHERE telegram_id = 999999999;" > /dev/null 2>&1
echo -e "${GREEN}✅ Test data cleaned up${NC}"

# ───────────────────────────────────────────────────────────────────────────
# 8. Success Summary
# ───────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ PHASE 1 COMPLETE - Database Schema Deployed Successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📊 Deployment Summary:"
echo "  ✓ 4 tables created"
echo "  ✓ 8 functions created"
echo "  ✓ Indexes created"
echo "  ✓ All tests passed"
echo ""
echo "🎯 What's Next:"
echo "  → Phase 2: Create n8n workflows"
echo "     1. rivet_usage_tracker.json"
echo "     2. rivet_stripe_checkout.json"
echo "     3. rivet_stripe_webhook.json"
echo "     4. rivet_chat_with_print.json"
echo "     5. rivet_commands.json"
echo ""
echo "📚 Useful queries saved to: scripts/verify_schema.sql"
echo "📝 Document your deployment in: docs/DEPLOYMENT_LOG.md"
echo ""
