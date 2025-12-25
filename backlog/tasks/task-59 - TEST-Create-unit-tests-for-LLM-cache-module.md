---
id: task-59
title: 'TEST: Create unit tests for LLM cache module'
status: To Do
assignee: []
created_date: '2025-12-21 12:59'
labels:
  - test
  - llm
  - cache
  - week-2
dependencies:
  - task-56
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create comprehensive unit tests for the LRU cache implementation in agent_factory/llm/cache.py.

**Context**: Part of REFACTOR Step 4 (LLM caching). The cache module needs test coverage before integration.

**Scope**:
- Test cache hit/miss scenarios
- Test TTL expiration
- Test max size limits
- Test hash key generation
- Test thread safety

**Files**:
- tests/test_llm_cache.py (create)
- agent_factory/llm/cache.py (reference)

**Dependencies**: 
- Blocked by: task-56 (LRU cache implementation must be complete first)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Unit tests exist at tests/test_llm_cache.py
- [ ] #2 All cache methods have test coverage (hit, miss, expire, evict)
- [ ] #3 Tests validate TTL expiration logic
- [ ] #4 Tests validate max size eviction (LRU)
- [ ] #5 Tests pass: poetry run pytest tests/test_llm_cache.py -v
- [ ] #6 Code coverage >90% for cache.py
<!-- AC:END -->
