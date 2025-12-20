# VPS & Cloud Development Setup

## VPS KB Factory (Hostinger)

24/7 knowledge base ingestion pipeline running on Hostinger VPS.

**VPS:** `72.60.175.144`

**Services (Docker Compose):**
- `postgres` - PostgreSQL 16 + pgvector for semantic search
- `redis` - Job queue for ingestion URLs
- `ollama` - Local LLM (deepseek-r1:1.5b) + embeddings (nomic-embed-text)
- `rivet-worker` - LangGraph ingestion pipeline
- `rivet-scheduler` - Hourly job scheduling

**Query VPS from ScriptwriterAgent:**
```python
from agents.content.scriptwriter_agent import ScriptwriterAgent

agent = ScriptwriterAgent()

# Keyword search
atoms = agent.query_vps_atoms("ControlLogix", limit=5)

# Semantic search (uses Ollama embeddings)
atoms = agent.query_vps_atoms_semantic("How to troubleshoot motor faults", limit=5)

# Generate script from atoms
script = agent.generate_script("PLC Motor Control", atoms)
```

**VPS Management Commands:**
```bash
# SSH into VPS
ssh root@72.60.175.144

# Check services
cd /opt/rivet/infra && docker-compose ps

# View worker logs
docker logs infra_rivet-worker_1 --tail 50

# Add URL to ingest
docker exec infra_redis_1 redis-cli RPUSH kb_ingest_jobs "https://example.com/manual.pdf"

# Check atom count
docker exec infra_postgres_1 psql -U rivet -d rivet -c "SELECT COUNT(*) FROM knowledge_atoms;"
```

**Environment Variables (in .env):**
```
VPS_KB_HOST=72.60.175.144
VPS_KB_PORT=5432
VPS_KB_USER=rivet
VPS_KB_PASSWORD=rivet_factory_2025!
VPS_KB_DATABASE=rivet
```

**KB Ingestion Scripts:**
```powershell
# Push industrial PDFs to VPS (from PowerShell)
.\push_urls_to_vps.ps1

# Monitor ingestion progress
ssh root@72.60.175.144 "docker logs infra_rivet-worker_1 --tail 50"
```

**Source Files:**
- `scripts/kb_seed_urls.py` - 17 curated industrial PDF URLs (Rockwell, Siemens, Mitsubishi, Omron, Schneider)
- `scripts/push_urls_to_vps.py` - Python push script
- `scripts/monitor_vps_ingestion.py` - Python monitor script
- `push_urls_to_vps.ps1` - PowerShell push script (Windows)

---

## Cloud Dev Box Setup

**Remote development with Claude Code CLI on cloud VM**

### Quick Start

```bash
# SSH into cloud VM
ssh user@your-cloud-vm.com
cd ~/agent-factory

# One-time setup (first login)
./scripts/cloud-dev-box/setup-from-scratch.sh

# Launch Claude Code session
./scripts/cloud-dev-box/launch-claude.sh
```

### Daily Workflow

```bash
# 1. SSH into VM
ssh user@your-cloud-vm.com
cd ~/agent-factory

# 2. Check environment (optional)
./scripts/cloud-dev-box/check-prerequisites.sh

# 3. Launch Claude
./scripts/cloud-dev-box/launch-claude.sh

# 4. Work on tasks inside Claude session
> Read TASK.md
> What should I work on next?

# 5. Exit when done (Ctrl+D)
```

### Session Management

```bash
# Resume previous session
./scripts/cloud-dev-box/launch-claude.sh --resume

# List saved sessions
./scripts/cloud-dev-box/utils/session-manager.sh list

# Load specific session
./scripts/cloud-dev-box/utils/session-manager.sh resume feature-xyz
```

### Access from Mobile

**Termux (Android):**
```bash
pkg install openssh
ssh user@your-cloud-vm.com
cd ~/agent-factory && ./scripts/cloud-dev-box/launch-claude.sh
```

**JuiceSSH (Android):**
- Create connection: user@your-cloud-vm.com
- Save snippet: `cd ~/agent-factory && ./scripts/cloud-dev-box/launch-claude.sh`
- One-tap access!

**See:** `Guides for Users/deployment/CLOUD_DEV_BOX_GUIDE.md` for complete setup guide
