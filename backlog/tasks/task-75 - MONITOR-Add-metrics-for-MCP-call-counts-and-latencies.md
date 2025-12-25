---
id: task-75
title: 'MONITOR: Add metrics for MCP call counts and latencies'
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
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Prometheus-style metrics to track MCP operation performance and usage patterns.

**Context**: Need observability into MCP integration performance for debugging and optimization.

**Metrics to implement**:
- Counter: `backlog_mcp_calls_total` (by operation: list, view, create, edit)
- Histogram: `backlog_mcp_latency_seconds` (by operation)
- Counter: `backlog_mcp_errors_total` (by error type)
- Gauge: `backlog_mcp_cache_hit_rate` (cache effectiveness)
- Counter: `backlog_fallback_activations_total` (MCP unavailable events)

**Implementation**:
- Use agent_factory/observability/metrics.py infrastructure
- Add metrics collection to backlog_parser.py
- Expose via /metrics endpoint
- Create Grafana dashboard panel for Backlog.md metrics

**Files**:
- agent_factory/scaffold/backlog_metrics.py (create)
- agent_factory/scaffold/backlog_parser.py (add metrics)
- grafana_dashboards/backlog_panel.json (create)

**Dependencies**:
- Blocked by: task-65 (Prometheus metrics infrastructure)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Metrics implemented in agent_factory/scaffold/backlog_metrics.py
- [ ] #2 All 5 metric types working
- [ ] #3 Metrics exposed via /metrics endpoint
- [ ] #4 Metrics collected on each MCP operation
- [ ] #5 Grafana dashboard panel created
- [ ] #6 Metrics visible in Prometheus
- [ ] #7 Dashboard imports successfully into Grafana
<!-- AC:END -->
