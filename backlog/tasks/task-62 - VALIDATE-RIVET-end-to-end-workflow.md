---
id: task-62
title: 'VALIDATE: RIVET end-to-end workflow'
status: To Do
assignee: []
created_date: '2025-12-21 12:59'
labels:
  - test
  - rivet
  - e2e
  - week-3-4
  - production-blocker
dependencies:
  - task-44
  - task-61
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create end-to-end integration test for complete RIVET query workflow from Telegram input to answer delivery.

**Context**: Critical production blocker. Must validate entire pipeline works before RIVET production launch.

**Workflow to validate**:
1. User sends question via Telegram
2. Intent detector classifies query
3. Orchestrator routes to correct SME agent
4. SME agent searches KB (hybrid search)
5. RAG reranking improves results
6. SME generates answer with citations
7. Confidence scorer validates quality (>0.9)
8. Response returned to Telegram
9. Low confidence triggers human escalation

**Files**:
- tests/integration/test_rivet_end_to_end.py (create)
- agent_factory/rivet_pro/orchestrator.py (reference)
- agent_factory/integrations/telegram/ (reference)

**Dependencies**:
- Blocked by: task-44 (RAG reranking)
- Blocked by: task-61 (SME integration tests)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 E2E test exists at tests/integration/test_rivet_end_to_end.py
- [ ] #2 Test validates full Telegram → KB → Answer workflow
- [ ] #3 Test validates all 4 route types (A, B, C, D)
- [ ] #4 Test validates confidence scoring triggers
- [ ] #5 Test validates human escalation for low confidence (<0.9)
- [ ] #6 Test validates citation quality
- [ ] #7 Test passes: poetry run pytest tests/integration/test_rivet_end_to_end.py -v
- [ ] #8 Test uses real KB atoms and mocked Telegram API
<!-- AC:END -->
