#!/usr/bin/env python3
"""
Deploy Knowledge Atoms Schema to Supabase

Executes the production schema with pgvector support.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase package not installed")
    print("Run: poetry add supabase")
    sys.exit(1)

def deploy_schema():
    """Deploy the knowledge atoms schema to Supabase."""

    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Missing Supabase credentials")
        print("Need: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        sys.exit(1)

    print("=" * 80)
    print("DEPLOYING KNOWLEDGE ATOMS SCHEMA TO SUPABASE")
    print("=" * 80)
    print()

    # Connect
    try:
        supabase = create_client(url, key)
        print(f"Connected to: {url}")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        sys.exit(1)

    # Read schema file
    schema_file = Path("docs/supabase_knowledge_schema.sql")
    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        sys.exit(1)

    schema_sql = schema_file.read_text()

    print(f"Loaded schema: {len(schema_sql)} chars")
    print()

    # Execute schema
    print("Deploying schema...")
    print("This will create:")
    print("  - pgvector extension")
    print("  - knowledge_atoms table")
    print("  - HNSW vector index")
    print("  - 3 search functions")
    print("  - 8 indexes")
    print()

    try:
        # Note: Supabase Python client doesn't support raw SQL execution
        # User needs to paste this into Supabase SQL Editor
        print("=" * 80)
        print("MANUAL DEPLOYMENT REQUIRED")
        print("=" * 80)
        print()
        print("The Supabase Python client cannot execute raw SQL.")
        print("You need to manually deploy this schema:")
        print()
        print("1. Open Supabase SQL Editor:")
        print(f"   {url.replace('https://', 'https://app.')}/sql/new")
        print()
        print("2. Copy/paste this file:")
        print(f"   {schema_file.absolute()}")
        print()
        print("3. Click 'Run' to execute")
        print()
        print("4. Verify deployment:")
        print("   Run: poetry run python scripts/verify_supabase_schema.py")
        print()
        print("=" * 80)
        print()

        # Show schema preview
        print("SCHEMA PREVIEW (first 50 lines):")
        print("-" * 80)
        lines = schema_sql.split('\n')[:50]
        print('\n'.join(lines))
        print("...")
        print("-" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_schema()
