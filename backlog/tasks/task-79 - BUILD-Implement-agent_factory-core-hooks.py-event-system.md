---
id: task-79
title: 'BUILD: Implement agent_factory/core/hooks.py (event system)'
status: To Do
assignee: []
created_date: '2025-12-21 13:04'
labels:
  - build
  - pai-config
  - hooks
  - core
  - week-3
dependencies:
  - task-78
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Python hook/event system based on pai-config patterns analysis.

**Context**: After studying pai-config patterns (task-78), implement the hook system in Python.

**Implementation**:
- HookManager class (register, unregister, execute hooks)
- Hook decorator (@hook decorator for functions)
- Hook lifecycle (before, after, on_error)
- Context object for passing data between hooks
- Priority-based execution ordering
- Async hook support (async/await)
- Error handling and recovery

**API design**:
```python
from agent_factory.core.hooks import HookManager, hook

manager = HookManager()

@manager.register('agent.created', priority=10)
def log_agent_creation(context):
    print(f"Agent created: {context.agent_name}")

@manager.register('agent.created', priority=20, async_hook=True)
async def notify_team(context):
    await send_slack_message(f"New agent: {context.agent_name}")
```

**Files**:
- agent_factory/core/hooks.py (create implementation)
- tests/test_hooks.py (create tests)
- examples/hooks_demo.py (create example)

**Dependencies**:
- Blocked by: task-78 (pattern analysis must be complete)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Hooks implementation complete at agent_factory/core/hooks.py
- [ ] #2 HookManager class implemented
- [ ] #3 Hook decorator working
- [ ] #4 Priority-based execution working
- [ ] #5 Async hooks supported
- [ ] #6 Context passing working
- [ ] #7 Error handling implemented
- [ ] #8 Tests pass: poetry run pytest tests/test_hooks.py -v
- [ ] #9 Example demonstrates all features
<!-- AC:END -->
