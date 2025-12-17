#!/usr/bin/env python3
"""
Safety Monitor - Cost/Time/Failure Tracking

Enforces hard limits on autonomous execution to prevent runaway costs/time.

Hard Limits:
- Max Cost: $5.00 per night (configurable)
- Max Time: 4 hours wall-clock time (configurable)
- Max Consecutive Failures: 3 (circuit breaker)

Per-Issue Limits:
- Timeout: 30 minutes per issue

Usage:
    from scripts.autonomous.safety_monitor import SafetyMonitor

    monitor = SafetyMonitor(max_cost=5.0, max_time_hours=4.0, max_consecutive_failures=3)

    # Before each issue
    can_continue, stop_reason = monitor.check_limits()
    if not can_continue:
        print(f"Safety limit: {stop_reason}")
        break

    # After issue completion
    monitor.record_issue_success(issue_number, cost=0.42, duration_sec=245.3)

    # After issue failure
    monitor.record_issue_failure(issue_number, error="Timeout", cost=0.10)
"""

import os
import time
import logging
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("safety_monitor")


class SafetyMonitor:
    """
    Enforce hard limits on autonomous execution.

    Features:
    - Cost tracking: Stop when total cost >= max_cost
    - Time tracking: Stop when elapsed time >= max_time_hours
    - Failure tracking: Stop when consecutive_failures >= max_consecutive_failures
    - Progress reporting: Track success rate, remaining budget

    Example:
        monitor = SafetyMonitor(max_cost=5.0, max_time_hours=4.0, max_consecutive_failures=3)

        for issue in queue:
            can_continue, stop_reason = monitor.check_limits()
            if not can_continue:
                alert_user(stop_reason)
                break

            # Process issue...

            if success:
                monitor.record_issue_success(issue_num, cost, duration)
            else:
                monitor.record_issue_failure(issue_num, error, cost)
    """

    def __init__(
        self,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0,
        max_consecutive_failures: int = 3
    ):
        """
        Initialize safety monitor.

        Args:
            max_cost: Maximum API cost in USD (default: $5.00)
            max_time_hours: Maximum wall-clock time in hours (default: 4.0)
            max_consecutive_failures: Max consecutive failures before stop (default: 3)
        """
        self.max_cost = max_cost
        self.max_time_hours = max_time_hours
        self.max_consecutive_failures = max_consecutive_failures

        # Session tracking
        self.total_cost = 0.0
        self.start_time = time.time()
        self.consecutive_failures = 0
        self.issues_processed = 0
        self.issues_succeeded = 0
        self.issues_failed = 0

        # Per-issue tracking
        self.current_issue_number: Optional[int] = None
        self.current_issue_start_time: Optional[float] = None

        # History
        self.issue_history = []

        logger.info("="*70)
        logger.info("SAFETY MONITOR INITIALIZED")
        logger.info("="*70)
        logger.info(f"Max Cost: ${self.max_cost:.2f}")
        logger.info(f"Max Time: {self.max_time_hours:.1f}h")
        logger.info(f"Max Consecutive Failures: {self.max_consecutive_failures}")
        logger.info("="*70)

    def check_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Check if any safety limit has been exceeded.

        Returns:
            (can_continue: bool, stop_reason: Optional[str])

            - (True, None) = All limits OK, continue processing
            - (False, reason) = Limit exceeded, stop immediately
        """
        # Check cost limit
        if self.total_cost >= self.max_cost:
            reason = f"Cost limit reached: ${self.total_cost:.2f} >= ${self.max_cost:.2f}"
            logger.error(f"[SAFETY] {reason}")
            return False, reason

        # Check time limit
        elapsed_hours = (time.time() - self.start_time) / 3600
        if elapsed_hours >= self.max_time_hours:
            reason = f"Time limit reached: {elapsed_hours:.1f}h >= {self.max_time_hours:.1f}h"
            logger.error(f"[SAFETY] {reason}")
            return False, reason

        # Check failure circuit breaker
        if self.consecutive_failures >= self.max_consecutive_failures:
            reason = f"Circuit breaker tripped: {self.consecutive_failures} consecutive failures"
            logger.error(f"[SAFETY] {reason}")
            return False, reason

        return True, None

    def record_issue_start(self, issue_number: int):
        """
        Record the start of issue processing.

        Args:
            issue_number: GitHub issue number being processed
        """
        self.issues_processed += 1
        self.current_issue_number = issue_number
        self.current_issue_start_time = time.time()

        logger.info(f"[SAFETY] Starting issue #{issue_number} ({self.issues_processed} total)")

        # Log current budget status
        budget = self.get_remaining_budget()
        logger.info(
            f"[SAFETY] Budget remaining: "
            f"${budget['cost_remaining']} cost, "
            f"{budget['time_remaining_hours']} time, "
            f"{budget['failures_until_stop']} failures"
        )

    def record_issue_success(
        self,
        issue_number: int,
        cost: float,
        duration_sec: float
    ):
        """
        Record successful issue resolution.

        Args:
            issue_number: GitHub issue number
            cost: Estimated API cost in USD
            duration_sec: Processing duration in seconds
        """
        self.issues_succeeded += 1
        self.consecutive_failures = 0  # Reset failure counter
        self.total_cost += cost

        logger.info(
            f"[SAFETY] SUCCESS #{issue_number} | "
            f"Cost: ${cost:.4f} | "
            f"Time: {duration_sec:.1f}s"
        )
        logger.info(
            f"[SAFETY] Running totals: "
            f"${self.total_cost:.2f} cost, "
            f"{self.issues_succeeded}/{self.issues_processed} succeeded"
        )

        # Add to history
        self.issue_history.append({
            "issue_number": issue_number,
            "status": "success",
            "cost": cost,
            "duration_sec": duration_sec,
            "timestamp": datetime.now().isoformat()
        })

        # Clear current issue tracking
        self.current_issue_number = None
        self.current_issue_start_time = None

    def record_issue_failure(
        self,
        issue_number: int,
        error: str,
        cost: float = 0.0
    ):
        """
        Record failed issue attempt.

        Args:
            issue_number: GitHub issue number
            error: Error message describing failure
            cost: Partial API cost incurred (default: 0.0)
        """
        self.issues_failed += 1
        self.consecutive_failures += 1
        self.total_cost += cost  # Track partial costs even on failure

        logger.error(
            f"[SAFETY] FAILURE #{issue_number} | "
            f"Error: {error[:100]} | "
            f"Partial cost: ${cost:.4f}"
        )
        logger.error(
            f"[SAFETY] Consecutive failures: "
            f"{self.consecutive_failures}/{self.max_consecutive_failures}"
        )

        # Add to history
        duration_sec = 0.0
        if self.current_issue_start_time:
            duration_sec = time.time() - self.current_issue_start_time

        self.issue_history.append({
            "issue_number": issue_number,
            "status": "failed",
            "error": error,
            "cost": cost,
            "duration_sec": duration_sec,
            "timestamp": datetime.now().isoformat()
        })

        # Clear current issue tracking
        self.current_issue_number = None
        self.current_issue_start_time = None

    def get_current_issue_elapsed(self) -> Optional[float]:
        """
        Get elapsed time for current issue in seconds.

        Returns:
            Elapsed time in seconds, or None if no issue being processed
        """
        if self.current_issue_start_time is None:
            return None

        return time.time() - self.current_issue_start_time

    def is_current_issue_timeout(self, timeout_minutes: int = 30) -> bool:
        """
        Check if current issue has exceeded timeout.

        Args:
            timeout_minutes: Timeout threshold in minutes (default: 30)

        Returns:
            True if current issue has exceeded timeout, False otherwise
        """
        elapsed = self.get_current_issue_elapsed()
        if elapsed is None:
            return False

        timeout_sec = timeout_minutes * 60
        return elapsed >= timeout_sec

    def get_remaining_budget(self) -> Dict[str, Any]:
        """
        Get remaining budget for user visibility.

        Returns:
            Dict with remaining cost, time, failures, and session stats
        """
        elapsed_hours = (time.time() - self.start_time) / 3600

        success_rate = 0.0
        if self.issues_processed > 0:
            success_rate = (self.issues_succeeded / self.issues_processed) * 100

        return {
            "cost_remaining": f"${self.max_cost - self.total_cost:.2f}",
            "time_remaining_hours": f"{self.max_time_hours - elapsed_hours:.1f}h",
            "failures_until_stop": self.max_consecutive_failures - self.consecutive_failures,
            "total_cost": f"${self.total_cost:.2f}",
            "elapsed_time_hours": f"{elapsed_hours:.1f}h",
            "issues_processed": self.issues_processed,
            "issues_succeeded": self.issues_succeeded,
            "issues_failed": self.issues_failed,
            "success_rate": f"{success_rate:.0f}%",
            "consecutive_failures": self.consecutive_failures
        }

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get complete session summary.

        Returns:
            Dict with all session statistics and issue history
        """
        budget = self.get_remaining_budget()

        return {
            **budget,
            "max_cost": f"${self.max_cost:.2f}",
            "max_time_hours": f"{self.max_time_hours:.1f}h",
            "max_consecutive_failures": self.max_consecutive_failures,
            "issue_history": self.issue_history,
            "session_start": datetime.fromtimestamp(self.start_time).isoformat(),
            "session_end": datetime.now().isoformat()
        }

    def format_summary(self) -> str:
        """
        Format session summary as human-readable string.

        Returns:
            Formatted summary string
        """
        budget = self.get_remaining_budget()

        summary_lines = [
            "="*70,
            "SAFETY MONITOR - SESSION SUMMARY",
            "="*70,
            "",
            "Results:",
            f"  ✅ Successful: {self.issues_succeeded}",
            f"  ❌ Failed: {self.issues_failed}",
            f"  📋 Total Processed: {self.issues_processed}",
            f"  📈 Success Rate: {budget['success_rate']}",
            "",
            "Resources Used:",
            f"  💵 Total Cost: {budget['total_cost']}",
            f"  ⏱️  Total Time: {budget['elapsed_time_hours']}",
            "",
            "Remaining Budget:",
            f"  💰 Cost: {budget['cost_remaining']} (of ${self.max_cost:.2f})",
            f"  ⏲️  Time: {budget['time_remaining_hours']} (of {self.max_time_hours:.1f}h)",
            f"  🔁 Failures: {budget['failures_until_stop']} until circuit breaker",
            "",
            "="*70
        ]

        return "\n".join(summary_lines)


if __name__ == "__main__":
    # Test safety monitor
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\nTesting Safety Monitor...\n")

    # Test 1: Normal operation
    print("="*70)
    print("TEST 1: Normal Operation")
    print("="*70)

    monitor = SafetyMonitor(max_cost=5.0, max_time_hours=4.0, max_consecutive_failures=3)

    for i in range(1, 6):
        monitor.record_issue_start(i)

        # Simulate processing
        time.sleep(0.1)

        # Simulate success
        monitor.record_issue_success(i, cost=0.50, duration_sec=10.0)

        # Check limits
        can_continue, stop_reason = monitor.check_limits()
        print(f"\nIssue #{i} complete. Can continue: {can_continue}")

    print("\n" + monitor.format_summary())

    # Test 2: Cost limit
    print("\n\n" + "="*70)
    print("TEST 2: Cost Limit")
    print("="*70)

    monitor2 = SafetyMonitor(max_cost=2.0, max_time_hours=4.0, max_consecutive_failures=3)

    for i in range(1, 10):
        can_continue, stop_reason = monitor2.check_limits()
        if not can_continue:
            print(f"\n🛑 STOPPED: {stop_reason}")
            break

        monitor2.record_issue_start(i)
        monitor2.record_issue_success(i, cost=0.75, duration_sec=10.0)

    print("\n" + monitor2.format_summary())

    # Test 3: Failure circuit breaker
    print("\n\n" + "="*70)
    print("TEST 3: Failure Circuit Breaker")
    print("="*70)

    monitor3 = SafetyMonitor(max_cost=5.0, max_time_hours=4.0, max_consecutive_failures=3)

    for i in range(1, 10):
        can_continue, stop_reason = monitor3.check_limits()
        if not can_continue:
            print(f"\n🛑 STOPPED: {stop_reason}")
            break

        monitor3.record_issue_start(i)

        # Simulate failures
        if i % 2 == 0:
            monitor3.record_issue_failure(i, error="Test failure", cost=0.05)
        else:
            monitor3.record_issue_success(i, cost=0.25, duration_sec=5.0)

    print("\n" + monitor3.format_summary())

    print("\n✅ All safety monitor tests complete!")
