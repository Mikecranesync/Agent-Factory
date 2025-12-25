---
id: task-85
title: 'BUILD: Agent hook registration system (subscribe to events)'
status: To Do
assignee: []
created_date: '2025-12-21 13:05'
labels:
  - build
  - pai-config
  - hooks
  - agents
  - ongoing
dependencies:
  - task-79
  - task-80
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable agents to register hooks and subscribe to events for extensibility without modifying core code.

**Context**: Final piece of hook/event system. Allow agents to plug into lifecycle events.

**Implementation**:
- Agent registration API
- Automatic hook discovery (via decorators or registry)
- Hook categories (agent.created, agent.executing, agent.completed, agent.failed)
- Event subscription by agents
- Hook execution in agent context
- Security/sandboxing (prevent malicious hooks)

**Use cases**:
- Agent logs all invocations to database
- Agent sends metrics to monitoring service
- Agent validates inputs before execution
- Agent enriches outputs after execution
- Agent handles errors with custom recovery

**API design**:
```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.core.hooks import hook

class MyAgent:
    @hook('agent.before_execute')
    def validate_inputs(self, context):
        if not context.query:
            raise ValueError("Query cannot be empty")
    
    @hook('agent.after_execute')
    def log_results(self, context):
        logger.info(f"Agent {self.name} completed: {context.result}")

factory = AgentFactory()
agent = factory.create_agent("MyAgent", hooks_enabled=True)
```

**Files**:
- agent_factory/core/agent_hooks.py (create)
- agent_factory/core/agent_factory.py (integrate)
- tests/test_agent_hooks.py (create tests)
- examples/agent_hooks_demo.py (create example)

**Dependencies**:
- Blocked by: task-79 (hooks.py implementation)
- Blocked by: task-80 (events.py implementation)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Agent hook registration implemented at agent_factory/core/agent_hooks.py
- [ ] #2 Hook decorator working for agent methods
- [ ] #3 Automatic hook discovery working
- [ ] #4 All lifecycle hooks supported (before/after/error)
- [ ] #5 Event subscription by agents working
- [ ] #6 Hook execution in agent context
- [ ] #7 Security sandboxing implemented
- [ ] #8 Tests pass: poetry run pytest tests/test_agent_hooks.py -v
- [ ] #9 Example demonstrates agent hook usage
<!-- AC:END -->
