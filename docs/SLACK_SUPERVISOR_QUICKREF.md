# Slack Supervisor Quick Reference

## Installation

```bash
poetry add asyncpg httpx
psql $DATABASE_URL -f sql/supervisor_schema.sql
```

## Configuration

```bash
# .env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
DATABASE_URL=postgresql://...
```

## Basic Usage

```python
from agent_factory.observability import agent_task

async with agent_task('agent-id', 'Task Name') as ctx:
    await ctx.checkpoint('Step 1', progress=25)
    await ctx.checkpoint('Step 2', progress=50)
    ctx.add_artifact('output.txt')
    ctx.update_tokens(50000)
```

## Status Types

| Status | Emoji | Color | Use Case |
|--------|-------|-------|----------|
| STARTING | 🚀 | Blue | Agent initialized |
| PLANNING | 🧠 | Purple | Planning phase |
| WORKING | ⚙️ | Green | Active processing |
| CHECKPOINT | 📍 | Yellow | Progress update |
| WAITING_APPROVAL | ⏳ | Orange | Human approval needed |
| BLOCKED | 🚧 | Orange | Blocked by dependency |
| ERROR | ❌ | Red | Execution error |
| COMPLETE | ✅ | Green | Task finished |
| CANCELLED | 🛑 | Gray | Task cancelled |

## Context Manager Methods

```python
# Post checkpoint
await ctx.checkpoint('Action', progress=50, force=False)

# Add artifact (PR, file, URL)
ctx.add_artifact('https://github.com/user/repo/pull/123')

# Update token usage
ctx.update_tokens(150000)  # Warning at 140k (70%)

# Set progress
ctx.set_progress(75)  # 0-100

# Get elapsed time
elapsed = ctx.elapsed_seconds
```

## Decorator Pattern

```python
from agent_factory.observability import supervised_agent

@supervised_agent('agent-id', 'Task Name', repo_scope='repo')
async def my_agent(ctx):
    await ctx.checkpoint('Working', progress=50)
    return result
```

## Manual Supervisor

```python
from agent_factory.observability import get_supervisor, AgentCheckpoint, AgentStatus

supervisor = get_supervisor()

cp = AgentCheckpoint(
    agent_id='agent-id',
    task_name='Task',
    status=AgentStatus.WORKING,
    progress=50,
    last_action='Processing data'
)

await supervisor.post_checkpoint(cp, force=True)
await supervisor.close()
```

## Sync Emitter (Subprocess)

```python
from agent_factory.observability import SyncCheckpointEmitter

emitter = SyncCheckpointEmitter('agent-id', 'Task Name')
emitter.emit('Step 1', status='working', progress=50)
```

## Database Queries

```bash
# Active tasks
curl http://localhost:3001/tasks?status=running

# Agent stats
curl http://localhost:3001/tasks/agent-id-123

# Daily metrics
curl http://localhost:3001/metrics?days=7
```

## Deployment

```bash
# Local
poetry run uvicorn agent_factory.observability.server:create_app --factory --port 3001

# VPS
./scripts/deploy_slack_supervisor.sh

# Systemd
sudo systemctl start supervisor
sudo journalctl -u supervisor -f
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No Slack messages | Check SLACK_BOT_TOKEN and bot permissions |
| Database errors | Verify schema deployed: `\dt agent_*` |
| Token warnings | Agent using >70% context (140k/200k tokens) |
| Import errors | Run `poetry install` or `poetry add asyncpg httpx` |

## Examples

**RIVET Orchestrator (Already Integrated):**
```python
# agent_factory/orchestrators/rivet_orchestrator.py
async with agent_task(
    agent_id=f"rivet-diagnose-{int(time.time())}",
    task_name=f"Diagnose {fault_code} on {equipment_type}",
) as ctx:
    await ctx.checkpoint(f"Routed to {route} SME", progress=30)
    # ... processing ...
    await ctx.checkpoint("Diagnosis complete", progress=100)
```

**Long-Running Job:**
```python
async with agent_task('scraper', 'Scrape 1000 URLs') as ctx:
    for i, url in enumerate(urls):
        await scrape(url)
        progress = int((i + 1) / len(urls) * 100)
        await ctx.checkpoint(f"Scraped {url}", progress=progress)
```

**Multi-Agent Coordination:**
```python
async with agent_task('main', 'Deploy App') as main_ctx:
    await main_ctx.checkpoint('Starting', progress=10)

    async with agent_task('test', 'Run Tests') as test_ctx:
        await test_ctx.checkpoint('Testing', progress=50)

    await main_ctx.checkpoint('Tests passed', progress=50)
    # ... continue deployment ...
```

## Resources

- Full docs: `docs/SLACK_SUPERVISOR_INTEGRATION.md`
- Demo: `examples/slack_supervisor_demo.py`
- Deploy script: `scripts/deploy_slack_supervisor.sh`
- Service file: `rivet/supervisor.service`
- Schema: `sql/supervisor_schema.sql`
