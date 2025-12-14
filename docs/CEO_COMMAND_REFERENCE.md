# CEO/Executive Command Reference

**Agent Factory Management Dashboard - Telegram Commands**

**Version:** 1.0
**Date:** 2025-12-14
**Access:** Restricted to authorized Telegram users

---

## Quick Command List

```
MONITORING
/status  - Overall system health
/agents  - List all 24 agents
/metrics - Performance KPIs
/errors  - Recent error log

CONTENT APPROVAL
/pending      - Videos awaiting approval
/approve <id> - Approve video for publishing
/reject <id> <reason> - Reject with feedback

AGENT CONTROL
/pause <agent>   - Pause agent execution
/resume <agent>  - Resume paused agent
/restart <agent> - Restart failed agent

REPORTS
/daily   - Daily KPI summary
/weekly  - Weekly performance report
/monthly - Monthly business metrics

CONFIGURATION
/config - View system configuration
/backup - Trigger database backup
```

---

## System Monitoring Commands

### `/status` - System Health Check

**Purpose:** Get overall system status at a glance

**Output:**
```
SYSTEM STATUS REPORT
Generated: 2025-12-14 15:30:00

Agent Factory
├─ 24/24 agents validated
├─ All imports working
└─ Ready for production

Database
├─ Provider: Neon (primary)
├─ Connection: OK
└─ Failover: Enabled (Supabase ready)

Knowledge Base
├─ Total atoms: 1,964
├─ Embeddings: Complete
└─ Vector search: Enabled

APIs
├─ OpenAI: OK ($1.23/mo)
├─ Anthropic: OK ($4.87/mo)
└─ YouTube: Configured

Voice Production
└─ Edge-TTS (FREE)

Estimated monthly cost: $6.10
```

**When to use:**
- Daily morning check
- After system changes
- Before major deployments

---

### `/agents` - Agent Status List

**Purpose:** View status of all 24 agents

**Output:**
```
AGENT STATUS (24 agents)

EXECUTIVE TEAM (2)
  [STOPPED]  AICEOAgent
  [STOPPED]  AIChiefOfStaffAgent

RESEARCH TEAM (6)
  [STOPPED]  ResearchAgent
  [STOPPED]  AtomBuilderAgent
  [STOPPED]  AtomLibrarianAgent
  [STOPPED]  QualityCheckerAgent
  [STOPPED]  OEMPDFScraperAgent
  [STOPPED]  AtomBuilderFromPDF

CONTENT TEAM (8)
  [STOPPED]  MasterCurriculumAgent
  [STOPPED]  ContentStrategyAgent
  [STOPPED]  ScriptwriterAgent
  [STOPPED]  SEOAgent
  [STOPPED]  ThumbnailAgent
  [STOPPED]  ContentCuratorAgent
  [STOPPED]  TrendScoutAgent
  [STOPPED]  VideoQualityReviewerAgent

MEDIA TEAM (4)
  [STOPPED]  VoiceProductionAgent
  [STOPPED]  VideoAssemblyAgent
  [STOPPED]  PublishingStrategyAgent
  [STOPPED]  YouTubeUploaderAgent

ENGAGEMENT TEAM (3)
  [STOPPED]  CommunityAgent
  [STOPPED]  AnalyticsAgent
  [STOPPED]  SocialAmplifierAgent

ORCHESTRATION (1)
  [STOPPED]  MasterOrchestratorAgent
```

**Agent Status Codes:**
- `[RUNNING]` - Agent actively executing
- `[PAUSED]` - Manually paused (use /resume)
- `[ERROR]` - Failed execution (use /restart)
- `[STOPPED]` - Not currently running

**When to use:**
- Check which agents are active
- Identify failed agents
- Verify agent deployments

---

### `/metrics` - Performance KPIs

**Purpose:** View key performance indicators

**Output:**
```
PERFORMANCE METRICS

CONTENT PRODUCTION
├─ Videos in queue: 3
├─ Videos published (today): 0
├─ Videos published (week): 0
└─ Average quality score: N/A

AGENT EXECUTION
├─ Total runs (24h): 0
├─ Success rate: N/A
├─ Average execution time: N/A
└─ Failed executions: 0

SYSTEM HEALTH
├─ Uptime: 99.9%
├─ API response time: <200ms
└─ Database query time: <50ms

COSTS (MTD)
├─ OpenAI API: $1.23
├─ Anthropic API: $4.87
└─ Total: $6.10 / $50 budget (12%)
```

**When to use:**
- Weekly performance reviews
- Budget tracking
- Quality monitoring

---

### `/errors` - Recent Error Log

**Purpose:** View recent errors and failures

**Output:**
```
RECENT ERRORS (Last 24h)

No errors logged in the last 24 hours.

All systems operational.
```

**Or (if errors exist):**
```
RECENT ERRORS (Last 24h)

[2025-12-14 14:23:15] [ERROR] ScriptwriterAgent
  Error: OpenAI API timeout
  Impact: Script generation delayed
  Action: Retry successful

[2025-12-14 12:45:30] [WARNING] DatabaseManager
  Warning: Neon connection slow (5.2s)
  Impact: None (failover ready)
  Action: None required
```

**When to use:**
- Troubleshooting issues
- Identifying patterns
- Before major deployments

---

## Content Approval Workflow

### `/pending` - Videos Awaiting Approval

**Purpose:** View all videos pending CEO review

**Output:**
```
PENDING VIDEO APPROVALS (3)

Video ID: abc123
├─ Title: "What is a PLC? - Complete Guide"
├─ Duration: 5m 23s
├─ Quality Score: 0.92 / 1.00
├─ Submitted: 2025-12-14 13:00:00
├─ Priority: NORMAL
└─ Actions: /approve abc123 | /reject abc123

Video ID: def456
├─ Title: "Top 5 PLC Programming Mistakes"
├─ Duration: 7m 45s
├─ Quality Score: 0.88 / 1.00
├─ Submitted: 2025-12-14 12:30:00
├─ Priority: HIGH
└─ Actions: /approve def456 | /reject def456

Video ID: ghi789
├─ Title: "Allen-Bradley vs Siemens PLCs"
├─ Duration: 6m 12s
├─ Quality Score: 0.95 / 1.00
├─ Submitted: 2025-12-14 11:00:00
├─ Priority: NORMAL
└─ Actions: /approve ghi789 | /reject ghi789
```

**Priority Levels:**
- `URGENT` - Time-sensitive (breaking news, hot topic)
- `HIGH` - Important but not urgent
- `NORMAL` - Standard content
- `LOW` - Evergreen content, no rush

**When to use:**
- Daily approval workflow
- Before scheduled publishing times
- When approval alerts arrive

---

### `/approve <video_id>` - Approve Video

**Purpose:** Approve video for YouTube publishing

**Usage:**
```
/approve abc123
```

**Output:**
```
VIDEO APPROVED

Video ID: abc123
Title: "What is a PLC? - Complete Guide"
Status: APPROVED → Publishing queue

Actions taken:
1. Status updated to 'approved'
2. Queued for YouTubeUploaderAgent
3. Publishing scheduled for optimal time

Estimated publish time: 2025-12-14 18:00:00 (peak hours)

You will receive notification when published.
```

**When to use:**
- After reviewing video preview
- When quality score >0.85
- When content aligns with strategy

---

### `/reject <video_id> <reason>` - Reject Video

**Purpose:** Reject video with feedback for re-production

**Usage:**
```
/reject abc123 Audio narration too fast, reduce pace by 20%
```

**Output:**
```
VIDEO REJECTED

Video ID: abc123
Title: "What is a PLC? - Complete Guide"
Status: REJECTED

Reason: Audio narration too fast, reduce pace by 20%

Actions taken:
1. Status updated to 'rejected'
2. Feedback sent to VideoQualityReviewerAgent
3. Video queued for re-production

The agent will:
- Adjust narration pace
- Re-render video
- Submit for re-approval

Expected re-submission: ~2 hours
```

**When to use:**
- Quality score <0.85
- Content inaccuracies
- Audio/visual issues
- SEO optimization needed

**Common rejection reasons:**
- "Audio too fast/slow"
- "Thumbnail not eye-catching"
- "Script lacks depth on [topic]"
- "SEO keywords missing"
- "Visuals don't match narration"

---

## Agent Control Commands

### `/pause <agent_name>` - Pause Agent

**Purpose:** Temporarily stop agent execution

**Usage:**
```
/pause ScriptwriterAgent
```

**Output:**
```
AGENT PAUSED

Agent: ScriptwriterAgent
Team: Content
Previous status: RUNNING
New status: PAUSED

The agent will not execute until resumed.

To resume: /resume ScriptwriterAgent
```

**When to use:**
- System maintenance
- Testing new features
- Temporarily reduce costs
- Debugging issues

**⚠️ WARNING:**
- Pausing content agents may delay publishing schedule
- Pausing engagement agents may reduce viewer interaction

---

### `/resume <agent_name>` - Resume Agent

**Purpose:** Resume paused agent execution

**Usage:**
```
/resume ScriptwriterAgent
```

**Output:**
```
AGENT RESUMED

Agent: ScriptwriterAgent
Team: Content
Previous status: PAUSED
New status: RUNNING

The agent will resume normal execution.

Next scheduled run: 2025-12-14 16:00:00
```

**When to use:**
- After maintenance complete
- When ready to resume normal operations

---

### `/restart <agent_name>` - Restart Failed Agent

**Purpose:** Restart agent after error/failure

**Usage:**
```
/restart VideoAssemblyAgent
```

**Output:**
```
AGENT RESTARTED

Agent: VideoAssemblyAgent
Team: Media
Previous status: ERROR
New status: RUNNING

Last error: FFmpeg rendering timeout
Error cleared: Yes

The agent has been restarted and will retry.

Monitor status: /agents
```

**When to use:**
- After agent fails
- After fixing configuration
- After API errors resolved

---

## Executive Reports

### `/daily` - Daily KPI Summary

**Purpose:** Morning/evening daily summary

**Output:**
```
DAILY KPI REPORT
Date: 2025-12-14

CONTENT PRODUCTION
├─ Videos published: 2
├─ Videos pending approval: 3
├─ Scripts generated: 5
└─ Average quality: 0.91 / 1.00

AGENT HEALTH
├─ Agents running: 8/24
├─ Success rate: 98.5%
├─ Failed executions: 1 (VideoAssemblyAgent - resolved)
└─ Average execution time: 2m 15s

ENGAGEMENT (Last 24h)
├─ New subscribers: 12
├─ Total views: 450
├─ Comments: 23 (18 replied by CommunityAgent)
└─ Engagement rate: 8.2%

COSTS (Today)
├─ OpenAI: $0.12
├─ Anthropic: $0.45
└─ Total: $0.57

TOP PERFORMING VIDEO (Today)
  "What is a PLC?" - 285 views, 8.9% engagement
```

**When to use:**
- Every morning (check overnight progress)
- Every evening (review day's output)
- Before investor calls

---

### `/weekly` - Weekly Performance Report

**Purpose:** Comprehensive weekly summary

**Output:**
```
WEEKLY PERFORMANCE REPORT
Week of: Dec 8-14, 2025

CONTENT MILESTONES
├─ Videos published: 15 (+25% vs last week)
├─ Total watch time: 2,450 minutes
├─ Average quality score: 0.89 / 1.00
└─ Topics covered: 12 unique

GROWTH METRICS
├─ New subscribers: 127 (+18%)
├─ Total subscribers: 850
├─ Total views: 3,200 (+22%)
└─ Watch time: +35%

TOP 3 VIDEOS (This Week)
1. "Top 5 PLC Mistakes" - 680 views, 12% engagement
2. "Allen-Bradley Tutorial" - 520 views, 10% engagement
3. "What is a PLC?" - 485 views, 9% engagement

AGENT PERFORMANCE
├─ Total executions: 456
├─ Success rate: 97.8%
├─ Fastest agent: SEOAgent (45s avg)
└─ Slowest agent: VideoAssemblyAgent (8m avg)

COSTS (Week)
├─ Total spent: $12.50
├─ Budget usage: 25% ($50/mo limit)
└─ Cost per video: $0.83

NEXT WEEK PROJECTIONS
├─ Videos planned: 18
├─ Estimated costs: $15
└─ Subscriber target: 1,000
```

**When to use:**
- Monday morning planning
- Weekly team meetings
- Progress tracking

---

### `/monthly` - Monthly Business Metrics

**Purpose:** High-level business performance

**Output:**
```
MONTHLY BUSINESS REPORT
Month: December 2025

REVENUE
├─ YouTube AdSense: $85 (first payout!)
├─ Premium subscriptions: $0 (launching Month 2)
├─ B2B inquiries: 3
└─ Total: $85

GROWTH
├─ Subscribers: 850 → 1,200 (+41%)
├─ Total views: 12,500 (+150%)
├─ Watch time: 8,200 minutes
└─ Engagement rate: 7.8%

CONTENT LIBRARY
├─ Videos published: 52
├─ Total watch time: 8,200 min
├─ Average view duration: 4m 12s
└─ Topics covered: 35 unique

AGENT AUTOMATION
├─ Total executions: 1,850
├─ Success rate: 97.2%
├─ Human approval rate: 92% (target: <10% by Month 6)
└─ Fully autonomous: 8% of videos

COSTS
├─ Infrastructure: $6/mo
├─ APIs: $18/mo
├─ Total: $24/mo
└─ Cost per video: $0.46

PROFITABILITY
├─ Revenue: $85
├─ Costs: $24
└─ Net profit: +$61 (first profitable month!)

GOALS FOR NEXT MONTH
├─ 2,000 subscribers (+67%)
├─ $200 revenue (+135%)
├─ 100 videos (+92%)
└─ 30% autonomous (no approval needed)
```

**When to use:**
- Month-end reviews
- Investor updates
- Strategic planning

---

## Configuration Commands

### `/config` - View Configuration

**Purpose:** View current system configuration

**Output:**
```
SYSTEM CONFIGURATION

DATABASE
├─ Primary provider: Neon
├─ Backup provider: Supabase
├─ Failover: Enabled
└─ Connection pool: 10 max

LLM PROVIDERS
├─ Default: OpenAI (gpt-4o)
├─ Fallback: Anthropic (claude-sonnet-3.5)
├─ Embeddings: OpenAI (text-embedding-3-small)
└─ Cost optimization: Enabled

VOICE PRODUCTION
├─ Mode: Edge-TTS (FREE)
├─ Voice: en-US-GuyNeural
└─ Upgrade path: ElevenLabs ($99/mo)

VIDEO SETTINGS
├─ Target duration: 5-7 minutes
├─ Resolution: 1080p
├─ Frame rate: 30fps
└─ Codec: H.264

APPROVAL WORKFLOW
├─ Auto-approve threshold: 0.95 quality score
├─ Human review required: <0.90 quality
├─ CEO approval: First 20 videos, then sample
└─ Rejection re-submission: Automatic

PUBLISHING STRATEGY
├─ Optimal upload times: 6PM-9PM EST
├─ Frequency: 2-3 videos/day
├─ Platform: YouTube (primary)
└─ Cross-posting: TikTok, Instagram (future)

SECURITY
├─ Authorized users: 1
├─ API rate limits: Enabled
├─ PII filtering: Enabled
└─ Audit logging: Enabled
```

**When to use:**
- Onboarding new team members
- Troubleshooting configuration issues
- Before changing settings

---

### `/backup` - Trigger Database Backup

**Purpose:** Manually trigger database backup

**Usage:**
```
/backup
```

**Output:**
```
DATABASE BACKUP INITIATED

Provider: Neon
Timestamp: 2025-12-14 15:45:00

Backup includes:
├─ Knowledge atoms (1,964)
├─ Video scripts (52)
├─ Agent status (24 agents)
├─ Approval queue (3 pending)
├─ Alert history (128 alerts)
└─ Configuration settings

Estimated time: 2-3 minutes
Backup location: Neon automated backups

You will be notified when complete.
```

**When to use:**
- Before major system changes
- Before database migrations
- Monthly backup verification
- Before VPS restarts

**⚠️ NOTE:**
- Neon free tier: 7-day backup retention
- Neon Pro: 30-day retention + point-in-time recovery

---

## Command Best Practices

### Daily Workflow (Recommended)

**Morning (9:00 AM):**
```
/status     # System health check
/pending    # Review overnight videos
/daily      # Yesterday's performance
```

**Approve videos:**
```
/approve <id>  # For quality score >0.90
/reject <id> "reason"  # For issues found
```

**Midday Check (12:00 PM):**
```
/agents     # Verify all agents running
/errors     # Check for issues
```

**Evening (6:00 PM):**
```
/daily      # Today's summary
/pending    # Approve for evening publishing
```

---

### Weekly Workflow (Recommended)

**Monday Morning:**
```
/weekly     # Last week's performance
/metrics    # Current KPIs
/config     # Verify settings
```

**Friday Afternoon:**
```
/backup     # Weekly backup
/monthly    # Month-to-date progress (after Day 5)
```

---

### Emergency Procedures

**System Down:**
```
/status     # Identify issue
/agents     # Check which agents failed
/errors     # View error log
/restart <agent>  # Restart failed agents
```

**Quality Issues:**
```
/pending    # Review all pending videos
/reject <id> "detailed feedback"
/pause ScriptwriterAgent  # Stop production if systemic
```

**Budget Overrun:**
```
/metrics    # Check current spend
/config     # Review cost settings
/pause <agent>  # Pause expensive agents temporarily
```

---

## Command Access Control

**Authorization:**
- Only Telegram users in `AUTHORIZED_TELEGRAM_USERS` can execute commands
- Currently authorized: User ID `8445149012`

**To add users:**
1. Edit `.env` file
2. Add user ID to `AUTHORIZED_TELEGRAM_USERS`
3. Restart bot

**Security:**
- All commands logged with user ID + timestamp
- Approval actions stored in database (audit trail)
- Unauthorized access attempts blocked and logged

---

## Troubleshooting

### "Command not found"
- **Cause:** Bot not running or handlers not registered
- **Fix:** Restart bot, verify deployment

### "Database connection failed"
- **Cause:** Neon free tier connection limit
- **Fix:** Wait 30 seconds, retry. Or switch to Supabase:
  ```
  DATABASE_PROVIDER=supabase  # in .env
  ```

### "No pending videos"
- **Cause:** VideoAssemblyAgent not running
- **Fix:** `/agents` to check status, `/restart VideoAssemblyAgent`

### "Agent restart failed"
- **Cause:** Configuration error or missing API key
- **Fix:** `/config` to verify settings, check API keys in `.env`

---

## Next Steps

1. **Deploy database schema:**
   ```bash
   poetry run python scripts/deploy_management_schema.py
   ```

2. **Test commands locally (optional):**
   ```bash
   poetry run python agent_factory/integrations/telegram/run_bot.py
   ```

3. **Deploy to Render.com for 24/7 operation:**
   - Push code to GitHub
   - Render auto-deploys on push
   - Bot available 24/7 at no cost

4. **Start daily workflow:**
   - Send `/status` every morning
   - Review `/pending` videos twice daily
   - Approve first 20 videos manually (set quality standard)

---

## Support

**Documentation:**
- `docs/architecture/AGENT_ORGANIZATION.md` - Agent specifications
- `docs/implementation/YOUTUBE_WIKI_STRATEGY.md` - Content strategy
- `Guides for Users/BOT_DEPLOYMENT_GUIDE.md` - Deployment guide

**Issues:**
- Check `/errors` for recent issues
- Review `query_intelligence.log` for user queries
- Check Render.com logs for deployment issues

**Contact:**
- Telegram: Send message to bot (ID: 8445149012)
- Email: (add your support email)

---

**Last Updated:** 2025-12-14
**Version:** 1.0.0
**Status:** Production Ready
