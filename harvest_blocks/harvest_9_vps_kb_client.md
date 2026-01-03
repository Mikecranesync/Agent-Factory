# HARVEST BLOCK 9: VPS KB Client

**Priority**: HIGH - Independent (parallel with HARVEST 8)
**Size**: 14.5KB (422 lines)
**Source**: `agent_factory/rivet_pro/vps_kb_client.py`
**Target**: `rivet/integrations/vps_kb_client.py`

## Quick Implementation

1. Copy source file: `cp agent_factory/rivet_pro/vps_kb_client.py rivet/integrations/vps_kb_client.py`
2. Install: `poetry add psycopg2-binary requests`
3. Set env vars (see below)
4. Validate: `python -c "from rivet.integrations.vps_kb_client import VPSKBClient; client = VPSKBClient(); print(client.health_check())"`

## Environment Variables

```bash
VPS_KB_HOST=72.60.175.144
VPS_KB_PORT=5432
VPS_KB_USER=rivet
VPS_KB_PASSWORD=rivet_factory_2025!
VPS_KB_DATABASE=rivet
VPS_OLLAMA_URL=http://72.60.175.144:11434
```

## Key Features

```python
from rivet.integrations.vps_kb_client import VPSKBClient

client = VPSKBClient()

# Keyword search
atoms = client.query_atoms("motor overheating", limit=5)

# Equipment search
atoms = client.search_by_equipment(equipment_type="plc", manufacturer="allen_bradley")

# Semantic search (pgvector + Ollama)
atoms = client.query_atoms_semantic("How to troubleshoot ControlLogix faults", limit=5, similarity_threshold=0.7)

# Health check
health = client.health_check()
```

## What This Enables

- Direct VPS KB Factory access (no HTTP latency)
- Semantic search with pgvector embeddings
- Equipment-specific filtering
- Health monitoring with 1-minute cache
- Graceful degradation (semantic → keyword fallback)

SEE FULL SOURCE: `agent_factory/rivet_pro/vps_kb_client.py` (422 lines - copy as-is)
