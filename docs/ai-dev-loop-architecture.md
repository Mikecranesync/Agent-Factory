# AI Development Control Loop - System Architecture

**Version:** 1.0
**Last Updated:** 2025-12-17
**Status:** Production Design
**Parent Task:** [task-23 - AI Dev Control Loop Dashboard](../backlog/tasks/task-23.md)

---

## Table of Contents

1. [Overview & Vision](#overview--vision)
2. [Core Components](#core-components)
   - [2.1 Backlog.md (Task Management Layer)](#21-backlogmd-task-management-layer)
   - [2.2 Headless Orchestrator](#22-headless-orchestrator)
   - [2.3 Claude Code CLI Agent](#23-claude-code-cli-agent)
   - [2.4 Safety Monitor](#24-safety-monitor)
   - [2.5 PR Creator](#25-pr-creator)
   - [2.6 Issue Queue Builder](#26-issue-queue-builder)
3. [Data Flow & Control Loop](#data-flow--control-loop)
4. [Task Management Layer](#task-management-layer)
5. [Execution Layer](#execution-layer)
6. [Integration & Safety](#integration--safety)
7. [Extension Guide](#extension-guide)

---

## Overview & Vision

### What is the AI Development Control Loop?

The **AI Development Control Loop** is an autonomous software development system that enables unattended, intelligent task execution using AI agents. It transforms Backlog.md task management into an execution engine that works overnight to solve problems, implement features, and create pull requests—all while enforcing strict safety limits.

**Core Concept:** Tasks are the unit of work. The control loop continuously:
1. Queries Backlog.md for eligible tasks (status=To Do, dependencies satisfied)
2. Routes tasks to appropriate agents (Claude Code CLI, specialized agents)
3. Executes tasks in isolated git worktrees
4. Creates draft PRs for human review
5. Updates Backlog.md with results
6. Repeats until safety limits reached or queue exhausted

### Key Features

1. **Autonomous Execution** - Runs unattended during off-hours (nightly 2am-6am UTC)
2. **Safety-First Design** - Hard limits prevent runaway costs, time, and failures
3. **Multi-Repository Support** - Can manage tasks across multiple repositories
4. **Intelligent Routing** - Matches task types to specialized agents automatically
5. **Draft PRs Only** - All work requires human review before merge
6. **Failure Recovery** - Circuit breakers halt execution on systemic issues
7. **Real-Time Monitoring** - Telegram notifications provide live session updates

### Success Metrics

| Metric | Target | Purpose |
|--------|--------|---------|
| **Tasks/Night** | 5-10 | Productivity baseline |
| **Success Rate** | >75% | Quality threshold |
| **Cost Efficiency** | <$5/night | Budget constraint |
| **Time Window** | <4 hours | Overnight window (2am-6am) |
| **Failure Recovery** | <3 consecutive | Circuit breaker threshold |

### Target Use Cases

**When to Use Autonomous Mode:**
- Repetitive tasks with clear acceptance criteria
- Bug fixes with reproducible steps
- Documentation updates
- Test coverage improvements
- Code cleanup and refactoring
- Feature implementation with detailed specs

**When to Use Manual Mode:**
- Architecture decisions
- Security-critical changes
- Design discussions
- Ambiguous requirements
- Cross-cutting concerns
- Production deployments

### Current Implementation Status

**Phase Breakdown (8 total):**

| Phase | Component | Status | Lines | Notes |
|-------|-----------|--------|-------|-------|
| **Phase 1** | Autonomous execution (issue-based) | ✅ Complete | 2,500 | Nightly issue solver |
| **Phase 2** | Backlog.md integration | ✅ Complete | 1,000 | Task management layer |
| **Phase 3** | Headless orchestrator (Backlog tasks) | 📋 Planned | ~400 | task-23.2 |
| **Phase 4** | Multi-repo support | 📋 Planned | ~300 | Config-driven repos |
| **Phase 5** | Dashboard UI (React) | 📋 Planned | ~800 | Web interface |
| **Phase 6** | Telegram bot controls | 📋 Planned | ~400 | Mobile management |
| **Phase 7** | Agent marketplace | 📋 Future | TBD | Custom agent plugins |
| **Phase 8** | Enterprise features | 📋 Future | TBD | Multi-tenant, RBAC |

**Current Capabilities:**
- ✅ GitHub issue-based autonomous solver (scripts/autonomous/autonomous_runner.py)
- ✅ Safety monitoring with cost/time/failure limits (scripts/autonomous/safety_monitor.py)
- ✅ Smart issue queue building with hybrid scoring (scripts/autonomous/issue_queue_builder.py)
- ✅ Draft PR creation workflow (scripts/autonomous/pr_creator.py)
- ✅ Telegram notifications for session updates (scripts/autonomous/telegram_notifier.py)
- ✅ Backlog.md task management with MCP integration (backlog/README.md)
- ✅ TASK.md auto-sync for Claude Code integration (scripts/backlog/sync_tasks.py)

**Next Milestones:**
- **Week 1:** Implement Headless Orchestrator (task-23.2) - Backlog task consumption
- **Week 2:** Multi-repo configuration support (task-23.4)
- **Week 3:** React dashboard prototype (task-23.5)
- **Month 2:** Production deployment with monitoring

---

## Core Components

The AI Dev Control Loop consists of 6 major components, each with a specific responsibility:

```
┌──────────────────────────────────────────────────────────────┐
│  1. BACKLOG.MD - Task Management Layer                      │
│     Source of truth for all work items                      │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  2. HEADLESS ORCHESTRATOR - Control Loop Engine             │
│     Fetches tasks, routes to agents, manages sessions       │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  3. CLAUDE CODE CLI AGENT - Execution Environment           │
│     Isolated worktrees, CLAUDE.md prompts, tool access      │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  4. SAFETY MONITOR - Limit Enforcement                      │
│     Cost/time/failure tracking, circuit breakers            │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  5. PR CREATOR - GitHub Integration                          │
│     Branch creation, draft PRs, issue linking               │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  6. ISSUE QUEUE BUILDER - Task Selection                    │
│     Priority scoring, constraint checking, queue building   │
└──────────────────────────────────────────────────────────────┘
```

### 2.1 Backlog.md (Task Management Layer)

**Purpose:** Structured task storage using YAML frontmatter + Markdown files.

**File Structure:**
```
backlog/
├── tasks/                 # Active tasks (To Do, In Progress)
│   ├── task-23.md         # EPIC: AI Dev Control Loop Dashboard
│   ├── task-23.1.md       # Subtask 1: Fork and vendor Backlog.md
│   ├── task-23.2.md       # Subtask 2: Headless Claude runner
│   └── task-23.3.md       # Subtask 3: Architecture documentation (THIS FILE)
├── completed/             # Archived completed tasks
├── drafts/                # WIP task ideas
├── config.yml             # Backlog.md configuration
└── README.md              # Comprehensive workflow guide
```

**Task Schema (YAML Frontmatter):**
```yaml
---
id: task-23.3                    # Unique identifier (auto-generated)
title: 'BUILD: Define AI Dev Loop architecture (AI Dev Loop 2/6)'
status: To Do                    # To Do | In Progress | Done
priority: high                   # high | medium | low
labels: [build, ai-loop, architecture, documentation]
dependencies: []                 # Task IDs that must complete first
parent_task_id: task-23          # Epic relationship (optional)
created_at: 2025-12-17T22:00:00Z
updated_at: 2025-12-17T22:00:00Z
---

## Description
Create comprehensive architecture document describing all control loop components
so humans and agents can reason about the system.

## Acceptance Criteria
- [ ] #1 docs/ai-dev-loop-architecture.md exists with all major components described
- [ ] #2 Diagrams (text or Mermaid) cover main E2E loop
- [ ] #3 Another developer/agent can read doc and understand adding new task type/repo
```

**MCP Integration:**
Tasks are accessible programmatically via Backlog.md MCP server:
```python
from mcp import backlog

# Query tasks
tasks = backlog.task_list(status="To Do", priority="high")
# Returns: [{"id": "task-23.3", "title": "BUILD: ...", ...}, ...]

# View task details
task = backlog.task_view("task-23.3")
# Returns: {"id": "task-23.3", "title": "...", "description": "...", "acceptanceCriteria": [...]}

# Update task status
backlog.task_edit("task-23.3", status="In Progress")

# Add execution notes
backlog.task_edit(
    "task-23.3",
    notes_append=["Started execution at 2025-12-17 22:30", "Created worktree"]
)

# Mark complete
backlog.task_edit("task-23.3", status="Done")
```

**TASK.md Auto-Sync:**
Auto-generated view layer synced from Backlog.md:
```markdown
# Active Tasks

<!-- BACKLOG_SYNC:CURRENT:BEGIN -->
## Current Task
### task-23.3: BUILD: Define AI Dev Loop architecture
**Status:** In Progress
**Priority:** high
**Parent:** task-23 (AI Dev Control Loop Dashboard)
<!-- BACKLOG_SYNC:CURRENT:END -->

<!-- BACKLOG_SYNC:BACKLOG:BEGIN -->
## Backlog

### High Priority
- task-23.2: BUILD: Headless Claude runner (AI Dev Loop 3/6)
- task-4: BUILD: RIVET Pro Phase 4 - Orchestrator

### Medium Priority
- task-5: BUILD: RIVET Pro Phase 5 - Research Pipeline
- task-6: BUILD: RIVET Pro Phase 6 - Logging
<!-- BACKLOG_SYNC:BACKLOG:END -->
```

Sync triggered by: `python scripts/backlog/sync_tasks.py`

**Key Principles:**
- **Source of Truth:** Backlog.md tasks own all metadata (status, priority, acceptance criteria)
- **One-Way Sync:** Backlog.md → TASK.md (TASK.md is read-only view)
- **Atomic Updates:** MCP tools handle concurrency and validation
- **Version Control:** All tasks are git-tracked markdown files

---

### 2.2 Headless Orchestrator

**Purpose:** Main control loop engine that coordinates task fetching, routing, execution, and result processing.

**Architecture:**
```python
class HeadlessOrchestrator:
    """
    Main control loop for autonomous task execution.

    Components:
        - TaskFetcher: Queries Backlog.md MCP for eligible tasks
        - AgentRouter: Matches task type to agent (Claude Code, custom)
        - SessionManager: Tracks active sessions, enforces concurrency
        - ResultProcessor: Updates Backlog.md based on outcome

    Workflow:
        1. Fetch tasks: status=To Do, priority=high, dependencies satisfied
        2. Route to agent based on labels/title prefix
        3. Create isolated worktree
        4. Execute task
        5. Process result (PR creation or failure logging)
        6. Update SafetyMonitor
        7. Repeat until budget exhausted or queue empty
    """

    def __init__(
        self,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0,
        max_consecutive_failures: int = 3
    ):
        # Initialize components
        self.task_fetcher = TaskFetcher()
        self.agent_router = AgentRouter()
        self.session_manager = SessionManager()
        self.safety_monitor = SafetyMonitor(max_cost, max_time_hours, max_consecutive_failures)
        self.pr_creator = PRCreator()

        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = datetime.now()

    async def run_cycle(self):
        """Main execution loop."""
        logger.info(f"Starting autonomous cycle: {self.session_id}")

        # Fetch eligible tasks
        tasks = self.task_fetcher.fetch_eligible_tasks(
            status="To Do",
            max_tasks=10
        )

        for task in tasks:
            # Check safety limits before each task
            can_continue, stop_reason = self.safety_monitor.check_limits()
            if not can_continue:
                logger.error(f"Safety limit: {stop_reason}")
                break

            # Route task to agent
            agent = self.agent_router.route(task)

            # Create isolated worktree
            worktree_path = self.session_manager.create_worktree(task['id'])

            # Execute task
            try:
                result = await agent.execute(task, worktree_path)

                if result['success']:
                    # Create PR
                    pr_url = self.pr_creator.create_draft_pr(task['id'], result)

                    # Update task status
                    backlog.task_edit(task['id'], status="Done")

                    # Record success
                    self.safety_monitor.record_success(task['id'], result['cost'], result['duration'])
                else:
                    # Log failure
                    self._log_failure(task['id'], result['error'])

                    # Record failure
                    self.safety_monitor.record_failure(task['id'], result['error'])

            except Exception as e:
                logger.error(f"Task {task['id']} failed: {e}")
                self.safety_monitor.record_failure(task['id'], str(e))

            finally:
                # Cleanup worktree
                self.session_manager.cleanup_worktree(worktree_path)

        # Generate session summary
        summary = self.safety_monitor.get_session_summary()
        logger.info(f"Cycle complete: {summary}")
```

**Configuration Options:**
```python
# config/autonomous_config.yml
orchestrator:
  max_cost: 5.0               # Max $5 per night
  max_time_hours: 4.0         # Max 4 hours (2am-6am window)
  max_consecutive_failures: 3 # Circuit breaker threshold
  max_tasks_per_run: 10       # Queue size limit
  per_task_timeout: 1800      # 30 minutes per task

task_fetcher:
  status_filter: "To Do"
  priority_order: ["high", "medium", "low"]
  respect_dependencies: true

agent_router:
  default_agent: "claude_code"
  routing_rules:
    - label: "agent:research"
      agent: "research_pipeline"
    - title_prefix: "BUILD:"
      agent: "claude_code"
    - title_prefix: "FIX:"
      agent: "claude_code"
    - title_prefix: "TEST:"
      agent: "test_agent"
```

---

### 2.3 Claude Code CLI Agent

**Purpose:** Primary execution environment using Claude Code CLI in isolated git worktrees.

**Invocation Pattern:**
```bash
# Session-based execution with system prompts from CLAUDE.md
claude code \
  --session "autonomous/task-23-3" \
  --prompt "$(cat backlog/tasks/task-23.3*.md)" \
  --model claude-sonnet-4.5 \
  --max-tokens 100000 \
  --timeout 1800

# The prompt combines:
# 1. Task description from Backlog.md
# 2. Acceptance criteria checklist
# 3. CLAUDE.md system instructions
# 4. Current codebase context
```

**System Prompts (from CLAUDE.md):**
```
You are Claude Code, Anthropic's official CLI for Claude.
Your task: {task_description}

Acceptance Criteria:
{acceptance_criteria}

Instructions:
1. Read relevant files to understand context
2. Plan the implementation approach
3. Implement changes following project patterns
4. Test that acceptance criteria are met
5. Commit changes with detailed message

Safety Rules:
- Only modify files related to the task
- Follow existing code patterns
- Add tests for new functionality
- Never skip acceptance criteria validation
```

**Tool Access:**
- **Read:** Read any file in the worktree
- **Write:** Create new files
- **Edit:** Modify existing files
- **Bash:** Run terminal commands (git, poetry, pytest)
- **Grep:** Search code for patterns
- **Glob:** Find files by name pattern

**Session Isolation:**
Each task executes in a dedicated git worktree:
```bash
# Worktree creation
git worktree add ../agent-factory-task-23-3 -b autonomous/task-23-3
cd ../agent-factory-task-23-3

# Execution (isolated from main repo)
claude code --session autonomous/task-23-3 ...

# Cleanup after task
cd ../Agent-Factory
git worktree remove ../agent-factory-task-23-3
```

**Benefits of Worktree Isolation:**
1. **Parallel Execution:** Multiple agents can work simultaneously without conflicts
2. **Branch Isolation:** Each task gets its own branch (autonomous/task-{id})
3. **Easy Cleanup:** `rm -rf ../agent-factory-task-23-3` removes all traces
4. **State Preservation:** Main repo remains untouched during execution

---

### 2.4 Safety Monitor

**Purpose:** Enforce hard limits on autonomous execution to prevent runaway costs, time, and failures.

**Hard Limits:**
```python
class SafetyMonitor:
    """
    Enforce safety limits on autonomous execution.

    Hard Limits:
        - max_cost: $5.00 per night (configurable)
        - max_time_hours: 4.0 hours wall-clock (configurable)
        - max_consecutive_failures: 3 (circuit breaker)

    Per-Task Limits:
        - timeout: 30 minutes per task
    """

    def __init__(
        self,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0,
        max_consecutive_failures: int = 3
    ):
        self.max_cost = max_cost
        self.max_time_hours = max_time_hours
        self.max_consecutive_failures = max_consecutive_failures

        # Session tracking
        self.total_cost = 0.0
        self.start_time = time.time()
        self.consecutive_failures = 0
        self.issues_processed = 0
        self.issues_succeeded = 0
        self.issues_failed = 0

    def check_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Check if any safety limit has been exceeded.

        Returns:
            (can_continue: bool, stop_reason: Optional[str])

            - (True, None) = All limits OK, continue processing
            - (False, reason) = Limit exceeded, stop immediately
        """
        # Check cost limit
        if self.total_cost >= self.max_cost:
            reason = f"Cost limit reached: ${self.total_cost:.2f} >= ${self.max_cost:.2f}"
            return False, reason

        # Check time limit
        elapsed_hours = (time.time() - self.start_time) / 3600
        if elapsed_hours >= self.max_time_hours:
            reason = f"Time limit reached: {elapsed_hours:.1f}h >= {self.max_time_hours:.1f}h"
            return False, reason

        # Check failure circuit breaker
        if self.consecutive_failures >= self.max_consecutive_failures:
            reason = f"Circuit breaker tripped: {self.consecutive_failures} consecutive failures"
            return False, reason

        return True, None
```

**Usage Pattern:**
```python
monitor = SafetyMonitor(max_cost=5.0, max_time_hours=4.0, max_consecutive_failures=3)

for task in queue:
    # Check limits BEFORE each task
    can_continue, stop_reason = monitor.check_limits()
    if not can_continue:
        send_alert(f"Autonomous system halted: {stop_reason}")
        break

    # Execute task...

    if success:
        monitor.record_success(task_id, cost=0.42, duration_sec=512)
    else:
        monitor.record_failure(task_id, error="Timeout")
```

**Session Summary:**
```python
summary = monitor.get_session_summary()
# Returns:
{
    "total_cost": 2.83,
    "remaining_budget": 2.17,
    "elapsed_hours": 1.2,
    "remaining_time_hours": 2.8,
    "tasks_processed": 6,
    "tasks_succeeded": 5,
    "tasks_failed": 1,
    "success_rate": 0.833,
    "consecutive_failures": 0,
    "status": "healthy"
}
```

---

### 2.5 PR Creator

**Purpose:** Create draft pull requests for completed tasks with detailed descriptions and issue linking.

**Workflow:**
1. **Commit changes** to `autonomous/{task-id}` branch
2. **Push to GitHub** remote
3. **Create draft PR** with metadata:
   - Title: `[AUTO] {task_title}`
   - Body: Task description + acceptance criteria + files changed + metrics
   - Link: `Resolves task-{id}` (or `Closes #{issue_number}` for GitHub issues)
   - Label: `autonomous`
   - Draft: true (requires manual review)
4. **Request review** from repository owner

**Implementation:**
```python
class PRCreator:
    """Create draft pull requests for Claude-resolved tasks."""

    def create_draft_pr(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> str:
        """
        Create draft PR for completed task.

        Args:
            task_id: Backlog task ID (e.g., "task-23.3")
            result: Execution result from agent

        Returns:
            PR URL string
        """
        # Fetch task details
        task = backlog.task_view(task_id)

        # Create PR title
        title = f"[AUTO] {task['title']}"

        # Build PR description
        body = f"""Complete implementation of {task_id}.

## Summary
{result['summary']}

## Acceptance Criteria
{self._format_acceptance_criteria(task['acceptanceCriteria'])}

## Files Changed
{self._format_files_changed(result['files_changed'])}

## Testing
{result.get('testing_summary', 'Manual testing required')}

## Metrics
- Cost: ${result['cost']:.2f}
- Duration: {self._format_duration(result['duration_sec'])}
- Model: {result.get('model', 'claude-sonnet-4.5')}

## Review Checklist
- [ ] Code follows project patterns
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Acceptance criteria met

Resolves {task_id}

🤖 Generated with AI Dev Control Loop
"""

        # Create draft PR
        pr = self.repo.create_pull(
            title=title,
            body=body,
            head=f"autonomous/{task_id}",
            base="main",
            draft=True
        )

        # Add label
        pr.add_to_labels("autonomous")

        # Request review from owner
        pr.create_review_request([self.repo.owner.login])

        return pr.html_url
```

**Draft PR Requirement:**
All PRs created by the autonomous system are drafts, requiring explicit human approval before merge. This ensures:
- **Human oversight** of all automated changes
- **Quality review** before production deployment
- **Safety net** for edge cases Claude might miss
- **Compliance** with organizational policies requiring human approval

---

### 2.6 Issue Queue Builder

**Purpose:** Smart task selection using hybrid scoring (heuristic + LLM semantic analysis).

**Selection Algorithm:**
```python
class IssueQueueBuilder:
    """
    Smart task queue builder with hybrid scoring.

    Scoring:
        1. Heuristic complexity (fast, $0):
           - Label analysis (good-first-issue = -3, breaking-change = +4)
           - Description length (longer = harder)
           - Code snippet count (more = harder)
           - File mention count (more = harder)
           - Issue age (older = harder)

        2. LLM semantic scoring (accurate, ~$0.002/task):
           - Claude Haiku analyzes description
           - Estimates time (0.5-4 hours)
           - Assesses risk (low/medium/high)
           - Returns complexity 0-10 with reasoning

        3. Final complexity = (heuristic * 0.4) + (llm_score * 0.6)

        4. Priority = business_value * (1 / complexity) * feasibility

    Constraints:
        - Total estimated time < remaining budget (e.g., <4 hours)
        - Dependencies satisfied
        - Max 5-10 tasks per run
    """

    def build_queue(self, max_tasks: int = 10) -> List[Dict[str, Any]]:
        """Build prioritized task queue."""
        # Fetch all open tasks
        tasks = backlog.task_list(status="To Do")

        # Score each task
        scored_tasks = []
        for task in tasks:
            # Heuristic scoring (fast)
            heuristic_score = self._heuristic_complexity(task)

            # LLM semantic scoring (optional, if ANTHROPIC_API_KEY set)
            if self.llm:
                llm_score = self._llm_semantic_score(task)
            else:
                llm_score = heuristic_score

            # Combine scores
            final_complexity = (heuristic_score * 0.4) + (llm_score * 0.6)

            # Calculate priority
            priority = self._calculate_priority(task, final_complexity)

            scored_tasks.append({
                **task,
                "heuristic_complexity": heuristic_score,
                "llm_complexity": llm_score,
                "final_complexity": final_complexity,
                "priority_score": priority
            })

        # Sort by priority (highest first)
        scored_tasks.sort(key=lambda x: x["priority_score"], reverse=True)

        # Select top tasks under time budget
        selected_tasks = self._select_under_budget(scored_tasks, max_tasks)

        return selected_tasks
```

**Priority Formula:**
```python
def _calculate_priority(self, task: Dict, complexity: float) -> float:
    """
    Calculate priority score.

    Priority = business_value * (1 / complexity) * feasibility

    Where:
        - business_value: Based on labels (bug=10, feature=7, docs=3)
        - complexity: 0-10 from hybrid scoring
        - feasibility: Based on dependencies (all satisfied=1.0, blocked=0.0)
    """
    # Business value from labels
    business_value = 5.0  # Default
    if "bug" in task["labels"]:
        business_value = 10.0
    elif "feature" in task["labels"]:
        business_value = 7.0
    elif "documentation" in task["labels"]:
        business_value = 3.0

    # Feasibility from dependencies
    feasibility = 1.0
    if task["dependencies"]:
        # Check if all dependencies are Done
        all_satisfied = all(
            backlog.task_view(dep_id)["status"] == "Done"
            for dep_id in task["dependencies"]
        )
        feasibility = 1.0 if all_satisfied else 0.0

    # Priority score
    priority = business_value * (1.0 / (complexity + 0.1)) * feasibility
    return priority
```

---

## Data Flow & Control Loop

This section provides three ASCII diagrams showing the complete end-to-end flow of the AI Dev Control Loop system.

### Diagram 1: End-to-End Task Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKLOG.MD (Source of Truth)                         │
│  backlog/tasks/task-23.3 - BUILD: Define AI Dev Loop architecture      │
│  Status: To Do → In Progress → Done                                    │
│  Priority: high | Labels: [build, ai-loop, architecture]               │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      │ 1. Fetch eligible tasks
                      │    (status=To Do, dependencies satisfied)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           HEADLESS ORCHESTRATOR (Python Script)                         │
│  Components:                                                            │
│  - TaskFetcher: Query Backlog.md MCP                                   │
│  - AgentRouter: Match task type to agent                               │
│  - SessionManager: Create worktree, manage execution                   │
│  - ResultProcessor: Update Backlog.md with outcome                     │
│                                                                         │
│  Workflow:                                                              │
│  1. Check SafetyMonitor limits (cost/time/failures)                    │
│  2. Route task to agent based on labels/title                          │
│  3. Create git worktree: ../agent-factory-task-23-3                    │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      │ 2. Execute task in isolated worktree
                      │    Branch: autonomous/task-23-3
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             AGENT EXECUTOR (Claude Code CLI)                            │
│  claude code --session autonomous/task-23-3 \                          │
│    --prompt "$(cat backlog/tasks/task-23.3*.md)" \                     │
│    --model claude-sonnet-4.5                                           │
│                                                                         │
│  Process:                                                               │
│  1. Read CLAUDE.md system instructions                                 │
│  2. Read task description + acceptance criteria                        │
│  3. Explore codebase to understand context                             │
│  4. Implement changes following project patterns                       │
│  5. Commit to autonomous/task-23-3 branch                              │
│                                                                         │
│  Result: {                                                              │
│    "success": true,                                                     │
│    "summary": "Created architecture doc with 7 sections + 3 diagrams", │
│    "files_changed": ["docs/ai-dev-loop-architecture.md"],              │
│    "cost": 0.42,                                                        │
│    "duration_sec": 512                                                  │
│  }                                                                      │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      │ 3. Record metrics (cost, time)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                SAFETY MONITOR (Tracker)                                 │
│  - Record cost: $0.42 (session total: $2.83 / $5.00)                   │
│  - Record time: 8m 32s (session elapsed: 47m / 4h)                     │
│  - Reset consecutive_failures counter (was 0, still 0)                 │
│  - Update success rate: 6/7 = 85.7%                                    │
│  - Check limits: ✅ Can continue (budget: 43%, time: 19%)              │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      │ 4. Create draft PR with task metadata
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               PR CREATOR (GitHub Integration)                           │
│  1. Push branch: autonomous/task-23-3                                  │
│  2. Create draft PR:                                                    │
│     - Title: "[AUTO] BUILD: Define AI Dev Loop architecture"           │
│     - Body: Task description + acceptance criteria + metrics           │
│     - Link: "Resolves task-23.3"                                       │
│     - Label: "autonomous"                                              │
│     - Draft: true (requires human review)                              │
│  3. Request review from repository owner                               │
│                                                                         │
│  Output: PR URL (https://github.com/.../pull/142)                      │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
                      │ 5. Update task status and sync to TASK.md
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              BACKLOG.MD UPDATE (MCP Tool)                               │
│  backlog task edit task-23.3 --status "Done"                           │
│  python scripts/backlog/sync_tasks.py                                  │
│                                                                         │
│  Updates:                                                               │
│  - backlog/tasks/task-23.3*.md: status → "Done"                        │
│  - TASK.md: Removes from "Current Task", shows in completed list       │
│                                                                         │
│  Notification: Telegram bot sends success message                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Diagram 2: Multi-Task Session Flow

```
AUTONOMOUS SESSION (4-hour window, $5 budget)
═══════════════════════════════════════════════════════════════════════════

START: 2025-12-17 22:00 UTC
Budget: $5.00 | Time Window: 4h (22:00-02:00)

┌─ TASK 1: task-23.3 (Priority: 9.2, Complexity: 3.5/10, Est: 30m)
│  ├─ Fetch from Backlog.md (status=To Do, dependencies satisfied)
│  ├─ Check SafetyMonitor: ✅ Budget: $5.00, Time: 4h, Failures: 0
│  ├─ Route to agent: claude_code (default for BUILD tasks)
│  ├─ Create worktree: ../agent-factory-task-23-3 → Branch: autonomous/task-23-3
│  ├─ Execute: claude code --session autonomous/task-23-3 ...
│  │  ├─ Read task requirements (1 min)
│  │  ├─ Explore reference files (2 min)
│  │  ├─ Write architecture doc 7 sections (5 min)
│  │  └─ Commit changes (10 sec)
│  ├─ Result: ✅ SUCCESS
│  │  ├─ Files: docs/ai-dev-loop-architecture.md (1,850 lines)
│  │  ├─ Cost: $0.42 (API calls: 120K tokens in, 80K tokens out)
│  │  └─ Time: 8m 32s
│  ├─ Create PR: #142 (draft) → "Resolves task-23.3"
│  ├─ Update Backlog: task-23.3 status → "Done"
│  ├─ Cleanup: Remove worktree
│  └─ Record: SafetyMonitor (cost: $0.42, time: 8m, success: yes)
│
├─ TASK 2: task-23.2 (Priority: 8.8, Complexity: 5.2/10, Est: 45m)
│  ├─ Check SafetyMonitor: ✅ Budget: $4.58, Time: 3h 51m, Failures: 0
│  ├─ Route to agent: claude_code
│  ├─ Create worktree: ../agent-factory-task-23-2 → Branch: autonomous/task-23-2
│  ├─ Execute: claude code --session autonomous/task-23-2 ...
│  │  ├─ Read architecture doc from task-23.3 (context)
│  │  ├─ Implement HeadlessOrchestrator class (400 lines)
│  │  ├─ Write unit tests (200 lines)
│  │  ├─ Run tests: pytest → ✅ All passed
│  │  └─ Commit changes
│  ├─ Result: ✅ SUCCESS
│  │  ├─ Files: scripts/autonomous/headless_orchestrator.py, tests/autonomous/test_orchestrator.py
│  │  ├─ Cost: $0.67
│  │  └─ Time: 12m 18s
│  ├─ Create PR: #143 (draft) → "Resolves task-23.2"
│  └─ Record: SafetyMonitor (cost: $0.67, time: 12m, success: yes)
│
├─ TASK 3: task-14 (Priority: 6.5, Complexity: 4.0/10, Est: 20m)
│  ├─ Check SafetyMonitor: ✅ Budget: $3.91, Time: 3h 29m, Failures: 0
│  ├─ Route to agent: claude_code
│  ├─ Create worktree: ../agent-factory-task-14 → Branch: autonomous/task-14
│  ├─ Execute: claude code --session autonomous/task-14 ...
│  │  ├─ Attempt to install pgvector for PostgreSQL 18
│  │  ├─ Timeout after 30 minutes (per-task limit)
│  │  └─ Error: "pgvector extension not available for PostgreSQL 18"
│  ├─ Result: ❌ FAILURE (timeout)
│  │  ├─ Files: None
│  │  ├─ Cost: $0.08 (partial execution)
│  │  └─ Time: 30m 00s (timeout)
│  ├─ Log failure: backlog/decisions/task-14-failure.md
│  ├─ Keep status: To Do (retry later with different approach)
│  └─ Record: SafetyMonitor (cost: $0.08, time: 30m, failure: yes)
│
├─ TASK 4: task-4 (Priority: 8.2, Complexity: 6.0/10, Est: 60m)
│  ├─ Check SafetyMonitor: ✅ Budget: $3.83, Time: 2h 59m, Failures: 1
│  ├─ Route to agent: claude_code
│  ├─ Execute: claude code --session autonomous/task-4 ...
│  ├─ Result: ✅ SUCCESS
│  │  ├─ Cost: $0.89
│  │  └─ Time: 18m 45s
│  ├─ Create PR: #144 (draft)
│  └─ Record: SafetyMonitor (cost: $0.89, time: 19m, success: yes, failures reset to 0)
│
├─ TASK 5: task-5 (Priority: 7.1, Complexity: 7.5/10, Est: 90m)
│  ├─ Check SafetyMonitor: ✅ Budget: $2.94, Time: 2h 20m, Failures: 0
│  ├─ Execute: ...
│  ├─ Result: ✅ SUCCESS
│  │  ├─ Cost: $1.15
│  │  └─ Time: 25m 12s
│  └─ Record: SafetyMonitor (cost: $1.15, time: 25m, success: yes)
│
├─ TASK 6: task-6 (Priority: 6.8, Complexity: 3.0/10, Est: 30m)
│  ├─ Check SafetyMonitor: ✅ Budget: $1.79, Time: 1h 55m, Failures: 0
│  ├─ Execute: ...
│  ├─ Result: ✅ SUCCESS
│  │  ├─ Cost: $0.35
│  │  └─ Time: 9m 50s
│  └─ Record: SafetyMonitor (cost: $0.35, time: 10m, success: yes)
│
└─ STOP: Safety limit approaching (budget at 71%, time window closing)

   SESSION SUMMARY:
   ════════════════════════════════════════════════════════════════════
   Total Tasks: 6
   Succeeded: 5 (83.3%)
   Failed: 1 (16.7%)
   Total Cost: $3.56 / $5.00 (71.2%)
   Total Time: 1h 44m / 4h (43.3%)
   PRs Created: 5 draft PRs (#142-#146)
   Tasks Completed: task-23.3, task-23.2, task-4, task-5, task-6
   Tasks Failed: task-14 (timeout, will retry with different approach)
   ════════════════════════════════════════════════════════════════════
```

### Diagram 3: Git Worktree Isolation

```
GIT WORKTREE ISOLATION PATTERN
═══════════════════════════════════════════════════════════════════════════

MAIN REPOSITORY: C:\Users\...\Agent Factory\
├── .git/                       # Shared git database
│   ├── objects/                # All commits, trees, blobs
│   ├── refs/heads/main         # Main branch pointer
│   ├── refs/heads/autonomous/  # Autonomous task branches
│   └── worktrees/              # Worktree metadata
│       ├── agent-factory-task-23-3/
│       └── agent-factory-task-23-2/
├── agent_factory/              # Main codebase
├── backlog/tasks/              # Task definitions
├── scripts/autonomous/         # Control loop scripts
└── docs/                       # Documentation

WORKTREE 1 (Task 23.3): C:\Users\...\agent-factory-task-23-3\
├── .git/                       # Symlink → Main .git
├── agent_factory/              # Full codebase copy
├── backlog/                    # Full backlog copy
├── scripts/                    # Full scripts copy
└── docs/
    └── ai-dev-loop-architecture.md  ← NEW FILE (created here)

Branch: autonomous/task-23-3
HEAD points to: autonomous/task-23-3 (detached from main)

WORKTREE 2 (Task 23.2): C:\Users\...\agent-factory-task-23-2\
├── .git/                       # Symlink → Main .git
└── scripts/autonomous/
    └── headless_orchestrator.py  ← NEW FILE (created here)

Branch: autonomous/task-23-2
HEAD points to: autonomous/task-23-2 (detached from main)

BENEFITS OF WORKTREE ISOLATION:
════════════════════════════════════════════════════════════════════════

✅ PARALLEL EXECUTION
   - Multiple agents can work simultaneously on different tasks
   - No file conflicts (each worktree is independent filesystem)
   - No race conditions on git operations

✅ BRANCH ISOLATION
   - Each task gets dedicated branch: autonomous/{task-id}
   - Changes committed to branch, not main
   - Easy to track what changed for each task

✅ EASY CLEANUP
   - Remove worktree: git worktree remove ../agent-factory-task-23-3
   - Or just: rm -rf ../agent-factory-task-23-3 (filesystem cleanup)
   - No traces left in main repository

✅ STATE PRESERVATION
   - Main repository remains untouched during execution
   - Can inspect worktree state after completion
   - Can resume work if agent stops mid-task

✅ DISK EFFICIENCY
   - Worktrees share .git database (objects stored once)
   - Only working tree files duplicated
   - ~600 MB per worktree vs ~1.2 GB for full clone

WORKFLOW EXAMPLE:
════════════════════════════════════════════════════════════════════════

# Create worktree for task-23.3
git worktree add ../agent-factory-task-23-3 -b autonomous/task-23-3
cd ../agent-factory-task-23-3

# Verify isolation
git branch
# * autonomous/task-23-3

# Make changes (agent creates docs/ai-dev-loop-architecture.md)

# Commit to task branch
git add docs/ai-dev-loop-architecture.md
git commit -m "docs(ai-dev-loop): Add architecture documentation"

# Push task branch to remote
git push -u origin autonomous/task-23-3

# Return to main repo
cd ../Agent-Factory

# Create PR from task branch → main (done by PRCreator)
gh pr create --head autonomous/task-23-3 --base main --draft

# Cleanup worktree after PR merged
git worktree remove ../agent-factory-task-23-3
git branch -d autonomous/task-23-3  # Delete local branch
git push origin --delete autonomous/task-23-3  # Delete remote branch
```

---

## Task Management Layer

Detailed specification of Backlog.md task management and TASK.md sync mechanism.

### 4.1 Task File Structure

**Complete YAML Frontmatter Schema:**
```yaml
---
# Core Identifiers (Required)
id: task-23.3                    # Unique identifier (auto-generated by Backlog.md)
title: 'BUILD: Define AI Dev Loop architecture (AI Dev Loop 2/6)'
                                 # Action prefix required: BUILD, FIX, TEST, CLEANUP, AUDIT, RESEARCH, DEPLOY

# Status & Priority (Required)
status: To Do                    # States: To Do | In Progress | Done
priority: high                   # Levels: high | medium | low

# Organization (Optional)
labels: [build, ai-loop, architecture, documentation]
                                 # Tags for categorization, filtering, routing
parent_task_id: task-23          # Epic relationship (optional, for subtasks)
dependencies: []                 # Task IDs that must complete first (optional)

# Metadata (Auto-generated)
created_at: 2025-12-17T22:00:00Z
updated_at: 2025-12-17T22:30:00Z
completed_at: null               # Set when status → Done

# Execution Tracking (Optional, added by agents)
assignee: []                     # Agents or humans assigned
estimated_hours: 1.5             # Time estimate
actual_hours: null               # Actual time spent (filled on completion)
---

## Description
Create comprehensive architecture document describing all control loop components
so humans and agents can reason about the system.

This document serves as the foundation for implementing task-23.2 (Headless Claude runner)
and all subsequent AI Dev Loop phases.

## Acceptance Criteria
- [ ] #1 docs/ai-dev-loop-architecture.md exists with all major components described
- [ ] #2 Diagrams (ASCII box style) cover main E2E loop
- [ ] #3 Another developer/agent can read doc and understand adding new task type/repo

## Implementation Notes
[Optional section added during execution]

## Dependencies
[Optional section documenting why dependencies exist]
```

**Example Task File (Complete):**
```markdown
---
id: task-23.2
title: 'BUILD: Headless Claude runner (AI Dev Loop 3/6)'
status: To Do
priority: high
labels: [build, ai-loop, orchestration, python]
parent_task_id: task-23
dependencies: [task-23.3]
created_at: 2025-12-17T22:00:00Z
updated_at: 2025-12-17T22:00:00Z
---

## Description
Implement `scripts/autonomous/headless_orchestrator.py` - the main control loop
that consumes Backlog.md tasks and routes them to appropriate agents.

Accepts a task ID from Backlog.md, runs Claude Code CLI (or custom agent),
creates git worktree/branch, implements changes, runs tests, opens draft PR,
marks task In Progress → Done/Blocked automatically based on results.

## Acceptance Criteria
- [ ] #1 scripts/autonomous/headless_orchestrator.py implements HeadlessOrchestrator class
- [ ] #2 Can fetch tasks from Backlog.md MCP server
- [ ] #3 Routes tasks to agents based on labels/title prefix
- [ ] #4 Creates worktrees and manages git branches
- [ ] #5 Updates Backlog.md task status automatically
- [ ] #6 Integrates with SafetyMonitor for limits enforcement
- [ ] #7 Unit tests with 80%+ coverage

## Implementation Notes
- Follow architecture defined in docs/ai-dev-loop-architecture.md (task-23.3)
- Reference existing autonomous_runner.py for GitHub issue-based patterns
- Use Backlog.md MCP tools for task queries and updates
- Support dry-run mode for testing
```

### 4.2 Task Lifecycle States

**State Machine:**
```
┌──────────┐
│  TO DO   │  ← Initial state (task created, not started)
└────┬─────┘
     │
     │ Prerequisites:
     │ - Dependencies satisfied (all dependency tasks have status=Done)
     │ - Agent available
     │ - Safety limits not exceeded
     │
     │ Triggered by:
     │ - HeadlessOrchestrator fetch_eligible_tasks()
     │ - Manual: backlog task edit <id> --status "In Progress"
     │
     ▼
┌──────────────┐
│  IN PROGRESS │  ← Task actively being executed
└────┬─────────┘
     │
     │ Agent executing:
     │ - Claude Code CLI running in worktree
     │ - Changes being committed to autonomous/<task-id> branch
     │ - Timeout: 30 minutes (configurable)
     │
     │ Outcomes:
     │ ├─ Success → DONE (acceptance criteria met, PR created)
     │ └─ Failure → TO DO (error logged, task remains in queue for retry)
     │
     ▼
┌──────────┐
│   DONE   │  ← Task completed successfully
└────┬─────┘
     │
     │ Completion criteria:
     │ - All acceptance criteria checked
     │ - Draft PR created
     │ - No blocking errors
     │
     │ Next actions:
     │ - Moved to TASK.md completed section
     │ - Manual: Archive to backlog/completed/ (optional)
     │ - Dependent tasks become eligible (if this was a dependency)
     │
     ▼
┌──────────┐
│ ARCHIVED │  ← Task moved to backlog/completed/ (optional, manual)
└──────────┘
```

**State Transition Logic:**
```python
def transition_task_status(task_id: str, new_status: str, result: Optional[Dict] = None):
    """
    Transition task to new status with validation.

    Args:
        task_id: Backlog task ID
        new_status: Target status (To Do, In Progress, Done)
        result: Execution result (required for Done transition)
    """
    task = backlog.task_view(task_id)
    current_status = task["status"]

    # Validate state transition
    if new_status == "In Progress":
        # Check dependencies
        if task["dependencies"]:
            for dep_id in task["dependencies"]:
                dep_task = backlog.task_view(dep_id)
                if dep_task["status"] != "Done":
                    raise ValueError(f"Dependency {dep_id} not satisfied")

        # Check safety limits
        can_continue, stop_reason = safety_monitor.check_limits()
        if not can_continue:
            raise ValueError(f"Cannot start task: {stop_reason}")

    elif new_status == "Done":
        # Validate acceptance criteria
        if not result or not result.get("success"):
            raise ValueError("Cannot mark Done without successful result")

        # Validate PR created
        if "pr_url" not in result:
            raise ValueError("Cannot mark Done without PR URL")

    # Update status
    backlog.task_edit(task_id, status=new_status)

    # Add execution notes if provided
    if result:
        backlog.task_edit(
            task_id,
            notes_append=[
                f"Status: {current_status} → {new_status}",
                f"Cost: ${result.get('cost', 0):.2f}",
                f"Duration: {result.get('duration_sec', 0)} seconds",
                f"PR: {result.get('pr_url', 'N/A')}"
            ]
        )

    # Sync to TASK.md
    subprocess.run(["python", "scripts/backlog/sync_tasks.py"])
```

### 4.3 MCP Integration

**Programmatic Task Access:**
```python
# Import Backlog.md MCP client
from mcp import backlog

# ═══════════════════════════════════════════════════════════════
# QUERY TASKS
# ═══════════════════════════════════════════════════════════════

# List all To Do tasks
tasks = backlog.task_list(status="To Do")
# Returns: List[Dict] with id, title, status, priority, labels

# Filter by priority
high_priority_tasks = backlog.task_list(status="To Do", priority="high")

# Search by query
architecture_tasks = backlog.task_search(query="architecture")

# ═══════════════════════════════════════════════════════════════
# VIEW TASK DETAILS
# ═══════════════════════════════════════════════════════════════

task = backlog.task_view("task-23.3")
# Returns: {
#     "id": "task-23.3",
#     "title": "BUILD: Define AI Dev Loop architecture",
#     "status": "To Do",
#     "priority": "high",
#     "labels": ["build", "ai-loop", "architecture"],
#     "description": "Create comprehensive architecture document...",
#     "acceptanceCriteria": [
#         "#1 docs/ai-dev-loop-architecture.md exists",
#         "#2 Diagrams cover E2E loop",
#         "#3 Extension guide included"
#     ],
#     "dependencies": [],
#     "parent_task_id": "task-23",
#     "created_at": "2025-12-17T22:00:00Z",
#     "updated_at": "2025-12-17T22:00:00Z"
# }

# ═══════════════════════════════════════════════════════════════
# UPDATE TASKS
# ═══════════════════════════════════════════════════════════════

# Mark task In Progress
backlog.task_edit("task-23.3", status="In Progress")

# Add execution notes
backlog.task_edit(
    "task-23.3",
    notes_append=["Started execution at 22:30", "Created worktree"]
)

# Update multiple fields
backlog.task_edit(
    "task-23.3",
    status="Done",
    notes_append=["Completed successfully", "PR #142 created"]
)

# ═══════════════════════════════════════════════════════════════
# CREATE TASKS (Programmatic)
# ═══════════════════════════════════════════════════════════════

backlog.task_create(
    title="FIX: Database connection timeout",
    description="Increase connection pool size and add retry logic",
    priority="high",
    labels=["fix", "database", "production"],
    acceptanceCriteria=[
        "Connection pool size increased to 50",
        "Exponential backoff retry added (3 attempts)",
        "Tests pass with simulated connection failures"
    ]
)
```

### 4.4 TASK.md Auto-Sync

**Sync Zone Markers:**
TASK.md uses HTML comments to define auto-generated zones:
```markdown
# Active Tasks

<!-- BACKLOG_SYNC:CURRENT:BEGIN -->
## Current Task
[Auto-generated from Backlog In Progress tasks]
<!-- BACKLOG_SYNC:CURRENT:END -->

<!-- BACKLOG_SYNC:BACKLOG:BEGIN -->
## Backlog
[Auto-generated from Backlog To Do tasks, grouped by priority]
<!-- BACKLOG_SYNC:BACKLOG:END -->

## Project Context & History
[Manual content, never touched by sync script]
```

**Sync Script:**
```python
# File: scripts/backlog/sync_tasks.py

def sync_task_md(path: str, section: str = "all"):
    """
    Sync Backlog.md data to TASK.md.

    Args:
        path: Path to TASK.md
        section: Which section to sync (current, backlog, all)
    """
    # Read current TASK.md
    task_md_content = Path(path).read_text()

    # Fetch In Progress tasks for "Current Task" section
    if section in ("current", "all"):
        in_progress_tasks = backlog.task_list(status="In Progress")
        current_section = format_current_task_section(in_progress_tasks)

        # Replace content between CURRENT markers
        task_md_content = replace_section(
            task_md_content,
            ("<!-- BACKLOG_SYNC:CURRENT:BEGIN -->", "<!-- BACKLOG_SYNC:CURRENT:END -->"),
            current_section
        )

    # Fetch To Do tasks for "Backlog" section
    if section in ("backlog", "all"):
        to_do_tasks = backlog.task_list(status="To Do")
        backlog_section = format_backlog_section(to_do_tasks)  # Grouped by priority

        # Replace content between BACKLOG markers
        task_md_content = replace_section(
            task_md_content,
            ("<!-- BACKLOG_SYNC:BACKLOG:BEGIN -->", "<!-- BACKLOG_SYNC:BACKLOG:END -->"),
            backlog_section
        )

    # Write updated TASK.md
    Path(path).write_text(task_md_content)
```

**Trigger Points:**
```bash
# Manual sync (after task status changes)
poetry run python scripts/backlog/sync_tasks.py

# Dry-run preview (see what would change)
poetry run python scripts/backlog/sync_tasks.py --dry-run

# Sync only current section
poetry run python scripts/backlog/sync_tasks.py --section current

# Automated triggers (optional, via git hooks):
# - Pre-commit hook: Sync before commit
# - Post-merge hook: Sync after pulling changes
# - CI/CD: Sync on push to main
```

---

## Execution Layer

Detailed specification of agent routing, execution, and result processing.

### 5.1 Agent Routing Logic

**Decision Tree:**
```python
class AgentRouter:
    """
    Route tasks to appropriate agents based on labels and title prefix.

    Routing Priority:
    1. Explicit agent label (agent:X)
    2. Title prefix (BUILD, FIX, TEST, etc.)
    3. Domain labels (plc-tutor, rivet-pro)
    4. Default (claude_code)
    """

    def __init__(self):
        # Register available agents
        self.agents = {
            "claude_code": ClaudeCodeAgent(),
            "research_pipeline": ResearchPipelineAgent(),
            "plc_tutor": PLCTutorAgent(),
            "test_agent": TestAutomationAgent(),
            "deployment_agent": DeploymentAgent()
        }

    def route(self, task: Dict) -> Agent:
        """
        Route task to agent based on labels and title.

        Args:
            task: Backlog task dict with id, title, labels

        Returns:
            Agent instance to execute the task
        """
        labels = task.get("labels", [])
        title = task["title"]

        # Priority 1: Explicit agent label
        for label in labels:
            if label.startswith("agent:"):
                agent_name = label.split(":")[1]
                if agent_name in self.agents:
                    logger.info(f"Routing to {agent_name} (explicit label)")
                    return self.agents[agent_name]

        # Priority 2: Title prefix
        if title.startswith("BUILD:") or title.startswith("FIX:"):
            logger.info("Routing to claude_code (BUILD/FIX prefix)")
            return self.agents["claude_code"]

        elif title.startswith("TEST:"):
            logger.info("Routing to test_agent (TEST prefix)")
            return self.agents["test_agent"]

        elif title.startswith("DEPLOY:"):
            logger.info("Routing to deployment_agent (DEPLOY prefix)")
            return self.agents["deployment_agent"]

        elif title.startswith("RESEARCH:"):
            logger.info("Routing to research_pipeline (RESEARCH prefix)")
            return self.agents["research_pipeline"]

        # Priority 3: Domain labels
        if "plc-tutor" in labels:
            logger.info("Routing to plc_tutor (domain label)")
            return self.agents["plc_tutor"]

        # Default: Claude Code CLI
        logger.info("Routing to claude_code (default)")
        return self.agents["claude_code"]
```

**Agent Interface:**
```python
class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    async def execute(self, task: Dict, worktree_path: str) -> Dict:
        """
        Execute task in isolated worktree.

        Args:
            task: Backlog task dict with all metadata
            worktree_path: Path to git worktree for isolation

        Returns:
            Result dict: {
                "success": bool,
                "summary": str,
                "files_changed": List[str],
                "cost": float,
                "duration_sec": float,
                "error": Optional[str]
            }
        """
        pass
```

### 5.2 Result Processing

**Success Case:**
```python
async def process_success(task_id: str, result: Dict):
    """
    Process successful task execution.

    Workflow:
    1. Create draft PR
    2. Update Backlog.md status → Done
    3. Sync to TASK.md
    4. Record metrics in SafetyMonitor
    5. Send Telegram notification
    """
    logger.info(f"Processing success for {task_id}")

    # Step 1: Create draft PR
    pr_url = pr_creator.create_draft_pr(
        task_id,
        {
            "summary": result["summary"],
            "files_changed": result["files_changed"],
            "cost": result["cost"],
            "duration_sec": result["duration_sec"]
        }
    )
    logger.info(f"Created PR: {pr_url}")

    # Step 2: Update Backlog status
    backlog.task_edit(task_id, status="Done")
    logger.info(f"Updated {task_id} status → Done")

    # Step 3: Sync to TASK.md
    subprocess.run(["python", "scripts/backlog/sync_tasks.py"])
    logger.info("Synced to TASK.md")

    # Step 4: Record metrics
    safety_monitor.record_success(
        task_id,
        cost=result["cost"],
        duration_sec=result["duration_sec"]
    )
    logger.info("Recorded metrics in SafetyMonitor")

    # Step 5: Send Telegram notification
    telegram_notifier.send_success(
        task_id,
        summary=result["summary"],
        pr_url=pr_url,
        cost=result["cost"],
        duration_sec=result["duration_sec"]
    )
    logger.info("Sent Telegram notification")
```

**Failure Case:**
```python
async def process_failure(task_id: str, error: str, cost: float):
    """
    Process failed task execution.

    Workflow:
    1. Log detailed error to backlog/decisions/
    2. Keep status as To Do (for retry)
    3. Add failure notes to task
    4. Record failure in SafetyMonitor
    5. Check circuit breaker
    6. Send Telegram alert
    """
    logger.error(f"Processing failure for {task_id}: {error}")

    # Step 1: Log detailed error
    error_log_path = f"backlog/decisions/task-{task_id}-failure.md"
    with open(error_log_path, 'w') as f:
        f.write(f"""# Task {task_id} Failure Log

**Error:** {error}
**Cost:** ${cost:.2f}
**Timestamp:** {datetime.now().isoformat()}

## Error Details
{error}

## Recommended Actions
1. Review error message
2. Adjust task approach
3. Retry with modified strategy
""")
    logger.info(f"Logged error to {error_log_path}")

    # Step 2: Keep status To Do (for retry)
    # No status change needed

    # Step 3: Add failure notes
    backlog.task_edit(
        task_id,
        notes_append=[
            f"❌ Failure at {datetime.now().isoformat()}",
            f"Error: {error}",
            f"Cost: ${cost:.2f}",
            f"Log: {error_log_path}"
        ]
    )
    logger.info("Added failure notes to task")

    # Step 4: Record failure
    safety_monitor.record_failure(task_id, error, cost)
    logger.info("Recorded failure in SafetyMonitor")

    # Step 5: Check circuit breaker
    if safety_monitor.consecutive_failures >= 3:
        logger.critical("Circuit breaker tripped: 3 consecutive failures")
        send_alert("Autonomous system halted: Circuit breaker tripped")
        raise CircuitBreakerTrippedException()

    # Step 6: Send Telegram alert
    telegram_notifier.send_failure(
        task_id,
        error=error,
        cost=cost,
        consecutive_failures=safety_monitor.consecutive_failures
    )
    logger.info("Sent Telegram alert")
```

---

## Integration & Safety

Production-ready safety mechanisms and observability infrastructure.

### 6.1 Safety Limits Reference

| Limit | Default | Configurable | Purpose | Enforcement |
|-------|---------|--------------|---------|-------------|
| **Max Cost** | $5.00 | ✅ Yes | Prevent runaway LLM costs | Checked before each task |
| **Max Time** | 4 hours | ✅ Yes | Overnight execution window (2am-6am) | Checked before each task |
| **Max Consecutive Failures** | 3 | ✅ Yes | Circuit breaker for systemic issues | Incremented on failure, reset on success |
| **Per-Task Timeout** | 30 min | ✅ Yes | Prevent hung tasks monopolizing session | Enforced during execution |

**Configuration:**
```bash
# Custom limits via command-line flags
poetry run python scripts/autonomous/headless_orchestrator.py \
  --max-cost 3.0 \
  --max-time 2.0 \
  --max-consecutive-failures 2 \
  --per-task-timeout 1200

# Custom limits via environment variables
export AUTONOMOUS_MAX_COST=3.0
export AUTONOMOUS_MAX_TIME_HOURS=2.0
export AUTONOMOUS_MAX_CONSECUTIVE_FAILURES=2
export AUTONOMOUS_PER_TASK_TIMEOUT=1200

# Custom limits via config file (recommended for production)
# File: config/autonomous_config.yml
safety:
  max_cost: 3.0
  max_time_hours: 2.0
  max_consecutive_failures: 2
  per_task_timeout: 1200
```

**Dry-Run Mode (Testing):**
```bash
# Test without making actual changes
poetry run python scripts/autonomous/headless_orchestrator.py --dry-run

# What dry-run mode does:
# ✅ Fetches tasks from Backlog.md
# ✅ Routes tasks to agents
# ✅ Simulates execution (mock results)
# ❌ Does NOT create worktrees
# ❌ Does NOT execute agents
# ❌ Does NOT create PRs
# ❌ Does NOT update Backlog.md
# ✅ Logs all actions as if they happened
# ✅ Reports session summary

# Output:
# [DRY-RUN] Would fetch tasks: task-23.3, task-23.2, task-4
# [DRY-RUN] Would route task-23.3 to claude_code
# [DRY-RUN] Would create worktree: ../agent-factory-task-23-3
# [DRY-RUN] Would execute: claude code --session autonomous/task-23-3
# [DRY-RUN] Mock result: SUCCESS (cost: $0.42, duration: 512s)
# [DRY-RUN] Would create PR: #142
# [DRY-RUN] Would update task-23.3 status → Done
# [DRY-RUN] Session summary: 3 tasks, $1.25 total, 45m elapsed
```

### 6.2 Observability & Logging

**Structured Logging (JSON):**
```json
{
  "timestamp": "2025-12-17T22:30:15Z",
  "level": "INFO",
  "logger": "autonomous_orchestrator",
  "session_id": "autonomous-20251217-220000",
  "task_id": "task-23.3",
  "agent_id": "claude_code",
  "event": "task_completed",
  "status": "success",
  "cost": 0.42,
  "duration_sec": 512,
  "files_changed": ["docs/ai-dev-loop-architecture.md"],
  "pr_url": "https://github.com/Mikecranesync/Agent-Factory/pull/142",
  "acceptance_criteria_met": [
    "#1 docs/ai-dev-loop-architecture.md exists",
    "#2 Diagrams cover E2E loop",
    "#3 Extension guide included"
  ]
}
```

**Session Tracking:**
```python
# Session log file: logs/autonomous_20251217_220000.log
# Contains all events for one execution cycle

class SessionLogger:
    """Session-based logging with structured data."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_file = f"logs/autonomous_{session_id}.log"

        # Configure structured logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(message)s'  # JSON format
        )

    def log_event(self, event: str, **kwargs):
        """Log structured event."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "event": event,
            **kwargs
        }
        logging.info(json.dumps(log_data))
```

**Metrics Dashboard (Future):**
```python
# Real-time metrics exposed for dashboard/monitoring
{
    "session_id": "autonomous-20251217-220000",
    "status": "running",
    "start_time": "2025-12-17T22:00:00Z",
    "elapsed_hours": 0.5,
    "remaining_hours": 3.5,
    "total_cost": 0.42,
    "remaining_budget": 4.58,
    "tasks_processed": 1,
    "tasks_succeeded": 1,
    "tasks_failed": 0,
    "success_rate": 1.0,
    "current_task": "task-23.2",
    "queue_size": 9,
    "estimated_completion": "2025-12-17T01:45:00Z"
}
```

### 6.3 Telegram Notifications

**Success Notification:**
```
🎉 Task Completed: task-23.3
✅ BUILD: Define AI Dev Loop architecture

📊 Metrics:
- Cost: $0.42
- Duration: 8m 32s
- Files: 1 new (docs/ai-dev-loop-architecture.md)
- Lines: +1,850

🔗 PR: #142 (draft)
https://github.com/Mikecranesync/Agent-Factory/pull/142

📈 Progress: 1/10 tasks (10%)
💰 Budget: $0.42 / $5.00 (8%)
⏱️ Time: 8m / 4h (3%)
```

**Failure Notification:**
```
❌ Task Failed: task-14
FIX: pgvector Extension for PostgreSQL 18

🚨 Error:
Timeout after 30 minutes
Extension not available for PostgreSQL 18

💰 Cost: $0.08
⏱️ Time: 30m (timeout)

⚠️ Consecutive Failures: 1/3
(Circuit breaker will trip at 3)

📋 Action Required:
Review backlog/decisions/task-14-failure.md
Adjust approach and retry manually
```

**Session Summary Notification:**
```
🏁 Autonomous Session Complete
Session: autonomous-20251217-220000

📊 Results:
✅ Succeeded: 5 tasks (83.3%)
❌ Failed: 1 task (16.7%)
📝 Total: 6 tasks processed

💰 Cost: $3.56 / $5.00 (71.2%)
⏱️ Time: 1h 44m / 4h (43.3%)

🔗 PRs Created:
#142 - task-23.3 (architecture docs)
#143 - task-23.2 (orchestrator)
#144 - task-4 (RIVET orchestrator)
#145 - task-5 (research pipeline)
#146 - task-6 (logging)

⚠️ Failed:
task-14 (timeout, will retry)

✨ Status: Healthy
Next run: 2025-12-18 22:00 UTC
```

---

## Extension Guide

How to extend the AI Dev Control Loop with new capabilities.

### 7.1 Adding New Task Types

**Example: DEPLOY Task Type**

**Step 1: Create Task Template**
```yaml
# File: backlog/templates/deploy.md
---
id: task-{id}
title: 'DEPLOY: {title}'
status: To Do
priority: high
labels: [deploy, production]
dependencies: []
---

## Description
Deploy {component} to {environment}.

## Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Staging environment validated
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

## Acceptance Criteria
- [ ] #1 Deployment successful
- [ ] #2 Health checks passing
- [ ] #3 No errors in logs (5 min window)
- [ ] #4 Performance metrics baseline met

## Rollback Plan
[Describe rollback procedure]
```

**Step 2: Add Routing Rule**
```python
# File: agent_factory/core/agent_router.py

class AgentRouter:
    def route(self, task: Dict) -> Agent:
        # Add DEPLOY routing
        if task["title"].startswith("DEPLOY:"):
            logger.info("Routing to deployment_agent (DEPLOY prefix)")
            return self.agents["deployment_agent"]
```

**Step 3: Implement Agent**
```python
# File: agents/deployment_agent.py

class DeploymentAgent(BaseAgent):
    """
    Specialized agent for production deployments.

    Capabilities:
    - Run deployment scripts
    - Monitor health checks
    - Validate performance metrics
    - Execute rollback if needed
    """

    async def execute(self, task: Dict, worktree_path: str) -> Dict:
        # Parse deployment target
        component = self._extract_component(task["title"])
        environment = self._extract_environment(task["description"])

        # Run pre-deployment checks
        checks_passed = await self._run_pre_deployment_checks()
        if not checks_passed:
            return {
                "success": False,
                "error": "Pre-deployment checks failed"
            }

        # Execute deployment
        deploy_result = await self._deploy(component, environment)

        # Verify health checks
        health_ok = await self._verify_health_checks()
        if not health_ok:
            # Rollback
            await self._rollback(component, environment)
            return {
                "success": False,
                "error": "Health checks failed, rolled back"
            }

        return {
            "success": True,
            "summary": f"Deployed {component} to {environment}",
            "files_changed": [],
            "cost": 0.0,
            "duration_sec": 300
        }
```

### 7.2 Adding New Repositories

**Multi-Repo Configuration:**
```yaml
# File: config/repos.yml
repositories:
  - name: agent-factory
    owner: Mikecranesync
    repo: Agent-Factory
    backlog_path: backlog/
    default_branch: main

  - name: rivet
    owner: Mikecranesync
    repo: RIVET
    backlog_path: backlog/
    default_branch: main

  - name: plc-tutor
    owner: Mikecranesync
    repo: PLC-Tutor
    backlog_path: backlog/
    default_branch: main
```

**Multi-Repo Orchestrator:**
```python
class MultiRepoOrchestrator:
    """
    Orchestrate tasks across multiple repositories.

    Features:
    - Round-robin task fetching from all repos
    - Per-repo safety limits
    - Cross-repo dependency support
    """

    def __init__(self, repos_config: List[Dict]):
        self.repos = {
            repo["name"]: RepoContext(repo)
            for repo in repos_config
        }

        # Per-repo safety monitors
        self.safety_monitors = {
            name: SafetyMonitor(
                max_cost=repo_ctx.config.get("max_cost", 5.0),
                max_time_hours=repo_ctx.config.get("max_time_hours", 4.0)
            )
            for name, repo_ctx in self.repos.items()
        }

    async def run_cycle(self):
        """Run autonomous cycle across all repositories."""
        for repo_name, repo_ctx in self.repos.items():
            logger.info(f"Processing repository: {repo_name}")

            # Fetch tasks from this repo's Backlog
            tasks = repo_ctx.backlog.task_list(status="To Do")

            for task in tasks:
                # Check this repo's safety limits
                can_continue, stop_reason = self.safety_monitors[repo_name].check_limits()
                if not can_continue:
                    logger.warning(f"Repo {repo_name} safety limit: {stop_reason}")
                    break

                # Execute task in this repo's context
                result = await self.execute_task(repo_ctx, task)

                # Record metrics for this repo
                if result["success"]:
                    self.safety_monitors[repo_name].record_success(
                        task["id"],
                        result["cost"],
                        result["duration_sec"]
                    )
```

### 7.3 Adding New Agents

**Example: PLC Tutor Agent**
```python
# File: agents/plc_tutor_agent.py

class PLCTutorAgent(BaseAgent):
    """
    Specialized agent for PLC Tutor content generation.

    Capabilities:
    - Query RAG for PLC knowledge atoms
    - Generate lesson scripts
    - Create video content
    - Validate technical accuracy
    """

    def __init__(self, llm, rag_client):
        self.llm = llm
        self.rag = rag_client

    async def execute(self, task: Dict, worktree_path: str) -> Dict:
        # Extract lesson topic
        topic = self._extract_topic(task["title"])

        # Query RAG for knowledge atoms
        atoms = self.rag.search(topic, top_k=5)

        # Generate lesson script
        script = await self._generate_script(topic, atoms)

        # Write script to file
        script_path = f"{worktree_path}/plc/content/lessons/{topic}.md"
        Path(script_path).write_text(script)

        # Commit changes
        subprocess.run([
            "git", "-C", worktree_path,
            "add", script_path
        ])
        subprocess.run([
            "git", "-C", worktree_path,
            "commit", "-m", f"feat(plc-tutor): Add lesson on {topic}"
        ])

        return {
            "success": True,
            "summary": f"Generated PLC lesson: {topic}",
            "files_changed": [script_path],
            "cost": 0.15,
            "duration_sec": 120
        }
```

**Agent Registration:**
```python
# File: agent_factory/core/agent_factory.py

# Register new agent
agents = {
    "claude_code": ClaudeCodeAgent(),
    "research_pipeline": ResearchPipelineAgent(),
    "plc_tutor": PLCTutorAgent(llm, rag),  # NEW AGENT
    "test_agent": TestAutomationAgent(),
    "deployment_agent": DeploymentAgent()
}

# Update router to recognize plc-tutor label
# (Already handled by routing logic in section 5.1)
```

### 7.4 Custom Safety Policies

**Per-Agent Budgets:**
```python
class AdvancedSafetyMonitor(SafetyMonitor):
    """
    Advanced safety monitor with per-agent budgets.

    Allows different cost/time limits for different agents.
    Example: Research agent gets $1 max, coding agent gets $3 max.
    """

    def __init__(self, agent_budgets: Dict[str, float], **kwargs):
        super().__init__(**kwargs)

        self.agent_budgets = agent_budgets
        # Example: {"claude_code": 3.0, "research_pipeline": 1.0, "plc_tutor": 1.0}

        # Track per-agent spending
        self.agent_spending = {
            agent: 0.0
            for agent in self.agent_budgets.keys()
        }

    def check_agent_budget(self, agent_id: str, estimated_cost: float) -> Tuple[bool, Optional[str]]:
        """Check if agent has budget remaining."""
        current_spending = self.agent_spending.get(agent_id, 0.0)
        agent_limit = self.agent_budgets.get(agent_id, self.max_cost)

        if current_spending + estimated_cost > agent_limit:
            reason = f"Agent {agent_id} budget exceeded: ${current_spending:.2f} + ${estimated_cost:.2f} > ${agent_limit:.2f}"
            return False, reason

        return True, None

    def record_agent_success(self, agent_id: str, task_id: str, cost: float, duration_sec: float):
        """Record successful execution and update agent spending."""
        # Update agent-specific spending
        self.agent_spending[agent_id] = self.agent_spending.get(agent_id, 0.0) + cost

        # Call parent method for global tracking
        self.record_success(task_id, cost, duration_sec)
```

**Usage:**
```python
# Configure per-agent budgets
agent_budgets = {
    "claude_code": 3.0,      # $3 max for coding tasks
    "research_pipeline": 1.0, # $1 max for research
    "plc_tutor": 1.0         # $1 max for content generation
}

safety_monitor = AdvancedSafetyMonitor(
    agent_budgets=agent_budgets,
    max_cost=5.0,  # Global limit still applies
    max_time_hours=4.0
)

# Before executing task
agent_id = "claude_code"
estimated_cost = 0.50
can_continue, stop_reason = safety_monitor.check_agent_budget(agent_id, estimated_cost)
if not can_continue:
    logger.error(stop_reason)
```

### 7.5 Dashboard UI Integration

**React Component for Session Monitoring:**
```typescript
// File: dashboard/components/AutonomousSessionMonitor.tsx

import { useEffect, useState } from 'react';

interface Session {
  session_id: string;
  status: 'running' | 'completed' | 'failed';
  start_time: string;
  elapsed_hours: number;
  total_cost: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  current_task: string | null;
}

export function AutonomousSessionMonitor() {
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    // Poll /api/autonomous/status every 30 seconds
    const interval = setInterval(async () => {
      const response = await fetch('/api/autonomous/status');
      const data = await response.json();
      setSession(data);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (!session) {
    return <div>No active session</div>;
  }

  return (
    <div className="session-monitor">
      <h2>Autonomous Session: {session.session_id}</h2>

      <div className="metrics">
        <MetricCard
          label="Status"
          value={session.status}
          icon={session.status === 'running' ? '🔄' : '✅'}
        />
        <MetricCard
          label="Tasks"
          value={`${session.tasks_succeeded}/${session.tasks_processed}`}
          subtitle={`${(session.tasks_succeeded / session.tasks_processed * 100).toFixed(1)}% success`}
        />
        <MetricCard
          label="Cost"
          value={`$${session.total_cost.toFixed(2)}`}
          subtitle={`of $${session.max_cost}`}
        />
        <MetricCard
          label="Time"
          value={`${session.elapsed_hours.toFixed(1)}h`}
          subtitle={`of ${session.max_time_hours}h`}
        />
      </div>

      {session.current_task && (
        <div className="current-task">
          <h3>Current Task: {session.current_task}</h3>
          <ProgressBar progress={50} />
        </div>
      )}

      <TaskList
        tasks={session.recent_tasks}
        onTaskClick={(taskId) => window.open(`/tasks/${taskId}`, '_blank')}
      />
    </div>
  );
}
```

**API Endpoint:**
```python
# File: api/routes/autonomous.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/autonomous/status")
async def get_autonomous_status():
    """
    Get current autonomous session status.

    Returns real-time metrics for dashboard display.
    """
    # Read from session log or database
    session = load_current_session()

    return {
        "session_id": session.session_id,
        "status": session.status,
        "start_time": session.start_time.isoformat(),
        "elapsed_hours": session.elapsed_hours,
        "remaining_hours": session.remaining_hours,
        "total_cost": session.total_cost,
        "remaining_budget": session.remaining_budget,
        "max_cost": session.max_cost,
        "max_time_hours": session.max_time_hours,
        "tasks_processed": session.tasks_processed,
        "tasks_succeeded": session.tasks_succeeded,
        "tasks_failed": session.tasks_failed,
        "success_rate": session.success_rate,
        "current_task": session.current_task,
        "recent_tasks": session.recent_tasks[-10:]  # Last 10 tasks
    }
```

---

## Conclusion

This architecture document provides a comprehensive guide to the AI Development Control Loop system. The system enables autonomous, intelligent task execution with strict safety guarantees and human oversight.

**Key Takeaways:**
1. **Backlog.md is the source of truth** for all work items
2. **Safety limits are non-negotiable** - cost, time, and failure thresholds enforced
3. **Draft PRs require human review** - no automatic merges to production
4. **Git worktrees enable parallelism** - multiple agents can work simultaneously
5. **Extension points are well-defined** - easy to add task types, repos, agents

**Next Steps:**
- Implement task-23.2 (Headless Orchestrator) using this architecture
- Deploy to production with monitoring
- Iterate based on real-world usage and feedback

**Related Documentation:**
- [Task Management Guide](../backlog/README.md)
- [Autonomous Execution Scripts](../scripts/autonomous/)
- [Agent Factory Platform Architecture](architecture/00_architecture_platform.md)
- [RIVET + PLC Tutor Integration](architecture/TRIUNE_STRATEGY.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-17
**Maintainer:** Agent Factory Core Team
**Status:** Production Ready ✅
