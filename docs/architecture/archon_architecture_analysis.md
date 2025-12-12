# Archon Architecture Analysis

**Date:** 2025-12-09
**Repository:** https://github.com/coleam00/Archon (13.4k⭐)
**Purpose:** Deep dive into Archon's microservices architecture for Agent Factory integration

---

## 1. System Overview

Archon is a production-ready RAG (Retrieval-Augmented Generation) system built with:
- **Backend:** Python 3.12, FastAPI, Supabase (PostgreSQL + pgvector)
- **Frontend:** React 18, TypeScript, Vite, TanStack Query
- **MCP Server:** FastMCP for AI assistant integration
- **Agent Service:** Microservice for agent work orders
- **Database:** Supabase with pgvector extension for vector search

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Browser    │  │  Claude.app  │  │  Cursor/Windsurf     │  │
│  │  (React UI)  │  │              │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────┘  │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          │ HTTP/REST        │ MCP Protocol     │ MCP Protocol
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────────┐
│                      Service Layer                                │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │  FastAPI       │  │  MCP Server    │  │  Agent Work      │   │
│  │  Server        │  │  (FastMCP)     │  │  Orders Service  │   │
│  │  Port 8181     │  │  Port 8051     │  │  Port 8053       │   │
│  └────────┬───────┘  └────────┬───────┘  └────────┬─────────┘   │
│           │                   │                     │             │
│           │ HTTP              │ HTTP                │ HTTP        │
│           │                   │                     │             │
└───────────┼───────────────────┼─────────────────────┼─────────────┘
            │                   │                     │
            │                   │                     │
            └───────────────────┴─────────────────────┘
                                │
                                │
                    ┌───────────▼────────────┐
                    │   Supabase Database    │
                    │   (PostgreSQL + pgvec) │
                    │                        │
                    │  - archon_sources      │
                    │  - archon_crawled_pages│
                    │  - archon_code_examples│
                    │  - archon_page_metadata│
                    │  - archon_settings     │
                    └────────────────────────┘
```

---

## 2. Service Breakdown

### 2.1 FastAPI Server (Port 8181)

**Purpose:** Core business logic, API endpoints, RAG queries, document processing

**Key Components:**

```python
# src/server/main.py
app = FastAPI(title="Archon API", version="1.0.0")

# API Routes Structure
/api/rag/query              # RAG search with hybrid + reranking
/api/rag/sources            # List knowledge sources
/api/rag/code-examples      # Search code snippets
/api/pages                  # Page metadata management
/api/pages/{page_id}        # Get full page content
/api/projects               # Project management (optional)
/api/tasks                  # Task tracking
/api/settings               # Runtime configuration
/api/providers              # LLM provider management
/api/internal/health        # Service health checks
```

**Service Layer Pattern:**

```
API Route → Service → Database
     ↓          ↓         ↓
Handler    Business    Supabase
Function    Logic      Queries
```

Example:
```python
# api_routes/knowledge_api.py
@router.post("/api/rag/query")
async def rag_query(request: RAGQueryRequest):
    # Validate input
    # Call service layer
    success, result = await rag_service.perform_rag_query(
        query=request.query,
        source=request.source,
        match_count=request.match_count
    )
    return result

# services/search/rag_service.py
class RAGService:
    async def perform_rag_query(self, query, source, match_count):
        # 1. Create embedding
        embedding = await create_embedding(query)

        # 2. Search with hybrid strategy
        results = await self.hybrid_strategy.search_documents(...)

        # 3. Rerank if enabled
        if self.reranking_strategy:
            results = await self.reranking_strategy.rerank_results(...)

        # 4. Format and return
        return True, {"results": results, ...}
```

**Key Services:**

1. **RAGService** (`services/search/rag_service.py`)
   - Orchestrates search strategies
   - Handles hybrid search, reranking, agentic RAG
   - Pipeline: Search → Rerank → Group

2. **CrawlingService** (`services/crawling/crawling_service.py`)
   - Web scraping with Crawl4AI
   - Multiple strategies: single page, recursive, sitemap, batch
   - Progress tracking and cancellation support

3. **EmbeddingService** (`services/embeddings/embedding_service.py`)
   - Multi-provider embedding generation
   - Batch processing with rate limiting
   - Contextual embeddings (optional)

4. **CredentialService** (`services/credential_service.py`)
   - Database-backed settings with encryption
   - Environment variable fallback
   - Runtime configuration updates

### 2.2 MCP Server (Port 8051)

**Purpose:** Model Context Protocol server for AI assistant integration (Claude, Cursor, Windsurf)

**Architecture Pattern:** HTTP-based microservice (no direct imports from FastAPI server)

**Tools Provided:**

```python
# src/mcp_server/features/rag/rag_tools.py

@mcp.tool()
async def rag_search_knowledge_base(ctx, query, source_id=None, match_count=5):
    """Search knowledge base using RAG"""
    # HTTP call to FastAPI server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/rag/query",
            json={"query": query, "source": source_id, "match_count": match_count}
        )
    return json.dumps(response.json())

@mcp.tool()
async def rag_get_available_sources(ctx):
    """List all knowledge sources"""
    # HTTP call to FastAPI server
    ...

@mcp.tool()
async def rag_read_full_page(ctx, page_id=None, url=None):
    """Retrieve full page content"""
    # HTTP call to FastAPI server
    ...
```

**Other Tool Categories:**
- **Projects** (`find_projects`, `manage_project`)
- **Tasks** (`find_tasks`, `manage_task`)
- **Documents** (`find_documents`, `manage_document`)
- **Versions** (`find_versions`, `manage_version`)

**Tool Pattern:**
- `find_*` - List, search, or get single item
- `manage_*` - Create, update, delete with action parameter

**Benefits of HTTP-based MCP:**
- True microservices isolation
- Independent restart/upgrade
- Clear service boundaries
- Easier testing and deployment

### 2.3 Agent Work Orders Service (Port 8053)

**Purpose:** Independent microservice for agent task management

**Pattern:** Separate FastAPI app with its own lifecycle

```python
# src/agent_work_orders/server.py
app = FastAPI(title="Agent Work Orders Service")

@app.post("/work-orders")
async def create_work_order(request: WorkOrderRequest):
    # Business logic for agent work orders
    ...
```

**Why Separate Service:**
- Agent operations can be resource-intensive
- Can scale independently from main API
- Can use different infrastructure (GPU, memory)
- Isolated failure domain

---

## 3. Database Architecture

### 3.1 Core Tables

**archon_sources** - Knowledge source metadata
```sql
CREATE TABLE archon_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    domain TEXT,
    crawl_status TEXT,  -- 'pending', 'in_progress', 'completed', 'failed'
    total_pages INT DEFAULT 0,
    pages_crawled INT DEFAULT 0,
    strategy TEXT,  -- 'single_page', 'recursive', 'sitemap', 'batch'
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sources_crawl_status ON archon_sources(crawl_status);
CREATE INDEX idx_sources_domain ON archon_sources(domain);
```

**archon_crawled_pages** - Document chunks with embeddings
```sql
CREATE TABLE archon_crawled_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    chunk_number INT DEFAULT 0,
    content TEXT NOT NULL,

    -- Multi-dimensional embedding support
    embedding_768 vector(768),
    embedding_1024 vector(1024),
    embedding_1536 vector(1536),
    embedding_3072 vector(3072),

    -- Model tracking
    embedding_model TEXT,
    embedding_dimension INT,
    llm_chat_model TEXT,  -- For contextual embeddings

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    source_id UUID REFERENCES archon_sources(id) ON DELETE CASCADE,
    page_id UUID REFERENCES archon_page_metadata(id),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity indexes (one per dimension)
CREATE INDEX idx_crawled_pages_embedding_768
    ON archon_crawled_pages USING ivfflat (embedding_768 vector_cosine_ops);

CREATE INDEX idx_crawled_pages_embedding_1536
    ON archon_crawled_pages USING ivfflat (embedding_1536 vector_cosine_ops);

-- Full-text search index
CREATE INDEX idx_crawled_pages_content_search
    ON archon_crawled_pages USING gin(to_tsvector('english', content));

-- Foreign key indexes
CREATE INDEX idx_crawled_pages_source_id ON archon_crawled_pages(source_id);
CREATE INDEX idx_crawled_pages_page_id ON archon_crawled_pages(page_id);
```

**archon_page_metadata** - Full page tracking
```sql
CREATE TABLE archon_page_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    section_title TEXT,  -- From llms-full.txt sections
    word_count INT DEFAULT 0,
    full_content TEXT,   -- Complete page content
    source_id UUID REFERENCES archon_sources(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_page_metadata_url ON archon_page_metadata(url);
CREATE INDEX idx_page_metadata_source_id ON archon_page_metadata(source_id);
```

**archon_code_examples** - Extracted code snippets
```sql
CREATE TABLE archon_code_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    chunk_number INT DEFAULT 0,
    content TEXT NOT NULL,  -- The code snippet
    summary TEXT,           -- LLM-generated description

    -- Embeddings
    embedding_768 vector(768),
    embedding_1536 vector(1536),
    embedding_3072 vector(3072),

    metadata JSONB DEFAULT '{}'::jsonb,
    source_id UUID REFERENCES archon_sources(id),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_code_examples_embedding_1536
    ON archon_code_examples USING ivfflat (embedding_1536 vector_cosine_ops);

CREATE INDEX idx_code_examples_content_search
    ON archon_code_examples USING gin(to_tsvector('english', content || ' ' || COALESCE(summary, '')));
```

**archon_settings** - Runtime configuration
```sql
CREATE TABLE archon_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,  -- 'rag_strategy', 'llm', 'embeddings'
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    is_encrypted BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, key)
);

-- Example settings
INSERT INTO archon_settings (category, key, value) VALUES
('rag_strategy', 'USE_HYBRID_SEARCH', 'true'),
('rag_strategy', 'USE_RERANKING', 'true'),
('rag_strategy', 'USE_CONTEXTUAL_EMBEDDINGS', 'false'),
('embeddings', 'EMBEDDING_PROVIDER', 'openai'),
('embeddings', 'EMBEDDING_MODEL', 'text-embedding-3-small'),
('llm', 'LLM_PROVIDER', 'openai'),
('llm', 'LLM_CHAT_MODEL', 'gpt-4o-mini');
```

### 3.2 PostgreSQL RPC Functions

**Hybrid Search for Documents:**
```sql
CREATE OR REPLACE FUNCTION hybrid_search_archon_crawled_pages(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 5,
    filter JSONB DEFAULT '{}'::jsonb,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    url TEXT,
    chunk_number INT,
    content TEXT,
    metadata JSONB,
    source_id UUID,
    similarity FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        SELECT
            p.id, p.url, p.chunk_number, p.content, p.metadata, p.source_id,
            1 - (p.embedding_1536 <=> query_embedding) AS similarity,
            'vector' AS match_type
        FROM archon_crawled_pages p
        WHERE (source_filter IS NULL OR p.source_id::text = source_filter)
        ORDER BY p.embedding_1536 <=> query_embedding
        LIMIT match_count
    ),
    text_search AS (
        SELECT
            p.id, p.url, p.chunk_number, p.content, p.metadata, p.source_id,
            ts_rank(to_tsvector('english', p.content), plainto_tsquery('english', query_text)) AS similarity,
            'text' AS match_type
        FROM archon_crawled_pages p
        WHERE (source_filter IS NULL OR p.source_id::text = source_filter)
            AND to_tsvector('english', p.content) @@ plainto_tsquery('english', query_text)
        ORDER BY similarity DESC
        LIMIT match_count
    )
    SELECT DISTINCT ON (v.id)
        COALESCE(v.id, t.id) AS id,
        COALESCE(v.url, t.url) AS url,
        COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
        COALESCE(v.content, t.content) AS content,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.source_id, t.source_id) AS source_id,
        GREATEST(COALESCE(v.similarity, 0), COALESCE(t.similarity, 0)) AS similarity,
        CASE
            WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'both'
            WHEN v.id IS NOT NULL THEN 'vector'
            ELSE 'text'
        END AS match_type
    FROM vector_search v
    FULL OUTER JOIN text_search t ON v.id = t.id
    ORDER BY v.id, similarity DESC
    LIMIT match_count;
END;
$$;
```

**Hybrid Search for Code Examples:**
```sql
CREATE OR REPLACE FUNCTION hybrid_search_archon_code_examples(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::jsonb,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    url TEXT,
    chunk_number INT,
    content TEXT,
    summary TEXT,
    metadata JSONB,
    source_id UUID,
    similarity FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Similar pattern to document search
    -- Combines vector similarity on code + summary with full-text search
    ...
END;
$$;
```

### 3.3 Database Indexes Strategy

**Vector Indexes (IVFFlat):**
- One index per embedding dimension
- Uses cosine similarity (`vector_cosine_ops`)
- IVFFlat is faster than HNSW for moderate datasets (<1M vectors)

**Full-Text Search Indexes (GIN):**
- On `content` column for documents
- On `content || summary` for code examples
- Uses PostgreSQL's built-in text search

**Foreign Key Indexes:**
- All FK columns have indexes for JOIN performance
- Enables efficient cascade deletes

**Composite Indexes:**
- `(source_id, created_at)` for time-based queries
- `(crawl_status, updated_at)` for crawl monitoring

---

## 4. RAG Pipeline Deep Dive

### 4.1 Document Ingestion Pipeline

```
1. URL Input
   ↓
2. Crawling Service
   │ - Strategy selection (single/recursive/sitemap/batch)
   │ - Crawl4AI web scraping
   │ - Progress tracking
   ↓
3. Document Processing
   │ - Text extraction
   │ - Chunking (configurable size)
   │ - Metadata extraction
   ↓
4. Optional: Contextual Embedding
   │ - LLM rewrites chunk with document context
   │ - Improves semantic search quality
   │ - Costs: ~$0.01 per 1000 chunks
   ↓
5. Embedding Generation
   │ - Batch processing (50 chunks/batch)
   │ - Multi-provider support (OpenAI, Voyage, Cohere)
   │ - Rate limiting and retry logic
   ↓
6. Storage
   │ - Insert into archon_crawled_pages
   │ - Link to archon_page_metadata
   │ - Create vector + full-text indexes
   ↓
7. Optional: Code Extraction
   │ - LLM identifies code blocks
   │ - Generates summaries
   │ - Stores in archon_code_examples
```

**Batch Processing Pattern:**
```python
async def add_documents_to_supabase(contents, batch_size=50, progress_callback=None):
    # Load settings from database
    batch_size = await settings.get_int("DOCUMENT_STORAGE_BATCH_SIZE", 50)
    use_contextual = await settings.get_bool("USE_CONTEXTUAL_EMBEDDINGS", False)

    total_batches = (len(contents) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(contents), batch_size), 1):
        # Get batch
        batch = contents[i:i+batch_size]

        # Optional: Contextual embeddings
        if use_contextual:
            batch = await generate_contextual_embeddings_batch(batch)

        # Generate embeddings with rate limiting
        embeddings = await create_embeddings_batch(batch)

        # Insert with retry logic
        for retry in range(3):
            try:
                client.table("archon_crawled_pages").insert(batch_data).execute()
                break
            except Exception as e:
                if retry == 2:
                    # Final attempt: individual inserts
                    for record in batch_data:
                        try:
                            client.table("archon_crawled_pages").insert(record).execute()
                        except:
                            logger.error(f"Failed to insert {record['url']}")

        # Report progress
        progress = int((batch_num / total_batches) * 100)
        await progress_callback("processing", progress, f"Batch {batch_num}/{total_batches}")
```

### 4.2 Query Pipeline

```
1. User Query
   ↓
2. Query Embedding
   │ - Generate embedding for search query
   │ - Use same model as documents
   ↓
3. Search Strategy Selection
   │ - Check settings: USE_HYBRID_SEARCH
   │ - If true: Hybrid (vector + text)
   │ - If false: Pure vector search
   ↓
4. Hybrid Search Execution
   │ - Call PostgreSQL RPC function
   │ - Returns vector matches + text matches
   │ - Deduplicates and scores
   ↓
5. Optional: Reranking
   │ - Check settings: USE_RERANKING
   │ - If enabled: CrossEncoder re-scores results
   │ - Fetch 5x more candidates for reranker
   ↓
6. Results Formatting
   │ - Return mode: "pages" or "chunks"
   │ - If "pages": Group chunks by page_id
   │ - Include metadata, similarity scores
   ↓
7. Response
   │ - JSON with results array
   │ - Metadata: search_mode, reranking_applied
```

**Query Code Example:**
```python
async def perform_rag_query(self, query, source=None, match_count=5, return_mode="pages"):
    # 1. Create embedding
    query_embedding = await create_embedding(query)

    # 2. Check strategy settings
    use_hybrid = self.get_bool_setting("USE_HYBRID_SEARCH", False)
    use_reranking = self.get_bool_setting("USE_RERANKING", False)

    # 3. Adjust match count if reranking
    search_count = match_count * 5 if use_reranking else match_count

    # 4. Execute search
    if use_hybrid:
        results = await self.hybrid_strategy.search_documents_hybrid(
            query=query,
            query_embedding=query_embedding,
            match_count=search_count,
            filter_metadata={"source": source} if source else None
        )
    else:
        results = await self.base_strategy.vector_search(
            query_embedding=query_embedding,
            match_count=search_count
        )

    # 5. Apply reranking
    if use_reranking and self.reranking_strategy:
        results = await self.reranking_strategy.rerank_results(
            query, results, content_key="content", top_k=match_count
        )

    # 6. Group by pages if requested
    if return_mode == "pages":
        results = await self._group_chunks_by_pages(results, match_count)

    return True, {
        "results": results,
        "search_mode": "hybrid" if use_hybrid else "vector",
        "reranking_applied": use_reranking,
        "return_mode": return_mode
    }
```

---

## 5. Frontend Architecture

### 5.1 Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **TanStack Query** for data fetching (no Redux, no prop drilling)
- **Biome** for linting (features/) + ESLint (legacy)
- **Tailwind CSS** with glassmorphism styling

### 5.2 Data Fetching Pattern

**No Prop Drilling - TanStack Query Everywhere:**

```typescript
// src/features/knowledge/hooks/useRAGSearch.ts
export function useRAGSearch() {
  const mutation = useMutation({
    mutationFn: async (params: RAGSearchParams) => {
      const response = await fetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      return response.json();
    },
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['search-history'] });
    }
  });

  return mutation;
}

// Component usage - no props needed!
function SearchComponent() {
  const { mutate, data, isPending } = useRAGSearch();

  const handleSearch = (query: string) => {
    mutate({ query, match_count: 5, return_mode: "pages" });
  };

  return (
    <div>
      <SearchInput onSubmit={handleSearch} />
      {isPending && <Spinner />}
      {data && <ResultsList results={data.results} />}
    </div>
  );
}
```

### 5.3 Feature-Based Structure

```
src/features/
├── knowledge/
│   ├── components/
│   │   ├── SearchInput.tsx
│   │   └── ResultsList.tsx
│   ├── hooks/
│   │   ├── useRAGSearch.ts
│   │   └── useSources.ts
│   ├── services/
│   │   └── knowledgeService.ts
│   └── types/
│       └── knowledge.types.ts
├── projects/
│   ├── components/
│   ├── hooks/
│   └── services/
└── settings/
    ├── components/
    ├── hooks/
    └── services/
```

**Key Principle:** Vertical slices - each feature owns its sub-features.

---

## 6. Key Architectural Patterns

### 6.1 Strategy Pattern (RAG Search)

Multiple search strategies that can be composed:

```python
class BaseSearchStrategy:
    """Pure vector similarity search"""
    async def vector_search(self, embedding, match_count): ...

class HybridSearchStrategy:
    """Vector + full-text combined"""
    async def search_documents_hybrid(self, query, embedding, match_count): ...

class RerankingStrategy:
    """CrossEncoder re-scoring"""
    async def rerank_results(self, query, results, top_k): ...

class AgenticRAGStrategy:
    """Enhanced code example extraction"""
    async def search_code_examples(self, query, match_count): ...
```

### 6.2 Service Layer Pattern

**API → Service → Database**

Benefits:
- Business logic isolated from HTTP concerns
- Services are testable without FastAPI
- Services can be reused across API routes and MCP tools

### 6.3 Settings-Driven Configuration

**All major features controlled by database settings:**
- No code changes needed
- No service restarts required
- A/B testing friendly
- Environment-specific configs

### 6.4 Progress Reporting Pattern

**Long-running operations report detailed progress:**

```python
async def crawl_website(url, progress_callback):
    # Stage 1: Discovery
    await progress_callback("discovery", 10, "Finding pages...")
    pages = await discover_pages(url)

    # Stage 2: Crawling
    for i, page in enumerate(pages):
        progress = 10 + int((i / len(pages)) * 40)
        await progress_callback("crawling", progress, f"Page {i+1}/{len(pages)}")
        await crawl_page(page)

    # Stage 3: Processing
    await progress_callback("processing", 60, "Generating embeddings...")
    await generate_embeddings()

    # Stage 4: Storage
    await progress_callback("storage", 90, "Saving to database...")
    await save_to_db()

    # Complete
    await progress_callback("completed", 100, "Crawl complete")
```

**Frontend receives updates via WebSocket or polling:**
- Shows progress bar
- Displays current stage
- Allows cancellation

### 6.5 Cancellation Pattern

**Graceful shutdown for long operations:**

```python
def cancellation_check():
    """Raises CancelledError if operation should stop"""
    if is_cancelled:
        raise asyncio.CancelledError("Operation cancelled by user")

async def process_batch(batch, cancellation_check):
    for item in batch:
        cancellation_check()  # Check before each item
        await process_item(item)
```

---

## 7. Key Learnings for Agent Factory

### 7.1 Architecture Wins

1. **HTTP-Based MCP Server**
   - Clean separation of concerns
   - Independent deployment
   - Better for production scaling

2. **Strategy Pattern for Search**
   - Composable, not mutually exclusive
   - Settings-driven enablement
   - Easy to add new strategies

3. **Multi-Dimensional Embeddings**
   - Future-proof for model changes
   - Track which model was used
   - Support multiple providers

4. **Database-Backed Settings**
   - Runtime configuration changes
   - No service restarts
   - Encryption for sensitive values

5. **Batch Processing with Progress**
   - User visibility into long operations
   - Graceful cancellation support
   - Retry logic with fallbacks

### 7.2 Database Patterns

1. **RPC Functions for Complex Queries**
   - Hybrid search at database level
   - Better performance than application-level merging
   - Leverage PostgreSQL's text search capabilities

2. **Multiple Embedding Columns**
   - Support 768, 1024, 1536, 3072 dimensions
   - Dynamic column selection based on model
   - Track model name + dimension

3. **Page + Chunk Relationship**
   - `archon_page_metadata` for full pages
   - `archon_crawled_pages` for chunks
   - Link via `page_id` FK

4. **Metadata as JSONB**
   - Flexible schema evolution
   - No migrations for new fields
   - Queryable with GIN indexes

### 7.3 Operational Patterns

1. **Observability**
   - Logfire integration for traces
   - Progress callbacks for visibility
   - Match type tracking (vector/text/both)

2. **Error Handling**
   - Retry with exponential backoff
   - Fallback strategies (batch → individual)
   - Detailed error logging

3. **Performance**
   - Batch processing (50 items default)
   - Parallel embedding generation
   - Connection pooling for Supabase

---

## 8. Integration Recommendations

### For Agent Factory Memory System:

1. **Add Hybrid Search RPC Function**
   - Copy pattern from `hybrid_search_archon_crawled_pages`
   - Apply to `session_memories` table
   - Support vector + full-text search

2. **Implement Settings Service**
   - Create `agent_factory_settings` table
   - Database-backed with env fallback
   - Enable runtime configuration

3. **Add Multi-Dimensional Support**
   - Modify `session_memories` table
   - Add `embedding_768`, `embedding_1536`, etc.
   - Track `embedding_model` and `embedding_dimension`

4. **Batch Processing for Memory Operations**
   - Follow Archon's batch pattern
   - Add progress callbacks
   - Implement cancellation support

5. **Create MCP Server (Optional)**
   - Separate process for MCP tools
   - HTTP calls to Agent Factory API
   - Better isolation and scaling

---

## References

- **Repository:** https://github.com/coleam00/Archon
- **Documentation:** Archon/CLAUDE.md, Archon/README.md
- **Database Schema:** Archon/migration/complete_setup.sql
- **RAG Implementation:** Archon/python/src/server/services/search/
- **MCP Tools:** Archon/python/src/mcp_server/features/
