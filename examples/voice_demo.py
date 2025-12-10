#!/usr/bin/env python3
"""
Voice Production Demo - Test hybrid TTS voice modes

Tests all 3 voice modes:
1. Edge-TTS (FREE, Microsoft neural voices)
2. OpenAI TTS (PAID, $15/1M chars)
3. ElevenLabs (PAID, custom voice clone - not yet implemented)

Usage:
    poetry run python examples/voice_demo.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from agents.media.voice_production_agent import VoiceProductionAgent


def main():
    """Test voice generation with all available modes."""

    print("=" * 70)
    print("VOICE PRODUCTION DEMO - Hybrid TTS System")
    print("=" * 70)
    print()

    # Test script
    test_script = """
    Welcome to PLC fundamentals! Today we'll learn about voltage, current, and resistance.
    These are the three most important concepts in electricity. Think of voltage as pressure,
    current as flow, and resistance as friction. Together, they form Ohm's Law: V equals I times R.
    """

    output_dir = Path("output/voice_tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get current voice mode
    current_mode = os.getenv("VOICE_MODE", "edge")
    print(f"Current VOICE_MODE: {current_mode}\n")

    # Test 1: Edge-TTS (FREE)
    print("[1/3] Testing Edge-TTS (FREE Microsoft neural voices)...")
    print("-" * 70)
    try:
        os.environ["VOICE_MODE"] = "edge"
        agent = VoiceProductionAgent()

        output_file = output_dir / "test_edge_tts.mp3"
        result = agent.generate_audio(test_script, str(output_file))

        print(f"  [OK] Edge-TTS generation successful")
        print(f"  File: {result}")
        print(f"  Cost: $0.00 (FREE)")
        print()
    except Exception as e:
        print(f"  [FAIL] Edge-TTS failed: {e}\n")

    # Test 2: OpenAI TTS (PAID)
    print("[2/3] Testing OpenAI TTS (PAID, ~$15/1M chars)...")
    print("-" * 70)
    if os.getenv("OPENAI_API_KEY"):
        try:
            os.environ["VOICE_MODE"] = "openai"
            agent = VoiceProductionAgent()

            output_file = output_dir / "test_openai_tts.mp3"
            result = agent.generate_audio(test_script, str(output_file))

            char_count = len(test_script)
            cost = (char_count / 1_000_000) * 15
            print(f"  [OK] OpenAI TTS generation successful")
            print(f"  File: {result}")
            print(f"  Characters: {char_count}")
            print(f"  Cost: ${cost:.4f}")
            print()
        except Exception as e:
            print(f"  [FAIL] OpenAI TTS failed: {e}\n")
    else:
        print("  [SKIP] OPENAI_API_KEY not set in .env\n")

    # Test 3: ElevenLabs (PAID, custom voice - not yet implemented)
    print("[3/3] Testing ElevenLabs (PAID, custom voice clone)...")
    print("-" * 70)
    try:
        os.environ["VOICE_MODE"] = "elevenlabs"
        agent = VoiceProductionAgent()

        output_file = output_dir / "test_elevenlabs_tts.mp3"
        result = agent.generate_audio(test_script, str(output_file))

        print(f"  [OK] ElevenLabs generation successful")
        print(f"  File: {result}")
        print()
    except NotImplementedError as e:
        print(f"  [SKIP] {e}\n")
    except Exception as e:
        print(f"  [FAIL] ElevenLabs failed: {e}\n")

    # Restore original mode
    os.environ["VOICE_MODE"] = current_mode

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Voice Modes Available:")
    print("  1. Edge-TTS (FREE) - Recommended for development")
    print("  2. OpenAI TTS ($15/1M chars) - Good quality, paid")
    print("  3. ElevenLabs (custom voice) - Coming Saturday after voice training")
    print()
    print("To change voice mode, update .env:")
    print("  VOICE_MODE=edge       # FREE (default)")
    print("  VOICE_MODE=openai     # PAID")
    print("  VOICE_MODE=elevenlabs # PAID (after Saturday)")
    print()
    print("Output files saved to: output/voice_tests/")
    print()

    # Cost comparison
    print("Cost Comparison (for 100 videos @ 1,000 words each):")
    print("-" * 70)
    chars_per_video = 1000 * 5  # Assume 5 chars per word
    videos = 100

    edge_cost = 0
    openai_cost = (chars_per_video * videos / 1_000_000) * 15
    elevenlabs_cost = (chars_per_video * videos / 1_000_000) * 30  # Estimate

    print(f"  Edge-TTS:     ${edge_cost:.2f} (FREE!)")
    print(f"  OpenAI TTS:   ${openai_cost:.2f}")
    print(f"  ElevenLabs:   ${elevenlabs_cost:.2f} (estimate)")
    print()
    print(f"Savings with Edge-TTS: ${openai_cost:.2f} per 100 videos")
    print()

    # Recommendation
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print()
    print("For development (now - Saturday):")
    print("  Use VOICE_MODE=edge (100% FREE, professional quality)")
    print()
    print("For production (Saturday onwards):")
    print("  Use VOICE_MODE=elevenlabs (custom voice, best quality)")
    print()
    print("Migration path:")
    print("  1. Develop with Edge-TTS (FREE)")
    print("  2. Train custom voice Saturday")
    print("  3. Switch to ElevenLabs (one env variable change)")
    print("  4. Re-render any videos that need custom voice")
    print()


if __name__ == "__main__":
    main()
