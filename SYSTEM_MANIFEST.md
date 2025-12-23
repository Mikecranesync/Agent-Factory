# SYSTEM MANIFEST

**Last Updated:** 2025-12-22
**Scope:** CI/CD Pipelines, VPS Deployments, Running Services

---

## CRITICAL FINDING: GitHub Actions vs Manual Deployment Mismatch

### Problem
GitHub Actions workflow `.github/workflows/deploy-vps.yml` is **FAILING** because it's deploying an **OUTDATED** bot setup. The bot running successfully on VPS uses a **DIFFERENT** codebase and service name.

### Status
- ❌ **GitHub Actions:** FAILING (deploys old `telegram_bot.py`)
- ✅ **Manual Deployment:** WORKING (deploys new `orchestrator_bot.py`)
- ✅ **Production Bot:** RUNNING (systemd service `orchestrator-bot.service`)

---

## VPS Infrastructure

### Server Details
- **Host:** 72.60.175.144 (Hostinger VPS)
- **OS:** Ubuntu (confirmed via systemd)
- **Access:** SSH passwordless (ed25519 key)
- **User:** root

### Projects on VPS
Located in `/root/`:
1. **Agent-Factory/** - Main repository (connected to GitHub)
2. **n8n/** - Automation platform (separate project)

### Git Repositories
- **Only One:** `/root/Agent-Factory/.git`
- **Remote:** GitHub (owner/repo TBD - check with `git remote -v`)
- **Branch:** main

---

## Production Bot Deployment

### Current Working Setup (✅ RUNNING)

**Bot File:**
```
/root/Agent-Factory/agent_factory/integrations/telegram/orchestrator_bot.py
```

**Systemd Service:**
```
/etc/systemd/system/orchestrator-bot.service
```

**Service Definition:**
```ini
[Unit]
Description=Rivet Orchestrator Telegram Bot
After=network.target docker.service
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/Agent-Factory
Environment=PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/root/Agent-Factory/.env
ExecStart=/root/.local/bin/poetry run python -m agent_factory.integrations.telegram.orchestrator_bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Safety limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

**Deployment Method:** Manual
```bash
# Current working deployment process
ssh root@72.60.175.144
cd /root/Agent-Factory
git pull origin main
systemctl restart orchestrator-bot
journalctl -u orchestrator-bot -f
```

**Bot Username:** @RivetCeo_bot
**Token Env Var:** `ORCHESTRATOR_BOT_TOKEN`
**Admin Chat ID:** 8445149012

---

## Pre-Deployment Validation

Run these checks **BEFORE** every deployment to VPS:

### 1. Schema Validation
```bash
poetry run python scripts/validate_schema.py
```
**Purpose:** Ensures retriever.py columns match database schema
**Expected:** `[RESULT] Schema validation passed!`
**If fails:** Update retriever.py to use existing columns

### 2. Import Check
```bash
poetry run python -c "from agent_factory.core.orchestrator import RivetOrchestrator; print('OK')"
```
**Purpose:** Verifies no import errors
**Expected:** `OK`
**If fails:** Fix import errors before deploying

### 3. Deploy to VPS
```bash
git push origin main
ssh vps "cd /root/Agent-Factory && git pull && systemctl restart orchestrator-bot"
```

### 4. Verify Deployment
```bash
# Check service status
ssh vps "systemctl status orchestrator-bot --no-pager"

# Check for errors
ssh vps "journalctl -u orchestrator-bot -n 30 --no-pager | grep -i error"

# Check trace logs
ssh vps "tail -20 /root/Agent-Factory/logs/traces.jsonl"
```

---

## Old Bot Setup (⚠️ LEGACY - NOT RUNNING)

### Files Exist But Unused

**Old Bot File:**
```
/root/Agent-Factory/telegram_bot.py
```

**Old Service File (on disk, not active):**
```
/root/Agent-Factory/rivet-pro.service
```

**Old Deployment Script:**
```
/root/Agent-Factory/deploy_rivet_pro.sh
```

**Status:** These files exist in the repo but are **NOT** being used. The GitHub Actions workflow references them, causing deployment failures.

---

## GitHub Actions Workflows

### Location
`.github/workflows/` in Agent-Factory repository

### Workflows

#### 1. deploy-vps.yml ❌ FAILING

**Name:** Deploy RIVET Pro to VPS

**Trigger:**
- Push to `main` branch with changes to:
  - `agent_factory/**`
  - `telegram_bot.py` (OLD)
  - `deploy_rivet_pro.sh` (OLD)
  - `rivet-pro.service` (OLD)
- Manual workflow_dispatch

**What It Does:**
1. Checkout code
2. Setup SSH with secret `VPS_SSH_KEY`
3. Copy `.env` from secret `VPS_ENV_FILE`
4. SSH to VPS and run:
   - `git fetch origin && git reset --hard origin/main`
   - `./deploy_rivet_pro.sh`
   - Verify `telegram_bot.py` process is running (FAILS - wrong bot)
   - Check `rivet-pro.service` status (FAILS - wrong service)

**Why It Fails:**
- Looks for `telegram_bot.py` process (doesn't run)
- Checks `rivet-pro.service` (not enabled/active)
- Should check `orchestrator-bot.service` instead

**Secrets Required:**
- `VPS_SSH_KEY` - SSH private key for root@72.60.175.144
- `VPS_ENV_FILE` - Complete .env file content
- `TELEGRAM_BOT_TOKEN` - For deployment notifications
- `TELEGRAM_ADMIN_CHAT_ID` - Admin chat for notifications

#### 2. claude-autonomous.yml (Status Unknown)

**Name:** Autonomous Claude - Nighttime Issue Solver

**Trigger:**
- Schedule: `0 2 * * *` (2am UTC daily)
- Manual workflow_dispatch

**What It Does:**
1. Checkout repo
2. Install Python 3.10 + Poetry
3. Run `scripts/autonomous/autonomous_claude_runner.py`
4. Process up to 10 GitHub issues autonomously
5. Create draft PRs for solutions
6. Upload session logs as artifacts

**Safety Limits:**
- Max cost: $5.00 USD
- Max time: 4 hours (5-hour workflow timeout)
- Max failures: 3 consecutive

**Secrets Required:**
- `ANTHROPIC_API_KEY` - Claude API
- `GITHUB_TOKEN` - Auto-provided
- `TELEGRAM_BOT_TOKEN` - Notifications
- `TELEGRAM_ADMIN_CHAT_ID` - Admin notifications

**Notes:**
- Runs nightly to solve GitHub issues
- Creates draft PRs (NOT auto-merged)
- Logs uploaded to GitHub Actions artifacts (7-day retention)

#### 3. claude.yml (Not Reviewed)

**Status:** File exists but content not reviewed in this audit

---

## Active Systemd Services

Located on VPS at `72.60.175.144`

### Running Services
```
orchestrator-bot.service    loaded  active  running  Rivet Orchestrator Telegram Bot
monarx-agent.service        loaded  active  running  Monarx Agent - Security Scanner
qemu-guest-agent.service    loaded  active  running  QEMU Guest Agent
```

### Service Commands
```bash
# Status
systemctl status orchestrator-bot

# Restart
systemctl restart orchestrator-bot

# Logs (live)
journalctl -u orchestrator-bot -f

# Logs (last 50 lines)
journalctl -u orchestrator-bot -n 50
```

---

## VPS Deployment Files

Located in `/root/Agent-Factory/deploy/vps/`

```
README.md                      - VPS deployment guide
agent-factory-bot.service      - OLD service template
orchestrator-bot.service       - CURRENT service template
deploy.sh                      - Deployment script
setup.sh                       - Initial VPS setup
status.sh                      - Check service status
logs.sh                        - View service logs
```

**Note:** The `orchestrator-bot.service` template here matches `/etc/systemd/system/orchestrator-bot.service`

---

## Recent Commits (VPS)

```
9714c7c  feat: Add source attribution and admin debug traces to bot
fd1724c  feat: Split bot responses into two messages - clean user response + admin debug trace
ac36b77  feat: Add Groq LLM fallback for Routes C & D
b0ee560  fix: Change SQL placeholders from $N to %s for psycopg3 compatibility
5b418ee  fix: Convert VendorType enum to string value in RivetIntent creation
```

**Observation:** Recent commits focus on `orchestrator_bot.py` improvements, NOT `telegram_bot.py`

---

## CI/CD Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Production Bot** | ✅ RUNNING | orchestrator-bot.service via systemd |
| **Manual Deploy** | ✅ WORKING | git pull + systemctl restart |
| **GitHub Actions** | ❌ FAILING | Deploys wrong bot (telegram_bot.py) |
| **Autonomous Claude** | ⚠️ UNKNOWN | Runs at 2am UTC, check GitHub Actions logs |

---

## Recommendations

### 1. Fix GitHub Actions Deploy Workflow (HIGH PRIORITY)

**Option A: Update workflow to deploy new bot**

Edit `.github/workflows/deploy-vps.yml`:
- Change verification from `telegram_bot.py` to `orchestrator_bot.py`
- Change service check from `rivet-pro.service` to `orchestrator-bot.service`
- Update deployment script or remove reference to `deploy_rivet_pro.sh`

**Option B: Disable workflow (SIMPLER)**

Since manual deployment works:
- Remove or disable `.github/workflows/deploy-vps.yml`
- Continue using manual `git pull + systemctl restart`
- Add comment: "Manual deployment only - GitHub Actions disabled"

### 2. Clean Up Legacy Files (MEDIUM PRIORITY)

Remove or archive unused files:
```bash
git rm telegram_bot.py rivet-pro.service deploy_rivet_pro.sh
git commit -m "chore: Remove legacy bot files (replaced by orchestrator_bot)"
```

### 3. Document Deployment Process (LOW PRIORITY)

Create `DEPLOYMENT.md` with:
- Current deployment steps (manual)
- Environment variables required
- Rollback procedure
- Health check commands

---

## Environment Variables

### Required on VPS
Located in `/root/Agent-Factory/.env`

**Critical:**
- `ORCHESTRATOR_BOT_TOKEN` - Telegram bot token for @RivetCeo_bot
- `NEON_CONNECTION_STRING` - Database connection (Neon PostgreSQL)

**LLM APIs:**
- `ANTHROPIC_API_KEY` - Claude API
- `OPENAI_API_KEY` - OpenAI API
- `GOOGLE_API_KEY` - Google Gemini API
- `GROQ_API_KEY` - Groq API (free tier)

**Note:** `.env` is .gitignored (correctly) and must be managed separately via:
- GitHub Actions secret `VPS_ENV_FILE` (for automated deploys)
- Manual SSH + editing (for manual deploys)

---

## Data Sources

This manifest was compiled from:
1. SSH investigation of VPS (2025-12-22)
2. GitHub Actions workflow files in `.github/workflows/`
3. Systemd service definitions
4. Git commit history
5. Running service status

**Verification Commands Used:**
```bash
ssh root@72.60.175.144 "ls -la /root/"
ssh root@72.60.175.144 "ls -la /root/Agent-Factory/.github/workflows/"
ssh root@72.60.175.144 "cd /root/Agent-Factory && git log --oneline -5"
ssh root@72.60.175.144 "find /root /opt -name '.git' -type d"
ssh root@72.60.175.144 "systemctl list-units --type=service | grep -E 'rivet|orchestrator'"
ssh root@72.60.175.144 "systemctl cat orchestrator-bot.service"
```

---

## Questions for User

1. **GitHub Actions:** Do you want to fix the deploy-vps.yml workflow or disable it?
2. **Legacy Files:** Can we delete `telegram_bot.py`, `rivet-pro.service`, `deploy_rivet_pro.sh`?
3. **Autonomous Claude:** Is the nightly autonomous issue solver active? Check GitHub Actions logs.
4. **Secrets:** Are all required GitHub Actions secrets configured?

---

**Document Owner:** User (hharp)
**System:** Agent-Factory @ 72.60.175.144
**Next Audit:** After GitHub Actions workflow update
