#!/usr/bin/env python3
"""
Test ScriptwriterAgent query_atoms() method.

Tests:
1. Query for "PLC" topic
2. Query for "motor" topic
3. Query for "ladder" topic

Expected: Each query returns relevant atoms from Supabase
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent


def test_query_atoms():
    """Test query_atoms() with 3 topics"""
    print("=" * 70)
    print("TESTING ScriptwriterAgent.query_atoms()")
    print("=" * 70)

    agent = ScriptwriterAgent()

    # Test 1: PLC basics
    print("\nTest 1: Query for 'PLC'")
    print("-" * 70)
    plc_atoms = agent.query_atoms("PLC", limit=3)
    print(f"Results: {len(plc_atoms)} atoms")
    for i, atom in enumerate(plc_atoms, 1):
        print(f"\n{i}. {atom.get('title', 'Untitled')}")
        print(f"   Type: {atom.get('atom_type', 'unknown')}")
        print(f"   Manufacturer: {atom.get('manufacturer', 'unknown')}")
        print(f"   Summary: {atom.get('summary', '')[:100]}...")

    # Test 2: Motor control
    print("\n" + "=" * 70)
    print("Test 2: Query for 'motor'")
    print("-" * 70)
    motor_atoms = agent.query_atoms("motor", limit=3)
    print(f"Results: {len(motor_atoms)} atoms")
    for i, atom in enumerate(motor_atoms, 1):
        print(f"\n{i}. {atom.get('title', 'Untitled')}")
        print(f"   Type: {atom.get('atom_type', 'unknown')}")
        print(f"   Manufacturer: {atom.get('manufacturer', 'unknown')}")
        print(f"   Summary: {atom.get('summary', '')[:100]}...")

    # Test 3: Ladder logic
    print("\n" + "=" * 70)
    print("Test 3: Query for 'ladder'")
    print("-" * 70)
    ladder_atoms = agent.query_atoms("ladder", limit=3)
    print(f"Results: {len(ladder_atoms)} atoms")
    for i, atom in enumerate(ladder_atoms, 1):
        print(f"\n{i}. {atom.get('title', 'Untitled')}")
        print(f"   Type: {atom.get('atom_type', 'unknown')}")
        print(f"   Manufacturer: {atom.get('manufacturer', 'unknown')}")
        print(f"   Summary: {atom.get('summary', '')[:100]}...")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"Total queries: 3")
    print(f"PLC atoms found: {len(plc_atoms)}")
    print(f"Motor atoms found: {len(motor_atoms)}")
    print(f"Ladder atoms found: {len(ladder_atoms)}")

    # Validation
    if len(plc_atoms) > 0 and len(motor_atoms) > 0 and len(ladder_atoms) > 0:
        print("\n[SUCCESS] All queries returned results")
        return True
    else:
        print("\n[WARNING] Some queries returned no results")
        return False


if __name__ == "__main__":
    success = test_query_atoms()
    sys.exit(0 if success else 1)
