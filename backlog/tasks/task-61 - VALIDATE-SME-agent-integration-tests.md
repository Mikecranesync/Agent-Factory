---
id: task-61
title: 'VALIDATE: SME agent integration tests'
status: To Do
assignee: []
created_date: '2025-12-21 12:59'
labels:
  - test
  - rivet
  - sme-agents
  - week-3-4
  - production-blocker
dependencies:
  - task-51
  - task-52
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create integration tests for all 4 SME agents to validate they work together in the RIVET orchestration pipeline.

**Context**: Part of Week 3-4 production blockers. SME agents (Motor Control, Programming, Troubleshooting, Networking) must be validated before RIVET production launch.

**Scope**:
- Test Motor Control SME with real KB queries
- Test Programming SME with PLC code questions
- Test Troubleshooting SME with diagnostic scenarios
- Test Networking SME with industrial network questions
- Test confidence scoring accuracy
- Test citation quality
- Test orchestrator routing to correct SME

**Files**:
- tests/integration/test_sme_agents.py (create)
- agent_factory/rivet_pro/agents/*.py (reference)

**Dependencies**:
- Blocked by: task-51 (Motor Control SME implementation)
- Blocked by: task-52 (remaining 3 SME agents implementation)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Integration tests exist at tests/integration/test_sme_agents.py
- [ ] #2 All 4 SME agents have test coverage
- [ ] #3 Tests validate confidence scoring (>0.9 threshold)
- [ ] #4 Tests validate citation quality (sources present)
- [ ] #5 Tests validate orchestrator routing
- [ ] #6 Tests use real KB atoms (not mocks)
- [ ] #7 Tests pass: poetry run pytest tests/integration/test_sme_agents.py -v
- [ ] #8 Test coverage for happy path + edge cases
<!-- AC:END -->
