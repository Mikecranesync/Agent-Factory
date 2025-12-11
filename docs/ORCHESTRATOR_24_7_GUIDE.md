# Master Orchestrator - 24/7 Autonomous Production

## Overview

The MasterOrchestratorAgent is the "CEO" of your autonomous video production system. It runs 24/7, scheduling and executing all agents on time-based and dependency-based triggers.

## Architecture

```
MasterOrchestratorAgent (24/7 Daemon)
├── Task Scheduler (Cron-style)
├── Dependency Manager
├── Execution Engine
├── Retry Handler
├── Health Monitor
└── Metrics Tracker
```

## Production Schedule

### Daily Tasks

**00:00 UTC - Content Curation**
- ContentCuratorAgent selects next topic from 90-day calendar
- Priority: HIGH
- Duration: ~10 seconds

**Every 4 Hours - Video Production Pipeline**
- 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
- Produces 6 videos/day (target: 3/day minimum)

Pipeline:
```
1. ScriptwriterAgent (4 min)
   ↓
2. InstructionalDesignerAgent (1 min)
   ↓
3. VoiceProductionAgent (2 min)
   ↓
4. VideoAssemblyAgent (3 min)
   ↓
5. VideoQualityReviewerAgent (30 sec)
   ↓
6. QualityReviewCommittee (10 sec)
   ↓
7. ABTestOrchestratorAgent (1 min)
```

**12:00 UTC - YouTube Upload Batch**
- Upload all approved videos from previous 12 hours
- Creates A/B/C test variants
- Publishes with optimized metadata

### Every 6 Hours - Analytics

**00:00, 06:00, 12:00, 18:00 UTC**
- AnalyticsCommittee reviews performance metrics
- Identifies winning A/B test variants
- Flags underperforming videos
- Generates optimization recommendations

### Weekly Tasks

**Sunday 00:00 UTC - Style Guide Update**
- TrendScoutAgent analyzes latest viral patterns
- Updates CHANNEL_STYLE_GUIDE.md
- Design Committee reviews changes

**Sunday 06:00 UTC - Gap Analysis**
- ContentCuratorAgent analyzes knowledge coverage
- Identifies missing topics
- Prioritizes content backfill

## Quick Start

### Option 1: Manual Start (Testing)

```bash
# Run orchestrator in foreground
poetry run python agents/orchestration/master_orchestrator_agent.py

# Or use batch file (Windows)
scripts\run_orchestrator_24_7.bat
```

### Option 2: Windows Task Scheduler (24/7 Auto-Start)

1. Open Task Scheduler
2. Create Basic Task → "Agent Factory Orchestrator"
3. Trigger: At startup
4. Action: Start a program
5. Program: `C:\Users\hharp\OneDrive\Desktop\Agent Factory\scripts\run_orchestrator_24_7.bat`
6. Settings:
   - Run whether user is logged on or not
   - Run with highest privileges
   - If task fails, restart every: 1 minute
   - Attempt to restart up to: 999 times

### Option 3: Linux/Mac systemd (Production)

```bash
# Create service file
sudo nano /etc/systemd/system/agent-factory-orchestrator.service
```

```ini
[Unit]
Description=Agent Factory Master Orchestrator
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/Agent Factory
ExecStart=/usr/bin/poetry run python agents/orchestration/master_orchestrator_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable agent-factory-orchestrator
sudo systemctl start agent-factory-orchestrator

# Check status
sudo systemctl status agent-factory-orchestrator

# View logs
sudo journalctl -u agent-factory-orchestrator -f
```

## Task Configuration

### Task Structure

```python
Task(
    task_id="script_generation_4h",
    agent_name="ScriptwriterAgent",
    action="generate_script",
    priority=TaskPriority.HIGH,
    schedule="0 */4 * * *",  # Cron expression
    dependencies=["content_curation_daily"],
    retry_count=0,
    max_retries=3,
    timeout_seconds=600
)
```

### Cron Schedule Format

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, Sunday=0)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Examples:**
- `0 0 * * *` - Daily at midnight
- `0 */4 * * *` - Every 4 hours
- `0 12 * * *` - Daily at noon
- `0 0 * * 0` - Weekly on Sunday at midnight

### Dependencies

Tasks can depend on other tasks completing first:

```python
# This task runs immediately after script_generation_4h completes
Task(
    task_id="instructional_design",
    schedule="immediate",
    dependencies=["script_generation_4h"]
)
```

## Monitoring

### Logs

All activity logged to:
- `data/logs/master_orchestrator.log` - Main log file
- `data/logs/health_YYYYMMDD.json` - Daily health reports

### Health Checks

Every hour, orchestrator performs health check:
```json
{
  "timestamp": "2025-12-11T22:00:00Z",
  "uptime_hours": 48.5,
  "task_queue_size": 12,
  "active_tasks": 2,
  "completed_tasks": 145,
  "failed_tasks": 3,
  "metrics": {
    "videos_produced_today": 18,
    "videos_produced_total": 245,
    "tasks_completed": 145,
    "tasks_failed": 3
  }
}
```

### Metrics Dashboard

Key metrics tracked:
- **Videos Produced Today**: Current 24-hour count
- **Videos Produced Total**: All-time count
- **Tasks Completed**: Successful task executions
- **Tasks Failed**: Failed tasks (after retries)
- **Uptime Hours**: Continuous runtime
- **Last Health Check**: Most recent health check timestamp

## Failure Handling

### Retry Logic

Failed tasks automatically retry with exponential backoff:
1. First retry: 1 minute wait
2. Second retry: 2 minutes wait
3. Third retry: 4 minutes wait
4. After 3 retries: Mark as FAILED PERMANENTLY

### Task States

- `PENDING` - Waiting for schedule/dependencies
- `IN_PROGRESS` - Currently executing
- `COMPLETED` - Successfully finished
- `FAILED` - Failed after max retries
- `RETRYING` - Waiting to retry
- `CANCELLED` - Manually cancelled

### Common Failures

**ScriptwriterAgent timeout:**
- Cause: Knowledge base query slow
- Solution: Increase timeout_seconds to 900 (15 min)

**VoiceProductionAgent failure:**
- Cause: Edge-TTS network issue
- Solution: Automatic retry (usually resolves)

**YouTubeUploaderAgent quota exceeded:**
- Cause: Daily API quota limit
- Solution: Wait 24 hours, videos queued for next cycle

## Production Targets

**Daily:**
- Minimum: 3 videos
- Target: 6 videos
- Maximum: 12 videos (if all cycles succeed)

**Monthly:**
- Minimum: 90 videos (90-day calendar)
- Target: 180 videos
- Maximum: 360 videos

**Annual:**
- Minimum: 1,080 videos
- Target: 2,160 videos

## Commands

### Start Orchestrator

```bash
# Foreground (testing)
poetry run python agents/orchestration/master_orchestrator_agent.py

# Background (Linux/Mac)
nohup poetry run python agents/orchestration/master_orchestrator_agent.py &

# Background (Windows)
start /B poetry run python agents/orchestration/master_orchestrator_agent.py
```

### Stop Orchestrator

```bash
# Graceful stop (Ctrl+C in foreground)
# Waits for active tasks to complete (max 5 minutes)

# Force stop (Linux/Mac)
pkill -f master_orchestrator_agent.py

# Force stop (Windows)
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *master_orchestrator*"
```

### View Logs

```bash
# Tail live log
tail -f data/logs/master_orchestrator.log

# View today's health
cat data/logs/health_$(date +%Y%m%d).json

# Check orchestrator state
cat data/tasks/orchestrator_state.json
```

## Customization

### Add New Scheduled Task

Edit `master_orchestrator_agent.py`, add to `_create_default_schedule()`:

```python
schedule.append(Task(
    task_id="my_custom_task",
    agent_name="MyCustomAgent",
    action="my_action",
    priority=TaskPriority.MEDIUM,
    schedule="0 */2 * * *",  # Every 2 hours
    dependencies=[]
))
```

### Change Production Schedule

Modify cron expressions:

```python
# Change from every 4 hours to every 2 hours
schedule="0 */2 * * *"

# Change from daily at noon to daily at 6 AM
schedule="0 6 * * *"
```

### Adjust Retry Behavior

```python
# Allow more retries
max_retries=5

# Increase timeout
timeout_seconds=1200  # 20 minutes
```

## Troubleshooting

### Orchestrator won't start

```bash
# Check Python environment
poetry run python --version

# Check dependencies
poetry install

# Check logs directory exists
mkdir -p data/logs data/tasks data/schedules
```

### Tasks stuck in PENDING

- Check dependencies are met
- Verify schedule is correct (cron expression)
- Check orchestrator is running (`ps aux | grep master_orchestrator`)

### High failure rate

- Review `data/logs/master_orchestrator.log`
- Check individual agent logs
- Verify knowledge base is accessible
- Check disk space for videos
- Verify network connectivity (Edge-TTS, YouTube API)

### Memory usage growing

- Restart orchestrator weekly (automatic via systemd)
- Clear old completed tasks (keep last 100)
- Rotate logs daily

## Performance Optimization

### Reduce Task Queue Size

```python
# Only keep recent completed tasks
if len(self.completed_tasks) > 100:
    self.completed_tasks = self.completed_tasks[-100:]
```

### Parallel Execution

Currently sequential. For parallel:

```python
# Execute multiple tasks concurrently
await asyncio.gather(*[self._execute_task(t) for t in due_tasks])
```

### Resource Limits

```python
# Limit concurrent tasks
max_concurrent_tasks = 3
if len(self.active_tasks) >= max_concurrent_tasks:
    continue  # Skip new tasks
```

## Security

### Secrets Management

Never hardcode secrets in orchestrator:

```python
# Use environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
```

### Access Control

Run as dedicated user (not root):

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash agent-factory

# Set ownership
sudo chown -R agent-factory:agent-factory /path/to/Agent-Factory

# Run as user
sudo -u agent-factory poetry run python agents/orchestration/master_orchestrator_agent.py
```

### Rate Limiting

Built-in rate limiting:
- Max 3 retries per task
- 1-minute minimum between iterations
- 60-second retry backoff

## Cost Analysis

**24/7 Operation Cost: $0.00/month**

- Edge-TTS: FREE (unlimited)
- FFmpeg: FREE (local processing)
- Supabase: FREE tier (500 MB)
- YouTube API: FREE (10,000 quota/day)
- Compute: Local machine (already owned)

**At Scale (1,000 videos/month):**
- Still $0.00 (all tools remain free at this volume)

## Next Steps

1. **Start orchestrator**: Run `scripts\run_orchestrator_24_7.bat`
2. **Monitor logs**: Watch `data/logs/master_orchestrator.log`
3. **Check health**: Review `data/logs/health_*.json` hourly
4. **Verify videos**: Check `data/videos/` for new content
5. **Review metrics**: Track daily production count

## Support

**Common Issues:**
- Task stuck: Check dependencies met
- High failure rate: Review agent logs
- No videos produced: Verify ContentCuratorAgent has topics

**Debugging:**
- Enable verbose logging: `logger.setLevel(logging.DEBUG)`
- Run single task: `await orchestrator._execute_task(task)`
- Dry run mode: Set `task.timeout_seconds = 1` to simulate

---

**Generated:** 2025-12-11
**Version:** 1.0
**Author:** MasterOrchestratorAgent
