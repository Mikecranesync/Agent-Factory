---
id: task-60
title: 'TEST: Create integration tests for streaming support'
status: To Do
assignee: []
created_date: '2025-12-21 12:59'
labels:
  - test
  - llm
  - streaming
  - week-2
dependencies:
  - task-57
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create integration tests for streaming LLM responses with async generators.

**Context**: Part of REFACTOR Step 5 (streaming support). Need to validate streaming works with real LLM providers.

**Scope**:
- Test streaming with OpenAI (gpt-4o-mini)
- Test streaming with Anthropic (claude-3-haiku)
- Test streaming with Google (gemini-pro)
- Test fallback to batch mode when streaming unavailable
- Test token-by-token delivery
- Test error handling during streaming

**Files**:
- tests/test_streaming.py (create)
- agent_factory/llm/streaming.py (reference)

**Dependencies**:
- Blocked by: task-57 (streaming implementation must be complete first)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Integration tests exist at tests/test_streaming.py
- [ ] #2 Tests validate OpenAI streaming API
- [ ] #3 Tests validate Anthropic streaming API
- [ ] #4 Tests validate Google streaming API
- [ ] #5 Tests validate fallback to batch mode
- [ ] #6 Tests validate token-by-token delivery
- [ ] #7 Tests pass: poetry run pytest tests/test_streaming.py -v
- [ ] #8 Tests use mocked API calls (no real API costs)
<!-- AC:END -->
