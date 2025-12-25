# History System - CORE Skill

## Purpose

The History System (UOCS - Use Of Claude Sessions) tracks all interactions with Claude Code for:
- **Continuity**: Resume context from previous sessions
- **Debugging**: Trace errors back to specific sessions
- **Productivity**: Measure time spent, tasks completed
- **Learning**: Analyze patterns in how you work with AI

---

## What Gets Tracked

### 1. Sessions
**File**: `.claude/history/sessions.md` + `.claude/history/sessions/*.json`

Every Claude Code session is logged:
- Start/end timestamps
- Duration (minutes)
- Git branch + commit
- Tasks in progress
- Files modified
- Active skill loaded
- Productivity metrics

**Example**:
```json
{
  "session_id": "ses_2025-12-22_16-45-30",
  "timestamp": "2025-12-22T16:45:30Z",
  "git_branch": "feature-pai-hooks",
  "git_commit": "a1b2c3d4",
  "tasks_in_progress": ["task-55", "task-56"],
  "files_modified": [
    ".claude/hooks/README.md",
    ".claude/hooks/on_session_start.sh"
  ],
  "context": {
    "active_skill": "CORE",
    "product_focus": "platform"
  },
  "metrics": {
    "duration_minutes": 45,
    "tools_used": 12,
    "files_read": 8,
    "files_written": 4
  }
}
```

### 2. Agent Executions
**File**: `.claude/history/agents.md`

Every autonomous agent execution:
- Agent name
- Task performed
- Success/failure status
- Duration (ms)
- Cost (USD)
- Output artifacts

**Example**:
```
| 2025-12-22T14:30:45Z | ScriptwriterAgent | Generate script | success | 12,450ms | $0.042 | data/scripts/plc-motor-control-001.md |
```

### 3. Decisions
**File**: `.claude/history/decisions.md`

Major architectural and strategic decisions:
- **Context**: Why was this decision needed?
- **Decision**: What was chosen?
- **Rationale**: Why was this the right choice?
- **Consequences**: What does this enable/prevent?
- **Alternatives**: What else was considered?
- **Status**: Active | Superseded | Deprecated

**Example**:
```markdown
## [2025-12-22] PAI Foundation with Bash Hooks

**Context**: Needed event-driven automation...
**Decision**: Use Bash hooks (not TypeScript)
**Rationale**: Immediate usability, no build step, git integration...
**Status**: Active
```

### 4. Outputs
**Directory**: `.claude/history/outputs/`

Artifacts from Claude Code sessions:
- Generated code snippets
- Analysis reports
- Decision summaries
- Debug logs

---

## How It Works

### Automatic Logging (Hooks)

The History System is powered by **PAI Hooks** (`.claude/hooks/`):

1. **on_session_start.sh** - Logs session start, restores previous context
2. **on_session_end.sh** - Logs session end, saves summary
3. **on_agent_execute.sh** - Logs agent execution start
4. **on_agent_finish.sh** - Logs agent completion, cost, output

**You don't need to do anything** - hooks run automatically.

### Manual Logging (When Needed)

For important decisions, add to `.claude/history/decisions.md`:

```bash
# Open decisions log
code .claude/history/decisions.md

# Add decision using template (see decisions.md)
```

---

## Viewing History

### Session History

```bash
# View all sessions (Markdown)
cat .claude/history/sessions.md

# View last session (JSON)
cat .claude/history/last_session.json

# View specific session
cat .claude/history/sessions/ses_2025-12-22_16-45-30.json

# View weekly summary
cat .claude/history/weekly_summary_2025-W51.json
```

### Agent History

```bash
# View agent execution log
cat .claude/history/agents.md

# View agent metrics
jq '.' data/logs/hooks/metrics.json
```

### Decision History

```bash
# View all decisions
cat .claude/history/decisions.md

# Search for specific decision
grep -A 20 "SCAFFOLD Priority" .claude/history/decisions.md
```

---

## UOCS Pattern

**UOCS** = Use Of Claude Sessions

The pattern:
1. **Track everything** - Every session, every agent, every decision
2. **Human-readable** - Markdown logs for humans
3. **Machine-readable** - JSON logs for agents/analysis
4. **Auto-restore** - Next session continues from last one
5. **Weekly summaries** - Aggregated productivity metrics

**Why?**
- **Resume work** - Pick up where you left off (even days later)
- **Debug issues** - "What changed between yesterday and today?"
- **Measure productivity** - "How much time did I spend on SCAFFOLD this week?"
- **Learn patterns** - "Which agents are slow/expensive?"

---

## Session Continuity

### How Auto-Restore Works

1. **Session Start** → Hook reads `.claude/history/last_session.json`
2. **Shows context**:
   - Last session time
   - Git branch
   - Tasks in progress
   - Files modified
3. **You decide** → Resume tasks or start new work

### Example Restore

```bash
$ .claude/hooks/on_session_start.sh

🚀 Session starting...

📜 Last session: 2025-12-22T16:45:30Z (branch: feature-pai-hooks)
   Tasks in progress:
   - task-55: Create PAI Hooks System
   - task-56: Implement LRU cache

💡 Quick commands:
   backlog task view task-55    # Resume task-55
   Skill("CORE")                # Load CORE context
```

---

## Productivity Metrics

### Weekly Summary

Auto-generated in `.claude/history/weekly_summary_YYYY-WWN.json`:

```json
{
  "week": "2025-W51",
  "sessions": 5,
  "total_duration_minutes": 240,
  "tasks_completed": 8,
  "files_modified": 32,
  "agents_executed": 15,
  "total_cost_usd": 2.45
}
```

### Monthly Trends

```bash
# Sessions per week
jq '.sessions' .claude/history/weekly_summary_*.json

# Total time this month
jq -s 'map(.total_duration_minutes) | add' .claude/history/weekly_summary_2025-W*.json

# Cost per week
jq '.total_cost_usd' .claude/history/weekly_summary_*.json
```

---

## Integration with Other Systems

### Backlog.md MCP

Session history integrates with Backlog.md:
- **Tasks in progress** → Synced from Backlog.md
- **Task completion** → Hook updates Backlog.md + logs to history
- **Weekly summary** → Pulls task completion count from Backlog.md

### Git

Session history tracks git context:
- **Branch** → Which branch was active
- **Commit** → Last commit hash
- **Worktree** → Which worktree was used

Useful for:
- "What was I working on in this feature branch?"
- "Which commits happened during this session?"

### Agent Factory Core

Agent execution history feeds into:
- **Cost tracking** → Total spend per agent
- **Performance monitoring** → Which agents are slow
- **Failure analysis** → Which agents error most

---

## Best Practices

### 1. Review History Weekly

Every Friday:
```bash
# View weekly summary
cat .claude/history/weekly_summary_$(date +%Y-W%U).json

# Review decisions made this week
grep "$(date +%Y-%m)" .claude/history/decisions.md

# Check for failed agents
grep "failure" .claude/history/agents.md
```

### 2. Log Major Decisions

Before implementing big changes:
1. Open `.claude/history/decisions.md`
2. Add decision using template
3. Document context, rationale, alternatives
4. Update status when superseded

### 3. Archive Old Sessions

Keep only 100 most recent sessions (auto-enforced by hooks):
```yaml
# .claude/hooks/config.yml
uocs:
  max_sessions_stored: 100
```

Older sessions auto-archived to `.claude/history/archive/`.

### 4. Use Outputs Directory

Save generated artifacts to `.claude/history/outputs/`:
```bash
# Good
cat > .claude/history/outputs/analysis_2025-12-22.md <<EOF
...
EOF

# Bad (clutters repo root)
cat > analysis.md <<EOF
...
EOF
```

---

## Troubleshooting

### "No session history found"

**Cause**: First time running, no sessions yet.

**Fix**: Run a hook to create session:
```bash
.claude/hooks/on_session_start.sh
```

### "Session restore failed"

**Cause**: Corrupted `.claude/history/last_session.json`

**Fix**: Delete and let hook recreate:
```bash
rm .claude/history/last_session.json
.claude/hooks/on_session_start.sh
```

### "History logs too large"

**Cause**: Too many sessions/agents logged.

**Fix**: Archive old logs:
```bash
mkdir -p .claude/history/archive
mv .claude/history/sessions/ses_2025-*.json .claude/history/archive/
```

---

## Commands Reference

### Session History
```bash
# View sessions
cat .claude/history/sessions.md

# Last session
cat .claude/history/last_session.json

# Specific session
cat .claude/history/sessions/ses_<ID>.json

# Weekly summary
cat .claude/history/weekly_summary_<YEAR-W##>.json
```

### Agent History
```bash
# View agent log
cat .claude/history/agents.md

# Agent metrics
jq '.' data/logs/hooks/metrics.json
```

### Decision History
```bash
# View decisions
cat .claude/history/decisions.md

# Search decisions
grep -i "database" .claude/history/decisions.md
```

### Manual Session Control
```bash
# Start session manually
.claude/hooks/on_session_start.sh

# End session manually
.claude/hooks/on_session_end.sh

# Complete task manually
.claude/hooks/on_task_complete.sh task-55 "Task Title"
```

---

## Files Reference

| File | Purpose | Format | Auto-Updated |
|------|---------|--------|--------------|
| `sessions.md` | Human-readable session log | Markdown | ✅ Yes |
| `last_session.json` | Current session state | JSON | ✅ Yes |
| `sessions/*.json` | Archived sessions | JSON | ✅ Yes |
| `weekly_summary_*.json` | Weekly metrics | JSON | ✅ Yes |
| `agents.md` | Agent execution log | Markdown | ✅ Yes |
| `decisions.md` | Decision records | Markdown | ❌ Manual |
| `outputs/` | Session artifacts | Various | ❌ Manual |

---

## Related Documentation

- **PAI Hooks**: `.claude/hooks/README.md`
- **Hook Configuration**: `.claude/hooks/config.yml`
- **Backlog Integration**: `backlog/README.md`
- **Platform Roadmap**: `docs/implementation/00_platform_roadmap.md`

---

**Last Updated**: 2025-12-22
**Version**: 1.0.0
