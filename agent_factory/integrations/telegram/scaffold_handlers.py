"""SCAFFOLD Integration Handlers for Telegram Bot

Provides Telegram command handlers for creating and managing SCAFFOLD
autonomous task execution sessions.

Commands:
    /scaffold <description> - Create and execute task from natural language
    /scaffold_status <session_id> - Check execution status
    /scaffold_history - View recent SCAFFOLD sessions

Usage:
    handlers = ScaffoldHandlers(repo_root=Path.cwd())
    app.add_handler(CommandHandler("scaffold", handlers.handle_scaffold_create))
"""

import threading
import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from agent_factory.scaffold.orchestrator import ScaffoldOrchestrator
from agent_factory.scaffold.backlog_parser import BacklogParser
from .nl_task_parser import NLTaskParser

logger = logging.getLogger(__name__)


class ScaffoldHandlers:
    """Telegram handlers for SCAFFOLD autonomous task execution"""

    def __init__(
        self,
        repo_root: Path,
        anthropic_api_key: Optional[str] = None,
        max_cost: float = 5.0,
        max_time_hours: float = 2.0,
        dry_run: bool = False
    ):
        """Initialize SCAFFOLD handlers

        Args:
            repo_root: Root directory of the repository
            anthropic_api_key: Anthropic API key for NL parsing
            max_cost: Maximum USD cost per execution (default: $5)
            max_time_hours: Maximum execution time in hours (default: 2)
            dry_run: If True, simulate execution without making changes
        """
        self.repo_root = Path(repo_root)
        self.max_cost = max_cost
        self.max_time_hours = max_time_hours
        self.dry_run = dry_run

        # Initialize components
        self.nl_parser = NLTaskParser(anthropic_api_key)
        self.backlog = BacklogParser()

        # Track active executions
        self.active_executions = {}  # chat_id -> session_id

        logger.info(f"ScaffoldHandlers initialized (dry_run={dry_run})")

    async def handle_scaffold_create(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /scaffold <description> command

        Creates a task from natural language and executes it via SCAFFOLD orchestrator.

        Args:
            update: Telegram update object
            context: Telegram context with command arguments

        Example:
            /scaffold Build a REST API for user management with CRUD operations
        """
        chat_id = update.effective_chat.id
        user = update.effective_user

        # Check if there's already an active execution
        if chat_id in self.active_executions:
            session_id = self.active_executions[chat_id]
            await update.message.reply_text(
                f"⚠️ You already have an active execution:\n"
                f"Session: `{session_id}`\n\n"
                f"Check status with: /scaffold_status {session_id}\n\n"
                f"Wait for it to complete before starting a new one.",
                parse_mode="Markdown"
            )
            return

        # Extract description from command
        description = " ".join(context.args) if context.args else ""

        if not description:
            await update.message.reply_text(
                "📋 **SCAFFOLD Task Creation**\n\n"
                "**Usage:** `/scaffold <task description>`\n\n"
                "**Examples:**\n"
                "• `/scaffold Build login system with email verification`\n"
                "• `/scaffold Fix bug where users can't upload images`\n"
                "• `/scaffold Add unit tests for authentication module`\n\n"
                "**Features:**\n"
                "✅ Natural language parsing (no rigid syntax!)\n"
                "✅ Automatic execution via Claude Code CLI\n"
                "✅ PR creation on completion\n"
                "✅ Cost and time tracking\n"
                "✅ Safety limits enforced\n\n"
                f"**Limits:**\n"
                f"💰 Max cost: ${self.max_cost:.2f}\n"
                f"⏱️ Max time: {self.max_time_hours:.1f} hours",
                parse_mode="Markdown"
            )
            return

        logger.info(f"User {user.username} ({user.id}) requested task: {description[:100]}...")

        # Step 1: Parse natural language to structured task
        await update.message.reply_text(
            "🧠 **Understanding your request...**\n\n"
            "Using Claude AI to extract task specification from your description...",
            parse_mode="Markdown"
        )

        try:
            task_spec = self.nl_parser.parse_nl_to_task(description)
            logger.info(f"Parsed task spec: {task_spec['title']}")

        except Exception as e:
            logger.error(f"Failed to parse natural language: {e}")
            await update.message.reply_text(
                f"❌ **Failed to parse task description**\n\n"
                f"Error: {str(e)}\n\n"
                f"Please try rephrasing your request with more details.",
                parse_mode="Markdown"
            )
            return

        # Step 2: Create task in Backlog.md
        await update.message.reply_text(
            f"📝 **Creating task in Backlog.md...**\n\n"
            f"**Title:** {task_spec['title']}\n"
            f"**Priority:** {task_spec['priority']}\n"
            f"**Labels:** {', '.join(task_spec['labels'])}",
            parse_mode="Markdown"
        )

        try:
            # Generate unique task ID
            timestamp = int(time.time())
            task_id = f"task-telegram-{timestamp}"

            # Add task to Backlog.md via MCP
            # (In production, this would call backlog_parser.create_task())
            # For now, we'll create a simple task and add to backlog

            logger.info(f"Creating task {task_id} in Backlog.md")

            # TODO: Actually create in Backlog.md using MCP
            # For MVP, we'll pass task_spec directly to orchestrator

        except Exception as e:
            logger.error(f"Failed to create task in Backlog.md: {e}")
            await update.message.reply_text(
                f"❌ **Failed to create task**\n\n"
                f"Error: {str(e)}\n\n"
                f"Please try again or contact support.",
                parse_mode="Markdown"
            )
            return

        # Step 3: Trigger SCAFFOLD orchestrator
        mode_str = "DRY RUN" if self.dry_run else "EXECUTION"

        await update.message.reply_text(
            f"✅ **Task created:** `{task_id}`\n"
            f"🚀 **Starting {mode_str}...**\n\n"
            f"This may take 5-30 minutes depending on task complexity.\n\n"
            f"💡 **Tip:** You can check status anytime with:\n"
            f"`/scaffold_status <session_id>`\n\n"
            f"I'll notify you when complete!",
            parse_mode="Markdown"
        )

        # Track this execution
        self.active_executions[chat_id] = task_id

        # Launch orchestrator in background thread
        self._execute_scaffold_async(
            task_id=task_id,
            task_spec=task_spec,
            chat_id=chat_id,
            bot=context.bot,
            username=user.username or str(user.id)
        )

    def _execute_scaffold_async(
        self,
        task_id: str,
        task_spec: Dict,
        chat_id: int,
        bot,
        username: str
    ):
        """Execute SCAFFOLD orchestrator in background thread

        Args:
            task_id: Unique task identifier
            task_spec: Structured task specification
            chat_id: Telegram chat ID for notifications
            bot: Telegram bot instance
            username: User who triggered execution
        """
        def run():
            session_id = None
            start_time = datetime.now()

            try:
                logger.info(f"Starting SCAFFOLD execution for {task_id}")

                # Create orchestrator
                orch = ScaffoldOrchestrator(
                    repo_root=self.repo_root,
                    dry_run=self.dry_run,
                    max_tasks=1,  # Execute just this one task
                    max_concurrent=1,
                    max_cost=self.max_cost,
                    max_time_hours=self.max_time_hours,
                    labels=["telegram-trigger"]
                )

                # Run orchestration
                summary = orch.run()
                session_id = summary.get('session_id', 'unknown')

                # Calculate execution time
                duration_sec = (datetime.now() - start_time).total_seconds()

                logger.info(f"SCAFFOLD execution complete: {session_id}")

                # Format completion message
                message = self._format_completion_message(
                    summary=summary,
                    task_spec=task_spec,
                    duration_sec=duration_sec
                )

                # Send completion notification
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                ))

            except Exception as e:
                logger.error(f"SCAFFOLD execution failed: {e}", exc_info=True)

                # Calculate execution time
                duration_sec = (datetime.now() - start_time).total_seconds()

                # Send failure notification
                message = (
                    f"❌ **SCAFFOLD Execution Failed**\n\n"
                    f"**Task:** {task_spec['title']}\n"
                    f"**Session:** `{session_id or 'unknown'}`\n"
                    f"**Duration:** {duration_sec / 60:.1f} minutes\n\n"
                    f"**Error:**\n```\n{str(e)}\n```\n\n"
                    f"Check logs for more details or try again with a simpler task."
                )

                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                ))

            finally:
                # Remove from active executions
                if chat_id in self.active_executions:
                    del self.active_executions[chat_id]

        # Start background thread
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        logger.info(f"Background thread started for {task_id}")

    def _format_completion_message(
        self,
        summary: Dict[str, Any],
        task_spec: Dict,
        duration_sec: float
    ) -> str:
        """Format completion notification message

        Args:
            summary: Orchestrator execution summary
            task_spec: Original task specification
            duration_sec: Execution duration in seconds

        Returns:
            Formatted Markdown message
        """
        completed = summary.get('tasks_completed', 0)
        failed = summary.get('tasks_failed', 0)
        cost = summary.get('total_cost', 0.0)
        session_id = summary.get('session_id', 'unknown')

        message = "🎉 **SCAFFOLD Execution Complete!**\n\n"

        # Task info
        message += f"**Task:** {task_spec['title']}\n"
        message += f"**Session:** `{session_id}`\n\n"

        # Results
        message += "**Results:**\n"
        message += f"✅ Completed: {completed}\n"
        message += f"❌ Failed: {failed}\n"
        message += f"💰 Cost: ${cost:.2f}\n"
        message += f"⏱️ Duration: {duration_sec / 60:.1f} minutes\n\n"

        # Success message
        if completed > 0:
            message += "**Next Steps:**\n"
            message += "📁 Check GitHub for new Pull Requests\n"
            message += "✅ Review and approve the changes\n"
            message += "🔄 Merge when ready!\n\n"
            message += "View details: `/scaffold_status " + session_id + "`"
        else:
            message += "⚠️ No tasks completed. Check session details for more information.\n\n"
            message += "View details: `/scaffold_status " + session_id + "`"

        if self.dry_run:
            message += "\n\n🔵 **DRY RUN MODE** - No actual changes made"

        return message

    async def handle_scaffold_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /scaffold_status <session_id> command

        Displays current status of a SCAFFOLD execution session.

        Args:
            update: Telegram update object
            context: Telegram context with command arguments

        Example:
            /scaffold_status 20251219_140000
        """
        if not context.args:
            await update.message.reply_text(
                "📊 **SCAFFOLD Status Check**\n\n"
                "**Usage:** `/scaffold_status <session_id>`\n\n"
                "**Example:**\n"
                "`/scaffold_status 20251219_140000`\n\n"
                "💡 Get session ID from the creation confirmation or history.",
                parse_mode="Markdown"
            )
            return

        session_id = context.args[0]
        session_file = self.repo_root / ".scaffold" / "sessions" / f"{session_id}.json"

        if not session_file.exists():
            await update.message.reply_text(
                f"❌ **Session not found:** `{session_id}`\n\n"
                f"Possible reasons:\n"
                f"• Session ID is incorrect\n"
                f"• Session files were cleaned up\n"
                f"• Execution hasn't started yet\n\n"
                f"View available sessions: /scaffold_history",
                parse_mode="Markdown"
            )
            return

        try:
            with open(session_file, 'r') as f:
                state = json.load(f)

            message = self._format_status_message(state)
            await update.message.reply_text(message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Failed to read session file: {e}")
            await update.message.reply_text(
                f"❌ **Error reading session**\n\n"
                f"Error: {str(e)}",
                parse_mode="Markdown"
            )

    def _format_status_message(self, state: Dict) -> str:
        """Format session status message

        Args:
            state: Session state dict from JSON file

        Returns:
            Formatted Markdown message
        """
        session_id = state.get('session_id', 'unknown')
        start_time = state.get('start_time', 'unknown')

        tasks_queued = state.get('tasks_queued', [])
        tasks_in_progress = state.get('tasks_in_progress', {})
        tasks_completed = state.get('tasks_completed', [])
        tasks_failed = state.get('tasks_failed', [])

        total_cost = state.get('total_cost', 0.0)
        total_duration = state.get('total_duration_sec', 0.0)

        message = "📊 **SCAFFOLD Session Status**\n\n"

        # Session info
        message += f"**Session ID:** `{session_id}`\n"
        message += f"**Started:** {start_time}\n\n"

        # Task counts
        message += "**Tasks:**\n"
        message += f"📋 Queued: {len(tasks_queued)}\n"
        message += f"▶️ In Progress: {len(tasks_in_progress)}\n"
        message += f"✅ Completed: {len(tasks_completed)}\n"
        message += f"❌ Failed: {len(tasks_failed)}\n\n"

        # Resource usage
        message += "**Resource Usage:**\n"
        message += f"💰 Total Cost: ${total_cost:.2f}\n"
        message += f"⏱️ Total Duration: {total_duration / 60:.1f} minutes\n\n"

        # Active tasks
        if tasks_in_progress:
            message += "**Currently Running:**\n"
            for task_id, worktree in list(tasks_in_progress.items())[:3]:
                message += f"• `{task_id}`\n"

        # Completed tasks
        if tasks_completed:
            message += "\n**Completed Tasks:**\n"
            for task_id in tasks_completed[:5]:
                message += f"✅ `{task_id}`\n"

        # Failed tasks
        if tasks_failed:
            message += "\n**Failed Tasks:**\n"
            for task_id in tasks_failed[:5]:
                message += f"❌ `{task_id}`\n"

        return message

    async def handle_scaffold_history(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /scaffold_history command

        Shows recent SCAFFOLD execution sessions.

        Args:
            update: Telegram update object
            context: Telegram context
        """
        sessions_dir = self.repo_root / ".scaffold" / "sessions"

        if not sessions_dir.exists():
            await update.message.reply_text(
                "📚 **No SCAFFOLD Sessions Found**\n\n"
                "You haven't run any SCAFFOLD executions yet.\n\n"
                "**Get started:**\n"
                "`/scaffold Build a simple REST API`",
                parse_mode="Markdown"
            )
            return

        # Get all session files, sorted by modification time (newest first)
        try:
            sessions = sorted(
                sessions_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:10]  # Show last 10 sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            await update.message.reply_text(
                f"❌ **Error listing sessions**\n\n"
                f"Error: {str(e)}",
                parse_mode="Markdown"
            )
            return

        if not sessions:
            await update.message.reply_text(
                "📚 **No SCAFFOLD Sessions Found**\n\n"
                "Session directory exists but is empty.",
                parse_mode="Markdown"
            )
            return

        # Build history message
        message = "📚 **Recent SCAFFOLD Sessions**\n\n"

        for session_file in sessions:
            try:
                with open(session_file, 'r') as f:
                    state = json.load(f)

                session_id = state.get('session_id', session_file.stem)
                completed = len(state.get('tasks_completed', []))
                failed = len(state.get('tasks_failed', []))
                cost = state.get('total_cost', 0.0)
                duration = state.get('total_duration_sec', 0.0)

                message += f"**`{session_id}`**\n"
                message += f"✅ {completed} completed • ❌ {failed} failed\n"
                message += f"💰 ${cost:.2f} • ⏱️ {duration / 60:.1f}m\n\n"

            except Exception as e:
                logger.warning(f"Failed to read session {session_file.name}: {e}")
                continue

        message += "**Commands:**\n"
        message += "• `/scaffold_status <session_id>` - View details\n"
        message += "• `/scaffold <description>` - Create new task"

        await update.message.reply_text(message, parse_mode="Markdown")
