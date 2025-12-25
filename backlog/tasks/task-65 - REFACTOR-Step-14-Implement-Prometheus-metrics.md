---
id: task-65
title: 'REFACTOR Step 14: Implement Prometheus metrics'
status: To Do
assignee: []
created_date: '2025-12-21 13:00'
labels:
  - refactor
  - observability
  - metrics
  - week-4-5
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Prometheus-style metrics endpoint for production monitoring with counters, histograms, and gauges.

**Context**: Part of Week 4-5 observability. Need real-time metrics for agent performance monitoring.

**Metrics to implement**:
- Counter: agent_invocations_total (by agent type)
- Counter: llm_tokens_total (by model, input/output)
- Histogram: agent_response_latency_seconds
- Histogram: llm_api_latency_seconds
- Gauge: active_sessions_count
- Counter: agent_errors_total (by error type)
- Counter: llm_cost_usd_total (by model)

**Files**:
- agent_factory/observability/metrics.py (implement)
- agent_factory/api/app.py (add /metrics endpoint)
- docs/deployment/MONITORING_SETUP.md (create)
- grafana_dashboards/agent_factory.json (create Grafana dashboard)

**Dependencies**:
- None (can start anytime)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Metrics implementation complete in agent_factory/observability/metrics.py
- [ ] #2 All 7 metric types implemented
- [ ] #3 /metrics endpoint added to FastAPI app
- [ ] #4 Endpoint returns Prometheus format
- [ ] #5 Metrics updated on each agent invocation
- [ ] #6 Documentation exists at docs/deployment/MONITORING_SETUP.md
- [ ] #7 Grafana dashboard exists at grafana_dashboards/agent_factory.json
- [ ] #8 Metrics endpoint accessible: curl http://localhost:8000/metrics
- [ ] #9 Grafana dashboard imports successfully
<!-- AC:END -->
