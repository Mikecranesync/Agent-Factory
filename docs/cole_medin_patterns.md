# Cole Medin Patterns - Research Summary

**Date:** 2025-12-09
**Purpose:** Extract proven patterns from Cole Medin's production systems for Agent Factory integration

**Repositories Analyzed:**
- **Archon** (13.4k⭐) - RAG system with Supabase + pgvector
- **context-engineering-intro** (11.8k⭐) - Context engineering framework
- **mcp-mem0** - MCP server for long-term memory

---

## 1. Vector Search & RAG Patterns (from Archon)

### 1.1 Hybrid Search Architecture

**Pattern:** Combine vector similarity search with full-text search for better recall and precision

```python
# PostgreSQL RPC function call pattern
response = supabase_client.rpc(
    "hybrid_search_archon_crawled_pages",
    {
        "query_embedding": query_embedding,
        "query_text": query,
        "match_count": match_count,
        "filter": filter_json,
        "source_filter": source_filter,
    },
).execute()

# Result includes match_type: "vector", "text", or "both"
```

**Key Insights:**
- PostgreSQL RPC functions handle complex search logic at database level
- Returns union of vector + full-text results
- Tracks match type for debugging and analysis
- Uses ts_vector for efficient keyword matching

**Database Pattern:**
```sql
-- Store both vector embeddings and tsvector for full-text search
CREATE TABLE archon_crawled_pages (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding_768 vector(768),      -- Support multiple dimensions
    embedding_1024 vector(1024),
    embedding_1536 vector(1536),
    embedding_3072 vector(3072),
    content_tsvector tsvector,      -- Full-text search index
    metadata JSONB,
    source_id UUID REFERENCES archon_sources(id)
);
```

### 1.2 Strategy Pattern for RAG

**Pattern:** Composable search strategies that can be enabled/disabled via settings

```python
class RAGService:
    """Coordinator service that orchestrates multiple RAG strategies"""

    def __init__(self, supabase_client=None):
        # Base strategy (always needed)
        self.base_strategy = BaseSearchStrategy(supabase_client)

        # Optional strategies initialized based on settings
        self.hybrid_strategy = HybridSearchStrategy(supabase_client, self.base_strategy)
        self.agentic_strategy = AgenticRAGStrategy(supabase_client, self.base_strategy)

        # Reranking loaded conditionally
        use_reranking = self.get_bool_setting("USE_RERANKING", False)
        if use_reranking:
            self.reranking_strategy = RerankingStrategy()

    async def perform_rag_query(self, query, ...):
        # Pipeline: Search → Rerank → Group
        results = await self.search_documents(query, use_hybrid_search=True)

        if self.reranking_strategy:
            results = await self.reranking_strategy.rerank_results(query, results)

        return results
```

**Strategies Available:**
1. **BaseSearchStrategy** - Pure vector similarity search
2. **HybridSearchStrategy** - Vector + full-text combined
3. **RerankingStrategy** - CrossEncoder re-scoring of results
4. **AgenticRAGStrategy** - Enhanced code example extraction

**Key Insight:** Strategies are composable - you can enable multiple at once and they work together in a pipeline.

### 1.3 Multi-Dimensional Embeddings

**Pattern:** Support multiple embedding dimensions with dynamic column selection

```python
# Determine correct column based on embedding dimension
embedding_dim = len(embedding)

if embedding_dim == 768:
    embedding_column = "embedding_768"
elif embedding_dim == 1024:
    embedding_column = "embedding_1024"
elif embedding_dim == 1536:
    embedding_column = "embedding_1536"
elif embedding_dim == 3072:
    embedding_column = "embedding_3072"

# Track which model was used
data = {
    "content": text,
    embedding_column: embedding,  # Dynamic column
    "embedding_model": embedding_model_name,
    "embedding_dimension": embedding_dim,
    "llm_chat_model": llm_chat_model  # For contextual embeddings
}
```

**Supported Models:**
- 768: MiniLM, BGE-small
- 1024: Voyage-3, Cohere-v3
- 1536: OpenAI text-embedding-3-small
- 3072: OpenAI text-embedding-3-large

**Key Insight:** Store dimension info for debugging and to support model migrations.

### 1.4 Contextual Embeddings

**Pattern:** Enhance chunks with full document context before embedding

```python
# Optional enhancement - disabled by default, enabled via setting
use_contextual = await credential_service.get_credential(
    "USE_CONTEXTUAL_EMBEDDINGS", "false", decrypt=True
)

if use_contextual:
    # Send chunk + full document to LLM for context enrichment
    contextual_contents = await generate_contextual_embeddings_batch(
        full_documents,  # Full page content
        chunk_contents   # Individual chunks
    )

    # Mark which chunks have contextual embeddings
    metadata["contextual_embedding"] = True
```

**LLM Prompt Pattern:**
```
Document: {full_document}
Chunk: {chunk}

Rewrite this chunk with context from the full document to improve semantic search.
```

**Key Insight:** Contextual embeddings improve retrieval quality but increase LLM costs. Make it configurable.

### 1.5 Reranking with CrossEncoder

**Pattern:** Use CrossEncoder models to re-score search results

```python
class RerankingStrategy:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    async def rerank_results(self, query, results, content_key="content", top_k=None):
        # Build query-document pairs
        query_doc_pairs = [[query, result[content_key]] for result in results]

        # Get rerank scores
        scores = self.model.predict(query_doc_pairs)

        # Add scores and sort by relevance
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])

        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

        # Return top_k if specified
        return reranked[:top_k] if top_k else reranked
```

**Key Insight:** Fetch 5x more candidates when reranking is enabled (e.g., fetch 25 to return top 5 after reranking).

### 1.6 Batch Processing with Progress Callbacks

**Pattern:** Process large datasets in batches with detailed progress reporting

```python
async def add_documents_to_supabase(
    contents,
    batch_size=50,
    progress_callback=None,
    cancellation_check=None
):
    total_batches = (len(contents) + batch_size - 1) // batch_size
    completed_batches = 0

    for batch_num, i in enumerate(range(0, len(contents), batch_size), 1):
        # Check for cancellation
        if cancellation_check:
            try:
                cancellation_check()
            except asyncio.CancelledError:
                if progress_callback:
                    await progress_callback(
                        "cancelled", 99, "Storage cancelled",
                        current_batch=batch_num,
                        total_batches=total_batches
                    )
                raise

        # Process batch
        batch_contents = contents[i:i+batch_size]
        embeddings = await create_embeddings_batch(batch_contents)

        # Insert with retry logic
        for retry in range(3):
            try:
                client.table("documents").insert(batch_data).execute()
                completed_batches += 1

                # Report progress
                progress = int((completed_batches / total_batches) * 100)
                await progress_callback(
                    "processing", progress,
                    f"Batch {batch_num}/{total_batches}",
                    completed_batches=completed_batches
                )
                break
            except Exception as e:
                if retry == 2:
                    # Final attempt: try individual inserts
                    pass
```

**Key Features:**
- Cancellation support (graceful shutdown)
- Progress reporting (batch-level granularity)
- Retry logic with exponential backoff
- Fallback to individual inserts on batch failure
- Configurable batch sizes from settings

---

## 2. MCP Server Patterns

### 2.1 HTTP-Based Microservices (from Archon)

**Pattern:** MCP server communicates via HTTP, not direct imports

```python
# MCP Server Tool (runs in separate process)
@mcp.tool()
async def rag_search_knowledge_base(ctx: Context, query: str, source_id: str = None):
    """Search knowledge base using RAG"""
    api_url = get_api_url()  # Service discovery
    timeout = httpx.Timeout(30.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            urljoin(api_url, "/api/rag/query"),
            json={"query": query, "source": source_id}
        )

        if response.status_code == 200:
            result = response.json()
            return json.dumps({
                "success": True,
                "results": result.get("results", []),
                "error": None
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }, indent=2)
```

**Benefits:**
- True microservices architecture
- MCP server can restart independently
- Clear service boundaries
- Easier testing and deployment

### 2.2 Lifespan Context Management (from mcp-mem0)

**Pattern:** Manage resources across MCP server lifecycle

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class Mem0Context:
    """Context for the Mem0 MCP server"""
    mem0_client: Memory

@asynccontextmanager
async def mem0_lifespan(server: FastMCP) -> AsyncIterator[Mem0Context]:
    """Manages the Mem0 client lifecycle"""
    # Initialize resource
    mem0_client = get_mem0_client()

    try:
        yield Mem0Context(mem0_client=mem0_client)
    finally:
        # Cleanup (if needed)
        pass

# Initialize FastMCP with lifespan
mcp = FastMCP(
    "mcp-mem0",
    lifespan=mem0_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)

# Access context in tools
@mcp.tool()
async def save_memory(ctx: Context, text: str):
    mem0_client = ctx.request_context.lifespan_context.mem0_client
    mem0_client.add([{"role": "user", "content": text}])
```

**Key Insight:** Lifespan context prevents repeated initialization and cleanup for every tool call.

### 2.3 Memory Operations Pattern (from mcp-mem0)

**Pattern:** Three core memory operations

```python
# 1. Save - Store new information
@mcp.tool()
async def save_memory(ctx: Context, text: str) -> str:
    messages = [{"role": "user", "content": text}]
    mem0_client.add(messages, user_id=DEFAULT_USER_ID)
    return f"Successfully saved memory"

# 2. Search - Semantic search for relevant memories
@mcp.tool()
async def search_memories(ctx: Context, query: str, limit: int = 3) -> str:
    memories = mem0_client.search(query, user_id=DEFAULT_USER_ID, limit=limit)
    return json.dumps([m["memory"] for m in memories["results"]], indent=2)

# 3. Get All - Retrieve complete context
@mcp.tool()
async def get_all_memories(ctx: Context) -> str:
    memories = mem0_client.get_all(user_id=DEFAULT_USER_ID)
    return json.dumps([m["memory"] for m in memories["results"]], indent=2)
```

**Key Insight:** Three operations cover most use cases - save, search, retrieve all.

---

## 3. Settings & Configuration Patterns (from Archon)

### 3.1 Database-Backed Settings with Encryption

**Pattern:** Store settings in database with optional encryption

```python
class CredentialService:
    """Manages credentials and settings"""

    async def get_credential(self, key: str, default: str = "", decrypt: bool = False):
        """Get a credential from database or environment"""
        # Try database first
        if hasattr(self, "_cache") and self._cache_initialized:
            cached_value = self._cache.get(key)

            if isinstance(cached_value, dict) and cached_value.get("is_encrypted"):
                if decrypt:
                    return self._decrypt_value(cached_value["encrypted_value"])
                return cached_value["encrypted_value"]
            elif cached_value:
                return str(cached_value)

        # Fallback to environment variable
        return os.getenv(key, default)

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Get boolean setting"""
        value = self.get_setting(key, "false" if not default else "true")
        return value.lower() in ("true", "1", "yes", "on")
```

**Database Schema:**
```sql
CREATE TABLE archon_settings (
    id UUID PRIMARY KEY,
    category TEXT NOT NULL,  -- "rag_strategy", "llm", "embeddings"
    key TEXT NOT NULL,
    value TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, key)
);
```

**Key Insight:** Settings are versioned, encrypted, and categorized. No need to restart services to change configuration.

### 3.2 RAG Strategy Settings

**Settings Used in Archon:**
```python
# Search strategies
USE_HYBRID_SEARCH=true           # Enable hybrid vector+text search
USE_RERANKING=true              # Enable CrossEncoder reranking
USE_AGENTIC_RAG=true            # Enable agentic code extraction
USE_CONTEXTUAL_EMBEDDINGS=false # Expensive but improves quality

# Batch processing
DOCUMENT_STORAGE_BATCH_SIZE=50
CONTEXTUAL_EMBEDDING_BATCH_SIZE=50
CONTEXTUAL_EMBEDDINGS_MAX_WORKERS=4
DELETE_BATCH_SIZE=50
ENABLE_PARALLEL_BATCHES=true

# Models
RERANKING_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKING_TOP_K=0  # 0 = return all

# Model selection
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
LLM_PROVIDER=openai
LLM_CHAT_MODEL=gpt-4o-mini
```

---

## 4. Context Engineering Patterns (from context-engineering-intro)

### 4.1 PRP Framework (Product Requirements Prompt)

**Pattern:** Structured prompt template for AI agents

```yaml
name: "Multi-Agent System: Research Agent with Email Draft Sub-Agent"
description: |
  ## Purpose
  Build a Pydantic AI multi-agent system...

  ## Core Principles
  1. Context is King: Include ALL necessary documentation
  2. Validation Loops: Provide executable tests/lints
  3. Information Dense: Use keywords from codebase
  4. Progressive Success: Start simple, validate, enhance

## Goal
[Clear objective]

## Why
- Business value: [What it unlocks]
- Integration: [How it fits]
- Problems solved: [What it fixes]

## What
[Concrete deliverables]

### Success Criteria
- [ ] Research Agent successfully searches via Brave API
- [ ] Email Agent creates Gmail drafts
- [ ] All tests pass

## All Needed Context

### Documentation & References
```yaml
- url: https://ai.pydantic.dev/agents/
  why: Core agent creation patterns

- file: examples/agent/agent.py
  why: Pattern for agent creation, tool registration
```

### Current Codebase
[Tree structure showing current state]

### Desired Codebase
[Tree structure showing target state]

## Implementation Steps
1. [Step with validation command]
2. [Step with validation command]

## Validation
[Commands to verify each step]
```

**Key Principles:**
1. **Context is King** - Include all docs, examples, caveats
2. **Validation Loops** - Provide runnable tests for AI to self-check
3. **Information Dense** - Use actual keywords from codebase
4. **Progressive Success** - Start simple, validate, then enhance

### 4.2 CLAUDE.md Pattern

**Pattern:** Single file with all AI interaction rules

```markdown
### 🔄 Project Awareness & Context
- Always read PLANNING.md at start of conversation
- Check TASK.md before starting new tasks
- Use consistent naming conventions from PLANNING.md

### 🧱 Code Structure & Modularity
- Never create files longer than 500 lines
- Organize into modules by feature:
  - agent.py - Main agent definition
  - tools.py - Tool functions
  - prompts.py - System prompts

### 🧪 Testing & Reliability
- Always create Pytest unit tests for new features
- Tests should live in /tests folder
- Include: expected use, edge case, failure case

### ✅ Task Completion
- Mark completed tasks in TASK.md immediately

### 📎 Style & Conventions
- Use Python, PEP8, type hints, black formatting
- Use pydantic for data validation
- Write docstrings for every function (Google style)
```

### 4.3 Modular Agent Structure

**Pattern:** Separate files for different concerns

```
agents/
├── research_agent/
│   ├── __init__.py
│   ├── agent.py          # Agent definition & execution
│   ├── tools.py          # Tool functions
│   ├── prompts.py        # System prompts
│   └── models.py         # Pydantic models
```

**agent.py:**
```python
from .tools import brave_search_tool, email_draft_tool
from .prompts import RESEARCH_AGENT_PROMPT
from .models import ResearchResult

def create_research_agent(deps: AgentDependencies):
    return Agent(
        name="research_agent",
        tools=[brave_search_tool, email_draft_tool],
        system_prompt=RESEARCH_AGENT_PROMPT,
        result_type=ResearchResult
    )
```

**Key Insight:** Clear separation makes code easier to understand and modify.

---

## 5. Integration Recommendations for Agent Factory

### 5.1 Immediate Wins (Low Effort, High Value)

1. **Adopt MCP Lifespan Pattern**
   - Implement context management for agent resources
   - Prevents repeated initialization
   - File: `agent_factory/memory/context_manager.py` already exists, extend it

2. **Add Settings Service**
   - Create `agent_factory/core/settings_service.py`
   - Support database-backed + environment fallback
   - Enable runtime configuration changes

3. **Implement CLAUDE.md + TASK.md Pattern**
   - Already have CLAUDE.md, enhance with task tracking
   - Add TASK.md for active work tracking
   - Improve AI agent interaction clarity

### 5.2 Medium-Term Enhancements

1. **Add Hybrid Search to Memory Storage**
   - Current: Pure Supabase storage
   - Enhance: Add full-text search alongside vector
   - Pattern: Use PostgreSQL RPC functions like Archon

2. **Implement Batch Processing with Progress**
   - Current: No batch processing in memory system
   - Enhance: Add batch saves with progress callbacks
   - Pattern: Follow Archon's `add_documents_to_supabase`

3. **Create PRP Templates for Agent Creation**
   - Create `docs/prp_templates/` directory
   - Template for agent creation
   - Template for tool creation
   - Template for integration addition

### 5.3 Future Considerations

1. **Multi-Dimensional Embedding Support**
   - Current: Single embedding column
   - Future: Support multiple dimensions
   - Enables model switching without migration

2. **Reranking Strategy**
   - Add CrossEncoder reranking for memory search
   - Improves retrieval quality for complex queries
   - Optional, settings-driven

3. **HTTP-Based MCP Integration**
   - Current: Agent Factory runs inline
   - Future: Separate MCP server process
   - Better for scaling and isolation

---

## 6. Code Examples for Agent Factory

### 6.1 Settings Service Implementation

```python
# agent_factory/core/settings_service.py
import os
from typing import Any, Optional
from supabase import create_client, Client

class SettingsService:
    """Database-backed settings with environment fallback"""

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.client: Optional[Client] = None
        self._cache = {}
        self._cache_initialized = False

        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                self._initialize_cache()
            except Exception as e:
                print(f"[WARN] Failed to connect to Supabase for settings: {e}")

    def _initialize_cache(self):
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

    def get_setting(self, key: str, default: str = "", category: str = "general") -> str:
        """Get a setting from cache or environment"""
        cache_key = f"{category}.{key}"

        # Try cache first
        if self._cache_initialized and cache_key in self._cache:
            return self._cache[cache_key]

        # Fallback to environment variable
        return os.getenv(key, default)

    def get_bool_setting(self, key: str, default: bool = False, category: str = "general") -> bool:
        """Get boolean setting"""
        value = self.get_setting(key, "false" if not default else "true", category)
        return value.lower() in ("true", "1", "yes", "on")

    def get_int_setting(self, key: str, default: int = 0, category: str = "general") -> int:
        """Get integer setting"""
        value = self.get_setting(key, str(default), category)
        try:
            return int(value)
        except ValueError:
            return default

# Singleton instance
settings_service = SettingsService()
```

**Database Schema:**
```sql
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

-- Example settings
INSERT INTO agent_factory_settings (category, key, value, description) VALUES
('memory', 'USE_HYBRID_SEARCH', 'false', 'Enable hybrid vector + text search'),
('memory', 'BATCH_SIZE', '50', 'Batch size for memory operations'),
('orchestration', 'MAX_RETRIES', '3', 'Max retries for agent calls'),
('llm', 'DEFAULT_MODEL', 'gpt-4o-mini', 'Default LLM model');
```

### 6.2 Hybrid Search for Agent Factory Memory

```python
# agent_factory/memory/hybrid_search.py
from typing import List, Dict, Any, Optional
from supabase import Client

async def hybrid_search_memories(
    client: Client,
    query: str,
    query_embedding: List[float],
    session_id: str,
    match_count: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search on session_memories table.

    Combines vector similarity with full-text search for better recall.
    """
    try:
        # Call PostgreSQL RPC function
        response = client.rpc(
            "hybrid_search_session_memories",
            {
                "query_embedding": query_embedding,
                "query_text": query,
                "p_session_id": session_id,
                "match_count": match_count
            }
        ).execute()

        if not response.data:
            return []

        # Format results
        results = []
        for row in response.data:
            result = {
                "id": row["id"],
                "memory_type": row["memory_type"],
                "content": row["content"],
                "metadata": row["metadata"],
                "similarity": row["similarity"],
                "match_type": row["match_type"],  # "vector", "text", or "both"
                "created_at": row["created_at"]
            }
            results.append(result)

        return results

    except Exception as e:
        print(f"[ERROR] Hybrid memory search failed: {e}")
        return []
```

**PostgreSQL RPC Function:**
```sql
CREATE OR REPLACE FUNCTION hybrid_search_session_memories(
    query_embedding vector(1536),
    query_text TEXT,
    p_session_id TEXT,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    session_id TEXT,
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
            m.id, m.session_id, m.memory_type, m.content, m.metadata,
            1 - (m.embedding <=> query_embedding) AS similarity,
            'vector' AS match_type,
            m.created_at
        FROM session_memories m
        WHERE m.session_id = p_session_id
        ORDER BY m.embedding <=> query_embedding
        LIMIT match_count
    ),
    text_search AS (
        SELECT
            m.id, m.session_id, m.memory_type, m.content, m.metadata,
            ts_rank(to_tsvector('english', m.content::text), plainto_tsquery('english', query_text)) AS similarity,
            'text' AS match_type,
            m.created_at
        FROM session_memories m
        WHERE m.session_id = p_session_id
            AND to_tsvector('english', m.content::text) @@ plainto_tsquery('english', query_text)
        ORDER BY similarity DESC
        LIMIT match_count
    )
    SELECT DISTINCT ON (v.id)
        v.id, v.session_id, v.memory_type, v.content, v.metadata,
        GREATEST(v.similarity, COALESCE(t.similarity, 0)) AS similarity,
        CASE
            WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'both'
            WHEN v.id IS NOT NULL THEN 'vector'
            ELSE 'text'
        END AS match_type,
        v.created_at
    FROM vector_search v
    FULL OUTER JOIN text_search t ON v.id = t.id
    ORDER BY v.id, similarity DESC
    LIMIT match_count;
END;
$$;
```

---

## 7. Key Takeaways

### What Makes Archon Production-Ready

1. **Composable Architecture** - Strategies can be mixed and matched
2. **Settings-Driven** - No code changes needed for configuration
3. **Robust Error Handling** - Retry logic, fallbacks, detailed logging
4. **Progress Reporting** - Users see what's happening during long operations
5. **Cancellation Support** - Graceful shutdown of long-running tasks
6. **Multi-Model Support** - Works with different embeddings and LLMs

### What Makes context-engineering-intro Effective

1. **Clear Structure** - CLAUDE.md, PLANNING.md, TASK.md system
2. **Modular Code** - Separate files for agent, tools, prompts
3. **Validation Loops** - AI can test its own work
4. **Context References** - URLs and files with "why they matter"
5. **Progressive Success** - Start simple, validate, enhance

### What Makes mcp-mem0 Clean

1. **Lifespan Management** - Resources initialized once, cleaned up properly
2. **Three Core Operations** - Save, search, retrieve all
3. **JSON Responses** - Consistent format for all tools
4. **User Scoping** - Memories isolated by user_id
5. **Transport Flexibility** - SSE or stdio based on config

---

## 8. Next Steps for Agent Factory

### Immediate (This Week)
- [ ] Add `agent_factory/core/settings_service.py` with database + env fallback
- [ ] Create `TASK.md` for active work tracking
- [ ] Enhance `CLAUDE.md` with modular structure principles

### Short-Term (This Month)
- [ ] Add hybrid search RPC function to Supabase
- [ ] Implement batch processing for memory operations
- [ ] Create PRP templates in `docs/prp_templates/`

### Long-Term (Next Quarter)
- [ ] Multi-dimensional embedding support
- [ ] Reranking strategy for memory search
- [ ] HTTP-based MCP server (optional)

---

**References:**
- Archon: https://github.com/coleam00/Archon
- context-engineering-intro: https://github.com/coleam00/context-engineering-intro
- mcp-mem0: https://github.com/coleam00/mcp-mem0
