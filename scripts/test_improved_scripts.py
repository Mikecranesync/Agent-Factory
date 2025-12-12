#!/usr/bin/env python3
"""
Test improved ScriptwriterAgent - verify teaching content not data dumps

Compares old (data dump) vs new (teaching) script generation
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent


def test_script_generation():
    """Test improved script generation"""
    print("=" * 70)
    print("IMPROVED SCRIPTWRITER TEST")
    print("=" * 70)

    agent = ScriptwriterAgent()

    # Test 1: Motor Control
    print("\n[TEST 1] Motor Control")
    print("-" * 70)
    atoms = agent.query_atoms("motor control", limit=3)
    print(f"Found {len(atoms)} atoms")

    if atoms:
        script = agent.generate_script("Motor Control Basics", atoms)
        script = agent.add_personality_markers(script)
        script = agent.add_visual_cues(script)

        print(f"\nScript Preview (first 500 chars):")
        print(script['full_script'][:500])
        print(f"\n... ({script['word_count']} words total)")

        # Check for data dump indicators
        has_table = '|' in script['full_script'] and '---' in script['full_script']
        has_raw_code = 'Axis:=' in script['full_script']
        has_params = '_multi_fb_in_' in script['full_script']

        print(f"\nQuality Checks:")
        print(f"  ❌ Contains raw table: {has_table}" if has_table else f"  ✅ No raw tables")
        print(f"  ❌ Contains raw code: {has_raw_code}" if has_raw_code else f"  ✅ No raw code")
        print(f"  ❌ Contains parameters: {has_params}" if has_params else f"  ✅ No parameters")

        if not (has_table or has_raw_code or has_params):
            print("\n✅ Script looks TEACHING-FOCUSED (not data dump)")
        else:
            print("\n❌ Script still contains raw data!")

    # Test 2: PLC Introduction
    print("\n\n[TEST 2] PLC Introduction")
    print("-" * 70)
    atoms = agent.query_atoms("PLC", limit=3)
    print(f"Found {len(atoms)} atoms")

    if atoms:
        script = agent.generate_script("Introduction to PLCs", atoms)
        script = agent.add_personality_markers(script)
        script = agent.add_visual_cues(script)

        print(f"\nScript Preview (first 500 chars):")
        print(script['full_script'][:500])
        print(f"\n... ({script['word_count']} words total)")

        # Check for specification tables
        has_spec_table = 'Table 2-1' in script['full_script']
        has_pipes = script['full_script'].count('|') > 5  # More than just visual cues

        print(f"\nQuality Checks:")
        print(f"  ❌ Contains spec tables: {has_spec_table}" if has_spec_table else f"  ✅ No spec tables")
        print(f"  ❌ Contains pipe formatting: {has_pipes}" if has_pipes else f"  ✅ Clean narration")

        if not (has_spec_table or has_pipes):
            print("\n✅ Script looks TEACHING-FOCUSED (not specification dump)")
        else:
            print("\n❌ Script still contains spec tables!")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_script_generation()
