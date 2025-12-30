"""
Slack Supervisor - Real-time agent observability via Slack
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    STARTING = "starting"
    PLANNING = "planning"
    WORKING = "working"
    CHECKPOINT = "checkpoint"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    ERROR = "error"
    COMPLETE = "complete"
    CANCELLED = "cancelled"

    @property
    def color(self) -> str:
        return {
            "starting": "#0099ff",
            "planning": "#9933ff",
            "working": "#00cc00",
            "checkpoint": "#ffcc00",
            "waiting_approval": "#ff9900",
            "blocked": "#ff6600",
            "error": "#ff0000",
            "complete": "#00cc00",
            "cancelled": "#808080",
        }.get(self.value, "#808080")

    @property
    def emoji(self) -> str:
        return {
            "starting": "🚀",
            "planning": "🧠",
            "working": "⚙️",
            "checkpoint": "📍",
            "waiting_approval": "⏳",
            "blocked": "🚧",
            "error": "❌",
            "complete": "✅",
            "cancelled": "🛑",
        }.get(self.value, "📋")


@dataclass
class AgentCheckpoint:
    """Structured checkpoint data for agent state reporting."""
    agent_id: str
    task_name: str
    status: AgentStatus
    progress: int = 0
    tokens_used: int = 0
    context_limit: int = 200000
    last_action: str = ""
    repo_scope: Optional[str] = None
    elapsed_seconds: int = 0
    checkpoints_completed: List[str] = field(default_factory=list)
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def context_usage_percent(self) -> float:
        return (self.tokens_used / self.context_limit) * 100 if self.context_limit > 0 else 0

    @property
    def context_warning(self) -> bool:
        return self.context_usage_percent > 70

    def to_slack_fields(self) -> List[Dict[str, Any]]:
        fields = [
            {"title": "Task", "value": self.task_name, "short": True},
            {"title": "Progress", "value": f"{self.progress}%", "short": True},
        ]

        if self.repo_scope:
            fields.append({"title": "Repo", "value": self.repo_scope, "short": True})

        ctx_val = f"{self.tokens_used:,} / {self.context_limit:,} ({self.context_usage_percent:.1f}%)"
        if self.context_warning:
            ctx_val = f"⚠️ {ctx_val}"
        fields.append({"title": "Context", "value": ctx_val, "short": True})

        if self.last_action:
            fields.append({"title": "Last Action", "value": self.last_action, "short": False})

        fields.append({"title": "Elapsed", "value": self._format_elapsed(), "short": True})

        if self.checkpoints_completed:
            fields.append({
                "title": "Steps",
                "value": " → ".join(self.checkpoints_completed[-5:]),
                "short": False
            })

        if self.error:
            fields.append({"title": "🔴 Error", "value": self.error, "short": False})

        if self.artifacts:
            fields.append({
                "title": "Artifacts",
                "value": "\n".join(f"• {a}" for a in self.artifacts),
                "short": False
            })

        return fields

    def _format_elapsed(self) -> str:
        s = self.elapsed_seconds
        if s < 60:
            return f"{s}s"
        elif s < 3600:
            return f"{s // 60}m {s % 60}s"
        else:
            return f"{s // 3600}h {(s % 3600) // 60}m"


class SlackSupervisor:
    """Slack-based supervisory control plane for agents."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: str = "#agent-supervisory",
        min_checkpoint_interval: int = 30,
    ):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = default_channel
        self.min_checkpoint_interval = min_checkpoint_interval

        self._task_threads: Dict[str, str] = {}
        self._last_checkpoint: Dict[str, datetime] = {}
        self._client = httpx.AsyncClient(timeout=30.0)

        if not self.webhook_url and not self.bot_token:
            logger.warning("No Slack credentials - updates will be logged only")

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    def _should_post(self, agent_id: str, force: bool = False) -> bool:
        if force:
            return True
        last = self._last_checkpoint.get(agent_id)
        if not last:
            return True
        return (datetime.now(timezone.utc) - last).total_seconds() >= self.min_checkpoint_interval

    async def post_checkpoint(
        self,
        checkpoint: AgentCheckpoint,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None,
        force: bool = False,
    ) -> Optional[str]:
        """Post checkpoint to Slack. Returns thread_ts for replies."""
        if not self._should_post(checkpoint.agent_id, force):
            return self._task_threads.get(checkpoint.agent_id)

        channel = channel or self.default_channel
        thread_ts = thread_ts or self._task_threads.get(checkpoint.agent_id)

        payload = self._build_payload(checkpoint, channel, thread_ts)
        logger.info(f"Checkpoint [{checkpoint.agent_id}]: {checkpoint.status.value} - {checkpoint.last_action}")

        if not self.webhook_url and not self.bot_token:
            return None

        try:
            if self.bot_token:
                result = await self._post_via_api(payload)
            else:
                result = await self._post_via_webhook(payload)

            if result and "ts" in result:
                new_ts = result.get("ts")
                if not thread_ts:
                    self._task_threads[checkpoint.agent_id] = new_ts
                self._last_checkpoint[checkpoint.agent_id] = datetime.now(timezone.utc)
                return new_ts
            return thread_ts
        except Exception as e:
            logger.error(f"Slack post failed: {e}")
            return None

    def _build_payload(self, cp: AgentCheckpoint, channel: str, thread_ts: Optional[str]) -> Dict:
        title = f"{cp.status.emoji} Agent `{cp.agent_id}` – {cp.status.value.upper()}"

        payload = {
            "channel": channel,
            "attachments": [{
                "color": cp.status.color,
                "title": title,
                "fields": cp.to_slack_fields(),
                "footer": "Agent Factory",
                "ts": int(datetime.now().timestamp()),
            }],
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        if cp.context_usage_percent > 85:
            payload["text"] = f"⚠️ *Context Warning*: `{cp.agent_id}` at {cp.context_usage_percent:.0f}%"

        return payload

    async def _post_via_webhook(self, payload: Dict) -> Optional[Dict]:
        resp = await self._client.post(self.webhook_url, json=payload)
        resp.raise_for_status()
        return {"ok": True}

    async def _post_via_api(self, payload: Dict) -> Optional[Dict]:
        headers = {"Authorization": f"Bearer {self.bot_token}", "Content-Type": "application/json"}
        resp = await self._client.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            raise Exception(f"Slack API error: {result.get('error')}")
        return result

    async def post_task_start(
        self,
        agent_id: str,
        task_name: str,
        plan: str,
        repo_scope: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Optional[str]:
        """Post task start. Returns thread_ts."""
        cp = AgentCheckpoint(
            agent_id=agent_id,
            task_name=task_name,
            status=AgentStatus.STARTING,
            last_action=f"Plan:\n{plan[:500]}{'...' if len(plan) > 500 else ''}",
            repo_scope=repo_scope,
        )
        return await self.post_checkpoint(cp, channel=channel, force=True)

    async def post_task_complete(
        self,
        agent_id: str,
        task_name: str,
        summary: str,
        artifacts: List[str] = None,
        pr_url: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Optional[str]:
        cp = AgentCheckpoint(
            agent_id=agent_id,
            task_name=task_name,
            status=AgentStatus.COMPLETE,
            progress=100,
            last_action=summary,
            artifacts=artifacts or [],
        )
        if pr_url:
            cp.artifacts.append(f"<{pr_url}|Pull Request>")
        return await self.post_checkpoint(cp, channel=channel, force=True)

    async def post_error(
        self,
        agent_id: str,
        task_name: str,
        error: str,
        retry_count: int = 0,
        channel: Optional[str] = None,
    ) -> Optional[str]:
        cp = AgentCheckpoint(
            agent_id=agent_id,
            task_name=task_name,
            status=AgentStatus.ERROR,
            error=f"{error}\n(Retry: {retry_count})" if retry_count else error,
        )
        return await self.post_checkpoint(cp, channel=channel, force=True)

    def clear_task(self, agent_id: str):
        self._task_threads.pop(agent_id, None)
        self._last_checkpoint.pop(agent_id, None)


# Module-level singleton
_supervisor: Optional[SlackSupervisor] = None

def get_supervisor() -> SlackSupervisor:
    global _supervisor
    if _supervisor is None:
        _supervisor = SlackSupervisor()
    return _supervisor
