---
id: task-55
title: 'REFACTOR Step 2: Update LLM model pricing for Q1 2025'
status: Done
assignee: []
created_date: '2025-12-21 12:29'
updated_date: '2025-12-21 12:35'
labels:
  - refactor
  - pricing
  - week-1
  - llm
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure cost optimization uses current prices from OpenAI/Anthropic/Google.

**Actions**:
- Open `agent_factory/llm/config.py`
- Verify pricing for each model (check official pricing pages)
- Update `MODEL_PRICING` dict if changed
- Update `last_verified_date` comment
- Re-run cost optimization tests to verify savings still accurate

**Risk**: Low (just data update)
**Files Changed**: `agent_factory/llm/config.py`

**Reference**: docs/REFACTOR_PLAN.md Step 2
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Verified all model pricing against official sources (OpenAI, Anthropic, Google)
- [x] #2 Updated MODEL_PRICING dict with Q1 2025 prices
- [x] #3 Updated last_verified_date comment
- [x] #4 Ran: poetry run pytest tests/test_llm_router.py -k pricing
<!-- AC:END -->
