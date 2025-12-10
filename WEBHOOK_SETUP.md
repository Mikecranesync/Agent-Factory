# GitHub Webhook → Orchestrator Setup Guide

Complete guide for setting up the GitHub Webhook automation system for Agent Factory.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [GitHub Webhook Configuration](#github-webhook-configuration)
- [Local Testing with ngrok](#local-testing-with-ngrok)
- [Production Deployment](#production-deployment)
- [Workflow Examples](#workflow-examples)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

```
GitHub Event → Webhook Handler → Supabase Queue → Orchestrator → Agents
   (push)         (FastAPI)        (agent_jobs)      (24/7 loop)   (execution)
```

**Components:**

1. **webhook_handler.py** - FastAPI server that receives GitHub webhooks
   - Validates HMAC signatures for security
   - Creates jobs in Supabase queue
   - Provides manual trigger endpoint for testing

2. **orchestrator.py** - Background process that runs 24/7
   - Polls Supabase for pending jobs every 60 seconds
   - Runs git pull to stay synchronized
   - Routes jobs to appropriate agents
   - Updates job status and handles errors

3. **Supabase Tables**:
   - `agent_jobs` - Job queue with status tracking
   - `webhook_events` - Audit trail of all webhook events

## Quick Start

### 1. Install Dependencies

```bash
poetry install
```

This will install FastAPI, uvicorn, and all other required dependencies.

### 2. Set Up Supabase

Run the migration in your Supabase SQL editor:

```bash
cat docs/supabase_migrations_orchestrator.sql
```

Copy and execute the SQL in Supabase dashboard → SQL Editor.

### 3. Configure Environment

Copy `.env.example` to `.env` and set:

```bash
# Generate a secure webhook secret (at least 20 characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env:
GITHUB_WEBHOOK_SECRET=your-generated-secret-here

# Configure Supabase (if not already set)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Optional orchestrator settings
ORCHESTRATOR_LOG_LEVEL=INFO
TICK_INTERVAL_SECONDS=60
GIT_SYNC_ENABLED=true
MAX_CONCURRENT_JOBS=3
```

### 4. Start Webhook Handler

```bash
python webhook_handler.py
```

The server will start on `http://localhost:8000`

### 5. Start Orchestrator (in another terminal)

```bash
python orchestrator.py
```

The orchestrator will run continuously, checking for jobs every 60 seconds.

### 6. Test Manual Trigger

```bash
# Test webhook handler is working
curl -X POST http://localhost:8000/webhook/manual

# Check health
curl http://localhost:8000/health
```

## Detailed Setup

### Prerequisites

- Python 3.10+
- Poetry installed
- Supabase project with connection credentials
- GitHub repository with admin access (for webhook configuration)

### Database Setup

The migration creates two tables:

**agent_jobs:**
- Stores jobs created by webhooks
- Status: pending → running → completed/failed
- Priority-based queue (higher priority = processed first)

**webhook_events:**
- Audit trail of all webhook events received
- Tracks whether event was converted to job

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_WEBHOOK_SECRET` | Yes | - | Secret for HMAC signature verification (min 20 chars) |
| `SUPABASE_URL` | Yes | - | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | - | Your Supabase service key |
| `ORCHESTRATOR_LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TICK_INTERVAL_SECONDS` | No | 60 | How often orchestrator checks for jobs |
| `GIT_SYNC_ENABLED` | No | true | Whether to run git pull each cycle |
| `MAX_CONCURRENT_JOBS` | No | 3 | Max concurrent job processing |

## GitHub Webhook Configuration

### Step 1: Start webhook_handler.py

The webhook handler must be accessible from the internet. See [Local Testing](#local-testing-with-ngrok) or [Production Deployment](#production-deployment).

### Step 2: Configure GitHub Webhook

1. Go to your GitHub repository → Settings → Webhooks → Add webhook

2. Configure webhook:
   - **Payload URL**: `https://your-domain.com/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Your `GITHUB_WEBHOOK_SECRET` value
   - **SSL verification**: Enable

3. Select events to trigger:
   - ☑️ Pushes
   - ☑️ Releases
   - ☑️ Issues
   - ☑️ Pull requests
   - (Or select "Send me everything" for all events)

4. Ensure webhook is Active

5. Click "Add webhook"

### Step 3: Test Webhook

1. Make a test push to your repository or create a test issue

2. Check webhook delivery in GitHub:
   - Repository → Settings → Webhooks → Recent Deliveries
   - Should show 200 OK response

3. Verify job created in Supabase:
   ```sql
   SELECT * FROM agent_jobs ORDER BY created_at DESC LIMIT 10;
   ```

## Local Testing with ngrok

For local development, use ngrok to expose your webhook handler:

### Install ngrok

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/download
```

### Start ngrok Tunnel

```bash
# Start webhook handler
python webhook_handler.py

# In another terminal, start ngrok
ngrok http 8000
```

### Configure GitHub Webhook with ngrok URL

Use the ngrok URL in GitHub webhook configuration:
```
https://abc123.ngrok.io/webhook/github
```

### Test with Manual Trigger

```bash
# Test manual endpoint
curl -X POST https://abc123.ngrok.io/webhook/manual

# Or test locally
curl -X POST http://localhost:8000/webhook/manual
```

## Production Deployment

### Option 1: tmux (Simple)

Run orchestrator in background with tmux:

```bash
# Start webhook handler in tmux
tmux new -s webhook "poetry run python webhook_handler.py"

# Start orchestrator in tmux
tmux new -s orchestrator "poetry run python orchestrator.py"

# Detach from tmux: Ctrl+b then d
# Reattach: tmux attach -t orchestrator
```

### Option 2: systemd (Linux)

Create service files for automatic startup:

**webhook_handler.service:**

```ini
[Unit]
Description=Agent Factory Webhook Handler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/agent-factory
Environment="PATH=/path/to/poetry/bin:/usr/bin"
ExecStart=/path/to/poetry run python webhook_handler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**orchestrator.service:**

```ini
[Unit]
Description=Agent Factory Orchestrator
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/agent-factory
Environment="PATH=/path/to/poetry/bin:/usr/bin"
ExecStart=/path/to/poetry run python orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo cp webhook_handler.service /etc/systemd/system/
sudo cp orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable webhook_handler orchestrator
sudo systemctl start webhook_handler orchestrator

# Check status
sudo systemctl status webhook_handler
sudo systemctl status orchestrator
```

### Option 3: Docker

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install poetry
RUN poetry install --no-dev

# Webhook handler
EXPOSE 8000
CMD ["poetry", "run", "python", "webhook_handler.py"]
```

```bash
# Build and run
docker build -t agent-factory-webhook .
docker run -p 8000:8000 --env-file .env agent-factory-webhook

# Run orchestrator in separate container
docker run --env-file .env agent-factory-webhook poetry run python orchestrator.py
```

### Reverse Proxy (nginx)

For production, use nginx to proxy requests to webhook handler:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Workflow Examples

### Example 1: Push Event → Code Review

**Trigger:** Push to main branch

**Workflow:**
1. Developer pushes code to GitHub
2. GitHub sends webhook to webhook_handler.py
3. Handler creates job: `{"job_type": "github_push", "payload": {...}}`
4. Orchestrator picks up job
5. Routes to code review agent
6. Agent analyzes diff, posts review comment
7. Job marked as completed

### Example 2: Release Event → Deployment

**Trigger:** New release created

**Workflow:**
1. User creates release on GitHub
2. Webhook → job created
3. Orchestrator routes to deployment agent
4. Agent runs deployment scripts
5. Posts status to Telegram
6. Job marked as completed

### Example 3: Issue Event → Agent Assignment

**Trigger:** Issue labeled "agent-task"

**Workflow:**
1. Issue labeled with "agent-task"
2. Webhook → job created
3. Orchestrator routes to task agent
4. Agent reads issue, creates implementation plan
5. Opens PR with solution
6. Comments on original issue with PR link

### Example 4: Manual Trigger

**Trigger:** Manual API call

```bash
curl -X POST http://localhost:8000/webhook/manual \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "custom_task",
    "payload": {
      "task": "Update documentation",
      "files": ["README.md"]
    }
  }'
```

## Troubleshooting

### Webhook Handler Issues

**Problem: Webhook returns 401 Unauthorized**

Solution: Check GITHUB_WEBHOOK_SECRET matches in both .env and GitHub webhook configuration.

```bash
# Verify secret is set
echo $GITHUB_WEBHOOK_SECRET

# Generate new secret if needed
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Problem: Webhook returns 500 Internal Server Error**

Solution: Check webhook handler logs and Supabase connection.

```bash
# Check logs
python webhook_handler.py  # Will show detailed errors

# Verify Supabase connection
python -c "from agent_factory.memory.storage import SupabaseMemoryStorage; s = SupabaseMemoryStorage(); print('Connected')"
```

**Problem: Webhook not receiving events**

Solution:
1. Check GitHub webhook Recent Deliveries for error messages
2. Verify webhook URL is accessible from internet
3. Check firewall settings
4. Test with curl:

```bash
curl -X POST http://localhost:8000/webhook/manual
```

### Orchestrator Issues

**Problem: Orchestrator not processing jobs**

Solution: Check orchestrator logs and job status in database.

```bash
# Check if orchestrator is running
ps aux | grep orchestrator

# Check logs
python orchestrator.py  # Will show detailed logs

# Check pending jobs in database
psql -d your-db -c "SELECT * FROM agent_jobs WHERE status = 'pending';"
```

**Problem: Jobs stuck in "running" state**

Solution: Jobs may have crashed. Check error logs and reset status.

```sql
-- Find stuck jobs
SELECT * FROM agent_jobs WHERE status = 'running' AND started_at < NOW() - INTERVAL '1 hour';

-- Reset stuck jobs
UPDATE agent_jobs SET status = 'failed', error = 'Job timeout' WHERE status = 'running' AND started_at < NOW() - INTERVAL '1 hour';
```

**Problem: Git sync failing**

Solution: Check git configuration and repository access.

```bash
# Test git pull manually
cd /path/to/agent-factory
git pull

# If git pull fails, check SSH keys or credentials
ssh -T git@github.com

# Disable git sync temporarily
export GIT_SYNC_ENABLED=false
python orchestrator.py
```

### Database Issues

**Problem: Cannot connect to Supabase**

Solution: Verify Supabase credentials and network access.

```bash
# Test connection
python -c "
from agent_factory.memory.storage import SupabaseMemoryStorage
import os
print(f'URL: {os.getenv(\"SUPABASE_URL\")}')
print(f'Key: {os.getenv(\"SUPABASE_KEY\")[:10]}...')
storage = SupabaseMemoryStorage()
print('Connected successfully')
"
```

**Problem: Tables not found**

Solution: Run migration script.

```bash
# Check if tables exist
psql -d your-db -c "\dt agent_jobs webhook_events"

# Run migration
cat docs/supabase_migrations_orchestrator.sql | psql -d your-db
```

### Testing Checklist

- [ ] Webhook handler starts without errors: `python webhook_handler.py`
- [ ] Orchestrator starts without errors: `python orchestrator.py`
- [ ] Health endpoint returns OK: `curl http://localhost:8000/health`
- [ ] Manual trigger creates job: `curl -X POST http://localhost:8000/webhook/manual`
- [ ] Job appears in database: `SELECT * FROM agent_jobs`
- [ ] Orchestrator picks up and processes job
- [ ] GitHub webhook delivers successfully (check Recent Deliveries)
- [ ] Job status updates to "completed" or "failed"

### Monitoring

**Check webhook handler status:**

```bash
curl http://localhost:8000/health
```

**Check orchestrator heartbeat:**

```sql
SELECT * FROM webhook_events WHERE event_type = 'heartbeat' ORDER BY received_at DESC LIMIT 1;
```

**Monitor job queue:**

```sql
-- Job statistics
SELECT status, COUNT(*) FROM agent_jobs GROUP BY status;

-- Recent jobs
SELECT * FROM agent_jobs ORDER BY created_at DESC LIMIT 10;

-- Failed jobs
SELECT * FROM agent_jobs WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;
```

## Security Best Practices

1. **Use strong webhook secret** (minimum 20 characters)
2. **Enable SSL verification** in GitHub webhook settings
3. **Use environment variables** for secrets (never commit .env)
4. **Restrict Supabase key permissions** (use service key with limited access)
5. **Monitor webhook events** for suspicious activity
6. **Use HTTPS in production** (nginx + Let's Encrypt)
7. **Implement rate limiting** for webhook endpoints (optional)

## Next Steps

1. **Customize job types**: Edit webhook_handler.py to add custom job types
2. **Add more agents**: Create specialized agents for different job types
3. **Add monitoring**: Integrate with monitoring tools (Sentry, DataDog, etc.)
4. **Add notifications**: Send Telegram/Slack notifications for job status
5. **Scale horizontally**: Run multiple orchestrator instances with job locking

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Webhooks Guide](https://docs.github.com/en/webhooks)
- [Supabase Documentation](https://supabase.com/docs)
- [ngrok Documentation](https://ngrok.com/docs)

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Check existing issues for solutions
- Review the troubleshooting section above

---

**Generated with Agent Factory** - Autonomous agent automation system
