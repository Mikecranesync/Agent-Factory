# CLAUDE.md

## What This Is

Agent Factory - a framework for building multi-agent AI systems. Part of a larger pipeline that turns ideas into live apps in 24 hours.

**You are building the engine that turns blueprints into working agents.**

---

## Current Focus

> **PHASE 1: ORCHESTRATION**
> 
> Build multi-agent routing. One agent receives query, routes to specialist.

See `docs/PHASE1_SPEC.md` for implementation details.

---

## Execution Rules

### Rule 1: One Thing at a Time
Check `PROGRESS.md` for the current checkbox. Complete it. Validate it. Move to next.

### Rule 2: Always Validate
After ANY change, run:
```bash
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"
```
If it fails, fix before moving on. Never build on broken code.

### Rule 3: Show Don't Tell
After completing a task, provide:
1. What you built (plain English)
2. How to test it (exact command)
3. Expected output

### Rule 4: Small Commits
After each working feature:
```bash
git add . && git commit -m "CHECKPOINT: [what works]"
```

### Rule 4.5: Always Use Worktrees
**ENFORCED:** Pre-commit hook blocks commits to main directory.

When working with multiple agents/tools on this codebase:
1. **NEVER work directly in main directory** - commits will be blocked
2. Create a worktree for each agent/feature/task
3. Each worktree gets its own branch
4. Clean up worktrees after PR is merged

**Why?** Multiple agents working in the same directory causes:
- File conflicts and lost work
- Race conditions on changes
- Confusion about which agent did what
- Test interference

**Create worktree:**
```bash
# Option 1: CLI (recommended)
agentcli worktree-create feature-name

# Option 2: Manual
git worktree add ../agent-factory-feature-name -b feature-name
cd ../agent-factory-feature-name
```

**See:** `docs/GIT_WORKTREE_GUIDE.md` for complete guide.

### Rule 5: Three Strikes
If something fails 3 times, STOP. Report the error. Don't keep trying different approaches - it may be a direction problem, not an execution problem.

### Rule 6: No Refactoring Without Permission
Don't "improve" or "clean up" working code unless explicitly asked. Working > elegant.

### Rule 7: Stay In Scope
If a task requires changing files outside the current phase, ask first.

### Rule 8: Security & Compliance by Design
Build enterprise-ready features from inception. No retrofitting security later.

**Before Writing ANY Code:**
Ask these 5 questions:
1. **Input:** Does this handle user input? → Validate + sanitize
2. **Data:** Does this touch data? → Encrypt if sensitive + log access
3. **Access:** Does this expose functionality? → Add auth + rate limits
4. **Output:** Does this generate output? → Filter PII + validate safety
5. **Abuse:** Could an agent abuse this? → Add monitoring + circuit breakers

**Before Marking Feature Complete:**
- [ ] Security implications documented in PR/commit
- [ ] Audit logging implemented (who did what, when)
- [ ] Error messages don't leak sensitive data
- [ ] Rate limits exist (if user-facing)
- [ ] Input validation with allow-lists (not block-lists)

**Before Declaring Phase Complete:**
- [ ] Update `docs/SECURITY_AUDIT.md` with new capabilities
- [ ] Add security tests (not just happy path)
- [ ] Document threat model (what could go wrong)
- [ ] Review against SOC 2 Trust Criteria checklist

**Core Security Principles (Always Follow):**
- **Principle of Least Privilege** - Default deny, explicit allow
- **Defense in Depth** - Multiple security layers
- **Fail Secure** - Errors should block, not allow
- **Audit Everything** - Log all privileged operations
- **Assume Breach** - Limit blast radius

**Why This Matters:**
- Enterprise customers require SOC 2 certification ($10K+ deals)
- Retrofitting security costs 10x more than building it right
- Security incidents destroy trust and revenue
- Compliance unlocks enterprise tier pricing ($299/mo vs $49/mo)

See `docs/SECURITY_STANDARDS.md` for implementation patterns and checklists.

---

## GitHub Strategy Implementation

**Pattern:** GitHub webhooks → Supabase jobs → Orchestrator → Agents

Agent Factory now operates as a **24/7 autonomous system** triggered by GitHub events. This enables:
- Code changes automatically trigger work
- Agents work continuously without manual intervention
- Telegram provides primary user interface (approve, monitor, control)
- Full audit trail in Supabase

### Components

**1. Webhook Handler** (`webhook_handler.py`)
- FastAPI server receiving GitHub POST /webhook/github
- Verifies HMAC signature (GITHUB_WEBHOOK_SECRET)
- Creates jobs in Supabase `agent_jobs` table
- Logs events to `webhook_events` table

**Events Handled:**
- `push` → Creates `sync_and_generate_content` or `full_video_pipeline` jobs
- `release` → Creates `full_video_pipeline` job (high priority)
- `issues` → Creates `manage_tasks` job (for issues labeled `agent-task`)

**2. Orchestrator** (`orchestrator.py`)
- Runs continuously (24/7 in tmux/systemd)
- Git pulls every 60 seconds (GitHub is source of truth)
- Fetches pending jobs from `agent_jobs` table
- Routes jobs to agents via AGENT_REGISTRY
- Sends heartbeat every 5 minutes to `agent_status` table

**Agent Registry Maps job_type → agent class:**
```python
AGENT_REGISTRY = {
    "research_web": "agents.research.research_agent.ResearchAgent",
    "write_script": "agents.content.scriptwriter_agent.ScriptwriterAgent",
    "upload_youtube": "agents.media.youtube_uploader_agent.YouTubeUploaderAgent",
    "full_video_pipeline": "orchestrator_workflows.video_production_pipeline",
    # ... 18 agents total
}
```

**3. Telegram Bot** (`telegram_bot.py`) - **PRIMARY USER INTERFACE**
- Commands: `/status`, `/agents`, `/metrics`, `/approve <id>`, `/reject <id>`, `/issue <title>`
- Daily standup delivery (8 AM configurable)
- Approval workflow (videos, scripts, atoms)
- Real-time notifications (agent failures, approvals needed)

**Why Telegram?**
- Control from phone/desktop without CLI
- Push notifications (alerts, standups)
- Approval workflow (one-tap approve/reject)
- No terminal access needed

**4. Supabase Tables**
- `agent_jobs` - Job queue (pending, assigned, running, completed, failed)
- `agent_status` - Health monitoring (heartbeat, tasks completed/failed)
- `agent_messages` - Inter-agent communication
- `approval_requests` - Human-in-loop workflow
- `webhook_events` - Audit log (all GitHub events)

### Workflow Examples

**Example 1: Push to main branch**
```
1. Developer pushes commit with "feat: Add video script for Ohm's Law"
2. GitHub sends push event → webhook_handler.py
3. Webhook creates job: type=full_video_pipeline, priority=3
4. Orchestrator picks up job (next 60s cycle)
5. Routes to agents: Scriptwriter → Voice → Video → Upload → Social
6. Telegram sends approval requests at checkpoints
7. User approves via /approve command
8. Video published, metadata stored in Supabase
```

**Example 2: GitHub release published**
```
1. Developer creates release v1.0.0
2. GitHub sends release event → webhook_handler.py
3. Webhook creates job: type=full_video_pipeline, priority=1 (high)
4. Orchestrator prioritizes (processes before other jobs)
5. Full pipeline executes autonomously
6. Telegram sends completion notification
```

**Example 3: Daily agent operations**
```
1. Orchestrator runs 24/7 (60s cycles)
2. Git pull on every cycle (code always fresh)
3. Agents check for work (research, quality check, analytics)
4. Telegram sends daily standup (8 AM)
5. User monitors via /status, /agents commands
6. Approvals handled via Telegram (no CLI needed)
```

### Setup Instructions

**1. Configure GitHub Webhook:**
```bash
# In GitHub repo → Settings → Webhooks → Add webhook
Payload URL: https://your-domain.com/webhook/github
Content type: application/json
Secret: <generate strong secret, add to .env as GITHUB_WEBHOOK_SECRET>
Events: push, release, issues
```

**2. Start Orchestrator (24/7):**
```bash
# Option 1: tmux (recommended for development)
tmux new -s orchestrator "python orchestrator.py"

# Option 2: systemd (recommended for production)
# See docs/SYSTEMD_SETUP.md for service configuration

# Option 3: Supervisor
# See docs/SUPERVISOR_SETUP.md
```

**3. Start Telegram Bot (24/7):**
```bash
# Get bot token from @BotFather on Telegram
# Add to .env: TELEGRAM_BOT_TOKEN=...
# Add authorized users: AUTHORIZED_TELEGRAM_USERS=123456789,987654321

# Run bot
tmux new -s telegram "python telegram_bot.py"
```

**4. Start Webhook Handler:**
```bash
# Option 1: Local + ngrok (development)
ngrok http 8000  # Get public URL
python webhook_handler.py  # Runs on http://localhost:8000

# Option 2: VPS + Cloudflare Tunnel (production)
# See docs/CLOUDFLARE_TUNNEL_SETUP.md
```

### Validation Commands

```bash
# Test orchestrator
python -c "from orchestrator import Orchestrator; print('Orchestrator OK')"

# Test webhook handler
python -c "from webhook_handler import app; print('Webhook Handler OK')"

# Test Telegram bot
python -c "from telegram_bot import TelegramBot; print('Telegram Bot OK')"

# Test agent imports
python -c "from agents.executive.ai_ceo_agent import AICEOAgent; print('Agents OK')"

# Check git worktree
git worktree list  # Should show github-strategy branch
```

### Files Created (GitHub Strategy)

- `orchestrator.py` (427 lines) - 24/7 automation loop
- `webhook_handler.py` (424 lines) - GitHub webhook receiver
- `telegram_bot.py` (635 lines) - Primary user interface
- `docs/supabase_agent_migrations.sql` (650+ lines) - Database schema
- `core/models.py` (780 lines) - Pydantic data models
- `agents/` (18 agent skeleton files, 4,248 lines)
- `AUTONOMOUS_PLAN.md` (356 lines) - 8-hour development plan
- `.claude/commands/autonomous-mode.md` (245 lines) - Autonomous mode command

**Total: ~7,800 lines of implementation**

### Next Steps

1. Deploy orchestrator + webhook + Telegram bot (Week 1)
2. Implement agents per AGENT_ORGANIZATION.md (Weeks 2-7)
3. Test end-to-end pipeline (Week 8)
4. Launch autonomous operations (Week 9+)

See: `AUTONOMOUS_PLAN.md` for complete development roadmap.

---

## Architecture Summary
```
agent_factory/
+-- core/
|   +-- agent_factory.py      # Main factory [EXISTS]
|   +-- orchestrator.py       # Routing [PHASE 1]
|   +-- callbacks.py          # Events [PHASE 1]
+-- schemas/                   # [PHASE 2]
+-- tools/                     # [EXISTS]
+-- refs/                      # [PHASE 5]
```

For full architecture, see `docs/ARCHITECTURE.md`.

---

## Reference Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `PROGRESS.md` | Current checklist | Every task |
| `docs/GIT_WORKTREE_GUIDE.md` | Git worktree setup and usage | Before starting work |
| `docs/SECURITY_STANDARDS.md` | Compliance patterns & checklists | Building any feature |
| `docs/lessons_learned/LESSONS_DATABASE.md` | Debugging insights & gotchas | Before implementing similar patterns |
| `docs/security/*.md` | Policy templates | Writing security docs |
| `docs/PHASE1_SPEC.md` | Phase 1 implementation details | Building Phase 1 |
| `docs/ARCHITECTURE.md` | Full system design | Need big picture |
| `docs/PATTERNS.md` | Google ADK patterns | Unsure how to structure something |
| `docs/PRODUCTION.md` | Observability, evals, failover | Production readiness |
| `CLAUDE_CODEBASE.md` | Existing code documentation | Need to understand current code |

---

## Standards

- **Python 3.10+**
- **Type hints** on all functions
- **Pydantic** for data models
- **Google ADK patterns** (see `docs/PATTERNS.md`)
- **ASCII-only output** (Windows compatible)

---

## Validation Commands
```bash
# 1. Import check (run after any change)
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"

# 2. Demo check (run after completing a feature)
poetry run python agent_factory/examples/demo.py

# 3. Test check (run before marking phase complete)
poetry run pytest

# 4. Orchestrator check (Phase 1 specific)
poetry run python -c "from agent_factory.core.orchestrator import AgentOrchestrator; print('OK')"
```

---

## Red Flags - Stop and Report

If you find yourself:
- Refactoring existing working code
- Trying the same fix 3+ times
- Saying "this should work" but it doesn't
- Changing files outside current phase scope
- Unsure why something is failing

**STOP. Report what's happening. Ask for guidance.**

---

## Context for the Human

The project owner is not a coder. When reporting progress:
- Use plain English
- Provide exact test commands they can copy/paste
- Show expected output
- Be honest about uncertainty

---

## Quick Reference: Current Patterns

### Creating Agents (existing)
```python
factory = AgentFactory()
agent = factory.create_agent(role="Name", tools_list=[...], ...)
```

### Creating Tools (existing)
```python
class MyTool(BaseTool):
    name = "my_tool"
    description = "What it does"
    def _run(self, query: str) -> str:
        return result
```

### Orchestrator (building now)
```python
orchestrator = factory.create_orchestrator()
orchestrator.register("name", agent, keywords=["..."])
response = orchestrator.route("user query")
```

---

## Goal

Build agents that are "AI amazing to the customer" - reliable, fast, trustworthy.

The human's apps: **Friday** (voice AI assistant), **Jarvis** (digital ecosystem manager).

---

## When in Doubt

1. Check `PROGRESS.md` for what to do next
2. Check the relevant spec doc for how to do it
3. Validate that it works
4. Commit checkpoint
5. Move to next item

Keep it simple. Keep it working. Keep moving forward.
```

---

Now you need the supporting docs. Here's the file structure:
```
Agent-Factory/
+-- CLAUDE.md              # Meta doc (above) - Claude CLI reads this
+-- PROGRESS.md            # Checklist - tracks what's done
+-- CLAUDE_CODEBASE.md     # Existing - your current code docs
+-- docs/
    +-- ARCHITECTURE.md    # Full architecture + pipeline diagram
    +-- PATTERNS.md        # 8 Google ADK patterns with examples
    +-- PRODUCTION.md      # 4 levels of production readiness
    +-- PHASE1_SPEC.md     # Detailed Phase 1 implementation
    +-- PHASE2_SPEC.md     # (create when ready)