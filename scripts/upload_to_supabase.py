#!/usr/bin/env python3
"""
Upload Knowledge Atoms to Supabase - PRODUCTION

Uploads all generated atoms to Supabase knowledge_atoms table.
Includes embeddings for vector search.

Run this after atoms are generated.

Usage:
    poetry run python scripts/upload_to_supabase.py
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase package not installed")
    print("Run: poetry add supabase")
    sys.exit(1)


def upload_atoms():
    """Upload all atoms to Supabase."""

    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    # Connect to Supabase
    supabase = create_client(url, key)

    # Find all atom files
    atoms_dir = Path("data/atoms")
    if not atoms_dir.exists():
        print(f"ERROR: {atoms_dir} does not exist")
        print("Run atom builder first")
        sys.exit(1)

    atom_files = list(atoms_dir.glob("**/*.json"))

    print(f"Found {len(atom_files)} atom files")
    print("Uploading to Supabase...")

    uploaded = 0
    failed = 0

    for atom_file in atom_files:
        try:
            with open(atom_file, "r") as f:
                atom = json.load(f)

            # Upload to knowledge_atoms table
            supabase.table("knowledge_atoms").upsert(atom).execute()

            uploaded += 1

            if uploaded % 100 == 0:
                print(f"  Uploaded {uploaded}/{len(atom_files)}...")

        except Exception as e:
            print(f"  FAILED: {atom_file.name} - {e}")
            failed += 1

    print(f"\nDONE")
    print(f"  Uploaded: {uploaded}")
    print(f"  Failed: {failed}")


if __name__ == "__main__":
    upload_atoms()
