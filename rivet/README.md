# Rivet Industrial - KB Factory V1

**24/7 autonomous knowledge base factory for industrial documentation**

Powered by LangGraph + Postgres + pgvector + Ollama

---

## Quick Start (VPS Deployment)

### Prerequisites

- **VPS Requirements:**
  - 8 vCPU minimum (16 recommended for heavy LLM workloads)
  - 32 GB RAM minimum (64 GB recommended)
  - 300 GB SSD minimum
  - Ubuntu 22.04 or similar Linux distribution

- **Software:**
  - Docker 24+ and Docker Compose V2
  - Git

### 1-Command Deployment

```bash
# Clone repository
git clone <your-repo-url> rivet-kb-factory
cd rivet-kb-factory/rivet

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration (optional for testing)
nano .env

# Start all services
cd infra
docker compose up -d

# Pull Ollama models (required on first run)
docker exec -it rivet-ollama ollama pull mistral:latest
docker exec -it rivet-ollama ollama pull nomic-embed-text

# Verify services are running
docker compose ps

# Check worker logs
docker compose logs -f rivet-worker

# Check scheduler logs
docker compose logs -f rivet-scheduler
```

---

## Architecture

```
┌─────────────┐
│  Scheduler  │  ← Enqueues source URLs every hour
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Redis    │  ← Job queue (kb_ingest_jobs)
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│   Worker    │ ───▶ │  LangGraph   │
└──────┬──────┘      │   Pipeline   │
       │             └──────────────┘
       │                     │
       │          ┌──────────┴──────────┐
       │          │                     │
       ▼          ▼                     ▼
┌─────────────┐ ┌──────────┐    ┌──────────┐
│  Postgres   │ │  Ollama  │    │  Ollama  │
│ + pgvector  │ │   LLM    │    │  Embed   │
└─────────────┘ └──────────┘    └──────────┘
```

---

## LangGraph Pipeline

**5 nodes in sequence:**

1. **Discovery** - Fetch source URL from queue
2. **Downloader** - Download PDF/HTML and extract text
3. **Parser** - Use Ollama LLM to extract structured atoms
4. **Critic** - Validate atoms (required fields, content quality)
5. **Indexer** - Store atoms in Postgres with pgvector embeddings

---

## Testing the Pipeline

### Run a single job (CLI)

```bash
docker exec -it rivet-worker python -m langgraph_app.cli "https://example.com/manual.pdf"
```

### Check database

```bash
# Connect to Postgres
docker exec -it rivet-postgres psql -U rivet -d rivet

# Query atoms
SELECT id, atom_type, title, vendor, product 
FROM knowledge_atoms 
ORDER BY created_at DESC 
LIMIT 10;

# Check total count
SELECT atom_type, COUNT(*) 
FROM knowledge_atoms 
GROUP BY atom_type;

# Semantic search example
SELECT title, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM knowledge_atoms
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

---

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Key variables:**

- `POSTGRES_PASSWORD` - Change from default!
- `OLLAMA_LLM_MODEL` - LLM for parsing (mistral:latest, deepseek-coder, etc.)
- `OLLAMA_EMBED_MODEL` - Embedding model (nomic-embed-text recommended)
- `SCHEDULER_INTERVAL` - Seconds between scheduling runs (default: 3600)
- `WORKER_POLL_INTERVAL` - Seconds worker waits for jobs (default: 5)

### Adding Source URLs

**Option 1 - Hardcoded (V1):**
Edit `langgraph_app/scheduler.py` and add URLs to the `source_urls` list.

**Option 2 - Database (Production):**
Insert into `ingestion_sources` table:

```sql
INSERT INTO ingestion_sources (source_url, source_type, vendor, product, priority)
VALUES ('https://example.com/manual.pdf', 'pdf', 'Siemens', 'S7-1200', 10);
```

Then modify scheduler to query the table.

---

## Monitoring

### View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f rivet-worker
docker compose logs -f rivet-scheduler
```

### Check service health

```bash
docker compose ps
```

All services should show "healthy" status.

### Job history

```sql
SELECT job_id, source_url, status, atoms_indexed, 
       started_at, completed_at
FROM ingestion_jobs
ORDER BY started_at DESC
LIMIT 20;
```

---

## Ollama Models

### Recommended Models

**For LLM parsing:**
- `mistral:latest` (7B, fast, good quality)
- `deepseek-coder:6.7b` (specialized for technical docs)
- `llama3.2:latest` (8B, balanced)

**For embeddings:**
- `nomic-embed-text` (768 dimensions, recommended)
- `all-minilm` (384 dimensions, faster but lower quality)

### Pull models

```bash
docker exec -it rivet-ollama ollama pull mistral:latest
docker exec -it rivet-ollama ollama pull deepseek-coder:6.7b
docker exec -it rivet-ollama ollama pull nomic-embed-text
```

### List installed models

```bash
docker exec -it rivet-ollama ollama list
```

---

## Troubleshooting

### Worker not processing jobs

Check logs:
```bash
docker compose logs rivet-worker | tail -50
```

Common issues:
- Ollama models not pulled
- Postgres connection failed
- Redis connection failed

### Ollama errors

Restart Ollama service:
```bash
docker compose restart ollama
```

Pull models again:
```bash
docker exec -it rivet-ollama ollama pull mistral:latest
```

### Database connection errors

Check Postgres is running:
```bash
docker compose ps postgres
```

Test connection:
```bash
docker exec -it rivet-postgres psql -U rivet -d rivet -c "SELECT 1;"
```

### Low memory warnings

Ollama requires significant RAM for LLM inference:
- 7B models: ~8 GB RAM
- 13B models: ~16 GB RAM

Reduce model size or increase VPS RAM.

---

## Performance Tuning

### Speed up processing

1. Use smaller LLM models (mistral:7b instead of llama3.2:70b)
2. Reduce `SCHEDULER_INTERVAL` for faster job submission
3. Run multiple worker containers (scale horizontally)
4. Increase Postgres `max_connections` if running many workers

### Horizontal scaling

```bash
# Run 3 worker instances
docker compose up -d --scale rivet-worker=3
```

---

## Production Checklist

- [ ] Change `POSTGRES_PASSWORD` from default
- [ ] Set up automated backups for Postgres data
- [ ] Configure firewall (block ports 5432, 6379, 11434 from public)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log rotation
- [ ] Add SSL/TLS for Postgres connections
- [ ] Implement proper error alerting
- [ ] Set resource limits in docker-compose.yml
- [ ] Enable Postgres query logging for debugging
- [ ] Set up pgvector HNSW index for better search performance

---

## Next Steps

1. **Add more sources** - Edit scheduler or insert into `ingestion_sources` table
2. **Improve parsing** - Fine-tune LLM prompts in `parser_node`
3. **Add observability** - Integrate Langfuse or Langsmith
4. **Build API** - Add FastAPI endpoints for querying atoms
5. **Build UI** - Admin dashboard for monitoring ingestion

---

## Support

For issues, check:
1. Docker logs: `docker compose logs -f`
2. Postgres logs: `docker compose logs postgres`
3. Ollama API health: `curl http://localhost:11434/api/tags`

---

**Status:** Production-ready V1 ✅

Deploy, test, iterate. The KB factory is autonomous from day 1.
