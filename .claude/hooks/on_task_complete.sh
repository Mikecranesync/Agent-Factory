#!/usr/bin/env bash
# Hook: on_task_complete.sh
# Runs when a task is marked as complete
# Version: 1.0.0

set -e

TASK_ID="$1"
TASK_TITLE="${2:-Unknown Task}"

if [ -z "$TASK_ID" ]; then
    echo "❌ ERROR: Task ID required"
    echo "Usage: $0 <task-id> [task-title]"
    exit 1
fi

echo "✅ Task completed: $TASK_ID - $TASK_TITLE"

# Create log directory
LOG_DIR="data/logs/hooks"
mkdir -p "$LOG_DIR"

# 1. Validate task has acceptance criteria (if Backlog.md MCP available)
if command -v backlog &> /dev/null; then
    echo ""
    echo "🔍 Validating task..."

    if ! backlog task view "$TASK_ID" | grep -q "Acceptance Criteria" 2>/dev/null; then
        echo "⚠️  Warning: Task has no acceptance criteria"
        echo "   Best practice: Add criteria before marking complete"
    else
        # Check if all criteria are checked
        UNCHECKED=$(backlog task view "$TASK_ID" | grep -c "- \[ \]" 2>/dev/null || echo 0)
        if [ "$UNCHECKED" -gt 0 ]; then
            echo "⚠️  Warning: $UNCHECKED acceptance criteria not checked"
            echo "   Review before marking task as complete"
        else
            echo "✅ All acceptance criteria checked"
        fi
    fi
fi

# 2. Update metrics
echo ""
echo "📊 Updating metrics..."

# Count completed tasks
COMPLETED_COUNT=0
if [ -d "backlog/tasks" ]; then
    COMPLETED_COUNT=$(grep -rl "status: Done" backlog/tasks/*.md 2>/dev/null | wc -l)
    echo "   Total completed tasks: $COMPLETED_COUNT"
fi

# 3. Sync to TASK.md
if [ -f "scripts/backlog/sync_tasks.py" ] && command -v poetry &> /dev/null; then
    echo ""
    echo "📝 Syncing to TASK.md..."
    poetry run python scripts/backlog/sync_tasks.py 2>/dev/null && echo "   ✅ TASK.md updated" || echo "   ⚠️  Sync failed (non-blocking)"
fi

# 4. Log completion
TIMESTAMP=$(date -Iseconds)
echo "$TIMESTAMP TASK_COMPLETE task_id=$TASK_ID title=\"$TASK_TITLE\"" >> "$LOG_DIR/tasks.log"

# 5. Update session history (if exists)
HISTORY_DIR=".claude/history"
if [ -f "$HISTORY_DIR/last_session.json" ]; then
    # Remove task from tasks_in_progress
    jq --arg tid "$TASK_ID" '.tasks_in_progress = (.tasks_in_progress // [] | map(select(. != $tid)))' "$HISTORY_DIR/last_session.json" > "$HISTORY_DIR/last_session.json.tmp"
    mv "$HISTORY_DIR/last_session.json.tmp" "$HISTORY_DIR/last_session.json"
fi

# 6. Check for milestones
echo ""
if [ "$COMPLETED_COUNT" -eq 10 ]; then
    echo "🎉 Milestone reached: 10 tasks completed!"
elif [ "$COMPLETED_COUNT" -eq 25 ]; then
    echo "🎉 Milestone reached: 25 tasks completed!"
elif [ "$COMPLETED_COUNT" -eq 50 ]; then
    echo "🎉 Milestone reached: 50 tasks completed!"
elif [ "$COMPLETED_COUNT" -eq 100 ]; then
    echo "🎉 Milestone reached: 100 tasks completed!"
fi

# 7. Update weekly summary
WEEK_NUMBER=$(date +%Y-W%U)
SUMMARY_FILE="$HISTORY_DIR/weekly_summary_${WEEK_NUMBER}.json"

if [ -f "$SUMMARY_FILE" ]; then
    jq '.tasks_completed += 1' "$SUMMARY_FILE" > "$SUMMARY_FILE.tmp"
    mv "$SUMMARY_FILE.tmp" "$SUMMARY_FILE"
fi

echo ""
echo "✅ Task completion logged!"
echo ""
