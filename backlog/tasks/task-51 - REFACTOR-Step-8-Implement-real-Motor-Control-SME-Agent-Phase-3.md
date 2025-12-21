---
id: task-51
title: 'REFACTOR Step 8: Implement real Motor Control SME Agent (Phase 3)'
status: To Do
assignee: []
created_date: '2025-12-21 11:49'
labels:
  - refactor
  - rivet
  - production-blocker
  - week-3
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace mock with production Motor Control SME agent using template.

**Actions**:
1. Use SME template from task-43
2. Implement `MotorControlSMEAgent`:
   - Query analysis for motor questions
   - KB search with vendor filtering
   - Answer generation with citations
   - Confidence scoring
3. Integration test with real KB
4. Deploy to staging

**Risk**: Medium (production feature)
**Files Changed**: rivet_pro/agents/motor_control_sme.py, tests/integration/

**Reference**: docs/REFACTOR_PLAN.md Step 8, Phase 3 task-3.1
**Depends on**: task-43 (SME template)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Mock replaced with real implementation
- [ ] #2 Integration tests pass
- [ ] #3 Works with real KB (1964 atoms)
- [ ] #4 Staging deployment successful
- [ ] #5 Confidence scoring accurate
<!-- AC:END -->
