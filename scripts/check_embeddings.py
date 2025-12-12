#!/usr/bin/env python3
"""Quick check: Do atoms have embeddings?"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

# Check a few atoms
response = supabase.table("knowledge_atoms").select("atom_id, embedding").limit(10).execute()

print(f"\n{'='*80}")
print(f"EMBEDDING CHECK")
print(f"{'='*80}\n")

with_embeddings = sum(1 for a in response.data if a.get('embedding'))
without_embeddings = len(response.data) - with_embeddings

print(f"Sample of {len(response.data)} atoms:")
print(f"  With embeddings: {with_embeddings}")
print(f"  Without embeddings: {without_embeddings}\n")

for atom in response.data[:5]:
    has_embedding = "YES" if atom.get('embedding') else "NO"
    print(f"  - {atom['atom_id'][:50]:<50} | Embedding: {has_embedding}")

print(f"\n{'='*80}\n")

if with_embeddings == 0:
    print("❌ NO EMBEDDINGS - Atoms uploaded without embeddings")
    print("   This is why vector search returned 0 results")
    print("   Need to re-upload with embeddings OR update existing atoms")
elif with_embeddings == len(response.data):
    print("✅ ALL ATOMS HAVE EMBEDDINGS")
else:
    print("⚠️  PARTIAL EMBEDDINGS - Some atoms missing embeddings")

print()
