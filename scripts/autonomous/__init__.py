"""
Autonomous Claude System

Enables Claude to work autonomously at night processing GitHub issues.

Components:
- issue_queue_builder.py: Score and rank all open issues
- safety_monitor.py: Enforce cost/time/failure limits
- autonomous_claude_runner.py: Main orchestrator
- claude_executor.py: Per-issue Claude Code Action wrapper
- pr_creator.py: Create draft PRs
- telegram_notifier.py: Real-time session notifications
"""

__version__ = "1.0.0"
