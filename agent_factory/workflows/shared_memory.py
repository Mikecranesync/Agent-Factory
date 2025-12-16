"""
Shared Agent Memory - Semantic Memory for Multi-Agent Collaboration

Enables agents to:
- Store discoveries for other agents to find
- Retrieve relevant past solutions via semantic search
- Learn from previous successes and failures

Uses Supabase pgvector for semantic similarity search.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json

from langchain_openai import OpenAIEmbeddings


class SharedAgentMemory:
    """
    Semantic memory system for agent collaboration.

    Agents can store discoveries that other agents can later retrieve
    via semantic search. Enables learning from past work.

    Example:
        >>> memory = SharedAgentMemory()

        # Agent 1 stores a discovery
        >>> memory.store(
        ...     content="PLC scan cycle runs at 10ms intervals",
        ...     agent_name="ResearchAgent",
        ...     metadata={"topic": "plc_basics", "quality": 0.9}
        ... )

        # Agent 2 retrieves relevant discoveries
        >>> discoveries = memory.retrieve(
        ...     query="How fast does PLC run?",
        ...     limit=3
        ... )
    """

    def __init__(
        self,
        embedding_provider: str = "openai",
        table_name: str = "agent_shared_memory"
    ):
        """
        Initialize shared memory system.

        Args:
            embedding_provider: Currently only "openai" is supported
            table_name: Supabase table for storing memories
        """
        self.table_name = table_name

        # Initialize embeddings (currently only OpenAI supported)
        if embedding_provider == "openai":
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small"
            )
        else:
            raise ValueError(
                f"Unknown embedding provider: {embedding_provider}. "
                "Currently only 'openai' is supported."
            )

        # Initialize Supabase client
        self._init_supabase()

    def _init_supabase(self):
        """Initialize Supabase client for vector storage"""
        try:
            from supabase import create_client, Client

            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")

            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in environment"
                )

            self.supabase: Client = create_client(url, key)

        except ImportError:
            raise ImportError(
                "Supabase client not installed. Run: pip install supabase"
            )

    def store(
        self,
        content: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Store a discovery in shared memory.

        Args:
            content: The discovery text (e.g., "Found solution: ...")
            agent_name: Which agent made the discovery
            metadata: Optional metadata (topic, quality_score, etc.)
            session_id: Optional session ID for grouping memories

        Returns:
            Memory ID (UUID)

        Example:
            >>> memory_id = memory.store(
            ...     content="Allen-Bradley uses ladder logic",
            ...     agent_name="ResearchAgent",
            ...     metadata={"vendor": "ab", "quality": 0.95}
            ... )
        """
        # Generate embedding
        embedding = self.embeddings.embed_query(content)

        # Build record
        record = {
            "content": content,
            "agent_name": agent_name,
            "embedding": embedding,
            "metadata": metadata or {},
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat()
        }

        # Insert into Supabase
        result = self.supabase.table(self.table_name).insert(record).execute()

        if result.data:
            return result.data[0]["id"]
        else:
            raise RuntimeError(f"Failed to store memory: {result}")

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        agent_filter: Optional[str] = None,
        session_filter: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories via semantic search.

        Args:
            query: Semantic search query (e.g., "how to troubleshoot motor")
            limit: Maximum number of memories to return
            agent_filter: Only return memories from specific agent
            session_filter: Only return memories from specific session
            metadata_filter: Filter by metadata fields

        Returns:
            List of memories sorted by relevance

        Example:
            >>> memories = memory.retrieve(
            ...     query="PLC scan cycle timing",
            ...     limit=3,
            ...     agent_filter="ResearchAgent"
            ... )
            >>> for m in memories:
            ...     print(f"{m['agent_name']}: {m['content'][:50]}...")
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Build RPC call for vector search
        # Note: Requires pgvector function in Supabase
        # See: docs/supabase_migrations.sql for setup
        rpc_params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,  # Minimum similarity threshold
            "match_count": limit
        }

        # Add filters if provided
        if agent_filter:
            rpc_params["agent_name"] = agent_filter
        if session_filter:
            rpc_params["session_id"] = session_filter

        # Execute semantic search
        result = self.supabase.rpc(
            "match_agent_memories",
            rpc_params
        ).execute()

        memories = result.data if result.data else []

        # Apply metadata filters if provided
        if metadata_filter and memories:
            memories = [
                m for m in memories
                if all(
                    m.get("metadata", {}).get(k) == v
                    for k, v in metadata_filter.items()
                )
            ]

        return memories

    def get_agent_history(
        self,
        agent_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all memories from a specific agent.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of memories to return

        Returns:
            List of memories in chronological order

        Example:
            >>> history = memory.get_agent_history("ResearchAgent")
            >>> print(f"Found {len(history)} discoveries")
        """
        result = self.supabase.table(self.table_name).select("*").eq(
            "agent_name", agent_name
        ).order("created_at", desc=True).limit(limit).execute()

        return result.data if result.data else []

    def get_session_memories(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all memories from a specific session.

        Args:
            session_id: Session identifier

        Returns:
            List of memories in chronological order

        Example:
            >>> session_memories = memory.get_session_memories("sess_123")
            >>> print(f"Session had {len(session_memories)} discoveries")
        """
        result = self.supabase.table(self.table_name).select("*").eq(
            "session_id", session_id
        ).order("created_at", desc=False).execute()

        return result.data if result.data else []

    def clear_session(self, session_id: str) -> int:
        """
        Clear all memories from a session.

        Args:
            session_id: Session to clear

        Returns:
            Number of memories deleted

        Example:
            >>> deleted = memory.clear_session("sess_123")
            >>> print(f"Deleted {deleted} memories")
        """
        result = self.supabase.table(self.table_name).delete().eq(
            "session_id", session_id
        ).execute()

        return len(result.data) if result.data else 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about shared memory usage.

        Returns:
            Dict with memory counts per agent and total

        Example:
            >>> stats = memory.get_stats()
            >>> print(f"Total memories: {stats['total']}")
            >>> print(f"Agents: {', '.join(stats['by_agent'].keys())}")
        """
        # Get total count
        total_result = self.supabase.table(self.table_name).select(
            "id", count="exact"
        ).execute()
        total = total_result.count if total_result.count else 0

        # Get counts by agent
        agent_result = self.supabase.table(self.table_name).select(
            "agent_name"
        ).execute()

        by_agent = {}
        if agent_result.data:
            for record in agent_result.data:
                agent = record["agent_name"]
                by_agent[agent] = by_agent.get(agent, 0) + 1

        return {
            "total": total,
            "by_agent": by_agent,
            "table_name": self.table_name
        }


# ========================================
# Integration with LangGraph Workflows
# ========================================

def add_memory_to_workflow(
    workflow_state: Dict[str, Any],
    memory: SharedAgentMemory,
    agent_name: str
) -> Dict[str, Any]:
    """
    Add shared memory capabilities to a workflow state.

    Enriches the state with relevant past discoveries before
    agent execution.

    Args:
        workflow_state: Current workflow state
        memory: Shared memory instance
        agent_name: Which agent is about to execute

    Returns:
        Enhanced state with memory context

    Example:
        >>> state = {"query": "How does PLC work?", "context": []}
        >>> state = add_memory_to_workflow(state, memory, "ResearchAgent")
        >>> # state["context"] now includes relevant past discoveries
    """
    query = workflow_state.get("query", "")

    if not query:
        return workflow_state

    # Retrieve relevant memories
    memories = memory.retrieve(
        query=query,
        limit=3,
        agent_filter=agent_name  # Only this agent's past work
    )

    # Add to context
    if memories:
        memory_context = "\n\n".join([
            f"Past Discovery ({m['created_at'][:10]}):\n{m['content']}"
            for m in memories
        ])

        workflow_state["context"] = workflow_state.get("context", [])
        workflow_state["context"].append(f"Relevant Past Work:\n{memory_context}")

    return workflow_state


def store_workflow_findings(
    workflow_state: Dict[str, Any],
    memory: SharedAgentMemory,
    agent_name: str,
    session_id: Optional[str] = None
) -> str:
    """
    Store workflow findings to shared memory.

    Call this after an agent completes work to save
    discoveries for future agents.

    Args:
        workflow_state: Current workflow state
        memory: Shared memory instance
        agent_name: Which agent made the discovery
        session_id: Optional session ID

    Returns:
        Memory ID of stored finding

    Example:
        >>> state = {
        ...     "findings": {"research": "Found 3 PLC vendors..."},
        ...     "quality_score": 0.9
        ... }
        >>> memory_id = store_workflow_findings(
        ...     state, memory, "ResearchAgent", "sess_123"
        ... )
    """
    # Extract findings for this agent
    findings = workflow_state.get("findings", {})
    agent_key = agent_name.lower().replace("agent", "")

    content = findings.get(agent_key, "")

    if not content:
        # Try to get from final_answer if no specific findings
        content = workflow_state.get("final_answer", "")

    if not content:
        raise ValueError(f"No findings to store for {agent_name}")

    # Build metadata
    metadata = {
        "quality_score": workflow_state.get("quality_score", 0.0),
        "retry_count": workflow_state.get("retry_count", 0),
        "current_step": workflow_state.get("current_step", "")
    }

    # Store to shared memory
    return memory.store(
        content=content,
        agent_name=agent_name,
        metadata=metadata,
        session_id=session_id
    )
