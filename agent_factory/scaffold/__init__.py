"""SCAFFOLD Platform - Autonomous Development System

SCAFFOLD = Specification-driven Autonomous Code generation Framework
          for Orchestrated Large-scale Development

Components:
- WorktreeManager: Manages isolated git worktrees for parallel task execution
- ContextAssembler: Prepares execution context for Claude Code CLI
- ClaudeExecutor: Executes tasks using Claude Code CLI in headless mode
- PRCreator: Creates draft PRs automatically after task completion
- StatusSyncer: Auto-updates Backlog.md task status
"""

from agent_factory.scaffold.models import WorktreeMetadata, TaskContext
from agent_factory.scaffold.worktree_manager import (
    WorktreeManager,
    WorktreeManagerError,
    WorktreeExistsError,
    WorktreeNotFoundError,
    WorktreeLimitError,
)
from agent_factory.scaffold.status_syncer import (
    StatusSyncer,
    StatusSyncerError,
    create_status_syncer
)

__all__ = [
    # Models
    "WorktreeMetadata",
    "TaskContext",
    # WorktreeManager
    "WorktreeManager",
    "WorktreeManagerError",
    "WorktreeExistsError",
    "WorktreeNotFoundError",
    "WorktreeLimitError",
    # StatusSyncer
    "StatusSyncer",
    "StatusSyncerError",
    "create_status_syncer",
]

__version__ = "0.1.0"
