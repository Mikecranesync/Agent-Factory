---
id: task-46
title: 'REFACTOR Step 12: Wire Langfuse integration for LLM observability'
status: To Do
assignee: []
created_date: '2025-12-21 11:48'
labels:
  - refactor
  - observability
  - monitoring
  - week-5
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Complete Langfuse integration to track all LLM calls in production.

**Actions**:
1. Complete `agent_factory/observability/langfuse_tracker.py`:
   - Initialize Langfuse client
   - Track every LLM call (model, prompt, response, latency, cost)
   - Link traces to user sessions
2. Add to `LLMRouter` as optional feature
3. Dashboard setup docs
4. Integration tests

**Risk**: Low (optional feature)
**Files Changed**: langfuse_tracker.py, router.py, docs/, tests/

**Reference**: docs/REFACTOR_PLAN.md Step 12
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Langfuse integration complete
- [ ] #2 All LLM calls tracked
- [ ] #3 Dashboard accessible
- [ ] #4 Tests pass: poetry run pytest tests/test_langfuse_integration.py
- [ ] #5 Traces visible in Langfuse UI
<!-- AC:END -->
