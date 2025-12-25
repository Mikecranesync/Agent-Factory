---
id: task-67
title: 'REFACTOR: Add task validation layer to Backlog.md'
status: To Do
assignee: []
created_date: '2025-12-21 13:01'
labels:
  - refactor
  - backlog
  - reliability
  - validation
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement schema validation and state machine for task lifecycle management.

**Context**: No validation currently exists for task state transitions or data integrity.

**Problems**:
- Tasks can skip states (To Do → Done without In Progress)
- Invalid status values accepted
- Missing required fields not caught
- Dependency cycles not detected

**Solution**:
- Add Pydantic schema for task validation
- Implement state machine (To Do → In Progress → Done)
- Validate transitions (block invalid state changes)
- Validate dependencies (detect cycles)
- Validate required fields (title, status, priority)

**Files**:
- agent_factory/scaffold/task_validator.py (create)
- agent_factory/scaffold/backlog_parser.py (integrate validation)
- tests/test_task_validator.py (create tests)

**Dependencies**:
- None
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Task validator exists at agent_factory/scaffold/task_validator.py
- [ ] #2 Pydantic schema validates all task fields
- [ ] #3 State machine enforces valid transitions
- [ ] #4 Dependency cycle detection working
- [ ] #5 Invalid transitions blocked (e.g., To Do → Done)
- [ ] #6 Integration with backlog_parser.py complete
- [ ] #7 Tests pass: poetry run pytest tests/test_task_validator.py -v
- [ ] #8 Validation errors provide clear messages
<!-- AC:END -->
