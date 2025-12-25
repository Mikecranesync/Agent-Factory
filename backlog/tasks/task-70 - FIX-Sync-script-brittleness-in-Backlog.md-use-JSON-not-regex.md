---
id: task-70
title: 'FIX: Sync script brittleness in Backlog.md (use JSON not regex)'
status: To Do
assignee: []
created_date: '2025-12-21 13:01'
labels:
  - fix
  - backlog
  - sync
  - reliability
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace regex-based sync script with JSON-based parsing for robustness.

**Context**: Current sync script uses regex to parse task files, which is fragile and error-prone.

**Problems** (scripts/backlog/sync_tasks.py):
- Regex breaks on multiline content
- Hard to maintain regex patterns
- Silent failures when parsing fails
- Doesn't validate JSON structure

**Solution**:
- Use frontmatter library to parse YAML
- Use json module for structured data
- Add proper error handling
- Validate parsed data before sync
- Log warnings for malformed files

**Files**:
- scripts/backlog/sync_tasks.py (rewrite parsing logic)
- tests/test_sync_script.py (create tests)

**Dependencies**:
- None
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sync script uses frontmatter library (not regex)
- [ ] #2 YAML parsing validates structure
- [ ] #3 JSON validation before sync
- [ ] #4 Proper error handling with logging
- [ ] #5 Handles multiline content correctly
- [ ] #6 No silent failures (logs all errors)
- [ ] #7 Tests pass: poetry run pytest tests/test_sync_script.py -v
- [ ] #8 Manual test: poetry run python scripts/backlog/sync_tasks.py
<!-- AC:END -->
