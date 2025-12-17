#!/usr/bin/env python3
"""
Telegram Notifier - Real-Time Session Updates

Sends Telegram notifications throughout autonomous session.

Notification Types:
1. Session start
2. Issue queue summary
3. Issue success (PR created)
4. Issue failure
5. Safety limit hit (alert)
6. Session complete (summary)

Usage:
    from scripts.autonomous.telegram_notifier import TelegramNotifier

    notifier = TelegramNotifier()

    # Session start
    notifier.send_session_start()

    # Queue summary
    notifier.send_queue_summary(queue)

    # PR created
    notifier.send_pr_created(issue_number, title, pr_url, time, cost)

    # Issue failed
    notifier.send_issue_failed(issue_number, title, error)

    # Session complete
    notifier.send_session_complete(summary)
"""

import os
import logging
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger("telegram_notifier")


class TelegramNotifier:
    """
    Send Telegram notifications for autonomous session updates.

    Features:
    - Session start/end notifications
    - Issue queue summary
    - Per-issue success/failure updates
    - Safety limit alerts
    - Formatted markdown messages

    Example:
        notifier = TelegramNotifier()

        notifier.send_session_start()
        notifier.send_queue_summary(queue)

        for issue in queue:
            # ... process issue ...
            if success:
                notifier.send_pr_created(issue_num, title, pr_url, time, cost)
            else:
                notifier.send_issue_failed(issue_num, title, error)

        notifier.send_session_complete(summary)
    """

    def __init__(self):
        """Initialize Telegram notifier."""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        if not self.bot_token or not self.admin_chat_id:
            logger.warning(
                "TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID not set. "
                "Notifications will be logged only."
            )
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram notifications enabled (chat_id: {self.admin_chat_id})")

    def send_message(
        self,
        text: str,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Send Telegram message.

        Args:
            text: Message text (supports Markdown formatting)
            parse_mode: Parse mode ("Markdown" or "HTML")
            disable_web_page_preview: Disable link previews (default: True)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"[Telegram] {text}")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.admin_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.debug(f"Telegram notification sent: {text[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            logger.info(f"[Telegram] {text}")  # Log anyway
            return False

    def send_session_start(self):
        """Send session start notification."""
        text = "🤖 **Autonomous Claude Started**\n\nAnalyzing open issues..."
        self.send_message(text)

    def send_queue_summary(self, queue: List[Dict[str, Any]]):
        """
        Send issue queue summary.

        Args:
            queue: List of issue data dicts from IssueQueueBuilder
        """
        if not queue:
            text = "✅ **No Issues to Process**\n\nAll issues either too complex or already have PRs."
            self.send_message(text)
            return

        lines = [f"📋 **Issue Queue ({len(queue)} issues)**\n"]

        for i, issue_data in enumerate(queue, 1):
            complexity = issue_data["final_complexity"]
            priority = issue_data["priority_score"]
            time_est = issue_data["estimated_time_hours"]

            # Truncate title if too long
            title = issue_data["title"]
            if len(title) > 45:
                title = title[:42] + "..."

            lines.append(
                f"{i}. **#{issue_data['number']}** {title}\n"
                f"   Complexity: {complexity:.1f}/10 | Priority: {priority:.1f} | Est: {time_est:.1f}h"
            )

        text = "\n\n".join(lines)
        self.send_message(text)

    def send_pr_created(
        self,
        issue_number: int,
        title: str,
        pr_url: str,
        duration_sec: float,
        cost: float
    ):
        """
        Send PR created notification.

        Args:
            issue_number: GitHub issue number
            title: Issue title
            pr_url: PR URL
            duration_sec: Processing time in seconds
            cost: Estimated API cost in USD
        """
        text = (
            f"✅ **PR Created for Issue #{issue_number}**\n\n"
            f"[{title}]({pr_url})\n\n"
            f"⏱️ Time: {duration_sec:.1f}s\n"
            f"💵 Cost: ${cost:.4f}\n\n"
            f"Review and merge when ready."
        )
        self.send_message(text)

    def send_issue_failed(
        self,
        issue_number: int,
        title: str,
        error: str
    ):
        """
        Send issue failure notification.

        Args:
            issue_number: GitHub issue number
            title: Issue title
            error: Error message
        """
        # Truncate error if too long
        error_msg = error
        if len(error_msg) > 200:
            error_msg = error_msg[:197] + "..."

        text = (
            f"❌ **Issue #{issue_number} Failed**\n\n"
            f"{title}\n\n"
            f"Error: `{error_msg}`\n\n"
            f"Will retry in next run if still open."
        )
        self.send_message(text)

    def send_safety_limit_alert(self, stop_reason: str, completed: int, total: int):
        """
        Send safety limit alert.

        Args:
            stop_reason: Reason for stopping (from SafetyMonitor)
            completed: Number of issues completed
            total: Total issues in queue
        """
        text = (
            f"⚠️ **Safety Limit Reached**\n\n"
            f"{stop_reason}\n\n"
            f"Stopping early ({completed}/{total} completed)"
        )
        self.send_message(text)

    def send_session_complete(self, summary: Dict[str, Any]):
        """
        Send session complete summary.

        Args:
            summary: Session summary dict from SafetyMonitor.get_remaining_budget()
        """
        text = (
            f"📊 **Session Complete**\n\n"
            f"**Results:**\n"
            f"✅ Successful PRs: {summary.get('issues_succeeded', 0)}\n"
            f"❌ Failed: {summary.get('issues_failed', 0)}\n"
            f"📋 Total Processed: {summary.get('issues_processed', 0)}\n\n"
            f"**Resources Used:**\n"
            f"💵 Total Cost: {summary.get('total_cost', '$0.00')}\n"
            f"⏱️ Total Time: {summary.get('elapsed_time_hours', '0.0h')}\n"
            f"📈 Success Rate: {summary.get('success_rate', '0%')}\n\n"
            f"**Remaining Budget:**\n"
            f"💰 Cost: {summary.get('cost_remaining', '$0.00')}\n"
            f"⏲️ Time: {summary.get('time_remaining_hours', '0.0h')}"
        )
        self.send_message(text)

    def send_test_notification(self):
        """Send test notification to verify Telegram integration."""
        text = (
            "🧪 **Test Notification**\n\n"
            "Autonomous Claude Telegram integration is working!\n\n"
            "You'll receive notifications here during autonomous sessions."
        )
        return self.send_message(text)


if __name__ == "__main__":
    # Test Telegram notifier
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\nTesting Telegram Notifier...\n")

    notifier = TelegramNotifier()

    if notifier.enabled:
        print("Sending test notification...")
        success = notifier.send_test_notification()

        if success:
            print("✅ Test notification sent! Check your Telegram.")
        else:
            print("❌ Failed to send test notification. Check logs.")

    else:
        print("⚠️ Telegram not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID missing)")
        print("\nDemo notifications (would be sent to Telegram):\n")

        # Demo notifications
        print("="*70)
        notifier.send_session_start()

        print("\n" + "="*70)
        demo_queue = [
            {
                "number": 48,
                "title": "Add type hints to core modules",
                "final_complexity": 3.1,
                "priority_score": 8.2,
                "estimated_time_hours": 0.8
            },
            {
                "number": 52,
                "title": "Implement hybrid search with semantic + keyword",
                "final_complexity": 6.2,
                "priority_score": 7.5,
                "estimated_time_hours": 1.5
            }
        ]
        notifier.send_queue_summary(demo_queue)

        print("\n" + "="*70)
        notifier.send_pr_created(
            48,
            "Add type hints to core modules",
            "https://github.com/owner/repo/pull/123",
            245.3,
            0.42
        )

        print("\n" + "="*70)
        notifier.send_issue_failed(
            52,
            "Implement hybrid search",
            "Timeout after 30 minutes - complexity higher than estimated"
        )

        print("\n" + "="*70)
        notifier.send_safety_limit_alert(
            "Cost limit reached: $5.02 >= $5.00",
            4,
            7
        )

        print("\n" + "="*70)
        demo_summary = {
            "issues_succeeded": 5,
            "issues_failed": 2,
            "issues_processed": 7,
            "total_cost": "$2.18",
            "elapsed_time_hours": "2.3h",
            "success_rate": "71%",
            "cost_remaining": "$2.82",
            "time_remaining_hours": "1.7h"
        }
        notifier.send_session_complete(demo_summary)

        print("\n✅ Demo notifications complete!")
