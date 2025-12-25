# PAI Hooks System

**Event-driven automation for Agent Factory**

Hooks capture work, manage state, and automate workflows across all products.

---

## What Are Hooks?

Hooks are scripts that run automatically when specific events occur:
- **Tool calls** - Before/after agents use tools
- **Session events** - Start, end, save, load
- **Task events** - Create, update, complete
- **Agent events** - Initialize, execute, finish

**Inspired by**: PAI (Personal AI Infrastructure) patterns from Archon (13.4k⭐)

---

## Quick Start

### Enable Hooks
```bash
# Hooks are auto-enabled if .claude/hooks/ directory exists
# Check current hooks
ls .claude/hooks/

# Test a hook
.claude/hooks/on_session_start.sh
```

### Hook Lifecycle
```
Event Triggered
    ↓
Hook Script Executes
    ↓
Hook Output Logged (data/logs/hooks/)
    ↓
Success/Failure Reported
```

---

## Available Hooks

### Session Hooks
| Hook | When | Use Case |
|------|------|----------|
| `on_session_start.sh` | Session begins | Load context, check git status, restore state |
| `on_session_end.sh` | Session ends | Save state, commit work, sync backlog |
| `on_session_save.sh` | Manual save (Ctrl+S) | Checkpoint progress, update UOCS |

### Task Hooks
| Hook | When | Use Case |
|------|------|----------|
| `on_task_create.sh` | New task created | Update backlog.md, sync to Backlog.md MCP |
| `on_task_update.sh` | Task status changed | Log progress, notify team |
| `on_task_complete.sh` | Task marked done | Validate acceptance criteria, update metrics |

### Tool Hooks
| Hook | When | Use Case |
|------|------|----------|
| `on_tool_use.sh` | Before tool call | Validate inputs, check permissions |
| `after_tool_use.sh` | After tool call | Log outputs, update state |

### Agent Hooks
| Hook | When | Use Case |
|------|------|----------|
| `on_agent_init.sh` | Agent created | Register in database, set up logging |
| `on_agent_execute.sh` | Agent runs | Track cost, measure latency |
| `on_agent_finish.sh` | Agent completes | Save results, update metrics |

### Git Hooks
| Hook | When | Use Case |
|------|------|----------|
| `pre_commit.sh` | Before git commit | Run tests, lint code, validate |
| `post_commit.sh` | After git commit | Update changelog, sync docs |
| `pre_push.sh` | Before git push | Check branch, prevent force push to main |

---

## Hook Implementation

### Example: on_session_start.sh

```bash
#!/usr/bin/env bash
# Hook: on_session_start.sh
# Runs when a new Claude Code session begins

set -e

echo "🚀 Session starting..."

# 1. Check git status
echo "📊 Git status:"
git status --short

# 2. Load task context
if [ -f "TASK.md" ]; then
    echo "📋 Current task:"
    head -n 20 TASK.md
fi

# 3. Check for blocking user actions
if grep -q "## User Actions" TASK.md 2>/dev/null; then
    echo "⚠️  User actions required! See TASK.md"
fi

# 4. Restore previous session state (UOCS pattern)
if [ -f ".claude/history/last_session.json" ]; then
    echo "📜 Restoring session from $(jq -r '.timestamp' .claude/history/last_session.json)"
fi

# 5. Log session start
mkdir -p data/logs/hooks
echo "$(date -Iseconds) SESSION_START" >> data/logs/hooks/sessions.log

echo "✅ Session ready!"
```

### Example: on_task_complete.sh

```bash
#!/usr/bin/env bash
# Hook: on_task_complete.sh
# Runs when a task is marked as complete

set -e

TASK_ID="$1"
TASK_TITLE="$2"

echo "✅ Task completed: $TASK_ID - $TASK_TITLE"

# 1. Validate task has acceptance criteria
if ! backlog task view "$TASK_ID" | grep -q "Acceptance Criteria"; then
    echo "⚠️  Warning: Task has no acceptance criteria"
fi

# 2. Update metrics
COMPLETED_COUNT=$(grep -c "status: Done" backlog/tasks/*.md || echo 0)
echo "📊 Total completed tasks: $COMPLETED_COUNT"

# 3. Sync to TASK.md
echo "📝 Syncing to TASK.md..."
poetry run python scripts/backlog/sync_tasks.py

# 4. Log completion
echo "$(date -Iseconds) TASK_COMPLETE task_id=$TASK_ID" >> data/logs/hooks/tasks.log

# 5. Check if milestone reached
if [ "$COMPLETED_COUNT" -eq 10 ]; then
    echo "🎉 Milestone: 10 tasks completed!"
fi
```

### Example: pre_commit.sh

```bash
#!/usr/bin/env bash
# Hook: pre_commit.sh
# Runs before every git commit

set -e

echo "🔍 Pre-commit checks..."

# 1. Check if committing to main directory (blocked by worktree pattern)
if [ ! -d "../.git" ]; then
    echo "❌ ERROR: Direct commits to main directory are blocked!"
    echo "   Use git worktrees: agentcli worktree-create <feature-name>"
    exit 1
fi

# 2. Run linting (if available)
if command -v ruff &> /dev/null; then
    echo "🧹 Running linter..."
    ruff check . --fix || {
        echo "⚠️  Linting warnings found (non-blocking)"
    }
fi

# 3. Run tests (if available)
if [ -d "tests" ]; then
    echo "🧪 Running tests..."
    poetry run pytest tests/ -q || {
        echo "❌ Tests failed! Fix before committing."
        exit 1
    }
fi

# 4. Validate no secrets in staged files
echo "🔐 Checking for secrets..."
if git diff --cached --name-only | grep -qE "\.(env|credentials\.json|secrets\.)"; then
    echo "❌ ERROR: Attempting to commit secrets!"
    git diff --cached --name-only | grep -E "\.(env|credentials\.json|secrets\.)"
    exit 1
fi

echo "✅ Pre-commit checks passed!"
```

---

## Hook Configuration

### Enable/Disable Hooks

```bash
# Enable hooks (default if .claude/hooks/ exists)
echo "hooks_enabled: true" >> .claude/settings.json

# Disable specific hook
chmod -x .claude/hooks/on_task_create.sh

# Re-enable hook
chmod +x .claude/hooks/on_task_create.sh

# Disable all hooks temporarily
export PAI_HOOKS_DISABLED=1
```

### Hook Settings (`.claude/hooks/config.yml`)

```yaml
hooks:
  enabled: true
  log_directory: data/logs/hooks
  timeout_seconds: 30
  retry_on_failure: false

session_hooks:
  on_session_start:
    enabled: true
    async: false  # Block session start until complete
  on_session_end:
    enabled: true
    async: true   # Don't block session end

task_hooks:
  on_task_complete:
    enabled: true
    validate_acceptance_criteria: true
    sync_to_task_md: true

git_hooks:
  pre_commit:
    enabled: true
    run_tests: true
    check_secrets: true
  pre_push:
    enabled: true
    prevent_force_push_main: true
```

---

## UOCS Pattern (Use Of Claude Sessions)

**UOCS** tracks every Claude Code session for continuity and debugging.

### Session History Format

```json
{
  "session_id": "ses_2025-12-22_14-30-45",
  "timestamp": "2025-12-22T14:30:45Z",
  "git_branch": "feature-pai-hooks",
  "git_commit": "a1b2c3d",
  "tasks_in_progress": ["task-55", "task-56"],
  "files_modified": [
    ".claude/hooks/README.md",
    ".claude/hooks/on_session_start.sh"
  ],
  "context": {
    "last_command": "Skill('CORE')",
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

### Stored In: `.claude/history/`

```
.claude/history/
├── last_session.json              # Most recent session
├── sessions/
│   ├── 2025-12-22_14-30-45.json  # Individual sessions
│   ├── 2025-12-22_16-15-30.json
│   └── 2025-12-23_09-00-00.json
└── weekly_summary.json            # Aggregated stats
```

### Restore Previous Session

```bash
# on_session_start.sh automatically checks for last_session.json

# Manual restore
SESSION_ID=$(jq -r '.session_id' .claude/history/last_session.json)
echo "Restoring session: $SESSION_ID"

# Show previous context
jq '.context' .claude/history/last_session.json

# Resume tasks
jq -r '.tasks_in_progress[]' .claude/history/last_session.json | while read task_id; do
    echo "Task in progress: $task_id"
    backlog task view "$task_id"
done
```

---

## Windows Integration

### PowerShell Hook Wrappers

Hooks can call PowerShell for Windows-specific operations:

```bash
# .claude/hooks/on_session_start.sh

# Check if running on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "🪟 Windows detected - running PowerShell integration"
    powershell.exe -File .claude/hooks/windows/sync_context.ps1
fi
```

### PowerShell Script: `sync_context.ps1`

```powershell
# .claude/hooks/windows/sync_context.ps1
# Sync Agent Factory context across Windows apps

Write-Host "🔄 Syncing context to Windows registry..."

# Read current context
$context = Get-Content .claude/history/last_session.json | ConvertFrom-Json

# Store in registry for other apps to access
$regPath = "HKCU:\Software\AgentFactory\Context"
if (!(Test-Path $regPath)) {
    New-Item -Path $regPath -Force
}

Set-ItemProperty -Path $regPath -Name "SessionID" -Value $context.session_id
Set-ItemProperty -Path $regPath -Name "ActiveSkill" -Value $context.context.active_skill
Set-ItemProperty -Path $regPath -Name "ProductFocus" -Value $context.context.product_focus

Write-Host "✅ Context synced to registry"
```

---

## Hook Development

### Create New Hook

1. Create script in `.claude/hooks/`
2. Make executable: `chmod +x .claude/hooks/my_hook.sh`
3. Test: `.claude/hooks/my_hook.sh`
4. Enable in config: Update `.claude/hooks/config.yml`

### Hook Template

```bash
#!/usr/bin/env bash
# Hook: my_hook.sh
# Description: What this hook does

set -e  # Exit on error

# Hook metadata
HOOK_NAME="my_hook"
HOOK_VERSION="1.0.0"

# Arguments (if any)
ARG1="${1:-default_value}"

echo "🎣 Running hook: $HOOK_NAME"

# Your logic here
echo "Doing something with $ARG1"

# Log to hook logs
LOG_DIR="data/logs/hooks"
mkdir -p "$LOG_DIR"
echo "$(date -Iseconds) $HOOK_NAME arg1=$ARG1" >> "$LOG_DIR/hook_executions.log"

echo "✅ Hook complete"
```

### Testing Hooks

```bash
# Test hook directly
.claude/hooks/on_session_start.sh

# Test with arguments
.claude/hooks/on_task_complete.sh "task-55" "Test Task"

# Dry run (no side effects)
export PAI_HOOKS_DRY_RUN=1
.claude/hooks/pre_commit.sh

# Verbose logging
export PAI_HOOKS_VERBOSE=1
.claude/hooks/on_session_start.sh
```

---

## Hook Logging

### Log Files

```
data/logs/hooks/
├── sessions.log              # Session start/end
├── tasks.log                 # Task lifecycle events
├── hook_executions.log       # All hook executions
├── errors.log                # Hook failures
└── metrics.json              # Aggregated stats
```

### Log Format

```
2025-12-22T14:30:45Z SESSION_START session_id=ses_2025-12-22_14-30-45 branch=main
2025-12-22T14:31:12Z TASK_CREATE task_id=task-55 title="Create hooks system"
2025-12-22T14:45:30Z TASK_UPDATE task_id=task-55 status=in_progress
2025-12-22T15:15:00Z TASK_COMPLETE task_id=task-55 duration_min=44
2025-12-22T15:16:00Z SESSION_END session_id=ses_2025-12-22_14-30-45 duration_min=45
```

### View Logs

```bash
# Recent hook executions
tail -f data/logs/hooks/hook_executions.log

# Session history
tail -n 50 data/logs/hooks/sessions.log

# Hook errors
cat data/logs/hooks/errors.log

# Metrics summary
jq '.' data/logs/hooks/metrics.json
```

---

## Security & Permissions

### Hook Execution Rules

1. **Only execute hooks owned by user** - Prevent malicious scripts
2. **Validate hook signature** - Check hash against known-good
3. **Sandbox execution** - Run in isolated environment (if available)
4. **Timeout enforcement** - Kill hooks that run >30 seconds
5. **Audit logging** - Log all hook executions

### Protected Operations

Hooks **cannot** modify:
- `.claude/settings.json` (PAI contract)
- `products/*/config/` (product configurations)
- `.env` files (secrets)

These require explicit user approval via `AskUserQuestion` tool.

---

## Examples

### Example 1: Auto-sync Backlog on Task Update

```bash
# .claude/hooks/on_task_update.sh

TASK_ID="$1"

echo "📝 Task updated: $TASK_ID"
echo "🔄 Auto-syncing to TASK.md..."

poetry run python scripts/backlog/sync_tasks.py

echo "✅ TASK.md updated"
```

### Example 2: Cost Tracking on Agent Execution

```bash
# .claude/hooks/on_agent_execute.sh

AGENT_NAME="$1"
TASK="$2"

echo "🤖 Agent executing: $AGENT_NAME"

# Log to metrics
METRICS_FILE="data/logs/hooks/metrics.json"
COST=$(jq -r ".agents.\"$AGENT_NAME\".total_cost_usd // 0" "$METRICS_FILE")

echo "💰 Current agent cost: \$$COST"
```

### Example 3: Validate Acceptance Criteria on Task Complete

```bash
# .claude/hooks/on_task_complete.sh

TASK_ID="$1"

# Check if task has acceptance criteria
if ! backlog task view "$TASK_ID" | grep -q "Acceptance Criteria"; then
    echo "❌ ERROR: Task $TASK_ID has no acceptance criteria!"
    echo "   Please add criteria before marking complete."
    exit 1
fi

# Validate all criteria checked
UNCHECKED=$(backlog task view "$TASK_ID" | grep -c "- \[ \]" || echo 0)
if [ "$UNCHECKED" -gt 0 ]; then
    echo "⚠️  Warning: $UNCHECKED acceptance criteria not checked"
    echo "   Mark all criteria as complete before closing task."
fi

echo "✅ Task validation passed"
```

---

## Troubleshooting

### Hook Not Running

```bash
# Check if hook is executable
ls -la .claude/hooks/on_session_start.sh

# Make executable
chmod +x .claude/hooks/on_session_start.sh

# Check if hooks are enabled
grep "hooks_enabled" .claude/settings.json

# Check logs
cat data/logs/hooks/errors.log
```

### Hook Timing Out

```bash
# Increase timeout in config
# .claude/hooks/config.yml
hooks:
  timeout_seconds: 60  # Increase from 30

# Or run hook manually to debug
.claude/hooks/slow_hook.sh
```

### Hook Failing Silently

```bash
# Enable verbose logging
export PAI_HOOKS_VERBOSE=1

# Run hook
.claude/hooks/my_hook.sh

# Check error logs
cat data/logs/hooks/errors.log
```

---

## References

- **PAI Patterns**: Inspired by Archon (13.4k⭐) hook system
- **UOCS**: Use Of Claude Sessions pattern for continuity
- **Hook Types**: Session, Task, Tool, Agent, Git hooks
- **Windows Integration**: PowerShell wrappers, registry sync
- **Security**: Sandboxing, signature validation, audit logging

---

**Last Updated**: 2025-12-22
**Version**: 1.0.0
