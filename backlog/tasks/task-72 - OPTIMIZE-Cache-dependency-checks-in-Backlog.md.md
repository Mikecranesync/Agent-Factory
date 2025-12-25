---
id: task-72
title: 'OPTIMIZE: Cache dependency checks in Backlog.md'
status: To Do
assignee: []
created_date: '2025-12-21 13:02'
labels:
  - optimize
  - backlog
  - cache
  - performance
dependencies:
  - task-68
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add LRU cache for dependency status checks with 5-10 minute TTL to reduce MCP calls.

**Context**: After fixing N+1 queries (task-68), further optimize with caching.

**Implementation**:
- Use functools.lru_cache or custom cache
- Cache key: set of dependency IDs
- Cache value: list of (task_id, status) tuples
- TTL: 5-10 minutes (configurable)
- Invalidate on task status updates

**Performance impact**:
- First call: 1 MCP batch query (~50ms)
- Subsequent calls (cached): 0 MCP calls (~1ms)
- 50x speedup for repeated checks

**Files**:
- agent_factory/scaffold/dependency_cache.py (create)
- agent_factory/scaffold/backlog_parser.py (integrate cache)
- tests/test_dependency_cache.py (create tests)

**Dependencies**:
- Blocked by: task-68 (N+1 fix must be done first)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Cache implemented at agent_factory/scaffold/dependency_cache.py
- [ ] #2 LRU cache with TTL (5-10 minutes)
- [ ] #3 Cache integrated into backlog_parser.py
- [ ] #4 Cache invalidated on status updates
- [ ] #5 Performance improved 10-50x for repeated checks
- [ ] #6 Tests validate cache hit/miss behavior
- [ ] #7 Tests pass: poetry run pytest tests/test_dependency_cache.py -v
- [ ] #8 Cache statistics logged (hit rate, size)
<!-- AC:END -->
