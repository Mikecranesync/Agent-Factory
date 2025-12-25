#!/usr/bin/env bash
# Hook: on_session_start.sh
# Runs when a new Claude Code session begins
# Version: 1.0.0

set -e

echo "🚀 Session starting..."

# Create log directory if it doesn't exist
LOG_DIR="data/logs/hooks"
mkdir -p "$LOG_DIR"

# 1. Check git status
echo ""
echo "📊 Git status:"
git status --short || echo "(No git repository)"

# 2. Load task context
if [ -f "TASK.md" ]; then
    echo ""
    echo "📋 Current task:"
    head -n 20 TASK.md
fi

# 3. Check for blocking user actions
if [ -f "TASK.md" ] && grep -q "## User Actions" TASK.md 2>/dev/null; then
    echo ""
    echo "⚠️  User actions required! See TASK.md - User Actions section"
fi

# 4. Restore previous session state (UOCS pattern)
HISTORY_DIR=".claude/history"
if [ -f "$HISTORY_DIR/last_session.json" ]; then
    echo ""
    LAST_SESSION=$(cat "$HISTORY_DIR/last_session.json")
    TIMESTAMP=$(echo "$LAST_SESSION" | jq -r '.timestamp // "unknown"')
    BRANCH=$(echo "$LAST_SESSION" | jq -r '.git_branch // "unknown"')
    echo "📜 Last session: $TIMESTAMP (branch: $BRANCH)"

    # Show tasks in progress
    TASKS_IN_PROGRESS=$(echo "$LAST_SESSION" | jq -r '.tasks_in_progress[]?' 2>/dev/null || echo "")
    if [ -n "$TASKS_IN_PROGRESS" ]; then
        echo "   Tasks in progress:"
        echo "$TASKS_IN_PROGRESS" | while read task_id; do
            echo "   - $task_id"
        done
    fi
fi

# 5. Check Agent Factory platform health
echo ""
echo "🏗️  Platform health:"

# Check if Supabase is accessible (non-blocking)
if command -v poetry &> /dev/null; then
    poetry run python -c "from agent_factory.core.settings_service import settings; print('✅ Settings service OK')" 2>/dev/null || echo "⚠️  Settings service unavailable (non-blocking)"
else
    echo "⚠️  Poetry not found - skipping health checks"
fi

# 6. Log session start
SESSION_ID="ses_$(date +%Y-%m-%d_%H-%M-%S)"
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "no-git")
echo "$(date -Iseconds) SESSION_START session_id=$SESSION_ID branch=$CURRENT_BRANCH" >> "$LOG_DIR/sessions.log"

# 7. Create session history entry
mkdir -p "$HISTORY_DIR/sessions"
cat > "$HISTORY_DIR/last_session.json" <<EOF
{
  "session_id": "$SESSION_ID",
  "timestamp": "$(date -Iseconds)",
  "git_branch": "$CURRENT_BRANCH",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'no-git')",
  "tasks_in_progress": [],
  "files_modified": [],
  "context": {
    "last_command": null,
    "active_skill": null,
    "product_focus": "platform"
  },
  "metrics": {
    "duration_minutes": 0,
    "tools_used": 0,
    "files_read": 0,
    "files_written": 0
  }
}
EOF

echo ""
echo "✅ Session ready! (ID: $SESSION_ID)"
echo ""
echo "💡 Quick commands:"
echo "   Skill('CORE')          - Load core context"
echo "   Skill('PLC_TUTOR')    - Load PLC Tutor context"
echo "   cat backlog.md         - View master backlog"
echo ""
