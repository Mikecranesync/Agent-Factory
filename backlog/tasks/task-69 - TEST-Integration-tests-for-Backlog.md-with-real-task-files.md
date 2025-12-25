---
id: task-69
title: 'TEST: Integration tests for Backlog.md with real task files'
status: To Do
assignee: []
created_date: '2025-12-21 13:01'
labels:
  - test
  - backlog
  - integration
  - reliability
dependencies:
  - task-66
  - task-67
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create integration tests using real task files from backlog/tasks/ instead of mocks.

**Context**: Current tests use mocked MCP responses. Need tests with real task file parsing.

**Test scenarios**:
- Parse real task files with various formats
- Test dependency resolution with real tasks
- Test status filtering (To Do, In Progress, Done)
- Test task updates and state transitions
- Test error handling with malformed files
- Test fallback mode (when MCP unavailable)
- Test performance with 100+ task files

**Files**:
- tests/integration/test_backlog_real_files.py (create)
- backlog/tasks/*.md (use as test fixtures)

**Dependencies**:
- Blocked by: task-66 (MCP fallback mode)
- Blocked by: task-67 (validation layer)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Integration tests exist at tests/integration/test_backlog_real_files.py
- [ ] #2 Tests use real task files from backlog/tasks/
- [ ] #3 Tests validate task parsing accuracy
- [ ] #4 Tests validate dependency resolution
- [ ] #5 Tests validate status filtering
- [ ] #6 Tests validate fallback mode
- [ ] #7 Tests pass: poetry run pytest tests/integration/test_backlog_real_files.py -v
- [ ] #8 Performance test with 100+ tasks (<1 second)
<!-- AC:END -->
