---
id: task-41
title: 'REFACTOR Step 1: Remove dead files and cleanup root directory'
status: In Progress
assignee: []
created_date: '2025-12-21 11:48'
updated_date: '2025-12-21 11:53'
labels:
  - refactor
  - cleanup
  - week-1
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Clean up Agent-Factory root directory by removing dead files and archiving obsolete documentation.

**Actions**:
- Delete `Repos.jpg` (screenshot, not needed in git)
- Create `archive/deployment-guides/` directory
- Move old deployment guides to archive:
  - `Prompt telegram.md` → `archive/deployment-guides/`
  - `codebase fixer.md` → `archive/deployment-guides/`

**Risk**: None (just moving/deleting)
**Files Changed**: ~5 files

**Reference**: docs/REFACTOR_PLAN.md Step 1
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Repos.jpg deleted
- [ ] #2 archive/deployment-guides/ directory created
- [ ] #3 Old guides moved to archive
- [ ] #4 App still runs: poetry run python agent_factory/examples/demo.py
<!-- AC:END -->
