"""
GitHub Actions Integration for Telegram Admin Panel

Trigger and monitor GitHub Actions workflows from Telegram:
- Deploy to VPS
- Run tests
- Custom workflow triggers
- View workflow status
- Notifications on completion

Commands:
    /deploy - Trigger VPS deployment
    /workflow <name> - Trigger custom workflow
    /workflows - List available workflows
    /workflow_status - View recent runs

Usage:
    from agent_factory.integrations.telegram.admin import GitHubActions

    github = GitHubActions()
    app.add_handler(CommandHandler("deploy", github.handle_deploy))
"""

import logging
import os
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .permissions import require_admin

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """GitHub Actions workflow status"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    REQUESTED = "requested"


class WorkflowConclusion(str, Enum):
    """GitHub Actions workflow conclusion"""
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    NEUTRAL = "neutral"


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run information"""
    id: int
    name: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: datetime
    html_url: str
    run_number: int
    head_branch: str


class GitHubActions:
    """
    Manages GitHub Actions workflow triggers and monitoring.

    Provides:
    - Workflow triggers via API
    - Status monitoring
    - Recent run history
    - Completion notifications
    """

    def __init__(self):
        """Initialize GitHub Actions integration"""
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.owner = os.getenv("GITHUB_OWNER", "Mikecranesync")
        self.repo = os.getenv("GITHUB_REPO", "Agent-Factory")
        self.api_base = "https://api.github.com"

        if not self.token:
            logger.warning("GITHUB_TOKEN not set - GitHub Actions integration disabled")

        logger.info(f"GitHubActions initialized for {self.owner}/{self.repo}")

    @require_admin
    async def handle_deploy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /deploy command - trigger VPS deployment.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not self.token:
            await update.message.reply_text(
                "❌ *GitHub Integration Disabled*\n\n"
                "GITHUB_TOKEN not configured in .env\n\n"
                "Add your GitHub Personal Access Token to enable deployments.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Confirm deployment
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="deploy_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="deploy_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🚀 *Deploy to VPS*\n\n"
            "⚠️ This will:\n"
            "• Pull latest code from main branch\n"
            "• Install dependencies\n"
            "• Restart services\n"
            "• Notify on completion\n\n"
            "Confirm deployment?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @require_admin
    async def handle_deploy_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute confirmed deployment"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "🔄 *Triggering Deployment*\n\n"
            "Please wait...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Trigger deploy-vps workflow
            run_id = await self._trigger_workflow("deploy-vps.yml")

            if run_id:
                workflow_url = f"https://github.com/{self.owner}/{self.repo}/actions/runs/{run_id}"

                await query.edit_message_text(
                    "✅ *Deployment Triggered*\n\n"
                    f"Workflow Run: #{run_id}\n\n"
                    "• Pulling latest code\n"
                    "• Installing dependencies\n"
                    "• Restarting services\n\n"
                    f"[View Progress]({workflow_url})\n\n"
                    "You'll receive a notification when complete.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(
                    "❌ *Deployment Failed*\n\n"
                    "Could not trigger workflow.\n"
                    "Check GitHub token permissions.",
                    parse_mode=ParseMode.MARKDOWN
                )

        except Exception as e:
            logger.error(f"Failed to trigger deployment: {e}")
            await query.edit_message_text(
                f"❌ *Deployment Failed*\n\n"
                f"Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_admin
    async def handle_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /workflow <name> command - trigger custom workflow.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: `/workflow <workflow_name>`\n\n"
                "Example: `/workflow claude.yml`\n\n"
                "Use /workflows to see available workflows.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        workflow_name = context.args[0]

        await update.message.reply_text(f"🔄 Triggering workflow: {workflow_name}...")

        try:
            run_id = await self._trigger_workflow(workflow_name)

            if run_id:
                workflow_url = f"https://github.com/{self.owner}/{self.repo}/actions/runs/{run_id}"

                await update.message.reply_text(
                    f"✅ *Workflow Triggered*\n\n"
                    f"Name: `{workflow_name}`\n"
                    f"Run ID: #{run_id}\n\n"
                    f"[View Progress]({workflow_url})",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to trigger workflow: {workflow_name}",
                    parse_mode=ParseMode.MARKDOWN
                )

        except Exception as e:
            logger.error(f"Failed to trigger workflow: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_admin
    async def handle_workflows(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /workflows command - list available workflows.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Fetching workflows...")

        try:
            workflows = await self._list_workflows()

            if not workflows:
                await update.message.reply_text(
                    "⚠️ No workflows found.\n\n"
                    "Add .github/workflows/*.yml files to your repo.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format workflow list
            message = "📋 *Available Workflows*\n\n"
            for wf in workflows:
                message += f"• `{wf['name']}`\n"
                message += f"  File: `{wf['path']}`\n"
                message += f"  State: {wf['state']}\n\n"

            message += "\nTrigger with: `/workflow <filename>`"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_admin
    async def handle_workflow_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /workflow_status command - view recent runs.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Fetching workflow runs...")

        try:
            runs = await self._get_recent_runs(limit=5)

            if not runs:
                await update.message.reply_text(
                    "⚠️ No recent workflow runs.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format runs list
            message = "📊 *Recent Workflow Runs*\n\n"
            for run in runs:
                status_emoji = self._get_status_emoji(run)
                message += f"{status_emoji} *{run.name}* (#{run.run_number})\n"
                message += f"  • Status: {run.status}\n"

                if run.conclusion:
                    message += f"  • Result: {run.conclusion}\n"

                time_ago = self._time_ago(run.updated_at)
                message += f"  • Updated: {time_ago}\n"
                message += f"  • Branch: {run.head_branch}\n"
                message += f"  [View]({run.html_url})\n\n"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def _trigger_workflow(self, workflow_filename: str, inputs: Optional[Dict] = None) -> Optional[int]:
        """
        Trigger GitHub Actions workflow via API.

        Args:
            workflow_filename: Workflow file name (e.g., "deploy-vps.yml")
            inputs: Optional workflow inputs

        Returns:
            Run ID if successful, None otherwise
        """
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_filename}/dispatches"

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        data = {
            "ref": "main",
            "inputs": inputs or {}
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 204:
                logger.info(f"Triggered workflow: {workflow_filename}")
                # Get latest run ID (GitHub doesn't return it in dispatch response)
                return await self._get_latest_run_id()
            else:
                logger.error(f"Failed to trigger workflow: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            return None

    async def _list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows in repository"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/workflows"

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("workflows", [])

        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []

    async def _get_recent_runs(self, limit: int = 5) -> List[WorkflowRun]:
        """Get recent workflow runs"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/runs"

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        params = {
            "per_page": limit
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            runs = []

            for run_data in data.get("workflow_runs", []):
                runs.append(WorkflowRun(
                    id=run_data["id"],
                    name=run_data["name"],
                    status=WorkflowStatus(run_data["status"]),
                    conclusion=WorkflowConclusion(run_data["conclusion"]) if run_data.get("conclusion") else None,
                    created_at=datetime.fromisoformat(run_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(run_data["updated_at"].replace("Z", "+00:00")),
                    html_url=run_data["html_url"],
                    run_number=run_data["run_number"],
                    head_branch=run_data["head_branch"]
                ))

            return runs

        except Exception as e:
            logger.error(f"Error getting recent runs: {e}")
            return []

    async def _get_latest_run_id(self) -> Optional[int]:
        """Get ID of most recent workflow run"""
        runs = await self._get_recent_runs(limit=1)
        return runs[0].id if runs else None

    def _get_status_emoji(self, run: WorkflowRun) -> str:
        """Get emoji for workflow run status"""
        if run.conclusion == WorkflowConclusion.SUCCESS:
            return "✅"
        elif run.conclusion == WorkflowConclusion.FAILURE:
            return "❌"
        elif run.conclusion == WorkflowConclusion.CANCELLED:
            return "⚠️"
        elif run.status == WorkflowStatus.IN_PROGRESS:
            return "🔄"
        elif run.status == WorkflowStatus.QUEUED:
            return "⏳"
        else:
            return "❓"

    def _time_ago(self, dt: datetime) -> str:
        """Format time ago string"""
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"
