"""
RIVET Pro Telegram Bot Handlers

Comprehensive conversation flows for monetizable troubleshooting service.

Features:
- Onboarding new users
- Troubleshooting Q&A with confidence scoring
- Subscription upgrades (Free → Pro → Enterprise)
- Expert booking flow
- Session history and exports

Commands:
- /start - Onboarding flow
- /troubleshoot - Start troubleshooting session
- /upgrade - Upgrade to Pro/Enterprise
- /book_expert - Schedule expert call
- /my_sessions - View troubleshooting history
- /export_session - Export session as PDF
- /pro_stats - View usage stats

Integrates with:
- intent_detector: Classify questions
- confidence_scorer: Quality gates and upsells
- Stripe: Payment processing
- Supabase: Session tracking
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from agent_factory.rivet_pro.intent_detector import IntentDetector, IntentType
from agent_factory.rivet_pro.confidence_scorer import ConfidenceScorer, AnswerAction
from agent_factory.rivet_pro.database import RIVETProDatabase
from agent_factory.integrations.telegram.conversation_manager import ConversationManager


class RIVETProHandlers:
    """
    Telegram handlers for RIVET Pro monetization features.

    Manages complete user journey from onboarding to troubleshooting
    to premium upgrades.

    Now with conversation memory for natural language intelligence!
    """

    def __init__(self):
        """Initialize handlers with dependencies"""
        self.intent_detector = IntentDetector()
        self.confidence_scorer = ConfidenceScorer()
        self.db = RIVETProDatabase()  # Uses DATABASE_PROVIDER from .env
        self.conversation_manager = ConversationManager(db=self.db)  # Phase 1: Memory

        # Stripe config (test mode)
        self.stripe_api_key = os.getenv("STRIPE_API_KEY", "")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

        # Pricing
        self.PRO_PRICE_MONTHLY = 29.00
        self.ENTERPRISE_PRICE_MONTHLY = 499.00
        self.EXPERT_CALL_PRICE_HOURLY = 75.00

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start command - Onboarding flow for new users.

        Creates user subscription record and explains tiers.
        """
        user = update.effective_user
        user_id = str(user.id)

        # Check if user exists
        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Welcome message
        welcome_text = f"""
👋 **Welcome to RIVET Pro!**

I'm your 24/7 industrial troubleshooting assistant, powered by **1,964+ validated maintenance atoms**.

🤖 **What I Can Do:**
• Answer troubleshooting questions instantly
• Analyze equipment photos (Field Eye vision)
• Connect you with expert technicians
• Export troubleshooting reports (PDF)

📊 **Your Plan:** {user_sub['tier'].upper()}

🆓 **Free Tier:**
• 5 questions/day
• AI-powered answers
• Community knowledge base

💼 **Pro Tier ($29/mo):**
• Unlimited questions
• Priority support
• Image analysis (Field Eye)
• Export reports (PDF)

🚀 **Ready to start?**

Try asking me something like:
• "Motor running hot and tripping"
• "VFD showing E210 fault"
• "How do I troubleshoot a PLC?"

Or use these commands:
/troubleshoot - Start troubleshooting
/upgrade - Upgrade to Pro
/help - See all commands
"""

        await update.message.reply_text(
            text=welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_troubleshoot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle troubleshooting questions (main conversation flow).

        Flow (ENHANCED with Phase 1 - Conversation Memory):
        1. Load conversation session (NEW)
        2. Detect intent with context awareness (ENHANCED)
        3. Check user tier and question limits
        4. Search knowledge base
        5. Score confidence
        6. Respond with answer + upsell if needed
        7. Save conversation history (NEW)
        """
        user = update.effective_user
        user_id = str(user.id)
        question = update.message.text

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # 🆕 Phase 1: Load conversation session
        session = self.conversation_manager.get_or_create_session(
            user_id=user_id,
            telegram_username=user.username
        )

        # Get user subscription
        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Check question limits
        can_ask, limit_message = await self._check_question_limit(user_sub)
        if not can_ask:
            # Question limit reached - show upgrade prompt
            await self._send_upgrade_prompt(update, trigger="question_limit")
            return

        # 🆕 Phase 1: Add user message to history
        self.conversation_manager.add_user_message(
            session,
            question,
            metadata={
                "telegram_message_id": update.message.message_id,
                "user_tier": user_sub["tier"]
            }
        )

        # 🆕 Phase 1: Get conversation context
        conv_context = self.conversation_manager.get_context(session)

        # Detect intent (now context-aware)
        intent = self.intent_detector.detect(question)

        # 🆕 Phase 1: Enhance intent with conversation context
        # If user says "what about bearings?" we know they're still talking about motors
        if conv_context.last_equipment_type and not intent.equipment_info.equipment_type:
            intent.equipment_info.equipment_type = conv_context.last_equipment_type

        # Handle non-troubleshooting intents
        if intent.intent_type == IntentType.BOOKING:
            await self._handle_booking_intent(update, context)
            return
        elif intent.intent_type == IntentType.ACCOUNT:
            await self._handle_account_intent(update, context)
            return

        # Search knowledge base
        matched_atoms = await self._search_knowledge_base(
            question=question,
            equipment_type=intent.equipment_info.equipment_type,
            keywords=intent.keywords,
        )

        # Score confidence
        quality = self.confidence_scorer.score_answer(
            question=question,
            matched_atoms=matched_atoms,
            user_tier=user_sub["tier"],
            questions_today=user_sub["questions_today"],
            daily_limit=user_sub["daily_limit"],
            intent_data=intent.to_dict(),
        )

        # Create troubleshooting session
        session_id = await self._create_troubleshooting_session(
            user_id=user_id,
            question=question,
            intent=intent,
            quality=quality,
            matched_atoms=matched_atoms,
        )

        # Increment question count
        await self._increment_question_count(user_id)

        # Handle response based on confidence
        bot_response = ""
        if quality.answer_action == AnswerAction.AUTO_RESPOND:
            # High confidence - send answer
            bot_response = await self._send_answer(update, question, matched_atoms, intent, quality)

        elif quality.answer_action == AnswerAction.SUGGEST_UPGRADE:
            # Medium confidence - send answer + upsell
            bot_response = await self._send_answer(update, question, matched_atoms, intent, quality)
            if quality.should_upsell:
                await self._send_upsell(update, quality)

        elif quality.answer_action == AnswerAction.REQUIRE_EXPERT:
            # Low confidence - suggest expert call
            bot_response = await self._send_expert_required(update, question, intent, quality)

        # 🆕 Phase 1: Save bot response to conversation history
        self.conversation_manager.add_bot_message(
            session,
            bot_response,
            metadata={
                "confidence": quality.overall_confidence,
                "intent_type": intent.intent_type.value,
                "equipment_type": intent.equipment_info.equipment_type,
                "atoms_used": len(matched_atoms),
                "session_id": session_id
            }
        )

        # 🆕 Phase 1: Persist conversation session to database
        self.conversation_manager.save_session(session)

        # Log conversion event
        await self._log_conversion_event(
            user_id=user_id,
            event_type="troubleshooting_question",
            trigger_context={
                "confidence": quality.overall_confidence,
                "intent_type": intent.intent_type.value,
                "urgency": intent.urgency_score,
            },
        )

    async def handle_upgrade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /upgrade command - Show upgrade options with payment links.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")
        current_tier = user_sub["tier"]

        if current_tier == "pro":
            await update.message.reply_text(
                "You're already on the Pro tier! 🎉\n\n"
                "Want to upgrade to Enterprise? Contact us at enterprise@rivetpro.com"
            )
            return

        # Create payment link (Stripe Checkout)
        payment_link = await self._create_stripe_checkout_link(user_id, "pro")

        upgrade_text = f"""
💼 **Upgrade to RIVET Pro**

**Current Plan:** {current_tier.upper()}

🚀 **Pro Benefits:**
• ✅ Unlimited questions/day
• ✅ Priority support (<1hr response)
• ✅ Image analysis (Field Eye)
• ✅ Export troubleshooting reports (PDF)
• ✅ Session history (unlimited)

**Price:** ${self.PRO_PRICE_MONTHLY}/month
**Billing:** Monthly, cancel anytime

[Upgrade Now]({payment_link})

Questions? Reply /help for support.
"""

        keyboard = [
            [InlineKeyboardButton("💳 Upgrade to Pro - $29/mo", url=payment_link)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upgrade")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=upgrade_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )

    async def handle_book_expert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /book_expert command - Expert marketplace and booking flow.
        """
        user = update.effective_user
        user_id = str(user.id)

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Get available experts
        experts = await self._get_available_experts()

        if not experts:
            await update.message.reply_text(
                "😔 No experts available right now.\n\n"
                "Join the waitlist: /waitlist"
            )
            return

        # Format expert list
        expert_text = "👨‍🔧 **Available Experts**\n\n"

        for i, expert in enumerate(experts[:5], 1):
            expert_text += (
                f"{i}. **{expert['name']}**\n"
                f"   ⭐ {expert['average_rating']:.1f}/5.0 ({expert['total_calls_completed']} calls)\n"
                f"   💰 ${expert['hourly_rate_usd']}/hr\n"
                f"   🔧 {', '.join(expert['specialties'][:3])}\n"
                f"   ⏰ Available: Now\n"
                f"   [Book]({self._create_booking_link(expert['id'])})\n\n"
            )

        expert_text += (
            "📅 **How it works:**\n"
            "1. Select an expert and time slot\n"
            "2. Pay securely via Stripe\n"
            "3. Join video call at scheduled time\n"
            "4. Receive post-call summary report\n\n"
            "Questions? Reply /help"
        )

        await update.message.reply_text(
            text=expert_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def handle_my_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /my_sessions command - Show user's troubleshooting history.
        """
        user = update.effective_user
        user_id = str(user.id)

        # Fetch recent sessions
        sessions = await self._get_user_sessions(user_id, limit=10)

        if not sessions:
            await update.message.reply_text(
                "No troubleshooting sessions yet.\n\n"
                "Ask me a question to get started!"
            )
            return

        # Format sessions
        session_text = f"📋 **Your Troubleshooting History** ({len(sessions)} sessions)\n\n"

        for i, session in enumerate(sessions, 1):
            status_emoji = "✅" if session.get("resolved") else "⏳"
            session_text += (
                f"{i}. {status_emoji} **{session.get('equipment_type', 'Unknown')}**\n"
                f"   Issue: {session['issue_description'][:60]}...\n"
                f"   Confidence: {session.get('confidence_score', 0):.0%}\n"
                f"   Date: {session['created_at'][:10]}\n"
                f"   [View Details](/session_{session['id']})\n\n"
            )

        session_text += "\n💡 Tip: Use /export_session to download PDF reports"

        await update.message.reply_text(
            text=session_text,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def handle_pro_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /pro_stats command - Show user's usage statistics.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Calculate stats
        total_sessions = await self._count_user_sessions(user_id)
        resolved_sessions = await self._count_resolved_sessions(user_id)
        avg_confidence = await self._calc_avg_confidence(user_id)

        stats_text = f"""
📊 **Your RIVET Pro Stats**

**Subscription:**
• Tier: {user_sub['tier'].upper()}
• Member since: {user_sub['created_at'][:10]}
• Status: {'Active ✅' if user_sub['is_active'] else 'Inactive ❌'}

**Usage This Month:**
• Questions asked: {user_sub['questions_this_month']}
• Questions today: {user_sub['questions_today']}/{user_sub['daily_limit']}
• Total sessions: {total_sessions}
• Resolved: {resolved_sessions} ({(resolved_sessions/max(1, total_sessions)*100):.0f}%)

**Quality:**
• Average confidence: {avg_confidence:.0%}

**Next Renewal:** {user_sub.get('renews_at', 'N/A')[:10]}

Need help? Reply /help
"""

        await update.message.reply_text(
            text=stats_text,
            parse_mode=ParseMode.MARKDOWN,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_or_create_user(self, user_id: str, username: str) -> Dict[str, Any]:
        """Get or create user subscription record"""
        try:
            # Check if user exists
            user = self.db.get_user(user_id)

            if user:
                return user

            # Create new user
            user = self.db.create_user(
                user_id=user_id,
                telegram_user_id=int(user_id),
                telegram_username=username,
                tier="free",
                daily_limit=5,
                questions_today=0,
                questions_this_month=0,
                is_active=True,
                signup_source="telegram"
            )
            return user

        except Exception as e:
            print(f"Error getting/creating user: {e}")
            # Return default
            return {
                "user_id": user_id,
                "tier": "free",
                "daily_limit": 5,
                "questions_today": 0,
                "questions_this_month": 0,
            }

    async def _check_question_limit(self, user_sub: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Check if user can ask another question"""
        if user_sub["tier"] in ["pro", "enterprise"]:
            return True, None

        if user_sub["questions_today"] >= user_sub["daily_limit"]:
            return False, f"Daily limit reached ({user_sub['daily_limit']} questions/day)"

        return True, None

    async def _increment_question_count(self, user_id: str):
        """Increment user's question count"""
        try:
            self.db.increment_question_count(user_id)
        except Exception as e:
            print(f"Error incrementing question count: {e}")

    async def _search_knowledge_base(
        self,
        question: str,
        equipment_type: Optional[str],
        keywords: list,
    ) -> list:
        """Search knowledge base for relevant atoms"""
        try:
            # TODO: Implement actual vector search
            # For now, return mock atoms
            return [
                {
                    "atom_id": "mock_001",
                    "title": "Motor Overheating Diagnosis",
                    "similarity": 0.92,
                    "equipment_type": equipment_type or "motor",
                    "human_verified": True,
                    "citations": ["https://oem-manual.com"],
                    "symptoms": ["overheating", "tripping"],
                    "summary": "Motors overheat due to bearing wear, insufficient cooling, or overloading.",
                }
            ]
        except Exception as e:
            print(f"Error searching KB: {e}")
            return []

    async def _create_troubleshooting_session(
        self,
        user_id: str,
        question: str,
        intent: Any,
        quality: Any,
        matched_atoms: list,
    ) -> str:
        """Create troubleshooting session record"""
        try:
            session = self.db.create_session(
                user_id=user_id,
                issue_description=question,
                equipment_type=intent.equipment_info.equipment_type,
                equipment_manufacturer=intent.equipment_info.manufacturer,
                equipment_model=intent.equipment_info.model,
                fault_codes=intent.equipment_info.fault_codes,
                urgency_score=intent.urgency_score,
                confidence_score=quality.overall_confidence,
                status="open",
                matched_atoms=[atom.get("atom_id") for atom in matched_atoms],
                atoms_used_count=len(matched_atoms)
            )
            return str(session["id"])

        except Exception as e:
            print(f"Error creating session: {e}")
            return "mock_session_id"

    async def _send_answer(self, update: Update, question: str, atoms: list, intent: Any, quality: Any) -> str:
        """Send AI-generated answer to user and return the text"""
        # Format answer from atoms
        answer_text = f"🔍 **Analysis Complete**\n\nConfidence: {quality.overall_confidence:.0%}\n\n"

        if atoms:
            answer_text += f"**Top {len(atoms[:3])} Matches:**\n\n"
            for i, atom in enumerate(atoms[:3], 1):
                answer_text += (
                    f"{i}. **{atom.get('title', 'Unknown')}**\n"
                    f"   {atom.get('summary', '')[:100]}...\n"
                    f"   Relevance: {atom.get('similarity', 0):.0%}\n\n"
                )

            answer_text += "\n💡 Need more details? Ask a follow-up question!"
        else:
            answer_text += "😔 No exact matches found.\n\nTry rephrasing or /book_expert for live help."

        await update.message.reply_text(
            text=answer_text,
            parse_mode=ParseMode.MARKDOWN,
        )

        return answer_text  # Return for conversation history

    async def _send_upsell(self, update: Update, quality: Any):
        """Send upsell message based on quality assessment"""
        if not quality.upsell_message:
            return

        await update.message.reply_text(
            text=quality.upsell_message,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def _send_expert_required(self, update: Update, question: str, intent: Any, quality: Any) -> str:
        """Send expert call required message and return the text"""
        message = f"""
⚠️ **Complex Issue Detected**

Confidence: {quality.overall_confidence:.0%}
Urgency: {intent.urgency_score}/10

This appears to require expert assistance.

📞 **Book Expert Call** - $75/hour
• Real-time video support
• 30-60 minute sessions
• Post-call summary report

[Book Now](/book_expert) [Try AI Answer Anyway](/force_answer)
"""

        await update.message.reply_text(
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

        return message  # Return for conversation history

    async def _send_upgrade_prompt(self, update: Update, trigger: str):
        """Send upgrade prompt when limits reached"""
        message = """
🚫 **Daily Question Limit Reached**

You've used all 5 free questions today.

💼 **Upgrade to Pro** for:
• Unlimited questions/day
• Priority support
• Image analysis
• PDF exports

**Only $29/month** - Cancel anytime

[Upgrade Now](/upgrade)
"""

        await update.message.reply_text(
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def _get_available_experts(self) -> list:
        """Fetch available experts from database"""
        try:
            experts = self.db.get_available_experts(specialty=None)
            return experts or []
        except Exception as e:
            print(f"Error fetching experts: {e}")
            return []

    async def _get_user_sessions(self, user_id: str, limit: int = 10) -> list:
        """Fetch user's troubleshooting sessions"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit)
            return sessions or []
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    async def _count_user_sessions(self, user_id: str) -> int:
        """Count total sessions for user"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit=1000)  # Get all
            return len(sessions)
        except Exception as e:
            return 0

    async def _count_resolved_sessions(self, user_id: str) -> int:
        """Count resolved sessions for user"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit=1000)
            return len([s for s in sessions if s.get("resolved")])
        except Exception as e:
            return 0

    async def _calc_avg_confidence(self, user_id: str) -> float:
        """Calculate average confidence for user's sessions"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit=1000)
            scores = [s["confidence_score"] for s in sessions if s.get("confidence_score")]
            return sum(scores) / len(scores) if scores else 0.0
        except Exception as e:
            return 0.0

    async def _create_stripe_checkout_link(self, user_id: str, tier: str) -> str:
        """Create Stripe Checkout session link"""
        # TODO: Implement actual Stripe integration
        return f"https://rivetpro.com/checkout?user={user_id}&tier={tier}"

    def _create_booking_link(self, expert_id: str) -> str:
        """Create expert booking link"""
        # TODO: Implement actual booking system (Calendly/Cal.com integration)
        return f"https://rivetpro.com/book?expert={expert_id}"

    async def _log_conversion_event(self, user_id: str, event_type: str, trigger_context: Dict[str, Any]):
        """Log conversion event for analytics"""
        try:
            user = self.db.get_user(user_id)
            current_tier = user["tier"] if user else "free"

            self.db.track_conversion_event(
                user_id=user_id,
                event_type=event_type,
                converted=False,
                telegram_user_id=int(user_id),
                current_tier=current_tier,
                trigger_context=trigger_context
            )
        except Exception as e:
            print(f"Error logging conversion event: {e}")

    async def _handle_booking_intent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle booking intent from natural language"""
        await update.message.reply_text(
            "I see you want to book an expert call!\n\n"
            "Use /book_expert to see available experts."
        )

    async def _handle_account_intent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle account management intent"""
        await update.message.reply_text(
            "Account management:\n\n"
            "/upgrade - Upgrade subscription\n"
            "/pro_stats - View your stats\n"
            "/cancel - Cancel subscription"
        )


# Singleton instance
rivet_pro_handlers = RIVETProHandlers()


# Export handler functions for registration
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rivet_pro_handlers.handle_start(update, context)


async def handle_troubleshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rivet_pro_handlers.handle_troubleshoot(update, context)


async def handle_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rivet_pro_handlers.handle_upgrade(update, context)


async def handle_book_expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rivet_pro_handlers.handle_book_expert(update, context)


async def handle_my_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rivet_pro_handlers.handle_my_sessions(update, context)


async def handle_pro_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rivet_pro_handlers.handle_pro_stats(update, context)
