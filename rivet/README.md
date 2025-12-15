# Rivet Industrial - Knowledge Base Factory V1

**24/7 cloud pipeline for ingesting industrial documentation into structured knowledge base**

Built with LangGraph, Ollama (open-source LLMs), PostgreSQL + pgvector, and Docker.

---

## Architecture

**Single VPS deployment:**
- **PostgreSQL 16** with pgvector extension - stores knowledge atoms with semantic embeddings
- **Redis** - job queue for ingestion tasks
- **Ollama** - hosts open-source LLM (DeepSeek 1.5B) and embedding model (nomic-embed-text)
- **Worker** - processes jobs from queue using LangGraph workflow
- **Scheduler** - enqueues source URLs periodically

**Workflow:**
```
Discovery → Downloader → Parser → Critic → Indexer
    ↓           ↓           ↓         ↓        ↓
   URLs     Extract      LLM     Validate  DB+Vector
            Text       Extract             Index
```

---

## Quick Start (VPS Deployment)

### Prerequisites
- VPS with 8 vCPU, 32 GB RAM, 300+ GB SSD
- Ubuntu 22.04 or later
- Docker and Docker Compose installed
- Git installed

### Step 1: Install Dependencies (if not already installed)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y
```

### Step 2: Clone Repository

```bash
# Clone to VPS
git clone <YOUR_REPO_URL> rivet
cd rivet
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (optional - defaults work for local testing)
nano .env
```

**Important:** In production, change `POSTGRES_PASSWORD` to a strong password!

### Step 4: Start Services

```bash
cd infra
docker-compose up -d
```

This will:
1. Start PostgreSQL with pgvector extension
2. Create database schema (knowledge_atoms table)
3. Start Redis
4. Start Ollama
5. Build and start worker and scheduler

### Step 5: Download Ollama Models

```bash
# Exec into Ollama container
docker exec -it infra-ollama-1 bash

# Pull models (this will take 5-10 minutes)
ollama pull deepseek-r1:1.5b
ollama pull nomic-embed-text

# Exit container
exit
```

### Step 6: Verify Services

```bash
# Check all services are running
docker-compose ps

# Should show:
# - postgres (healthy)
# - redis (healthy)
# - ollama (running)
# - rivet-worker (running)
# - rivet-scheduler (running)

# View worker logs
docker-compose logs -f rivet-worker

# View scheduler logs
docker-compose logs -f rivet-scheduler
```

### Step 7: Monitor First Ingestion

The scheduler will automatically enqueue jobs every hour. To see immediate results:

```bash
# Watch worker logs
docker-compose logs -f rivet-worker

# In another terminal, check database
docker exec -it infra-postgres-1 psql -U rivet -d rivet

# Query atoms
SELECT atom_id, title, atom_type FROM knowledge_atoms LIMIT 10;
\q
```

---

## Manual Testing (CLI)

To test a single document without waiting for scheduler:

```bash
# Build CLI image
docker-compose build rivet-worker

# Run single job
docker-compose run --rm rivet-worker python -m langgraph_app.cli \
  "https://example.com/manual.pdf"
```

---

## Configuration

All configuration is in `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `rivet` | Database name |
| `POSTGRES_USER` | `rivet` | Database user |
| `POSTGRES_PASSWORD` | `change_me` | **Change in production!** |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_LLM_MODEL` | `deepseek-r1:1.5b` | LLM for extraction |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `BATCH_SIZE` | `10` | Atoms per batch |
| `MAX_RETRIES` | `3` | Max job retries |
| `TIMEOUT_SECONDS` | `300` | Job timeout |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Adding Source Documents

### Method 1: Edit Scheduler (Permanent)

Edit `langgraph_app/scheduler.py`:

```python
sources = [
    "https://your-manual-1.pdf",
    "https://your-manual-2.pdf",
]
```

Rebuild and restart:
```bash
docker-compose build rivet-scheduler
docker-compose restart rivet-scheduler
```

### Method 2: Redis CLI (One-time)

```bash
# Exec into Redis
docker exec -it infra-redis-1 redis-cli

# Add job to queue
RPUSH kb_ingest_jobs "https://your-manual.pdf"

# Check queue length
LLEN kb_ingest_jobs

# Exit
exit
```

---

## Database Schema

**knowledge_atoms** table:

```sql
CREATE TABLE knowledge_atoms (
    atom_id SERIAL PRIMARY KEY,
    atom_type VARCHAR(50),  -- fault, pattern, concept, procedure
    vendor VARCHAR(100),
    product VARCHAR(100),
    title VARCHAR(500),
    summary TEXT,
    content TEXT,

    -- Fault fields
    code VARCHAR(50),
    symptoms TEXT[],
    causes TEXT[],
    fixes TEXT[],

    -- Pattern fields
    pattern_type VARCHAR(100),
    prerequisites TEXT[],
    steps TEXT[],

    -- Metadata
    keywords TEXT[],
    difficulty VARCHAR(20),
    source_url TEXT,

    -- Vector embedding (768 dimensions)
    embedding vector(768),

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Indexes:**
- HNSW index on `embedding` for vector similarity search
- GIN indexes on `keywords` and full-text
- B-tree indexes on `atom_type`, `vendor`, `product`, `difficulty`

---

## Querying Knowledge Base

### Semantic Search (Vector Similarity)

```sql
-- Find atoms similar to query
WITH query_embedding AS (
    -- Note: In practice, generate embedding using Ollama API
    SELECT '[0.1, 0.2, ...]'::vector AS emb
)
SELECT
    title,
    atom_type,
    1 - (embedding <=> query_embedding.emb) AS similarity
FROM knowledge_atoms, query_embedding
WHERE embedding IS NOT NULL
ORDER BY embedding <=> query_embedding.emb
LIMIT 10;
```

### Full-Text Search

```sql
-- Search by keywords
SELECT title, summary
FROM knowledge_atoms
WHERE to_tsvector('english', title || ' ' || summary)
      @@ to_tsquery('english', 'motor & fault');
```

### Filter by Type/Vendor

```sql
-- Find all faults for Allen-Bradley
SELECT title, code, symptoms
FROM knowledge_atoms
WHERE atom_type = 'fault'
  AND vendor = 'allen_bradley';
```

---

## Monitoring

### Service Health

```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs -f rivet-worker
docker-compose logs -f rivet-scheduler

# Check resource usage
docker stats
```

### Database Metrics

```bash
# Connect to database
docker exec -it infra-postgres-1 psql -U rivet -d rivet

# Count atoms by type
SELECT atom_type, COUNT(*) FROM knowledge_atoms GROUP BY atom_type;

# Recent ingestions
SELECT source_url, COUNT(*) as atoms
FROM knowledge_atoms
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY source_url;

# Database size
SELECT pg_size_pretty(pg_database_size('rivet'));
```

### Redis Queue

```bash
# Connect to Redis
docker exec -it infra-redis-1 redis-cli

# Check queue length
LLEN kb_ingest_jobs

# Peek at next job
LINDEX kb_ingest_jobs 0
```

---

## Troubleshooting

### Worker not processing jobs

```bash
# Check worker logs
docker-compose logs rivet-worker

# Common issues:
# 1. Ollama models not pulled
docker exec -it infra-ollama-1 ollama list

# 2. Database connection failed
docker exec -it infra-postgres-1 pg_isready -U rivet

# 3. Redis connection failed
docker exec -it infra-redis-1 redis-cli ping
```

### Ollama out of memory

```bash
# Check model memory usage
docker stats infra-ollama-1

# Use smaller model
# Edit .env:
OLLAMA_LLM_MODEL=deepseek-r1:1.5b  # ~3GB RAM

# Or use Mistral
OLLAMA_LLM_MODEL=mistral:7b-instruct
```

### PDF extraction failing

Current implementation uses stub PDF extractor. To enable full PDF support:

1. Uncomment in `requirements.txt`:
```
PyPDF2>=3.0.0
pdfplumber>=0.10.0
```

2. Update `langgraph_app/nodes/downloader.py` to use real PDF library

3. Rebuild:
```bash
docker-compose build rivet-worker
docker-compose restart rivet-worker
```

---

## Scaling Up

### Horizontal Scaling (Multiple Workers)

```bash
# In docker-compose.yml, scale workers:
docker-compose up -d --scale rivet-worker=3
```

### Add GPU Support for Ollama

Edit `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Requires NVIDIA Docker runtime installed.

---

## Next Steps

**Short-term improvements:**
1. Add proper PDF extraction (PyPDF2/pdfplumber)
2. Add HTML scraping for web documentation
3. Implement retry logic for failed jobs
4. Add job status tracking in database
5. Build simple web UI for monitoring

**Medium-term features:**
1. Add Langfuse observability
2. Implement human-in-the-loop validation
3. Add A/B testing for extraction prompts
4. Build RAG API for querying knowledge base
5. Add automated source discovery (crawlers)

**Production hardening:**
1. Add authentication and authorization
2. Implement rate limiting
3. Add comprehensive error handling
4. Set up backup and disaster recovery
5. Add monitoring (Prometheus/Grafana)
6. Configure log aggregation (ELK stack)

---

## License

[Your License Here]

---

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.
