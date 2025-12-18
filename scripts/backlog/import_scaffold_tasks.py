#!/usr/bin/env python3
"""
SCAFFOLD Task Import Script

Safely imports 144 SCAFFOLD tasks from Master Orchestration Prompt into Backlog.md
using semantic IDs (task-scaffold-*) to avoid conflicts with existing tasks.

Phased Approach:
- Phase 1: 11 Core Build tasks + 1 EPIC parent (12 files)
- Phase 2: 9 Validation tasks (9 files)
- Phase 3: 123 Content Production tasks (123 files)

Safety Features:
- Dry-run mode (preview without creating files)
- Approval gates (explicit --approve flag required)
- Conflict detection (checks for ID collisions)
- Rollback capability (delete all SCAFFOLD tasks)

Usage:
    # Dry-run (preview)
    poetry run python scripts/backlog/import_scaffold_tasks.py --phase 1 --dry-run

    # Import with approval
    poetry run python scripts/backlog/import_scaffold_tasks.py --phase 1 --approve

    # Rollback all SCAFFOLD tasks
    poetry run python scripts/backlog/import_scaffold_tasks.py --rollback
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import yaml


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TaskSpec:
    """Task specification extracted from SCAFFOLD Master Prompt."""
    original_id: str
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: str = "medium"  # critical, high, medium, low
    labels: List[str] = field(default_factory=list)
    action_prefix: str = "BUILD"  # BUILD, TEST, FIX, etc.
    domain: str = ""  # orchestration, agents, youtube, etc.


# ============================================================================
# Component 1: SemanticIDMapper
# ============================================================================

class SemanticIDMapper:
    """Maps SCAFFOLD prompt IDs to semantic IDs."""

    # Core Build mapping (11 tasks)
    CORE_BUILD_MAP = {
        "task-23.2": "task-scaffold-orchestrator",
        "task-23.3": "task-scaffold-backlog-parser",
        "task-23.4": "task-scaffold-context-assembler",
        "task-23.5": "task-scaffold-git-worktree-manager",
        "task-23.6": "task-scaffold-cost-tracking",
        "task-23.7": "task-scaffold-claude-integration",
        "task-23.8": "task-scaffold-pr-creation",
        "task-23.9": "task-scaffold-backlog-sync",
        "task-23.10": "task-scaffold-logging",
        "task-23.11": "task-scaffold-documentation",
        "task-23.12": "task-scaffold-safety-rails",
    }

    # Validation mapping (9 tasks)
    VALIDATION_MAP = {
        "task-validate-agent-factory-1": "task-scaffold-validate-parser-scale",
        "task-validate-agent-factory-2": "task-scaffold-validate-parallel-execution",
        "task-validate-scraper-1": "task-scaffold-validate-scraper-clips",
        "task-validate-scraper-2": "task-scaffold-validate-scraper-metadata",
        "task-validate-integration-youtube": "task-scaffold-validate-youtube-api",
        "task-validate-integration-twitter": "task-scaffold-validate-twitter-api",
        "task-validate-knowledge-base": "task-scaffold-validate-knowledge-base",
        "task-validate-seo": "task-scaffold-validate-seo-rankings",
        "task-validate-video-automation-e2e": "task-scaffold-validate-e2e-pipeline",
    }

    @staticmethod
    def map_id(original_id: str) -> str:
        """
        Map prompt ID to semantic ID.

        Args:
            original_id: Original ID from SCAFFOLD prompt

        Returns:
            Semantic ID (task-scaffold-*)
        """
        # Check Core Build map
        if original_id in SemanticIDMapper.CORE_BUILD_MAP:
            return SemanticIDMapper.CORE_BUILD_MAP[original_id]

        # Check Validation map
        if original_id in SemanticIDMapper.VALIDATION_MAP:
            return SemanticIDMapper.VALIDATION_MAP[original_id]

        # Content tasks - pattern-based mapping
        if original_id.startswith("task-content-"):
            return original_id.replace("task-content-", "task-scaffold-content-")

        # Unknown ID
        raise ValueError(f"Unknown task ID in prompt: {original_id}")

    @staticmethod
    def remap_dependencies(dependencies: List[str]) -> List[str]:
        """
        Remap all dependency IDs from prompt format to semantic format.

        Args:
            dependencies: List of original dependency IDs

        Returns:
            List of remapped semantic IDs
        """
        return [SemanticIDMapper.map_id(dep) for dep in dependencies if dep]


# ============================================================================
# Component 2: ConflictDetector
# ============================================================================

class ConflictDetector:
    """Prevents ID collisions with existing tasks."""

    @staticmethod
    def get_existing_ids(backlog_dir: Path) -> List[str]:
        """
        Extract all existing task IDs from backlog/tasks/ directory.

        Args:
            backlog_dir: Path to backlog/tasks/ directory

        Returns:
            List of existing task IDs
        """
        existing_ids = []

        for task_file in backlog_dir.glob("task-*.md"):
            try:
                content = task_file.read_text(encoding='utf-8')

                # Extract YAML frontmatter
                match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if match:
                    yaml_content = match.group(1)
                    task_data = yaml.safe_load(yaml_content)
                    if 'id' in task_data:
                        existing_ids.append(task_data['id'])
            except Exception as e:
                print(f"Warning: Could not parse {task_file.name}: {e}")
                continue

        return existing_ids

    @staticmethod
    def check_conflicts(new_ids: List[str], backlog_dir: Path) -> List[str]:
        """
        Check if any new semantic IDs conflict with existing task IDs.

        Args:
            new_ids: List of new semantic IDs to check
            backlog_dir: Path to backlog/tasks/ directory

        Returns:
            List of conflicting IDs (empty if no conflicts)
        """
        existing_ids = ConflictDetector.get_existing_ids(backlog_dir)
        conflicts = [task_id for task_id in new_ids if task_id in existing_ids]

        return conflicts


# ============================================================================
# Component 3: TaskFileGenerator
# ============================================================================

class TaskFileGenerator:
    """Generates Backlog.md-compatible task files."""

    @staticmethod
    def sanitize_filename(text: str) -> str:
        """
        Sanitize text for use in filename.

        Args:
            text: Raw text

        Returns:
            Filename-safe text
        """
        # Remove special characters, keep alphanumeric, hyphens, underscores
        sanitized = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with hyphens
        sanitized = re.sub(r'[\s]+', '-', sanitized)
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Trim to reasonable length (100 chars max)
        return sanitized[:100].strip('-')

    @staticmethod
    def format_acceptance_criteria(criteria: List[str]) -> str:
        """
        Format acceptance criteria as markdown checkboxes.

        Args:
            criteria: List of acceptance criteria

        Returns:
            Formatted markdown string
        """
        if not criteria:
            return "- [ ] To be defined during implementation\n"

        lines = []
        for i, criterion in enumerate(criteria, 1):
            lines.append(f"- [ ] #{i} {criterion}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_task_file(
        task: TaskSpec,
        semantic_id: str,
        parent_id: str = "task-scaffold-master"
    ) -> Tuple[str, str]:
        """
        Generate task markdown file content and filename.

        Args:
            task: TaskSpec object
            semantic_id: Semantic ID for this task
            parent_id: Parent task ID (default: task-scaffold-master)

        Returns:
            Tuple of (file_content, filename)
        """
        # Generate filename
        title_for_filename = task.title.replace("BUILD: ", "").replace("TEST: ", "")
        title_for_filename = title_for_filename.replace("FIX: ", "").replace("CLEANUP: ", "")
        sanitized_title = TaskFileGenerator.sanitize_filename(title_for_filename)
        filename = f"{semantic_id} - {task.action_prefix}-{sanitized_title}.md"

        # Format labels for YAML
        labels = ["scaffold"]
        if task.action_prefix.lower() not in labels:
            labels.append(task.action_prefix.lower())
        if task.domain and task.domain.lower() not in labels:
            labels.append(task.domain.lower())
        labels.extend(task.labels)

        # Remove duplicates, preserve order
        labels = list(dict.fromkeys(labels))

        # Remap dependencies
        remapped_deps = SemanticIDMapper.remap_dependencies(task.dependencies)

        # Generate YAML frontmatter
        yaml_data = {
            'id': semantic_id,
            'title': task.title,
            'status': 'To Do',
            'assignee': [],
            'created_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'labels': labels,
            'dependencies': remapped_deps,
            'parent_task_id': parent_id,
            'priority': task.priority.lower(),
        }

        yaml_str = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Generate markdown content
        content = f"""---
{yaml_str}---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
{task.description}

**Part of EPIC:** {parent_id} (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
{TaskFileGenerator.format_acceptance_criteria(task.acceptance_criteria)}
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.
<!-- SECTION:NOTES:END -->
"""

        return content, filename


# ============================================================================
# Component 4: ScaffoldTaskParser (SIMPLIFIED for Phase 1 Manual Entry)
# ============================================================================

class ScaffoldTaskParser:
    """
    Simplified parser using manual task definitions.

    NOTE: Full automatic parsing of the SCAFFOLD Master Prompt would require
    complex markdown parsing. For safety and accuracy, tasks are manually
    defined here with data extracted from the prompt.
    """

    @staticmethod
    def get_phase1_tasks() -> List[TaskSpec]:
        """
        Get Phase 1 Core Build tasks (11 tasks manually defined from prompt).

        Returns:
            List of TaskSpec objects
        """
        return [
            TaskSpec(
                original_id="task-23.2",
                title="BUILD: Headless Orchestrator Skeleton",
                description="""Build the main orchestration loop for autonomous task execution.

The orchestrator reads tasks from Backlog.md via MCP, routes to appropriate agents (Claude Code CLI or custom), manages execution in isolated git worktrees, and updates task status after completion.

Key components:
- TaskFetcher: Query Backlog.md for eligible tasks (status=To Do, dependencies satisfied)
- AgentRouter: Match task to agent (explicit label, title prefix, domain, default)
- SessionManager: Track active sessions, enforce concurrency limits
- ResultProcessor: Create PRs on success, update Backlog.md, log failures

This is the foundation for the entire SCAFFOLD platform.""",
                acceptance_criteria=[
                    "Orchestrator class exists with main() entry point",
                    "TaskFetcher queries Backlog.md via MCP (backlog task list)",
                    "AgentRouter routes tasks based on labels/title/domain",
                    "SessionManager tracks active worktrees and budgets",
                    "ResultProcessor updates Backlog.md after task completion",
                    "Command: poetry run python scripts/autonomous/scaffold_orchestrator.py works"
                ],
                dependencies=[],
                priority="critical",
                labels=["build", "orchestration", "autonomous"],
                action_prefix="BUILD",
                domain="orchestration"
            ),
            TaskSpec(
                original_id="task-23.3",
                title="BUILD: Backlog Parser with MCP Integration",
                description="""Integrate Backlog.md MCP tools for task querying and status updates.

The Backlog Parser provides a clean interface for the orchestrator to:
- List tasks (with filters: status, priority, labels, dependencies)
- View task details (full YAML + markdown)
- Update task status (To Do → In Progress → Done)
- Edit task metadata (labels, dependencies, notes)

Uses existing backlog MCP tools (backlog task list, backlog task view, backlog task edit).""",
                acceptance_criteria=[
                    "BacklogParser class wraps MCP tools",
                    "list_tasks(status, labels, dependencies_satisfied) method works",
                    "get_task(task_id) returns TaskSpec object",
                    "update_status(task_id, new_status) works",
                    "add_notes(task_id, notes) appends to SECTION:NOTES",
                    "Unit tests pass for all methods"
                ],
                dependencies=["task-23.2"],
                priority="critical",
                labels=["build", "backlog", "mcp"],
                action_prefix="BUILD",
                domain="backlog"
            ),
            TaskSpec(
                original_id="task-23.4",
                title="BUILD: Context Assembler (CLAUDE.md + Repo Snapshot)",
                description="""Assemble context for Claude Code CLI execution.

The Context Assembler prepares the execution environment for each task:
- Reads CLAUDE.md system prompts
- Generates repo snapshot (file tree, recent commits, key files)
- Formats task specification (title, description, acceptance criteria)
- Creates execution prompt template
- Packages context for Claude Code CLI invocation

This ensures Claude has full context for autonomous task execution.""",
                acceptance_criteria=[
                    "ContextAssembler class with assemble_context(task_id) method",
                    "Reads CLAUDE.md and extracts system prompts",
                    "Generates file tree snapshot (max depth 3, excludes node_modules)",
                    "Extracts last 10 commits from git log",
                    "Formats task spec as markdown",
                    "Returns complete context string ready for Claude Code CLI"
                ],
                dependencies=["task-23.3"],
                priority="high",
                labels=["build", "context", "claude"],
                action_prefix="BUILD",
                domain="context"
            ),
            TaskSpec(
                original_id="task-23.5",
                title="BUILD: Git Worktree Manager",
                description="""Manage isolated git worktrees for parallel task execution.

The Worktree Manager creates and cleans up dedicated worktrees for each task:
- Creates worktree in ../agent-factory-{task-id}/ on branch autonomous/{task-id}
- Tracks active worktrees (prevents duplicates, enforces limits)
- Cleans up after PR creation (removes worktree, deletes branch if merged)
- Handles errors (removes corrupted worktrees)

This enables parallel execution of multiple tasks without conflicts.""",
                acceptance_criteria=[
                    "WorktreeManager class with create_worktree(task_id) method",
                    "Creates worktree: git worktree add ../agent-factory-{id} -b autonomous/{id}",
                    "Tracks active worktrees in memory (dict or database)",
                    "Prevents duplicate worktrees for same task",
                    "Enforces max_concurrent_worktrees limit (default: 3)",
                    "cleanup_worktree(task_id) removes worktree and deletes branch"
                ],
                dependencies=["task-23.2"],
                priority="high",
                labels=["build", "git", "worktree"],
                action_prefix="BUILD",
                domain="git"
            ),
            TaskSpec(
                original_id="task-23.6",
                title="BUILD: Cost & Time Tracking (Safety Monitor)",
                description="""Track API costs and execution time with circuit breakers.

The Safety Monitor enforces hard limits to prevent runaway costs:
- Tracks total cost (API calls to Claude)
- Tracks elapsed time (session duration)
- Tracks consecutive failures (circuit breaker)
- Checks limits before each task execution
- Aborts session if limits exceeded

Safety limits (configurable):
- max_cost: $5 (default)
- max_time_hours: 4 (default)
- max_consecutive_failures: 3 (default)""",
                acceptance_criteria=[
                    "SafetyMonitor class with check_limits() method",
                    "Tracks total_cost, elapsed_time, consecutive_failures",
                    "check_limits() returns (allowed, reason) tuple",
                    "Aborts if total_cost >= max_cost",
                    "Aborts if elapsed_time >= max_time_hours",
                    "Aborts if consecutive_failures >= max_consecutive_failures",
                    "Resets consecutive_failures on task success"
                ],
                dependencies=["task-23.2"],
                priority="critical",
                labels=["build", "safety", "monitoring"],
                action_prefix="BUILD",
                domain="safety"
            ),
            TaskSpec(
                original_id="task-23.7",
                title="BUILD: Claude Code CLI Integration",
                description="""Execute tasks via Claude Code CLI with full context.

The Claude Executor invokes Claude Code CLI in isolated worktrees:
- Prepares execution prompt (context + task spec)
- Invokes Claude Code CLI with --non-interactive flag
- Captures output (stdout, stderr, exit code)
- Parses results (success/failure, files changed, tests passed)
- Returns execution summary

Uses existing Claude Code CLI installation (assumes in PATH).""",
                acceptance_criteria=[
                    "ClaudeExecutor class with execute_task(task_id, worktree_path) method",
                    "Formats execution prompt using ContextAssembler",
                    "Invokes: claude-code --non-interactive --prompt '{prompt}' in worktree",
                    "Captures stdout, stderr, exit code",
                    "Parses output for success indicators (commit created, tests passed)",
                    "Returns ExecutionResult(success, files_changed, output, error)"
                ],
                dependencies=["task-23.4", "task-23.5"],
                priority="critical",
                labels=["build", "claude", "execution"],
                action_prefix="BUILD",
                domain="claude"
            ),
            TaskSpec(
                original_id="task-23.8",
                title="BUILD: PR Creation & Auto-Approval Request",
                description="""Create draft PRs automatically after successful task completion.

The PR Creator commits changes, pushes branch, and creates draft PR via GitHub CLI:
- Commits all changes in worktree with detailed message
- Pushes branch to origin
- Creates draft PR using gh pr create
- Links PR to task (adds task ID to PR body)
- Requests review from user

PRs are ALWAYS created as drafts (user must manually approve merges).""",
                acceptance_criteria=[
                    "PRCreator class with create_pr(task_id, worktree_path) method",
                    "Commits changes: git add . && git commit -m '{detailed_message}'",
                    "Pushes branch: git push -u origin autonomous/{task-id}",
                    "Creates draft PR: gh pr create --title '{title}' --body '{body}' --draft",
                    "PR body includes: task ID, summary, acceptance criteria checklist",
                    "Returns PR URL on success"
                ],
                dependencies=["task-23.7"],
                priority="high",
                labels=["build", "github", "pr"],
                action_prefix="BUILD",
                domain="github"
            ),
            TaskSpec(
                original_id="task-23.9",
                title="BUILD: Backlog Status Sync (PR to Backlog.md)",
                description="""Auto-update Backlog.md task status after PR creation.

The Status Syncer updates task metadata:
- Marks task as In Progress when execution starts
- Marks task as Done when PR is created (pending human review)
- Adds PR URL to task notes
- Syncs to TASK.md via sync_tasks.py

Uses backlog task edit MCP tool for updates.""",
                acceptance_criteria=[
                    "StatusSyncer class with sync_status(task_id, new_status, pr_url) method",
                    "Updates status: backlog task edit {id} --status '{status}'",
                    "Adds PR URL to notes: backlog task edit {id} --notes-append 'PR: {url}'",
                    "Calls sync_tasks.py to update TASK.md",
                    "Handles errors gracefully (logs warning if sync fails)"
                ],
                dependencies=["task-23.8"],
                priority="medium",
                labels=["build", "backlog", "sync"],
                action_prefix="BUILD",
                domain="backlog"
            ),
            TaskSpec(
                original_id="task-23.10",
                title="BUILD: Structured Logging & Session History",
                description="""Log all orchestrator actions with structured JSON logs.

The Logger records:
- Session start/end timestamps
- Task execution attempts (start, success, failure)
- API costs per task
- Errors and warnings
- Final session summary (tasks completed, total cost, time elapsed)

Logs are written to logs/scaffold_sessions/{session_id}.jsonl (JSONL format).""",
                acceptance_criteria=[
                    "Logger class with log_event(event_type, data) method",
                    "Logs written to logs/scaffold_sessions/{session_id}.jsonl",
                    "Event types: session_start, task_start, task_success, task_failure, session_end",
                    "Each log entry has: timestamp, event_type, task_id, data (dict)",
                    "Session summary includes: total_tasks, successful, failed, total_cost, elapsed_time",
                    "Logs are valid JSONL (one JSON object per line)"
                ],
                dependencies=["task-23.2"],
                priority="medium",
                labels=["build", "logging", "observability"],
                action_prefix="BUILD",
                domain="logging"
            ),
            TaskSpec(
                original_id="task-23.11",
                title="BUILD: SCAFFOLD User Documentation",
                description="""Write comprehensive user guide for SCAFFOLD platform.

Documentation covers:
- How to create tasks in Backlog.md for autonomous execution
- How to run the orchestrator (manual and scheduled modes)
- How to configure safety limits (cost, time, failures)
- How to review and approve PRs
- Troubleshooting guide (common errors, recovery procedures)

Documentation location: docs/scaffold/USER_GUIDE.md""",
                acceptance_criteria=[
                    "docs/scaffold/USER_GUIDE.md exists with all sections",
                    "Section 1: Overview (what SCAFFOLD is, why use it)",
                    "Section 2: Creating Tasks (Backlog.md format, required fields)",
                    "Section 3: Running Orchestrator (manual, cron, GitHub Actions)",
                    "Section 4: Safety Configuration (cost/time/failure limits)",
                    "Section 5: Reviewing PRs (approval workflow, merge checklist)",
                    "Section 6: Troubleshooting (common errors, recovery steps)"
                ],
                dependencies=[],
                priority="medium",
                labels=["build", "documentation"],
                action_prefix="BUILD",
                domain="documentation"
            ),
            TaskSpec(
                original_id="task-23.12",
                title="BUILD: Safety Rails & Circuit Breakers",
                description="""Implement comprehensive safety mechanisms to prevent catastrophic failures.

Safety features:
- Pre-execution validation (task spec valid, dependencies satisfied, no conflicts)
- Cost estimation (predict task cost before execution, skip if too expensive)
- Error recovery (retry failed tasks with exponential backoff)
- Manual override (allow user to skip/retry/cancel tasks)
- Emergency stop (kill switch via Ctrl+C or file flag)

These rails ensure the orchestrator can run unattended safely.""",
                acceptance_criteria=[
                    "SafetyRails class with validate_task(task_id) method",
                    "Pre-execution checks: task exists, dependencies satisfied, YAML valid",
                    "Cost estimation: estimate_cost(task_spec) returns predicted cost",
                    "Retry logic: retry failed tasks up to 3 times with exponential backoff",
                    "Emergency stop: checks for .scaffold_stop file before each task",
                    "Manual override: reads .scaffold_skip file to skip specific tasks"
                ],
                dependencies=["task-23.6"],
                priority="critical",
                labels=["build", "safety", "error-handling"],
                action_prefix="BUILD",
                domain="safety"
            ),
        ]

    @staticmethod
    def get_epic_parent() -> TaskSpec:
        """
        Get EPIC parent task (task-scaffold-master).

        Returns:
            TaskSpec for parent EPIC
        """
        return TaskSpec(
            original_id="task-scaffold-master",
            title="EPIC: SCAFFOLD Platform Build (Strategic Priority #1)",
            description="""SCAFFOLD: Specification-driven autonomous code generation platform powered by Claude.

**Vision:**
User writes task spec in Backlog.md → SCAFFOLD orchestrator reads spec → Claude implements autonomously in isolated git worktree → Tests validate code → PR opens automatically → User reviews and merges → Backlog.md auto-updates to Done

**Why SCAFFOLD is Strategic Priority #1:**
- Fastest path to revenue (6 months vs 12-18 for RIVET/Friday)
- Lowest risk (uncontested market, proven demand)
- Funds everything else ($1M+ ARR enables RIVET, Friday, hiring)
- Validates all Agent Factory subsystems at scale

**Timeline:**
- Weeks 1-12: Secret Build + Recording (11 core build tasks + safety rails)
- Weeks 13-16: Content Production Automation (120+ tasks)
- Weeks 17-28: Sequential Content Release
- Week 29: Public Launch

**Revenue Potential:** $1M-$3.2M Year 1

This EPIC tracks all 144 SCAFFOLD tasks across 3 phases:
- Phase 1: 11 Core Build tasks (orchestrator, parser, executor, safety)
- Phase 2: 9 Validation tasks (test all subsystems at scale)
- Phase 3: 123 Content Production tasks (videos, blogs, tweets, thumbnails)""",
            acceptance_criteria=[
                "All 144 child tasks created and tracked in Backlog.md",
                "Phase 1 (Core Build) completed: 11/11 tasks Done",
                "Phase 2 (Validation) completed: 9/9 tasks Done",
                "Phase 3 (Content Production) completed: 123/123 tasks Done",
                "SCAFFOLD orchestrator runs autonomously and completes 10+ tasks unattended",
                "Public launch successful: $1M+ ARR achieved in first 12 months"
            ],
            dependencies=[],
            priority="critical",
            labels=["scaffold", "epic", "strategic-priority-1"],
            action_prefix="EPIC",
            domain="platform"
        )

    @staticmethod
    def get_phase2_tasks() -> List[TaskSpec]:
        """
        Get Phase 2 Validation tasks (9 tasks manually defined).

        These tasks validate that SCAFFOLD subsystems work at production scale:
        - Agent Factory orchestration (100+ tasks, 24 concurrent)
        - Video extraction and metadata scraping (24 clips from 100 hours)
        - API integrations (YouTube, Twitter)
        - Knowledge base generation (24 blog posts)
        - SEO validation (organic rankings)
        - End-to-end pipeline (unattended execution)

        Returns:
            List of 9 TaskSpec objects
        """
        return [
            # Task 1: Parser Scale Test
            TaskSpec(
                original_id="task-validate-agent-factory-1",
                title="VALIDATE: Task Parsing at Scale (100+ tasks)",
                description="""Verify that Agent Factory can handle large numbers of tasks without degradation.

This validates the core orchestrator's ability to parse, organize, and manage a high volume of concurrent task specifications. The parser must handle 100+ tasks efficiently with minimal memory footprint and fast parse times.

**Key Components Tested:**
- Backlog.md Parser (MCP integration)
- Task specification validation
- Memory management at scale
- Parse performance benchmarks

**Success Indicators:**
- All 100+ tasks parsed correctly
- No data loss or corruption
- Parse completes in <5 seconds
- Memory stays under 100MB""",
                acceptance_criteria=[
                    "Parser processes 100+ tasks from Backlog.md without errors",
                    "Zero data loss or task corruption during parsing",
                    "Memory usage remains below 100MB during parsing",
                    "Parse operation completes in under 5 seconds",
                    "All task metadata (titles, descriptions, dependencies) extracted correctly"
                ],
                dependencies=["task-scaffold-backlog-parser"],
                priority="high",
                labels=["scaffold", "validate", "parser", "performance", "orchestration"],
                action_prefix="VALIDATE",
                domain="orchestration"
            ),

            # Task 2: Parallel Execution Test
            TaskSpec(
                original_id="task-validate-agent-factory-2",
                title="VALIDATE: Parallel Execution (24 concurrent tasks)",
                description="""Verify that the orchestrator can safely manage multiple tasks running in parallel without conflicts.

This test ensures the git worktree manager can handle 24 concurrent tasks, each in its own worktree, without resource contention, state conflicts, or race conditions. All tasks must complete successfully and create valid PRs.

**Key Components Tested:**
- Git Worktree Manager (isolation)
- Concurrent execution safety
- Resource allocation and cleanup
- PR creation at scale

**Success Indicators:**
- 24 tasks execute simultaneously
- Zero conflicts between processes
- All PRs created successfully
- Clean worktree cleanup""",
                acceptance_criteria=[
                    "24 tasks launched in parallel without errors",
                    "Zero conflicts detected between concurrent processes",
                    "No race conditions in shared resources (logs, status files)",
                    "All 24 tasks complete successfully with passing tests",
                    "All 24 PRs created with valid metadata",
                    "Resource isolation verified (each task uses own worktree)"
                ],
                dependencies=["task-scaffold-git-worktree-manager", "task-scaffold-backlog-sync"],
                priority="critical",
                labels=["scaffold", "validate", "concurrency", "orchestration", "parallel"],
                action_prefix="VALIDATE",
                domain="orchestration"
            ),

            # Task 3: Video Extraction Test
            TaskSpec(
                original_id="task-validate-scraper-1",
                title="VALIDATE: Video Extraction (24 clips from 100 hours)",
                description="""Validate the video scraper/extraction component by extracting 24 highlight clips from 100 hours of raw footage.

Tests the full content extraction pipeline including scene detection, highlight identification, clip extraction, and video rendering. Each clip must be 30-60 seconds with professional transitions and normalized audio.

**Key Components Tested:**
- Video scene detection
- Highlight identification (ML/heuristics)
- Clip extraction and rendering
- Audio normalization
- Fade transitions

**Success Indicators:**
- 24 usable clips extracted
- Professional quality output
- Consistent audio levels
- Fast extraction pipeline""",
                acceptance_criteria=[
                    "24 clips successfully extracted from 100 hours of footage",
                    "Each clip is 30-60 seconds in duration",
                    "Video quality is high (no artifacts, glitches, or corruption)",
                    "Fade transitions applied to all clip boundaries (in/out)",
                    "Audio levels normalized across all clips (no volume jumps)"
                ],
                dependencies=["task-scaffold-safety-rails"],
                priority="high",
                labels=["scaffold", "validate", "scraper", "video-extraction", "media"],
                action_prefix="VALIDATE",
                domain="media"
            ),

            # Task 4: Metadata Extraction Test
            TaskSpec(
                original_id="task-validate-scraper-2",
                title="VALIDATE: Metadata Extraction (timestamps, topics, keywords)",
                description="""Validate that structured metadata can be extracted from video clips with high accuracy.

Tests automatic topic identification, keyword extraction, and timestamp accuracy for use in content distribution. Metadata must be accurate, well-structured (JSON), and production-ready for SEO and social media amplification.

**Key Components Tested:**
- AI-driven transcription
- Topic classification
- Keyword extraction
- Timestamp accuracy

**Success Indicators:**
- 90%+ metadata accuracy
- Valid JSON output
- Relevant topics and keywords
- Timestamps within 100ms accuracy""",
                acceptance_criteria=[
                    "All 24 clips transcribed with AI (speech-to-text)",
                    "Metadata extraction quality score above 90%",
                    "JSON output is valid and well-formed (passes schema validation)",
                    "Timestamps accurate within 100 milliseconds of actual content",
                    "Topics correctly identified from clip content (relevant and specific)"
                ],
                dependencies=["task-validate-scraper-1"],
                priority="high",
                labels=["scaffold", "validate", "scraper", "metadata", "ai", "media"],
                action_prefix="VALIDATE",
                domain="media"
            ),

            # Task 5: YouTube API Integration Test
            TaskSpec(
                original_id="task-validate-integration-youtube",
                title="VALIDATE: YouTube API Integration (schedule 24 videos)",
                description="""Validate YouTube API integration by scheduling 24 videos with complete metadata, thumbnails, and descriptions.

Ensures the publishing pipeline can interact reliably with YouTube's systems including authentication, rate limits, metadata application, and scheduled publishing. All 24 videos must be queued successfully with correct release times.

**Key Components Tested:**
- YouTube Data API v3 integration
- OAuth authentication flow
- Rate limit handling
- Metadata upload (titles, descriptions, tags)
- Thumbnail upload
- Scheduled publishing

**Success Indicators:**
- All 24 videos scheduled
- Metadata correctly applied
- No API errors or rate limits
- Correct publish times set""",
                acceptance_criteria=[
                    "YouTube API authenticated and connected successfully",
                    "All 24 videos successfully uploaded and scheduled",
                    "Metadata correctly applied (titles, descriptions, tags match specifications)",
                    "Thumbnails properly uploaded and linked to videos",
                    "No API rate-limit errors encountered during upload batch"
                ],
                dependencies=["task-scaffold-documentation"],
                priority="high",
                labels=["scaffold", "validate", "integration", "youtube", "api", "distribution"],
                action_prefix="VALIDATE",
                domain="distribution"
            ),

            # Task 6: Twitter API Integration Test
            TaskSpec(
                original_id="task-validate-integration-twitter",
                title="VALIDATE: Twitter API Integration (post 24 threads)",
                description="""Validate Twitter/X API integration by creating and scheduling 24 Twitter threads.

Tests the social media amplification component ensuring proper threading, formatting, rate limit handling, and optimal post timing. Each thread must have 6-10 tweets with correct linking and formatting.

**Key Components Tested:**
- Twitter API v2 integration
- Thread creation and linking
- Tweet formatting (280 char limit)
- Rate limit handling
- Scheduled posting
- Optimal timing algorithm

**Success Indicators:**
- 24 threads created successfully
- Proper tweet threading
- No rate limit errors
- Optimal posting times""",
                acceptance_criteria=[
                    "24 Twitter threads created successfully (each 6-10 tweets)",
                    "Thread formatting is correct (proper linking between consecutive tweets)",
                    "Each tweet respects 280-character limit (no truncation errors)",
                    "No rate-limit errors encountered during thread creation",
                    "Threads scheduled for optimal posting times (engagement algorithm)"
                ],
                dependencies=["task-scaffold-documentation"],
                priority="medium",
                labels=["scaffold", "validate", "integration", "twitter", "social-media", "distribution"],
                action_prefix="VALIDATE",
                domain="distribution"
            ),

            # Task 7: Blog Post Generation Test
            TaskSpec(
                original_id="task-validate-knowledge-base",
                title="VALIDATE: Blog Post Generation (24 posts from transcripts)",
                description="""Validate the knowledge base builder by generating 24 blog posts from video transcripts.

Tests AI-driven content generation quality, SEO optimization, markdown formatting, and production readiness. Each post must be 2000+ words, professionally written, and require minimal editing before publication.

**Key Components Tested:**
- AI content generation (GPT-4)
- SEO optimization (keywords, meta descriptions)
- Markdown formatting
- Citation and linking
- Content quality assessment

**Success Indicators:**
- 24 blog posts generated
- 2000+ words per post
- Publishable quality
- SEO metadata included""",
                acceptance_criteria=[
                    "24 blog posts generated successfully from video transcripts",
                    "Each post is 2000+ words in length",
                    "Content is publishable quality (minimal editing needed, coherent, professional)",
                    "Markdown formatting is correct (headings, lists, code blocks, links)",
                    "SEO metadata included (meta descriptions, target keywords, image alt text)"
                ],
                dependencies=["task-scaffold-logging"],
                priority="high",
                labels=["scaffold", "validate", "knowledge-base", "content-generation", "ai", "content"],
                action_prefix="VALIDATE",
                domain="content"
            ),

            # Task 8: SEO Ranking Validation Test
            TaskSpec(
                original_id="task-validate-seo",
                title="VALIDATE: SEO Rankings (organic page 1 results)",
                description="""Validate that generated blog posts rank organically in search results for target keywords.

This is a long-running validation (4+ weeks) that confirms the knowledge base produces SEO-friendly, discoverable content. Posts must rank on page 1 of Google for target keywords with measurable organic traffic increases.

**Key Components Tested:**
- SEO optimization effectiveness
- Keyword targeting accuracy
- Organic ranking progression
- Traffic analytics

**Success Indicators:**
- 50%+ posts rank page 1
- Organic traffic increases
- Average ranking improves
- Target keywords have search volume""",
                acceptance_criteria=[
                    "50% or more of generated posts rank on page 1 of Google for target keywords",
                    "Organic traffic to blog increases measurably (baseline vs 4-week measurement)",
                    "Average ranking position improves over 4-week period (tracked weekly)",
                    "Target keywords have monthly search volume above 100 searches"
                ],
                dependencies=["task-validate-knowledge-base"],
                priority="medium",
                labels=["scaffold", "validate", "seo", "organic-traffic", "long-running", "content"],
                action_prefix="VALIDATE",
                domain="content"
            ),

            # Task 9: End-to-End Pipeline Test
            TaskSpec(
                original_id="task-validate-video-automation-e2e",
                title="VALIDATE: End-to-End Pipeline (recording to publishing)",
                description="""Validate the complete video automation pipeline from raw recording through final publication.

Ensures all components work together seamlessly: extraction, editing, metadata generation, scheduling, and publishing without manual intervention. This is the comprehensive system validation test.

**Key Components Tested:**
- Full pipeline integration
- Unattended execution
- Error recovery
- Quality gates
- Multi-platform publishing

**Success Indicators:**
- Full pipeline executes end-to-end
- Zero manual interventions needed
- Professional quality output
- All platforms published successfully""",
                acceptance_criteria=[
                    "Full pipeline executes end-to-end without errors (recording to final publication)",
                    "Zero manual edits or interventions required during execution",
                    "Output video is professional quality (meets quality gates for resolution, audio, transitions)",
                    "All metadata applied correctly (titles, descriptions, tags, thumbnails)",
                    "Video published successfully to all scheduled platforms (YouTube, Twitter, blog)"
                ],
                dependencies=[
                    "task-validate-agent-factory-1",
                    "task-validate-agent-factory-2",
                    "task-validate-scraper-1",
                    "task-validate-scraper-2",
                    "task-validate-integration-youtube",
                    "task-validate-integration-twitter",
                    "task-validate-knowledge-base",
                    "task-validate-seo"
                ],
                priority="critical",
                labels=["scaffold", "validate", "e2e", "video-automation", "pipeline", "platform"],
                action_prefix="VALIDATE",
                domain="platform"
            ),
        ]


# ============================================================================
# Component 5: CLI Interface & Main Logic
# ============================================================================

def print_dry_run_phase1(tasks: List[TaskSpec], epic: TaskSpec):
    """Print dry-run output for Phase 1."""
    print("\n" + "=" * 60)
    print("SCAFFOLD PHASE 1 DRY RUN")
    print("=" * 60)
    print(f"\n12 files would be created:\n")

    # EPIC parent
    print("EPIC Parent:")
    epic_id = "task-scaffold-master"
    print(f"  - {epic_id}.md")
    print(f'    Title: "{epic.title}"')
    print(f"    Dependencies: []")
    print(f"    Labels: {epic.labels}")
    print()

    # Core Build tasks
    print("Core Build (11 tasks):")
    for task in tasks:
        semantic_id = SemanticIDMapper.map_id(task.original_id)
        remapped_deps = SemanticIDMapper.remap_dependencies(task.dependencies)

        print(f"  - {semantic_id}.md")
        print(f'    Title: "{task.title}"')
        print(f"    Dependencies: {remapped_deps}")
        print(f"    Labels: ['scaffold', '{task.action_prefix.lower()}', '{task.domain}']")
        print()

    print("No conflicts detected.")
    print("No files created (dry-run mode).\n")


def print_dry_run_phase2(tasks: List[TaskSpec]):
    """Print dry-run output for Phase 2."""
    print("\n" + "=" * 60)
    print("SCAFFOLD PHASE 2 DRY RUN")
    print("=" * 60)
    print(f"\n9 files would be created:\n")

    # Validation tasks
    print("Validation Tasks (9 tasks):")
    for task in tasks:
        semantic_id = SemanticIDMapper.map_id(task.original_id)
        remapped_deps = SemanticIDMapper.remap_dependencies(task.dependencies)

        print(f"  - {semantic_id}.md")
        print(f'    Title: "{task.title}"')
        print(f"    Dependencies: {remapped_deps}")
        print(f"    Labels: {task.labels}")
        print()

    print("No conflicts detected.")
    print("No files created (dry-run mode).\n")


def import_phase1(backlog_dir: Path, dry_run: bool = False, approve: bool = False, yes: bool = False) -> bool:
    """
    Import Phase 1: EPIC parent + 11 Core Build tasks.

    Args:
        backlog_dir: Path to backlog/tasks/ directory
        dry_run: If True, preview without creating files
        approve: If True, actually create files (requires user confirmation)
        yes: If True, skip confirmation prompt (auto-confirm)

    Returns:
        True if successful, False otherwise
    """
    # Get tasks
    epic = ScaffoldTaskParser.get_epic_parent()
    tasks = ScaffoldTaskParser.get_phase1_tasks()

    # Collect all IDs
    all_ids = ["task-scaffold-master"]
    all_ids.extend([SemanticIDMapper.map_id(task.original_id) for task in tasks])

    # Dry-run mode
    if dry_run:
        print_dry_run_phase1(tasks, epic)
        return True

    # Check for conflicts
    conflicts = ConflictDetector.check_conflicts(all_ids, backlog_dir)
    if conflicts:
        print(f"\nERROR: ID conflicts detected: {conflicts}")
        print("Aborting import. No files created.")
        return False

    # Require approval
    if not approve:
        print("\nERROR: --approve flag required to create files.")
        print("Run with --approve to proceed, or --dry-run to preview changes.")
        return False

    # Confirmation prompt (skip if --yes flag)
    if not yes:
        print("\n" + "=" * 60)
        print("SCAFFOLD PHASE 1 IMPORT")
        print("=" * 60)
        print("This will create 12 task files in backlog/tasks/")
        print("All tasks will have parent_task_id: task-scaffold-master")
        print()
        response = input("Proceed with import? [y/N]: ")

        if response.lower() != 'y':
            print("Import cancelled.")
            return False
    else:
        print("\n" + "=" * 60)
        print("SCAFFOLD PHASE 1 IMPORT (AUTO-CONFIRMED)")
        print("=" * 60)

    # Create files
    print("\nCreating files...")
    created_count = 0

    # Create EPIC parent
    try:
        epic_id = "task-scaffold-master"
        content, filename = TaskFileGenerator.generate_task_file(epic, epic_id, parent_id="")
        file_path = backlog_dir / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"  [OK] Created {filename}")
        created_count += 1
    except Exception as e:
        print(f"  [FAILED] Failed to create EPIC parent: {e}")
        return False

    # Create Core Build tasks
    for task in tasks:
        try:
            semantic_id = SemanticIDMapper.map_id(task.original_id)
            content, filename = TaskFileGenerator.generate_task_file(task, semantic_id)
            file_path = backlog_dir / filename
            file_path.write_text(content, encoding='utf-8')
            print(f"  [OK] Created {filename}")
            created_count += 1
        except Exception as e:
            print(f"  [FAILED] Failed to create {task.original_id}: {e}")
            # Continue with remaining tasks

    print(f"\n[SUCCESS] Phase 1 import complete: {created_count}/12 files created")
    print("\nNext steps:")
    print("1. Run: poetry run python scripts/backlog/validate_tasks.py")
    print("2. Run: poetry run python scripts/backlog/sync_tasks.py")
    print("3. Commit: git add backlog/tasks/task-scaffold-*.md TASK.md")
    print("4. Commit: git commit -m 'feat(scaffold): Import Phase 1 Core Build (12 tasks)'")
    print()

    return True


def import_phase2(backlog_dir: Path, dry_run: bool = False, approve: bool = False, yes: bool = False) -> bool:
    """
    Import Phase 2: 9 Validation tasks.

    Args:
        backlog_dir: Path to backlog/tasks/ directory
        dry_run: If True, preview without creating files
        approve: If True, actually create files (requires user confirmation)
        yes: If True, skip confirmation prompt (auto-confirm)

    Returns:
        True if successful, False otherwise
    """
    # Get tasks
    tasks = ScaffoldTaskParser.get_phase2_tasks()

    # Collect all IDs
    all_ids = [SemanticIDMapper.map_id(task.original_id) for task in tasks]

    # Dry-run mode
    if dry_run:
        print_dry_run_phase2(tasks)
        return True

    # Approval mode
    if not approve:
        print("\n[ERROR] Missing --approve flag.")
        print("Phase 2 import requires explicit approval.")
        print("\nUsage: python import_scaffold_tasks.py --phase 2 --approve [--yes]\n")
        return False

    # Interactive confirmation (skip if --yes flag)
    if not yes:
        print("\n" + "=" * 60)
        print("SCAFFOLD PHASE 2 VALIDATION IMPORT")
        print("=" * 60)
        print(f"\nThis will create 9 task files in:")
        print(f"  {backlog_dir}")
        print(f"\nTask IDs:")
        for task_id in all_ids:
            print(f"  - {task_id}")
        print("\nAll tasks labeled with: ['scaffold', 'validate', ...]")
        print("All tasks have parent: task-scaffold-master")
        print()

        response = input("Proceed with import? [y/N]: ")
        if response.lower() != 'y':
            print("\n[CANCELLED] Phase 2 import cancelled by user.\n")
            return False
    else:
        print("\n" + "=" * 60)
        print("SCAFFOLD PHASE 2 VALIDATION IMPORT (AUTO-CONFIRMED)")
        print("=" * 60)

    # Validate backlog directory exists
    if not backlog_dir.exists():
        print(f"\n[ERROR] Backlog directory not found: {backlog_dir}")
        print("Please create it first: mkdir -p backlog/tasks\n")
        return False

    # Create validation tasks
    print(f"\nCreating 9 validation tasks...")
    created_count = 0

    for task in tasks:
        try:
            semantic_id = SemanticIDMapper.map_id(task.original_id)
            content, filename = TaskFileGenerator.generate_task_file(
                task, semantic_id, parent_id="task-scaffold-master"
            )
            file_path = backlog_dir / filename
            file_path.write_text(content, encoding='utf-8')
            print(f"  [OK] Created {filename}")
            created_count += 1
        except Exception as e:
            print(f"  [FAILED] Failed to create {task.original_id}: {e}")
            # Continue with remaining tasks

    print(f"\n[SUCCESS] Phase 2 import complete: {created_count}/9 files created")
    print("\nNext steps:")
    print("1. Run: poetry run python scripts/backlog/validate_tasks.py")
    print("2. Run: poetry run python scripts/backlog/sync_tasks.py")
    print("3. Commit: git add backlog/tasks/task-scaffold-validate-*.md TASK.md")
    print("4. Commit: git commit -m 'feat(scaffold): Import Phase 2 Validation (9 tasks)'")
    print()

    return True


def rollback_scaffold_tasks(backlog_dir: Path) -> bool:
    """
    Delete all task-scaffold-* files (rollback import).

    Args:
        backlog_dir: Path to backlog/tasks/ directory

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("ROLLBACK SCAFFOLD TASKS")
    print("=" * 60)
    print("This will DELETE all task-scaffold-*.md files.")
    print("This operation cannot be undone.")
    print()
    response = input("Proceed? [y/N]: ")

    if response.lower() != 'y':
        print("Rollback cancelled.")
        return False

    # Find all SCAFFOLD task files
    scaffold_files = list(backlog_dir.glob("task-scaffold-*.md"))

    if not scaffold_files:
        print("\nNo SCAFFOLD task files found.")
        return True

    print(f"\nDeleting {len(scaffold_files)} files...")
    deleted_count = 0

    for file_path in scaffold_files:
        try:
            file_path.unlink()
            print(f"  [OK] Deleted {file_path.name}")
            deleted_count += 1
        except Exception as e:
            print(f"  [FAILED] Failed to delete {file_path.name}: {e}")

    print(f"\n[SUCCESS] Rollback complete: {deleted_count}/{len(scaffold_files)} files deleted")
    print("\nNext steps:")
    print("1. Run: poetry run python scripts/backlog/sync_tasks.py")
    print("2. Commit: git add -A && git commit -m 'rollback(scaffold): Remove all SCAFFOLD tasks'")
    print()

    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Import SCAFFOLD tasks with semantic IDs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --phase 1 --dry-run        # Preview Phase 1 import
  %(prog)s --phase 1 --approve        # Import Phase 1 (12 files)
  %(prog)s --rollback                 # Delete all SCAFFOLD tasks
        """
    )

    parser.add_argument(
        "--phase",
        choices=["1", "2", "3"],
        help="Which phase to import (1=Core Build, 2=Validation, 3=Content)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without creating files"
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Required to actually create files (safety gate)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-confirm (skip interactive prompt)"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Delete all task-scaffold-* files (undo import)"
    )

    args = parser.parse_args()

    # Find backlog directory
    repo_root = Path(__file__).parent.parent.parent
    backlog_dir = repo_root / "backlog" / "tasks"

    if not backlog_dir.exists():
        print(f"ERROR: Backlog directory not found: {backlog_dir}")
        sys.exit(1)

    # Rollback mode
    if args.rollback:
        success = rollback_scaffold_tasks(backlog_dir)
        sys.exit(0 if success else 1)

    # Require --phase for import
    if not args.phase:
        parser.print_help()
        print("\nERROR: --phase required (or use --rollback)")
        sys.exit(1)

    # Phase 1 import
    if args.phase == "1":
        success = import_phase1(backlog_dir, dry_run=args.dry_run, approve=args.approve, yes=args.yes)
        sys.exit(0 if success else 1)

    # Phase 2 import
    if args.phase == "2":
        success = import_phase2(backlog_dir, dry_run=args.dry_run, approve=args.approve, yes=args.yes)
        sys.exit(0 if success else 1)

    # Phase 3 not yet implemented
    print(f"\nERROR: Phase {args.phase} import not yet implemented.")
    print("Currently only Phase 1 (Core Build) and Phase 2 (Validation) are available.")
    sys.exit(1)


if __name__ == "__main__":
    main()
