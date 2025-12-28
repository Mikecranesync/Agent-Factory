#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# RIVET CMMS - Public Launch Deployment Script
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "RIVET CMMS - PUBLIC LAUNCH DEPLOYMENT"
echo "═══════════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Check prerequisites
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "Step 1: Checking prerequisites..."

if [ -z "$NEON_DB_URL" ]; then
    echo "❌ NEON_DB_URL not set. Please run: source .env"
    exit 1
fi

if [ -z "$PUBLIC_TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  PUBLIC_TELEGRAM_BOT_TOKEN not set."
    echo "   Have you created the new bot with @BotFather?"
    echo "   See: migrations/public_launch/SETUP_GUIDE.md"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Prerequisites checked"

# ─────────────────────────────────────────────────────────────────────────────
# 2. Run database migration
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "Step 2: Running database migration..."

psql "$NEON_DB_URL" -f migrations/public_launch/001_public_ready_schema.sql

echo "✓ Database migration complete"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Test the public bot locally
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "Step 3: Testing public bot..."

python -c "
from agent_factory.integrations.telegram.public_auth import auth
print('  ✓ public_auth module loads')

# Check admin table
if auth.is_admin(8445149012):
    print('  ✓ You are registered as admin')
else:
    print('  ⚠️  Admin registration may have failed')
"

echo "✓ Module tests passed"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Summary
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "DEPLOYMENT READY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Create bot with @BotFather (if not done):"
echo "   /newbot → 'Rivet CMMS' → '@RivetCMMS_bot'"
echo ""
echo "2. Add token to .env.production:"
echo "   PUBLIC_TELEGRAM_BOT_TOKEN=your_token_here"
echo ""
echo "3. Start the public bot:"
echo "   python rivet_public_bot.py"
echo ""
echo "4. Or deploy to VPS:"
echo "   scp rivet_public_bot.py root@72.60.175.144:/opt/rivet/"
echo "   ssh root@72.60.175.144 'cd /opt/rivet && python rivet_public_bot.py'"
echo ""
echo "═══════════════════════════════════════════════════════════════"
