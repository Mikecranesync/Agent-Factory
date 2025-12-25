---
id: task-66
title: 'REFACTOR: Implement MCP fallback mode for Backlog.md'
status: To Do
assignee: []
created_date: '2025-12-21 13:00'
labels:
  - refactor
  - backlog
  - reliability
  - mcp-fallback
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add file-based task parsing fallback when MCP server is unavailable to prevent silent failures.

**Context**: Current implementation silently returns empty list if MCP unavailable. Need robust fallback.

**Problem**: 
- agent_factory/scaffold/backlog_parser.py returns [] if MCP tools fail
- No error logging when MCP unavailable
- Hard to debug MCP connection issues

**Solution**:
- Implement direct file parsing as fallback
- Read backlog/tasks/*.md files directly
- Parse YAML frontmatter + markdown
- Match same TaskSpec dataclass structure
- Log warning when using fallback mode

**Files**:
- agent_factory/scaffold/backlog_parser.py (add fallback logic)
- tests/test_backlog_parser.py (test fallback mode)

**Dependencies**:
- None
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Fallback mode implemented in backlog_parser.py
- [ ] #2 Fallback reads task files directly from backlog/tasks/
- [ ] #3 Fallback parses YAML frontmatter correctly
- [ ] #4 Fallback returns same TaskSpec structure as MCP
- [ ] #5 Warning logged when MCP unavailable: 'Using file-based fallback'
- [ ] #6 Tests validate fallback mode works
- [ ] #7 Tests pass: poetry run pytest tests/test_backlog_parser.py -v
- [ ] #8 No silent failures (always returns tasks or raises error)
<!-- AC:END -->
