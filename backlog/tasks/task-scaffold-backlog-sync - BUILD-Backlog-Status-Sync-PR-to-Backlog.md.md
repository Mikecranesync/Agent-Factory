---
id: task-scaffold-backlog-sync
title: 'BUILD: Backlog Status Sync (PR to Backlog.md)'
status: To Do
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-20 23:54'
labels:
  - scaffold
  - build
  - backlog
  - sync
dependencies:
  - task-scaffold-pr-creation
parent_task_id: task-scaffold-master
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Auto-update Backlog.md task status after PR creation.

The Status Syncer updates task metadata:
- Marks task as In Progress when execution starts
- Marks task as Done when PR is created (pending human review)
- Adds PR URL to task notes
- Syncs to TASK.md via sync_tasks.py

Uses backlog task edit MCP tool for updates.

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 StatusSyncer class with sync_status(task_id, new_status, pr_url) method
- [ ] #2 Updates status: backlog task edit {id} --status '{status}'
- [ ] #3 Adds PR URL to notes: backlog task edit {id} --notes-append 'PR: {url}'
- [ ] #4 Calls sync_tasks.py to update TASK.md
- [ ] #5 Handles errors gracefully (logs warning if sync fails)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.
<!-- SECTION:NOTES:END -->
