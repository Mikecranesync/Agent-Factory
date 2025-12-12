# Create all 18 worktrees for Agent Factory autonomous agents
# Usage: PowerShell -ExecutionPolicy Bypass -File scripts\create_all_worktrees.ps1

param(
    [switch]$Force = $false
)

Write-Host "============================================================"
Write-Host "Agent Factory - Worktree Creation Script"
Write-Host "============================================================"
Write-Host ""
Write-Host "This will create 18 worktrees for the 18-agent system."
Write-Host "Each worktree gets its own directory and branch."
Write-Host ""
Write-Host "Directory structure:"
Write-Host "  Agent Factory\           (main repo - DO NOT COMMIT HERE)"
Write-Host "  agent-factory-*\         (18 worktrees for development)"
Write-Host ""

# Get project root
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ParentDir = Split-Path -Parent $ProjectRoot

Write-Host "Project root: $ProjectRoot"
Write-Host "Worktrees will be created in: $ParentDir"
Write-Host ""

# Confirm with user
if (-not $Force) {
    $Confirm = Read-Host "Continue? (y/N)"
    if ($Confirm -ne 'y') {
        Write-Host "Cancelled."
        exit 0
    }
}

# Function to create worktree
function Create-Worktree {
    param(
        [string]$Name,
        [string]$Branch
    )

    $Path = Join-Path $ParentDir $Name

    Write-Host "Creating: $Name (branch: $Branch)"

    # Check if worktree directory already exists
    if (Test-Path $Path) {
        Write-Host "  ⚠️  Directory already exists: $Path" -ForegroundColor Yellow
        Write-Host "  Skipping..."
        Write-Host ""
        return
    }

    # Check if branch already exists
    $BranchExists = git rev-parse --verify $Branch 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ℹ️  Branch already exists: $Branch" -ForegroundColor Cyan
        Write-Host "  Creating worktree from existing branch..."
        git worktree add $Path $Branch
    } else {
        Write-Host "  ✅ Creating new branch and worktree..." -ForegroundColor Green
        git worktree add $Path -b $Branch
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Worktree created: $Path" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed to create worktree" -ForegroundColor Red
    }

    Write-Host ""
}

# Change to project root
Set-Location $ProjectRoot

Write-Host "============================================================"
Write-Host "Executive Team (2 agents)"
Write-Host "============================================================"
Write-Host ""

Create-Worktree "agent-factory-executive-ai-ceo" "executive/ai-ceo-agent"
Create-Worktree "agent-factory-executive-chief-of-staff" "executive/chief-of-staff-agent"

Write-Host "============================================================"
Write-Host "Research & Knowledge Base Team (4 agents)"
Write-Host "============================================================"
Write-Host ""

Create-Worktree "agent-factory-research" "research/research-agent"
Create-Worktree "agent-factory-atom-builder" "research/atom-builder-agent"
Create-Worktree "agent-factory-librarian" "research/librarian-agent"
Create-Worktree "agent-factory-quality-checker" "research/quality-checker-agent"

Write-Host "============================================================"
Write-Host "Content Production Team (5 agents)"
Write-Host "============================================================"
Write-Host ""

Create-Worktree "agent-factory-curriculum" "content/curriculum-agent"
Create-Worktree "agent-factory-strategy" "content/strategy-agent"
Create-Worktree "agent-factory-scriptwriter" "content/scriptwriter-agent"
Create-Worktree "agent-factory-seo" "content/seo-agent"
Create-Worktree "agent-factory-thumbnail" "content/thumbnail-agent"

Write-Host "============================================================"
Write-Host "Media & Publishing Team (4 agents)"
Write-Host "============================================================"
Write-Host ""

Create-Worktree "agent-factory-voice" "media/voice-production-agent"
Create-Worktree "agent-factory-video" "media/video-assembly-agent"
Create-Worktree "agent-factory-publishing-strategy" "media/publishing-strategy-agent"
Create-Worktree "agent-factory-youtube-uploader" "media/youtube-uploader-agent"

Write-Host "============================================================"
Write-Host "Engagement & Analytics Team (3 agents)"
Write-Host "============================================================"
Write-Host ""

Create-Worktree "agent-factory-community" "engagement/community-agent"
Create-Worktree "agent-factory-analytics" "engagement/analytics-agent"
Create-Worktree "agent-factory-social-amplifier" "engagement/social-amplifier-agent"

Write-Host "============================================================"
Write-Host "✅ Worktree Creation Complete" -ForegroundColor Green
Write-Host "============================================================"
Write-Host ""
Write-Host "18 worktrees created in: $ParentDir"
Write-Host ""
Write-Host "List all worktrees:"
Write-Host "  git worktree list"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. cd ..\agent-factory-research"
Write-Host "  2. Start building Research Agent (Issue #47)"
Write-Host "  3. Open new Claude Code instances for parallel work"
Write-Host ""
Write-Host "See: docs\GIT_WORKTREE_GUIDE.md for complete workflow guide"
Write-Host ""
