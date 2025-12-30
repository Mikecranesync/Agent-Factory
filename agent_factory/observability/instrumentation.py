"""
Agent Instrumentation - Decorators and context managers for checkpoint reporting
"""

import asyncio
import functools
import time
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional, Callable, List
from dataclasses import dataclass, field

from .supervisor import SlackSupervisor, AgentCheckpoint, AgentStatus, get_supervisor

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Context manager for tracking agent execution with automatic checkpointing."""

    agent_id: str
    task_name: str
    repo_scope: Optional[str] = None
    supervisor: Optional[SlackSupervisor] = None
    channel: Optional[str] = None
    auto_checkpoints: bool = True
    checkpoint_interval: int = 300
    context_limit: int = 200000

    _start_time: float = field(default=0, init=False)
    _tokens_used: int = field(default=0, init=False)
    _progress: int = field(default=0, init=False)
    _checkpoints_completed: List[str] = field(default_factory=list, init=False)
    _artifacts: List[str] = field(default_factory=list, init=False)
    _thread_ts: Optional[str] = field(default=None, init=False)
    _last_action: str = field(default="", init=False)
    _auto_task: Optional[asyncio.Task] = field(default=None, init=False)

    def __post_init__(self):
        if self.supervisor is None:
            self.supervisor = get_supervisor()

    async def __aenter__(self) -> "AgentContext":
        self._start_time = time.time()

        self._thread_ts = await self.supervisor.post_task_start(
            agent_id=self.agent_id,
            task_name=self.task_name,
            plan="Agent execution started",
            repo_scope=self.repo_scope,
            channel=self.channel,
        )

        if self.auto_checkpoints:
            self._auto_task = asyncio.create_task(self._auto_checkpoint_loop())

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._auto_task:
            self._auto_task.cancel()
            try:
                await self._auto_task
            except asyncio.CancelledError:
                pass

        if exc_type is not None:
            await self.supervisor.post_error(
                agent_id=self.agent_id,
                task_name=self.task_name,
                error=f"{exc_type.__name__}: {exc_val}",
                channel=self.channel,
            )
        else:
            await self.supervisor.post_task_complete(
                agent_id=self.agent_id,
                task_name=self.task_name,
                summary=self._last_action or "Task completed",
                artifacts=self._artifacts,
                channel=self.channel,
            )

        self.supervisor.clear_task(self.agent_id)
        return False

    async def _auto_checkpoint_loop(self):
        while True:
            await asyncio.sleep(self.checkpoint_interval)
            await self._post_state()

    async def _post_state(self):
        cp = AgentCheckpoint(
            agent_id=self.agent_id,
            task_name=self.task_name,
            status=AgentStatus.WORKING,
            progress=self._progress,
            tokens_used=self._tokens_used,
            context_limit=self.context_limit,
            last_action=self._last_action,
            repo_scope=self.repo_scope,
            elapsed_seconds=int(time.time() - self._start_time),
            checkpoints_completed=self._checkpoints_completed,
            artifacts=self._artifacts,
        )
        await self.supervisor.post_checkpoint(cp, channel=self.channel, thread_ts=self._thread_ts)

    async def checkpoint(
        self,
        action: str,
        progress: Optional[int] = None,
        tokens_used: Optional[int] = None,
        status: AgentStatus = AgentStatus.CHECKPOINT,
        force: bool = False,
    ):
        """Record a checkpoint."""
        self._last_action = action
        self._checkpoints_completed.append(action[:50])

        if progress is not None:
            self._progress = progress
        if tokens_used is not None:
            self._tokens_used = tokens_used

        cp = AgentCheckpoint(
            agent_id=self.agent_id,
            task_name=self.task_name,
            status=status,
            progress=self._progress,
            tokens_used=self._tokens_used,
            context_limit=self.context_limit,
            last_action=action,
            repo_scope=self.repo_scope,
            elapsed_seconds=int(time.time() - self._start_time),
            checkpoints_completed=self._checkpoints_completed,
            artifacts=self._artifacts,
        )

        await self.supervisor.post_checkpoint(
            cp, channel=self.channel, thread_ts=self._thread_ts, force=force
        )

    def add_artifact(self, artifact: str):
        self._artifacts.append(artifact)

    def update_tokens(self, tokens: int):
        self._tokens_used = tokens

    def set_progress(self, progress: int):
        self._progress = min(100, max(0, progress))

    @property
    def elapsed_seconds(self) -> int:
        return int(time.time() - self._start_time)


def supervised_agent(
    agent_id: str,
    task_name: str,
    repo_scope: Optional[str] = None,
    channel: Optional[str] = None,
    auto_checkpoints: bool = True,
):
    """Decorator to add Slack supervision to an agent function."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with AgentContext(
                agent_id=agent_id,
                task_name=task_name,
                repo_scope=repo_scope,
                channel=channel,
                auto_checkpoints=auto_checkpoints,
            ) as ctx:
                return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator


@asynccontextmanager
async def agent_task(
    agent_id: str,
    task_name: str,
    repo_scope: Optional[str] = None,
    channel: Optional[str] = None,
):
    """Async context manager for supervised agent tasks."""
    async with AgentContext(
        agent_id=agent_id,
        task_name=task_name,
        repo_scope=repo_scope,
        channel=channel,
    ) as ctx:
        yield ctx


class SyncCheckpointEmitter:
    """Sync checkpoint emitter for subprocess-based agents."""

    def __init__(
        self,
        agent_id: str,
        task_name: str,
        webhook_url: Optional[str] = None,
        repo_scope: Optional[str] = None,
    ):
        import requests
        self.agent_id = agent_id
        self.task_name = task_name
        self.repo_scope = repo_scope
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self._requests = requests
        self._start_time = time.time()
        self._progress = 0
        self._tokens_used = 0

    def emit(
        self,
        action: str,
        status: str = "checkpoint",
        progress: Optional[int] = None,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
    ):
        if progress is not None:
            self._progress = progress
        if tokens_used is not None:
            self._tokens_used = tokens_used

        status_enum = AgentStatus(status)

        payload = {
            "attachments": [{
                "color": status_enum.color,
                "title": f"{status_enum.emoji} Agent `{self.agent_id}` – {status.upper()}",
                "fields": [
                    {"title": "Task", "value": self.task_name, "short": True},
                    {"title": "Progress", "value": f"{self._progress}%", "short": True},
                    {"title": "Action", "value": action, "short": False},
                    {"title": "Elapsed", "value": f"{int(time.time() - self._start_time)}s", "short": True},
                ],
                "footer": "Agent Factory",
            }]
        }

        if self.repo_scope:
            payload["attachments"][0]["fields"].insert(2, {"title": "Repo", "value": self.repo_scope, "short": True})

        if error:
            payload["attachments"][0]["fields"].append({"title": "🔴 Error", "value": error, "short": False})

        if self.webhook_url:
            try:
                self._requests.post(self.webhook_url, json=payload, timeout=10)
            except Exception as e:
                logger.error(f"Checkpoint emit failed: {e}")

        logger.info(f"[{self.agent_id}] {status}: {action}")
