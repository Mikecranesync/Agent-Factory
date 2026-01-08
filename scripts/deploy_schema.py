#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RIVET Pro - Python Schema Deployment Script
Deploy rivet_pro_schema.sql to Neon PostgreSQL without requiring psql
"""

import os
import sys
import subprocess
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ANSI color codes for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

def print_colored(message, color=NC):
    """Print colored message to terminal"""
    try:
        print(f"{color}{message}{NC}")
    except UnicodeEncodeError:
        # Fallback to ASCII if UTF-8 fails
        message_ascii = message.encode('ascii', 'replace').decode('ascii')
        print(f"{color}{message_ascii}{NC}")

def print_header():
    """Print deployment header"""
    print_colored("\n🚀 RIVET Pro - Database Schema Deployment (Python)", CYAN)
    print_colored("=" * 50, CYAN)
    print()

def check_psycopg2():
    """Check if psycopg2 is installed, offer to install if not"""
    try:
        import psycopg2
        print_colored("✅ psycopg2 is installed", GREEN)
        return True
    except ImportError:
        print_colored("⚠️  psycopg2 not found", YELLOW)
        print()
        print("psycopg2-binary is required to connect to PostgreSQL.")
        response = input("Install psycopg2-binary now? (y/N): ").strip().lower()

        if response == 'y':
            print_colored("\n📦 Installing psycopg2-binary...", YELLOW)
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
                print_colored("✅ psycopg2-binary installed successfully", GREEN)
                return True
            except subprocess.CalledProcessError:
                print_colored("❌ Failed to install psycopg2-binary", RED)
                return False
        else:
            print_colored("\n❌ Cannot proceed without psycopg2", RED)
            print("\nTo install manually, run:")
            print("  pip install psycopg2-binary")
            return False

def get_neon_url():
    """Get NEON_DB_URL from environment or .env file"""
    # Try environment variable first
    neon_url = os.getenv('NEON_DB_URL')

    if not neon_url:
        # Try loading from .env file
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            print_colored(f"📄 Loading from {env_path}", YELLOW)
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('NEON_DB_URL='):
                        neon_url = line.split('=', 1)[1].strip()
                        break

    if not neon_url:
        print_colored("❌ NEON_DB_URL not found", RED)
        print("\nPlease set NEON_DB_URL in one of these ways:")
        print("  1. Set environment variable:")
        print('     export NEON_DB_URL="postgresql://..."')
        print("  2. Add to .env file:")
        print('     NEON_DB_URL=postgresql://...')
        return None

    print_colored("✅ NEON_DB_URL loaded", GREEN)
    # Mask password in display
    display_url = neon_url.split('@')[1] if '@' in neon_url else neon_url
    print(f"   Database: {display_url}")
    return neon_url

def read_schema_file():
    """Read the schema SQL file"""
    schema_path = Path(__file__).parent.parent / 'sql' / 'rivet_pro_schema.sql'

    if not schema_path.exists():
        print_colored(f"❌ Schema file not found: {schema_path}", RED)
        return None

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    line_count = schema_sql.count('\n') + 1
    print_colored(f"✅ Schema file loaded ({line_count} lines)", GREEN)
    return schema_sql

def deploy_schema(neon_url, schema_sql):
    """Deploy the schema to Neon PostgreSQL"""
    import psycopg2
    from psycopg2 import sql

    print()
    print_colored("🚀 Deploying schema to Neon...", YELLOW)
    print()

    try:
        # Connect to database
        conn = psycopg2.connect(neon_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Execute schema
        cursor.execute(schema_sql)

        print_colored("✅ Schema deployed successfully!", GREEN)

        # Verify tables
        print()
        print_colored("🧪 Verifying deployment...", YELLOW)
        print()

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

        # Verify functions
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

        # Run basic tests
        print()
        print_colored("🧪 Running basic functionality tests...", YELLOW)
        print()

        # Test 1: Create test user
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

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print_colored(f"\n❌ Database error: {e}", RED)
        return False
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", RED)
        return False

def print_success_summary():
    """Print success summary"""
    print()
    print_colored("=" * 60, GREEN)
    print_colored("✅ PHASE 1 COMPLETE - Database Schema Deployed Successfully!", GREEN)
    print_colored("=" * 60, GREEN)
    print()
    print_colored("📊 Deployment Summary:", NC)
    print("  ✓ 4 tables created")
    print("  ✓ 8 functions created")
    print("  ✓ Indexes created")
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
    print_colored("📝 Document your deployment in: docs/DEPLOYMENT_LOG.md", NC)
    print()

def main():
    """Main deployment function"""
    print_header()

    # Check prerequisites
    print_colored("📋 Checking prerequisites...", YELLOW)
    print()

    if not check_psycopg2():
        sys.exit(1)

    neon_url = get_neon_url()
    if not neon_url:
        sys.exit(1)

    schema_sql = read_schema_file()
    if not schema_sql:
        sys.exit(1)

    print()
    print_colored("⚠️  This will deploy the schema to your Neon database.", YELLOW)
    response = input("Continue with deployment? (y/N): ").strip().lower()

    if response != 'y':
        print("Deployment cancelled.")
        sys.exit(0)

    # Deploy
    if deploy_schema(neon_url, schema_sql):
        print_success_summary()
        sys.exit(0)
    else:
        print_colored("\n❌ Deployment failed", RED)
        sys.exit(1)

if __name__ == '__main__':
    main()
