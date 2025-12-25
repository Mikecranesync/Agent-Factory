---
id: task-81
title: 'BUILD: Multi-app context synchronization in SettingsService'
status: To Do
assignee: []
created_date: '2025-12-21 13:04'
labels:
  - build
  - pai-config
  - context
  - settings
  - week-4
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend SettingsService to synchronize context across multiple agent applications (Friday, RIVET, PLC Tutor).

**Context**: pai-config-windows allows cross-app context sharing. Need same capability in Agent-Factory for multi-app coordination.

**Implementation**:
- Shared context storage (Redis or database)
- Context versioning (track changes, rollback)
- Sync protocol (pub/sub for updates)
- Context scopes (global, app-specific, session-specific)
- Conflict resolution (last-write-wins or merge strategies)
- Context expiry (TTL for session context)

**Use cases**:
- Friday voice assistant shares user preferences with RIVET
- RIVET shares KB status with PLC Tutor
- Cross-app analytics (user journey across apps)

**Files**:
- agent_factory/core/context_sync.py (create)
- agent_factory/core/settings_service.py (extend)
- tests/test_context_sync.py (create tests)

**Dependencies**:
- None (extends existing SettingsService)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Context sync implemented at agent_factory/core/context_sync.py
- [ ] #2 SettingsService extended with multi-app support
- [ ] #3 Shared context storage working (Redis or DB)
- [ ] #4 Context versioning implemented
- [ ] #5 Pub/sub sync protocol working
- [ ] #6 Context scopes supported (global, app, session)
- [ ] #7 Conflict resolution implemented
- [ ] #8 TTL expiry working
- [ ] #9 Tests pass: poetry run pytest tests/test_context_sync.py -v
<!-- AC:END -->
