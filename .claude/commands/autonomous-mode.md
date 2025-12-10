# /autonomous-mode

**Enable 8-hour unattended development sessions**

## What This Does

Activates autonomous building mode where Claude Code:
- Works continuously for 8+ hours without asking questions
- Uses `AUTONOMOUS_PLAN.md` as the complete specification
- Makes decisions based on strategy documents (no guessing)
- Tracks progress automatically (commits every 30-60 min)
- Escalates only for truly undefined scenarios

## When to Use

- You want to "build while you sleep"
- Clear task queue exists (`AUTONOMOUS_PLAN.md`)
- Strategy docs provide complete intent specification
- You'll be unavailable for 4-8+ hours

## How It Works

1. Reads `AUTONOMOUS_PLAN.md` (task queue + decision rules)
2. Reads strategy documents (complete specifications)
3. Works through tasks in priority order
4. Makes decisions using pre-defined rules
5. Commits progress every 30 min
6. Logs decisions in `DECISION_LOG.md`
7. Stops only for escalation-worthy issues

## Example Usage

```bash
# In Claude Code
/autonomous-mode
```

**Output:**
```
🤖 AUTONOMOUS MODE ACTIVATED

Session Goal: Complete GitHub Strategy Implementation (5 remaining tasks)
Estimated Time: 4-6 hours
Task Queue:
  1. [HIGH] Create Telegram Bot (60-90 min)
  2. [HIGH] Create AI Rules Document (30-45 min)
  3. [HIGH] Create 18 Agent Skeleton Files (90-120 min)
  4. [MED] Update CLAUDE.md (30-45 min)
  5. [MED] Create GitHub Issues (60-90 min)

Decision Framework: Loaded from AUTONOMOUS_PLAN.md
Intent Specification: TRIUNE_STRATEGY.md, AGENT_ORGANIZATION.md, IMPLEMENTATION_ROADMAP.md

Starting Task 1: Telegram Bot...
```

## What Gets Built

Based on `AUTONOMOUS_PLAN.md`, this session will complete:

**Task 1: Telegram Bot** (`telegram_bot.py`)
- Commands: /status, /approve, /reject, /agents, /metrics, /issue
- Supabase integration (agent_status, approval_requests, agent_jobs)
- Daily standup delivery (8 AM user timezone)
- Retry logic (3x exponential backoff)

**Task 2: AI Rules** (`docs/ai-rules.md`)
- Architecture patterns
- Code standards (Python, Pydantic, type hints)
- Security rules (no hardcoded secrets, audit logging)
- Testing requirements (pytest, 80% coverage)
- Git workflow (worktrees, commit messages)

**Task 3: Agent Skeletons** (18 files)
- `agents/executive/` (2 agents)
- `agents/research/` (4 agents)
- `agents/content/` (5 agents)
- `agents/media/` (4 agents)
- `agents/engagement/` (3 agents)
- All with docstrings, type hints, method signatures (no implementation)

**Task 4: CLAUDE.md Update**
- New section: "GitHub Strategy Implementation"
- Document orchestrator + webhook + Telegram patterns
- Update validation commands

**Task 5: GitHub Issues**
- Issues #50-67 (one per agent)
- Complete descriptions from AGENT_ORGANIZATION.md
- Dependencies linked
- Milestones assigned (Week 2-7)

## Progress Tracking

**Every 30 minutes:**
- Update todo list (mark completed, update in_progress)
- Checkpoint commit
- Push to branch

**After each task:**
- Mark completed immediately
- Commit with descriptive message
- Validate (import check or test)
- Move to next task

## Decision Making

**Autonomous Decisions (no questions):**
- File structure (follows existing patterns)
- Code style (follows CONTRIBUTING.md)
- Naming conventions (follows AGENT_ORGANIZATION.md)
- Error handling (retry 3x, log to Supabase)
- Commit messages (follows conventional commits)

**Escalation Triggers (STOP and REPORT):**
- Security concerns (credentials, permissions)
- Architectural conflicts (contradicts patterns)
- External failures (API outages)
- User preference needed (branding, tone)
- Budget implications (new paid service)
- Ambiguity not resolved by docs

## Success Criteria

**Minimum (4-6 hours):**
- ✅ Telegram bot functional
- ✅ AI rules complete
- ✅ 18 agent skeletons created
- ✅ Checkpoint commits every 30-60 min

**Stretch (6-8 hours):**
- ✅ CLAUDE.md updated
- ✅ GitHub issues created
- ✅ Pull request ready for review

## Final Output

When complete, you'll receive:
- Summary of completed tasks
- Pull request URL (if created)
- Decision log (key choices made)
- Next steps recommendation
- Total time elapsed

## Safety Features

**Built-in Safeguards:**
- Read-only until task starts (verify intent)
- Git worktree isolation (no conflicts)
- Checkpoint commits (rollback points)
- Decision logging (audit trail)
- Escalation protocol (stop if needed)

**What It Won't Do:**
- Merge to main (only creates PR)
- Delete existing code
- Deploy to production
- Make breaking changes without docs
- Guess at ambiguous requirements

## Comparison to Normal Mode

| Aspect | Normal Mode | Autonomous Mode |
|--------|-------------|-----------------|
| Questions | Frequent (clarify intent) | Rare (only escalations) |
| Decision Speed | Waits for approval | Uses pre-defined rules |
| Progress Updates | On request | Automatic (every 30 min) |
| Session Length | 30-60 min | 4-8+ hours |
| User Attention | High (active collaboration) | Low (review later) |
| Use Case | Exploration, design | Execution, building |

## When NOT to Use

- Exploring new ideas (need discussion)
- Major architectural decisions (need approval)
- Working with production systems (risky)
- Unclear requirements (need clarification)
- Quick tasks < 1 hour (overhead not worth it)

## Resuming After Break

If session is interrupted:
1. Check `DECISION_LOG.md` (what was done)
2. Check git log (what was committed)
3. Check todo list (what's remaining)
4. Run `/autonomous-mode` again (resumes from last task)

## Implementation Details

**Reads these files on activation:**
- `AUTONOMOUS_PLAN.md` (task queue + decision rules)
- `docs/TRIUNE_STRATEGY.md` (complete vision)
- `docs/AGENT_ORGANIZATION.md` (18-agent specs)
- `docs/IMPLEMENTATION_ROADMAP.md` (week-by-week plan)
- `.claude/commands/autonomous-mode.md` (this file)

**Creates these files during session:**
- `DECISION_LOG.md` (decisions made)
- Progress commits (every 30 min)
- Task deliverables (per AUTONOMOUS_PLAN.md)

**Updates these files:**
- Todo list (mark completed)
- CLAUDE.md (if Task 4 reached)

## Tips for Best Results

1. **Before activating:**
   - Ensure `AUTONOMOUS_PLAN.md` task queue is clear
   - Verify strategy docs are complete
   - Commit any work in progress
   - Set expectations (4-8 hours)

2. **During session:**
   - Don't interrupt (let it run)
   - Check progress periodically (git log)
   - Trust the decision framework

3. **After session:**
   - Review `DECISION_LOG.md` (understand choices)
   - Review git diff (verify work)
   - Approve or request changes
   - Merge PR when satisfied

## Roadmap

**v1.0 (current):**
- Single session execution
- Manual activation
- Decision logging
- Progress commits

**v2.0 (future):**
- Multi-day continuous mode
- Self-updating task queue
- Adaptive decision-making
- Real-time progress dashboard

**v3.0 (vision):**
- Fully autonomous orchestrator
- Self-learning from feedback
- Multi-agent coordination
- Zero human intervention needed

---

**Ready to build while you sleep? Run `/autonomous-mode`** 🌙
