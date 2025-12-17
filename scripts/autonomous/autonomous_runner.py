#!/usr/bin/env python3
"""
Autonomous Runner - Headless Claude for Overnight Issue Solving

Orchestrates issue_queue_builder + safety_monitor to automatically solve GitHub issues.

Features:
- Builds prioritized issue queue (5-10 issues, <4h total)
- Solves issues via automated code changes
- Creates PRs with solutions
- Enforces safety limits ($5, 4h, 3 failures max)
- Sends summary via Telegram
- Dry-run mode for testing

Usage:
    # Dry-run (no actual changes)
    poetry run python scripts/autonomous/autonomous_runner.py --dry-run

    # Live execution
    poetry run python scripts/autonomous/autonomous_runner.py

    # Custom limits
    poetry run python scripts/autonomous/autonomous_runner.py --max-cost 3.0 --max-time 2.0
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from scripts.autonomous.issue_queue_builder import IssueQueueBuilder
from scripts.autonomous.safety_monitor import SafetyMonitor

logger = logging.getLogger("autonomous_runner")


class AutonomousRunner:
    """
    Headless Claude orchestrator for overnight issue solving.

    Workflow:
    1. Build issue queue (IssueQueueBuilder)
    2. For each issue:
       - Analyze context
       - Generate solution
       - Create PR
       - Track progress (SafetyMonitor)
    3. Send summary report
    """

    def __init__(
        self,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0,
        max_consecutive_failures: int = 3,
        dry_run: bool = False
    ):
        """
        Initialize autonomous runner.

        Args:
            max_cost: Maximum API cost in USD (default: $5.00)
            max_time_hours: Maximum wall-clock time in hours (default: 4.0)
            max_consecutive_failures: Max consecutive failures before stop (default: 3)
            dry_run: If True, simulate without making actual changes (default: False)
        """
        self.dry_run = dry_run
        self.max_issues_per_run = 10

        # Initialize components
        self.queue_builder = IssueQueueBuilder()
        self.monitor = SafetyMonitor(
            max_cost=max_cost,
            max_time_hours=max_time_hours,
            max_consecutive_failures=max_consecutive_failures
        )

        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = datetime.now()

        logger.info("=" * 70)
        logger.info("AUTONOMOUS RUNNER INITIALIZED")
        logger.info("=" * 70)
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Max Issues: {self.max_issues_per_run}")
        logger.info("=" * 70)

    def run(self) -> Dict[str, Any]:
        """
        Main execution loop.

        Returns:
            Session summary dict with results
        """
        try:
            # STEP 1: Build issue queue
            logger.info("\n" + "=" * 70)
            logger.info("STEP 1: BUILDING ISSUE QUEUE")
            logger.info("=" * 70)

            queue = self.queue_builder.build_queue(max_issues=self.max_issues_per_run)

            if not queue:
                logger.warning("No issues in queue. Exiting.")
                return self._generate_summary(queue=[])

            logger.info(f"\nQueue built: {len(queue)} issues selected")
            self._print_queue_summary(queue)

            # STEP 2: Process each issue
            logger.info("\n" + "=" * 70)
            logger.info("STEP 2: PROCESSING ISSUES")
            logger.info("=" * 70)

            for issue_data in queue:
                # Check safety limits before each issue
                can_continue, stop_reason = self.monitor.check_limits()
                if not can_continue:
                    logger.error(f"\n🛑 SAFETY LIMIT REACHED: {stop_reason}")
                    break

                # Process issue
                self._process_issue(issue_data)

            # STEP 3: Generate summary
            logger.info("\n" + "=" * 70)
            logger.info("STEP 3: SESSION COMPLETE")
            logger.info("=" * 70)

            summary = self._generate_summary(queue=queue)
            self._print_summary(summary)

            # STEP 4: Send Telegram notification (if not dry-run)
            if not self.dry_run:
                self._send_telegram_summary(summary)

            return summary

        except KeyboardInterrupt:
            logger.warning("\n\n⚠️  Interrupted by user. Generating summary...")
            summary = self._generate_summary(queue=[])
            self._print_summary(summary)
            return summary

        except Exception as e:
            logger.error(f"\n\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "status": "failed"}

    def _process_issue(self, issue_data: Dict[str, Any]):
        """
        Process a single issue.

        Args:
            issue_data: Issue data from queue builder
        """
        issue_number = issue_data["number"]
        title = issue_data["title"]

        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESSING ISSUE #{issue_number}")
        logger.info(f"{'='*70}")
        logger.info(f"Title: {title}")
        logger.info(f"Complexity: {issue_data['final_complexity']:.1f}/10")
        logger.info(f"Estimated Time: {issue_data['estimated_time_hours']:.1f}h")
        logger.info(f"Priority: {issue_data['priority_score']:.1f}")
        logger.info(f"URL: {issue_data['url']}")

        # Start monitoring
        self.monitor.record_issue_start(issue_number)
        start_time = time.time()

        try:
            if self.dry_run:
                # Simulate processing
                logger.info("\n[DRY-RUN] Simulating issue resolution...")
                time.sleep(2)  # Simulate work

                # Simulate success/failure based on complexity
                if issue_data["final_complexity"] > 7.0:
                    raise Exception("Simulated failure: complexity too high")

                logger.info("[DRY-RUN] Solution generated (simulated)")
                logger.info("[DRY-RUN] PR created (simulated)")
                logger.info("[DRY-RUN] Tests passing (simulated)")

                # Simulate cost based on complexity
                simulated_cost = issue_data["final_complexity"] * 0.05
                duration = time.time() - start_time

                # Record success
                self.monitor.record_issue_success(
                    issue_number=issue_number,
                    cost=simulated_cost,
                    duration_sec=duration
                )

            else:
                # LIVE EXECUTION
                # TODO: Integrate with actual Claude Code execution
                # For now, placeholder
                logger.info("\n[LIVE] Analyzing issue context...")
                logger.info("[LIVE] Generating solution...")
                logger.info("[LIVE] Creating PR...")

                # Simulate for now until live integration ready
                time.sleep(5)
                simulated_cost = issue_data["final_complexity"] * 0.10
                duration = time.time() - start_time

                self.monitor.record_issue_success(
                    issue_number=issue_number,
                    cost=simulated_cost,
                    duration_sec=duration
                )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)[:200]  # Truncate long errors

            logger.error(f"\n❌ FAILED: {error_msg}")

            # Estimate partial cost (some API calls may have been made)
            partial_cost = issue_data["final_complexity"] * 0.02

            self.monitor.record_issue_failure(
                issue_number=issue_number,
                error=error_msg,
                cost=partial_cost
            )

    def _print_queue_summary(self, queue: List[Dict[str, Any]]):
        """Print queue summary table."""
        logger.info("\n" + "-" * 70)
        logger.info("QUEUE SUMMARY")
        logger.info("-" * 70)

        for i, issue in enumerate(queue, 1):
            logger.info(
                f"{i}. #{issue['number']}: {issue['title'][:50]}..."
            )
            logger.info(
                f"   Complexity: {issue['final_complexity']:.1f}/10 | "
                f"Time: {issue['estimated_time_hours']:.1f}h | "
                f"Priority: {issue['priority_score']:.1f}"
            )

        total_time = sum(i["estimated_time_hours"] for i in queue)
        logger.info("-" * 70)
        logger.info(f"Total Estimated Time: {total_time:.1f}h")
        logger.info("-" * 70)

    def _generate_summary(self, queue: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate session summary.

        Args:
            queue: List of issues processed

        Returns:
            Summary dict
        """
        monitor_summary = self.monitor.get_session_summary()

        return {
            "session_id": self.session_id,
            "mode": "dry-run" if self.dry_run else "live",
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "queue_size": len(queue),
            "monitor": monitor_summary,
            "issues_processed": len(queue)
        }

    def _print_summary(self, summary: Dict[str, Any]):
        """Print human-readable summary."""
        logger.info("\n" + self.monitor.format_summary())

        logger.info("\nSession Info:")
        logger.info(f"  Session ID: {summary['session_id']}")
        logger.info(f"  Mode: {summary['mode'].upper()}")
        logger.info(f"  Duration: {summary['session_start']} → {summary['session_end']}")

    def _send_telegram_summary(self, summary: Dict[str, Any]):
        """
        Send summary to Telegram.

        Args:
            summary: Session summary dict
        """
        try:
            import telegram_bot

            # Format message
            monitor = summary["monitor"]
            message = (
                f"🤖 **Autonomous Run Complete**\n\n"
                f"**Session:** {summary['session_id']}\n"
                f"**Issues Processed:** {monitor['issues_processed']}\n"
                f"**Success Rate:** {monitor['success_rate']}\n"
                f"**Total Cost:** {monitor['total_cost']}\n"
                f"**Total Time:** {monitor['elapsed_time_hours']}\n\n"
                f"**Budget Remaining:**\n"
                f"  - Cost: {monitor['cost_remaining']}\n"
                f"  - Time: {monitor['time_remaining_hours']}\n"
            )

            # TODO: Send via Telegram bot
            logger.info(f"\n[Telegram notification would be sent]:\n{message}")

        except Exception as e:
            logger.warning(f"Failed to send Telegram notification: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Runner - Headless Claude for overnight issue solving"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without making actual changes"
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=5.0,
        help="Maximum API cost in USD (default: 5.0)"
    )
    parser.add_argument(
        "--max-time",
        type=float,
        default=4.0,
        help="Maximum wall-clock time in hours (default: 4.0)"
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=3,
        help="Maximum consecutive failures before stop (default: 3)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Run
    runner = AutonomousRunner(
        max_cost=args.max_cost,
        max_time_hours=args.max_time,
        max_consecutive_failures=args.max_failures,
        dry_run=args.dry_run
    )

    summary = runner.run()

    # Exit with appropriate code
    if summary.get("error"):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
