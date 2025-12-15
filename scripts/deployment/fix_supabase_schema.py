#!/usr/bin/env python3
"""
Fix Supabase Schema - Generate Clean Schema SQL

This script:
1. Generates a SQL file with DROP + CREATE statements
2. Provides instructions to execute in Supabase SQL Editor
3. Verifies deployment after execution

Usage:
    poetry run python scripts/deployment/fix_supabase_schema.py

Safety:
    - Only drops Agent Factory tables (agent_messages, knowledge_atoms, etc.)
    - Does NOT touch other database tables
    - You manually control when SQL is executed (via SQL Editor)

Created: 2025-12-15
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment
env_path = project_root / ".env"
load_dotenv(env_path)


def generate_fix_sql():
    """Generate SQL file with DROP + CREATE statements."""

    print("=" * 80)
    print("FIX SUPABASE SCHEMA - GENERATE CLEAN SCHEMA SQL")
    print("=" * 80)
    print()

    # Load original schema
    schema_file = project_root / "docs" / "database" / "supabase_complete_schema.sql"

    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        sys.exit(1)

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Generate DROP statements
    drop_sql = """-- ============================================================================
-- DROP OLD TABLES (Clean Slate)
-- ============================================================================
-- This fixes the "column agent_name does not exist" error by dropping
-- old tables before recreating them with the correct schema.
-- ============================================================================

DROP TABLE IF EXISTS knowledge_atoms CASCADE;
DROP TABLE IF EXISTS research_staging CASCADE;
DROP TABLE IF EXISTS video_scripts CASCADE;
DROP TABLE IF EXISTS upload_jobs CASCADE;
DROP TABLE IF EXISTS agent_messages CASCADE;
DROP TABLE IF EXISTS session_memories CASCADE;
DROP TABLE IF EXISTS settings CASCADE;

-- ============================================================================
-- NOW CREATE TABLES WITH CORRECT SCHEMA
-- ============================================================================

"""

    # Combine DROP + CREATE
    combined_sql = drop_sql + schema_sql

    # Save to file
    output_file = project_root / "scripts" / "deployment" / "supabase_fix_schema.sql"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_sql)

    print(f"[OK] Generated SQL file: {output_file.name}")
    print()
    print("=" * 80)
    print("NEXT STEPS - MANUAL EXECUTION REQUIRED")
    print("=" * 80)
    print()
    print("1. Open Supabase Dashboard:")
    print(f"   {os.getenv('SUPABASE_URL')}")
    print()
    print("2. Go to: SQL Editor")
    print()
    print("3. Create New Query")
    print()
    print("4. Copy and paste the contents of this file:")
    print(f"   scripts/deployment/supabase_fix_schema.sql")
    print()
    print("5. Click 'Run' (or press Ctrl+Enter)")
    print()
    print("6. You should see:")
    print("   - DROP TABLE statements executed (7 tables)")
    print("   - CREATE TABLE statements executed (7 tables)")
    print("   - Sample settings inserted")
    print()
    print("7. Verify by running this command:")
    print("   poetry run python scripts/deployment/verify_supabase_schema.py")
    print()
    print("=" * 80)
    print()

    # Open file for easy copy-paste
    print(f"SQL file location: {output_file.resolve()}")
    print()
    print("TIP: Open the file in a text editor, select all (Ctrl+A), copy (Ctrl+C)")
    print()


def verify_schema():
    """Verify schema is deployed correctly."""

    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed")
        print("Run: poetry add supabase")
        return False

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("ERROR: Missing Supabase credentials")
        return False

    print("=" * 80)
    print("VERIFYING SCHEMA DEPLOYMENT")
    print("=" * 80)
    print()

    try:
        client = create_client(url, key)
        print(f"[OK] Connected to: {url}")
        print()
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return False

    # Test knowledge_atoms table
    print("Testing knowledge_atoms table...")
    try:
        result = client.table("knowledge_atoms").select("count").limit(1).execute()
        print("  [OK] Table exists and is accessible")
    except Exception as e:
        print(f"  [FAIL] Table not accessible: {e}")
        return False

    # Test agent_messages table (the one that had issues)
    print()
    print("Testing agent_messages table...")
    try:
        result = client.table("agent_messages").select("*").limit(1).execute()
        print("  [OK] Table exists and is accessible")
        print("  [OK] Schema is correctly deployed!")
    except Exception as e:
        print(f"  [FAIL] Table not accessible: {e}")
        print()
        print("  Please run the SQL file in Supabase SQL Editor first.")
        return False

    print()
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("Schema is ready! Next step:")
    print("  poetry run python scripts/knowledge/upload_atoms_to_supabase.py")
    print()

    return True


def main():
    """Main execution."""

    import argparse

    parser = argparse.ArgumentParser(description="Fix Supabase schema")
    parser.add_argument("--verify", action="store_true",
                       help="Verify schema after manual SQL execution")
    args = parser.parse_args()

    if args.verify:
        # Verify schema
        success = verify_schema()
        sys.exit(0 if success else 1)
    else:
        # Generate SQL file
        generate_fix_sql()


if __name__ == "__main__":
    main()
