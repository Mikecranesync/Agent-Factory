# HARVEST BLOCK 26: Performance Tracker

**Priority**: LOW
**Size**: 198KB (total across 18 files in core/performance.py + monitoring/)
**Source**: `agent_factory/core/performance.py` (5.54KB) + `agent_factory/monitoring/` (192KB, 8 files)
**Target**: `rivet/core/performance.py` + `rivet/monitoring/`

---

## Overview

Production observability suite for Agent Factory - includes performance instrumentation, distributed tracing, cost tracking, Slack supervisor alerting, health monitoring, and multi-service metrics collection for production deployment.

### What This Adds

- **Performance Instrumentation**: Decorators & context managers for operation timing
- **Cumulative Metrics**: PerformanceTracker class for aggregated stats
- **Slack Supervisor**: Real-time alerts via Slack (bot errors, API failures, KB gaps)
- **Health Server**: HTTP health endpoint for k8s/Docker readiness probes
- **CMMS Monitoring**: Atlas CMMS integration health tracking
- **Telegram Bot Monitoring**: Bot uptime, message throughput, error rates
- **KB Coverage Monitoring**: Knowledge base gap detection & alerts
- **Supervisor Service**: Centralized monitoring orchestrator

### Key Features

```python
from rivet.core.performance import timed_operation, timer, PerformanceTracker

# Decorator timing (async/sync auto-detection)
@timed_operation("route_query")
async def route_query(request):
    # ... implementation ...
    pass
# Logs: ⏱️ PERF [route_query]: 245.3ms

# Context manager timing
with timer("database_query"):
    results = db.execute(query)
# Logs: ⏱️ PERF [database_query]: 12.7ms

# Cumulative metrics tracking
tracker = PerformanceTracker()

with tracker.measure("llm_call"):
    response = llm.complete(messages)

with tracker.measure("db_query"):
    results = db.query(sql)

with tracker.measure("llm_call"):  # Second LLM call
    response2 = llm.complete(messages2)

# Get summary
print(tracker.summary())
# Output:
# Operation: llm_call
#   Count: 2
#   Total: 523.5ms
#   Avg: 261.8ms
#   Min: 234.2ms
#   Max: 289.3ms
# Operation: db_query
#   Count: 1
#   Total: 12.7ms
#   Avg: 12.7ms
```

---

## Performance Instrumentation

**Decorator Pattern** (`@timed_operation`):
```python
from rivet.core.performance import timed_operation

# Async function
@timed_operation("route_a_kb_query")
async def route_a_strong_kb(self, request):
    # ... implementation ...
    pass
# Logs: ⏱️ PERF [route_a_kb_query]: 187.4ms

# Sync function
@timed_operation("calculate_confidence")
def calculate_confidence(atoms, query):
    # ... implementation ...
    return score
# Logs: ⏱️ PERF [calculate_confidence]: 3.2ms

# With custom log level
@timed_operation("debug_operation", log_level=logging.DEBUG)
async def debug_fn():
    pass
```

**Context Manager Pattern** (`with timer()`):
```python
from rivet.core.performance import timer

# Time specific code blocks
with timer("semantic_search"):
    results = retriever.retrieve(query, limit=10)

with timer("response_generation"):
    response = synthesizer.generate(atoms, query)

# Nested timing
with timer("full_pipeline"):
    with timer("retrieval"):
        atoms = retriever.retrieve(query)
    with timer("generation"):
        response = synthesizer.generate(atoms)
```

---

## Cumulative Metrics Tracking

```python
from rivet.core.performance import PerformanceTracker

# Initialize tracker
tracker = PerformanceTracker()

# Measure operations
for i in range(100):
    with tracker.measure("llm_call"):
        response = llm.complete(prompt)

    with tracker.measure("db_query"):
        results = db.query(sql)

# Get statistics
print(tracker.summary())

# Access raw data
for op_name, stats in tracker.operations.items():
    print(f"{op_name}:")
    print(f"  Count: {stats['count']}")
    print(f"  Total: {stats['total_ms']:.1f}ms")
    print(f"  Avg: {stats['total_ms'] / stats['count']:.1f}ms")
    print(f"  Min: {stats['min_ms']:.1f}ms")
    print(f"  Max: {stats['max_ms']:.1f}ms")

print(f"Total time: {tracker.total_time_ms:.1f}ms")
```

---

## Slack Supervisor Alerting

**Real-time Alerts** (`rivet.monitoring.slack_reporter`):
```python
from rivet.monitoring.slack_reporter import SlackReporter

# Initialize reporter
reporter = SlackReporter(
    webhook_url="https://hooks.slack.com/services/...",
    channel="#rivet-alerts"
)

# Send alert
await reporter.send_alert(
    title="🚨 High Error Rate Detected",
    message="Telegram bot error rate exceeded 10% (15 errors in last hour)",
    severity="critical",  # critical, warning, info
    fields={
        "Error Rate": "15%",
        "Time Window": "Last 60 minutes",
        "Bot": "RIVET Telegram Bot"
    }
)

# Send metric update
await reporter.send_metric(
    metric_name="KB Coverage",
    value="87.3%",
    trend="up",  # up, down, neutral
    context="Knowledge base coverage improved by 3.2% this week"
)
```

---

## Health Monitoring Server

**HTTP Health Endpoint** (`rivet.monitoring.health_server`):
```python
from rivet.monitoring.health_server import HealthServer

# Start health server (for k8s readiness probes)
health_server = HealthServer(port=8080)
health_server.start()

# Health check endpoint: http://localhost:8080/health
# Response:
{
  "status": "UP",
  "checks": {
    "database": "UP",
    "redis": "UP",
    "llm_api": "UP"
  },
  "uptime_seconds": 3600,
  "version": "1.0.0"
}

# Register custom health check
health_server.register_check("atlas_cmms", check_atlas_health)
```

---

## CMMS Integration Monitoring

**Atlas CMMS Monitoring** (`rivet.monitoring.cmms_monitor`):
```python
from rivet.monitoring.cmms_monitor import CMmsMonitor

monitor = CMmsMonitor()

# Track work order creation
await monitor.track_work_order_created(
    work_order_id="WO-12345",
    priority="HIGH",
    created_by="rivet_bot"
)

# Track work order completion
await monitor.track_work_order_completed(
    work_order_id="WO-12345",
    duration_hours=2.5,
    resolved_by="tech_456"
)

# Get CMMS metrics
metrics = monitor.get_metrics(days=7)
# Returns: work_orders_created, avg_resolution_time, failure_rate
```

---

## Telegram Bot Monitoring

**Bot Health Tracking** (`rivet.monitoring.telegram_monitor`):
```python
from rivet.monitoring.telegram_monitor import TelegramMonitor

monitor = TelegramMonitor()

# Track message received
await monitor.track_message(
    user_id="telegram_123",
    message_type="text",  # text, voice, photo
    intent="troubleshooting"
)

# Track bot response
await monitor.track_response(
    user_id="telegram_123",
    route="route_a",  # A, B, C, D
    confidence=0.87,
    response_time_ms=245.3
)

# Track error
await monitor.track_error(
    error_type="LLMAPIError",
    error_message="OpenAI API timeout",
    severity="high"
)

# Get bot metrics
metrics = monitor.get_metrics(hours=24)
# Returns: message_count, avg_response_time, error_rate, route_distribution
```

---

## KB Coverage Monitoring

**Knowledge Gap Tracking** (`rivet.monitoring.kb_monitor`):
```python
from rivet.monitoring.kb_monitor import KBMonitor

monitor = KBMonitor()

# Track KB query
await monitor.track_query(
    query="Siemens S7-1200 fault F003",
    kb_coverage="strong",  # strong, thin, none
    atoms_found=12
)

# Track gap detected
await monitor.track_gap(
    query="Unknown manufacturer XYZ",
    gap_type="unknown_manufacturer",
    triggered_research=True
)

# Get KB health metrics
metrics = monitor.get_metrics(days=7)
# Returns: coverage_rate, gap_count, research_triggers, top_gaps
```

---

## Supervisor Service

**Centralized Monitoring Orchestrator** (`rivet.monitoring.supervisor_service`):
```python
from rivet.monitoring.supervisor_service import SupervisorService

# Initialize supervisor
supervisor = SupervisorService(
    slack_webhook="https://hooks.slack.com/...",
    check_interval_seconds=60,
    alert_threshold={
        "error_rate": 0.10,  # Alert if >10% errors
        "response_time_p95": 5000,  # Alert if p95 >5s
        "kb_coverage": 0.80  # Alert if <80% coverage
    }
)

# Start monitoring (runs in background)
await supervisor.start()

# Supervisor automatically:
# 1. Polls services every 60 seconds
# 2. Checks metrics against thresholds
# 3. Sends Slack alerts on violations
# 4. Tracks long-term trends

# Stop supervisor
await supervisor.stop()
```

---

## Dependencies

```bash
# Install required packages
poetry add prometheus-client slack-sdk aiohttp

# Optional: For advanced monitoring
poetry add grafana-api datadog
```

## Environment Variables

```bash
# Slack Integration
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export SLACK_CHANNEL=#rivet-alerts

# Health Server
export HEALTH_SERVER_PORT=8080

# Monitoring Intervals
export SUPERVISOR_CHECK_INTERVAL=60  # seconds
export METRICS_RETENTION_DAYS=30
```

---

## Quick Implementation Guide

1. Copy source files:
   ```bash
   cp agent_factory/core/performance.py rivet/core/performance.py
   cp -r agent_factory/monitoring/ rivet/monitoring/
   ```
2. Install: `poetry add prometheus-client slack-sdk aiohttp`
3. Set env vars: `SLACK_WEBHOOK_URL`, `HEALTH_SERVER_PORT`
4. Validate: `python -c "from rivet.core.performance import PerformanceTracker; print('OK')"`

---

## Validation

```bash
# Test performance instrumentation
python -c "
from rivet.core.performance import timed_operation, timer

@timed_operation('test')
def test_fn():
    import time
    time.sleep(0.1)

test_fn()
# Output: ⏱️ PERF [test]: 100.2ms
"

# Test cumulative tracking
python -c "
from rivet.core.performance import PerformanceTracker

tracker = PerformanceTracker()

for i in range(5):
    with tracker.measure('operation'):
        import time
        time.sleep(0.05)

print(tracker.summary())
"

# Test Slack reporter (requires webhook)
python -c "
import asyncio
from rivet.monitoring.slack_reporter import SlackReporter

async def test():
    reporter = SlackReporter()
    await reporter.send_alert('Test Alert', 'Test message', 'info')

asyncio.run(test())
"
```

---

## Integration Notes

**RIVET Orchestrator Integration**:
```python
from rivet.core.orchestrator import RivetOrchestrator
from rivet.core.performance import PerformanceTracker
from rivet.monitoring.supervisor_service import SupervisorService

# Initialize with monitoring
orchestrator = RivetOrchestrator()
tracker = PerformanceTracker()
supervisor = SupervisorService()

# Start supervisor (background monitoring)
await supervisor.start()

# Track orchestrator performance
async def route_query_monitored(request):
    with tracker.measure("full_pipeline"):
        with tracker.measure("routing_decision"):
            decision = orchestrator.decide_route(request)

        with tracker.measure("route_execution"):
            response = await orchestrator.execute_route(decision, request)

    # Send metrics to supervisor
    await supervisor.report_metrics({
        "route": decision.route,
        "response_time_ms": tracker.operations["full_pipeline"]["total_ms"],
        "confidence": response.confidence
    })

    return response
```

**Cost Tracking Integration**:
```python
from rivet.core.performance import PerformanceTracker
from rivet.llm.tracker import get_global_tracker

# Combine performance + cost tracking
perf_tracker = PerformanceTracker()
cost_tracker = get_global_tracker()

with perf_tracker.measure("llm_call"):
    response = llm.complete(prompt)

# Generate combined report
perf_summary = perf_tracker.summary()
cost_summary = cost_tracker.aggregate_stats()

print(f"Performance: {perf_summary}")
print(f"Cost: ${cost_summary['total_cost_usd']:.2f}")
```

---

## What This Enables

- ✅ Production observability (performance, cost, errors)
- ✅ Real-time Slack alerts (error rates, KB gaps, API failures)
- ✅ Health monitoring (k8s readiness probes)
- ✅ CMMS integration tracking (work orders, resolution time)
- ✅ Telegram bot metrics (throughput, error rates, response time)
- ✅ KB coverage monitoring (gap detection, research triggers)
- ✅ Distributed tracing (LangSmith integration)
- ✅ Supervisor service (centralized monitoring orchestrator)

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Supervisor Service (Central)                │
│  - Polls services every 60s                              │
│  - Checks thresholds                                     │
│  - Sends Slack alerts                                    │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┼─────────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼         ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Telegram││  CMMS   ││   KB    ││ Health  ││  Slack  │
│ Monitor ││ Monitor ││ Monitor ││ Server  ││Reporter │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌──────────────────────────────────────────────────────┐
│         Performance Tracker (Core)                    │
│  - @timed_operation decorators                        │
│  - with timer() context managers                      │
│  - PerformanceTracker class                           │
└──────────────────────────────────────────────────────┘
```

---

## Production Deployment

**Docker Compose** (with health checks):
```yaml
services:
  rivet-orchestrator:
    image: rivet-orchestrator:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    environment:
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - HEALTH_SERVER_PORT=8080
      - SUPERVISOR_CHECK_INTERVAL=60
```

**Kubernetes** (readiness probe):
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: rivet-orchestrator
spec:
  containers:
  - name: rivet
    image: rivet-orchestrator:latest
    readinessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 30
```

---

## TIER 4 COMPLETE! ✅

**All 4 TIER 4 extraction blocks created:**
- ✅ HARVEST 23: Voice Handler (Telegram voice processing)
- ✅ HARVEST 24: Atlas Client (CMMS B2B integration)
- ✅ HARVEST 25: Manus Client (robotics automation)
- ✅ HARVEST 26: Performance Tracker (observability suite)

**Next Steps:**
1. Commit TIER 4 blocks
2. Create TIER4_HARVEST_COMPLETE.md
3. **ALL 27 HARVEST BLOCKS COMPLETE** - Ready for Rivet-PRO implementation

SEE FULL SOURCE:
- `agent_factory/core/performance.py` (5.54KB)
- `agent_factory/monitoring/` (8 files, 192KB):
  - `cmms_monitor.py` - CMMS integration tracking
  - `telegram_monitor.py` - Bot health metrics
  - `kb_monitor.py` - Knowledge base coverage
  - `slack_reporter.py` - Real-time alerts
  - `health_server.py` - HTTP health endpoint
  - `supervisor_service.py` - Centralized monitoring
  - `slack_command_handler.py` - Slack slash commands
  - `__init__.py`
