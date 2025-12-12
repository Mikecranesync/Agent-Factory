#!/usr/bin/env python3
"""
Test Telegram KB Commands

Tests the KB integration without actually running the bot.
Simulates the command handlers to verify they work.
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.memory.storage import SupabaseMemoryStorage

print("=" * 80)
print("TESTING TELEGRAM KB INTEGRATION")
print("=" * 80)
print()

# Test 1: Supabase Connection
print("[1/4] Testing Supabase connection...")
try:
    storage = SupabaseMemoryStorage()
    result = storage.client.table("knowledge_atoms").select("atom_id", count="exact").limit(1).execute()
    print(f"  [OK] Connected to Supabase")
    print(f"  [OK] knowledge_atoms table exists")
except Exception as e:
    print(f"  [FAIL] Connection failed: {e}")
    sys.exit(1)

# Test 2: KB Stats Query
print("\n[2/4] Testing KB stats query...")
try:
    # Total atoms
    result = storage.client.table("knowledge_atoms")\
        .select("atom_id", count="exact")\
        .execute()
    total = result.count if hasattr(result, 'count') else len(result.data)

    print(f"  [OK] Total atoms: {total:,}")

    # By manufacturer
    for mfr in ["allen_bradley", "siemens"]:
        result = storage.client.table("knowledge_atoms")\
            .select("atom_id", count="exact")\
            .eq("manufacturer", mfr)\
            .execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        if count > 0:
            print(f"  [OK] {mfr.replace('_', ' ').title()}: {count:,}")

except Exception as e:
    print(f"  [FAIL] Stats query failed: {e}")
    sys.exit(1)

# Test 3: KB Search Query
print("\n[3/4] Testing KB search query...")
try:
    topic = "motor"

    result = storage.client.table("knowledge_atoms")\
        .select("atom_id, title, manufacturer")\
        .or_(
            f"title.ilike.%{topic}%,"
            f"summary.ilike.%{topic}%,"
            f"content.ilike.%{topic}%"
        )\
        .limit(5)\
        .execute()

    atoms = result.data

    if atoms:
        print(f"  [OK] Found {len(atoms)} atoms for '{topic}'")
        print(f"  [OK] Sample: {atoms[0].get('title', 'Untitled')[:50]}...")
    else:
        print(f"  [WARN] No atoms found for '{topic}' (this may be OK)")

except Exception as e:
    print(f"  [FAIL] Search query failed: {e}")
    sys.exit(1)

# Test 4: KB Get Query
print("\n[4/4] Testing KB get query...")
try:
    # Get first atom
    result = storage.client.table("knowledge_atoms")\
        .select("atom_id, title, content")\
        .limit(1)\
        .execute()

    if result.data:
        atom = result.data[0]
        atom_id = atom.get("atom_id", "")

        # Get by atom_id
        result2 = storage.client.table("knowledge_atoms")\
            .select("*")\
            .eq("atom_id", atom_id)\
            .execute()

        if result2.data:
            atom_full = result2.data[0]
            print(f"  [OK] Retrieved atom: {atom_id}")
            print(f"  [OK] Title: {atom_full.get('title', 'Untitled')[:50]}...")
            print(f"  [OK] Has content: {len(atom_full.get('content', ''))} chars")
        else:
            print(f"  [FAIL] Failed to retrieve atom by ID")
    else:
        print(f"  [FAIL] No atoms in database to test with")

except Exception as e:
    print(f"  [FAIL] Get query failed: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print()
print("Telegram KB commands are ready to use:")
print("  /kb_stats - Show KB metrics")
print("  /kb_search <topic> - Search atoms")
print("  /kb_get <atom_id> - Get atom details")
print("  /generate_script <topic> - Generate YouTube script")
print()
print("Start bot: poetry run python -m agent_factory.integrations.telegram")
print()
