# HARVEST BLOCK 11: Trace Persistence

**Priority**: HIGH
**Size**: 13.2KB (409 lines)
**Source**: `agent_factory/rivet_pro/trace_persistence.py`
**Target**: `rivet/rivet_pro/trace_persistence.py`

---

## Overview

Supabase persistence layer for AgentTrace data - enables production analytics, debugging, and cost tracking.

### What This Adds

- Single and batch trace insertion to Supabase
- Query traces by user, route, or agent
- Error trace debugging queries
- Slow query monitoring (>5sec threshold)
- Research trigger tracking (Route C analytics)
- Aggregated analytics with 7-day views
- Graceful degradation (no Supabase = no-op)

### Key Features

```python
from rivet.rivet_pro.trace_persistence import TracePersistence
from rivet.rivet_pro.models import AgentTrace

persistence = TracePersistence()

# Save single trace
trace = AgentTrace(...)
persistence.save_trace(trace, tokens_used=500, estimated_cost_usd=0.002)

# Save batch (faster for bulk)
traces_batch = [{"request_id": "...", "user_id": "..."}, ...]
persistence.save_traces_batch(traces_batch)

# Query user traces (last 10)
traces = persistence.get_user_traces(user_id="telegram_123", limit=10)

# Get analytics (7-day aggregated stats)
stats = persistence.get_analytics(days=7)
# Returns: {"total_requests": 1500, "total_cost_usd": 12.34, "total_errors": 5}

# Debug slow queries
slow = persistence.get_slow_queries(threshold_ms=5000, limit=10)

# Track research triggers (Route C)
research_traces = persistence.get_research_triggers(limit=10)
```

---

## Environment Variables

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/rivet_pro/trace_persistence.py rivet/rivet_pro/trace_persistence.py`
2. Install: `poetry add supabase`
3. Set environment variables (see above)
4. Validate: `python -c "from rivet.rivet_pro.trace_persistence import TracePersistence; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.rivet_pro.trace_persistence import TracePersistence; print('OK')"

# Test with credentials
python -c "
from rivet.rivet_pro.trace_persistence import TracePersistence
persistence = TracePersistence()
stats = persistence.get_analytics(days=7)
print(f'Stats: {stats}')
"
```

---

## Integration Notes

**Fire-and-Forget Pattern** (async logging):
```python
# In RivetOrchestrator
async def _persist_trace_async(self, trace: AgentTrace):
    """Save trace without blocking main response"""
    asyncio.create_task(self._save_trace_background(trace))

async def _save_trace_background(self, trace: AgentTrace):
    try:
        self.trace_persistence.save_trace(trace)
    except Exception as e:
        logger.error(f"Trace save failed: {e}")
```

**Query Methods**:
- `get_user_traces(user_id, limit, offset, start_date, end_date)` - User history with date filtering
- `get_traces_by_route(route, limit, days)` - Route statistics (A/B/C/D)
- `get_traces_by_agent(agent_id, limit, days)` - Agent performance metrics
- `get_error_traces(limit, days)` - Debug failed requests
- `get_slow_queries(threshold_ms, limit, days)` - Performance monitoring
- `get_research_triggers(limit, days)` - Track Route C invocations
- `get_analytics(days)` - Aggregated stats from `agent_traces_analytics` view
- `get_user_analytics(user_id)` - Per-user metrics

**Graceful Degradation**:
- If Supabase credentials missing → logs warning, returns empty results
- No exceptions bubble up to caller
- All methods return empty list/dict on failure

---

## What This Enables

- ✅ Production analytics dashboard (cost, latency, errors)
- ✅ User-specific request history
- ✅ Route performance comparison (A vs B vs C vs D)
- ✅ Agent performance benchmarking (Siemens vs Rockwell vs Generic)
- ✅ Debugging with error traces and slow query tracking
- ✅ Cost tracking per request (tokens + estimated USD)
- ✅ Research trigger monitoring (Route C invocation rate)
- ✅ Fire-and-forget async persistence (non-blocking)

---

## Next Steps

After implementing HARVEST 11, proceed to **HARVEST 12: Feedback Handler** for user feedback processing and quality loop.

SEE FULL SOURCE: `agent_factory/rivet_pro/trace_persistence.py` (409 lines - copy as-is)
