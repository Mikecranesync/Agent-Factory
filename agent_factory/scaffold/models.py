"""SCAFFOLD Platform - Data Models

Data models for SCAFFOLD autonomous development system.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WorktreeMetadata:
    """Metadata for a git worktree managed by SCAFFOLD.

    Attributes:
        task_id: Unique task identifier (e.g., "task-42")
        worktree_path: Absolute path to worktree directory
        branch_name: Git branch name (e.g., "autonomous/task-42")
        created_at: ISO 8601 timestamp of creation
        creator: Who created this worktree (e.g., "scaffold-orchestrator", "agentcli")
        status: Current status (active|stale|merged|abandoned)
        pr_url: GitHub PR URL if created (optional)
    """
    task_id: str
    worktree_path: str
    branch_name: str
    created_at: str
    creator: str
    status: str  # "active", "stale", "merged", "abandoned"
    pr_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "worktree_path": self.worktree_path,
            "branch_name": self.branch_name,
            "created_at": self.created_at,
            "creator": self.creator,
            "status": self.status,
            "pr_url": self.pr_url
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorktreeMetadata":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            task_id=data["task_id"],
            worktree_path=data["worktree_path"],
            branch_name=data["branch_name"],
            created_at=data["created_at"],
            creator=data["creator"],
            status=data["status"],
            pr_url=data.get("pr_url")
        )


@dataclass
class TaskContext:
    """Task specification for SCAFFOLD execution.

    Attributes:
        task_id: Unique task identifier (e.g., "task-42")
        title: Task title
        description: Detailed task description
        acceptance_criteria: List of acceptance criteria
        priority: Task priority (high|medium|low)
        labels: Task labels/tags
    """
    task_id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str
    labels: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority,
            "labels": self.labels
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskContext":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            acceptance_criteria=data["acceptance_criteria"],
            priority=data["priority"],
            labels=data["labels"]
        )


@dataclass
class SessionState:
    """Persistent session state for SCAFFOLD orchestrator.

    Attributes:
        session_id: Unique session identifier (e.g., "20251218_140000")
        start_time: ISO 8601 timestamp of session start
        max_tasks: Maximum tasks to process in this session
        max_cost: Maximum API cost in USD
        max_time_hours: Maximum wall-clock time in hours
        tasks_queued: List of task IDs queued for execution
        tasks_in_progress: Dict mapping task_id -> worktree_path
        tasks_completed: List of task IDs successfully completed
        tasks_failed: List of task IDs that failed
        total_cost: Total API cost incurred (USD)
        total_duration_sec: Total execution time (seconds)
    """
    session_id: str
    start_time: str  # ISO 8601
    max_tasks: int
    max_cost: float
    max_time_hours: float
    tasks_queued: List[str]
    tasks_in_progress: dict  # task_id -> worktree_path
    tasks_completed: List[str]
    tasks_failed: List[str]
    total_cost: float = 0.0
    total_duration_sec: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "max_tasks": self.max_tasks,
            "max_cost": self.max_cost,
            "max_time_hours": self.max_time_hours,
            "tasks_queued": self.tasks_queued,
            "tasks_in_progress": self.tasks_in_progress,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_cost": self.total_cost,
            "total_duration_sec": self.total_duration_sec
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            max_tasks=data["max_tasks"],
            max_cost=data["max_cost"],
            max_time_hours=data["max_time_hours"],
            tasks_queued=data["tasks_queued"],
            tasks_in_progress=data["tasks_in_progress"],
            tasks_completed=data["tasks_completed"],
            tasks_failed=data["tasks_failed"],
            total_cost=data.get("total_cost", 0.0),
            total_duration_sec=data.get("total_duration_sec", 0.0)
        )
