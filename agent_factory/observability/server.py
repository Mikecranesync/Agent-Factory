"""
Slack Server - FastAPI webhook handler for Slack commands and events
"""

import os
import re
import json
import hmac
import hashlib
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from .supervisor import SlackSupervisor, AgentCheckpoint, AgentStatus, get_supervisor
from .supervisor_db import SupervisoryDB, get_db

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    TEST = "test"
    REFACTOR = "refactor"
    DOCS = "docs"
    FIX = "fix"
    REVIEW = "review"
    ANALYZE = "analyze"
    BUILD = "build"
    DEPLOY = "deploy"
    UNKNOWN = "unknown"


@dataclass
class ParsedTask:
    task_type: TaskType
    description: str
    repo: Optional[str] = None
    scope: Optional[str] = None
    requested_by: Optional[str] = None
    channel: Optional[str] = None
    thread_ts: Optional[str] = None

    def to_prompt(self) -> str:
        parts = [self.description]
        if self.repo:
            parts.append(f"\nRepository: {self.repo}")
        if self.scope:
            parts.append(f"\nScope: {self.scope}")
        return "\n".join(parts)


class SlackServer:
    """FastAPI-based Slack command and event handler."""

    def __init__(
        self,
        signing_secret: Optional[str] = None,
        bot_token: Optional[str] = None,
        claude_code_path: str = "claude",
        work_dir: str = "/home/claude/agent-factory",
    ):
        self.signing_secret = signing_secret or os.getenv("SLACK_SIGNING_SECRET")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.claude_code_path = claude_code_path
        self.work_dir = work_dir

        self.supervisor = get_supervisor()
        self.db = get_db()
        self._client = httpx.AsyncClient(timeout=30.0)
        self._pending: Dict[str, ParsedTask] = {}

    def verify_signature(self, timestamp: str, body: bytes, signature: str) -> bool:
        if not self.signing_secret:
            return True
        sig_base = f"v0:{timestamp}:{body.decode()}"
        my_sig = "v0=" + hmac.new(self.signing_secret.encode(), sig_base.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(my_sig, signature)

    def parse_task(self, text: str, user: str, channel: str, thread_ts: Optional[str] = None) -> ParsedTask:
        text_lower = text.lower()

        patterns = {
            TaskType.TEST: r"\b(test|tests|testing|run tests)\b",
            TaskType.REFACTOR: r"\b(refactor|refactoring|restructure|rewrite)\b",
            TaskType.DOCS: r"\b(docs|documentation|document|docstrings)\b",
            TaskType.FIX: r"\b(fix|bug|issue|repair|resolve)\b",
            TaskType.REVIEW: r"\b(review|audit|check|inspect)\b",
            TaskType.ANALYZE: r"\b(analyze|analysis|investigate)\b",
            TaskType.BUILD: r"\b(build|compile|create)\b",
            TaskType.DEPLOY: r"\b(deploy|release|publish|ship)\b",
        }

        task_type = TaskType.UNKNOWN
        for t, p in patterns.items():
            if re.search(p, text_lower):
                task_type = t
                break

        repo = None
        repo_match = re.search(r"\b(?:in|for|on)\s+([a-zA-Z0-9_/-]+)", text_lower)
        if repo_match:
            repo = repo_match.group(1)

        return ParsedTask(
            task_type=task_type,
            description=text,
            repo=repo,
            requested_by=user,
            channel=channel,
            thread_ts=thread_ts,
        )

    def generate_plan(self, task: ParsedTask) -> str:
        plans = {
            TaskType.TEST: f"1. Analyze tests in {task.repo or 'repo'}\n2. Run test suite\n3. Generate coverage report\n4. Report results",
            TaskType.REFACTOR: f"1. Analyze code in {task.repo or 'target'}\n2. Identify improvements\n3. Implement changes\n4. Run tests\n5. Create PR",
            TaskType.DOCS: "1. Scan for undocumented code\n2. Generate docstrings\n3. Update README\n4. Create PR",
            TaskType.FIX: "1. Analyze issue\n2. Locate code\n3. Implement fix\n4. Add test\n5. Create PR",
        }
        return plans.get(task.task_type, f"1. Analyze: {task.description}\n2. Plan\n3. Execute\n4. Report")

    async def handle_slash_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text", "").strip()
        user_id = payload.get("user_id")
        channel_id = payload.get("channel_id")

        if not text:
            return {"response_type": "ephemeral", "text": "Usage: `/agent-task refactor auth in api-server`"}

        task = self.parse_task(text, user_id, channel_id)
        plan = self.generate_plan(task)

        task_key = f"{channel_id}:{datetime.now().timestamp()}"
        self._pending[task_key] = task

        return {
            "response_type": "in_channel",
            "blocks": self._approval_blocks(task, plan, task_key)
        }

    async def handle_app_mention(self, event: Dict[str, Any]) -> None:
        text = re.sub(r"<@[A-Z0-9]+>", "", event.get("text", "")).strip()
        user = event.get("user")
        channel = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")

        if not text:
            await self._reply(channel, thread_ts, "How can I help? Try: run tests, refactor code, generate docs")
            return

        task = self.parse_task(text, user, channel, thread_ts)
        plan = self.generate_plan(task)

        task_key = f"{channel}:{thread_ts}"
        self._pending[task_key] = task

        await self._post_blocks(channel, self._approval_blocks(task, plan, task_key), thread_ts)

    async def handle_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("actions", [{}])[0]
        action_id = action.get("action_id", "")
        value = action.get("value", "")
        user = payload.get("user", {}).get("id")

        if action_id == "approve_task":
            task = self._pending.pop(value, None)
            if task:
                asyncio.create_task(self._launch_agent(task))
                return {"replace_original": True, "text": f"✅ Approved by <@{user}>. Agent launching..."}

        elif action_id == "reject_task":
            self._pending.pop(value, None)
            return {"replace_original": True, "text": f"🛑 Rejected by <@{user}>."}

        elif action_id == "cancel_agent":
            return {"text": f"🛑 Cancel requested by <@{user}>"}

        return {}

    def _approval_blocks(self, task: ParsedTask, plan: str, task_key: str) -> List[Dict]:
        return [
            {"type": "header", "text": {"type": "plain_text", "text": f"🤖 Agent Task: {task.task_type.value.title()}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Request:*\n```{task.description}```"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Repo:* {task.repo or 'Auto-detect'}"},
                {"type": "mrkdwn", "text": f"*By:* <@{task.requested_by}>"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Plan:*\n```{plan}```"}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "👍 Approve"}, "style": "primary", "action_id": "approve_task", "value": task_key},
                {"type": "button", "text": {"type": "plain_text", "text": "👎 Reject"}, "style": "danger", "action_id": "reject_task", "value": task_key},
            ]}
        ]

    async def _launch_agent(self, task: ParsedTask) -> None:
        agent_id = f"agent-{task.task_type.value}-{int(datetime.now().timestamp())}"

        # Record in DB
        await self.db.connect()
        await self.db.create_task(
            agent_id=agent_id,
            task_type=task.task_type.value,
            task_name=task.description[:200],
            description=task.description,
            repo_scope=task.repo,
            slack_channel=task.channel,
            slack_thread_ts=task.thread_ts,
            requested_by=task.requested_by,
        )
        await self.db.update_task_status(agent_id, "running")

        # Post start to Slack
        await self.supervisor.post_task_start(
            agent_id=agent_id,
            task_name=task.description[:100],
            plan=task.to_prompt(),
            repo_scope=task.repo,
            channel=task.channel,
        )

        # Run Claude Code
        await self._run_claude_code(agent_id, task)

    async def _run_claude_code(self, agent_id: str, task: ParsedTask) -> None:
        cmd = [self.claude_code_path, "--print", "--output-format", "json", task.to_prompt()]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                result = json.loads(stdout.decode()) if stdout else {}
                await self.supervisor.post_task_complete(
                    agent_id=agent_id,
                    task_name=task.description[:100],
                    summary=result.get("result", "Completed"),
                    channel=task.channel,
                )
                await self.db.update_task_status(agent_id, "completed", 100, result.get("result"))
            else:
                error = stderr.decode() if stderr else "Unknown error"
                await self.supervisor.post_error(agent_id, task.description[:100], error, channel=task.channel)
                await self.db.update_task_status(agent_id, "failed", error_message=error)

        except Exception as e:
            await self.supervisor.post_error(agent_id, task.description[:100], str(e), channel=task.channel)
            await self.db.update_task_status(agent_id, "failed", error_message=str(e))

    async def _reply(self, channel: str, thread_ts: str, text: str):
        if not self.bot_token:
            return
        headers = {"Authorization": f"Bearer {self.bot_token}"}
        await self._client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json={"channel": channel, "thread_ts": thread_ts, "text": text},
        )

    async def _post_blocks(self, channel: str, blocks: List[Dict], thread_ts: Optional[str] = None):
        if not self.bot_token:
            return
        payload = {"channel": channel, "blocks": blocks}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        headers = {"Authorization": f"Bearer {self.bot_token}"}
        await self._client.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)


def create_app() -> FastAPI:
    """Create FastAPI app with all Slack handlers."""
    app = FastAPI(title="Agent Factory Supervisor")
    server = SlackServer()

    @app.on_event("startup")
    async def startup():
        await server.db.connect()

    @app.on_event("shutdown")
    async def shutdown():
        await server.db.close()
        await server._client.aclose()

    @app.post("/slack/events")
    async def slack_events(request: Request, background_tasks: BackgroundTasks):
        body = await request.body()
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")

        if not server.verify_signature(timestamp, body, signature):
            raise HTTPException(401, "Invalid signature")

        payload = await request.json()

        if payload.get("type") == "url_verification":
            return {"challenge": payload.get("challenge")}

        event = payload.get("event", {})
        if event.get("type") == "app_mention":
            background_tasks.add_task(server.handle_app_mention, event)

        return {"ok": True}

    @app.post("/slack/commands")
    async def slack_commands(request: Request):
        form = await request.form()
        return await server.handle_slash_command(dict(form))

    @app.post("/slack/interactions")
    async def slack_interactions(request: Request):
        form = await request.form()
        payload = json.loads(form.get("payload", "{}"))
        return JSONResponse(await server.handle_interaction(payload))

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/tasks")
    async def list_tasks(status: Optional[str] = None, limit: int = 50):
        return await server.db.list_tasks(status, limit)

    @app.get("/tasks/{agent_id}")
    async def get_task(agent_id: str):
        return await server.db.get_agent_stats(agent_id)

    @app.get("/metrics")
    async def get_metrics(days: int = 7):
        return await server.db.get_daily_metrics(days)

    return app


# CLI runner
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=3000)
