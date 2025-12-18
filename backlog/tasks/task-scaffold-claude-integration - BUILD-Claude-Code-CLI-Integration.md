---
id: task-scaffold-claude-integration
title: 'BUILD: Claude Code CLI Integration'
status: To Do
assignee: []
created_date: 2025-12-18 06:24
labels:
- scaffold
- build
- claude
- execution
dependencies:
- task-scaffold-context-assembler
- task-scaffold-git-worktree-manager
parent_task_id: task-scaffold-master
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Execute tasks via Claude Code CLI with full context.

The Claude Executor invokes Claude Code CLI in isolated worktrees:
- Prepares execution prompt (context + task spec)
- Invokes Claude Code CLI with --non-interactive flag
- Captures output (stdout, stderr, exit code)
- Parses results (success/failure, files changed, tests passed)
- Returns execution summary

Uses existing Claude Code CLI installation (assumes in PATH).

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ClaudeExecutor class with execute_task(task_id, worktree_path) method
- [ ] #2 Formats execution prompt using ContextAssembler
- [ ] #3 Invokes: claude-code --non-interactive --prompt '{prompt}' in worktree
- [ ] #4 Captures stdout, stderr, exit code
- [ ] #5 Parses output for success indicators (commit created, tests passed)
- [ ] #6 Returns ExecutionResult(success, files_changed, output, error)

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.
<!-- SECTION:NOTES:END -->
