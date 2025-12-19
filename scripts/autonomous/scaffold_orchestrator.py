#!/usr/bin/env python3
"""
SCAFFOLD Orchestrator - Main CLI Entry Point

Autonomous task execution system for Agent Factory.

Workflow:
1. Fetch eligible tasks from Backlog.md
2. Route to handlers (Claude Code CLI, manual, etc.)
3. Execute in isolated git worktrees
4. Create draft PRs
5. Update Backlog.md status

Usage:
    # Basic usage
    python scripts/autonomous/scaffold_orchestrator.py

    # Dry run (no execution, just logging)
    DRY_RUN=true python scripts/autonomous/scaffold_orchestrator.py

    # Custom limits
    MAX_TASKS=5 MAX_COST=3.0 python scripts/autonomous/scaffold_orchestrator.py

    # Filter by labels
    python scripts/autonomous/scaffold_orchestrator.py --labels build,rivet-pro

Environment Variables:
    MAX_TASKS: Maximum tasks to process (default: 10)
    MAX_CONCURRENT: Maximum concurrent worktrees (default: 3)
    MAX_COST: Maximum API cost in USD (default: 5.0)
    MAX_TIME_HOURS: Maximum wall-clock time in hours (default: 4.0)
    DRY_RUN: Dry run mode (default: false)
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from agent_factory.scaffold.orchestrator import ScaffoldOrchestrator

# Configuration from environment
MAX_TASKS = int(os.getenv("MAX_TASKS", "10"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "3"))
MAX_COST = float(os.getenv("MAX_COST", "5.0"))
MAX_TIME_HOURS = float(os.getenv("MAX_TIME_HOURS", "4.0"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# Logging configuration
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"scaffold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("scaffold_cli")


def parse_args():
    """Parse command-line arguments.

    Returns:
        Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="SCAFFOLD Orchestrator - Autonomous Task Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with 3 tasks
  DRY_RUN=true MAX_TASKS=3 python scripts/autonomous/scaffold_orchestrator.py

  # Filter by labels
  python scripts/autonomous/scaffold_orchestrator.py --labels build,rivet-pro

  # Custom limits
  python scripts/autonomous/scaffold_orchestrator.py --max-cost 3.0 --max-time 2.0
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=DRY_RUN,
        help="Dry run mode (no execution, just logging)"
    )

    parser.add_argument(
        "--max-tasks",
        type=int,
        default=MAX_TASKS,
        help=f"Maximum tasks to process (default: {MAX_TASKS})"
    )

    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=MAX_CONCURRENT,
        help=f"Maximum concurrent worktrees (default: {MAX_CONCURRENT})"
    )

    parser.add_argument(
        "--max-cost",
        type=float,
        default=MAX_COST,
        help=f"Maximum API cost in USD (default: {MAX_COST})"
    )

    parser.add_argument(
        "--max-time",
        type=float,
        default=MAX_TIME_HOURS,
        help=f"Maximum wall-clock time in hours (default: {MAX_TIME_HOURS})"
    )

    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Filter tasks by labels (comma-separated, e.g., 'build,rivet-pro')"
    )

    return parser.parse_args()


def main():
    """Main entry point."""

    args = parse_args()

    # Parse labels
    labels = None
    if args.labels:
        labels = [l.strip() for l in args.labels.split(",")]

    # Log configuration
    logger.info("="*60)
    logger.info("SCAFFOLD Orchestrator Starting")
    logger.info("="*60)
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Max Tasks: {args.max_tasks}")
    logger.info(f"Max Concurrent: {args.max_concurrent}")
    logger.info(f"Max Cost: ${args.max_cost:.2f}")
    logger.info(f"Max Time: {args.max_time}h")
    if labels:
        logger.info(f"Label Filter: {labels}")
    logger.info(f"Log File: {log_file}")
    logger.info("="*60)

    # Create orchestrator
    try:
        orchestrator = ScaffoldOrchestrator(
            repo_root=Path.cwd(),
            dry_run=args.dry_run,
            max_tasks=args.max_tasks,
            max_concurrent=args.max_concurrent,
            max_cost=args.max_cost,
            max_time_hours=args.max_time,
            labels=labels
        )

        # Run
        summary = orchestrator.run()

        # Print summary
        print("\n" + "="*60)
        print("SCAFFOLD Session Summary")
        print("="*60)
        print(f"Session ID: {summary.get('session_id', 'unknown')}")
        print(f"Dry Run: {summary.get('dry_run', False)}")
        print(f"Tasks Queued: {summary.get('tasks_queued', 0)}")
        print(f"Tasks In Progress: {summary.get('tasks_in_progress', 0)}")
        print(f"Tasks Completed: {summary.get('tasks_completed', 0)}")
        print(f"Tasks Failed: {summary.get('tasks_failed', 0)}")
        print(f"Total Cost: ${summary.get('total_cost', 0.0):.2f}")
        print(f"Total Duration: {summary.get('total_duration_sec', 0.0):.1f}s")
        print("="*60)
        print(f"\nLog file: {log_file}")

        # Exit code
        if summary.get("dry_run"):
            # Dry run: exit 0 (success)
            sys.exit(0)
        elif summary.get("tasks_completed", 0) > 0:
            # At least one task completed: exit 0 (success)
            sys.exit(0)
        elif summary.get("tasks_failed", 0) > 0:
            # All tasks failed: exit 1 (failure)
            sys.exit(1)
        else:
            # No tasks processed: exit 2 (no work)
            sys.exit(2)

    except KeyboardInterrupt:
        logger.warning("\nSession interrupted by user (Ctrl+C)")
        print("\n\nSession interrupted.")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n\nFatal error: {e}")
        print(f"See log file for details: {log_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
