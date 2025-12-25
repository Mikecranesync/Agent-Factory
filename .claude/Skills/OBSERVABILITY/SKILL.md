# OBSERVABILITY Skill

## Purpose

Monitor agent health, track performance metrics, and detect issues across all Agent Factory products (SCAFFOLD, PLC Tutor, RIVET Industrial).

**Load this skill when:**
- Debugging agent failures
- Monitoring production systems
- Tracking performance trends
- Investigating cost overruns
- Validating system health

---

## Core Capabilities

### 1. Agent Health Monitoring
- **Real-time status**: Check if agents are running/stuck/crashed
- **Success rate tracking**: Monitor failure rates over time
- **Response time monitoring**: Detect slow agents
- **Cost tracking**: Monitor spend per agent

### 2. System Health Checks
- **Database connectivity**: Verify Supabase/Neon/Railway/Render connections
- **API availability**: Check OpenAI/Anthropic/ElevenLabs APIs
- **Memory usage**: Monitor PostgreSQL memory storage
- **Queue health**: Check Redis job queues (VPS)

### 3. Performance Metrics
- **Throughput**: Tasks/hour, atoms ingested/hour
- **Latency**: P50/P95/P99 response times
- **Cost efficiency**: $/task, $/atom, $/video
- **Quality metrics**: Success rate, retry rate, error rate

### 4. Alerting & Diagnostics
- **Threshold alerts**: Notify when metrics exceed limits
- **Anomaly detection**: Flag unusual patterns
- **Error aggregation**: Group similar failures
- **Root cause analysis**: Trace errors to source

---

## Quick Start

```bash
# Load observability context
Skill("OBSERVABILITY")

# Check system health (all products)
.claude/observability/health-check.sh

# View live dashboard
.claude/observability/status.sh

# Collect metrics (weekly aggregation)
.claude/observability/collect-metrics.sh
```

---

## Metrics Schema

**Location**: `.claude/observability/metrics.json`

```json
{
  "timestamp": "2025-12-22T18:30:00Z",
  "period": "hour",
  "platform": {
    "orchestrator": {
      "tasks_routed": 150,
      "avg_latency_ms": 45,
      "errors": 2
    },
    "llm_router": {
      "calls": 1200,
      "cost_usd": 3.45,
      "cache_hit_rate": 0.67
    },
    "database": {
      "active_provider": "supabase",
      "connections": 12,
      "query_p95_ms": 120
    }
  },
  "scaffold": {
    "prs_created": 8,
    "avg_pr_time_minutes": 42,
    "test_pass_rate": 0.95,
    "cost_per_pr_usd": 0.18
  },
  "plc_tutor": {
    "videos_generated": 3,
    "atoms_ingested": 47,
    "youtube_views": 1250,
    "cost_per_video_usd": 2.30
  },
  "rivet": {
    "reddit_posts_monitored": 340,
    "answers_generated": 18,
    "confidence_avg": 0.87,
    "escalations_to_human": 2
  }
}
```

---

## Health Check Script

**File**: `.claude/observability/health-check.sh`

**Validates:**
1. Database connectivity (4 providers)
2. LLM API availability (OpenAI, Anthropic, Google)
3. Memory storage (PostgreSQL + pgvector)
4. VPS KB Factory (Redis + Ollama)
5. Git worktree enforcement
6. Hooks system operational

**Exit codes:**
- `0` = All systems healthy
- `1` = Warning (degraded but functional)
- `2` = Critical (system unavailable)

**Example output:**
```
✅ Database: Supabase connected (12ms latency)
✅ LLM Router: 3/3 providers available
✅ Memory Storage: PostgreSQL operational
⚠️  VPS KB Factory: Redis queue backlog (340 jobs)
✅ Worktree Enforcement: pre-commit hook active
✅ Hooks System: 7/7 hooks enabled

Overall Status: HEALTHY (1 warning)
```

---

## Live Status Dashboard

**File**: `.claude/observability/status.sh`

**Displays:**
- Last 24 hours metrics (aggregated)
- Top 5 agents by cost
- Top 5 agents by failures
- Current system load
- Recent errors (last 10)

**Example output:**
```
=== Agent Factory Status Dashboard ===
Last Updated: 2025-12-22 18:30:00 EST

[PLATFORM HEALTH]
Orchestrator: ✅ 150 tasks/hour
LLM Router:   ✅ $3.45/hour (67% cache hit)
Database:     ✅ Supabase (12ms P95)

[PRODUCT METRICS - Last 24h]
SCAFFOLD:     8 PRs created, 95% tests pass
PLC Tutor:    3 videos, 47 atoms, $6.90 cost
RIVET:        18 answers, 87% confidence

[TOP AGENTS BY COST]
1. ScriptwriterAgent:      $4.20 (12 calls)
2. VoiceProductionAgent:   $3.80 (3 calls)
3. ResearchAgent:          $2.10 (47 calls)

[TOP AGENTS BY FAILURES]
1. YouTubeUploaderAgent:   2 failures (quota exceeded)
2. RedditResponder:        1 failure (auth expired)

[RECENT ERRORS]
2025-12-22 18:15:00 - YouTubeUploaderAgent - Quota exceeded (429)
2025-12-22 17:45:00 - RedditResponder - Auth token expired

Overall: 🟢 HEALTHY
```

---

## Metrics Collection

**File**: `.claude/observability/collect-metrics.sh`

**Aggregates:**
- Hourly metrics → daily summaries
- Daily summaries → weekly reports
- Weekly reports → monthly trends

**Stored in:**
- `.claude/observability/metrics/hourly/*.json`
- `.claude/observability/metrics/daily/*.json`
- `.claude/observability/metrics/weekly/*.json`

**Run automatically via cron (optional):**
```bash
# Add to crontab
0 * * * * cd ~/agent-factory && ./.claude/observability/collect-metrics.sh
```

---

## Integration with Other Systems

### Backlog.md MCP
- Metrics feed into task completion estimates
- Failed agents create FIX tasks automatically
- Cost tracking updates budget forecasts

### Hooks System
- on_agent_execute.sh logs start time
- on_agent_finish.sh logs duration, cost, status
- Metrics aggregated from hook logs

### LLM Router
- Cost tracking per model/capability
- Cache hit rates monitored
- Fallback chain usage tracked

### Database Manager
- Provider failover events logged
- Connection pool utilization tracked
- Query performance monitored

---

## Alerting Rules

**Defined in**: `.claude/observability/config.yml`

```yaml
alerts:
  llm_cost:
    threshold_usd_per_hour: 10.0
    action: "notify"

  agent_failure_rate:
    threshold_percent: 15.0
    window_hours: 1
    action: "create_task"

  database_latency:
    threshold_ms: 500
    action: "log"

  youtube_quota:
    threshold_percent: 90.0
    action: "notify"
```

---

## Key Observability Agents

### 1. MetricsCollectorAgent
**Purpose**: Aggregate metrics from logs, databases, APIs

**Runs**: Every hour (cron)

**Output**: `metrics.json` (hourly snapshots)

**Code**: `agent_factory/observability/metrics_collector.py`

### 2. HealthCheckerAgent
**Purpose**: Validate system components are operational

**Runs**: On-demand + every 5 minutes (optional)

**Output**: Health status (HEALTHY, DEGRADED, CRITICAL)

**Code**: `agent_factory/observability/health_checker.py`

### 3. AnomalyDetectorAgent
**Purpose**: Detect unusual patterns (cost spikes, failure clusters)

**Runs**: Every 6 hours

**Output**: Anomaly reports → creates FIX tasks if critical

**Code**: `agent_factory/observability/anomaly_detector.py`

### 4. AlertDispatcherAgent
**Purpose**: Send notifications when thresholds exceeded

**Runs**: Continuously (event-driven)

**Output**: Email, Slack, Discord, Telegram alerts

**Code**: `agent_factory/observability/alert_dispatcher.py`

---

## Observability Commands

```bash
# Health check (all systems)
.claude/observability/health-check.sh

# Live status dashboard
.claude/observability/status.sh

# Collect metrics (manual trigger)
.claude/observability/collect-metrics.sh

# View specific product metrics
jq '.scaffold' .claude/observability/metrics.json

# Check agent cost breakdown
jq '.platform.llm_router' .claude/observability/metrics.json

# View recent errors
tail -n 50 data/logs/hooks/errors.log

# Check database provider health
.claude/observability/health-check.sh --component database
```

---

## Monitoring Dashboards (Future)

**Planned integrations:**

1. **Grafana Dashboard** (Month 4+)
   - Real-time metrics visualization
   - Custom alerts + thresholds
   - Cost tracking charts
   - Agent performance heatmaps

2. **Prometheus Metrics** (Month 6+)
   - Expose `/metrics` endpoint
   - Scrape metrics every 15s
   - Long-term storage + querying

3. **Sentry Error Tracking** (Month 3+)
   - Automatic error reporting
   - Stack trace aggregation
   - Release tracking

---

## Performance Baselines

**Established from testing (Dec 2025):**

| Metric | Baseline | Target | Alert Threshold |
|--------|----------|--------|-----------------|
| Orchestrator Latency | 45ms P95 | <100ms | >200ms |
| LLM Cost/Hour | $3.45 | <$5.00 | >$10.00 |
| Database P95 Latency | 120ms | <200ms | >500ms |
| Agent Failure Rate | 2% | <5% | >15% |
| Cache Hit Rate | 67% | >60% | <40% |
| SCAFFOLD PR Time | 42min | <60min | >120min |
| PLC Video Cost | $2.30 | <$3.00 | >$5.00 |
| RIVET Confidence | 0.87 | >0.85 | <0.75 |

---

## Troubleshooting

### High LLM Costs
1. Check cache hit rate: `jq '.platform.llm_router.cache_hit_rate' metrics.json`
2. Review model selection: Are SIMPLE tasks using gpt-3.5-turbo?
3. Check for retry loops: `grep -i "retry" data/logs/hooks/agents.log`

### Agent Failures
1. View failure log: `grep "failure" .claude/history/agents.md`
2. Check error details: `tail -n 100 data/logs/hooks/errors.log`
3. Validate API keys: `.claude/observability/health-check.sh --component apis`

### Database Connection Issues
1. Check active provider: `jq '.platform.database.active_provider' metrics.json`
2. Test failover: `poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; print(DatabaseManager().health_check_all())"`
3. View connection pool: `SELECT count(*) FROM pg_stat_activity;` (in Supabase SQL Editor)

### VPS KB Factory Backlog
1. Check queue size: `ssh root@72.60.175.144 "docker exec infra_redis_1 redis-cli LLEN kb_ingest_jobs"`
2. View worker logs: `ssh root@72.60.175.144 "docker logs infra_rivet-worker_1 --tail 50"`
3. Scale workers: Edit `docker-compose.yml` → `scale rivet-worker=3`

---

## Best Practices

### 1. Monitor Daily (5 minutes)
```bash
# Morning routine
.claude/observability/status.sh
# Check for critical errors
grep "CRITICAL" data/logs/hooks/errors.log
```

### 2. Review Weekly (30 minutes)
- View weekly metrics: `cat .claude/history/weekly_summary_*.json`
- Check cost trends: `jq '.total_cost_usd' .claude/history/weekly_summary_*.json`
- Review failed agents: `grep "failure" .claude/history/agents.md | sort | uniq -c`

### 3. Tune Alerts
- Start with conservative thresholds (alert rarely)
- Lower thresholds as you learn normal ranges
- Disable noisy alerts (>5 per day = too noisy)

### 4. Investigate Anomalies
- Cost spike? Check LLM Router logs for retry loops
- Failure spike? Check if external API is down
- Latency spike? Check database provider health

---

## Files Reference

| File | Purpose | Auto-Updated |
|------|---------|--------------|
| `health-check.sh` | System health validation | ❌ Manual |
| `status.sh` | Live dashboard | ❌ Manual |
| `collect-metrics.sh` | Metrics aggregation | ✅ Cron (optional) |
| `metrics.json` | Current metrics snapshot | ✅ Hourly |
| `config.yml` | Alert thresholds | ❌ Manual |
| `metrics/hourly/*.json` | Hourly snapshots | ✅ Auto-archived |
| `metrics/daily/*.json` | Daily summaries | ✅ Auto-aggregated |
| `metrics/weekly/*.json` | Weekly reports | ✅ Auto-aggregated |

---

## Related Documentation

- **Platform Architecture**: `docs/architecture/00_architecture_platform.md`
- **LLM Router**: `agent_factory/llm/README.md`
- **Database Manager**: `agent_factory/core/database_manager.py`
- **Hooks System**: `.claude/hooks/README.md`
- **UOCS History**: `.claude/Skills/CORE/HistorySystem.md`

---

**Last Updated**: 2025-12-22
**Version**: 1.0.0
**Status**: Production Ready
