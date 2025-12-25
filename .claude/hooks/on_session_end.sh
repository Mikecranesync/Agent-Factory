#!/usr/bin/env bash
# Hook: on_session_end.sh
# Runs when a Claude Code session ends
# Version: 1.0.0

set -e

echo "👋 Session ending..."

# Create log directory if it doesn't exist
LOG_DIR="data/logs/hooks"
mkdir -p "$LOG_DIR"
HISTORY_DIR=".claude/history"
mkdir -p "$HISTORY_DIR/sessions"

# 1. Load current session
if [ -f "$HISTORY_DIR/last_session.json" ]; then
    SESSION_ID=$(jq -r '.session_id' "$HISTORY_DIR/last_session.json")
    START_TIME=$(jq -r '.timestamp' "$HISTORY_DIR/last_session.json")

    echo "📊 Session summary:"
    echo "   ID: $SESSION_ID"
    echo "   Started: $START_TIME"

    # Calculate duration
    START_EPOCH=$(date -d "$START_TIME" +%s 2>/dev/null || date +%s)
    END_EPOCH=$(date +%s)
    DURATION_MIN=$(( (END_EPOCH - START_EPOCH) / 60 ))
    echo "   Duration: ${DURATION_MIN} minutes"

    # Update session metrics
    jq --arg dur "$DURATION_MIN" '.metrics.duration_minutes = ($dur | tonumber)' "$HISTORY_DIR/last_session.json" > "$HISTORY_DIR/last_session.json.tmp"
    mv "$HISTORY_DIR/last_session.json.tmp" "$HISTORY_DIR/last_session.json"

    # Copy to sessions archive
    cp "$HISTORY_DIR/last_session.json" "$HISTORY_DIR/sessions/${SESSION_ID}.json"

else
    echo "⚠️  No session data found"
    SESSION_ID="unknown"
    DURATION_MIN=0
fi

# 2. Check for uncommitted work
if git status --porcelain 2>/dev/null | grep -q '^'; then
    echo ""
    echo "⚠️  Uncommitted changes detected:"
    git status --short
    echo ""
    echo "💡 Consider committing your work:"
    echo "   git add ."
    echo "   git commit -m \"Your message\""
fi

# 3. Sync backlog (if available)
if [ -f "scripts/backlog/sync_tasks.py" ] && command -v poetry &> /dev/null; then
    echo ""
    echo "📝 Syncing backlog to TASK.md..."
    poetry run python scripts/backlog/sync_tasks.py 2>/dev/null || echo "   (Sync skipped - not available)"
fi

# 4. Log session end
echo "$(date -Iseconds) SESSION_END session_id=$SESSION_ID duration_min=$DURATION_MIN" >> "$LOG_DIR/sessions.log"

# 5. Update weekly summary
WEEK_NUMBER=$(date +%Y-W%U)
SUMMARY_FILE="$HISTORY_DIR/weekly_summary_${WEEK_NUMBER}.json"

if [ ! -f "$SUMMARY_FILE" ]; then
    cat > "$SUMMARY_FILE" <<EOF
{
  "week": "$WEEK_NUMBER",
  "sessions": 0,
  "total_duration_minutes": 0,
  "tasks_completed": 0,
  "files_modified": 0
}
EOF
fi

# Increment session count
jq '.sessions += 1 | .total_duration_minutes += '"$DURATION_MIN" "$SUMMARY_FILE" > "$SUMMARY_FILE.tmp"
mv "$SUMMARY_FILE.tmp" "$SUMMARY_FILE"

echo ""
echo "✅ Session ended!"
echo ""
echo "📊 This week ($(date +%Y-W%U)):"
jq -r '"   Sessions: \(.sessions)\n   Total time: \(.total_duration_minutes) minutes"' "$SUMMARY_FILE"
echo ""
