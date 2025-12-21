---
id: task-44
title: 'REFACTOR Step 10: Add RAG reranking to improve answer quality'
status: To Do
assignee: []
created_date: '2025-12-21 11:48'
labels:
  - refactor
  - rivet
  - rag
  - week-4
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement cross-encoder reranking to improve retrieval quality beyond pure vector search.

**Actions**:
1. Implement `Reranker` in `agent_factory/rivet_pro/rag/reranker.py`:
   - Cross-encoder model (ms-marco-MiniLM-L-6-v2)
   - Score query-document pairs
   - Rerank top-k candidates
2. Integrate into retrieval pipeline
3. Benchmark improvement
4. Add to RIVET orchestrator

**Risk**: Medium (ML model, inference time)
**Files Changed**: rag/reranker.py, benchmarks/, tests/

**Reference**: docs/REFACTOR_PLAN.md Step 10
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reranker implemented
- [ ] #2 Integrated into pipeline
- [ ] #3 Benchmark shows quality improvement
- [ ] #4 Tests pass: poetry run pytest tests/test_reranker.py
- [ ] #5 Latency acceptable (<500ms for reranking)
<!-- AC:END -->
