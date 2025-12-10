# Autonomous Development Plan

**Purpose:** Enable 8-hour unattended development sessions where Claude Code works continuously without asking questions.

**User's Goal:** "Build this while I sleep, and then come back 8 hours later, and it's done."

---

## How This Works

1. **Intent Specification:** This document + strategy docs = complete specification
2. **Decision Rules:** Pre-defined answers to common questions
3. **Progress Tracking:** Automatic updates to todo list + commits
4. **Escalation Only:** Only stop if encountering truly undefined scenarios

---

## Current Session Goal

**Complete GitHub Strategy Implementation - Week 1 Foundation (Remaining Tasks)**

Based on strategy documents and current state:
- ✅ Core infrastructure complete (orchestrator, webhook, database schema, models)
- ⏳ 5 remaining tasks from todo list
- Target: All tasks complete, PR ready for review

---

## Task Queue (Ordered by Priority)

### Task 1: Create Telegram Bot (PRIMARY INTERFACE)
**File:** `telegram_bot.py`
**Priority:** CRITICAL (user explicitly requested this as primary interface)
**Time Estimate:** 60-90 min

**Specification:**
- Commands: `/status`, `/approve <id>`, `/reject <id> <reason>`, `/agents`, `/metrics`, `/issue <title>`
- Uses python-telegram-bot library
- Connects to Supabase (agent_status, approval_requests, agent_jobs tables)
- Sends notifications (daily standup, alerts, approval requests)
- Runs in background (separate process from orchestrator)

**Decision Rules:**
- Q: What tone for messages? → Professional but friendly (like Slack notifications)
- Q: HTML or plain text? → Markdown formatting (supported by Telegram)
- Q: How verbose? → Concise (3-5 lines max per message)
- Q: Error handling? → Retry 3x with exponential backoff, log failures to Supabase

**Success Criteria:**
- Bot responds to all 6 commands
- Connects to Supabase successfully
- YOU can approve items from phone
- Daily standup delivered at 8 AM (user's timezone)

---

### Task 2: Create AI Rules Document
**File:** `docs/ai-rules.md`
**Priority:** HIGH (sets standards for future AI work)
**Time Estimate:** 30-45 min

**Specification:**
- Audience: AI agents working on this codebase (Claude, GPT-4, future agents)
- Sections:
  1. Architecture patterns (orchestrator, agents, tools)
  2. Code standards (Python, Pydantic, type hints, docstrings)
  3. Security rules (never hardcode secrets, validate inputs, audit logging)
  4. Testing requirements (pytest, 80% coverage, integration tests)
  5. Git workflow (worktrees, commit messages, PR process)
  6. Decision-making authority (what needs approval, what's autonomous)

**Decision Rules:**
- Q: How detailed? → Medium (examples for each rule, not exhaustive)
- Q: Tone? → Directive but educational (explain WHY, not just WHAT)
- Q: What if conflict with CLAUDE.md? → CLAUDE.md wins (this doc extends, doesn't override)

**Success Criteria:**
- Document covers all 6 sections
- Includes code examples
- References existing patterns (CLAUDE.md, CONTRIBUTING.md)

---

### Task 3: Create 18 Agent Skeleton Files
**Files:** `agents/{team}/{agent_name}_agent.py` (18 files)
**Priority:** HIGH (enables parallel agent development)
**Time Estimate:** 90-120 min

**Specification:**
- Use AGENT_ORGANIZATION.md as complete spec
- Each file structure:
  - Module docstring (purpose, schedule, tools)
  - AgentBase inheritance (if exists, else standalone class)
  - All public methods with docstrings, type hints, pass statements
  - No implementation (skeletons only)
- Organize by team:
  - `agents/executive/` (ai_ceo_agent.py, ai_chief_of_staff_agent.py)
  - `agents/research/` (research_agent.py, atom_builder_agent.py, atom_librarian_agent.py, quality_checker_agent.py)
  - `agents/content/` (master_curriculum_agent.py, content_strategy_agent.py, scriptwriter_agent.py, seo_agent.py, thumbnail_agent.py)
  - `agents/media/` (voice_production_agent.py, video_assembly_agent.py, publishing_strategy_agent.py, youtube_uploader_agent.py)
  - `agents/engagement/` (community_agent.py, analytics_agent.py, social_amplifier_agent.py)

**Decision Rules:**
- Q: Include __init__.py? → Yes, for each team folder + agents/ root
- Q: Import structure? → Relative imports within team, absolute from root
- Q: Method names? → From AGENT_ORGANIZATION.md responsibilities (e.g., ResearchAgent.scrape_web())
- Q: Add TODOs? → Yes, for each method (# TODO: Implement [method purpose])

**Success Criteria:**
- All 18 agent files created
- All files import successfully (python -c "from agents.executive.ai_ceo_agent import AICEOAgent")
- Each file has complete docstrings
- Each file has method signatures matching AGENT_ORGANIZATION.md

---

### Task 4: Update CLAUDE.md with GitHub Strategy
**File:** `CLAUDE.md` (in worktree, not main)
**Priority:** MEDIUM (documentation)
**Time Estimate:** 30-45 min

**Specification:**
- Add new section: "GitHub Strategy Implementation"
- Document orchestrator pattern (git pull → process jobs → route to agents)
- Document webhook pattern (GitHub events → Supabase jobs → orchestrator)
- Document Telegram interface (primary user interface)
- Link to new files (orchestrator.py, webhook_handler.py, telegram_bot.py)
- Update validation commands

**Decision Rules:**
- Q: Where to add? → After "PLC Implementation References" section
- Q: How much detail? → High-level architecture + links to detailed docs
- Q: Update existing sections? → Only if contradictions exist
- Q: Tone? → Match existing CLAUDE.md (concise, directive)

**Success Criteria:**
- GitHub Strategy section added (300-500 words)
- Links to orchestrator.py, webhook_handler.py, telegram_bot.py
- Validation commands updated
- No contradictions with existing content

---

### Task 5: Create GitHub Issues for Agent Development
**Target:** GitHub Issues #50-67 (one per agent)
**Priority:** MEDIUM (planning)
**Time Estimate:** 60-90 min

**Specification:**
- Create issues for Weeks 2-7 agent development
- Use IMPLEMENTATION_ROADMAP.md Week 2-7 sections
- Template per issue:
  - Title: "[Week X] Build {AgentName}Agent"
  - Description: Responsibilities from AGENT_ORGANIZATION.md
  - Acceptance Criteria: Success metrics from AGENT_ORGANIZATION.md
  - Labels: agent-development, week-X, {team-name}
  - Milestone: Week X
  - Assignee: None (to be assigned)

**Decision Rules:**
- Q: Create all 18 at once? → Yes (batch operation via gh cli)
- Q: Link dependencies? → Yes, use "Depends on #N" in description
- Q: Add time estimates? → Yes, from IMPLEMENTATION_ROADMAP.md
- Q: Include file paths? → Yes, exact file from AGENT_ORGANIZATION.md

**Success Criteria:**
- 18 issues created (#50-67)
- All issues have complete descriptions
- Dependencies linked
- Milestones assigned

---

## Decision Framework

### When to Continue Autonomously
- Implementing something explicitly defined in strategy docs
- Creating files following established patterns (agent skeletons, docs)
- Writing code matching AGENT_ORGANIZATION.md specs
- Fixing errors with clear solutions (import errors, syntax errors)
- Updating documentation to reflect completed work

### When to Escalate (STOP and REPORT)
- Ambiguity in requirements not resolved by strategy docs
- Security concerns (API keys, credentials, permissions)
- Architectural decision not covered by existing patterns
- External dependency failure (API outage, service unavailable)
- User preference needed (tone, branding, naming)
- Budget/cost implications (new paid service)
- Failed same task 3+ times with different approaches

---

## Progress Tracking Pattern

**Every 30 minutes:**
1. Update todo list (mark completed tasks, add in_progress)
2. Commit progress (checkpoint commit)
3. Push to branch (backup)
4. Log decision if made (append to DECISION_LOG.md)

**After each task:**
1. Mark task completed immediately
2. Commit with descriptive message
3. Validate (run import check or test command)
4. Move to next task

**Pattern:**
```bash
# After Task 1 (Telegram Bot)
git add telegram_bot.py
git commit -m "feat: Add Telegram bot for user notifications

Implements primary user interface with 6 commands:
- /status, /approve, /reject, /agents, /metrics, /issue

Features:
- Supabase integration for agent monitoring
- Markdown formatting for messages
- Retry logic (3x with exponential backoff)
- Daily standup delivery (8 AM user timezone)

Connects to:
- agent_status table (monitoring)
- approval_requests table (approvals)
- agent_jobs table (job creation)

Usage:
  python telegram_bot.py

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin github-strategy
```

---

## Decision Log Format

**File:** `DECISION_LOG.md` (create if doesn't exist)

**Template:**
```markdown
## Decision: [Short Title]
**Date:** 2025-12-10
**Context:** [What was the situation?]
**Options Considered:** [What were the choices?]
**Decision:** [What did I choose?]
**Rationale:** [Why?]
**Impact:** [What does this affect?]
```

---

## Validation Commands

**After each task:**
```bash
# Task 1: Telegram Bot
python -c "from telegram_bot import TelegramBot; print('Telegram Bot OK')"

# Task 2: AI Rules
cat docs/ai-rules.md | wc -l  # Should be >200 lines

# Task 3: Agent Skeletons
python -c "from agents.executive.ai_ceo_agent import AICEOAgent; print('Agents OK')"

# Task 4: CLAUDE.md Update
grep "GitHub Strategy" CLAUDE.md  # Should return match

# Task 5: GitHub Issues
gh issue list --label agent-development | wc -l  # Should be 18
```

---

## Current Environment Context

**Working Directory:** `C:\Users\hharp\OneDrive\Desktop\agent-factory-github-strategy`
**Branch:** `github-strategy`
**Remote:** `origin/github-strategy`

**Completed Files:**
- core/models.py (780 lines, complete Pydantic schemas)
- docs/supabase_agent_migrations.sql (650+ lines, 7 tables)
- orchestrator.py (400+ lines, 24/7 loop)
- webhook_handler.py (400+ lines, FastAPI server)

**Environment Variables Available (.env):**
- SUPABASE_URL
- SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY
- GITHUB_WEBHOOK_SECRET
- TELEGRAM_BOT_TOKEN (assumed available, create if not)

**Python Version:** 3.10+
**Package Manager:** Poetry

---

## Success Criteria for This Session

**Minimum Viable (4-6 hours):**
- ✅ Telegram bot functional (can send/receive messages)
- ✅ AI rules document complete
- ✅ All 18 agent skeleton files created and importable
- ✅ Checkpoint commits every 30-60 minutes
- ✅ Progress tracked in todo list

**Stretch Goal (6-8 hours):**
- ✅ CLAUDE.md updated
- ✅ All 18 GitHub issues created
- ✅ Pull request created and ready for review
- ✅ README.md updated with setup instructions

**Final Output:**
- Pull request URL
- Summary of completed tasks
- Decision log with any key choices made
- Next steps recommendation

---

## Emergency Escalation

**If I encounter any of these, STOP immediately and report:**
- Security vulnerability (exposed credentials, SQL injection risk)
- Data loss risk (destructive operation without backup)
- Cost implications (>$10/mo new service)
- Architectural conflict (contradicts established patterns)
- External dependency critical failure (Supabase down, GitHub API unavailable)

**Report Format:**
```
🚨 ESCALATION NEEDED 🚨

Issue: [What happened?]
Context: [What was I doing?]
Impact: [What's at risk?]
Options: [What are possible solutions?]
Recommendation: [What do I suggest?]
```

---

## Start Command

To enable autonomous mode, Claude Code should:
1. Read this document
2. Read strategy documents (TRIUNE_STRATEGY.md, AGENT_ORGANIZATION.md, IMPLEMENTATION_ROADMAP.md)
3. Start with Task 1 (Telegram Bot)
4. Work through task queue in order
5. Track progress every 30 min
6. Escalate only if hitting decision framework "STOP" conditions

**Let's build while you sleep. 🌙**
