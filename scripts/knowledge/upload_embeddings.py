#!/usr/bin/env python3
"""
Upload knowledge atoms with embeddings to Supabase.

Usage:
    poetry run python scripts/knowledge/upload_embeddings.py \
        --input data/atoms-with-embeddings.json
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

# Load environment
load_dotenv()


def load_atoms(input_path: Path) -> List[Dict[str, Any]]:
    """Load atoms from JSON file."""
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)
        # Handle both raw list and wrapped structure with metadata
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'atoms' in data:
            return data['atoms']
        else:
            raise ValueError("Invalid JSON structure: expected list or dict with 'atoms' key")


def prepare_atom_for_db(atom: Dict[str, Any]) -> Dict[str, Any]:
    """Convert atom structure to database schema."""
    # Include code_example in content if it exists
    content = atom.get('content', '')
    if atom.get('code_example'):
        content += f"\n\n**Code Example:**\n{atom['code_example']}"

    # Handle source_pages - convert to array if needed
    source_pages = atom.get('source_pages', [])
    if isinstance(source_pages, str):
        source_pages = [source_pages] if source_pages else []

    # Map difficulty values (moderate -> intermediate)
    difficulty = atom.get('difficulty', 'intermediate')
    if difficulty == 'moderate':
        difficulty = 'intermediate'

    # Map atom_type to allowed values (concept, procedure, specification)
    atom_type = atom.get('atom_type') or atom.get('type')
    type_mapping = {
        'pattern': 'procedure',
        'best-practice': 'concept',
        'fault': 'procedure',
        'concept': 'concept',
        'procedure': 'procedure',
        'specification': 'specification'
    }
    atom_type = type_mapping.get(atom_type, 'concept')

    return {
        'atom_id': atom.get('atom_id'),
        'atom_type': atom_type,
        'title': atom.get('title'),
        'summary': atom.get('summary'),
        'content': content,
        'manufacturer': atom.get('vendor', 'agent-factory'),
        'product_family': atom.get('equipment_type', 'pattern'),
        'source_document': atom.get('source_document', ''),
        'source_pages': source_pages,
        'difficulty': difficulty,
        'prerequisites': atom.get('prereqs', []),
        'keywords': atom.get('keywords', []),
        'embedding': atom.get('embedding')
    }


def upload_atoms_batch(client, atoms: List[Dict[str, Any]], batch_size: int = 50):
    """Upload atoms in batches with progress tracking."""

    total = len(atoms)
    uploaded = 0
    failed = 0
    skipped = 0

    print(f"\nUploading {total} atoms in batches of {batch_size}...")
    print("=" * 70)

    for i in tqdm(range(0, total, batch_size), desc="Upload progress"):
        batch = atoms[i:i + batch_size]

        try:
            # Try batch insert
            result = client.table('knowledge_atoms').insert(batch).execute()
            uploaded += len(batch)

        except Exception as e:
            error_msg = str(e)

            # If batch fails due to duplicates, try one-by-one
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                print(f"\n[INFO] Batch {i//batch_size + 1}: Duplicates detected, uploading individually...")

                for atom in batch:
                    try:
                        client.table('knowledge_atoms').insert(atom).execute()
                        uploaded += 1
                    except Exception as e2:
                        if 'duplicate' in str(e2).lower() or 'unique' in str(e2).lower():
                            skipped += 1
                        else:
                            failed += 1
                            print(f"\n[ERROR] Failed to upload {atom.get('atom_id', 'unknown')}: {e2}")
            else:
                failed += len(batch)
                print(f"\n[ERROR] Batch {i//batch_size + 1} failed: {e}")

    print("\n" + "=" * 70)
    print("UPLOAD COMPLETE")
    print("=" * 70)
    print(f"Total atoms:    {total}")
    print(f"Uploaded:       {uploaded}")
    print(f"Skipped (dup):  {skipped}")
    print(f"Failed:         {failed}")
    print("=" * 70)

    return uploaded, skipped, failed


def verify_upload(client, expected_count: int):
    """Verify atoms were uploaded successfully."""
    print("\nVerifying upload...")

    try:
        result = client.table('knowledge_atoms').select('atom_id', count='exact').execute()
        actual_count = result.count

        print(f"Expected: {expected_count}")
        print(f"Actual:   {actual_count}")

        if actual_count >= expected_count:
            print("[SUCCESS] All atoms uploaded successfully!")
        else:
            print(f"[WARNING] Missing {expected_count - actual_count} atoms")

        # Show sample atoms
        sample = client.table('knowledge_atoms').select('atom_id, title').limit(5).execute()
        print("\nSample atoms:")
        for atom in sample.data:
            print(f"  - {atom['atom_id']}: {atom['title']}")

        return actual_count

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Upload atoms with embeddings to Supabase")
    parser.add_argument("--input", default="data/atoms-with-embeddings.json", help="Input JSON file")
    args = parser.parse_args()

    print("=" * 70)
    print("KNOWLEDGE ATOMS -> SUPABASE UPLOAD")
    print("=" * 70)

    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("\n[ERROR] Missing Supabase credentials in .env")
        print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        return False

    print(f"\nURL: {url}")
    print(f"Key: ***{key[-10:]}")

    # Connect to Supabase
    try:
        client = create_client(url, key)
        print("[OK] Connected to Supabase\n")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    # Load atoms
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return False

    print(f"Loading atoms from: {input_path}")
    atoms = load_atoms(input_path)
    print(f"Loaded {len(atoms)} atoms")

    # Prepare atoms for database
    db_atoms = [prepare_atom_for_db(atom) for atom in atoms]

    # Validate embeddings
    atoms_with_embeddings = [a for a in db_atoms if a.get('embedding')]
    if len(atoms_with_embeddings) != len(atoms):
        print(f"\n[WARNING] Only {len(atoms_with_embeddings)}/{len(atoms)} atoms have embeddings")

    # Upload atoms
    uploaded, skipped, failed = upload_atoms_batch(client, db_atoms, batch_size=50)

    # Verify
    verify_upload(client, uploaded)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
