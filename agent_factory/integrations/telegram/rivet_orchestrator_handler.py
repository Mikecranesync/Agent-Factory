"""
RivetOrchestrator Telegram Handler

Integrates RivetOrchestrator with Telegram bot for intelligent industrial
maintenance troubleshooting. Routes queries through 4-route system (A/B/C/D)
and formats responses with citations, suggested actions, and safety warnings.

Author: Agent Factory
Created: 2025-12-22
Phase: Integration
"""

from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional
import logging

from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import (
    create_text_request,
    ChannelType,
    RivetResponse,
    RouteType
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize orchestrator once at module level
try:
    orchestrator = RivetOrchestrator()
    logger.info("RivetOrchestrator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RivetOrchestrator: {e}")
    orchestrator = None


async def rivet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /rivet command - route through RivetOrchestrator.

    Routes user queries through the 4-route intelligent routing system:
    - Route A: Strong KB coverage → Direct answer
    - Route B: Thin KB coverage → Answer + enrichment
    - Route C: No KB coverage → Research pipeline
    - Route D: Unclear intent → Clarification questions

    Usage:
        /rivet <your industrial maintenance question>

    Examples:
        /rivet My Siemens G120C shows F3002 fault
        /rivet How do I wire a 3-phase motor?
        /rivet troubleshoot Allen-Bradley ControlLogix PLC
        /rivet What is LOTO procedure?

    Args:
        update: Telegram update object
        context: Telegram context with args

    Returns:
        None - sends formatted response back to user
    """
    # Check if orchestrator is available
    if orchestrator is None:
        await update.message.reply_text(
            "**WARNING:** RivetOrchestrator is not available. Please contact support."
        )
        logger.error("Attempted to use /rivet but orchestrator not initialized")
        return

    # Extract user info
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"

    # Extract query from command args
    query = " ".join(context.args) if context.args else ""

    # Validate query
    if not query or len(query.strip()) < 3:
        await update.message.reply_text(
            "**RIVET Troubleshooting Assistant**\n\n"
            "Usage: `/rivet <your question>`\n\n"
            "Examples:\n"
            "- `/rivet My Siemens G120C shows F3002 fault`\n"
            "- `/rivet How to troubleshoot motor won't start`\n"
            "- `/rivet Allen-Bradley PLC fault code 0x1234`\n"
            "- `/rivet What is LOTO procedure?`\n\n"
            "I'll analyze your question, search our knowledge base, and provide "
            "detailed troubleshooting steps with citations.",
            parse_mode="Markdown"
        )
        return

    # Send "typing" indicator
    await update.message.chat.send_action("typing")

    logger.info(f"Processing /rivet query from user {user_id} ({username}): {query}")

    try:
        # Create RivetRequest
        request = create_text_request(
            user_id=f"telegram_{user_id}",
            text=query,
            channel=ChannelType.TELEGRAM,
            username=username
        )

        # Route through orchestrator
        response = await orchestrator.route_query(request)

        # Format response for Telegram
        formatted_text = _format_response(response)

        # Send to user
        await update.message.reply_text(formatted_text, parse_mode="Markdown")

        logger.info(
            f"Successfully processed /rivet query for user {user_id}. "
            f"Route: {response.route_taken.value}, Confidence: {response.confidence:.2f}"
        )

    except Exception as e:
        logger.error(f"Error processing /rivet query: {e}", exc_info=True)
        await update.message.reply_text(
            "**ERROR:** An error occurred processing your request.\n\n"
            f"Error: {str(e)}\n\n"
            "Please try rephrasing your question or contact support if the issue persists.",
            parse_mode="Markdown"
        )


def _format_response(response: RivetResponse) -> str:
    """
    Format RivetResponse for Telegram display.

    Converts structured RivetResponse into user-friendly Markdown format with:
    - Safety warnings (prepended if present)
    - Main answer text
    - Suggested actions (numbered steps)
    - Citations/sources (bulleted links)
    - Route metadata (for transparency)

    Args:
        response: RivetResponse from orchestrator

    Returns:
        str: Markdown-formatted text for Telegram

    Example Output:
        ⚠️ SAFETY WARNING:
        - Lockout/tagout required before opening motor control center

        F3002 is DC bus overvoltage on Siemens G120C. Check input voltage...

        ✅ Steps to resolve:
        1. Check input voltage with multimeter
        2. Verify parameter P0210 = 480V
        3. Check DC bus voltage on display

        📚 Sources:
        - https://support.siemens.com/manual/G120C

        Route: A_direct_sme | Confidence: 89%
    """
    # Start with main answer text
    text = response.text

    # Prepend safety warnings (CRITICAL - must be visible first)
    if response.safety_warnings:
        warnings = "**SAFETY WARNING:**\n"
        for warning in response.safety_warnings:
            warnings += f"- {warning}\n"
        text = warnings + "\n" + text

    # Add suggested actions (numbered steps)
    if response.suggested_actions:
        text += "\n\n**Steps to resolve:**\n"
        for i, action in enumerate(response.suggested_actions, 1):
            text += f"{i}. {action}\n"

    # Add citations (bulleted links)
    if response.links:
        text += "\n\n**Sources:**\n"
        for link in response.links:
            text += f"- {link}\n"

    # Add route metadata (for transparency and debugging)
    route_name = response.route_taken.value
    confidence_pct = int(response.confidence * 100)
    text += f"\n\n_Route: {route_name} | Confidence: {confidence_pct}%_"

    # Add special notices for Route B/C
    if response.kb_enrichment_triggered:
        text += "\n\n_NOTE: Our team is enriching the knowledge base with this topic for better future answers._"

    if response.research_triggered:
        text += "\n\n_NOTE: Research pipeline triggered. Expect detailed response in 24-48 hours._"

    return text


def _is_technical_query(text: str) -> bool:
    """
    Detect if message is technical/industrial question.

    Used for optional automatic routing (future enhancement).
    Checks for industrial maintenance keywords without requiring /rivet command.

    Args:
        text: User message text

    Returns:
        bool: True if message looks like technical query

    Example:
        >>> _is_technical_query("My motor won't start")
        True
        >>> _is_technical_query("Hello, how are you?")
        False
    """
    technical_keywords = [
        # Fault/troubleshooting
        "fault", "error", "troubleshoot", "fix", "repair", "diagnose",
        "won't start", "won't run", "not working", "trip", "trips",

        # Equipment vendors
        "siemens", "rockwell", "allen-bradley", "abb", "schneider",
        "mitsubishi", "omron", "ge", "eaton", "automation direct",

        # Equipment types
        "motor", "plc", "vfd", "hmi", "contactor", "breaker",
        "sensor", "encoder", "servo", "relay", "drive",

        # Industrial actions
        "wire", "wiring", "install", "startup", "commission",
        "parameter", "program", "configure", "setup",

        # Safety
        "loto", "lockout", "tagout", "arc flash", "safety"
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in technical_keywords)
