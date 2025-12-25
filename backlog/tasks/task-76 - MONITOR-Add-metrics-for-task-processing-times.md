---
id: task-76
title: 'MONITOR: Add metrics for task processing times'
status: To Do
assignee: []
created_date: '2025-12-21 13:03'
labels:
  - monitor
  - backlog
  - metrics
  - observability
dependencies:
  - task-65
  - task-75
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Track task lifecycle metrics to understand task throughput and bottlenecks.

**Context**: Need visibility into how long tasks stay in each state and overall completion times.

**Metrics to implement**:
- Histogram: `backlog_task_duration_seconds` (by status: to_do, in_progress, done)
- Counter: `backlog_task_state_transitions_total` (by from_state, to_state)
- Gauge: `backlog_tasks_by_status` (current count by status)
- Histogram: `backlog_task_age_seconds` (time since creation)
- Counter: `backlog_tasks_created_total`
- Counter: `backlog_tasks_completed_total`

**Implementation**:
- Track timestamp on each state transition
- Calculate durations when state changes
- Update metrics in real-time
- Add to Grafana dashboard

**Files**:
- agent_factory/scaffold/task_metrics.py (create)
- agent_factory/scaffold/backlog_parser.py (add tracking)
- grafana_dashboards/backlog_panel.json (extend)

**Dependencies**:
- Blocked by: task-65 (Prometheus metrics infrastructure)
- Blocked by: task-75 (MCP metrics foundation)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Task metrics implemented in agent_factory/scaffold/task_metrics.py
- [ ] #2 All 6 metric types working
- [ ] #3 Timestamps tracked on state transitions
- [ ] #4 Duration calculations accurate
- [ ] #5 Metrics exposed via /metrics endpoint
- [ ] #6 Grafana dashboard shows task lifecycle metrics
- [ ] #7 Can visualize task throughput and bottlenecks
<!-- AC:END -->
