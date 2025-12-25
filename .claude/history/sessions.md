# Session History (UOCS - Use Of Claude Sessions)

**Tracks every Claude Code session for continuity and debugging**

---

## What is UOCS?

UOCS (Use Of Claude Sessions) is a pattern for tracking all Claude Code interactions:
- Session start/end timestamps
- Tasks worked on
- Files modified
- Context loaded (skills, products)
- Duration and productivity metrics

**Format**: Human-readable Markdown + machine-readable JSON (`.claude/history/sessions/*.json`)

---

## Session Log Format

Each session entry includes:
- **Timestamp**: ISO 8601 format
- **Session ID**: Unique identifier (ses_YYYY-MM-DD_HH-MM-SS)
- **Git Context**: Branch, commit hash
- **Tasks**: Tasks in progress during session
- **Files**: Files read/written
- **Duration**: Total session time
- **Metrics**: Tools used, cost, productivity

---

## Current Week Summary

**Week**: 2025-W51 (Dec 16-22, 2025)
- **Sessions**: 0 (will auto-update)
- **Total Time**: 0 minutes
- **Tasks Completed**: 0
- **Files Modified**: 0

---

## Recent Sessions

<!-- Sessions auto-logged by .claude/hooks/on_session_start.sh and on_session_end.sh -->

<!-- Example entry:
## 2025-12-22T16:45:30Z - Session Started
- **ID**: ses_2025-12-22_16-45-30
- **Branch**: feature-pai-hooks
- **Commit**: a1b2c3d4
- **Active Skill**: CORE
- **Product Focus**: platform

### Tasks in Progress
- task-55: Create PAI Hooks System
- task-56: Implement LRU cache for LLM responses

---

## 2025-12-22T17:30:15Z - Session Ended
- **ID**: ses_2025-12-22_16-45-30
- **Duration**: 45 minutes
- **Tasks Completed**: 1 (task-55)
- **Files Modified**: 7
  - .claude/hooks/README.md
  - .claude/hooks/on_session_start.sh
  - .claude/hooks/on_session_end.sh
  - .claude/hooks/config.yml
  - .claude/history/sessions.md
  - .gitignore
  - backlog.md

### Summary
- Created PAI Hooks System (7 files, 1,160+ lines)
- Implemented UOCS pattern with session tracking
- Added Windows integration (PowerShell registry sync)
- Updated .gitignore to exclude hook logs

---
-->

**Note**: Sessions are auto-logged. View JSON details in `.claude/history/sessions/*.json`
