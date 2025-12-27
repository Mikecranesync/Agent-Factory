"""Audio format conversion utilities for voice messages."""

import subprocess
from pathlib import Path
from typing import Optional


class AudioConverter:
    """Handles audio format conversion, primarily OGG to WAV for Whisper."""

    @staticmethod
    def ogg_to_wav(input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Convert OGG audio file to WAV format using ffmpeg.

        Args:
            input_path: Path to input OGG file
            output_path: Path for output WAV file (optional, defaults to same name with .wav)

        Returns:
            Path to converted WAV file

        Raises:
            RuntimeError: If ffmpeg conversion fails
        """
        if output_path is None:
            output_path = input_path.with_suffix('.wav')

        try:
            # Use ffmpeg for conversion
            subprocess.run([
                'ffmpeg',
                '-i', str(input_path),
                '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
                '-ar', '16000',  # 16kHz sample rate (Whisper optimal)
                '-ac', '1',  # Mono channel
                str(output_path)
            ], check=True, capture_output=True)

            return output_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg conversion failed: {e.stderr.decode()}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Please install ffmpeg: "
                "https://ffmpeg.org/download.html"
            )

    @staticmethod
    def cleanup_audio_files(*paths: Path) -> None:
        """Delete audio files after processing."""
        for path in paths:
            if path and path.exists():
                path.unlink(missing_ok=True)
