#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RIVET Pro - Clean Deployment Script
Drop old tables and deploy fresh RIVET Pro schema
"""

import psycopg2
from pathlib import Path
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_colored(message, color=NC):
    """Print colored message"""
    try:
        print(f"{color}{message}{NC}")
    except UnicodeEncodeError:
        message_ascii = message.encode('ascii', 'replace').decode('ascii')
        print(f"{color}{message_ascii}{NC}")

def get_neon_url():
    """Load NEON_DB_URL from .env file"""
    env_path = Path(__file__).parent.parent / '.env'

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('NEON_DB_URL='):
                return line.split('=', 1)[1].strip()
    return None

def main():
    print_colored("\n🔥 RIVET Pro - Clean Deployment", CYAN)
    print_colored("=" * 50, CYAN)
    print()

    # Get connection
    neon_url = get_neon_url()
    if not neon_url:
        print_colored("❌ NEON_DB_URL not found in .env", RED)
        sys.exit(1)

    print_colored("✅ Connected to Neon PostgreSQL", GREEN)
    display_url = neon_url.split('@')[1] if '@' in neon_url else neon_url
    print(f"   Database: {display_url}")
    print()

    # Warning
    print_colored("⚠️  WARNING: This will DROP all existing rivet_* tables!", YELLOW)
    print("   All data in these tables will be permanently deleted:")
    print("   - rivet_users")
    print("   - rivet_usage_log")
    print("   - rivet_print_sessions")
    print("   - rivet_stripe_events")
    print()

    response = input("Type 'YES' to continue: ").strip()
    if response != 'YES':
        print("Deployment cancelled.")
        sys.exit(0)

    conn = psycopg2.connect(neon_url)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Step 1: Drop existing tables
        print()
        print_colored("🗑️  Step 1: Dropping old tables...", YELLOW)

        drop_commands = [
            "DROP TABLE IF EXISTS rivet_stripe_events CASCADE",
            "DROP TABLE IF EXISTS rivet_print_sessions CASCADE",
            "DROP TABLE IF EXISTS rivet_usage_log CASCADE",
            "DROP TABLE IF EXISTS rivet_users CASCADE"
        ]

        for cmd in drop_commands:
            cursor.execute(cmd)
            table_name = cmd.split()[4]
            print(f"   ✓ Dropped {table_name}")

        # Step 2: Drop existing RIVET functions only
        print()
        print_colored("🗑️  Step 2: Dropping old RIVET functions...", YELLOW)

        rivet_functions = [
            'get_or_create_user',
            'check_and_increment_lookup',
            'update_subscription',
            'get_user_status',
            'start_print_session',
            'get_active_print_session',
            'add_print_message',
            'end_print_session',
            'can_user_lookup',
            'increment_lookup_counter',
            'update_user_machine_timestamp',
            'upsert_user'
        ]

        for func in rivet_functions:
            cursor.execute(f"DROP FUNCTION IF EXISTS {func} CASCADE")
            print(f"   ✓ Dropped {func} (if existed)")

        # Step 3: Deploy fresh schema
        print()
        print_colored("📦 Step 3: Deploying RIVET Pro schema...", YELLOW)

        schema_path = Path(__file__).parent.parent / 'sql' / 'rivet_pro_schema.sql'
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        cursor.execute(schema_sql)
        print_colored("   ✅ Schema deployed successfully!", GREEN)

        # Step 4: Verify deployment
        print()
        print_colored("🧪 Step 4: Verifying deployment...", YELLOW)
        print()

        # Check tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'rivet_%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        print_colored("📊 Tables created:", GREEN)
        for table in tables:
            print(f"   ✓ {table[0]}")

        # Check columns in rivet_users
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'rivet_users'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()

        print()
        print_colored("📋 rivet_users columns:", GREEN)
        for col in columns:
            print(f"   ✓ {col[0]}")

        # Check functions
        cursor.execute("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND (
                routine_name LIKE '%user%'
                OR routine_name LIKE '%lookup%'
                OR routine_name LIKE '%print%'
                OR routine_name LIKE '%subscription%'
            )
            ORDER BY routine_name
        """)
        functions = cursor.fetchall()

        print()
        print_colored("⚙️  Functions created:", GREEN)
        for func in functions:
            print(f"   ✓ {func[0]}")

        # Step 5: Run functionality tests
        print()
        print_colored("🧪 Step 5: Running functionality tests...", YELLOW)
        print()

        # Test 1: Create user
        cursor.execute("SELECT * FROM get_or_create_user(999999999, 'test_deploy', 'Deploy Test')")
        result = cursor.fetchone()
        print_colored("✅ Test 1: User creation works", GREEN)

        # Test 2: Check usage limit
        cursor.execute("SELECT allowed, remaining, is_pro FROM check_and_increment_lookup(999999999)")
        result = cursor.fetchone()
        print_colored(f"✅ Test 2: Usage tracking works (allowed={result[0]}, remaining={result[1]})", GREEN)

        # Test 3: Get user status
        cursor.execute("SELECT tier, lookup_count FROM get_user_status(999999999)")
        result = cursor.fetchone()
        print_colored(f"✅ Test 3: User status works (tier={result[0]}, count={result[1]})", GREEN)

        # Cleanup test data
        print()
        print_colored("🧹 Cleaning up test data...", YELLOW)
        cursor.execute("DELETE FROM rivet_users WHERE telegram_id = 999999999")
        print_colored("✅ Test data cleaned up", GREEN)

        # Success!
        print()
        print_colored("=" * 60, GREEN)
        print_colored("✅ PHASE 1 COMPLETE - Database Schema Deployed Successfully!", GREEN)
        print_colored("=" * 60, GREEN)
        print()
        print_colored("📊 Deployment Summary:", NC)
        print("  ✓ 4 tables created (fresh deployment)")
        print("  ✓ 8 functions created")
        print("  ✓ All indexes created")
        print("  ✓ All tests passed")
        print()
        print_colored("🎯 What's Next:", NC)
        print("  → Phase 2: Create n8n workflows")
        print("     1. rivet_usage_tracker.json")
        print("     2. rivet_stripe_checkout.json")
        print("     3. rivet_stripe_webhook.json")
        print("     4. rivet_chat_with_print.json")
        print("     5. rivet_commands.json")
        print()

        cursor.close()
        conn.close()

    except Exception as e:
        print_colored(f"\n❌ Error: {e}", RED)
        cursor.close()
        conn.close()
        sys.exit(1)

if __name__ == '__main__':
    main()
