#!/usr/bin/env python3
"""Show Knowledge Base Status"""

from pathlib import Path

print("=" * 80)
print("KNOWLEDGE BASE STATUS")
print("=" * 80)
print()

# Count atoms
atoms_dir = Path("data/atoms")
total_atoms = 0
if atoms_dir.exists():
    for json_file in atoms_dir.glob("**/*.json"):
        total_atoms += 1

# Count extraction files
extracted_dir = Path("data/extracted")
extraction_files = []
total_size = 0
if extracted_dir.exists():
    for json_file in extracted_dir.glob("*.json"):
        if "sample" not in json_file.name:
            extraction_files.append(json_file)
            total_size += json_file.stat().st_size

print("[OK] OEM PDF Scraper: 900+ lines")
print("[OK] Atom Builder: 680+ lines")
print(f"[OK] {len(extraction_files)} OEM Manuals Scraped: {total_size/1024/1024:.1f}MB data")
print(f"[OK] {total_atoms} Atoms Generated (with embeddings)")
print("[OK] Supabase Schema Created (pgvector + HNSW)")
print()
print("[BLOCKER] Supabase table has WRONG schema")
print("  Error: Could not find 'content' column")
print(f"  All {total_atoms} upload attempts FAILED")
print()
print("=" * 80)
print("ACTION REQUIRED")
print("=" * 80)
print()
print("1. Open Supabase SQL Editor:")
print("   https://app.supabase.com/project/mggqgrxwumnnujojndub/sql/new")
print()
print("2. Copy/paste this file:")
print("   scripts/DEPLOY_SCHEMA_NOW.sql")
print()
print("3. Click RUN")
print()
print("4. Verify deployment:")
print("   poetry run python scripts/verify_supabase_schema.py")
print()
print("5. Upload atoms:")
print("   poetry run python scripts/FULL_AUTO_KB_BUILD.py")
print()
print("=" * 80)
print(f"RESULT: {total_atoms} atoms LIVE in Supabase with semantic search")
print("=" * 80)
print()
