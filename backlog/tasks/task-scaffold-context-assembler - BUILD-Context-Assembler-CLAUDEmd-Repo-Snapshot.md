---
id: task-scaffold-context-assembler
title: 'BUILD: Context Assembler (CLAUDE.md + Repo Snapshot)'
status: To Do
assignee: []
created_date: 2025-12-18 06:24
labels:
- scaffold
- build
- context
- claude
dependencies:
- task-scaffold-backlog-parser
parent_task_id: task-scaffold-master
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Assemble context for Claude Code CLI execution.

The Context Assembler prepares the execution environment for each task:
- Reads CLAUDE.md system prompts
- Generates repo snapshot (file tree, recent commits, key files)
- Formats task specification (title, description, acceptance criteria)
- Creates execution prompt template
- Packages context for Claude Code CLI invocation

This ensures Claude has full context for autonomous task execution.

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ContextAssembler class with assemble_context(task_id) method
- [ ] #2 Reads CLAUDE.md and extracts system prompts
- [ ] #3 Generates file tree snapshot (max depth 3, excludes node_modules)
- [ ] #4 Extracts last 10 commits from git log
- [ ] #5 Formats task spec as markdown
- [ ] #6 Returns complete context string ready for Claude Code CLI

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.
<!-- SECTION:NOTES:END -->
