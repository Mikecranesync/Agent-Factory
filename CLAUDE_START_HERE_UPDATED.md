# CLAUDE START HERE - Three-Layer Company Implementation

**Status:** Ready to Build
**Date:** 2025-12-19
**Total Tasks:** 20 subtasks across 3 layers

---

## What to Read First

1. **COMPLETE_UNIFIED_SPECIFICATION.md** - Complete strategy (all 3 layers)
2. **TASK.md** - Current work in progress
3. **backlog/tasks/** - All 20 subtasks

---

## Three-Layer Architecture

```
                        YOU (CEO)
                            |
        +-------------------+-------------------+
        |                   |                   |
    TIER 0              TIER 1            SKUNK WORKS
Main Factory       Research Dept         R&D Lab
(40 hours)         (16 hours)           (8 hours)
    |                   |                   |
Telegram Bot      5 Explorers         Scraper
Intent Decoder    + Manager           + Sandbox
Orchestrator                          + Validator
7 Agents
Status Pipeline
```

---

## TIER 0: Main Factory Foundation (8 subtasks, 40 hours)

**Parent EPIC:** task-38

**Subtasks:**
- **task-38.5:** Telegram Bot Foundation (6h)
- **task-38.6:** Intent Decoder - Ollama Mistral (6h)
- **task-38.7:** Orchestrator Core (8h)
- **task-38.8:** Agent Registration System (4h)
- **task-38.9:** 7 Specialized Team Lead Agents (8h)
- **task-38.10:** Status Reporting Pipeline (4h)
- **task-38.11:** Error Handling & Fallbacks (2h)
- **task-38.12:** TIER 0 Testing & Validation Suite (2h)

**View all:** `backlog task list --parent-task-id task-38`

**Command Flow:**
```
Telegram Message → Intent Decoder → Orchestrator → Team Lead Agent → Response
       ↓                 ↓               ↓                ↓             ↓
  (task-38.5)      (task-38.6)     (task-38.7)     (task-38.9)   (task-38.10)
```

---

## TIER 1: Research Department (7 subtasks, 16 hours)

**Parent EPIC:** task-39

**Subtasks:**
- **task-39.7:** Research Manager Core (3h)
- **task-39.1:** Explorer 1 - Agentic Frameworks (2.5h)
- **task-39.2:** Explorer 2 - CI/CD Automation (2.5h)
- **task-39.3:** Explorer 3 - Local LLM Inference (2.5h)
- **task-39.4:** Explorer 4 - PLC & Industrial (2.5h)
- **task-39.5:** Explorer 5 - Telegram & Remote (2.5h)
- **task-39.6:** Source Verification Pipeline (0.5h)

**View all:** `backlog task list --parent-task-id task-39`

**Research Pipeline:**
```
5 Explorers (every 6 hours) → Research Manager → Filter → Score → Publish to Telegram
     |                              |                |        |          |
(task-39.1-39.5)              (task-39.7)     (quality)  (relevance) (breaking news)
```

**Monitoring Domains:**
- **Agentic Frameworks:** LangGraph, Crew AI, OpenDevin
- **CI/CD:** pytest, SWE-agent, GitHub Actions
- **Local LLMs:** Ollama, Mistral, DeepSeek
- **PLC/Industrial:** RIVET, Factory IO, OPC UA
- **Telegram:** Bot frameworks, API updates

---

## Skunk Works R&D Lab (5 subtasks, 8 hours)

**Parent EPIC:** task-40

**Subtasks:**
- **task-40.6:** Scraper Infrastructure (2.5h)
- **task-40.7:** Sandbox Docker Environment (2h)
- **task-40.3:** Experiment Runner & Benchmarking (2h)
- **task-40.4:** Validator Quality Gates (1h)
- **task-40.5:** Reporting Pipeline to CEO (0.5h)

**View all:** `backlog task list --parent-task-id task-40`

**Experiment Flow:**
```
Weekly Scraper → Sandbox → Experiment → Validate → Report to CEO (Fridays 3pm)
      |            |           |            |             |
(task-40.6)   (task-40.7)  (task-40.3)  (task-40.4)  (task-40.5)
```

**CEO Commands:**
- `/skunk approve` - Adopt immediately
- `/skunk sandbox` - More testing needed
- `/skunk archive` - Good idea, not now
- `/skunk reject` - Not viable

---

## Your First Command

**Send to Telegram bot:**
```
Build me a simple hello world agent
```

**Expected Flow:**
1. Telegram Bot receives message (task-38.5)
2. Intent Decoder classifies as "code" intent (task-38.6)
3. Orchestrator routes to Codegen Lead (task-38.7, task-38.8)
4. Codegen Lead generates code (task-38.9)
5. Status updates appear in Telegram (task-38.10)

---

## What Success Looks Like

### Week 1 (TIER 0 Complete)
- ✅ Telegram bot operational
- ✅ Intent decoder classifies commands
- ✅ Orchestrator routes to correct agents
- ✅ 7 team lead agents executing work
- ✅ Status bubbles appear in Telegram

### Week 2 (TIER 1 + Skunk Works Complete)
- ✅ Research team discovering 5+ innovations/week
- ✅ Breaking news articles with source links
- ✅ Skunk Works scraper running (background)
- ✅ First experiments logged

### Week 3+ (Full Autonomous Operation)
- ✅ All agents working 24/7
- ✅ PRs flowing automatically
- ✅ Research alerts daily
- ✅ Skunk Works reports weekly
- ✅ You make strategic decisions via Telegram

---

## Communication Protocol

**To Main Factory (TIER 0):**
```
"Add dark mode to the settings page"
"Fix the bug in checkout flow"
"Run all tests and create a PR"
```

**To Research Team (TIER 1):**
```
"What's new in LangGraph?"
"Find me the latest Ollama updates"
"Any new pytest features?"
```

**To Skunk Works:**
```
"/skunk status" - View current experiments
"/skunk approve experiment-42" - Adopt innovation
"/skunk archive experiment-38" - Good idea, later
```

---

## Next Steps

**1. View first task:**
```bash
backlog task view task-38.5
```

**2. Start implementation:**
```bash
# Mark as In Progress
backlog task edit task-38.5 --status "In Progress"

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py

# Follow acceptance criteria in task-38.5
```

**3. Iterate:**
- Complete task-38.5
- Mark "Done", move to task-38.6
- Repeat for all 20 tasks

**4. Monitor progress:**
```bash
# View all TIER 0 tasks
backlog task list --parent-task-id task-38

# View In Progress tasks
backlog task list --status "In Progress"

# Sync to TASK.md anytime
poetry run python scripts/backlog/sync_tasks.py
```

---

## Reference Documents

**Strategy:**
- `COMPLETE_UNIFIED_SPECIFICATION.md` - Three-layer company design
- `CLAUDE.md` - AI assistant instructions and execution rules

**Task Management:**
- `backlog/README.md` - Backlog.md workflow guide
- `TASK.md` - Current work (auto-synced)

**Parent EPICs:**
- `backlog/tasks/task-38.md` - TIER 0: Supercritical Main Factory
- `backlog/tasks/task-39.md` - TIER 1: Critical Research Department
- `backlog/tasks/task-40.md` - Skunk Works R&D Lab

**Implementation:**
- `docs/patterns/GIT_WORKTREE_GUIDE.md` - Worktree workflow
- `docs/patterns/SECURITY_STANDARDS.md` - Security by design

---

## Quick Commands Reference

```bash
# View all tasks
backlog task list

# View tasks by parent
backlog task list --parent-task-id task-38

# View task details
backlog task view task-38.5

# Mark task in progress
backlog task edit task-38.5 --status "In Progress"

# Mark task done
backlog task edit task-38.5 --status "Done"

# Add implementation notes
backlog task edit task-38.5 --notes-append "Implemented webhook handler using python-telegram-bot"

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py
```

---

## Validation Commands

```bash
# Verify TIER 0 tasks
backlog task list --parent-task-id task-38
# Expected: 8 tasks

# Verify TIER 1 tasks
backlog task list --parent-task-id task-39
# Expected: 7 tasks

# Verify Skunk Works tasks
backlog task list --parent-task-id task-40
# Expected: 5 tasks

# Total task count
backlog task list | wc -l
# Expected: 20+ (including parent EPICs)
```

---

## The Vision

You're building a **three-layer autonomous company**:

**Layer 1 (Main Factory)** - Executes your vision
**Layer 2 (Research Dept)** - Discovers what's possible
**Layer 3 (Skunk Works)** - Validates the future

Together, they create a **3-6 month competitive lead** through:
- 24/7 autonomous operation
- Continuous innovation discovery
- Validated frontier technology adoption
- CEO strategic control via Telegram

---

**Let's build your three-layer autonomous company.**

🚀
