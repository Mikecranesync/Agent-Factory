#!/usr/bin/env python3
"""
SEOAgent Demo - Generate SEO-optimized video metadata

This demo shows how to use the SEOAgent to optimize video metadata
for YouTube search and discovery.

Usage:
    python examples/seo_demo.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content.seo_agent import SEOAgent, VideoMetadata


def main():
    """Run SEO optimization demo"""

    print("=" * 80)
    print("SEOAgent Demo - Video Metadata Optimization")
    print("=" * 80)
    print()

    # Sample video script (from PLC tutorial)
    sample_script = """
    Welcome to PLC Ladder Logic Basics! Today we're learning about motor control.

    PLC ladder logic is the fundamental programming language for industrial automation.
    It uses relay logic symbols to represent electrical circuits.

    A basic motor start-stop circuit requires three components:
    - Start pushbutton (normally open)
    - Stop pushbutton (normally closed)
    - Motor contactor with seal-in contact

    When you press the start button, current flows through the stop button,
    start button, and energizes the motor contactor. The motor starts running.

    The seal-in contact closes, maintaining current flow even after releasing
    the start button. This is called latching or sealing.

    To stop the motor, press the stop button. This breaks the circuit and
    de-energizes the contactor, stopping the motor.

    This basic pattern is used in thousands of industrial applications worldwide.
    Understanding ladder logic fundamentals is essential for PLC programmers.

    Practice this pattern, and you'll master the foundation of PLC programming.
    """

    topic = "PLC Ladder Logic Basics"
    target_keywords = ["PLC tutorial", "ladder logic", "motor control", "Allen-Bradley"]

    print("INPUT:")
    print("-" * 80)
    print(f"Topic: {topic}")
    print(f"Target Keywords: {', '.join(target_keywords)}")
    print(f"Script Length: {len(sample_script.split())} words")
    print()

    # Create agent (with mocked Supabase for demo)
    try:
        from unittest.mock import MagicMock, patch

        with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
            # Mock Supabase client
            mock_client = MagicMock()
            mock_storage.return_value.client = mock_client

            agent = SEOAgent()

            print("PROCESSING:")
            print("-" * 80)
            print("Running SEO optimization...")
            print()

            # Generate optimized metadata
            metadata = agent.optimize_metadata(
                video_id="vid:demo123",
                script=sample_script,
                topic=topic,
                target_keywords=target_keywords
            )

            print("OUTPUT:")
            print("=" * 80)
            print()

            # Display optimized metadata
            print(f"VIDEO ID: {metadata.video_id}")
            print()

            print(f"TITLE ({len(metadata.title)} chars):")
            print(f"  {metadata.title}")
            print()

            print(f"PRIMARY KEYWORD:")
            print(f"  {metadata.primary_keyword}")
            print()

            print(f"SECONDARY KEYWORDS:")
            for kw in metadata.secondary_keywords:
                print(f"  - {kw}")
            print()

            print(f"TAGS ({len(metadata.tags)} total):")
            for tag in metadata.tags:
                print(f"  - {tag}")
            print()

            print(f"DESCRIPTION ({len(metadata.description)} chars):")
            print("-" * 80)
            print(metadata.description)
            print("-" * 80)
            print()

            print("SEO ANALYSIS:")
            print("-" * 80)
            print(f"Search Volume: {metadata.search_volume_estimate}")
            print(f"Competition: {metadata.competition_level}")
            print(f"Estimated CTR: {metadata.estimated_ctr:.2%}")
            print(f"Estimated Watch Time: {metadata.estimated_watch_time_minutes} minutes")
            print()

            # Validate against SEO best practices
            print("VALIDATION:")
            print("-" * 80)

            checks = [
                ("Title length (30-70 chars)", 30 <= len(metadata.title) <= 70),
                ("Title optimal (60-70 chars)", 60 <= len(metadata.title) <= 70),
                ("Description length (100-5000 chars)", 100 <= len(metadata.description) <= 5000),
                ("Tag count (10-15)", 10 <= len(metadata.tags) <= 15),
                ("Primary keyword in title", metadata.primary_keyword.lower() in metadata.title.lower() or topic.lower() in metadata.title.lower()),
                ("Primary keyword in description", metadata.primary_keyword in metadata.description),
                ("Timestamps in description", "0:00" in metadata.description),
                ("CTR > 5%", metadata.estimated_ctr > 0.05),
            ]

            for check_name, passed in checks:
                status = "PASS" if passed else "FAIL"
                symbol = "[OK]" if passed else "[FAIL]"
                print(f"  {symbol} {check_name}: {status}")

            print()

            # Save to file
            output_dir = Path("data/seo")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{metadata.video_id}_metadata.json"

            with open(output_path, "w") as f:
                json.dump(metadata.model_dump(), f, indent=2, default=str)

            print(f"SAVED: {output_path}")
            print()

            print("=" * 80)
            print("DEMO COMPLETE - SEOAgent successfully optimized video metadata!")
            print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
