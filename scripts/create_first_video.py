#!/usr/bin/env python3
"""
Create First YouTube Video - Complete Pipeline

Steps:
1. Generate script using ScriptwriterAgent
2. Generate audio using Edge-TTS (FREE)
3. Create simple video with text slides using MoviePy
4. Output ready-to-upload MP4

Usage:
    poetry run python scripts/create_first_video.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent

# Import for voice and video
import edge_tts
try:
    # MoviePy 2.x
    from moviepy import TextClip, AudioFileClip, concatenate_videoclips
except ImportError:
    # MoviePy 1.x fallback
    from moviepy.editor import TextClip, AudioFileClip, concatenate_videoclips


async def generate_audio(text: str, output_path: Path, voice: str = "en-US-GuyNeural"):
    """Generate audio from text using Edge-TTS"""
    print(f"\n[2/4] Generating audio with {voice}...")

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

    print(f"[OK] Audio saved: {output_path}")
    return output_path


def create_text_clip(text: str, duration: float, fontsize: int = 50):
    """Create a text clip with black background"""
    return (TextClip(text, font_size=fontsize, color='white',
                     font='Arial', size=(1280, None))
            .with_duration(duration)
            .with_position('center'))


def create_video(script: dict, audio_path: Path, output_path: Path):
    """Create video with text slides synced to audio"""
    print(f"\n[3/4] Creating video with text slides...")

    # Load audio to get duration
    audio = AudioFileClip(str(audio_path))
    total_duration = audio.duration

    # Create slides for each section
    slides = []

    # Title slide (5 seconds)
    title_slide = create_text_clip(script['title'], 5, fontsize=70)
    slides.append(title_slide)

    # Hook slide (10 seconds)
    hook_text = script['hook'].replace('[enthusiastic]', '').replace('[show title: ' + script['title'] + ']', '').strip()
    hook_slide = create_text_clip(hook_text, 10, fontsize=60)
    slides.append(hook_slide)

    # Section slides (divide remaining time)
    sections = script['sections']
    remaining_time = total_duration - 15  # After title + hook
    time_per_section = remaining_time / len(sections)

    for section in sections:
        # Clean text (remove markers and visual cues)
        content = section['content']
        for marker in ['[explanatory]', '[cautionary]', '[pause]', '[show code: ladder_logic]',
                       '[show diagram:', '[show table]', '[show citation:', ']']:
            content = content.replace(marker, '')

        # Limit text length for readability
        words = content.split()[:50]  # First 50 words
        content = ' '.join(words)

        section_slide = create_text_clip(
            f"{section['title']}\n\n{content[:200]}...",
            time_per_section,
            fontsize=40
        )
        slides.append(section_slide)

    # Create final video
    video = concatenate_videoclips(slides)
    video = video.with_audio(audio)

    # Write to file
    video.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        preset='medium'
    )

    print(f"[OK] Video saved: {output_path}")
    return output_path


async def main():
    """Complete video creation pipeline"""
    print("=" * 70)
    print("CREATE FIRST YOUTUBE VIDEO")
    print("=" * 70)

    # Output directories
    output_dir = project_root / "data" / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Generate script
    print("\n[1/4] Generating script...")
    agent = ScriptwriterAgent()

    # Query for PLC basics
    atoms = agent.query_atoms("PLC", limit=3)

    if not atoms:
        print("[ERROR] No atoms found for topic 'PLC'")
        return False

    # Generate script
    script = agent.generate_script("Introduction to PLCs", atoms)
    script = agent.add_personality_markers(script)
    script = agent.add_visual_cues(script)

    print(f"[OK] Script generated ({script['word_count']} words, {script['estimated_duration_seconds']}s)")

    # Save script
    script_path = output_dir / f"script_{timestamp}.txt"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script['full_script'])
    print(f"[OK] Script saved: {script_path}")

    # Step 2: Generate audio
    audio_path = output_dir / f"audio_{timestamp}.mp3"

    # Clean script text for TTS (remove markers)
    clean_text = script['full_script']
    markers = ['[enthusiastic]', '[explanatory]', '[cautionary]', '[pause]',
               '[emphasize]', '[show title:', '[show diagram:', '[show code:',
               '[show table]', '[show citation:', ']']
    for marker in markers:
        clean_text = clean_text.replace(marker, '')

    await generate_audio(clean_text, audio_path, voice="en-US-GuyNeural")

    # Step 3: Create video
    video_path = output_dir / f"video_{timestamp}.mp4"
    create_video(script, audio_path, video_path)

    # Step 4: Summary
    print("\n" + "=" * 70)
    print("VIDEO CREATION COMPLETE!")
    print("=" * 70)
    print(f"\nScript: {script_path}")
    print(f"Audio:  {audio_path}")
    print(f"Video:  {video_path}")
    print(f"\nVideo details:")
    print(f"  Title: {script['title']}")
    print(f"  Duration: {script['estimated_duration_seconds']} seconds (~{script['estimated_duration_seconds']//60} min)")
    print(f"  Word count: {script['word_count']}")
    print(f"\nCitations:")
    for citation in script['citations']:
        print(f"  - {citation}")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Watch the video to validate quality")
    print("2. Upload to YouTube:")
    print(f"   - Title: {script['title']}")
    print("   - Description: Add citations from above")
    print("   - Tags: PLC, automation, industrial, tutorial")
    print("   - Visibility: Unlisted (for review)")
    print("3. If quality is good, generate 2 more videos")
    print("4. If quality needs work, adjust script templates")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
