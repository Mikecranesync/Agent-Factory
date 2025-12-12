#!/usr/bin/env python3
"""
Verify Citations Column - Check if citations JSONB field exists in Supabase

Usage:
    poetry run python scripts/verify_citations_column.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

try:
    from supabase import create_client, Client
except ImportError:
    print("[ERROR] supabase package not installed")
    print("        Run: poetry add supabase")
    exit(1)

def verify_citations_column():
    """Check if citations column exists in knowledge_atoms table."""

    print("=" * 70)
    print("VERIFYING CITATIONS COLUMN IN SUPABASE")
    print("=" * 70)
    print()

    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("[ERROR] Missing Supabase credentials in .env")
        print("        Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        return False

    print(f"Connecting to: {url}")
    print()

    # Create client
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        return False

    # Try to query knowledge_atoms table with citations column
    print("[1/3] Checking if knowledge_atoms table exists...")
    try:
        result = supabase.table('knowledge_atoms').select('atom_id').limit(1).execute()
        print("      [OK] knowledge_atoms table exists")
        print()
    except Exception as e:
        print(f"      [X] Table not found: {e}")
        print()
        print("ACTION REQUIRED:")
        print("  1. Open Supabase SQL Editor:")
        print(f"     https://supabase.com/dashboard/project/{url.split('//')[1].split('.')[0]}/sql/new")
        print("  2. Copy/paste: docs/supabase_complete_schema.sql")
        print("  3. Click 'Run'")
        print()
        return False

    # Try to select citations column
    print("[2/3] Checking if citations column exists...")
    try:
        result = supabase.table('knowledge_atoms').select('atom_id,citations').limit(1).execute()
        print("      [OK] citations column exists")
        print()

        # Check if any atoms have citations
        if result.data:
            atom = result.data[0]
            if atom.get('citations'):
                print(f"      Sample citations: {atom['citations'][:100]}...")
            else:
                print("      (No atoms with citations yet)")
        else:
            print("      (No atoms in database yet)")
        print()

    except Exception as e:
        error_msg = str(e)
        if 'column "citations" does not exist' in error_msg.lower():
            print("      [X] citations column NOT FOUND")
            print()
            print("ACTION REQUIRED:")
            print("  The schema needs to be updated to include the citations column.")
            print()
            print("  Option 1: Run full schema (recommended)")
            print("    1. Open Supabase SQL Editor")
            print("    2. Copy/paste: docs/supabase_complete_schema.sql")
            print("    3. Click 'Run'")
            print()
            print("  Option 2: Add column only (if table exists)")
            print("    Run this SQL:")
            print("    ALTER TABLE knowledge_atoms")
            print("    ADD COLUMN IF NOT EXISTS citations JSONB DEFAULT '[]'::jsonb;")
            print()
            return False
        else:
            print(f"      [X] Error: {e}")
            return False

    # Try to insert a test citation
    print("[3/3] Testing citation insert...")
    test_atom = {
        'atom_id': 'test:verify:citations',
        'atom_type': 'concept',
        'title': 'Test Citation Verification',
        'summary': 'Testing citations JSONB field',
        'content': 'This is a test atom to verify citations column works',
        'manufacturer': 'test',
        'difficulty': 'beginner',
        'source_document': 'test.pdf',
        'source_pages': [1],
        'citations': [
            {
                'id': 1,
                'url': 'https://example.com/test',
                'title': 'Test Source',
                'accessed_at': '2025-12-12T00:00:00Z'
            }
        ]
    }

    try:
        # Delete test atom if exists
        supabase.table('knowledge_atoms').delete().eq('atom_id', 'test:verify:citations').execute()

        # Insert test atom
        result = supabase.table('knowledge_atoms').insert(test_atom).execute()
        print("      [OK] Successfully inserted atom with citations")
        print()

        # Verify citations were stored correctly
        result = supabase.table('knowledge_atoms').select('citations').eq('atom_id', 'test:verify:citations').execute()
        if result.data and result.data[0]['citations']:
            citations = result.data[0]['citations']
            print(f"      Stored citations: {citations}")
            print()

            # Clean up test atom
            supabase.table('knowledge_atoms').delete().eq('atom_id', 'test:verify:citations').execute()
            print("      [OK] Test atom cleaned up")
            print()

    except Exception as e:
        print(f"      [X] Insert failed: {e}")
        print()
        return False

    print("=" * 70)
    print("[SUCCESS] Citations column is working correctly!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Upload atoms with citations:")
    print("     poetry run python scripts/upload_atoms_to_supabase.py")
    print()
    print("  2. Test citation parsing:")
    print("     poetry run python examples/perplexity_citation_demo.py")
    print()

    return True


if __name__ == "__main__":
    success = verify_citations_column()
    exit(0 if success else 1)
