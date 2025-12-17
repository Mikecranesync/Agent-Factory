#!/usr/bin/env python3
"""
Autonomous Claude Runner - Main Orchestrator

Coordinates all autonomous components to process GitHub issues at night.

Workflow:
1. Build issue queue (IssueQueueBuilder)
2. Initialize safety monitor and Telegram notifications
3. For each issue:
   a. Check safety limits
   b. Execute Claude Code Action
   c. Create draft PR if successful
   d. Send Telegram notification
4. Send final session summary

Usage:
    # Run autonomous session
    python scripts/autonomous/autonomous_claude_runner.py

    # Dry run (analyze only, no execution)
    DRY_RUN=true python scripts/autonomous/autonomous_claude_runner.py

    # Custom limits
    MAX_ISSUES=5 SAFETY_MAX_COST=3.0 python scripts/autonomous/autonomous_claude_runner.py
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from scripts.autonomous.issue_queue_builder import IssueQueueBuilder
from scripts.autonomous.safety_monitor import SafetyMonitor
from scripts.autonomous.telegram_notifier import TelegramNotifier

# These will be implemented in Phase 4
try:
    from scripts.autonomous.claude_executor import ClaudeExecutor
    from scripts.autonomous.pr_creator import PRCreator
    PHASE_4_AVAILABLE = True
except ImportError:
    PHASE_4_AVAILABLE = False

# Configuration from environment
MAX_ISSUES = int(os.getenv("MAX_ISSUES", "10"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
SAFETY_MAX_COST = float(os.getenv("SAFETY_MAX_COST", "5.0"))
SAFETY_MAX_TIME_HOURS = float(os.getenv("SAFETY_MAX_TIME_HOURS", "4.0"))
SAFETY_MAX_FAILURES = int(os.getenv("SAFETY_MAX_FAILURES", "3"))

# Logging configuration
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"autonomous_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("autonomous_runner")


def format_queue_summary(queue: List[Dict]) -> str:
    """
    Format issue queue for Telegram notification.

    Args:
        queue: List of issue data dicts

    Returns:
        Formatted summary string
    """
    if not queue:
        return "No issues in queue"

    lines = []
    for i, issue in enumerate(queue, 1):
        complexity = issue["final_complexity"]
        priority = issue["priority_score"]
        time_est = issue["estimated_time_hours"]

        # Truncate title if too long
        title = issue["title"]
        if len(title) > 45:
            title = title[:42] + "..."

        lines.append(
            f"{i}. **#{issue['number']}** {title}\n"
            f"   Complexity: {complexity:.1f}/10 | Priority: {priority:.1f} | Est: {time_est:.1f}h"
        )

    return "\n\n".join(lines)


def format_final_summary(results: List[Dict], monitor: SafetyMonitor) -> str:
    """
    Format final session summary.

    Args:
        results: List of issue results
        monitor: SafetyMonitor instance

    Returns:
        Formatted summary string
    """
    success_count = len([r for r in results if r["status"] == "success"])
    failure_count = len([r for r in results if r["status"] == "failed"])
    dry_run_count = len([r for r in results if r["status"] == "dry_run"])

    budget = monitor.get_remaining_budget()

    if DRY_RUN:
        summary = (
            f"**Dry Run Results:**\n"
            f"📋 Issues Analyzed: {dry_run_count}\n"
            f"⏱️ Time: {budget['elapsed_time_hours']}\n\n"
            f"No issues were actually processed (dry run mode)."
        )
    else:
        summary = (
            f"**Results:**\n"
            f"✅ Successful PRs: {success_count}\n"
            f"❌ Failed: {failure_count}\n"
            f"📋 Total Processed: {len(results)}\n\n"
            f"**Resources Used:**\n"
            f"💵 Total Cost: {budget['total_cost']}\n"
            f"⏱️ Total Time: {budget['elapsed_time_hours']}\n"
            f"📈 Success Rate: {budget['success_rate']}\n\n"
            f"**Remaining Budget:**\n"
            f"💰 Cost: {budget['cost_remaining']}\n"
            f"⏲️ Time: {budget['time_remaining_hours']}"
        )

    return summary


def main():
    """Main autonomous execution loop."""

    logger.info("="*70)
    logger.info("AUTONOMOUS CLAUDE SYSTEM STARTED")
    logger.info("="*70)
    logger.info(f"Max Issues: {MAX_ISSUES}")
    logger.info(f"Dry Run: {DRY_RUN}")
    logger.info(f"Safety Limits: ${SAFETY_MAX_COST} cost, {SAFETY_MAX_TIME_HOURS}h time, {SAFETY_MAX_FAILURES} failures")
    logger.info("="*70)

    # Initialize components
    try:
        queue_builder = IssueQueueBuilder()
        safety_monitor = SafetyMonitor(
            max_cost=SAFETY_MAX_COST,
            max_time_hours=SAFETY_MAX_TIME_HOURS,
            max_consecutive_failures=SAFETY_MAX_FAILURES
        )
        telegram = TelegramNotifier()

        # Check if Phase 4 components are available
        if PHASE_4_AVAILABLE and not DRY_RUN:
            claude_executor = ClaudeExecutor()
            pr_creator = PRCreator()
            logger.info("Claude executor and PR creator initialized")
        else:
            if DRY_RUN:
                logger.info("Dry run mode - will skip execution and PR creation")
            else:
                logger.warning("Phase 4 components not available - dry run mode forced")
                DRY_RUN = True
            claude_executor = None
            pr_creator = None

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)

    # STEP 1: Build issue queue
    logger.info("\n" + "="*70)
    logger.info("STEP 1: Building Issue Queue")
    logger.info("="*70)

    telegram.send_session_start()

    try:
        issue_queue = queue_builder.build_queue(max_issues=MAX_ISSUES)
        logger.info(f"Queue built: {len(issue_queue)} issues selected")

    except Exception as e:
        logger.error(f"Queue building failed: {e}")
        telegram.send_message(f"❌ **Queue Building Failed**\n\n```{str(e)}```")
        sys.exit(1)

    if not issue_queue:
        logger.info("No issues in queue, exiting")
        telegram.send_message("✅ **No Issues to Process**\n\nAll issues either too complex or already have PRs.")
        return

    # Send queue summary
    telegram.send_queue_summary(issue_queue)

    # STEP 2: Process each issue in queue
    logger.info("\n" + "="*70)
    logger.info("STEP 2: Processing Issue Queue")
    logger.info("="*70)

    results = []

    for i, issue_data in enumerate(issue_queue, 1):
        issue_num = issue_data["number"]
        issue_title = issue_data["title"]

        logger.info(f"\n{'='*70}")
        logger.info(f"Processing issue {i}/{len(issue_queue)}: #{issue_num}")
        logger.info(f"Title: {issue_title}")
        logger.info(f"Complexity: {issue_data['final_complexity']:.1f}/10")
        logger.info(f"Priority: {issue_data['priority_score']:.1f}")
        logger.info(f"Estimated Time: {issue_data['estimated_time_hours']:.1f}h")
        logger.info(f"{'='*70}")

        # Check safety limits before processing
        can_continue, stop_reason = safety_monitor.check_limits()
        if not can_continue:
            logger.error(f"Safety limit reached: {stop_reason}")
            telegram.send_safety_limit_alert(stop_reason, i-1, len(issue_queue))
            break

        safety_monitor.record_issue_start(issue_num)
        start_time = time.time()

        try:
            if DRY_RUN:
                # Dry run - just log what would happen
                logger.info(f"[DRY RUN] Would process issue #{issue_num}")
                logger.info(f"[DRY RUN] Estimated cost: ~$0.50")
                logger.info(f"[DRY RUN] Estimated time: ~{issue_data['estimated_time_hours']*60:.0f} minutes")

                # Simulate processing time
                time.sleep(0.5)

                result = {
                    "success": True,
                    "dry_run": True,
                    "estimated_cost": 0.50,
                    "estimated_time": issue_data['estimated_time_hours'] * 3600
                }

            else:
                # Real execution - use Claude executor
                logger.info(f"Executing Claude on issue #{issue_num}...")
                result = claude_executor.execute_issue(issue_num, issue_data)

            # Process result
            duration_sec = time.time() - start_time

            if result["success"] and not DRY_RUN:
                # Create draft PR
                logger.info(f"Creating draft PR for issue #{issue_num}...")
                pr_url = pr_creator.create_draft_pr(issue_num, result)

                # Record success
                cost = result.get("estimated_cost", 0.0)
                safety_monitor.record_issue_success(issue_num, cost, duration_sec)

                # Send success notification
                telegram.send_pr_created(
                    issue_num,
                    issue_title,
                    pr_url,
                    duration_sec,
                    cost
                )

                results.append({
                    "issue_number": issue_num,
                    "status": "success",
                    "pr_url": pr_url,
                    "duration": duration_sec,
                    "cost": cost
                })

                logger.info(f"✅ Issue #{issue_num} completed successfully")

            elif result["success"] and DRY_RUN:
                logger.info(f"[DRY RUN] Would create PR for #{issue_num}")
                results.append({
                    "issue_number": issue_num,
                    "status": "dry_run",
                    "duration": duration_sec
                })

            else:
                raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            logger.error(f"Issue #{issue_num} failed: {e}")

            # Record failure
            duration_sec = time.time() - start_time
            cost = 0.0  # Estimate partial cost if available

            if not DRY_RUN:
                safety_monitor.record_issue_failure(issue_num, str(e), cost)

                # Send failure notification
                telegram.send_issue_failed(issue_num, issue_title, str(e))

            results.append({
                "issue_number": issue_num,
                "status": "failed",
                "error": str(e),
                "duration": duration_sec
            })

            logger.error(f"❌ Issue #{issue_num} failed")

    # STEP 3: Send final summary
    logger.info("\n" + "="*70)
    logger.info("AUTONOMOUS CLAUDE SYSTEM COMPLETED")
    logger.info("="*70)

    summary = format_final_summary(results, safety_monitor)
    logger.info(f"\n{summary}")

    # Send to Telegram
    telegram.send_session_complete(safety_monitor.get_remaining_budget())

    # Log final summary
    print("\n" + safety_monitor.format_summary())

    # Exit with appropriate code
    if not DRY_RUN:
        success_count = len([r for r in results if r["status"] == "success"])
        if success_count > 0:
            logger.info(f"✅ Session complete: {success_count} PRs created")
            sys.exit(0)
        else:
            logger.warning("⚠️ Session complete: No PRs created")
            sys.exit(1)
    else:
        logger.info("✅ Dry run complete")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
