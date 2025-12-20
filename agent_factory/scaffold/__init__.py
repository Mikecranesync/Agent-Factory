"""SCAFFOLD Platform - Autonomous Development System

SCAFFOLD = Specification-driven Autonomous Code generation Framework
          for Orchestrated Large-scale Development

Components:
- WorktreeManager: Manages isolated git worktrees for parallel task execution
- ContextAssembler: Prepares execution context for Claude Code CLI
- ClaudeExecutor: Executes tasks using Claude Code CLI in headless mode
- PRCreator: Creates draft PRs automatically after task completion
"""

from agent_factory.scaffold.models import WorktreeMetadata, TaskContext
from agent_factory.scaffold.worktree_manager import (
    WorktreeManager,
    WorktreeManagerError,
    WorktreeExistsError,
    WorktreeNotFoundError,
    WorktreeLimitError,
)
from agent_factory.scaffold.pr_creator import (
    PRCreator,
    PRCreatorError,
    create_pr_creator
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
    # PRCreator
    "PRCreator",
    "PRCreatorError",
    "create_pr_creator",
]

__version__ = "0.1.0"
