#!/usr/bin/env python3
"""Query the Knowledge Base"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Connect
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("=" * 80)
print("KNOWLEDGE BASE QUERY")
print("=" * 80)
print()

# Total count
result = supabase.table("knowledge_atoms").select("atom_id", count="exact").execute()
total = result.count if hasattr(result, 'count') else len(result.data)
print(f"Total Atoms: {total}")
print()

# By manufacturer
print("By Manufacturer:")
for mfr in ["allen_bradley", "siemens"]:
    result = supabase.table("knowledge_atoms")\
        .select("atom_id", count="exact")\
        .eq("manufacturer", mfr)\
        .execute()
    count = result.count if hasattr(result, 'count') else len(result.data)
    print(f"  {mfr}: {count}")

print()

# By type
print("By Type:")
for atom_type in ["concept", "procedure", "specification", "pattern", "fault", "reference"]:
    result = supabase.table("knowledge_atoms")\
        .select("atom_id", count="exact")\
        .eq("atom_type", atom_type)\
        .execute()
    count = result.count if hasattr(result, 'count') else len(result.data)
    if count > 0:
        print(f"  {atom_type}: {count}")

print()

# Sample atoms
print("Sample Atoms:")
result = supabase.table("knowledge_atoms")\
    .select("atom_id, title, manufacturer")\
    .limit(10)\
    .execute()

for atom in result.data:
    print(f"  [{atom['manufacturer']}] {atom['atom_id']}")
    print(f"    {atom['title']}")

print()
print("=" * 80)
print("KNOWLEDGE BASE IS LIVE!")
print("=" * 80)
print()
print("Next: Build Scriptwriter Agent to generate YouTube scripts from these atoms")
print()
