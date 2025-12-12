#!/usr/bin/env python3
"""Verify knowledge base is live in Supabase"""
import os, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing
try:
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    # Try SERVICE_ROLE_KEY first, then KEY
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY in .env")
        sys.exit(1)

    supabase = create_client(url, key)

    # Query atoms with count
    response = supabase.table("knowledge_atoms").select("atom_id, atom_type, manufacturer", count="exact").limit(10).execute()

    print("\n" + "="*80)
    print("KNOWLEDGE BASE STATUS")
    print("="*80)
    print(f"\nConnected to: {url}")
    print(f"Total atoms in database: {response.count}")
    print(f"\nSample atoms (first 10):")
    for atom in response.data:
        print(f"   - {atom['atom_id'][:50]:<50} | {atom.get('manufacturer', 'unknown')}")
    print("\n" + "="*80)
    print("KNOWLEDGE BASE IS LIVE!")
    print("="*80 + "\n")

except Exception as e:
    print(f"\nERROR: {e}\n")
    print("The atoms may still be in the database, but credentials need checking.")
    sys.exit(1)
