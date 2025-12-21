---
id: task-43
title: 'REFACTOR Step 7: Create SME agent template pattern'
status: To Do
assignee: []
created_date: '2025-12-21 11:48'
labels:
  - refactor
  - rivet
  - agents
  - week-3
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Standardize SME agent implementations with a reusable template before building real agents.

**Actions**:
1. Create `agent_factory/templates/sme_agent_template.py`:
   - Standard structure (analyze_query, search_kb, generate_answer, score_confidence)
   - Error handling patterns
   - Logging/tracing hooks
2. Document pattern in `docs/patterns/SME_AGENT_PATTERN.md`
3. Create example implementation

**Risk**: Low (just a template)
**Files Changed**: templates/sme_agent_template.py, docs/patterns/, examples/

**Reference**: docs/REFACTOR_PLAN.md Step 7
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SME template class created
- [ ] #2 Pattern documented
- [ ] #3 Example implementation works
- [ ] #4 Test runs: poetry run python examples/sme_agent_example.py
<!-- AC:END -->
