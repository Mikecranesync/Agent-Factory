"""
Database Client - Async PostgreSQL for audit trail
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)


class SupervisoryDB:
    """Async PostgreSQL client for agent supervisory data."""

    def __init__(self, dsn: Optional[str] = None, pool_size: int = 10):
        self.dsn = dsn or os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
        self.pool_size = pool_size
        self._pool: Optional[Pool] = None

    async def connect(self) -> None:
        if self._pool is not None:
            return
        self._pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=self.pool_size, command_timeout=60)
        logger.info("Database pool created")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.close()

    @asynccontextmanager
    async def conn(self):
        if self._pool is None:
            await self.connect()
        async with self._pool.acquire() as c:
            yield c

    # ==================== Tasks ====================

    async def create_task(
        self,
        agent_id: str,
        task_type: str,
        task_name: str,
        description: Optional[str] = None,
        repo_scope: Optional[str] = None,
        slack_channel: Optional[str] = None,
        slack_thread_ts: Optional[str] = None,
        requested_by: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        async with self.conn() as c:
            row = await c.fetchrow(
                """
                INSERT INTO agent_tasks (agent_id, task_type, task_name, description, repo_scope,
                    slack_channel, slack_thread_ts, requested_by, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                agent_id, task_type, task_name, description, repo_scope,
                slack_channel, slack_thread_ts, requested_by, json.dumps(metadata or {}),
            )
            return str(row["id"])

    async def update_task_status(
        self,
        agent_id: str,
        status: str,
        progress: Optional[int] = None,
        result_summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[str]:
        async with self.conn() as c:
            row = await c.fetchrow(
                """
                UPDATE agent_tasks SET
                    status = $2,
                    progress = COALESCE($3, progress),
                    result_summary = COALESCE($4, result_summary),
                    error_message = COALESCE($5, error_message),
                    started_at = CASE WHEN $2 = 'running' AND started_at IS NULL THEN NOW() ELSE started_at END,
                    completed_at = CASE WHEN $2 IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE completed_at END
                WHERE agent_id = $1
                RETURNING id
                """,
                agent_id, status, progress, result_summary, error_message,
            )
            return str(row["id"]) if row else None

    async def get_task(self, agent_id: str) -> Optional[Dict]:
        async with self.conn() as c:
            row = await c.fetchrow("SELECT * FROM agent_tasks WHERE agent_id = $1", agent_id)
            return dict(row) if row else None

    async def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        async with self.conn() as c:
            if status:
                rows = await c.fetch(
                    "SELECT * FROM agent_tasks WHERE status = $1 ORDER BY created_at DESC LIMIT $2",
                    status, limit
                )
            else:
                rows = await c.fetch(
                    "SELECT * FROM agent_tasks ORDER BY created_at DESC LIMIT $1", limit
                )
            return [dict(r) for r in rows]

    # ==================== Checkpoints ====================

    async def record_checkpoint(
        self,
        agent_id: str,
        checkpoint_type: str,
        action: str,
        progress: int = 0,
        tokens_used: int = 0,
        status: str = "working",
        elapsed_seconds: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        async with self.conn() as c:
            task = await c.fetchrow("SELECT id FROM agent_tasks WHERE agent_id = $1", agent_id)
            task_id = task["id"] if task else None

            row = await c.fetchrow(
                """
                INSERT INTO agent_checkpoints (task_id, agent_id, checkpoint_type, action_description,
                    progress, tokens_used, status, elapsed_seconds, error_message, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                task_id, agent_id, checkpoint_type, action, progress, tokens_used,
                status, elapsed_seconds, error_message, json.dumps(metadata or {}),
            )

            if task_id:
                await c.execute("UPDATE agent_tasks SET progress = $1 WHERE id = $2", progress, task_id)

            return str(row["id"])

    async def get_checkpoints(self, agent_id: str, limit: int = 100) -> List[Dict]:
        async with self.conn() as c:
            rows = await c.fetch(
                "SELECT * FROM agent_checkpoints WHERE agent_id = $1 ORDER BY created_at DESC LIMIT $2",
                agent_id, limit
            )
            return [dict(r) for r in rows]

    # ==================== Interventions ====================

    async def record_intervention(
        self,
        agent_id: str,
        intervention_type: str,
        user_id: str,
        action_details: Optional[str] = None,
    ) -> str:
        async with self.conn() as c:
            task = await c.fetchrow("SELECT id FROM agent_tasks WHERE agent_id = $1", agent_id)
            row = await c.fetchrow(
                """
                INSERT INTO human_interventions (task_id, agent_id, intervention_type, user_id, action_details)
                VALUES ($1, $2, $3, $4, $5) RETURNING id
                """,
                task["id"] if task else None, agent_id, intervention_type, user_id, action_details,
            )
            return str(row["id"])

    # ==================== Artifacts ====================

    async def add_artifact(
        self,
        agent_id: str,
        artifact_type: str,
        name: str,
        url: Optional[str] = None,
        content: Optional[str] = None,
    ) -> str:
        async with self.conn() as c:
            task = await c.fetchrow("SELECT id FROM agent_tasks WHERE agent_id = $1", agent_id)
            row = await c.fetchrow(
                """
                INSERT INTO task_artifacts (task_id, agent_id, artifact_type, artifact_name, artifact_url, artifact_content)
                VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
                """,
                task["id"] if task else None, agent_id, artifact_type, name, url, content,
            )
            return str(row["id"])

    async def get_artifacts(self, agent_id: str) -> List[Dict]:
        async with self.conn() as c:
            rows = await c.fetch(
                "SELECT * FROM task_artifacts WHERE agent_id = $1 ORDER BY created_at", agent_id
            )
            return [dict(r) for r in rows]

    # ==================== Metrics ====================

    async def get_daily_metrics(self, days: int = 7) -> List[Dict]:
        async with self.conn() as c:
            rows = await c.fetch(
                """
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))
                        FILTER (WHERE completed_at IS NOT NULL) as avg_duration
                FROM agent_tasks
                WHERE created_at >= CURRENT_DATE - $1
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                """,
                days
            )
            return [dict(r) for r in rows]

    async def get_agent_stats(self, agent_id: str) -> Dict:
        async with self.conn() as c:
            task = await c.fetchrow("SELECT * FROM agent_tasks WHERE agent_id = $1", agent_id)
            if not task:
                return {}

            cp_count = await c.fetchval("SELECT COUNT(*) FROM agent_checkpoints WHERE agent_id = $1", agent_id)
            art_count = await c.fetchval("SELECT COUNT(*) FROM task_artifacts WHERE agent_id = $1", agent_id)

            return {"task": dict(task), "checkpoints": cp_count, "artifacts": art_count}


_db: Optional[SupervisoryDB] = None

def get_db() -> SupervisoryDB:
    global _db
    if _db is None:
        _db = SupervisoryDB()
    return _db
