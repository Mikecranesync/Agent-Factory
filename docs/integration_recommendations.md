# Integration Recommendations for Agent Factory

**Date:** 2025-12-09
**Purpose:** Actionable roadmap for integrating Cole Medin patterns into Agent Factory
**Based on:** cole_medin_patterns.md, archon_architecture_analysis.md

---

## Executive Summary

Agent Factory has successfully implemented:
- ✅ Supabase memory storage with JSONB (60-120x faster than file-based)
- ✅ Dual storage architecture (Supabase + file backup)
- ✅ Memory atoms pattern with type/content/metadata
- ✅ Session-based memory isolation

**Next Phase:** Integrate proven production patterns from Cole Medin's 13.4k⭐ Archon system to make Agent Factory production-ready for RIVET deployment.

---

## Priority Matrix

```
High Value, Low Effort:        High Value, High Effort:
┌─────────────────────────┐    ┌─────────────────────────┐
│ 1. Settings Service     │    │ 5. Hybrid Search        │
│ 2. TASK.md Pattern      │    │ 6. Batch Processing     │
│ 3. MCP Lifespan         │    │ 7. Multi-Dimensional    │
└─────────────────────────┘    └─────────────────────────┘

Low Value, Low Effort:         Low Value, High Effort:
┌─────────────────────────┐    ┌─────────────────────────┐
│ 4. PRP Templates        │    │ 8. HTTP-Based MCP       │
│                         │    │ 9. Reranking            │
└─────────────────────────┘    └─────────────────────────┘
```

---

## Phase 1: Immediate Wins (This Week)

### 1. Settings Service [HIGH PRIORITY]

**Why:** Enable runtime configuration changes without code changes or restarts

**What:** Database-backed settings with environment fallback

**Implementation:**

```python
# agent_factory/core/settings_service.py
import os
from typing import Optional
from supabase import create_client, Client

class SettingsService:
    """
    Database-backed settings with environment fallback.

    Pattern from Archon's CredentialService.
    """

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.client: Optional[Client] = None
        self._cache = {}
        self._cache_initialized = False

        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                self._load_cache()
            except Exception as e:
                print(f"[WARN] Settings service using env vars only: {e}")

    def _load_cache(self):
        """Load all settings into memory cache"""
        if not self.client:
            return

        try:
            response = self.client.table("agent_factory_settings").select("*").execute()
            for row in response.data:
                key = f"{row['category']}.{row['key']}"
                self._cache[key] = row['value']
            self._cache_initialized = True
        except Exception as e:
            print(f"[WARN] Failed to load settings cache: {e}")

    def get(self, key: str, default: str = "", category: str = "general") -> str:
        """Get a setting from cache or environment"""
        cache_key = f"{category}.{key}"

        # Try cache first
        if self._cache_initialized and cache_key in self._cache:
            return self._cache[cache_key]

        # Fallback to environment variable
        return os.getenv(key, default)

    def get_bool(self, key: str, default: bool = False, category: str = "general") -> bool:
        """Get boolean setting"""
        value = self.get(key, "false" if not default else "true", category)
        return value.lower() in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0, category: str = "general") -> int:
        """Get integer setting"""
        value = self.get(key, str(default), category)
        try:
            return int(value)
        except ValueError:
            return default

    def reload(self):
        """Reload settings from database"""
        self._cache.clear()
        self._load_cache()

# Singleton instance
settings = SettingsService()
```

**Database Migration:**

```sql
-- Create settings table
CREATE TABLE IF NOT EXISTS agent_factory_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, key)
);

-- Create index for fast lookups
CREATE INDEX idx_settings_category_key ON agent_factory_settings(category, key);

-- Insert default settings
INSERT INTO agent_factory_settings (category, key, value, description) VALUES
('memory', 'BATCH_SIZE', '50', 'Batch size for memory operations'),
('memory', 'USE_HYBRID_SEARCH', 'false', 'Enable hybrid vector + text search'),
('orchestration', 'MAX_RETRIES', '3', 'Max retries for agent calls'),
('orchestration', 'TIMEOUT_SECONDS', '300', 'Default timeout for agent execution'),
('llm', 'DEFAULT_MODEL', 'gpt-4o-mini', 'Default LLM model'),
('llm', 'DEFAULT_TEMPERATURE', '0.7', 'Default temperature for LLM calls');
```

**Usage Example:**

```python
from agent_factory.core.settings_service import settings

# In agent code
max_retries = settings.get_int("MAX_RETRIES", default=3, category="orchestration")
use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")
default_model = settings.get("DEFAULT_MODEL", category="llm")

# Change setting via Supabase UI or API - no code changes needed!
```

**Effort:** 2-3 hours
**Value:** High - enables all future feature toggles

---

### 2. TASK.md Pattern [HIGH PRIORITY]

**Why:** Better task tracking and AI context for active work

**What:** Markdown file tracking current tasks, inspired by context-engineering-intro

**Implementation:**

Create `TASK.md` in project root:

```markdown
# Active Tasks - Agent Factory

**Last Updated:** 2025-12-09

## In Progress

### [P0] Add Settings Service
**Status:** In Progress
**Started:** 2025-12-09
**Assignee:** Claude
**Description:** Implement database-backed settings with env fallback
**Files:**
- [ ] Create `agent_factory/core/settings_service.py`
- [ ] Create SQL migration for `agent_factory_settings` table
- [ ] Add usage examples in README
- [ ] Write unit tests

**Validation:**
```bash
poetry run python -c "from agent_factory.core.settings_service import settings; print(settings.get('DEFAULT_MODEL', category='llm'))"
```

---

## Backlog

### [P1] Hybrid Search for Memory
**Status:** Not Started
**Description:** Add PostgreSQL RPC function for hybrid vector + text search
**Dependencies:** Settings Service
**Estimated Effort:** 4-6 hours

### [P2] Batch Processing with Progress
**Status:** Not Started
**Description:** Add batch processing for memory saves with progress callbacks
**Dependencies:** None
**Estimated Effort:** 3-4 hours

---

## Completed

### ✅ Supabase Memory Storage
**Completed:** 2025-12-08
**Description:** Implemented fast Supabase storage for memory atoms
**Performance:** 60-120x faster than file-based storage
**Files:** `agent_factory/memory/storage.py`, `agent_factory/memory/history.py`

---

## Discovered During Work

### Document Hybrid Search RPC Pattern
**Found During:** Settings Service implementation
**Description:** Need to document how PostgreSQL RPC functions work for hybrid search
**Priority:** P2

---

## Notes

- Always mark tasks as completed immediately after finishing
- Add new tasks discovered during work to "Discovered During Work" section
- Update status daily
```

**CLAUDE.md Update:**

Add to `.claude/CLAUDE.md`:

```markdown
### ✅ Task Completion
- **Check TASK.md before starting new tasks**
- **Mark completed tasks immediately** - update status from "In Progress" to "Completed"
- **Add discovered tasks** to "Discovered During Work" section with context
- **Update validation commands** after testing features
```

**Effort:** 1 hour (initial setup)
**Value:** High - improves AI context and task tracking

---

### 3. MCP Lifespan Context [MEDIUM PRIORITY]

**Why:** Prevent repeated initialization of resources for every tool call

**What:** Implement lifespan context management pattern from mcp-mem0

**Current State:**
```python
# Each tool call might recreate connections
@mcp.tool()
async def save_memory(text: str):
    storage = SupabaseMemoryStorage()  # ❌ Creates new client every time
    storage.save_memory_atom(...)
```

**Target State:**
```python
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class AgentFactoryContext:
    """Context for Agent Factory MCP server"""
    storage: SupabaseMemoryStorage
    settings: SettingsService

@asynccontextmanager
async def agent_factory_lifespan(server: FastMCP):
    """Manages resource lifecycle"""
    # Initialize once
    storage = SupabaseMemoryStorage()
    settings = SettingsService()

    try:
        yield AgentFactoryContext(storage=storage, settings=settings)
    finally:
        # Cleanup if needed
        pass

# Initialize MCP with lifespan
mcp = FastMCP(
    "agent-factory",
    lifespan=agent_factory_lifespan,
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=os.getenv("MCP_PORT", "8050")
)

# Access context in tools
@mcp.tool()
async def save_memory(ctx: Context, text: str):
    storage = ctx.request_context.lifespan_context.storage
    storage.save_memory_atom(...)
```

**Files to Modify:**
- `agentcli.py` (if MCP server is implemented)
- Create new file: `agent_factory/mcp/server.py`

**Effort:** 2-3 hours
**Value:** Medium - better performance, cleaner code

---

## Phase 2: High-Value Enhancements (This Month)

### 4. Hybrid Search for Memory [HIGH VALUE]

**Why:** Improve memory retrieval quality by combining vector + text search

**What:** PostgreSQL RPC function for hybrid search on `session_memories` table

**Implementation:**

**Step 1:** Add full-text search column to table

```sql
-- Add tsvector column for full-text search
ALTER TABLE session_memories
ADD COLUMN content_tsvector tsvector
GENERATED ALWAYS AS (to_tsvector('english', content::text)) STORED;

-- Create GIN index for full-text search
CREATE INDEX idx_session_memories_content_search
ON session_memories USING gin(content_tsvector);
```

**Step 2:** Create hybrid search RPC function

```sql
CREATE OR REPLACE FUNCTION hybrid_search_session_memories(
    query_embedding vector(1536),
    query_text TEXT,
    p_session_id TEXT,
    p_user_id TEXT,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    session_id TEXT,
    user_id TEXT,
    memory_type TEXT,
    content JSONB,
    metadata JSONB,
    similarity FLOAT,
    match_type TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        SELECT
            m.id, m.session_id, m.user_id, m.memory_type, m.content, m.metadata,
            1 - (m.embedding <=> query_embedding) AS similarity,
            'vector' AS match_type,
            m.created_at
        FROM session_memories m
        WHERE m.session_id = p_session_id
            AND m.user_id = p_user_id
        ORDER BY m.embedding <=> query_embedding
        LIMIT match_count
    ),
    text_search AS (
        SELECT
            m.id, m.session_id, m.user_id, m.memory_type, m.content, m.metadata,
            ts_rank(m.content_tsvector, plainto_tsquery('english', query_text)) AS similarity,
            'text' AS match_type,
            m.created_at
        FROM session_memories m
        WHERE m.session_id = p_session_id
            AND m.user_id = p_user_id
            AND m.content_tsvector @@ plainto_tsquery('english', query_text)
        ORDER BY similarity DESC
        LIMIT match_count
    )
    SELECT DISTINCT ON (v.id)
        COALESCE(v.id, t.id) AS id,
        COALESCE(v.session_id, t.session_id) AS session_id,
        COALESCE(v.user_id, t.user_id) AS user_id,
        COALESCE(v.memory_type, t.memory_type) AS memory_type,
        COALESCE(v.content, t.content) AS content,
        COALESCE(v.metadata, t.metadata) AS metadata,
        GREATEST(COALESCE(v.similarity, 0), COALESCE(t.similarity, 0)) AS similarity,
        CASE
            WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'both'
            WHEN v.id IS NOT NULL THEN 'vector'
            ELSE 'text'
        END AS match_type,
        COALESCE(v.created_at, t.created_at) AS created_at
    FROM vector_search v
    FULL OUTER JOIN text_search t ON v.id = t.id
    ORDER BY v.id, similarity DESC
    LIMIT match_count;
END;
$$;
```

**Step 3:** Add Python wrapper

```python
# agent_factory/memory/hybrid_search.py
from typing import List, Dict, Any
from supabase import Client

async def hybrid_search_memories(
    client: Client,
    query: str,
    query_embedding: List[float],
    session_id: str,
    user_id: str,
    match_count: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search on session_memories.

    Combines vector similarity with full-text search for better recall.
    Returns results with match_type: "vector", "text", or "both"
    """
    try:
        response = client.rpc(
            "hybrid_search_session_memories",
            {
                "query_embedding": query_embedding,
                "query_text": query,
                "p_session_id": session_id,
                "p_user_id": user_id,
                "match_count": match_count
            }
        ).execute()

        return response.data if response.data else []

    except Exception as e:
        print(f"[ERROR] Hybrid search failed: {e}")
        return []
```

**Step 4:** Integrate with settings

```python
from agent_factory.core.settings_service import settings

async def search_memories(query, session_id, user_id, match_count=5):
    # Create embedding
    embedding = await create_embedding(query)

    # Check if hybrid search is enabled
    use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")

    if use_hybrid:
        results = await hybrid_search_memories(
            client, query, embedding, session_id, user_id, match_count
        )
    else:
        # Fallback to pure vector search
        results = await vector_search_memories(
            client, embedding, session_id, user_id, match_count
        )

    return results
```

**Effort:** 4-6 hours
**Value:** High - significantly improves search quality

---

### 5. Batch Processing with Progress [MEDIUM VALUE]

**Why:** Enable visibility and control for long-running memory operations

**What:** Batch processing pattern from Archon's document storage

**Implementation:**

```python
# agent_factory/memory/batch_operations.py
from typing import List, Dict, Any, Callable, Optional
import asyncio

async def save_memories_batch(
    storage: SupabaseMemoryStorage,
    session_id: str,
    user_id: str,
    memories: List[Dict[str, Any]],
    batch_size: int = 50,
    progress_callback: Optional[Callable] = None
) -> Dict[str, int]:
    """
    Save multiple memories in batches with progress reporting.

    Args:
        storage: SupabaseMemoryStorage instance
        session_id: Session identifier
        user_id: User identifier
        memories: List of memory dicts with 'type', 'content', 'metadata'
        batch_size: Number of memories per batch (from settings)
        progress_callback: Optional async function(status, progress, message)

    Returns:
        Dict with 'saved', 'failed' counts
    """
    from agent_factory.core.settings_service import settings

    # Load batch size from settings
    batch_size = settings.get_int("BATCH_SIZE", default=50, category="memory")

    total_batches = (len(memories) + batch_size - 1) // batch_size
    completed_batches = 0
    total_saved = 0
    total_failed = 0

    for batch_num, i in enumerate(range(0, len(memories), batch_size), 1):
        batch = memories[i:i+batch_size]

        # Report progress
        if progress_callback:
            progress = int((completed_batches / total_batches) * 100)
            await progress_callback(
                "processing",
                progress,
                f"Saving batch {batch_num}/{total_batches}"
            )

        # Process batch with retry logic
        for retry in range(3):
            try:
                for memory in batch:
                    storage.save_memory_atom(
                        session_id=session_id,
                        user_id=user_id,
                        memory_type=memory['type'],
                        content=memory['content'],
                        metadata=memory.get('metadata', {})
                    )
                    total_saved += 1

                completed_batches += 1
                break

            except Exception as e:
                if retry == 2:
                    # Final attempt failed - try individual saves
                    for memory in batch:
                        try:
                            storage.save_memory_atom(
                                session_id=session_id,
                                user_id=user_id,
                                memory_type=memory['type'],
                                content=memory['content'],
                                metadata=memory.get('metadata', {})
                            )
                            total_saved += 1
                        except:
                            total_failed += 1
                    completed_batches += 1
                else:
                    # Retry with exponential backoff
                    await asyncio.sleep(2 ** retry)

        # Small delay between batches
        if i + batch_size < len(memories):
            await asyncio.sleep(0.1)

    # Final progress
    if progress_callback:
        await progress_callback("completed", 100, f"Saved {total_saved} memories")

    return {"saved": total_saved, "failed": total_failed}
```

**Usage Example:**

```python
# Progress callback
async def on_progress(status, progress, message):
    print(f"[{status}] {progress}% - {message}")

# Batch save
memories = [
    {"type": "decision", "content": {...}, "metadata": {}},
    {"type": "action", "content": {...}, "metadata": {}},
    # ... 1000 more memories
]

result = await save_memories_batch(
    storage=storage,
    session_id="session_123",
    user_id="user_456",
    memories=memories,
    progress_callback=on_progress
)

print(f"Saved: {result['saved']}, Failed: {result['failed']}")
```

**Effort:** 3-4 hours
**Value:** Medium - better UX for large operations

---

### 6. Multi-Dimensional Embedding Support [MEDIUM VALUE]

**Why:** Support multiple embedding models without migration pain

**What:** Add columns for different embedding dimensions (768, 1024, 1536, 3072)

**Implementation:**

```sql
-- Add multi-dimensional embedding columns
ALTER TABLE session_memories
ADD COLUMN embedding_768 vector(768),
ADD COLUMN embedding_1024 vector(1024),
ADD COLUMN embedding_1536 vector(1536),
ADD COLUMN embedding_3072 vector(3072),
ADD COLUMN embedding_model TEXT,
ADD COLUMN embedding_dimension INT;

-- Create indexes for each dimension
CREATE INDEX idx_session_memories_embedding_768
ON session_memories USING ivfflat (embedding_768 vector_cosine_ops);

CREATE INDEX idx_session_memories_embedding_1024
ON session_memories USING ivfflat (embedding_1024 vector_cosine_ops);

CREATE INDEX idx_session_memories_embedding_1536
ON session_memories USING ivfflat (embedding_1536 vector_cosine_ops);

CREATE INDEX idx_session_memories_embedding_3072
ON session_memories USING ivfflat (embedding_3072 vector_cosine_ops);

-- Migrate existing data (if embedding column exists)
UPDATE session_memories
SET embedding_1536 = embedding,
    embedding_dimension = 1536,
    embedding_model = 'text-embedding-3-small'
WHERE embedding IS NOT NULL;

-- Drop old column after verification
-- ALTER TABLE session_memories DROP COLUMN embedding;
```

**Python Changes:**

```python
# agent_factory/memory/storage.py

def save_memory_atom(self, session_id, user_id, memory_type, content, metadata=None):
    # Generate embedding
    embedding = create_embedding(content)

    # Determine column based on dimension
    embedding_dim = len(embedding)

    if embedding_dim == 768:
        embedding_column = "embedding_768"
        model_name = "all-MiniLM-L6-v2"
    elif embedding_dim == 1024:
        embedding_column = "embedding_1024"
        model_name = "voyage-3"
    elif embedding_dim == 1536:
        embedding_column = "embedding_1536"
        model_name = "text-embedding-3-small"
    elif embedding_dim == 3072:
        embedding_column = "embedding_3072"
        model_name = "text-embedding-3-large"
    else:
        raise ValueError(f"Unsupported embedding dimension: {embedding_dim}")

    atom = {
        "session_id": session_id,
        "user_id": user_id,
        "memory_type": memory_type,
        "content": content,
        "metadata": metadata or {},
        embedding_column: embedding,
        "embedding_model": model_name,
        "embedding_dimension": embedding_dim,
        "created_at": datetime.now().isoformat()
    }

    response = self.client.table(self.table_name).insert(atom).execute()
    return response.data[0]
```

**Effort:** 4-5 hours
**Value:** Medium - future-proofs embedding strategy

---

## Phase 3: Polish & Optimization (Next Quarter)

### 7. PRP Templates [LOW PRIORITY]

**Why:** Standardize agent creation process

**What:** Product Requirements Prompt templates from context-engineering-intro

**Implementation:**

Create `docs/prp_templates/`:

```
docs/prp_templates/
├── agent_creation.md        # Template for creating new agents
├── tool_creation.md          # Template for creating new tools
└── integration.md            # Template for adding integrations
```

**Example: agent_creation.md**

```markdown
name: "Agent Name"
description: |
  ## Purpose
  [What this agent does]

  ## Core Principles
  1. Context is King
  2. Validation Loops
  3. Information Dense
  4. Progressive Success

## Goal
[Clear objective]

## Why
- Business value: [What it unlocks]
- Integration: [How it fits]
- Problems solved: [What it fixes]

## What
[Concrete deliverables]

### Success Criteria
- [ ] Agent executes primary function
- [ ] Agent handles errors gracefully
- [ ] All tests pass

## All Needed Context

### Documentation & References
- file: agent_factory/core/agent_factory.py
  why: Pattern for agent creation
- file: agent_factory/schemas/agent_schema.py
  why: Pydantic schemas for validation

### Current Structure
[Show current agent_factory structure]

### Desired Structure
[Show target structure with new agent]

## Implementation Steps
1. Create agent file in agent_factory/agents/
2. Define tools in agent_factory/tools/
3. Add prompts to agent_factory/prompts/
4. Create unit tests
5. Register agent in factory

## Validation
```bash
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"
poetry run pytest tests/test_new_agent.py
```
```

**Effort:** 2-3 hours
**Value:** Low - helpful but not critical

---

### 8. Reranking Strategy [LOW PRIORITY]

**Why:** Improve search result quality

**What:** CrossEncoder model for re-scoring search results

**Implementation:**

```python
# agent_factory/memory/reranking.py
from sentence_transformers import CrossEncoder

class MemoryReranker:
    """Rerank memory search results using CrossEncoder"""

    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    async def rerank(self, query: str, results: List[Dict], top_k: int = 5):
        """
        Rerank search results.

        Args:
            query: Search query
            results: List of memory dicts with 'content'
            top_k: Number of results to return

        Returns:
            Reranked list of results with rerank_score
        """
        # Build query-document pairs
        pairs = [[query, str(result['content'])] for result in results]

        # Get scores
        scores = self.model.predict(pairs)

        # Add scores to results
        for i, result in enumerate(results):
            result['rerank_score'] = float(scores[i])

        # Sort by rerank score
        reranked = sorted(results, key=lambda x: x['rerank_score'], reverse=True)

        return reranked[:top_k]
```

**Usage:**

```python
from agent_factory.core.settings_service import settings

# Search with reranking
results = await search_memories(query, session_id, user_id, match_count=25)

# Apply reranking if enabled
use_reranking = settings.get_bool("USE_RERANKING", category="memory")
if use_reranking:
    reranker = MemoryReranker()
    results = await reranker.rerank(query, results, top_k=5)
```

**Dependencies:**
```bash
poetry add sentence-transformers torch
```

**Effort:** 3-4 hours
**Value:** Low - nice to have, not critical

---

### 9. HTTP-Based MCP Server [OPTIONAL]

**Why:** Better separation and scaling

**What:** Run MCP server as separate process, communicate via HTTP

**When:** Only needed if:
- Agent Factory becomes a service (not CLI)
- Need independent scaling of MCP server
- Want to isolate MCP failures

**Implementation:** See Archon's pattern in archon_architecture_analysis.md

**Effort:** 8-12 hours
**Value:** Low for current CLI use case

---

## Implementation Roadmap

### Week 1 (Dec 9-15)
- [ ] Implement Settings Service
- [ ] Add TASK.md pattern
- [ ] Update CLAUDE.md with new patterns
- [ ] Write tests for Settings Service

### Week 2 (Dec 16-22)
- [ ] Add MCP Lifespan Context
- [ ] Create hybrid search SQL migration
- [ ] Implement hybrid_search_memories function
- [ ] Write tests for hybrid search

### Week 3 (Dec 23-29)
- [ ] Implement batch processing
- [ ] Add progress callback support
- [ ] Test with large memory sets (1000+ atoms)

### Week 4 (Dec 30 - Jan 5)
- [ ] Add multi-dimensional embedding support
- [ ] Migrate existing embeddings
- [ ] Performance testing
- [ ] Documentation updates

### Month 2 (January)
- [ ] Create PRP templates
- [ ] Add reranking (optional)
- [ ] Polish and optimize
- [ ] Prepare for RIVET integration

---

## Testing Strategy

### Unit Tests

```python
# tests/test_settings_service.py
def test_settings_service_env_fallback():
    """Test that settings fall back to environment variables"""
    os.environ["TEST_SETTING"] = "from_env"
    settings = SettingsService(supabase_url=None)  # Force env fallback
    assert settings.get("TEST_SETTING") == "from_env"

def test_settings_service_cache():
    """Test that settings are cached"""
    settings = SettingsService()
    # First call loads from DB
    value1 = settings.get("DEFAULT_MODEL", category="llm")
    # Second call uses cache
    value2 = settings.get("DEFAULT_MODEL", category="llm")
    assert value1 == value2
```

```python
# tests/test_hybrid_search.py
async def test_hybrid_search_combines_results():
    """Test that hybrid search returns both vector and text matches"""
    results = await hybrid_search_memories(
        client, "agent orchestration", embedding, session_id, user_id, 5
    )

    # Should have mix of match types
    match_types = {r['match_type'] for r in results}
    assert 'vector' in match_types or 'text' in match_types or 'both' in match_types
```

### Integration Tests

```python
# tests/integration/test_end_to_end.py
async def test_save_and_search_with_hybrid():
    """End-to-end test of save + hybrid search"""
    # Save memories
    storage.save_memory_atom(session_id, user_id, "decision", {...})

    # Search with hybrid
    results = await hybrid_search_memories(client, "decision", embedding, ...)

    # Verify results
    assert len(results) > 0
    assert results[0]['memory_type'] == "decision"
```

---

## Success Metrics

### Performance
- Settings cache hit rate > 95%
- Hybrid search latency < 200ms
- Batch processing throughput > 100 memories/sec

### Quality
- Hybrid search recall > pure vector (test with benchmark queries)
- Reranking improves top-5 relevance by > 10%

### Reliability
- Settings reload without restart
- Batch operations handle failures gracefully
- All critical paths have unit + integration tests

---

## Migration Path

### From Current State to Phase 1

1. **Add Settings Table**
   - Run SQL migration
   - Populate with defaults
   - No code changes yet

2. **Add Settings Service**
   - Create settings_service.py
   - Add singleton instance
   - Start using in new code only

3. **Gradual Migration**
   - Replace `os.getenv()` calls with `settings.get()`
   - One file at a time
   - Test each change

4. **Add TASK.md**
   - Create file
   - Start tracking new work
   - Update CLAUDE.md

### From Phase 1 to Phase 2

1. **Add Hybrid Search SQL**
   - Add tsvector column
   - Create RPC function
   - Test with sample queries

2. **Add Python Wrapper**
   - Create hybrid_search.py
   - Integrate with storage.py
   - Use settings to enable/disable

3. **Add Batch Processing**
   - Create batch_operations.py
   - Add progress callbacks
   - Test with large datasets

---

## Risk Mitigation

### Risk: Database Migration Failures

**Mitigation:**
- Test migrations on dev environment first
- Keep old columns until migration verified
- Have rollback SQL scripts ready

### Risk: Settings Cache Stale

**Mitigation:**
- Add TTL to cache (5 minutes)
- Provide manual `reload()` function
- Log cache misses for monitoring

### Risk: Hybrid Search Slower Than Vector

**Mitigation:**
- Make hybrid search opt-in via settings
- Test with production-like data volumes
- Add query timeout limits

### Risk: Breaking Changes to Memory API

**Mitigation:**
- Keep old functions working during migration
- Add deprecation warnings
- Version the API if needed

---

## Next Steps

1. **Review this document** with team/stakeholders
2. **Prioritize tasks** based on RIVET requirements
3. **Start with Settings Service** (highest ROI)
4. **Update TASK.md** with chosen tasks
5. **Begin implementation** following roadmap

---

## References

- **Patterns:** docs/cole_medin_patterns.md
- **Architecture:** docs/archon_architecture_analysis.md
- **Archon Repo:** https://github.com/coleam00/Archon
- **Context Engineering:** https://github.com/coleam00/context-engineering-intro
- **MCP Mem0:** https://github.com/coleam00/mcp-mem0
