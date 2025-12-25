---
id: task-71
title: 'REFACTOR: Extend backlog/config.yml with SCAFFOLD settings'
status: To Do
assignee: []
created_date: '2025-12-21 13:02'
labels:
  - refactor
  - backlog
  - config
  - scaffold
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add SCAFFOLD-specific configuration options to backlog/config.yml for autonomous execution settings.

**Context**: Backlog.md config is minimal. Need to add SCAFFOLD executor settings for safety limits, MCP options, etc.

**New config sections**:
```yaml
scaffold:
  max_cost_per_task: 5.00  # USD
  max_execution_time: 1800  # 30 minutes
  max_retries: 3
  enable_pr_creation: true
  require_approval: false
  
mcp:
  fallback_enabled: true
  cache_ttl: 300  # 5 minutes
  batch_size: 50
  timeout: 30  # seconds
  
validation:
  enforce_state_machine: true
  detect_dependency_cycles: true
  require_acceptance_criteria: false
```

**Files**:
- backlog/config.yml (extend with new sections)
- agent_factory/scaffold/config_loader.py (create loader)
- tests/test_config_loader.py (create tests)

**Dependencies**:
- None
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 backlog/config.yml extended with scaffold, mcp, validation sections
- [ ] #2 Config loader implemented at agent_factory/scaffold/config_loader.py
- [ ] #3 Config loaded on startup
- [ ] #4 Default values provided if config missing
- [ ] #5 Environment variable overrides supported
- [ ] #6 Tests validate config parsing
- [ ] #7 Tests pass: poetry run pytest tests/test_config_loader.py -v
- [ ] #8 Documentation added to backlog/README.md
<!-- AC:END -->
