---
id: task-56
title: 'REFACTOR Step 4: Implement LRU cache for LLM responses'
status: Done
assignee: []
created_date: '2025-12-21 12:29'
updated_date: '2025-12-21 13:08'
labels:
  - refactor
  - performance
  - week-2
  - llm
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Reduce repeat API calls and save costs with response caching.

**Actions**:
1. In `agent_factory/llm/cache.py`, implement `LRUCache` class:
   - Use `functools.lru_cache` or custom implementation
   - Hash prompt + model → cache key
   - TTL: 1 hour (configurable)
   - Max size: 1000 entries
2. Add cache to `LLMRouter.route()` method
3. Add cache statistics method (`get_hit_rate()`)
4. Write unit tests for cache hit/miss/expiry

**Risk**: Low (optional feature, doesn't break existing)
**Files Changed**: cache.py, router.py, tests/test_llm_cache.py

**Reference**: docs/REFACTOR_PLAN.md Step 4
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Implemented LRUCache class in cache.py
- [ ] #2 Integrated cache into LLMRouter.route()
- [ ] #3 Added cache hit rate tracking
- [ ] #4 Wrote tests: poetry run pytest tests/test_llm_cache.py
- [ ] #5 Verified cache works: poetry run python examples/llm_router_demo.py --with-cache
<!-- AC:END -->
