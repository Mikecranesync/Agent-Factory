"""Voice message handler for Telegram bot."""

import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from agent_factory.integrations.telegram.voice.transcriber import WhisperTranscriber
from agent_factory.integrations.telegram.voice.audio_utils import AudioConverter
from agent_factory.rivet_pro.intent_detector import IntentDetector


class VoiceHandler:
    """
    Handles voice messages in Telegram bot.

    Flow:
    1. Download voice message (OGG format from Telegram)
    2. Transcribe using Whisper
    3. Acknowledge transcription to user
    4. Pass text to intent detector
    5. Route to appropriate handler
    """

    def __init__(
        self,
        transcriber: WhisperTranscriber,
        intent_detector: IntentDetector,
        conversation_manager,  # ConversationManager
        rivet_handlers  # RIVETProHandlers
    ):
        """
        Initialize voice handler.

        Args:
            transcriber: Whisper transcriber instance
            intent_detector: Intent detection service
            conversation_manager: Multi-turn conversation manager
            rivet_handlers: RIVET Pro handlers for routing
        """
        self.transcriber = transcriber
        self.intent_detector = intent_detector
        self.conversation_manager = conversation_manager
        self.rivet_handlers = rivet_handlers

    async def handle_voice(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle incoming voice message.

        Args:
            update: Telegram update with voice message
            context: Telegram context
        """
        voice = update.message.voice
        user_id = update.effective_user.id

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        audio_path: Optional[Path] = None

        try:
            # Download voice file to temp directory
            file = await context.bot.get_file(voice.file_id)

            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                await file.download_to_drive(tmp.name)
                audio_path = Path(tmp.name)

            # Transcribe using Whisper
            # Note: Whisper supports OGG directly, no conversion needed
            transcribed_text = await self.transcriber.transcribe(audio_path)

            if not transcribed_text:
                await update.message.reply_text(
                    "🎤 Sorry, I couldn't understand the audio. "
                    "Please try again or send a text message."
                )
                return

            # Acknowledge transcription to user
            await update.message.reply_text(
                f"🎤 I heard: \"{transcribed_text}\"\n\n"
                "Processing your request..."
            )

            # Detect intent from transcribed text
            intent = await self.intent_detector.detect(transcribed_text)

            # Add to conversation history
            self.conversation_manager.add_message(
                user_id=user_id,
                role="user",
                content=transcribed_text,
                metadata={"source": "voice", "intent": intent.to_dict()}
            )

            # Route based on intent type
            from agent_factory.rivet_pro.intent_detector import IntentType

            if intent.intent_type == IntentType.TROUBLESHOOTING:
                # Pass to troubleshooting handler
                await self.rivet_handlers.handle_troubleshooting_question(
                    update=update,
                    context=context,
                    question=transcribed_text,
                    intent=intent
                )

            elif intent.intent_type == IntentType.INFORMATION:
                # Knowledge base query
                await self.rivet_handlers.handle_information_query(
                    update=update,
                    context=context,
                    question=transcribed_text
                )

            elif intent.intent_type == IntentType.BOOKING:
                # Expert booking flow
                await update.message.reply_text(
                    "📞 I see you want to book an expert call. "
                    "Use /book_expert to schedule a session."
                )

            elif intent.intent_type == IntentType.ACCOUNT:
                # Account management
                await update.message.reply_text(
                    "⚙️ For account management, use:\n"
                    "/upgrade - Upgrade subscription\n"
                    "/pro_stats - View usage stats\n"
                    "/my_sessions - View history"
                )

            else:
                # Unknown intent - ask for clarification
                await update.message.reply_text(
                    "🤔 I'm not sure what you need help with. "
                    "Could you rephrase that? Or try:\n"
                    "/troubleshoot - Technical support\n"
                    "/book_expert - Schedule expert call"
                )

        except Exception as e:
            # Log error and notify user
            print(f"Voice handler error: {str(e)}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error processing your voice message. "
                "Please try sending a text message instead."
            )

        finally:
            # Cleanup audio file
            if audio_path:
                AudioConverter.cleanup_audio_files(audio_path)

    async def handle_voice_question_followup(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        print_path: Optional[Path] = None
    ) -> None:
        """
        Handle voice question about an uploaded schematic/print.

        Args:
            update: Telegram update with voice message
            context: Telegram context
            print_path: Optional path to previously uploaded print/schematic
        """
        voice = update.message.voice
        user_id = update.effective_user.id

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        audio_path: Optional[Path] = None

        try:
            # Download and transcribe
            file = await context.bot.get_file(voice.file_id)

            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                await file.download_to_drive(tmp.name)
                audio_path = Path(tmp.name)

            question = await self.transcriber.transcribe(audio_path)

            # If there's a print in context, analyze it with the question
            if print_path or context.user_data.get("current_print"):
                from agent_factory.rivet_pro.print_analyzer import PrintAnalyzer

                analyzer = PrintAnalyzer()
                print_file = Path(print_path or context.user_data["current_print"])

                answer = await analyzer.answer_question(print_file, question)

                await update.message.reply_text(
                    f"🎤 Question: \"{question}\"\n\n"
                    f"📊 Answer:\n{answer}"
                )

            else:
                # No print context, treat as regular question
                await self.handle_voice(update, context)

        except Exception as e:
            print(f"Voice followup error: {str(e)}")
            await update.message.reply_text(
                "❌ Error processing voice question. Please try text instead."
            )

        finally:
            if audio_path:
                AudioConverter.cleanup_audio_files(audio_path)
