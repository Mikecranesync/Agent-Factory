#!/bin/bash
# Clean up worktrees after PR merge
# Usage: bash scripts/cleanup_merged_worktrees.sh

set -e  # Exit on error

echo "============================================================"
echo "Agent Factory - Worktree Cleanup Script"
echo "============================================================"
echo ""
echo "This script removes worktrees for branches that have been"
echo "merged into main."
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Fetch latest from remote
echo "Fetching latest from remote..."
git fetch origin main --prune
echo ""

# Get list of merged branches
echo "Finding merged branches..."
MERGED_BRANCHES=$(git branch --merged origin/main | grep -v '^\*' | grep -v 'main' | sed 's/^[ \t]*//')

if [ -z "$MERGED_BRANCHES" ]; then
    echo "✅ No merged branches found. Nothing to clean up."
    exit 0
fi

echo "Merged branches:"
echo "$MERGED_BRANCHES"
echo ""

# Get list of worktrees
echo "Finding associated worktrees..."
WORKTREES_TO_REMOVE=""

while IFS= read -r branch; do
    # Check if worktree exists for this branch
    WORKTREE_PATH=$(git worktree list | grep "$branch" | awk '{print $1}' || true)

    if [ -n "$WORKTREE_PATH" ]; then
        WORKTREES_TO_REMOVE="$WORKTREES_TO_REMOVE\n$WORKTREE_PATH ($branch)"
    fi
done <<< "$MERGED_BRANCHES"

if [ -z "$WORKTREES_TO_REMOVE" ]; then
    echo "✅ No worktrees found for merged branches."
    echo ""
    echo "Merged branches (no worktrees):"
    echo "$MERGED_BRANCHES"
    echo ""
    read -p "Delete these branches? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        while IFS= read -r branch; do
            echo "Deleting branch: $branch"
            git branch -d "$branch"
        done <<< "$MERGED_BRANCHES"
        echo "✅ Branches deleted."
    else
        echo "Cancelled."
    fi
    exit 0
fi

echo "Worktrees to remove:"
echo -e "$WORKTREES_TO_REMOVE"
echo ""

# Confirm with user
read -p "Remove these worktrees and delete branches? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove worktrees and delete branches
while IFS= read -r branch; do
    WORKTREE_PATH=$(git worktree list | grep "$branch" | awk '{print $1}' || true)

    if [ -n "$WORKTREE_PATH" ]; then
        echo ""
        echo "Removing worktree: $WORKTREE_PATH"
        git worktree remove "$WORKTREE_PATH"
        echo "✅ Worktree removed"
    fi

    echo "Deleting branch: $branch"
    git branch -d "$branch"
    echo "✅ Branch deleted"

done <<< "$MERGED_BRANCHES"

echo ""
echo "============================================================"
echo "✅ Cleanup Complete"
echo "============================================================"
echo ""
echo "Remaining worktrees:"
git worktree list
echo ""
