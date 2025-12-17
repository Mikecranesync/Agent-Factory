# Autonomous Claude System - Complete Guide

Claude works autonomously at night (2am UTC) processing GitHub issues and creating draft PRs for your review.

## Quick Start

### 1. Configure GitHub Secrets

Go to your repository settings → Secrets and variables → Actions → New repository secret:

```
ANTHROPIC_API_KEY=sk-ant-...     # Your Claude API key
TELEGRAM_BOT_TOKEN=123456:ABC... # Your Telegram bot token (optional)
TELEGRAM_ADMIN_CHAT_ID=12345678  # Your Telegram user ID (optional)
```

### 2. Enable GitHub Actions Workflow

The workflow is already created at `.github/workflows/claude-autonomous.yml`.

It will run automatically at 2am UTC daily.

### 3. Test Manually (Recommended First Run)

Before letting it run autonomously, test manually:

1. Go to Actions tab in your repository
2. Click "Autonomous Claude - Nighttime Issue Solver"
3. Click "Run workflow"
4. Leave defaults or customize:
   - Max issues: 3 (start small)
   - Dry run: true (analyze only, no actual execution)
5. Click "Run workflow"

### 4. Review Results

After the workflow completes:

- Check Telegram for notifications (if configured)
- Review created draft PRs (if not dry run)
- Download session logs from workflow artifacts

## How It Works

```
2am UTC Daily
    ↓
GitHub Actions Triggers
    ↓
Issue Queue Builder → Analyzes ALL open issues
    ↓                  Scores by complexity (0-10)
    ↓                  Ranks by priority
    ↓
Selects 5-10 Best Issues
    ↓
Safety Monitor → Enforces limits ($5 cost, 4hr time, 3 failures)
    ↓
FOR EACH ISSUE:
    ↓
Claude Code Action → Explores → Plans → Implements → Tests
    ↓
IF SUCCESS: Create Draft PR
IF FAILURE: Comment on issue
    ↓
Telegram Notifications → Real-time updates
    ↓
Session Complete → Summary to Telegram
```

## Scoring Algorithm

### Complexity Score (0-10)

**Heuristic Scoring (40% weight, fast, $0 cost):**
- Description length: Sparse (<100 chars) = +2 complexity
- Labels:
  - "good first issue" = -3 complexity (easy)
  - "bug" = +1 complexity
  - "feature" = +2 complexity
  - "breaking change" = +4 complexity (very complex)
  - "docs" = -2 complexity (easy)
- Code snippets: Each ``` block = +0.5 complexity
- File mentions: Each .py/.js reference = +0.3 complexity
- Issue age: >90 days old = +1.5 complexity (probably hard)

**LLM Semantic Scoring (60% weight, accurate, ~$0.002/issue):**
- Analyzes description semantically
- Estimates time (0.5-4 hours)
- Assesses risk (low/medium/high)
- Returns complexity 0-10 with reasoning

**Final Complexity:** `(heuristic * 0.4) + (llm_score * 0.6)`

### Priority Score

```python
priority = business_value * (1 / complexity) * feasibility

# Business value from labels:
- "critical" or "urgent" = +3.0
- "high priority" = +2.0
- "good first issue" = +1.0
- "technical debt" = +1.5

# Feasibility from risk:
- low risk = 1.0
- medium risk = 0.7
- high risk = 0.3

# Complexity penalty (simpler = higher priority):
complexity_factor = (10 - complexity) / 10
```

**Result:** Higher priority = more valuable, less complex, more feasible

### Queue Selection

1. Sort all open issues by priority (highest first)
2. Filter: Skip issues with:
   - Complexity > 8/10
   - Estimated time > 2 hours
   - Already have PRs
   - Labeled: wontfix, duplicate, invalid, on-hold
3. Select top 5-10 issues where total estimated time < 4 hours

## Safety Mechanisms

### Hard Limits (Enforced Before Each Issue)

1. **Cost Limit:** $5.00 max per night
   - Stops immediately if `total_cost >= 5.0`
   - Default: $5.00 (configurable)

2. **Time Limit:** 4 hours max
   - Wall-clock time from session start
   - Default: 4.0 hours (configurable)

3. **Failure Circuit Breaker:** 3 consecutive failures → STOP
   - Prevents runaway failure loops
   - Resets on each success
   - Alerts via Telegram immediately

4. **Per-Issue Timeout:** 30 minutes max
   - Individual issue can't monopolize session
   - Fails gracefully, moves to next issue

### Soft Guardrails

5. **Complexity Filter:** Issues > 8/10 complexity excluded from queue
6. **Time Estimate Cap:** Issues estimated > 2 hours skipped
7. **Total Time Budget:** Queue selection ensures total estimated time < 4 hours
8. **Draft PRs Only:** All PRs created as DRAFT, you must approve merge

## Configuration

### Environment Variables

**Required:**
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Claude API key
GITHUB_TOKEN=ghp_...          # Auto-provided by GitHub Actions
```

**Optional:**
```bash
TELEGRAM_BOT_TOKEN=...        # Telegram notifications
TELEGRAM_ADMIN_CHAT_ID=...    # Your Telegram user ID
MAX_ISSUES=10                 # Max issues per night
SAFETY_MAX_COST=5.0           # Max cost in USD
SAFETY_MAX_TIME_HOURS=4.0     # Max time in hours
SAFETY_MAX_FAILURES=3         # Max consecutive failures
```

### Customizing Workflow

Edit `.github/workflows/claude-autonomous.yml`:

**Change schedule (2am → 11pm):**
```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # 11pm UTC daily
```

**Change default limits:**
```yaml
env:
  SAFETY_MAX_COST: '3.0'       # $3 instead of $5
  SAFETY_MAX_TIME_HOURS: '2.0' # 2 hours instead of 4
  MAX_ISSUES: '5'              # 5 issues instead of 10
```

## Telegram Notifications

### What You'll Receive

1. **Session Start:**
```
🤖 Autonomous Claude Started
Analyzing open issues...
```

2. **Queue Summary:**
```
📋 Issue Queue (7 issues)

1. #48 Add type hints to core
   Complexity: 3.1/10 | Priority: 8.2 | Est: 0.8h

2. #52 Implement hybrid search
   Complexity: 6.2/10 | Priority: 7.5 | Est: 1.5h
...
```

3. **PR Created:**
```
✅ PR Created for Issue #48

Add type hints to core modules
PR: https://github.com/owner/repo/pull/123

⏱️ Time: 245.3s
💵 Cost: $0.42

Review and merge when ready.
```

4. **Issue Failed:**
```
❌ Issue #52 Failed

Implement hybrid search
Error: Timeout after 30 minutes

Will retry in next run if still open.
```

5. **Safety Limit Hit:**
```
⚠️ Safety Limit Reached

Cost limit reached: $5.02 >= $5.00

Stopping early (4/7 completed)
```

6. **Session Complete:**
```
📊 Session Complete

Results:
✅ Successful PRs: 5
❌ Failed: 2
📋 Total Processed: 7

Resources Used:
💵 Total Cost: $2.18
⏱️ Total Time: 2.3h
📈 Success Rate: 71%

Remaining Budget:
💰 Cost: $2.82
⏲️ Time: 1.7h
```

## Testing Locally

### Test 1: Issue Queue Builder
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
python scripts/autonomous/issue_queue_builder.py
```

**Expected:** List of scored issues with complexity/priority/time

### Test 2: Safety Monitor
```bash
python scripts/autonomous/safety_monitor.py
```

**Expected:** 3 test scenarios (normal, cost limit, failure circuit breaker)

### Test 3: Telegram Notifier
```bash
python scripts/autonomous/telegram_notifier.py
```

**Expected:** Test notification sent to Telegram (or demo printed to console)

### Test 4: Full Dry Run
```bash
DRY_RUN=true python scripts/autonomous/autonomous_claude_runner.py
```

**Expected:**
- Queue built and logged
- Safety limits checked
- Telegram notifications sent (if configured)
- No actual execution or PRs created
- Session summary printed

## Troubleshooting

### "No issues in queue"

**Possible causes:**
- All open issues have PRs already
- All issues are too complex (>8/10)
- All issues estimated >2 hours
- Issues labeled: wontfix, duplicate, invalid, on-hold

**Solution:** Review issue queue builder output, adjust filters if needed

### "Safety limit reached" too early

**Possible causes:**
- Issues more complex than estimated
- LLM scoring too aggressive

**Solutions:**
1. Increase limits: `SAFETY_MAX_COST=10.0`, `SAFETY_MAX_TIME_HOURS=6.0`
2. Reduce max issues: `MAX_ISSUES=5`
3. Filter out complex issues manually before run

### "Workflow failed" in GitHub Actions

**Check:**
1. Secrets configured correctly (ANTHROPIC_API_KEY)
2. Download workflow logs from Actions tab
3. Check session logs artifact
4. Review error messages in Telegram (if configured)

### PRs not being created

**Possible causes:**
- Claude Code Action failed to execute
- Branch creation failed
- Permissions issue

**Check:**
1. Workflow has correct permissions (contents: write, pull-requests: write)
2. Claude Code Action workflow (`.github/workflows/claude.yml`) exists
3. Review session logs for errors

## Advanced Usage

### Manual Queue Review

Before autonomous run, review what would be selected:

```bash
python scripts/autonomous/issue_queue_builder.py > queue_preview.txt
```

### Custom Complexity Scoring

Edit `scripts/autonomous/issue_queue_builder.py`:

```python
# Adjust weights
final_complexity = (heuristic["score"] * 0.3) + (llm_analysis["complexity_score"] * 0.7)

# Add custom label scoring
if "p0" in labels:
    factors["p0_label"] = -2.0  # Prioritize P0 issues
```

### Multiple Daily Runs

Add multiple cron schedules:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'   # 2am
    - cron: '0 14 * * *'  # 2pm
    - cron: '0 23 * * *'  # 11pm
```

## Cost Estimation

**Average cost per night:** $2-3 (with $5 limit)

**Breakdown:**
- Issue queue building: ~$0.10 (LLM scoring for 50 issues)
- Per-issue execution: ~$0.30-0.50 each
- 5-10 issues: ~$1.50-5.00 total

**Monthly cost:** ~$60-90 (30 nights × $2-3/night)

**Savings:** If each PR saves you 30-60 minutes of work, ROI is massive.

## Success Metrics

After 1 week of autonomous runs, you should see:

- **5-10 draft PRs ready for review each morning**
- **Success rate: 60-80%** (5-8 PRs out of 10 attempts)
- **Average cost: $2-3 per night** (well under $5 limit)
- **Average time: 2-3 hours per night** (well under 4 hour limit)
- **Zero safety limit violations** (circuit breakers work correctly)

## FAQ

**Q: Will it auto-merge PRs?**
A: No. All PRs are created as DRAFT. You must review and merge manually.

**Q: What if it creates broken code?**
A: Review the PR, request changes, or close it. Draft PRs don't affect main branch.

**Q: Can I stop it mid-session?**
A: Yes. Cancel the GitHub Actions workflow. It will stop immediately.

**Q: What if I push code during the night?**
A: GitHub Actions pulls latest code before each run. No conflicts.

**Q: Does it work on private repositories?**
A: Yes, as long as GitHub Actions is enabled and secrets are configured.

**Q: Can I run it during the day?**
A: Yes. Use "workflow_dispatch" to trigger manually anytime.

## Support

- **Issues:** https://github.com/Mikecranesync/Agent-Factory/issues
- **Documentation:** `docs/autonomous/`
- **Logs:** Download from GitHub Actions artifacts

---

Ready to let Claude work while you sleep? 🌙
