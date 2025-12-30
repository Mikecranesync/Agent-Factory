# Slack Supervisor Integration

**Real-time agent observability via Slack**

## Overview

The Slack Supervisor provides real-time monitoring and supervisory control for autonomous agents running in Agent Factory. Every agent checkpoint, error, and completion is posted to Slack with structured data and visual indicators.

## Features

- **Real-time Checkpoints** - Agent status updates every 30s or on-demand
- **Context Tracking** - Token usage warnings at 70% and 85%
- **Error Alerting** - Immediate Slack notifications on failures
- **Audit Trail** - PostgreSQL database stores all agent activity
- **Thread-based Updates** - All agent updates in single Slack thread
- **Progress Tracking** - Visual progress bars (0-100%)
- **Artifact Tracking** - Links to PRs, files, deployments

## Architecture

```
Agent Execution
    ↓
agent_task() context manager
    ↓
SlackSupervisor.post_checkpoint()
    ↓
Slack API (Bot Token or Webhook)
    ↓
#agent-supervisory channel
    ↓
SupervisoryDB.record_checkpoint()
    ↓
PostgreSQL (audit trail)
```

## Quick Start

### 1. Install Dependencies

Already installed via poetry:
```bash
poetry add asyncpg httpx
```

### 2. Configure Slack

Add to `.env`:
```bash
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
```

### 3. Deploy Database Schema

```bash
psql $DATABASE_URL -f sql/supervisor_schema.sql
```

Creates 4 tables:
- `agent_tasks` - Task metadata and status
- `agent_checkpoints` - Checkpoint history
- `human_interventions` - Human approvals/cancellations
- `task_artifacts` - Generated artifacts (PRs, files, etc.)

### 4. Instrument Your Agent

```python
from agent_factory.observability import agent_task

async def my_agent_function():
    async with agent_task(
        agent_id='my-agent-123',
        task_name='Deploy Feature X',
        repo_scope='agent-factory'
    ) as ctx:
        # Post checkpoints
        await ctx.checkpoint('Reading files', progress=20)
        await ctx.checkpoint('Running tests', progress=50)
        await ctx.checkpoint('Creating PR', progress=80)

        # Track artifacts
        ctx.add_artifact('https://github.com/user/repo/pull/123')

        # Update token usage
        ctx.update_tokens(150000)
```

### 5. Start Supervisor Server (Optional)

For Slack webhooks and slash commands:

```bash
poetry run uvicorn agent_factory.observability.server:create_app --factory --port 3001
```

Or use systemd service:
```bash
sudo cp rivet/supervisor.service /etc/systemd/system/
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

## Usage Patterns

### Pattern 1: Context Manager (Recommended)

```python
from agent_factory.observability import agent_task

async with agent_task('agent-id', 'Task Name') as ctx:
    await ctx.checkpoint('Step 1', progress=25)
    await ctx.checkpoint('Step 2', progress=50, force=True)  # Force immediate post
    ctx.add_artifact('output.txt')
    ctx.update_tokens(50000)
```

### Pattern 2: Decorator

```python
from agent_factory.observability import supervised_agent

@supervised_agent(
    agent_id='refactor-agent',
    task_name='Refactor Auth Module',
    repo_scope='api-server'
)
async def refactor_auth(ctx):
    await ctx.checkpoint('Analyzing code', progress=30)
    # ... do work ...
    return result
```

### Pattern 3: Manual Supervisor

```python
from agent_factory.observability import get_supervisor, AgentCheckpoint, AgentStatus

supervisor = get_supervisor()

cp = AgentCheckpoint(
    agent_id='manual-agent',
    task_name='Manual Task',
    status=AgentStatus.WORKING,
    progress=50,
    tokens_used=10000,
    last_action='Processing data'
)

await supervisor.post_checkpoint(cp, force=True)
```

### Pattern 4: Sync Checkpoint Emitter (Subprocess Agents)

```python
from agent_factory.observability import SyncCheckpointEmitter

emitter = SyncCheckpointEmitter(
    agent_id='subprocess-agent',
    task_name='Background Job'
)

emitter.emit('Starting', status='starting', progress=0)
emitter.emit('Processing', status='working', progress=50)
emitter.emit('Done', status='complete', progress=100)
```

## Checkpoint Status Types

```python
class AgentStatus(str, Enum):
    STARTING = "starting"       # 🚀 Blue
    PLANNING = "planning"       # 🧠 Purple
    WORKING = "working"         # ⚙️ Green
    CHECKPOINT = "checkpoint"   # 📍 Yellow
    WAITING_APPROVAL = "waiting_approval"  # ⏳ Orange
    BLOCKED = "blocked"         # 🚧 Orange
    ERROR = "error"             # ❌ Red
    COMPLETE = "complete"       # ✅ Green
    CANCELLED = "cancelled"     # 🛑 Gray
```

## Database Schema

### agent_tasks
```sql
id UUID PRIMARY KEY
agent_id VARCHAR(255) UNIQUE  -- Agent identifier
task_type VARCHAR(50)         -- test, refactor, docs, etc.
task_name VARCHAR(500)        -- Human-readable task name
status VARCHAR(50)            -- pending, running, completed, failed
progress INTEGER              -- 0-100
slack_channel VARCHAR(50)     -- Slack channel ID
slack_thread_ts VARCHAR(50)   -- Slack thread timestamp
requested_by VARCHAR(50)      -- User ID who requested
created_at, started_at, completed_at TIMESTAMPTZ
result_summary TEXT
error_message TEXT
```

### agent_checkpoints
```sql
id UUID PRIMARY KEY
task_id UUID REFERENCES agent_tasks
agent_id VARCHAR(255)
checkpoint_type VARCHAR(50)   -- start, progress, complete, error
action_description TEXT       -- What the agent did
progress INTEGER              -- 0-100
tokens_used INTEGER
status VARCHAR(50)
elapsed_seconds INTEGER
error_message TEXT
```

## Slack Message Format

```
🚀 Agent `agent-id-123` – STARTING

Task: Deploy Feature X
Progress: 0%
Repo: agent-factory
Context: 0 / 200,000 (0.0%)
Last Action: Starting deployment
Elapsed: 0s
```

## Configuration

### Environment Variables

```bash
# Required for posting to Slack
SLACK_BOT_TOKEN=xoxb-...           # Bot User OAuth Token
SLACK_SIGNING_SECRET=...           # For webhook verification

# Optional (webhook alternative)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Database (required for audit trail)
DATABASE_URL=postgresql://...
```

### Supervisor Settings

```python
supervisor = SlackSupervisor(
    webhook_url="...",              # Alternative to bot token
    bot_token="...",                # For full API access
    default_channel="#agent-supervisory",
    min_checkpoint_interval=30      # Minimum seconds between posts
)
```

## Slack App Setup

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Agent Factory Supervisor"
4. Select workspace

### 2. Configure OAuth Scopes

Bot Token Scopes needed:
- `chat:write` - Post messages
- `chat:write.public` - Post to public channels
- `channels:read` - List channels
- `groups:read` - List private channels

### 3. Install App to Workspace

1. Go to "Install App" section
2. Click "Install to Workspace"
3. Copy "Bot User OAuth Token" → `SLACK_BOT_TOKEN`

### 4. Get Signing Secret

1. Go to "Basic Information"
2. Copy "Signing Secret" → `SLACK_SIGNING_SECRET`

### 5. Enable Events (Optional)

For interactive commands:
1. Go to "Event Subscriptions"
2. Enable Events
3. Request URL: `https://your-domain.com/slack/events`
4. Subscribe to bot events: `app_mention`, `message.channels`

### 6. Add Slash Command (Optional)

1. Go to "Slash Commands"
2. Create command: `/agent-task`
3. Request URL: `https://your-domain.com/slack/commands`

## Production Deployment

### VPS Deployment

```bash
# Copy files to VPS
scp -r agent_factory/observability/ root@vps:/root/Agent-Factory/agent_factory/
scp sql/supervisor_schema.sql root@vps:/root/Agent-Factory/sql/
scp rivet/supervisor.service root@vps:/etc/systemd/system/

# On VPS
ssh root@vps

# Deploy database schema
psql $DATABASE_URL -f /root/Agent-Factory/sql/supervisor_schema.sql

# Install dependencies
cd /root/Agent-Factory
poetry add asyncpg httpx

# Start service
systemctl daemon-reload
systemctl enable supervisor
systemctl start supervisor
systemctl status supervisor
```

### Health Check

```bash
curl http://localhost:3001/health
# {"status": "ok"}

curl http://localhost:3001/tasks
# [{"agent_id": "...", "status": "running", ...}]
```

## Monitoring

### View Active Tasks

```bash
curl http://localhost:3001/tasks?status=running
```

### View Agent Stats

```bash
curl http://localhost:3001/tasks/agent-id-123
# {
#   "task": {...},
#   "checkpoints": 15,
#   "artifacts": 3
# }
```

### View Daily Metrics

```bash
curl http://localhost:3001/metrics?days=7
# [
#   {"date": "2025-01-01", "total": 50, "completed": 45, "failed": 5, "avg_duration": 120.5},
#   ...
# ]
```

## Troubleshooting

### No Slack Messages Posting

1. Check credentials:
```bash
echo $SLACK_BOT_TOKEN
echo $SLACK_SIGNING_SECRET
```

2. Verify bot permissions: `chat:write`, `chat:write.public`

3. Check logs:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Database Connection Errors

```bash
# Test connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM agent_tasks;"

# Check schema exists
psql $DATABASE_URL -c "\dt agent_*"
```

### Context Usage Warnings

If you see "⚠️ Context Warning" in Slack:
- Agent is using >70% of token context (140k/200k)
- Consider summarization or context pruning
- Warning at 85% (170k/200k)

## Examples

### Example 1: RIVET Orchestrator (Already Integrated)

```python
# agent_factory/orchestrators/rivet_orchestrator.py

async with agent_task(
    agent_id=f"rivet-diagnose-{int(time.time())}",
    task_name=f"Diagnose {fault_code} on {equipment_type}",
    repo_scope="agent-factory",
) as ctx:
    await ctx.checkpoint(f"Starting diagnosis: {query}", progress=10)

    # Route to SME
    selected_route = self._detect_manufacturer(query, equipment_type, manufacturer)
    await ctx.checkpoint(f"Routed to {selected_route} SME", progress=30)

    # Call LLM
    await ctx.checkpoint(f"Calling {self.default_model} LLM", progress=50)
    response = self.client.chat.completions.create(...)

    # Return result
    await ctx.checkpoint("Diagnosis complete", progress=100)
    ctx.add_artifact(f"Route: {selected_route}")
```

### Example 2: Long-Running Background Job

```python
async def background_scraper():
    async with agent_task('scraper-001', 'Scrape 1000 URLs') as ctx:
        urls = get_urls()
        total = len(urls)

        for i, url in enumerate(urls):
            try:
                data = await scrape(url)
                progress = int((i + 1) / total * 100)
                await ctx.checkpoint(f"Scraped {url}", progress=progress)
                ctx.update_tokens(ctx._tokens_used + 500)
            except Exception as e:
                await ctx.checkpoint(f"Failed {url}: {e}", force=True)

        ctx.add_artifact(f"Scraped {total} URLs")
```

### Example 3: Multi-Agent Coordination

```python
async def orchestrate_deployment():
    async with agent_task('deploy-orchestrator', 'Deploy App v2.0') as main_ctx:
        await main_ctx.checkpoint('Starting deployment', progress=10)

        # Test agent
        async with agent_task('test-agent', 'Run Tests') as test_ctx:
            await test_ctx.checkpoint('Running unit tests', progress=50)
            await test_ctx.checkpoint('Tests passed', progress=100)

        await main_ctx.checkpoint('Tests complete', progress=40)

        # Build agent
        async with agent_task('build-agent', 'Build Docker Image') as build_ctx:
            await build_ctx.checkpoint('Building image', progress=50)
            await build_ctx.checkpoint('Image built', progress=100)

        await main_ctx.checkpoint('Build complete', progress=70)

        # Deploy agent
        async with agent_task('deploy-agent', 'Deploy to K8s') as deploy_ctx:
            await deploy_ctx.checkpoint('Applying manifests', progress=50)
            await deploy_ctx.checkpoint('Deployment successful', progress=100)

        await main_ctx.checkpoint('Deployment complete', progress=100)
        main_ctx.add_artifact('https://app.example.com')
```

## Roadmap

- [x] Basic checkpoint posting
- [x] Database audit trail
- [x] Slack threading
- [x] Context warnings
- [x] Error alerting
- [ ] Interactive buttons (Approve/Cancel)
- [ ] Human-in-loop approval flow
- [ ] Slack slash commands
- [ ] Agent metrics dashboard
- [ ] Cost tracking per agent
- [ ] Anomaly detection
- [ ] Agent health scoring

## License

Part of Agent Factory - MIT License
