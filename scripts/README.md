# Agent Factory Scripts

This directory contains automation scripts for managing the 18-agent development workflow.

---

## Worktree Management Scripts

### Create All Worktrees

**Purpose:** Create all 18 worktrees for the 18-agent system in one command.

**Windows (PowerShell - Recommended):**
```powershell
PowerShell -ExecutionPolicy Bypass -File scripts\create_all_worktrees.ps1
```

**macOS/Linux/Git Bash:**
```bash
bash scripts/create_all_worktrees.sh
```

**What it does:**
- Creates 18 directories (one per agent) outside the main repo
- Each worktree gets its own branch: `<team>/<agent>-agent`
- Organizes by team: executive, research, content, media, engagement
- Skips existing worktrees (safe to re-run)

**Example output:**
```
============================================================
Agent Factory - Worktree Creation Script
============================================================

Creating: agent-factory-research (branch: research/research-agent)
  ✅ Creating new branch and worktree...
  ✅ Worktree created: C:\Users\user\agent-factory-research

Creating: agent-factory-scriptwriter (branch: content/scriptwriter-agent)
  ✅ Creating new branch and worktree...
  ✅ Worktree created: C:\Users\user\agent-factory-scriptwriter

...

✅ Worktree Creation Complete

18 worktrees created in: C:\Users\user
```

**After running:**
```
Desktop/
├── Agent Factory/              # Main repo
├── agent-factory-research/     # Worktree 1
├── agent-factory-scriptwriter/ # Worktree 2
├── agent-factory-voice/        # Worktree 3
└── ... (18 total)
```

---

### Clean Up Merged Worktrees

**Purpose:** Remove worktrees for branches that have been merged into main.

**Usage:**
```bash
bash scripts/cleanup_merged_worktrees.sh
```

**What it does:**
- Fetches latest from `origin/main`
- Finds branches that have been merged
- Lists worktrees associated with merged branches
- Asks for confirmation before removing
- Removes worktrees and deletes branches

**When to use:**
- After PRs are merged
- Weekly cleanup routine
- Before starting new work

**Example:**
```bash
$ bash scripts/cleanup_merged_worktrees.sh

============================================================
Agent Factory - Worktree Cleanup Script
============================================================

Finding merged branches...
Merged branches:
  research/research-agent
  content/scriptwriter-agent

Finding associated worktrees...
Worktrees to remove:
  ../agent-factory-research (research/research-agent)
  ../agent-factory-scriptwriter (content/scriptwriter-agent)

Remove these worktrees and delete branches? (y/N): y

Removing worktree: ../agent-factory-research
✅ Worktree removed
Deleting branch: research/research-agent
✅ Branch deleted

✅ Cleanup Complete
```

---

## Telegram Bot Scripts

### Bot Manager (Singleton Entry Point)

**Purpose:** Start/stop/restart/status for Telegram bot (prevents duplicate instances).

**Commands:**
```bash
# Start bot
poetry run python scripts/bot_manager.py start

# Check status
poetry run python scripts/bot_manager.py status

# Stop bot
poetry run python scripts/bot_manager.py stop

# Restart bot
poetry run python scripts/bot_manager.py restart
```

**See:** [BOT_DEPLOYMENT_GUIDE.md](../BOT_DEPLOYMENT_GUIDE.md) for complete bot documentation.

---

### Windows Service Installer

**Purpose:** Install Telegram bot as a Windows Service using NSSM.

**Usage:**
```powershell
# Run as Administrator
PowerShell -ExecutionPolicy Bypass -File scripts\install_windows_service.ps1
```

**What it does:**
- Installs bot as Windows Service
- Auto-restart on failure
- Proper logging to `logs/` directory
- Service manager prevents duplicate instances

**See:** [BOT_DEPLOYMENT_GUIDE.md](../BOT_DEPLOYMENT_GUIDE.md) for complete installation guide.

---

## Quick Reference

### Worktree Workflow

```bash
# 1. Create all worktrees
PowerShell -ExecutionPolicy Bypass -File scripts\create_all_worktrees.ps1

# 2. Start working on agent
cd ..\agent-factory-research
code .

# 3. Make changes, commit
git add .
git commit -m "feat: Add Research Agent web scraping"

# 4. Push branch
git push origin research/research-agent

# 5. Create PR on GitHub

# 6. After merge, clean up
cd ..\Agent Factory
bash scripts/cleanup_merged_worktrees.sh
```

### Bot Management

```bash
# Development
poetry run python scripts/bot_manager.py start

# Production (Windows Service)
PowerShell -ExecutionPolicy Bypass -File scripts\install_windows_service.ps1
nssm status AgentFactoryTelegramBot
```

---

## File Listing

```
scripts/
├── README.md                       # This file
├── create_all_worktrees.sh         # Bash version (Git Bash/macOS/Linux)
├── create_all_worktrees.ps1        # PowerShell version (Windows)
├── cleanup_merged_worktrees.sh     # Clean up merged branches
├── bot_manager.py                  # Telegram bot manager (singleton)
└── install_windows_service.ps1     # NSSM service installer
```

---

## Additional Resources

- **Git Worktree Guide:** [docs/GIT_WORKTREE_GUIDE.md](../docs/GIT_WORKTREE_GUIDE.md)
- **Bot Deployment Guide:** [BOT_DEPLOYMENT_GUIDE.md](../BOT_DEPLOYMENT_GUIDE.md)
- **Agent Organization:** [docs/AGENT_ORGANIZATION.md](../docs/AGENT_ORGANIZATION.md)
- **Contributing Guide:** [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Troubleshooting

### "Execution of scripts is disabled on this system"

**Windows PowerShell error when running `.ps1` scripts.**

**Solution:**
```powershell
# Use -ExecutionPolicy Bypass flag
PowerShell -ExecutionPolicy Bypass -File scripts\create_all_worktrees.ps1
```

### "bash: command not found"

**Windows without Git Bash installed.**

**Solution:** Use PowerShell versions (`.ps1` files) instead.

### Worktree already exists

**Error:** "fatal: 'path' already exists"

**Solution:** Script will skip existing worktrees automatically. To force recreate:
```bash
# Remove worktree first
git worktree remove ../agent-factory-research

# Run creation script again
bash scripts/create_all_worktrees.sh
```

---

**"Automation that just works."**
