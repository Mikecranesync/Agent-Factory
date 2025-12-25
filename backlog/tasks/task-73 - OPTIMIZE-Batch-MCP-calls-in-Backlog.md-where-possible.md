---
id: task-73
title: 'OPTIMIZE: Batch MCP calls in Backlog.md where possible'
status: To Do
assignee: []
created_date: '2025-12-21 13:02'
labels:
  - optimize
  - backlog
  - mcp
  - performance
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Identify and batch multiple MCP calls into single requests to reduce latency.

**Context**: Multiple sequential MCP calls can often be combined into batches.

**Opportunities**:
- Task list + dependency checks → single call with filter
- Multiple task views → batch retrieval
- Status updates → batch updates (if MCP supports)
- Search + filter → combined query

**Implementation**:
- Audit all MCP call sites in backlog_parser.py
- Group related calls
- Use MCP batch APIs where available
- Fallback to sequential if batch not supported

**Performance**:
- Before: 5 separate calls (~250ms)
- After: 1 batched call (~50ms)
- 5x speedup

**Files**:
- agent_factory/scaffold/backlog_parser.py (batch MCP calls)
- agent_factory/scaffold/mcp_batch_helper.py (create)
- tests/test_mcp_batching.py (create benchmark)

**Dependencies**:
- None
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 MCP calls batched where possible in backlog_parser.py
- [ ] #2 Batch helper implemented at agent_factory/scaffold/mcp_batch_helper.py
- [ ] #3 At least 3 batching opportunities identified and implemented
- [ ] #4 Performance improved 3-5x for typical operations
- [ ] #5 Fallback to sequential if batch unsupported
- [ ] #6 Tests validate batching works correctly
- [ ] #7 Tests pass: poetry run pytest tests/test_mcp_batching.py -v
- [ ] #8 Benchmark shows latency reduction
<!-- AC:END -->
