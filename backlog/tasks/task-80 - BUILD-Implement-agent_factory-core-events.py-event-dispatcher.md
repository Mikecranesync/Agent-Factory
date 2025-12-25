---
id: task-80
title: 'BUILD: Implement agent_factory/core/events.py (event dispatcher)'
status: To Do
assignee: []
created_date: '2025-12-21 13:04'
labels:
  - build
  - pai-config
  - events
  - core
  - week-3
dependencies:
  - task-78
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement event dispatcher/pub-sub system for agent communication based on pai-config patterns.

**Context**: Complement hooks.py with pub-sub event system for loose coupling between components.

**Implementation**:
- EventDispatcher class (publish, subscribe, unsubscribe)
- Topic-based routing (wildcard support: agent.*, *.created)
- Event payload (typed data with Pydantic)
- Async event handlers
- Event filtering (by priority, source, etc.)
- Event history/logging
- Dead letter queue for failed events

**API design**:
```python
from agent_factory.core.events import EventDispatcher, Event

dispatcher = EventDispatcher()

@dispatcher.subscribe('agent.created')
def handle_agent_created(event: Event):
    print(f"New agent: {event.payload.agent_name}")

dispatcher.publish('agent.created', payload={"agent_name": "ResearchAgent"})
```

**Files**:
- agent_factory/core/events.py (create implementation)
- tests/test_events.py (create tests)
- examples/events_demo.py (create example)

**Dependencies**:
- Blocked by: task-78 (pattern analysis)
- Related to: task-79 (hooks system)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Event dispatcher implemented at agent_factory/core/events.py
- [ ] #2 EventDispatcher class working
- [ ] #3 Topic-based routing with wildcards
- [ ] #4 Async event handlers supported
- [ ] #5 Event filtering working
- [ ] #6 Event history/logging implemented
- [ ] #7 Dead letter queue for failed events
- [ ] #8 Tests pass: poetry run pytest tests/test_events.py -v
- [ ] #9 Example demonstrates pub/sub pattern
<!-- AC:END -->
