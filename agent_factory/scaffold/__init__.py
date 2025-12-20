"""SCAFFOLD Platform - Autonomous Development System

SCAFFOLD = Specification-driven Autonomous Code generation Framework
          for Orchestrated Large-scale Development

Components:
- WorktreeManager: Manages isolated git worktrees for parallel task execution
- ContextAssembler: Prepares execution context for Claude Code CLI
- ClaudeExecutor: Executes tasks using Claude Code CLI in headless mode
- PRCreator: Creates draft PRs automatically after task completion (Phase 3)
"""

from agent_factory.scaffold.models import (
    WorktreeMetadata,
    TaskContext,
    ExecutionResult
)
from agent_factory.scaffold.worktree_manager import (
    WorktreeManager,
    WorktreeManagerError,
    WorktreeExistsError,
    WorktreeNotFoundError,
    WorktreeLimitError,
)
from agent_factory.scaffold.claude_executor import (
    ClaudeExecutor,
    ClaudeExecutorError,
    create_claude_executor
)
from agent_factory.scaffold.safety_rails import (
    SafetyRails,
    SafetyRailsConfig,
    SafetyRailsError,
    RetryState,
    CostEstimate,
    ValidationFailureReason,
)

__all__ = [
    # Models
    "WorktreeMetadata",
    "TaskContext",
    "ExecutionResult",
    # WorktreeManager
    "WorktreeManager",
    "WorktreeManagerError",
    "WorktreeExistsError",
    "WorktreeNotFoundError",
    "WorktreeLimitError",
    # ClaudeExecutor
    "ClaudeExecutor",
    "ClaudeExecutorError",
    "create_claude_executor",
    # SafetyRails
    "SafetyRails",
    "SafetyRailsConfig",
    "SafetyRailsError",
    "RetryState",
    "CostEstimate",
    "ValidationFailureReason",
]

__version__ = "0.1.0"
