#!/usr/bin/env python3
"""
Create Simple Video - Audio + Black Screen

Simplest possible approach:
1. Generate script
2. Generate audio with Edge-TTS
3. Create black video with audio
4. You add visuals manually later if needed

Usage:
    poetry run python scripts/create_simple_video.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent
import edge_tts


async def generate_audio(text: str, output_path: Path, voice: str = "en-US-GuyNeural"):
    """Generate audio from text using Edge-TTS"""
    print(f"\nGenerating audio with {voice}...")

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

    print(f"[OK] Audio saved: {output_path}")
    return output_path


async def main():
    """Create audio from generated script"""
    print("=" * 70)
    print("CREATE YOUTUBE VIDEO - AUDIO GENERATION")
    print("=" * 70)

    # Output directory
    output_dir = project_root / "data" / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Generate script
    print("\n[1/2] Generating script...")
    agent = ScriptwriterAgent()

    atoms = agent.query_atoms("PLC", limit=3)

    if not atoms:
        print("[ERROR] No atoms found")
        return False

    script = agent.generate_script("Introduction to PLCs", atoms)
    script = agent.add_personality_markers(script)
    script = agent.add_visual_cues(script)

    print(f"[OK] Script: {script['word_count']} words, {script['estimated_duration_seconds']}s")

    # Save script
    script_path = output_dir / f"script_{timestamp}.txt"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(f"TITLE: {script['title']}\n")
        f.write(f"DURATION: {script['estimated_duration_seconds']} seconds\n")
        f.write(f"WORD COUNT: {script['word_count']}\n\n")
        f.write("=" * 70 + "\n\n")
        f.write(script['full_script'])
        f.write("\n\n" + "=" * 70 + "\n\n")
        f.write("CITATIONS:\n")
        for citation in script['citations']:
            f.write(f"- {citation}\n")

    print(f"[OK] Script saved: {script_path}")

    # Step 2: Generate audio
    print(f"\n[2/2] Generating audio...")
    audio_path = output_dir / f"audio_{timestamp}.mp3"

    # Clean script (remove markers)
    clean_text = script['full_script']
    markers = ['[enthusiastic]', '[explanatory]', '[cautionary]', '[pause]',
               '[emphasize]', '[show title:', '[show diagram:', '[show code:',
               '[show table]', '[show citation:', ']']
    for marker in markers:
        clean_text = clean_text.replace(marker, ' ')

    # Remove multiple spaces
    clean_text = ' '.join(clean_text.split())

    await generate_audio(clean_text, audio_path)

    # Summary
    print("\n" + "=" * 70)
    print("AUDIO GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  Script: {script_path}")
    print(f"  Audio:  {audio_path}")
    print(f"\nVideo details:")
    print(f"  Title: {script['title']}")
    print(f"  Duration: ~{script['estimated_duration_seconds']//60} min {script['estimated_duration_seconds']%60} sec")
    print(f"\nCitations for description:")
    for citation in script['citations']:
        print(f"  - {citation}")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Listen to audio file to validate quality")
    print("2. Create video using ONE of these methods:")
    print()
    print("   OPTION A - PowerPoint (Easiest, 10 min):")
    print("   - Open PowerPoint, create 5-8 slides with text")
    print("   - File → Export → Create Video")
    print("   - In video editor, replace audio with generated MP3")
    print()
    print("   OPTION B - Canva (Simple, 15 min):")
    print("   - Go to canva.com, create video project")
    print("   - Add text slides, upload audio MP3")
    print("   - Export as MP4")
    print()
    print("   OPTION C - Just Audio + Black Screen (Fastest, 2 min):")
    print("   - Use Windows Photos or any video editor")
    print("   - Create black video, add audio")
    print("   - Upload (audio-only videos work on YouTube!)")
    print()
    print("3. Upload to YouTube:")
    print(f"   - Title: {script['title']}")
    print("   - Description: Paste citations from above")
    print("   - Tags: PLC, automation, industrial, tutorial")
    print("   - Visibility: Unlisted (review first)")
    print()
    print("4. After uploading, DM me the YouTube link for review")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
