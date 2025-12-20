"""Safety Rails for SCAFFOLD orchestrator - Pre-execution validation and safety checks.

Implements 6 comprehensive safety mechanisms:
1. Pre-execution validation (task exists, dependencies satisfied, YAML valid)
2. Cost estimation (heuristic-based prediction)
3. Retry logic (exponential backoff, max 3 attempts)
4. Emergency stop (.scaffold_stop file check)
5. Manual override (.scaffold_skip file check)
6. Task validation (validate_task method)

Follows SafetyMonitor pattern: dataclass-based with tuple returns (bool, Optional[str]).
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from agent_factory.scaffold.backlog_parser import BacklogParser, BacklogParserError


class ValidationFailureReason(Enum):
    """Enumeration of all validation failure types."""
    TASK_NOT_FOUND = "task_not_found"
    DEPENDENCIES_NOT_SATISFIED = "dependencies_not_satisfied"
    INVALID_YAML = "invalid_yaml"
    EMERGENCY_STOP_ACTIVE = "emergency_stop_active"
    TASK_SKIPPED = "task_skipped"
    RETRY_LIMIT_EXCEEDED = "retry_limit_exceeded"
    COST_EXCEEDS_BUDGET = "cost_exceeds_budget"


@dataclass
class RetryState:
    """Tracks retry attempts for a single task."""
    task_id: str
    attempt_count: int = 0
    last_error: Optional[str] = None
    backoff_sec: float = 10.0  # Current backoff time
    next_retry_time: float = 0.0  # UTC timestamp when retry allowed

    def should_retry(self) -> bool:
        """Check if task is eligible for retry."""
        return self.attempt_count < 3

    def can_retry_now(self) -> bool:
        """Check if backoff period has elapsed."""
        if self.next_retry_time == 0.0:
            return True
        return time.time() >= self.next_retry_time

    def calculate_next_backoff(self) -> float:
        """Calculate exponential backoff (10s → 30s → 90s)."""
        if self.attempt_count == 0:
            return 10.0
        elif self.attempt_count == 1:
            return 30.0
        else:
            return 90.0


@dataclass
class CostEstimate:
    """Result of cost estimation for a task."""
    task_id: str
    estimated_cost_usd: float
    confidence: float  # 0.0-1.0
    method: str  # "heuristic", "llm", "constant"
    factors: Dict[str, any] = field(default_factory=dict)  # Breakdown of estimation


@dataclass
class SafetyRailsConfig:
    """Configuration for SafetyRails behavior."""
    max_retries: int = 3
    initial_backoff_sec: float = 10.0
    max_backoff_sec: float = 90.0
    enable_cost_estimation: bool = True
    cost_threshold_usd: float = 1.0
    emergency_stop_file: str = ".scaffold_stop"
    skip_file: str = ".scaffold_skip"


class SafetyRailsError(Exception):
    """Base exception for SafetyRails errors."""
    pass


class SafetyRails:
    """
    Pre-execution validation and safety checks for SCAFFOLD tasks.

    Enforces 6 safety mechanisms:
    - Emergency stop (file-based kill switch)
    - Manual skip list (skip specific tasks)
    - Task existence validation
    - Dependency satisfaction check
    - YAML validity verification
    - Retry limit enforcement

    Also provides heuristic cost estimation.

    Each SCAFFOLD session should create one SafetyRails instance.
    """

    def __init__(
        self,
        repo_root: Path,
        backlog_parser: Optional[BacklogParser] = None,
        config: Optional[SafetyRailsConfig] = None
    ):
        """
        Initialize SafetyRails.

        Args:
            repo_root: Root directory of git repository
            backlog_parser: BacklogParser instance (creates new if None)
            config: SafetyRailsConfig (uses defaults if None)
        """
        self.repo_root = Path(repo_root).resolve()
        self.backlog_parser = backlog_parser or BacklogParser()
        self.config = config or SafetyRailsConfig()

        # In-memory retry state (per session, not persisted)
        self._retry_states: Dict[str, RetryState] = {}

    def validate_task(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """
        Main validation entry point. Runs 6 checks sequentially.

        Checks performed:
        1. Emergency stop check (_check_emergency_stop)
        2. Manual skip check (_check_skip_list)
        3. Task existence check (_check_task_exists)
        4. Dependencies check (_check_dependencies)
        5. YAML validity check (_check_yaml_valid)
        6. Retry limit check (_check_retry_allowed)

        Args:
            task_id: Task identifier to validate

        Returns:
            Tuple of (valid, failure_reason):
                - valid=True, reason=None → All checks passed
                - valid=False, reason="..." → Specific failure reason
        """
        # Check 1: Emergency stop
        is_stopped, reason = self._check_emergency_stop()
        if is_stopped:
            return (False, f"Emergency stop: {reason}")

        # Check 2: Manual skip
        is_skipped, reason = self._check_skip_list(task_id)
        if is_skipped:
            return (False, f"Task skipped: {reason}")

        # Check 3: Task exists
        exists, reason = self._check_task_exists(task_id)
        if not exists:
            return (False, f"Task not found: {reason}")

        # Check 4: Dependencies satisfied
        satisfied, reason = self._check_dependencies(task_id)
        if not satisfied:
            return (False, f"Dependencies not satisfied: {reason}")

        # Check 5: YAML valid
        valid, reason = self._check_yaml_valid(task_id)
        if not valid:
            return (False, f"YAML invalid: {reason}")

        # Check 6: Retry allowed
        allowed, reason = self._check_retry_allowed(task_id)
        if not allowed:
            return (False, f"Retry limit exceeded: {reason}")

        # All checks passed
        return (True, None)

    def estimate_cost(self, task_id: str) -> CostEstimate:
        """
        Heuristic-based cost estimation.

        Formula:
        - Base cost: $0.10
        - Priority multiplier: high=1.5x, medium=1.0x, low=0.8x
        - Label adjustments:
          - scaffold: +$0.05
          - build: +$0.15
          - fix: -$0.05
          - refactor: +$0.10
        - Acceptance criteria: +$0.02 per criterion
        - Minimum floor: $0.05

        Args:
            task_id: Task to estimate cost for

        Returns:
            CostEstimate with 70% confidence (heuristic method)
            On error: Conservative $0.50 estimate with 30% confidence
        """
        try:
            task = self.backlog_parser.get_task(task_id)

            # Base cost
            cost = 0.10
            factors = {"base": 0.10}

            # Priority multiplier
            priority_mult = {"high": 1.5, "medium": 1.0, "low": 0.8}.get(
                task.priority, 1.0
            )
            cost *= priority_mult
            factors["priority_multiplier"] = priority_mult

            # Label adjustments
            label_adjustments = {
                "scaffold": 0.05,
                "build": 0.15,
                "fix": -0.05,
                "refactor": 0.10,
            }
            for label in task.labels:
                if label in label_adjustments:
                    adjustment = label_adjustments[label]
                    cost += adjustment
                    factors[f"label_{label}"] = adjustment

            # Acceptance criteria
            if task.acceptance_criteria:
                ac_cost = len(task.acceptance_criteria) * 0.02
                cost += ac_cost
                factors["acceptance_criteria"] = ac_cost

            # Minimum floor
            cost = max(cost, 0.05)

            return CostEstimate(
                task_id=task_id,
                estimated_cost_usd=round(cost, 2),
                confidence=0.70,
                method="heuristic",
                factors=factors
            )

        except Exception as e:
            # Fallback: Conservative estimate
            return CostEstimate(
                task_id=task_id,
                estimated_cost_usd=0.50,
                confidence=0.30,
                method="fallback",
                factors={"error": str(e)}
            )

    def record_failure(self, task_id: str, error: str):
        """
        Record task failure and update retry state.

        Increments attempt_count and calculates exponential backoff.

        Args:
            task_id: Task that failed
            error: Error message
        """
        if task_id not in self._retry_states:
            self._retry_states[task_id] = RetryState(task_id=task_id)

        state = self._retry_states[task_id]
        state.attempt_count += 1
        state.last_error = error
        state.backoff_sec = state.calculate_next_backoff()
        state.next_retry_time = time.time() + state.backoff_sec

    def record_success(self, task_id: str):
        """
        Record task success and clear retry state.

        Args:
            task_id: Task that succeeded
        """
        if task_id in self._retry_states:
            del self._retry_states[task_id]

    def get_retry_state(self, task_id: str) -> Optional[RetryState]:
        """
        Get current retry state for a task.

        Args:
            task_id: Task to check

        Returns:
            RetryState if exists, None otherwise
        """
        return self._retry_states.get(task_id)

    # -------------------------------------------------------------------------
    # Helper Methods (6 Validation Checks)
    # -------------------------------------------------------------------------

    def _check_emergency_stop(self) -> Tuple[bool, Optional[str]]:
        """
        Check for .scaffold_stop file (emergency kill switch).

        File format:
            REASON: Emergency stop reason here
            (additional lines ignored)

        Returns:
            (True, reason) if file exists
            (False, None) if file does not exist
        """
        stop_file = self.repo_root / self.config.emergency_stop_file

        if not stop_file.exists():
            return (False, None)

        try:
            content = stop_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            reason = "Emergency stop active"

            # Parse REASON: line if present
            for line in lines:
                if line.startswith("REASON:"):
                    reason = line[7:].strip()
                    break

            return (True, reason)

        except Exception as e:
            return (True, f"Emergency stop file found but unreadable: {e}")

    def _check_skip_list(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if task is in .scaffold_skip file.

        File format:
            task-42
            task-scaffold-example
            # Comments allowed

        Returns:
            (True, reason) if task_id in skip list
            (False, None) if not in skip list or file doesn't exist
        """
        skip_file = self.repo_root / self.config.skip_file

        if not skip_file.exists():
            return (False, None)

        try:
            content = skip_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")

            for line in lines:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                if line == task_id:
                    return (True, f"Task manually skipped (in {self.config.skip_file})")

            return (False, None)

        except Exception as e:
            # If file unreadable, don't block task
            return (False, None)

    def _check_task_exists(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verify task exists in Backlog.md via BacklogParser.

        Returns:
            (True, None) if task exists
            (False, reason) if task not found
        """
        try:
            task = self.backlog_parser.get_task(task_id)
            if task:
                return (True, None)
            else:
                return (False, f"Task {task_id} not found in Backlog.md")

        except BacklogParserError as e:
            return (False, str(e))
        except Exception as e:
            return (False, f"Error checking task existence: {e}")

    def _check_dependencies(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if all task dependencies are satisfied (status="Done").

        Returns:
            (True, None) if no dependencies or all satisfied
            (False, reason) if blocked by unsatisfied dependencies
        """
        try:
            task = self.backlog_parser.get_task(task_id)

            if not task.dependencies:
                return (True, None)

            # Check each dependency
            blocked_by = []
            for dep_id in task.dependencies:
                try:
                    dep_task = self.backlog_parser.get_task(dep_id)
                    if dep_task.status != "Done":
                        blocked_by.append(f"{dep_id} ({dep_task.status})")
                except Exception:
                    blocked_by.append(f"{dep_id} (not found)")

            if blocked_by:
                blocked_str = ", ".join(blocked_by)
                return (False, f"Blocked by: {blocked_str}")

            return (True, None)

        except Exception as e:
            return (False, f"Error checking dependencies: {e}")

    def _check_yaml_valid(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verify YAML is valid by checking if BacklogParser.get_task() succeeds.

        Relies on BacklogParser's YAML parsing - if get_task() works, YAML is valid.

        Returns:
            (True, None) if YAML valid
            (False, reason) if YAML error caught
        """
        try:
            # If get_task succeeds, YAML is valid
            task = self.backlog_parser.get_task(task_id)
            if task:
                return (True, None)
            else:
                return (False, "Task file empty or malformed")

        except yaml.YAMLError as e:
            return (False, f"YAML parsing error: {e}")
        except Exception as e:
            return (False, f"Error validating YAML: {e}")

    def _check_retry_allowed(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if task has exceeded retry limit or needs to wait for backoff.

        Returns:
            (True, None) if retry allowed or no prior failures
            (False, reason) if retry limit exceeded or backoff period active
        """
        if task_id not in self._retry_states:
            return (True, None)

        state = self._retry_states[task_id]

        # Check retry limit
        if not state.should_retry():
            return (
                False,
                f"Retry limit exceeded ({state.attempt_count}/{self.config.max_retries} attempts)"
            )

        # Check backoff period
        if not state.can_retry_now():
            wait_sec = state.next_retry_time - time.time()
            return (
                False,
                f"Backoff active (retry in {int(wait_sec)}s, attempt {state.attempt_count + 1})"
            )

        return (True, None)
