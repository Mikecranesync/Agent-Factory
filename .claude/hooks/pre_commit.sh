#!/usr/bin/env bash
# Hook: pre_commit.sh
# Runs before every git commit
# Version: 1.0.0

set -e

echo "🔍 Pre-commit checks..."

# 1. Check if committing to main directory (blocked by worktree pattern)
if [ ! -d "../.git" ]; then
    # We're in the main worktree
    if [ "$(git rev-parse --show-toplevel)" = "$(pwd)" ]; then
        echo "❌ ERROR: Direct commits to main directory are blocked!"
        echo ""
        echo "   Agent Factory uses git worktrees for safety."
        echo ""
        echo "   Create a worktree for your feature:"
        echo "   $ agentcli worktree-create <feature-name>"
        echo ""
        echo "   Or manually:"
        echo "   $ git worktree add ../agent-factory-<feature-name> -b <feature-name>"
        echo ""
        echo "   See: docs/patterns/GIT_WORKTREE_GUIDE.md"
        exit 1
    fi
fi

# 2. Validate no secrets in staged files
echo "🔐 Checking for secrets..."
SECRETS_FOUND=0

git diff --cached --name-only | while read file; do
    # Check for common secret file patterns
    if echo "$file" | grep -qE "\.(env|credentials\.json|secrets\.|key$|pem$)"; then
        echo "   ❌ Attempting to commit secrets: $file"
        SECRETS_FOUND=1
    fi
done

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo "❌ ERROR: Secret files detected in staged changes!"
    echo "   Add these to .gitignore and remove from staging:"
    echo "   $ git reset HEAD <file>"
    exit 1
fi

echo "   ✅ No secrets found"

# 3. Run linting (if available, non-blocking)
if command -v ruff &> /dev/null; then
    echo "🧹 Running linter..."
    if ruff check . --fix 2>/dev/null; then
        echo "   ✅ Linting passed"
    else
        echo "   ⚠️  Linting warnings found (non-blocking)"
    fi
else
    echo "   ⏭️  Linter not available (skipping)"
fi

# 4. Run tests (if available, blocking if tests exist)
if [ -d "tests" ] && command -v poetry &> /dev/null; then
    echo "🧪 Running tests..."

    # Check if pytest is installed
    if poetry run python -c "import pytest" 2>/dev/null; then
        if poetry run pytest tests/ -q 2>/dev/null; then
            echo "   ✅ Tests passed"
        else
            echo ""
            echo "❌ ERROR: Tests failed!"
            echo ""
            echo "   Fix failing tests before committing."
            echo "   Run tests manually:"
            echo "   $ poetry run pytest tests/ -v"
            echo ""
            echo "   Or skip tests (not recommended):"
            echo "   $ git commit --no-verify"
            exit 1
        fi
    else
        echo "   ⏭️  pytest not installed (skipping)"
    fi
else
    echo "   ⏭️  Tests not available (skipping)"
fi

# 5. Check commit message format (if pre-commit message hook exists)
# This would typically be done in a prepare-commit-msg hook
# For now, we'll just validate the commit isn't empty

# 6. Check file sizes (prevent accidentally committing large files)
echo "📦 Checking file sizes..."
LARGE_FILES=0

git diff --cached --name-only | while read file; do
    if [ -f "$file" ]; then
        SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        SIZE_MB=$((SIZE / 1024 / 1024))

        if [ "$SIZE_MB" -gt 10 ]; then
            echo "   ⚠️  Large file: $file (${SIZE_MB}MB)"
            echo "      Consider using Git LFS for files >10MB"
            LARGE_FILES=1
        fi
    fi
done

if [ "$LARGE_FILES" -eq 0 ]; then
    echo "   ✅ No large files detected"
fi

# 7. Log pre-commit check
LOG_DIR="data/logs/hooks"
mkdir -p "$LOG_DIR"
echo "$(date -Iseconds) PRE_COMMIT status=passed" >> "$LOG_DIR/hook_executions.log"

echo ""
echo "✅ Pre-commit checks passed!"
echo ""
