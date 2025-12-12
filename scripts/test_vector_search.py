#!/usr/bin/env python3
"""
TEST VECTOR SEARCH - Query knowledge base with embeddings

Tests semantic search on the live knowledge base.

Usage:
    poetry run python scripts/test_vector_search.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import openai

# Load env
load_dotenv()

#  Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("VECTOR SEARCH TEST - QUERYING LIVE KNOWLEDGE BASE")
print("=" * 80)
print()

# ============================================================================
# STEP 1: CONNECT TO SUPABASE
# ============================================================================

print("[1/4] Connecting to Supabase...")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not url or not key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY in .env")
    sys.exit(1)

supabase = create_client(url, key)
print(f"Connected to: {url}")
print()

# ============================================================================
# STEP 2: GENERATE QUERY EMBEDDING
# ============================================================================

print("[2/4] Generating query embedding...")

# Test query - targeting PLC motor starter content
query = "How do I wire a 3-wire motor starter circuit?"

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    print("ERROR: Missing OPENAI_API_KEY in .env")
    sys.exit(1)

try:
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding
    print(f"Query: \"{query}\"")
    print(f"Embedding dimensions: {len(query_embedding)}")
    print()
except Exception as e:
    print(f"ERROR generating embedding: {e}")
    sys.exit(1)

# ============================================================================
# STEP 3: SEARCH KNOWLEDGE BASE
# ============================================================================

print("[3/4] Searching knowledge base...")

# Format embedding for PostgreSQL
embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

# Use RPC function for vector search (if it exists), otherwise use direct query
try:
    # Try using RPC function (if created in Supabase)
    results = supabase.rpc(
        'search_atoms_by_embedding',
        {
            'query_embedding': embedding_str,
            'match_threshold': 0.7,
            'match_count': 5
        }
    ).execute()

    atoms = results.data
    print(f"Found {len(atoms)} relevant atoms via RPC")

except Exception as e:
    print(f"RPC search failed (function may not exist): {e}")
    print("Falling back to direct similarity query...")

    # Fallback: Direct query with cosine similarity
    # Note: This requires pgvector extension and proper indexing
    try:
        # For now, just get sample atoms to test the pipeline
        response = supabase.table("knowledge_atoms").select(
            "atom_id, atom_type, title, summary, manufacturer"
        ).limit(5).execute()

        atoms = response.data
        print(f"Retrieved {len(atoms)} sample atoms (vector search not yet configured)")
        print()
        print("NOTE: To enable proper vector search, run:")
        print("  - CREATE EXTENSION IF NOT EXISTS vector;")
        print("  - CREATE INDEX ON knowledge_atoms USING ivfflat (embedding vector_cosine_ops);")
        print("  - Create search_atoms_by_embedding() RPC function")
        print()

    except Exception as e2:
        print(f"ERROR: {e2}")
        sys.exit(1)

# ============================================================================
# STEP 4: DISPLAY RESULTS
# ============================================================================

print("[4/4] Search Results:")
print("=" * 80)

if not atoms:
    print("No results found")
else:
    for i, atom in enumerate(atoms, 1):
        print(f"\n[{i}] {atom.get('title', 'Untitled')}")
        print(f"    ID: {atom.get('atom_id', 'unknown')}")
        print(f"    Type: {atom.get('atom_type', 'unknown')}")
        print(f"    Manufacturer: {atom.get('manufacturer', 'unknown')}")
        print(f"    Summary: {atom.get('summary', 'No summary')[:150]}...")

print()
print("=" * 80)
print("VECTOR SEARCH TEST COMPLETE")
print("=" * 80)
print()

print("NEXT STEPS:")
print("1. Enable pgvector extension in Supabase")
print("2. Create vector index on embedding column")
print("3. Create search_atoms_by_embedding() RPC function")
print("4. Test semantic search with real embeddings")
print()
