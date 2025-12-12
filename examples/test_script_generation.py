#!/usr/bin/env python3
"""
Test ScriptwriterAgent generate_script() method.

Tests:
1. Generate script for "PLC Basics"
2. Validate script structure
3. Check word count (300-500 words expected)
4. Verify citations are included
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent


def test_script_generation():
    """Test generate_script() with real atoms"""
    print("=" * 70)
    print("TESTING ScriptwriterAgent.generate_script()")
    print("=" * 70)

    agent = ScriptwriterAgent()

    # Test: Generate script for "PLC Basics"
    print("\nStep 1: Query atoms for 'PLC'")
    print("-" * 70)
    atoms = agent.query_atoms("PLC", limit=3)
    print(f"Retrieved {len(atoms)} atoms")

    print("\nStep 2: Generate script from atoms")
    print("-" * 70)
    script = agent.generate_script("Introduction to PLCs", atoms)

    print(f"\nTitle: {script['title']}")
    print(f"Word Count: {script['word_count']}")
    print(f"Estimated Duration: {script['estimated_duration_seconds']} seconds (~{script['estimated_duration_seconds']//60} min {script['estimated_duration_seconds']%60} sec)")
    print(f"Sections: {len(script['sections'])}")
    print(f"Citations: {len(script['citations'])}")

    print("\n" + "=" * 70)
    print("FULL SCRIPT PREVIEW")
    print("=" * 70)

    print(f"\n[HOOK]")
    print(script['hook'])

    print(f"\n[INTRO]")
    print(script['intro'])

    for i, section in enumerate(script['sections'], 1):
        print(f"\n[SECTION {i}: {section['title']}]")
        preview = section['content'][:200] + "..." if len(section['content']) > 200 else section['content']
        print(preview)

    print(f"\n[SUMMARY]")
    print(script['summary'])

    print(f"\n[CTA]")
    print(script['cta'])

    print(f"\n[CITATIONS]")
    for citation in script['citations']:
        print(f"- {citation}")

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    # Validate structure
    checks = {
        "Has title": 'title' in script,
        "Has hook": 'hook' in script and len(script['hook']) > 0,
        "Has intro": 'intro' in script and len(script['intro']) > 0,
        "Has sections": 'sections' in script and len(script['sections']) > 0,
        "Has summary": 'summary' in script and len(script['summary']) > 0,
        "Has CTA": 'cta' in script and len(script['cta']) > 0,
        "Has citations": 'citations' in script and len(script['citations']) > 0,
        "Word count 300-500": 300 <= script['word_count'] <= 500,
        "Duration 2-4 min": 120 <= script['estimated_duration_seconds'] <= 240
    }

    passed = 0
    failed = 0

    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {check}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = test_script_generation()
    sys.exit(0 if success else 1)
