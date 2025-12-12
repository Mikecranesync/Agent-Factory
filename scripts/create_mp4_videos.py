#!/usr/bin/env python3
"""
Create MP4 videos from existing audio + slides

Uses imageio-ffmpeg (already installed with MoviePy)
"""

import sys
from pathlib import Path
from imageio_ffmpeg import write_frames

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image
import subprocess


def create_mp4(slide_path: Path, audio_path: Path, output_path: Path):
    """Create MP4 from single slide + audio using imageio-ffmpeg"""
    print(f"Creating {output_path.name}...")

    # Get imageio's ffmpeg
    from imageio_ffmpeg import get_ffmpeg_exe
    ffmpeg_exe = get_ffmpeg_exe()

    # Create video with static image + audio
    subprocess.run([
        ffmpeg_exe, "-y",
        "-loop", "1",
        "-i", str(slide_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-t", "300",  # Max 5 min
        str(output_path)
    ], check=True, capture_output=True)

    print(f"[OK] {output_path}")


def main():
    """Create MP4s for all generated videos"""
    videos_dir = project_root / "data" / "videos"

    # Find all video directories
    video_dirs = [d for d in videos_dir.iterdir() if d.is_dir() and d.name.startswith("video_")]

    print("=" * 70)
    print(f"CREATING MP4 VIDEOS")
    print("=" * 70)
    print(f"\nFound {len(video_dirs)} video directories\n")

    for video_dir in sorted(video_dirs)[-3:]:  # Last 3 videos
        print(f"\n{video_dir.name}:")

        audio_path = video_dir / "audio.mp3"
        script_path = video_dir / "script.txt"
        title_slide = video_dir / "slide_title.png"

        if not audio_path.exists():
            print(f"  [SKIP] No audio found")
            continue

        if not title_slide.exists():
            print(f"  [SKIP] No slides found")
            continue

        # Read title from script
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract title (first line or search for pattern)
            title = "Video"
            for line in content.split('\n'):
                if line.strip() and not line.startswith('['):
                    title = line.strip()[:50]  # First non-marker line
                    break

        # Create MP4
        output_path = video_dir / f"{title.replace(' ', '_').replace(':', '')}.mp4"

        try:
            create_mp4(title_slide, audio_path, output_path)
        except Exception as e:
            print(f"  [ERROR] {e}")

    print("\n" + "=" * 70)
    print("MP4 CREATION COMPLETE")
    print("=" * 70)
    print(f"\nVideos ready in: {videos_dir}")
    print("\nNext: Upload to YouTube and review!")


if __name__ == "__main__":
    main()
