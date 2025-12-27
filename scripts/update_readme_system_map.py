#!/usr/bin/env python3
"""
Update system map in README.md.

This script generates the system map and injects it into the README after
the "Latest Updates" section.

Usage:
    poetry run python scripts/update_readme_system_map.py

Behavior:
    - Generates system map using generate_system_map.py
    - Finds or creates "## 🗺️ System Map" section in README
    - Replaces entire section content with latest system map
    - Preserves all other README content
"""

import sys
import subprocess
from pathlib import Path
from typing import List


README_PATH = Path("README.md")
SECTION_HEADER = "## 🗺️ System Map"


def generate_system_map() -> str:
    """
    Run generate_system_map.py and capture output.

    Returns:
        System map markdown string
    """
    try:
        # Read from the saved markdown file (avoids encoding issues)
        map_path = Path("data/system_map.md")

        # Run generator
        subprocess.run(
            ["poetry", "run", "python", "scripts/generate_system_map.py"],
            check=True,
            capture_output=True
        )

        # Read generated map
        if map_path.exists():
            with open(map_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            print("ERROR: System map file not generated", file=sys.stderr)
            return ""

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to generate system map: {e}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return ""


def find_or_create_section(readme_lines: List[str]) -> tuple[int, int]:
    """
    Find system map section or create it after Latest Updates.

    Args:
        readme_lines: List of README lines

    Returns:
        Tuple of (section_start_line, section_end_line)
        If section doesn't exist, creates it and returns new indices
    """
    # Search for existing section
    for i, line in enumerate(readme_lines):
        if SECTION_HEADER in line:
            # Find end of section (next ## header or end of file)
            end_idx = len(readme_lines)
            for j in range(i + 1, len(readme_lines)):
                if readme_lines[j].strip().startswith("##"):
                    end_idx = j
                    break

            print(f"Found existing section at line {i+1}", file=sys.stderr)
            return (i, end_idx)

    # Section doesn't exist - find where to insert
    # Look for "Latest Updates" section first
    insert_after = None
    for i, line in enumerate(readme_lines):
        if "## 📝 Latest Updates" in line or "## Latest Updates" in line:
            # Find end of Latest Updates section
            for j in range(i + 1, len(readme_lines)):
                if readme_lines[j].strip().startswith("##"):
                    insert_after = j
                    break
            if insert_after is None:
                insert_after = len(readme_lines)
            break

    # If no Latest Updates, insert after line 50 (arbitrary safe point)
    if insert_after is None:
        insert_after = min(50, len(readme_lines))

    print(f"Section not found - inserting after line {insert_after}", file=sys.stderr)

    # Insert section header with blank lines
    insert_lines = [
        "\n",
        "---\n",
        "\n",
        f"{SECTION_HEADER}\n",
        "\n"
    ]

    for offset, line in enumerate(insert_lines):
        readme_lines.insert(insert_after + offset, line)

    # Return indices of new section
    section_start = insert_after + 3  # Index of header line
    section_end = section_start + 2   # End after blank line

    return (section_start, section_end)


def update_readme(system_map: str) -> bool:
    """
    Update README with new system map.

    Args:
        system_map: System map markdown content

    Returns:
        True if README was modified, False otherwise
    """
    if not README_PATH.exists():
        print(f"ERROR: {README_PATH} not found", file=sys.stderr)
        return False

    if not system_map:
        print("ERROR: Empty system map, skipping update", file=sys.stderr)
        return False

    # Read README
    with open(README_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find or create section
    section_start, section_end = find_or_create_section(lines)

    # Remove old content (keep header)
    del lines[section_start + 1:section_end]

    # Insert new system map after header
    map_lines = ["\n", system_map + "\n", "\n"]
    for offset, line in enumerate(map_lines):
        lines.insert(section_start + 1 + offset, line)

    # Check if content changed
    with open(README_PATH, "r", encoding="utf-8") as f:
        original_content = f.read()

    new_content = "".join(lines)

    if original_content == new_content:
        print("No changes to README.md system map", file=sys.stderr)
        return False

    # Write updated README
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ Updated system map in {README_PATH}", file=sys.stderr)
    return True


def main():
    """Main entry point."""
    # Generate system map
    print("Generating system map...", file=sys.stderr)
    system_map = generate_system_map()

    if not system_map:
        print("Failed to generate system map", file=sys.stderr)
        sys.exit(1)

    # Update README
    modified = update_readme(system_map)

    if modified:
        print("README.md system map updated successfully", file=sys.stderr)
        sys.exit(0)
    else:
        print("No changes needed", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
