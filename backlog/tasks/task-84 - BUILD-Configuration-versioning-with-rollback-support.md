---
id: task-84
title: 'BUILD: Configuration versioning with rollback support'
status: To Do
assignee: []
created_date: '2025-12-21 13:05'
labels:
  - build
  - pai-config
  - settings
  - versioning
  - ongoing
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add versioning and rollback capabilities to SettingsService for safe configuration changes.

**Context**: Enable safe configuration updates with ability to rollback bad changes.

**Implementation**:
- Configuration snapshots before changes
- Version history (store last N versions)
- Rollback to previous version
- Diff visualization (show what changed)
- Atomic updates (all-or-nothing)
- Validation before applying
- Audit log (who changed what, when)

**Use cases**:
- Rollback after bad LLM model change
- Revert database connection string
- Restore previous routing configuration
- Emergency rollback during incident

**API design**:
```python
from agent_factory.core.settings_service import settings

# Create snapshot before change
settings.snapshot("before-model-change")

# Make risky change
settings.set("DEFAULT_MODEL", "gpt-4o", category="llm")

# If problems occur, rollback
settings.rollback("before-model-change")

# Or rollback to previous version
settings.rollback_to_version(5)
```

**Files**:
- agent_factory/core/settings_versioning.py (create)
- agent_factory/core/settings_service.py (extend)
- tests/test_settings_versioning.py (create tests)

**Dependencies**:
- None (extends existing SettingsService)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Versioning implemented at agent_factory/core/settings_versioning.py
- [ ] #2 Snapshot creation working
- [ ] #3 Version history stored (last 10 versions)
- [ ] #4 Rollback to previous version working
- [ ] #5 Rollback to named snapshot working
- [ ] #6 Diff visualization implemented
- [ ] #7 Atomic updates working
- [ ] #8 Validation before applying changes
- [ ] #9 Audit log captured
- [ ] #10 Tests pass: poetry run pytest tests/test_settings_versioning.py -v
<!-- AC:END -->
