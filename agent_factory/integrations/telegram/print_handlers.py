"""
Telegram handlers for electrical print upload and machine-specific Q&A.

Commands:
- /add_machine <name> - Create a machine (e.g., /add_machine Lathe_1)
- /list_machines - Show user's machines
- /upload_print <machine> - Upload electrical print PDF
- /list_prints <machine> - Show machine's prints
- /chat_print <machine> - Start Q&A session with machine's prints
- /end_chat - End print Q&A session

Backend:
- Uses PrintIndexer for PDF text extraction and chunking
- Uses RIVETProDatabase for machine/print storage
- User-namespaced (each user has their own machines)
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from agent_factory.rivet_pro.database import RIVETProDatabase
from agent_factory.knowledge.print_indexer import PrintIndexer

logger = logging.getLogger(__name__)


# =============================================================================
# Machine Management Commands
# =============================================================================

async def add_machine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /add_machine <name> command.

    Creates a new machine for the user. Machine names are unique per user.

    Usage:
        /add_machine Lathe_1
        /add_machine CNC Mill (description)
    """
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:* `/add_machine <machine_name>`\n\n"
            "*Examples:*\n"
            "• `/add_machine Lathe_1`\n"
            "• `/add_machine CNC_Mill`\n"
            "• `/add_machine Packaging_Line_A`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    machine_name = " ".join(context.args)
    user_id = str(update.effective_user.id)

    try:
        db = RIVETProDatabase()

        # Check if user exists, create if not
        user = db.get_user_by_telegram_id(update.effective_user.id)
        if not user:
            user = db.create_user(
                telegram_id=update.effective_user.id,
                telegram_username=update.effective_user.username,
                tier="beta"
            )
            user_id = user["id"]
            logger.info(f"Created new user: {user_id} (Telegram: {update.effective_user.id})")
        else:
            user_id = user["id"]

        # Create machine (upsert - won't error if exists)
        machine = db.create_machine(user_id, machine_name)

        await update.message.reply_text(
            f"✅ *Machine Created*\n\n"
            f"🔧 **{machine_name}**\n\n"
            f"*Next steps:*\n"
            f"• Upload prints: `/upload_print {machine_name}`\n"
            f"• View machines: `/list_machines`",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"Machine created: {machine_name} for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to create machine: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error creating machine*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def list_machines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /list_machines command.

    Shows all machines for the current user.
    """
    try:
        db = RIVETProDatabase()

        # Get user
        user = db.get_user_by_telegram_id(update.effective_user.id)
        if not user:
            await update.message.reply_text(
                "ℹ️ No machines yet.\n\n"
                "Create one: `/add_machine <name>`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        machines = db.get_user_machines(user["id"])

        if not machines:
            await update.message.reply_text(
                "ℹ️ No machines yet.\n\n"
                "Create one: `/add_machine <name>`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Build response
        msg = "🏭 *Your Machines:*\n\n"
        for m in machines:
            # Get print count
            prints = db.get_machine_prints(m["id"])
            print_count = len(prints)

            msg += f"🔧 **{m['name']}**\n"
            msg += f"   📄 {print_count} print(s)\n"
            if m.get("description"):
                msg += f"   ℹ️ {m['description']}\n"
            msg += "\n"

        msg += "*Commands:*\n"
        msg += "• `/upload_print <machine>` - Upload print\n"
        msg += "• `/list_prints <machine>` - View prints\n"
        msg += "• `/chat_print <machine>` - Q&A with prints"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to list machines: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error listing machines*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


# =============================================================================
# Print Upload Commands
# =============================================================================

async def upload_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /upload_print <machine> command.

    Sets the bot to await a PDF upload for the specified machine.

    Usage:
        /upload_print Lathe_1
    """
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:* `/upload_print <machine_name>`\n\n"
            "*Example:*\n"
            "• `/upload_print Lathe_1`\n\n"
            "Don't have a machine? Create one first:\n"
            "• `/add_machine Lathe_1`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    machine_name = " ".join(context.args)

    try:
        db = RIVETProDatabase()
        user = db.get_user_by_telegram_id(update.effective_user.id)

        if not user:
            await update.message.reply_text(
                "❌ No user account found.\n\n"
                "Create a machine first: `/add_machine <name>`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Check if machine exists
        machine = db.get_machine_by_name(user["id"], machine_name)
        if not machine:
            await update.message.reply_text(
                f"❌ *Machine not found:* `{machine_name}`\n\n"
                f"Create it first:\n"
                f"• `/add_machine {machine_name}`\n\n"
                f"Or view your machines:\n"
                f"• `/list_machines`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Set awaiting flag
        context.user_data["awaiting_print"] = True
        context.user_data["upload_machine"] = machine_name
        context.user_data["upload_machine_id"] = machine["id"]

        await update.message.reply_text(
            f"📄 *Upload Print for {machine_name}*\n\n"
            f"Send a PDF of the electrical print or schematic.\n\n"
            f"*Supported types:*\n"
            f"• Wiring diagrams\n"
            f"• Ladder logic\n"
            f"• P&IDs\n"
            f"• Panel layouts\n\n"
            f"Send `/cancel` to abort.",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"Awaiting print upload for machine: {machine_name}")

    except Exception as e:
        logger.error(f"Failed to start print upload: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_print_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle PDF document upload when awaiting_print flag is set.

    Returns:
        True if handled, False if not (so other handlers can process it)
    """
    if not context.user_data.get("awaiting_print"):
        return False  # Not handled

    # Clear flag immediately
    context.user_data["awaiting_print"] = False

    doc = update.message.document

    # Validate PDF
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Please send a PDF file.\n\n"
            f"Received: `{doc.file_name}`\n\n"
            "Try again: `/upload_print <machine>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return True

    machine_name = context.user_data.get("upload_machine", "Unknown")
    machine_id = context.user_data.get("upload_machine_id")

    if not machine_id:
        await update.message.reply_text(
            "❌ Session expired. Please run `/upload_print <machine>` again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return True

    await update.message.reply_text("📥 *Processing print...*", parse_mode=ParseMode.MARKDOWN)

    # Download file
    file = await context.bot.get_file(doc.file_id)
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))

    try:
        await file.download_to_drive(temp_path)

        db = RIVETProDatabase()
        user = db.get_user_by_telegram_id(update.effective_user.id)

        if not user:
            await update.message.reply_text("❌ User not found.", parse_mode=ParseMode.MARKDOWN)
            return True

        # Create print record
        print_record = db.create_print(
            machine_id=machine_id,
            user_id=user["id"],
            name=doc.file_name,
            file_path=str(temp_path)
        )

        # Index the print
        indexer = PrintIndexer(db)
        result = indexer.index_print(
            file_path=str(temp_path),
            machine_id=machine_id,
            user_id=user["id"],
            name=doc.file_name
        )

        if result.get("success"):
            # Update print as vectorized
            db.update_print_vectorized(
                print_id=print_record["id"],
                chunk_count=result["chunk_count"],
                collection_name=result["collection_name"]
            )

            await update.message.reply_text(
                f"✅ *Print Uploaded Successfully!*\n\n"
                f"📄 **{doc.file_name}**\n"
                f"🔧 Machine: {machine_name}\n"
                f"📑 Pages: {result['page_count']}\n"
                f"🧩 Chunks: {result['chunk_count']}\n"
                f"📝 Type: {result.get('print_type', 'auto-detected')}\n\n"
                f"*Next:*\n"
                f"• Ask questions: `/chat_print {machine_name}`\n"
                f"• Upload more: `/upload_print {machine_name}`",
                parse_mode=ParseMode.MARKDOWN
            )

            logger.info(
                f"Print indexed: {doc.file_name} ({result['chunk_count']} chunks) "
                f"for machine {machine_name}"
            )
        else:
            await update.message.reply_text(
                f"❌ *Failed to index print*\n\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"The print was saved but not searchable. "
                f"Contact support if this persists.",
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        logger.error(f"Failed to process print upload: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error processing print*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return True


async def list_prints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /list_prints <machine> command.

    Shows all prints for the specified machine.
    """
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:* `/list_prints <machine_name>`\n\n"
            "*Example:*\n"
            "• `/list_prints Lathe_1`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    machine_name = " ".join(context.args)

    try:
        db = RIVETProDatabase()
        user = db.get_user_by_telegram_id(update.effective_user.id)

        if not user:
            await update.message.reply_text(
                "❌ No user account found.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        machine = db.get_machine_by_name(user["id"], machine_name)
        if not machine:
            await update.message.reply_text(
                f"❌ *Machine not found:* `{machine_name}`\n\n"
                f"View machines: `/list_machines`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        prints = db.get_machine_prints(machine["id"])

        if not prints:
            await update.message.reply_text(
                f"📄 *No prints for {machine_name}*\n\n"
                f"Upload one: `/upload_print {machine_name}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Build response
        msg = f"📄 *Prints for {machine_name}:*\n\n"
        for p in prints:
            status = "✅" if p.get("vectorized") else "⏳ (processing)"
            msg += f"{status} **{p['name']}**\n"
            if p.get("print_type"):
                msg += f"   Type: {p['print_type']}\n"
            if p.get("chunk_count"):
                msg += f"   Chunks: {p['chunk_count']}\n"
            msg += "\n"

        msg += f"*Commands:*\n"
        msg += f"• `/chat_print {machine_name}` - Q&A\n"
        msg += f"• `/upload_print {machine_name}` - Upload more"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to list prints: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error listing prints*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


# =============================================================================
# Print Q&A Commands
# =============================================================================

async def chat_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /chat_print <machine> command.

    Starts a Q&A session with the machine's prints. All subsequent messages
    will be searched against the print chunks until /end_chat is called.
    """
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:* `/chat_print <machine_name>`\n\n"
            "*Example:*\n"
            "• `/chat_print Lathe_1`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    machine_name = " ".join(context.args)

    try:
        db = RIVETProDatabase()
        user = db.get_user_by_telegram_id(update.effective_user.id)

        if not user:
            await update.message.reply_text(
                "❌ No user account found.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        machine = db.get_machine_by_name(user["id"], machine_name)
        if not machine:
            await update.message.reply_text(
                f"❌ *Machine not found:* `{machine_name}`\n\n"
                f"Create it: `/add_machine {machine_name}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        prints = db.get_machine_prints(machine["id"])
        vectorized_prints = [p for p in prints if p.get("vectorized")]

        if not vectorized_prints:
            await update.message.reply_text(
                f"❌ *No searchable prints for {machine_name}*\n\n"
                f"Upload a print first:\n"
                f"• `/upload_print {machine_name}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Start chat session
        context.user_data["print_chat_active"] = True
        context.user_data["print_chat_machine"] = machine_name
        context.user_data["print_chat_machine_id"] = machine["id"]

        await update.message.reply_text(
            f"🔍 *Chat Mode: {machine_name} Prints*\n\n"
            f"📄 {len(vectorized_prints)} print(s) loaded\n\n"
            f"*Ask me anything about the electrical prints!*\n\n"
            f"*Examples:*\n"
            f"• What's the wire gauge for the main feeder?\n"
            f"• Where is the E-stop circuit?\n"
            f"• What components are on Panel 3?\n"
            f"• Show me the motor starter wiring\n\n"
            f"Type `/end_chat` to exit.",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"Started print chat for machine: {machine_name}")

    except Exception as e:
        logger.error(f"Failed to start print chat: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error starting chat*\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )


async def end_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /end_chat command.

    Ends the current print chat session.
    """
    if not context.user_data.get("print_chat_active"):
        await update.message.reply_text(
            "ℹ️ No active chat session.\n\n"
            "Start one: `/chat_print <machine>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    machine_name = context.user_data.get("print_chat_machine", "Unknown")

    context.user_data["print_chat_active"] = False
    context.user_data.pop("print_chat_machine", None)
    context.user_data.pop("print_chat_machine_id", None)

    await update.message.reply_text(
        f"✅ *Chat session ended*\n\n"
        f"Machine: {machine_name}\n\n"
        f"Start a new session:\n"
        f"• `/chat_print <machine>`",
        parse_mode=ParseMode.MARKDOWN
    )

    logger.info(f"Ended print chat for machine: {machine_name}")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /cancel command.

    Cancels any pending upload or chat session.
    """
    cleared = []

    if context.user_data.get("awaiting_print"):
        context.user_data["awaiting_print"] = False
        cleared.append("print upload")

    if context.user_data.get("awaiting_manual"):
        context.user_data["awaiting_manual"] = False
        cleared.append("manual upload")

    if context.user_data.get("print_chat_active"):
        context.user_data["print_chat_active"] = False
        cleared.append("print chat session")

    if cleared:
        await update.message.reply_text(
            f"✅ Cancelled: {', '.join(cleared)}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "ℹ️ Nothing to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
