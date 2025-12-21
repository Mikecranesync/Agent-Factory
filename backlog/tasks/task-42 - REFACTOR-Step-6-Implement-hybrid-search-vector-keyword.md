---
id: task-42
title: 'REFACTOR Step 6: Implement hybrid search (vector + keyword)'
status: To Do
assignee: []
created_date: '2025-12-21 11:48'
labels:
  - refactor
  - memory
  - search
  - week-2
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Improve retrieval accuracy by combining pgvector semantic search with PostgreSQL full-text search.

**Actions**:
1. Implement `HybridSearcher` in `agent_factory/memory/hybrid_search.py`:
   - Combine vector + full-text search
   - Weighted scoring: 70% vector, 30% keyword (configurable)
   - Reranking logic
2. Add to `PostgresMemoryStorage` as optional feature
3. Benchmark vs pure vector search
4. Integration tests

**Risk**: Medium (database queries, performance)
**Files Changed**: hybrid_search.py, storage.py, benchmarks/, tests/

**Reference**: docs/REFACTOR_PLAN.md Step 6
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 HybridSearcher implemented
- [ ] #2 Integrated into PostgresMemoryStorage
- [ ] #3 Benchmark shows improvement
- [ ] #4 Tests pass: poetry run pytest tests/test_hybrid_search.py
- [ ] #5 Benchmark runs: poetry run python benchmarks/search_comparison.py
<!-- AC:END -->
