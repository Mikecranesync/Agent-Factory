#!/usr/bin/env python3
"""
Quick check: How many atoms are in Supabase?
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

# Count atoms
response = supabase.table("knowledge_atoms").select("atom_id", count="exact").execute()

print(f"\n{'='*80}")
print(f"ATOMS IN SUPABASE DATABASE")
print(f"{'='*80}")
print(f"\nTotal atoms: {response.count}")
print(f"\nFirst 5 atoms:")
for atom in response.data[:5]:
    print(f"  - {atom['atom_id']}")
print(f"\n{'='*80}\n")
