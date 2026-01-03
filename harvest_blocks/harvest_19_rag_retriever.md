# HARVEST BLOCK 19: RAG Retriever

**Priority**: MEDIUM
**Size**: 6.31KB (185 lines)
**Source**: `agent_factory/rivet_pro/rag/retriever.py`
**Target**: `rivet/rivet_pro/rag/retriever.py`

---

## Overview

Vector-based similarity search with PostgreSQL pgvector backend - performs semantic search over knowledge atoms with context window optimization and relevance filtering.

### What This Adds

- **pgvector integration**: PostgreSQL vector similarity search
- **Context window optimization**: Limits results to fit within token budget
- **Relevance filtering**: Minimum similarity threshold (default 0.5)
- **Hybrid search support**: Combines vector + keyword search
- **Connection pooling**: Reuses database connections for performance
- **Batch retrieval**: Efficient multi-query retrieval

### Key Features

```python
from rivet.rivet_pro.rag.retriever import RAGRetriever

# Initialize retriever
retriever = RAGRetriever(
    connection_string="postgresql://user:pass@localhost/rivet",
    embedding_model="text-embedding-ada-002",
    similarity_threshold=0.5,  # Minimum similarity score
    max_results=10
)

# Semantic search
results = retriever.retrieve(
    query="How to troubleshoot Siemens S7-1200 fault F0003?",
    limit=5
)

for result in results:
    print(f"Atom: {result['atom_id']}")
    print(f"Score: {result['score']:.2f}")
    print(f"Content: {result['content'][:100]}...")

# Hybrid search (vector + keyword)
results = retriever.hybrid_search(
    query="motor overheating",
    keywords=["motor", "temperature", "thermal"],
    vector_weight=0.7,  # 70% vector, 30% keyword
    limit=10
)

# Batch retrieval
queries = [
    "S7-1200 communication error",
    "PowerFlex 525 fault F003",
    "Motor vibration troubleshooting"
]
batch_results = retriever.batch_retrieve(queries, limit=5)
```

---

## Vector Similarity Search

```python
# pgvector cosine similarity query
SELECT
    atom_id,
    title,
    content,
    1 - (embedding <=> query_embedding) AS score
FROM knowledge_atoms
WHERE 1 - (embedding <=> query_embedding) > 0.5
ORDER BY embedding <=> query_embedding
LIMIT 10;

# Operators:
# <=> - Cosine distance (1 - similarity)
# <#> - Negative inner product
# <-> - L2 distance (Euclidean)
```

---

## Context Window Optimization

```python
# Limit results to fit within token budget
def optimize_for_context(results, max_tokens=4000):
    """Select top results that fit within token budget"""
    selected = []
    total_tokens = 0

    for result in results:
        content_tokens = len(result['content']) // 4  # Rough estimate
        if total_tokens + content_tokens <= max_tokens:
            selected.append(result)
            total_tokens += content_tokens
        else:
            break

    return selected

# Usage:
results = retriever.retrieve(query, limit=20)
optimized = retriever.optimize_for_context(results, max_tokens=4000)
```

---

## Hybrid Search (Vector + Keyword)

```python
# Combine vector similarity with keyword matching
def hybrid_search(query, keywords, vector_weight=0.7):
    """
    Hybrid search combines:
    - Vector similarity (semantic understanding)
    - Keyword matching (exact term coverage)
    """
    # Vector search
    vector_results = retrieve(query, limit=50)

    # Keyword search
    keyword_results = keyword_search(keywords, limit=50)

    # Merge and rerank
    merged = merge_results(
        vector_results,
        keyword_results,
        vector_weight=vector_weight
    )

    return merged[:10]  # Top 10 hybrid results
```

---

## Dependencies

```bash
# Install required packages
poetry add psycopg2-binary pgvector openai

# Database setup
psql -d rivet -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Environment Variables

```bash
export DATABASE_URL=postgresql://user:pass@localhost/rivet
export OPENAI_API_KEY=sk-...  # For embeddings
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/rivet_pro/rag/retriever.py rivet/rivet_pro/rag/retriever.py`
2. Install: `poetry add psycopg2-binary pgvector openai`
3. Setup database: `psql -d rivet -c "CREATE EXTENSION vector;"`
4. Validate: `python -c "from rivet.rivet_pro.rag.retriever import RAGRetriever; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.rivet_pro.rag.retriever import RAGRetriever; print('OK')"

# Test retrieval (requires database)
python -c "
from rivet.rivet_pro.rag.retriever import RAGRetriever

retriever = RAGRetriever()
results = retriever.retrieve('test query', limit=5)
print(f'Retrieved {len(results)} results')
"
```

---

## Integration Notes

**RivetOrchestrator Integration** (Route A):
```python
# In orchestrator - retrieve relevant KB docs
results = retriever.retrieve(
    query=request.text,
    limit=10
)

# Filter by relevance threshold
filtered = [r for r in results if r['score'] >= 0.5]

# Pass to SME agent
response = agent.generate_response(
    query=request.text,
    kb_docs=filtered
)
```

**Performance**:
- Retrieval latency: <100ms (with pgvector index)
- Batch retrieval: <500ms for 10 queries
- Index type: IVFFlat or HNSW (recommended for >100K atoms)

---

## What This Enables

- ✅ Semantic search over knowledge atoms (vector similarity)
- ✅ Context window optimization (fit within token budget)
- ✅ Relevance filtering (minimum similarity threshold)
- ✅ Hybrid search (vector + keyword combination)
- ✅ Connection pooling (database performance)
- ✅ Batch retrieval (efficient multi-query processing)

---

## Next Steps

After implementing HARVEST 19, proceed to **HARVEST 20: Confidence Scorer** for multi-dimensional response confidence scoring.

SEE FULL SOURCE: `agent_factory/rivet_pro/rag/retriever.py` (185 lines - copy as-is)
