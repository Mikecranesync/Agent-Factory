"""
Agent Execution Tracer - Context manager for tracing agent executions.

Automatically captures:
- Execution duration (ms)
- Token usage (LLM calls)
- Cost (USD)
- Success/failure status
- Error messages

Writes to agent_traces database table for full traceability.

Usage:
    >>> from agent_factory.core.database_manager import DatabaseManager
    >>> from agent_factory.observability.agent_tracer import AgentTracer
    >>>
    >>> db = DatabaseManager()
    >>> session_id = "abc-123"
    >>>
    >>> async with AgentTracer(session_id, "AtomBuilder", db) as tracer:
    ...     atoms = await build_atoms_from_pdf(pdf_path)
    ...     tracer.metadata["atoms_created"] = len(atoms)
    ...     # Trace automatically written to database on exit
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AgentTracer:
    """
    Context manager for tracing agent executions with database persistence.

    Captures execution metadata and writes to agent_traces table.
    Enables full traceability: atom → session → agents
    """

    def __init__(self, session_id: str, agent_name: str, db):
        """
        Initialize agent tracer.

        Args:
            session_id: UUID of the ingestion session this agent is part of
            agent_name: Name of the agent (AtomBuilder, CitationValidator, etc.)
            db: DatabaseManager instance for writing traces
        """
        self.session_id = session_id
        self.agent_name = agent_name
        self.db = db
        self.trace_id = str(uuid.uuid4())
        self.started_at: Optional[datetime] = None

        # Metadata dict - agents can update this during execution
        self.metadata: Dict[str, Any] = {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "success": True,
            "error_message": None
        }

    async def __aenter__(self):
        """Context manager entry - start timing."""
        self.started_at = datetime.now(timezone.utc)
        logger.debug(f"[{self.trace_id}] Started tracing {self.agent_name} for session {self.session_id}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - calculate duration and write to database.

        Automatically captures exceptions and marks success=False.
        """
        # Calculate duration
        if self.started_at is None:
            logger.error(f"[{self.trace_id}] Agent trace started_at is None, using NOW()")
            self.started_at = datetime.now(timezone.utc)

        duration_ms = int((datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000)

        # If exception occurred, mark as failed
        if exc_type:
            self.metadata["success"] = False
            self.metadata["error_message"] = str(exc_val)
            logger.error(
                f"[{self.trace_id}] {self.agent_name} failed: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )

        # Write trace to database
        try:
            await self._write_trace(duration_ms)
        except Exception as e:
            # NEVER let trace writing break the pipeline
            logger.error(f"[{self.trace_id}] Failed to write agent trace: {e}", exc_info=True)

        # Don't suppress exceptions
        return False

    async def _write_trace(self, duration_ms: int):
        """
        Write trace record to agent_traces table.

        Args:
            duration_ms: Execution duration in milliseconds
        """
        query = """
            INSERT INTO agent_traces (
                trace_id, session_id, agent_name, duration_ms,
                tokens_used, cost_usd, success, error_message, started_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        params = (
            self.trace_id,
            self.session_id,
            self.agent_name,
            duration_ms,
            self.metadata.get("tokens_used", 0),
            self.metadata.get("cost_usd", 0.0),
            self.metadata.get("success", True),
            self.metadata.get("error_message"),
            self.started_at
        )

        # Execute query (async if db supports it, else run in executor)
        if hasattr(self.db, 'execute_query_async'):
            await self.db.execute_query_async(query, params, fetch_mode="none")
        else:
            # Fallback: run synchronous query in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.db.execute_query,
                query,
                params,
                "none"  # fetch_mode
            )

        logger.info(
            f"[{self.trace_id}] Trace written: {self.agent_name} "
            f"({duration_ms}ms, {self.metadata['tokens_used']} tokens, "
            f"${self.metadata['cost_usd']:.4f}, success={self.metadata['success']})"
        )

    def record_llm_call(self, tokens_used: int, cost_usd: float):
        """
        Record LLM call metrics.

        Args:
            tokens_used: Number of tokens consumed
            cost_usd: Cost in USD
        """
        self.metadata["tokens_used"] += tokens_used
        self.metadata["cost_usd"] += cost_usd

    def record_error(self, error_message: str):
        """
        Record an error (non-exception).

        Args:
            error_message: Error description
        """
        self.metadata["success"] = False
        self.metadata["error_message"] = error_message


# ============================================================================
# Helper Functions
# ============================================================================

def create_tracer(session_id: str, agent_name: str, db) -> AgentTracer:
    """
    Factory function for creating agent tracers.

    Args:
        session_id: UUID of the ingestion session
        agent_name: Name of the agent
        db: DatabaseManager instance

    Returns:
        AgentTracer context manager

    Example:
        >>> tracer = create_tracer(session_id, "AtomBuilder", db)
        >>> async with tracer:
        ...     result = await agent.run()
    """
    return AgentTracer(session_id, agent_name, db)


# ============================================================================
# Synchronous Agent Tracer (for non-async agents)
# ============================================================================

class SyncAgentTracer:
    """
    Synchronous context manager for tracing agent executions.

    Use this for agents that are not async (AtomBuilder, CitationValidator, etc.)
    """

    def __init__(self, session_id: str, agent_name: str, db):
        """
        Initialize synchronous agent tracer.

        Args:
            session_id: UUID of the ingestion session
            agent_name: Name of the agent
            db: DatabaseManager instance
        """
        self.session_id = session_id
        self.agent_name = agent_name
        self.db = db
        self.trace_id = str(uuid.uuid4())
        self.started_at: Optional[datetime] = None

        # Metadata dict
        self.metadata: Dict[str, Any] = {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "success": True,
            "error_message": None
        }

    def __enter__(self):
        """Context manager entry - start timing."""
        self.started_at = datetime.now(timezone.utc)
        logger.debug(f"[{self.trace_id}] Started tracing {self.agent_name} for session {self.session_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - calculate duration and write to database."""
        # Calculate duration
        if self.started_at is None:
            logger.error(f"[{self.trace_id}] Agent trace started_at is None, using NOW()")
            self.started_at = datetime.now(timezone.utc)

        duration_ms = int((datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000)

        # If exception occurred, mark as failed
        if exc_type:
            self.metadata["success"] = False
            self.metadata["error_message"] = str(exc_val)
            logger.error(
                f"[{self.trace_id}] {self.agent_name} failed: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )

        # Write trace to database
        try:
            self._write_trace(duration_ms)
        except Exception as e:
            # NEVER let trace writing break the pipeline
            logger.error(f"[{self.trace_id}] Failed to write agent trace: {e}", exc_info=True)

        # Don't suppress exceptions
        return False

    def _write_trace(self, duration_ms: int):
        """
        Write trace record to agent_traces table (synchronous).

        Args:
            duration_ms: Execution duration in milliseconds
        """
        query = """
            INSERT INTO agent_traces (
                trace_id, session_id, agent_name, duration_ms,
                tokens_used, cost_usd, success, error_message, started_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        params = (
            self.trace_id,
            self.session_id,
            self.agent_name,
            duration_ms,
            self.metadata.get("tokens_used", 0),
            self.metadata.get("cost_usd", 0.0),
            self.metadata.get("success", True),
            self.metadata.get("error_message"),
            self.started_at
        )

        # Execute synchronous query
        self.db.execute_query(query, params, fetch_mode="none")

        logger.info(
            f"[{self.trace_id}] Trace written: {self.agent_name} "
            f"({duration_ms}ms, {self.metadata['tokens_used']} tokens, "
            f"${self.metadata['cost_usd']:.4f}, success={self.metadata['success']})"
        )

    def record_llm_call(self, tokens_used: int, cost_usd: float):
        """
        Record LLM call metrics.

        Args:
            tokens_used: Number of tokens consumed
            cost_usd: Cost in USD
        """
        self.metadata["tokens_used"] += tokens_used
        self.metadata["cost_usd"] += cost_usd

    def record_error(self, error_message: str):
        """
        Record an error (non-exception).

        Args:
            error_message: Error description
        """
        self.metadata["success"] = False
        self.metadata["error_message"] = error_message
