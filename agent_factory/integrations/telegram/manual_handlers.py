"""
Telegram handlers for OEM manual upload and search.

Commands:
- /upload_manual - Upload OEM manual PDF
- /manual_search <query> - Search equipment manuals
- /manual_list [manufacturer] [family] - List indexed manuals
- /manual_gaps - Show top requested missing manuals

Backend:
- Uses ManualIndexer for PDF indexing
- Uses ManualSearchService for vector search
- Shared knowledge base across all users
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from agent_factory.rivet_pro.database import RIVETProDatabase
from agent_factory.knowledge.manual_indexer import ManualIndexer
from agent_factory.knowledge.manual_search import ManualSearchService

logger = logging.getLogger(__name__)


# =============================================================================
# Manual Upload Commands
# =============================================================================

async def upload_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /upload_manual command.

    Sets the bot to await a PDF upload for manual indexing.
    Optionally accepts manufacturer and component family as arguments.

    Usage:
        /upload_manual
        /upload_manual Allen-Bradley VFD
    """
    manufacturer = None
    component_family = None

    # Parse optional args
    if context.args:
        if len(context.args) >= 1:
            manufacturer = context.args[0]
        if len(context.args) >= 2:
            component_family = " ".join(context.args[1:])

    # Set awaiting flag
    context.user_data["awaiting_manual"] = True
    context.user_data["manual_manufacturer"] = manufacturer
    context.user_data["manual_family"] = component_family

    msg = "📚 *Upload Equipment Manual*\n\n"
    msg += "Send a PDF of an OEM manual.\n\n"

    if manufacturer:
        msg += f"Manufacturer: **{manufacturer}**\n"
    if component_family:
        msg += f"Component: **{component_family}**\n"

    if not manufacturer:
        msg += "*Best results with:*\n"
        msg += "• User manuals\n"
        msg += "• Troubleshooting guides\n"
        msg += "• Fault code references\n"
        msg += "• Installation guides\n\n"

    msg += "Send `/cancel` to abort."

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    logger.info(
        f"Awaiting manual upload (manufacturer: {manufacturer}, family: {component_family})"
    )


async def handle_manual_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle PDF document upload when awaiting_manual flag is set.

    Returns:
        True if handled, False if not (so other handlers can process it)
    """
    if not context.user_data.get("awaiting_manual"):
        return False  # Not handled

    # Clear flag immediately
    context.user_data["awaiting_manual"] = False

    doc = update.message.document

    # Validate PDF
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Please send a PDF file.\n\n"
            f"Received: `{doc.file_name}`\n\n"
            "Try again: `/upload_manual`",
            parse_mode=ParseMode.MARKDOWN
        )
        return True

    manufacturer = context.user_data.get("manual_manufacturer", "Unknown")
    component_family = context.user_data.get("manual_family", "Unknown")

    await update.message.reply_text("📥 *Processing manual...*", parse_mode=ParseMode.MARKDOWN)

    # Download file
    file = await context.bot.get_file(doc.file_id)
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))

    try:
        await file.download_to_drive(temp_path)

        db = RIVETProDatabase()

        # Create manual record
        manual = db.create_manual(
            title=doc.file_name,
            manufacturer=manufacturer,
            component_family=component_family,
            file_path=str(temp_path)
        )

        # Index the manual
        indexer = ManualIndexer(db)
        result = indexer.index_manual(
            file_path=str(temp_path),
            title=doc.file_name,
            manufacturer=manufacturer,
            component_family=component_family
        )

        if result.get("success"):
            # Update manual as indexed
            db.update_manual_indexed(
                manual_id=manual["id"],
                collection_name=result["collection_name"],
                page_count=result["page_count"]
            )

            await update.message.reply_text(
                f"✅ *Manual Indexed Successfully!*\n\n"
                f"📄 **{doc.file_name}**\n"
                f"🏭 Manufacturer: {manufacturer}\n"
                f"🔧 Component: {component_family}\n"
                f"📑 Pages: {result['page_count']}\n"
                f"🧩 Chunks: {result['chunk_count']}\n\n"
                f"*Next:*\n"
                f"• Search: `/manual_search <query>`\n"
                f"• List all: `/manual_list`",
                parse_mode=ParseMode.MARKDOWN
            )

            logger.info(
                f"Manual indexed: {doc.file_name} ({result['chunk_count']} chunks) "
                f"for {manufacturer} {component_family}"
            )
        else:
            await update.message.reply_text(
                f"❌ *Failed to index manual*\n\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"The manual was saved but not searchable. "
                f"Contact support if this persists.",
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        logger.error(f"Failed to process manual upload: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error processing manual*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return True


# =============================================================================
# Manual Search Commands
# =============================================================================

async def manual_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /manual_search <query> command.

    Searches indexed manuals and returns relevant snippets with page numbers.

    Usage:
        /manual_search PowerFlex 525 fault F001
        /manual_search VFD overheating troubleshooting
    """
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:* `/manual_search <query>`\n\n"
            "*Examples:*\n"
            "• `/manual_search PowerFlex 525 fault F001`\n"
            "• `/manual_search VFD overheating`\n"
            "• `/manual_search Siemens S7-1200 wiring`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    query = " ".join(context.args)

    try:
        await update.message.chat.send_action("typing")

        search_service = ManualSearchService()
        results = search_service.search(query, top_k=5)

        if not results:
            await update.message.reply_text(
                f"🔍 *No results found for:*\n`{query}`\n\n"
                f"*Try:*\n"
                f"• Broader search terms\n"
                f"• Different keywords\n"
                f"• Upload the manual: `/upload_manual`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Build response
        msg = f"📚 *Manual Search Results:*\n"
        msg += f"Query: `{query}`\n\n"

        for i, result in enumerate(results[:5], 1):
            title = result.get("title", "Unknown Manual")
            manufacturer = result.get("manufacturer", "Unknown")
            snippet = result.get("snippet", "")
            score = result.get("score", 0.0)

            # Truncate snippet if too long
            if len(snippet) > 200:
                snippet = snippet[:197] + "..."

            msg += f"{i}. **{manufacturer} - {title}**\n"
            msg += f"   Relevance: {int(score * 100)}%\n"
            msg += f"   _{snippet}_\n\n"

        msg += f"*Commands:*\n"
        msg += f"• Refine search: `/manual_search <new query>`\n"
        msg += f"• List all: `/manual_list`"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

        logger.info(f"Manual search: '{query}' - {len(results)} results")

    except Exception as e:
        logger.error(f"Manual search failed: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Search error*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def manual_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /manual_list [manufacturer] [family] command.

    Lists all indexed manuals, optionally filtered by manufacturer or component family.

    Usage:
        /manual_list
        /manual_list Allen-Bradley
        /manual_list Siemens PLC
    """
    manufacturer = None
    component_family = None

    # Parse optional filters
    if context.args:
        if len(context.args) >= 1:
            manufacturer = context.args[0]
        if len(context.args) >= 2:
            component_family = " ".join(context.args[1:])

    try:
        db = RIVETProDatabase()

        # Get all indexed manuals
        manuals = db.get_indexed_manuals(
            manufacturer=manufacturer,
            component_family=component_family
        )

        if not manuals:
            msg = "📚 *No indexed manuals found*\n\n"
            if manufacturer or component_family:
                msg += f"Filters: "
                if manufacturer:
                    msg += f"Manufacturer: {manufacturer}  "
                if component_family:
                    msg += f"Component: {component_family}"
                msg += "\n\n"
                msg += "Try without filters: `/manual_list`\n"
            msg += "Upload manuals: `/upload_manual`"

            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return

        # Build response
        msg = "📚 *Indexed Manuals:*\n"
        if manufacturer or component_family:
            msg += "Filters: "
            if manufacturer:
                msg += f"**{manufacturer}** "
            if component_family:
                msg += f"**{component_family}**"
            msg += "\n"
        msg += "\n"

        # Group by manufacturer
        by_mfr = {}
        for manual in manuals:
            mfr = manual.get("manufacturer", "Unknown")
            if mfr not in by_mfr:
                by_mfr[mfr] = []
            by_mfr[mfr].append(manual)

        for mfr, mfr_manuals in sorted(by_mfr.items()):
            msg += f"🏭 **{mfr}**\n"
            for manual in mfr_manuals[:5]:  # Limit per manufacturer
                title = manual.get("title", "Unknown")
                family = manual.get("component_family", "")
                pages = manual.get("page_count", "?")
                msg += f"   • {title}\n"
                if family and family != "Unknown":
                    msg += f"     Type: {family}, Pages: {pages}\n"
            if len(mfr_manuals) > 5:
                msg += f"   _{len(mfr_manuals) - 5} more..._\n"
            msg += "\n"

        msg += f"Total: {len(manuals)} manual(s)\n\n"
        msg += "*Commands:*\n"
        msg += "• Search: `/manual_search <query>`\n"
        msg += "• Upload: `/upload_manual`"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to list manuals: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error listing manuals*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def manual_gaps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /manual_gaps command.

    Shows the top requested missing manuals to help prioritize manual uploads.
    """
    try:
        db = RIVETProDatabase()
        gaps = db.get_top_manual_gaps(limit=10)

        if not gaps:
            await update.message.reply_text(
                "📊 *No manual gaps tracked yet.*\n\n"
                "Gaps are tracked when users ask about equipment "
                "that doesn't have indexed manuals.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Build response
        msg = "📊 *Most Requested Missing Manuals:*\n\n"
        for i, gap in enumerate(gaps, 1):
            manufacturer = gap.get("manufacturer", "Unknown")
            family = gap.get("component_family", "Unknown")
            count = gap.get("request_count", 0)

            msg += f"{i}. **{manufacturer} - {family}**\n"
            msg += f"   Requests: {count}\n\n"

        msg += "*Help improve the knowledge base:*\n"
        msg += "Upload these manuals with `/upload_manual`"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

        logger.info(f"Manual gaps requested: {len(gaps)} gaps found")

    except Exception as e:
        logger.error(f"Failed to get manual gaps: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error getting manual gaps*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )
