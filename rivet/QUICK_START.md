# Quick Start - Rivet KB Factory

Deploy a 24/7 knowledge base factory in under 10 minutes.

## Prerequisites

- VPS with 8+ vCPU, 32+ GB RAM, 300+ GB SSD
- Ubuntu 22.04 or similar
- Docker + Docker Compose installed
- Git

## Deployment (3 Steps)

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd rivet
cp .env.example .env
```

### 2. Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
- Start all Docker services
- Load Ollama models (~10 min)
- Configure database
- Start workers

### 3. Verify

```bash
# Check services
cd infra && docker compose ps

# Monitor worker
docker compose logs -f rivet-worker

# Query database
docker exec -it infra-postgres-1 psql -U rivet -d rivet -c \
  "SELECT COUNT(*) FROM knowledge_atoms;"
```

## What's Running

- **Postgres** (port 5432): Vector database with pgvector
- **Redis** (port 6379): Job queue
- **Ollama** (port 11434): LLM + embeddings
- **Worker**: 24/7 job processor
- **Scheduler**: Hourly job enqueuer

## Monitoring

```bash
# Worker logs (real-time)
docker compose -f infra/docker-compose.yml logs -f rivet-worker

# Check queue depth
docker exec -it infra-redis-1 redis-cli LLEN kb_ingest_jobs

# View recent atoms
docker exec -it infra-postgres-1 psql -U rivet -d rivet -c \
  "SELECT title, atom_type FROM knowledge_atoms ORDER BY created_at DESC LIMIT 5;"
```

## Add Source Documents

Edit `langgraph_app/scheduler.py`:

```python
SEED_SOURCES = [
    "https://your-manual-1.pdf",
    "https://your-manual-2.html",
]
```

Then restart scheduler:
```bash
docker compose -f infra/docker-compose.yml restart rivet-scheduler
```

## Troubleshooting

**Worker not processing?**
```bash
# Manually enqueue test job
docker exec -it infra-redis-1 redis-cli RPUSH kb_ingest_jobs \
  "https://www.plcdev.com/book/export/html/1"
```

**Models not loaded?**
```bash
# Check models
docker exec infra-ollama-1 ollama list

# Reload if missing
docker exec infra-ollama-1 ollama pull mistral:latest
docker exec infra-ollama-1 ollama pull nomic-embed-text
```

## Next Steps

1. **Add real source URLs** to scheduler
2. **Monitor extraction quality** (first 50-100 atoms)
3. **Build search API** (query pgvector for similar atoms)
4. **Add observability** (Langfuse, Prometheus, etc.)

## Documentation

- **README.md**: Complete documentation
- **DEPLOYMENT_SUMMARY.md**: Architecture and details

## Support

Check logs: `docker compose -f infra/docker-compose.yml logs`

---

**Time to Deploy:** <10 minutes
**Time to First Atom:** ~2 minutes after models load
**Requires Manual Intervention:** No (fully automated)
