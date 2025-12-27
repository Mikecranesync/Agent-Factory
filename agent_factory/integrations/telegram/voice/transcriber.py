"""Whisper-based speech-to-text transcription for voice messages."""

import os
from pathlib import Path
from typing import Optional

from openai import OpenAI


class WhisperTranscriber:
    """
    Handles voice message transcription using OpenAI's Whisper model.

    Attributes:
        client: OpenAI API client
        model: Whisper model name (default: whisper-1)
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        Initialize Whisper transcriber.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Whisper model to use
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    async def transcribe(self, audio_path: Path, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file (supports OGG, WAV, MP3, etc.)
            language: Optional language code (e.g., 'en', 'es') for better accuracy

        Returns:
            Transcribed text

        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_path, "rb") as audio_file:
                # Whisper API accepts various formats directly (OGG, WAV, MP3, etc.)
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": "text"
                }

                # Add language if specified for better accuracy
                if language:
                    kwargs["language"] = language

                response = self.client.audio.transcriptions.create(**kwargs)

            return response.strip()

        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}") from e

    async def transcribe_with_timestamps(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio with word-level timestamps.

        Args:
            audio_path: Path to audio file
            language: Optional language code

        Returns:
            Dict with 'text' and 'segments' (timestamp data)
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_path, "rb") as audio_file:
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": "verbose_json"  # Returns timestamps
                }

                if language:
                    kwargs["language"] = language

                response = self.client.audio.transcriptions.create(**kwargs)

            return {
                "text": response.text,
                "segments": response.segments if hasattr(response, "segments") else []
            }

        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}") from e
