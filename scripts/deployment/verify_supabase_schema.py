#!/usr/bin/env python3
"""
Verify Supabase Knowledge Schema Deployment

Tests if knowledge_atoms table exists with proper structure.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase package not installed")
    sys.exit(1)

def verify_schema():
    """Verify the schema is properly deployed."""

    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Missing Supabase credentials")
        sys.exit(1)

    print("=" * 80)
    print("VERIFYING SUPABASE KNOWLEDGE SCHEMA")
    print("=" * 80)
    print()

    # Connect
    try:
        supabase = create_client(url, key)
        print(f"[OK] Connected to: {url}")
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        sys.exit(1)

    # Test 1: Table exists
    print()
    print("Test 1: knowledge_atoms table exists")
    try:
        result = supabase.table("knowledge_atoms").select("count").limit(1).execute()
        print("  [OK] Table exists")
    except Exception as e:
        print(f"  [FAIL] Table not found: {e}")
        print()
        print("ACTION REQUIRED:")
        print("  Deploy the schema using Supabase SQL Editor")
        print("  File: docs/supabase_knowledge_schema.sql")
        sys.exit(1)

    # Test 2: Insert test atom
    print()
    print("Test 2: Insert test atom")
    test_atom = {
        "atom_id": "test:verification:schema-test",
        "atom_type": "concept",
        "title": "Test Atom for Schema Verification",
        "summary": "This is a test atom to verify the schema is working",
        "content": "Test content " * 50,  # ~100 words
        "manufacturer": "test",
        "difficulty": "beginner",
        "source_document": "test.pdf",
        "source_pages": [1],
        "keywords": ["test", "verification"],
        "embedding": [0.1] * 1536  # Dummy embedding
    }

    try:
        supabase.table("knowledge_atoms").insert(test_atom).execute()
        print("  [OK] Insert succeeded")
    except Exception as e:
        print(f"  [FAIL] Insert failed: {e}")
        sys.exit(1)

    # Test 3: Query test atom
    print()
    print("Test 3: Query test atom")
    try:
        result = supabase.table("knowledge_atoms")\
            .select("atom_id, title")\
            .eq("atom_id", "test:verification:schema-test")\
            .execute()

        if result.data and len(result.data) > 0:
            print(f"  [OK] Query succeeded: {result.data[0]['title']}")
        else:
            print("  [FAIL] No data returned")
            sys.exit(1)
    except Exception as e:
        print(f"  [FAIL] Query failed: {e}")
        sys.exit(1)

    # Test 4: Count total atoms
    print()
    print("Test 4: Count existing atoms")
    try:
        result = supabase.table("knowledge_atoms").select("atom_id", count="exact").execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"  [OK] Total atoms in database: {count}")
    except Exception as e:
        print(f"  [FAIL] Count failed: {e}")

    # Test 5: Delete test atom
    print()
    print("Test 5: Cleanup test atom")
    try:
        supabase.table("knowledge_atoms")\
            .delete()\
            .eq("atom_id", "test:verification:schema-test")\
            .execute()
        print("  [OK] Cleanup succeeded")
    except Exception as e:
        print(f"  [WARN] Cleanup failed: {e}")

    # Summary
    print()
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("Schema is properly deployed and functional!")
    print()
    print("Next step:")
    print("  Upload atoms: poetry run python scripts/FULL_AUTO_KB_BUILD.py")
    print()

if __name__ == "__main__":
    verify_schema()
