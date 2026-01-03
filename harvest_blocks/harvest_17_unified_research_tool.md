# HARVEST BLOCK 17: Unified Research Tool

**Priority**: MEDIUM
**Size**: ~20KB (550 lines)
**Source**: `agent_factory/tools/unified_research_tool.py`
**Target**: `rivet/tools/unified_research_tool.py`

---

## Overview

Multi-backend research aggregation with intelligent routing and automatic fallback - combines free, moderate, and premium research backends with smart selection based on task complexity and cost.

### What This Adds

- **3 backend support**: ResearchExecutorTool (free/Ollama), OpenManusResearchTool (self-hosted), ManusResearchTool (commercial API)
- **Smart routing**: Auto-selects best backend based on task complexity, priority, and cost threshold
- **Automatic fallback chain**: Primary → Fallback 1 → Fallback 2 → Error (3 retries per backend)
- **Cost tracking**: Tracks total spend across all backends with budget limits
- **Unified interface**: Same ResearchTask/ResearchResult models for all backends
- **Preference system**: prefer_free, cost_threshold_usd, enable_fallback flags
- **Graceful degradation**: Works with any single backend available

### Key Features

```python
from rivet.tools.unified_research_tool import UnifiedResearchTool, BackendType
from rivet.tools.research_executor import ResearchTask, ResearchPriority

# Initialize with auto-routing (default)
tool = UnifiedResearchTool(backend="auto")

# Or with cost preferences
tool = UnifiedResearchTool(
    backend="auto",
    prefer_free=True,  # Prefer free backends when possible
    cost_threshold_usd=0.50,  # Switch to paid if free > threshold
    enable_fallback=True,  # Auto-fallback on errors
    max_retries=3  # Retry attempts per backend
)

# Execute research task
task = ResearchTask(
    objective="Find Siemens S7-1200 fault F0003 troubleshooting steps",
    manufacturer="Siemens",
    equipment_type="PLC",
    model_number="S7-1200",
    priority=ResearchPriority.HIGH,
    timeout_minutes=10
)

result = await tool.execute(task)

# Result contains:
print(result.summary)  # Executive summary
print(result.detailed_findings)  # Full research report
print(result.sources)  # Citation list
print(result.estimated_cost_usd)  # Total cost
print(result.llm_provider)  # Which backend was used
```

---

## Smart Routing Logic

```python
# Backend selection based on task complexity and priority

# Simple tasks (single lookup) → ResearchExecutor (free)
if task.priority == ResearchPriority.LOW:
    backend = "research_executor"

# Moderate tasks (research) → ResearchExecutor or OpenManus
elif task.priority == ResearchPriority.MEDIUM:
    backend = "research_executor" if prefer_free else "openmanus"

# Complex tasks (multi-source report) → Manus API (most reliable)
elif task.priority == ResearchPriority.HIGH:
    backend = "manus_api"

# Critical priority → Manus API (guaranteed SLA)
elif task.priority == ResearchPriority.CRITICAL:
    backend = "manus_api"
```

---

## Automatic Fallback Chain

```python
# Fallback order (tries each backend in sequence)
fallback_chain = [
    "research_executor",  # Free (Ollama) - try first
    "openmanus",          # Self-hosted (Ollama/Claude)
    "manus_api"           # Commercial API (last resort)
]

# Execution with fallback:
for backend_name in fallback_chain:
    try:
        result = await backend.execute(task)
        if result.status == "completed":
            return result
    except Exception as e:
        logger.warning(f"{backend_name} failed: {e}, trying next backend...")

# If all backends fail → raise error
raise RuntimeError("All backends failed")
```

---

## Backend Comparison

| Backend | Cost | Reliability | Speed | Best For |
|---------|------|-------------|-------|----------|
| **ResearchExecutor** | Free (Ollama) or $0.03 (DeepSeek) | Medium | Fast (2-5 min) | Simple lookups, low priority |
| **OpenManus** | Free (Ollama) or $0.30 (Claude) | High | Medium (5-10 min) | Moderate research, balanced |
| **Manus API** | $0.50-2.00 per task | Very High | Slow (10-20 min) | Complex reports, critical priority |

---

## Cost Tracking

```python
# Track total spend
tool._total_cost_usd += result.estimated_cost_usd

# Get total cost
total_cost = tool._total_cost_usd
print(f"Total research cost: ${total_cost:.2f}")

# Cost threshold enforcement
if task.estimated_cost_usd > tool.preferences.cost_threshold_usd:
    # Switch to paid backend or abort
    logger.warning(f"Cost exceeds threshold: ${task.estimated_cost_usd} > ${cost_threshold_usd}")
```

---

## Dependencies

```bash
# Install research backends (install what's available)
poetry add langchain langchain-openai  # For ResearchExecutor

# Optional backends
# poetry add manus-sdk  # For ManusResearchTool (commercial)
# poetry add ollama  # For OpenManusResearchTool (self-hosted)
```

## Environment Variables

```bash
# Optional API keys (only if using commercial backends)
export MANUS_API_KEY=mns_...  # Manus Research API
export OPENAI_API_KEY=sk-...  # OpenAI (for embeddings)
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/tools/unified_research_tool.py rivet/tools/unified_research_tool.py`
2. Install dependencies: `poetry add langchain langchain-openai`
3. Validate: `python -c "from rivet.tools.unified_research_tool import UnifiedResearchTool; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.tools.unified_research_tool import UnifiedResearchTool, BackendType; print('OK')"

# Test execution (requires research_executor backend)
python -c "
import asyncio
from rivet.tools.unified_research_tool import UnifiedResearchTool
from rivet.tools.research_executor import ResearchTask

async def test():
    tool = UnifiedResearchTool(backend='research_executor')
    task = ResearchTask(objective='Test research task')
    result = await tool.execute(task)
    print(f'Status: {result.status}')

asyncio.run(test())
"
```

---

## Integration Notes

**RivetOrchestrator Integration** (Route C):
```python
# In Route C (no KB coverage) → trigger research
from rivet.tools.unified_research_tool import UnifiedResearchTool

tool = UnifiedResearchTool(
    backend="auto",
    prefer_free=True,  # Use free backends first
    cost_threshold_usd=1.00  # Max $1 per research task
)

# Build research task from gap
task = ResearchTask(
    objective=gap.description,
    manufacturer=gap.extracted_manufacturer,
    equipment_type=gap.extracted_equipment_type,
    priority=ResearchPriority.HIGH
)

# Execute with automatic fallback
result = await tool.execute(task)

# Parse results into knowledge atoms
atoms = parse_research_result(result)
```

**Backend Selection Strategy**:
- **Low priority** → ResearchExecutor (free, fast)
- **Medium priority** → ResearchExecutor or OpenManus (balanced)
- **High priority** → Manus API (reliable, premium)
- **Critical priority** → Manus API only (guaranteed SLA)

---

## What This Enables

- ✅ Multi-backend research (3 backends with different cost/reliability tradeoffs)
- ✅ Smart routing (auto-selects best backend based on task requirements)
- ✅ Automatic fallback (tries multiple backends if primary fails)
- ✅ Cost optimization (prefer free backends, switch to paid only when needed)
- ✅ Unified interface (same ResearchTask/ResearchResult models)
- ✅ Budget management (cost threshold enforcement)
- ✅ Graceful degradation (works with any single backend available)

---

## Next Steps

After implementing HARVEST 17, proceed to **HARVEST 18: Conversation Manager** for multi-turn conversation state management.

SEE FULL SOURCE: `agent_factory/tools/unified_research_tool.py` (550 lines - copy as-is)
