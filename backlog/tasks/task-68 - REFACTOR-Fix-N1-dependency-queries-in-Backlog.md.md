---
id: task-68
title: 'REFACTOR: Fix N+1 dependency queries in Backlog.md'
status: To Do
assignee: []
created_date: '2025-12-21 13:01'
labels:
  - refactor
  - backlog
  - performance
  - n-plus-one
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Optimize dependency checking by batching MCP calls instead of 1 call per dependency.

**Context**: Current implementation makes 1 MCP call per dependency, causing slow performance with many dependencies.

**Problem** (from backlog_parser.py line ~100):
```python
for dep_id in task.dependencies:
    dep_task = mcp_backlog_task_view(dep_id)  # N+1 query!
    if dep_task.status != "Done":
        blocked = True
```

**Solution**:
- Batch dependency checks into single MCP call
- Use mcp_backlog_task_list with filter by IDs
- Cache results for 5-10 minutes
- Reduce MCP calls from N to 1

**Performance**:
- Before: 10 deps = 10 MCP calls (~500ms)
- After: 10 deps = 1 MCP call (~50ms)
- 10x speedup

**Files**:
- agent_factory/scaffold/backlog_parser.py (optimize)
- tests/test_backlog_parser_performance.py (benchmark)

**Dependencies**:
- None
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Dependency checking uses batched MCP call
- [ ] #2 Single mcp_backlog_task_list call for all dependencies
- [ ] #3 Performance improved 5-10x
- [ ] #4 Benchmark shows <100ms for 10 dependencies
- [ ] #5 Cache implemented (5-10 min TTL)
- [ ] #6 Tests pass: poetry run pytest tests/test_backlog_parser_performance.py -v
- [ ] #7 No regression in functionality (same results, faster)
<!-- AC:END -->
