#!/usr/bin/env python3
"""
ScriptwriterAgent Complete Demo

Demonstrates the full workflow:
1. Query atoms by topic
2. Generate base script
3. Add personality markers
4. Add visual cues
5. Save final script to file

Usage:
    poetry run python examples/scriptwriter_demo.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent


def save_script(script: dict, output_dir: Path):
    """Save script to JSON file"""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"script_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print(f"\n[SAVED] Script saved to: {filepath}")

    # Also save plain text version
    txt_filepath = output_dir / f"script_{timestamp}.txt"
    with open(txt_filepath, 'w', encoding='utf-8') as f:
        f.write(f"TITLE: {script['title']}\n")
        f.write(f"WORD COUNT: {script['word_count']}\n")
        f.write(f"DURATION: {script['estimated_duration_seconds']} seconds\n")
        f.write(f"GENERATED: {datetime.now().isoformat()}\n")
        f.write("=" * 70 + "\n\n")
        f.write(script['full_script'])
        f.write("\n\n" + "=" * 70 + "\n")
        f.write("CITATIONS:\n")
        for citation in script['citations']:
            f.write(f"- {citation}\n")

    print(f"[SAVED] Plain text version: {txt_filepath}")

    return filepath


def main():
    """Run complete scriptwriter demo"""
    print("=" * 70)
    print("SCRIPTWRITER AGENT - COMPLETE DEMO")
    print("=" * 70)

    # Initialize agent
    print("\n[1/5] Initializing ScriptwriterAgent...")
    agent = ScriptwriterAgent()
    print("[OK] Agent initialized")

    # Define topics to generate scripts for
    topics = [
        ("Introduction to PLCs", "PLC"),
        ("Motor Control Basics", "motor"),
        ("Ladder Logic Fundamentals", "ladder")
    ]

    output_dir = project_root / "data" / "scripts"

    for title, query in topics:
        print("\n" + "=" * 70)
        print(f"GENERATING: {title}")
        print("=" * 70)

        # Step 1: Query atoms
        print(f"\n[2/5] Querying atoms for '{query}'...")
        atoms = agent.query_atoms(query, limit=3)
        print(f"[OK] Retrieved {len(atoms)} atoms")

        if not atoms:
            print(f"[SKIP] No atoms found for '{query}'")
            continue

        # Step 2: Generate base script
        print(f"\n[3/5] Generating base script...")
        script = agent.generate_script(title, atoms)
        print(f"[OK] Script generated ({script['word_count']} words, ~{script['estimated_duration_seconds']//60} min)")

        # Step 3: Add personality markers
        print(f"\n[4/5] Adding personality markers...")
        script = agent.add_personality_markers(script)
        print("[OK] Personality markers added ([enthusiastic], [cautionary], [pause])")

        # Step 4: Add visual cues
        print(f"\n[5/5] Adding visual cues...")
        script = agent.add_visual_cues(script)
        print("[OK] Visual cues added ([show title], [show diagram], [show code])")

        # Save script
        filepath = save_script(script, output_dir)

        # Show preview
        print("\n" + "-" * 70)
        print("SCRIPT PREVIEW:")
        print("-" * 70)
        print(f"\nTitle: {script['title']}")
        print(f"Word Count: {script['word_count']}")
        print(f"Duration: {script['estimated_duration_seconds']} seconds")
        print(f"\nHook (first 50 chars):")
        print(script['hook'][:50] + "...")
        print(f"\nCitations: {len(script['citations'])}")
        for citation in script['citations']:
            print(f"  - {citation}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print(f"\nGenerated {len(topics)} scripts")
    print(f"Output directory: {output_dir}")
    print("\nNext steps:")
    print("1. Review generated scripts in data/scripts/")
    print("2. Test VoiceProductionAgent with these scripts")
    print("3. Create first video with VideoAssemblyAgent")


if __name__ == "__main__":
    main()
