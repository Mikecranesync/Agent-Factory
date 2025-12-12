#!/usr/bin/env python3
"""
Generate First YouTube Script

Uses Scriptwriter Agent to create a video script from knowledge atoms.
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content.scriptwriter_agent import ScriptwriterAgent

print("=" * 80)
print("GENERATING FIRST YOUTUBE SCRIPT")
print("=" * 80)
print()

# Initialize agent
agent = ScriptwriterAgent()

# Generate script for motor control
print("Topic: Motor Control Basics")
print("Target: 3-minute tutorial")
print()

payload = {
    "topic": "motor",
    "manufacturer": None,  # Search all manufacturers
    "target_duration_seconds": 180,  # 3 minutes
    "difficulty": None  # Any difficulty
}

try:
    result = agent.run(payload)

    if result["status"] == "success":
        script = result["result"]

        print("=" * 80)
        print("SCRIPT GENERATED!")
        print("=" * 80)
        print()
        print(f"Title: {script['title']}")
        print(f"Duration: {script['total_duration_seconds']}s")
        print(f"Atom Sources: {len(script['atom_sources'])}")
        print()
        print("Keywords:", ", ".join(script.get("keywords", [])[:5]))
        print()

        # Save to file
        output_dir = Path("data/scripts")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = script["title"].lower()\
            .replace(" ", "-")\
            .replace(":", "")\
            .replace("?", "")[:50] + ".json"

        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)

        print(f"Saved to: {output_path}")
        print()

        # Preview script
        print("=" * 80)
        print("SCRIPT PREVIEW")
        print("=" * 80)
        print()
        print(f"HOOK:\n{script.get('hook', '')}")
        print()
        print(f"INTRO:\n{script.get('intro', '')}")
        print()
        print(f"MAIN CONTENT ({len(script.get('sections', []))} sections):")
        for section in script.get("sections", []):
            print(f"\n  [{section.get('timestamp', '0:00')}] {section.get('title', '')}")
            print(f"  {section.get('script', '')[:200]}...")
        print()
        print(f"OUTRO:\n{script.get('outro', '')}")
        print()

    else:
        print(f"ERROR: {result.get('error')}")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
