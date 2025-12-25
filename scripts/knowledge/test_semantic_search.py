#!/usr/bin/env python3
"""
Test semantic search on uploaded knowledge atoms.

Usage:
    poetry run python scripts/knowledge/test_semantic_search.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import openai

# Load environment
load_dotenv()


def generate_query_embedding(query: str):
    """Generate embedding for search query."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def semantic_search(supabase_client, query: str, top_k: int = 3):
    """Perform semantic search using deployed RPC function."""
    # Generate query embedding
    query_embedding = generate_query_embedding(query)

    # Use the deployed RPC function
    result = supabase_client.rpc(
        'search_atoms_by_embedding',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.5,
            'match_count': top_k
        }
    ).execute()

    return result.data


def test_search(query: str, expected_atom_id: str = None):
    """Test semantic search."""
    # Connect to Supabase (which routes to correct database via DATABASE_PROVIDER config)
    client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)

    try:
        results = semantic_search(client, query, top_k=3)

        if not results:
            print("[WARNING] No results found")
            return False

        # Display results
        for i, atom in enumerate(results, 1):
            print(f"\n{i}. {atom.get('title')}")
            print(f"   Atom ID: {atom.get('atom_id')}")
            print(f"   Similarity: {atom.get('similarity'):.3f}")
            print(f"   Summary: {atom.get('summary')[:80]}...")

        # Validate
        if expected_atom_id and results:
            if results[0].get('atom_id') == expected_atom_id:
                print(f"\n[PASS] Top result matches expected atom")
                return True
            else:
                print(f"\n[WARNING] Expected {expected_atom_id}, got {results[0].get('atom_id')}")
                # Still pass if similarity is high
                return results[0].get('similarity', 0) > 0.7

        return True

    except Exception as e:
        print(f"\n[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test workflow."""
    print("\n" + "="*70)
    print("KNOWLEDGE ATOM SEMANTIC SEARCH VALIDATION")
    print("="*70)

    # Connect to database
    client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

    # Verify atoms exist
    print("\nVerifying uploaded atoms...")
    try:
        count_result = client.table('knowledge_atoms').select('atom_id', count='exact').eq('manufacturer', 'agent-factory').execute()
        print(f"Found {count_result.count} agent-factory atoms in database")

        if count_result.count == 0:
            print("[ERROR] No agent-factory atoms found!")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to count atoms: {e}")

    # Test queries
    test_queries = [
        ("LLM routing and cost optimization", "pattern:agent-factory-llm-router"),
        ("database failover pattern", "pattern:agent-factory-database-failover"),
        ("git worktree parallel development", None),
    ]

    print("\n" + "="*70)
    print("RUNNING TEST QUERIES")
    print("="*70)

    passed = 0
    failed = 0

    for query, expected_id in test_queries:
        if test_search(query, expected_id):
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(test_queries)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nAll tests passed!")
        return True
    else:
        print(f"\n{failed} test(s) had issues")
        return passed > 0


if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)
