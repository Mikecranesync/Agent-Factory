# HARVEST BLOCK 23: Voice Handler

**Priority**: LOW
**Size**: 12.92KB (389 lines total across 3 files)
**Source**: `agent_factory/integrations/telegram/voice/` (handler.py, transcriber.py, audio_utils.py)
**Target**: `rivet/integrations/telegram/voice/`

---

## Overview

Telegram voice message processing pipeline - downloads OGG audio, transcribes via OpenAI Whisper, detects intent, and routes to appropriate handlers for hands-free troubleshooting support.

### What This Adds

- **Speech-to-text**: OpenAI Whisper API transcription (supports OGG, WAV, MP3)
- **Multi-language support**: Language parameter for better accuracy
- **Intent detection**: Voice → text → intent classification → routing
- **Schematic Q&A**: Voice questions about uploaded prints/schematics
- **Conversation integration**: Voice messages added to conversation history
- **Typing indicators**: Shows "typing..." while processing
- **Error handling**: User-friendly error messages with fallback prompts

### Key Features

```python
from rivet.integrations.telegram.voice.handler import VoiceHandler
from rivet.integrations.telegram.voice.transcriber import WhisperTranscriber

# Initialize transcriber
transcriber = WhisperTranscriber(api_key="sk-...")

# Initialize voice handler
voice_handler = VoiceHandler(
    transcriber=transcriber,
    intent_detector=intent_detector,
    conversation_manager=conversation_manager,
    rivet_handlers=rivet_handlers
)

# Register Telegram handler
application.add_handler(MessageHandler(
    filters.VOICE,
    voice_handler.handle_voice
))

# Flow:
# 1. User sends voice message (OGG from Telegram)
# 2. Download → Transcribe → "🎤 I heard: '...'"
# 3. Detect intent → Route to troubleshooting/info/booking
# 4. Add to conversation history
# 5. Cleanup temp files
```

---

## Whisper Transcription

```python
from rivet.integrations.telegram.voice.transcriber import WhisperTranscriber

# Initialize transcriber
transcriber = WhisperTranscriber(
    api_key="sk-...",  # Defaults to OPENAI_API_KEY env var
    model="whisper-1"
)

# Basic transcription (text only)
text = await transcriber.transcribe(
    audio_path=Path("voice.ogg"),
    language="en"  # Optional, improves accuracy
)
# Returns: "How do I reset the fault code on my PowerFlex 525?"

# Transcription with timestamps (verbose mode)
result = await transcriber.transcribe_with_timestamps(
    audio_path=Path("voice.ogg")
)
# Returns: {
#   "text": "How do I reset the fault code...",
#   "segments": [{"start": 0.0, "end": 1.5, "text": "How do I"}]
# }
```

---

## Voice Message Flow

```python
# Full voice handling pipeline

async def handle_voice(update, context):
    # 1. Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    # 2. Download voice message to temp file
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        audio_path = Path(tmp.name)

    # 3. Transcribe using Whisper
    transcribed_text = await transcriber.transcribe(audio_path)

    # 4. Acknowledge transcription
    await update.message.reply_text(
        f"🎤 I heard: \"{transcribed_text}\"\n\n"
        "Processing your request..."
    )

    # 5. Detect intent
    intent = await intent_detector.detect(transcribed_text)

    # 6. Add to conversation history
    conversation_manager.add_message(
        user_id=user_id,
        role="user",
        content=transcribed_text,
        metadata={"source": "voice", "intent": intent.to_dict()}
    )

    # 7. Route based on intent
    if intent.intent_type == IntentType.TROUBLESHOOTING:
        await rivet_handlers.handle_troubleshooting_question(
            update, context, question=transcribed_text, intent=intent
        )
    elif intent.intent_type == IntentType.INFORMATION:
        await rivet_handlers.handle_information_query(...)
    # ... other intent types

    # 8. Cleanup temp files
    AudioConverter.cleanup_audio_files(audio_path)
```

---

## Schematic Voice Q&A

```python
# Ask voice question about uploaded schematic/print

async def handle_voice_question_followup(update, context, print_path):
    """
    User uploads schematic image, then asks voice question about it.
    Example: [uploads electrical schematic] → 🎤 "What's this symbol?"
    """

    # Download and transcribe voice
    question = await transcriber.transcribe(audio_path)

    # Analyze schematic with voice question
    if print_path or context.user_data.get("current_print"):
        from rivet.rivet_pro.print_analyzer import PrintAnalyzer

        analyzer = PrintAnalyzer()
        answer = await analyzer.answer_question(print_path, question)

        await update.message.reply_text(
            f"🎤 Question: \"{question}\"\n\n"
            f"📊 Answer:\n{answer}"
        )
```

---

## Audio Format Conversion

```python
from rivet.integrations.telegram.voice.audio_utils import AudioConverter

# Convert OGG to WAV (optional - Whisper supports OGG directly)
wav_path = AudioConverter.ogg_to_wav(
    input_path=Path("voice.ogg"),
    output_path=Path("voice.wav")  # Optional, defaults to same name
)

# Requires ffmpeg installed
# Converts to: PCM 16-bit, 16kHz, mono (Whisper optimal settings)

# Cleanup after processing
AudioConverter.cleanup_audio_files(voice_ogg, voice_wav)
```

---

## Dependencies

```bash
# Install required packages
poetry add openai python-telegram-bot

# Optional: ffmpeg for audio conversion (not required, Whisper supports OGG)
# Windows: Download from https://ffmpeg.org/download.html
# Linux: sudo apt install ffmpeg
# macOS: brew install ffmpeg
```

## Environment Variables

```bash
export OPENAI_API_KEY=sk-...  # For Whisper transcription
```

---

## Quick Implementation Guide

1. Copy source directory: `cp -r agent_factory/integrations/telegram/voice/ rivet/integrations/telegram/voice/`
2. Install: `poetry add openai python-telegram-bot`
3. Set env var: `export OPENAI_API_KEY=sk-...`
4. Validate: `python -c "from rivet.integrations.telegram.voice import VoiceHandler; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.integrations.telegram.voice.handler import VoiceHandler; print('OK')"
python -c "from rivet.integrations.telegram.voice.transcriber import WhisperTranscriber; print('OK')"

# Test transcriber (requires API key)
python -c "
from rivet.integrations.telegram.voice.transcriber import WhisperTranscriber
import asyncio

async def test():
    transcriber = WhisperTranscriber()
    # Note: Requires actual audio file to test
    print('Transcriber initialized OK')

asyncio.run(test())
"
```

---

## Integration Notes

**Telegram Bot Integration**:
```python
from telegram.ext import Application, MessageHandler, filters
from rivet.integrations.telegram.voice.handler import VoiceHandler

# Initialize voice handler
voice_handler = VoiceHandler(
    transcriber=WhisperTranscriber(),
    intent_detector=intent_detector,
    conversation_manager=conversation_manager,
    rivet_handlers=rivet_handlers
)

# Add to Telegram application
application.add_handler(MessageHandler(
    filters.VOICE,
    voice_handler.handle_voice
))

# Schematic followup handler (optional)
application.add_handler(MessageHandler(
    filters.VOICE & filters.REPLY,  # Voice reply to schematic
    voice_handler.handle_voice_question_followup
))
```

**Cost**: ~$0.006 per minute of audio (Whisper API pricing)

**Performance**:
- Download: <1s (depends on network)
- Transcription: 2-5s (Whisper API)
- Total latency: 3-7s for typical voice message

---

## What This Enables

- ✅ Hands-free troubleshooting (voice queries supported)
- ✅ Multi-language support (Whisper handles 50+ languages)
- ✅ Schematic Q&A (voice questions about uploaded prints)
- ✅ Conversation continuity (voice messages in history)
- ✅ Intent-based routing (voice → text → intent → handler)
- ✅ User feedback (echoes transcription for confirmation)
- ✅ Error handling (graceful fallback to text prompts)

---

## Next Steps

After implementing HARVEST 23, proceed to **HARVEST 24: Atlas Client** for Atlas CMMS system integration.

SEE FULL SOURCE:
- `agent_factory/integrations/telegram/voice/handler.py` (227 lines)
- `agent_factory/integrations/telegram/voice/transcriber.py` (106 lines)
- `agent_factory/integrations/telegram/voice/audio_utils.py` (56 lines)
