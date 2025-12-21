---
id: task-45
title: 'REFACTOR Step 11: Optimize slow test execution (task-16)'
status: To Do
assignee: []
created_date: '2025-12-21 11:48'
labels:
  - refactor
  - testing
  - performance
  - week-5
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Improve test suite performance by profiling, mocking external services, and parallelizing execution.

**Actions**:
1. Profile test suite: `pytest --durations=10`
2. Identify slow tests (likely integration tests)
3. Mock external services (Supabase, OpenAI) for unit tests
4. Parallelize with pytest-xdist
5. Split fast/slow test suites in CI/CD

**Risk**: Low (test improvements)
**Files Changed**: tests/conftest.py, .github/workflows/tests.yml, pytest.ini

**Reference**: docs/REFACTOR_PLAN.md Step 11, task-16
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Test execution 50% faster
- [ ] #2 Fast tests run on every PR
- [ ] #3 Slow tests run nightly
- [ ] #4 Parallel execution configured
- [ ] #5 All tests still pass
<!-- AC:END -->
