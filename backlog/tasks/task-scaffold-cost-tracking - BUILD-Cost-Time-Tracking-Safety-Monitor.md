---
id: task-scaffold-cost-tracking
title: 'BUILD: Cost & Time Tracking (Safety Monitor)'
status: To Do
assignee: []
created_date: 2025-12-18 06:24
labels:
- scaffold
- build
- safety
- monitoring
dependencies:
- task-scaffold-orchestrator
parent_task_id: task-scaffold-master
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Track API costs and execution time with circuit breakers.

The Safety Monitor enforces hard limits to prevent runaway costs:
- Tracks total cost (API calls to Claude)
- Tracks elapsed time (session duration)
- Tracks consecutive failures (circuit breaker)
- Checks limits before each task execution
- Aborts session if limits exceeded

Safety limits (configurable):
- max_cost: $5 (default)
- max_time_hours: 4 (default)
- max_consecutive_failures: 3 (default)

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SafetyMonitor class with check_limits() method
- [ ] #2 Tracks total_cost, elapsed_time, consecutive_failures
- [ ] #3 check_limits() returns (allowed, reason) tuple
- [ ] #4 Aborts if total_cost >= max_cost
- [ ] #5 Aborts if elapsed_time >= max_time_hours
- [ ] #6 Aborts if consecutive_failures >= max_consecutive_failures
- [ ] #7 Resets consecutive_failures on task success

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.
<!-- SECTION:NOTES:END -->
