#!/bin/bash
# Create all 18 worktrees for Agent Factory autonomous agents
# Usage: bash scripts/create_all_worktrees.sh

set -e  # Exit on error

echo "============================================================"
echo "Agent Factory - Worktree Creation Script"
echo "============================================================"
echo ""
echo "This will create 18 worktrees for the 18-agent system."
echo "Each worktree gets its own directory and branch."
echo ""
echo "Directory structure:"
echo "  Agent Factory/           (main repo - DO NOT COMMIT HERE)"
echo "  agent-factory-*/         (18 worktrees for development)"
echo ""

# Confirm with user
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Get project root (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT_DIR="$(dirname "$PROJECT_ROOT")"

echo ""
echo "Project root: $PROJECT_ROOT"
echo "Worktrees will be created in: $PARENT_DIR"
echo ""

# Function to create worktree
create_worktree() {
    local name=$1
    local branch=$2
    local path="$PARENT_DIR/$name"

    echo "Creating: $name (branch: $branch)"

    # Check if worktree already exists
    if [ -d "$path" ]; then
        echo "  ⚠️  Directory already exists: $path"
        echo "  Skipping..."
        return
    fi

    # Check if branch already exists
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
        echo "  ℹ️  Branch already exists: $branch"
        echo "  Creating worktree from existing branch..."
        git worktree add "$path" "$branch"
    else
        echo "  ✅ Creating new branch and worktree..."
        git worktree add "$path" -b "$branch"
    fi

    echo "  ✅ Worktree created: $path"
    echo ""
}

# Change to project root
cd "$PROJECT_ROOT"

echo "============================================================"
echo "Executive Team (2 agents)"
echo "============================================================"
echo ""

create_worktree "agent-factory-executive-ai-ceo" "executive/ai-ceo-agent"
create_worktree "agent-factory-executive-chief-of-staff" "executive/chief-of-staff-agent"

echo "============================================================"
echo "Research & Knowledge Base Team (4 agents)"
echo "============================================================"
echo ""

create_worktree "agent-factory-research" "research/research-agent"
create_worktree "agent-factory-atom-builder" "research/atom-builder-agent"
create_worktree "agent-factory-librarian" "research/librarian-agent"
create_worktree "agent-factory-quality-checker" "research/quality-checker-agent"

echo "============================================================"
echo "Content Production Team (5 agents)"
echo "============================================================"
echo ""

create_worktree "agent-factory-curriculum" "content/curriculum-agent"
create_worktree "agent-factory-strategy" "content/strategy-agent"
create_worktree "agent-factory-scriptwriter" "content/scriptwriter-agent"
create_worktree "agent-factory-seo" "content/seo-agent"
create_worktree "agent-factory-thumbnail" "content/thumbnail-agent"

echo "============================================================"
echo "Media & Publishing Team (4 agents)"
echo "============================================================"
echo ""

create_worktree "agent-factory-voice" "media/voice-production-agent"
create_worktree "agent-factory-video" "media/video-assembly-agent"
create_worktree "agent-factory-publishing-strategy" "media/publishing-strategy-agent"
create_worktree "agent-factory-youtube-uploader" "media/youtube-uploader-agent"

echo "============================================================"
echo "Engagement & Analytics Team (3 agents)"
echo "============================================================"
echo ""

create_worktree "agent-factory-community" "engagement/community-agent"
create_worktree "agent-factory-analytics" "engagement/analytics-agent"
create_worktree "agent-factory-social-amplifier" "engagement/social-amplifier-agent"

echo "============================================================"
echo "✅ Worktree Creation Complete"
echo "============================================================"
echo ""
echo "18 worktrees created in: $PARENT_DIR"
echo ""
echo "List all worktrees:"
echo "  git worktree list"
echo ""
echo "Next steps:"
echo "  1. cd ../agent-factory-research"
echo "  2. Start building Research Agent (Issue #47)"
echo "  3. Open new Claude Code instances for parallel work"
echo ""
echo "See: docs/GIT_WORKTREE_GUIDE.md for complete workflow guide"
echo ""
