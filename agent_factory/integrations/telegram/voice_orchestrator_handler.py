"""
Voice Message Handler with RivetOrchestrator Integration

Transcribes voice messages using Whisper and routes them through the
RivetOrchestrator (same routing as text messages).

Flow:
1. Download voice message
2. Transcribe with Whisper
3. Route through RivetOrchestrator (A/B/C/D routes)
4. Return formatted response with citations

Author: Agent Factory
Created: 2025-12-27
Phase: WS-3 Integration
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
import tempfile
import logging
from pathlib import Path

from openai import AsyncOpenAI
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import create_text_request, ChannelType

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client for Whisper
try:
    import os
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI Whisper client initialized")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    openai_client = None

# Initialize orchestrator once at module level
try:
    orchestrator = RivetOrchestrator()
    logger.info("RivetOrchestrator initialized for voice handler")
except Exception as e:
    logger.error(f"Failed to initialize RivetOrchestrator: {e}")
    orchestrator = None


async def handle_voice_orchestrator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice messages using RivetOrchestrator routing.

    Flow:
    1. Download voice message → temp file
    2. Transcribe with Whisper
    3. Send acknowledgment with transcription
    4. Route through RivetOrchestrator (A/B/C/D)
    5. Return formatted response

    Args:
        update: Telegram update with voice message
        context: Telegram context
    """
    # Check dependencies
    if openai_client is None:
        await update.message.reply_text(
            "⚠️ Voice transcription is not available. Please use text messages."
        )
        return

    if orchestrator is None:
        await update.message.reply_text(
            "⚠️ RivetOrchestrator is not available. Please contact support."
        )
        return

    # Extract user info
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    voice = update.message.voice

    logger.info(f"Received voice message from user {user_id} ({username}), duration: {voice.duration}s")

    # Send processing message
    processing_msg = await update.message.reply_text("🎤 Processing your voice message...")

    try:
        # Step 1: Download voice file
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

        file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            audio_path = Path(tmp.name)

        logger.info(f"Downloaded voice file: {audio_path}")

        # Step 2: Transcribe with Whisper
        await processing_msg.edit_text("🎤 Transcribing audio...")

        with open(audio_path, 'rb') as audio_file:
            transcription = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )

        transcribed_text = transcription.text.strip()
        logger.info(f"Transcribed voice message: {transcribed_text[:100]}...")

        # Clean up temp file
        audio_path.unlink()

        # Step 3: Acknowledge transcription
        await processing_msg.edit_text(
            f"🎤 **I heard:** \"{transcribed_text}\"\n\n"
            f"_Analyzing your question..._",
            parse_mode="Markdown"
        )

        # Step 4: Route through RivetOrchestrator (same as text messages)
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

        request = create_text_request(
            user_id=f"telegram_{user_id}",
            text=transcribed_text,
            channel=ChannelType.TELEGRAM,
            username=username
        )

        response = await orchestrator.route_query(request)

        # Step 5: Format and send response (same formatting as rivet_orchestrator_handler)
        from agent_factory.integrations.telegram.rivet_orchestrator_handler import _format_response
        formatted_text = _format_response(response)

        # Send final response
        await update.message.reply_text(formatted_text, parse_mode="Markdown")

        logger.info(
            f"Successfully processed voice message for user {user_id}. "
            f"Route: {response.route_taken.value}, Confidence: {response.confidence:.2f}"
        )

    except Exception as e:
        logger.error(f"Error processing voice message: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ **Error processing voice message**\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again or use text messages.",
            parse_mode="Markdown"
        )
