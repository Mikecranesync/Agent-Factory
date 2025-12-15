# VPS KB Factory - Credentials Setup

**⚠️ SECURITY:** Do NOT commit these credentials to Git!

## Environment Variables

Add these to your local `.env` file (already in `.gitignore`):

```bash
# ============================================================================
# VPS KB FACTORY DATABASE (Hostinger VPS - 72.60.175.144)
# ============================================================================
# PostgreSQL + pgvector for industrial knowledge base
VPS_KB_HOST=72.60.175.144
VPS_KB_PORT=5432
VPS_KB_USER=rivet
VPS_KB_PASSWORD=rivet_factory_2025!
VPS_KB_DATABASE=rivet
```

## Usage in Code

```python
from agents.content.scriptwriter_agent import ScriptwriterAgent

agent = ScriptwriterAgent()

# Query VPS for PLC atoms (keyword search)
atoms = agent.query_vps_atoms("ControlLogix", limit=5)

# Query VPS for semantic search (pgvector)
atoms = agent.query_vps_atoms_semantic("How to troubleshoot motor overload", limit=5)

# Generate script from atoms
script = agent.generate_script("Introduction to ControlLogix", atoms)
print(script['full_script'])
```

## Production Security

**Before deploying to production:**

1. **Rotate password** - Change from default `rivet_factory_2025!`
2. **Use secrets management** - Store in environment-specific secrets (not .env)
3. **Enable SSL** - Configure PostgreSQL SSL connections
4. **Firewall rules** - Restrict access to VPS IP ranges
5. **Audit logs** - Enable PostgreSQL query logging

## VPS Access

**SSH:** `root@72.60.175.144`
**Services:** Docker Compose running:
- PostgreSQL 16 + pgvector
- Ollama (DeepSeek 1.5B, nomic-embed-text)
- Redis
- LangGraph worker
- Scheduler

**Check status:**
```bash
ssh root@72.60.175.144
cd /opt/rivet/infra
docker-compose ps
```

## Database Schema

**Table:** `knowledge_atoms`
- **Rows:** 1,964+ validated maintenance atoms
- **Columns:** 20+ fields (atom_type, vendor, product, title, content, embedding, etc.)
- **Indexes:** pgvector for semantic search

**Query atom count:**
```bash
ssh root@72.60.175.144
docker exec -it infra-postgres-1 psql -U rivet -d rivet -c "SELECT COUNT(*) FROM knowledge_atoms;"
```

## Troubleshooting

**Connection refused:**
```bash
# Check VPS firewall
ssh root@72.60.175.144
sudo ufw status
sudo ufw allow 5432/tcp
```

**Slow queries:**
```bash
# Check PostgreSQL performance
docker exec -it infra-postgres-1 psql -U rivet -d rivet
SELECT * FROM pg_stat_activity WHERE state != 'idle';
```

**Ollama not responding:**
```bash
docker logs infra-ollama-1
docker restart infra-ollama-1
```

---

**📅 Last Updated:** 2025-12-15
**🔐 Security Level:** High - Production credentials, rotate regularly
