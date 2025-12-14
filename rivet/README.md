# Rivet Industrial - Knowledge Base Factory

24/7 automated knowledge base ingestion pipeline powered by LangGraph + Ollama + Postgres+pgvector.

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│  Scheduler  │────▶│  Redis   │◀────│   Worker    │
│  (hourly)   │     │  Queue   │     │  (24/7)     │
└─────────────┘     └──────────┘     └──────┬──────┘
                                             │
                           ┌─────────────────┴─────────────────┐
                           │      LangGraph Pipeline           │
                           │  Discovery → Download → Parse     │
                           │  → Critique → Index               │
                           └─────────────────┬─────────────────┘
                                             │
                ┌────────────────────────────┴────────────────────┐
                │                                                  │
          ┌─────▼──────┐                                  ┌───────▼──────┐
          │  Postgres  │                                  │    Ollama    │
          │ + pgvector │                                  │  LLM+Embed   │
          └────────────┘                                  └──────────────┘
```

## Components

- **Postgres + pgvector**: Vector database for atom storage and semantic search
- **Redis**: Job queue for URL processing
- **Ollama**: Open-source LLM (Mistral) + embeddings (nomic-embed-text)
- **LangGraph App**: Python worker with 5-node ingestion pipeline

## Quick Start (VPS Deployment)

### Prerequisites

- VPS with:
  - 8+ vCPU
  - 32+ GB RAM
  - 300+ GB SSD
  - Ubuntu 22.04 or similar
- Docker + Docker Compose installed
- Git

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd rivet
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for Docker Compose setup)
```

### 3. Start Services

```bash
cd infra
docker compose up -d
```

### 4. Load Ollama Models

```bash
# Load LLM (takes ~5-10 min, 4.1GB)
docker exec -it infra-ollama-1 ollama pull mistral:latest

# Load embedding model (takes ~2 min, 274MB)
docker exec -it infra-ollama-1 ollama pull nomic-embed-text
```

### 5. Verify Services

```bash
# Check all services running
docker compose ps

# Watch worker logs
docker compose logs -f rivet-worker

# Watch scheduler logs
docker compose logs -f rivet-scheduler
```

### 6. Monitor Processing

```bash
# Check Redis queue
docker exec -it infra-redis-1 redis-cli LLEN kb_ingest_jobs

# Check database for atoms
docker exec -it infra-postgres-1 psql -U rivet -d rivet -c "SELECT COUNT(*) FROM knowledge_atoms;"
```

## Development / Testing

### Local CLI Test

```bash
# Build image
docker build -f infra/docker/Dockerfile -t rivet-app .

# Test single URL
docker run --rm --env-file .env rivet-app \
  python -m langgraph_app.cli "https://example.com/manual.pdf"
```

### Database Schema

The `knowledge_atoms` table is auto-created on first run:

```sql
CREATE TABLE knowledge_atoms (
    id SERIAL PRIMARY KEY,
    atom_type VARCHAR(50),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | Postgres hostname |
| `POSTGRES_DB` | `rivet` | Database name |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_LLM_MODEL` | `mistral:latest` | LLM for extraction |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `SCHEDULER_INTERVAL` | `3600` | Seconds between scheduler runs |
| `WORKER_POLL_INTERVAL` | `5` | Worker Redis poll interval |

## LangGraph Pipeline

### Nodes

1. **Discovery**: Validate source URL
2. **Downloader**: Fetch PDF/HTML and extract text
3. **Parser**: Use Ollama LLM to extract structured atoms
4. **Critic**: Validate atom quality
5. **Indexer**: Store in Postgres with pgvector embeddings

### Flow

```python
Discovery → Downloader → Parser → Critic → (if valid) → Indexer → END
                                         → (if errors) → END
```

## Adding New Sources

Edit `langgraph_app/scheduler.py` and add URLs to `SEED_SOURCES`:

```python
SEED_SOURCES = [
    "https://your-doc-1.pdf",
    "https://your-doc-2.html",
]
```

Or implement database-driven discovery (query `sources` table).

## Troubleshooting

### Worker not processing jobs

```bash
# Check Redis queue has jobs
docker exec -it infra-redis-1 redis-cli LLEN kb_ingest_jobs

# Manually enqueue test job
docker exec -it infra-redis-1 redis-cli RPUSH kb_ingest_jobs "https://example.com/test.pdf"
```

### Ollama model not found

```bash
# List loaded models
docker exec -it infra-ollama-1 ollama list

# Pull missing model
docker exec -it infra-ollama-1 ollama pull mistral:latest
```

### Database connection failed

```bash
# Check Postgres health
docker compose ps postgres

# Test connection
docker exec -it infra-postgres-1 psql -U rivet -d rivet -c "SELECT 1;"
```

## Production Checklist

- [ ] Change `POSTGRES_PASSWORD` in `.env`
- [ ] Set `LOG_LEVEL=WARNING` for production
- [ ] Configure firewall (only expose necessary ports)
- [ ] Set up backups for `pgdata` volume
- [ ] Monitor disk usage (Ollama models + pgvector data)
- [ ] Add observability (Langfuse, Prometheus, etc.)

## Next Steps

1. **Implement proper PDF parsing** (replace placeholder in `downloader.py`)
2. **Add discovery from database** (replace hardcoded URLs in `scheduler.py`)
3. **Add semantic search API** (query pgvector for similar atoms)
4. **Add observability** (Langfuse for LangGraph tracing)
5. **Add tests** (pytest for nodes and graph)

## License

Proprietary - Rivet Industrial

---

**Status**: V1 - Production-ready for single VPS deployment
**Last Updated**: 2024-12-13
