#!/usr/bin/env python3
"""
FULL AUTOMATION - KB BUILD + UPLOAD

Runs the complete pipeline:
1. Generate atoms from ALL extracted PDFs
2. Upload atoms to Supabase
3. Show final stats

NO USER INPUT REQUIRED.

Usage:
    poetry run python scripts/FULL_AUTO_KB_BUILD.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.knowledge.atom_builder_from_pdf import AtomBuilderFromPDF
from supabase import create_client

print("=" * 80)
print("FULL AUTOMATION - KNOWLEDGE BASE BUILD + UPLOAD")
print("=" * 80)
print()

# ============================================================================
# STEP 1: BUILD ATOMS FROM ALL EXTRACTED PDFs
# ============================================================================

print("[1/3] BUILDING ATOMS FROM EXTRACTED PDFs...")
print()

builder = AtomBuilderFromPDF()

extracted_dir = Path("data/extracted")
extraction_files = list(extracted_dir.glob("*.json"))

# Skip sample file
extraction_files = [f for f in extraction_files if "sample" not in f.name]

print(f"Found {len(extraction_files)} extraction files")

all_atoms = []

for idx, json_file in enumerate(extraction_files, 1):
    print(f"\n[{idx}/{len(extraction_files)}] Processing: {json_file.name}")

    try:
        atoms = builder.process_pdf_extraction(
            json_file,
            output_dir=Path("data/atoms") / json_file.stem
        )
        all_atoms.extend(atoms)
        print(f"  Generated {len(atoms)} atoms")
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n{'=' * 80}")
print(f"ATOMS GENERATED: {len(all_atoms)}")
print(f"{'=' * 80}")

# Show stats
stats = builder.get_stats()
print("\nBreakdown:")
for k, v in stats.items():
    print(f"  {k}: {v}")

# ============================================================================
# STEP 2: CONNECT TO SUPABASE
# ============================================================================

print(f"\n[2/3] CONNECTING TO SUPABASE...")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not url or not key:
    print("\nERROR: Supabase credentials not found in .env")
    print("Need: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    print("\nAtoms saved locally to: data/atoms/")
    print("Upload them manually when Supabase is ready.")
    sys.exit(0)

try:
    supabase = create_client(url, key)
    print(f"Connected to: {url}")
except Exception as e:
    print(f"\nERROR connecting to Supabase: {e}")
    print("\nAtoms saved locally to: data/atoms/")
    sys.exit(0)

# ============================================================================
# STEP 3: UPLOAD ATOMS TO SUPABASE
# ============================================================================

print(f"\n[3/3] UPLOADING {len(all_atoms)} ATOMS TO SUPABASE...")
print()

uploaded = 0
failed = 0

for idx, atom in enumerate(all_atoms, 1):
    try:
        # Convert to dict
        atom_dict = atom.to_dict()

        # Upload (upsert by atom_id - update if exists, insert if new)
        response = supabase.table("knowledge_atoms").upsert(
            atom_dict,
            on_conflict="atom_id"
        ).execute()

        uploaded += 1

        if uploaded % 100 == 0:
            print(f"  Uploaded {uploaded}/{len(all_atoms)}...")

    except Exception as e:
        print(f"  FAILED: {atom.atom_id} - {e}")
        failed += 1

print(f"\n{'=' * 80}")
print(f"UPLOAD COMPLETE")
print(f"{'=' * 80}")
print(f"\n  Uploaded: {uploaded}")
print(f"  Failed: {failed}")
print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("=" * 80)
print("KNOWLEDGE BASE READY")
print("=" * 80)
print()
print(f"Total Atoms: {uploaded}")
print()
print("Atom Types:")
print(f"  Concepts: {stats.get('concepts', 0)}")
print(f"  Procedures: {stats.get('procedures', 0)}")
print(f"  Specifications: {stats.get('specifications', 0)}")
print(f"  Patterns: {stats.get('patterns', 0)}")
print(f"  Faults: {stats.get('faults', 0)}")
print(f"  References: {stats.get('references', 0)}")
print()
print(f"Embeddings Generated: {stats.get('embeddings_generated', 0)}")
print(f"Embedding Cost: ${stats.get('embeddings_generated', 0) * 0.000004:.4f}")
print()
print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("1. Test vector search:")
print("   - Query Supabase knowledge_atoms table")
print("   - Use search_atoms_by_embedding() function")
print()
print("2. Generate YouTube scripts:")
print("   - Query atoms for topic")
print("   - Run scriptwriter agent")
print("   - Generate video")
print()
print("3. START MAKING CONTENT")
print()
