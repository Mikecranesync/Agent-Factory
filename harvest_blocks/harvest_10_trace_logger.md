# HARVEST BLOCK 10: Trace Logger

**Priority**: HIGH - Independent (parallel with HARVEST 8-9)
**Size**: 11.6KB (314 lines)
**Source**: `agent_factory/core/trace_logger.py`
**Target**: `rivet/core/trace_logger.py`

## Quick Implementation

1. Copy source file: `cp agent_factory/core/trace_logger.py rivet/core/trace_logger.py`
2. No dependencies needed (uses stdlib only)
3. Validate: `python -c "from rivet.core.trace_logger import RequestTrace; trace = RequestTrace('test', '123'); trace.event('TEST'); print('OK')"`

## Key Features

```python
from rivet.core.trace_logger import RequestTrace

# Trace full request lifecycle
with RequestTrace("photo", user_id="123", username="alice", content="VFD fault") as trace:
    trace.event("OCR_START")
    # ... OCR processing ...
    trace.timing("ocr_ms", 850)
    
    trace.decision(
        decision_point="routing",
        outcome="route_b",
        reasoning="Detected manufacturer: Siemens",
        confidence=0.95
    )
    
    # ... SME processing ...
    trace.timing("sme_ms", 1200)
    
    # Auto-generates summary and admin message
    summary = trace.summary()
```

## Logging Outputs

- **JSONL Files**: `logs/traces.jsonl`, `logs/errors.jsonl`, `logs/metrics.jsonl`
- **Admin Telegram**: Formatted trace messages with timing/routing/errors

## Enhanced Trace Data

- `trace.decision()` - Routing decision points
- `trace.agent_reasoning()` - Agent thought process
- `trace.research_pipeline_status()` - Research pipeline status
- `trace.langgraph_execution()` - LangGraph workflow trace
- `trace.kb_retrieval()` - KB atom retrieval details

## What This Enables

- Production observability (JSONL logs)
- Admin Telegram notifications
- Performance monitoring (timing tracking)
- Error isolation for quick triage
- Request lifecycle tracing (start → decisions → completion)

SEE FULL SOURCE: `agent_factory/core/trace_logger.py` (314 lines - copy as-is)
