#!/usr/bin/env python3
"""
MasterOrchestratorAgent - 24/7 Autonomous Video Production System

This is the "CEO" agent that coordinates all other agents on schedules.
Runs continuously, managing the complete pipeline from topic selection
to YouTube publishing with committee oversight.

Architecture:
- Runs as background daemon (24/7 uptime)
- Schedules agent execution (cron-style)
- Manages task queues and dependencies
- Handles failures and retries
- Monitors system health
- Logs all decisions and outcomes

Agent Schedule:
- ContentCuratorAgent: Daily at 00:00 UTC (topic selection)
- ScriptwriterAgent: Every 4 hours (script generation)
- InstructionalDesignerAgent: Immediately after ScriptwriterAgent
- VoiceProductionAgent: After script approval
- VideoAssemblyAgent: After voice generation
- Quality Committees: Before publishing
- YouTubeUploaderAgent: Daily at 12:00 UTC (batch upload)
- AnalyticsAgent: Every 6 hours (performance monitoring)
- TrendScoutAgent: Weekly on Sunday (style guide updates)

Production Target: 3 videos/day (90 videos/month)

Created: Dec 2025
Part of: PLC Tutor autonomous production system
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/logs/master_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1  # System health, urgent fixes
    HIGH = 2      # Daily content production
    MEDIUM = 3    # Analytics, optimization
    LOW = 4       # Style updates, research


@dataclass
class Task:
    """Represents a scheduled task"""
    task_id: str
    agent_name: str
    action: str
    priority: TaskPriority
    schedule: str  # Cron-style: "0 */4 * * *" = every 4 hours
    dependencies: List[str]  # Task IDs that must complete first
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 600
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class MasterOrchestratorAgent:
    """
    Master orchestrator for 24/7 autonomous video production.

    Coordinates all agents, manages schedules, handles failures,
    and ensures continuous content production.

    Example:
        >>> orchestrator = MasterOrchestratorAgent()
        >>> await orchestrator.run_forever()
    """

    def __init__(self, project_root: Path = None):
        """
        Initialize MasterOrchestratorAgent.

        Args:
            project_root: Path to project root (defaults to auto-detect)
        """
        self.agent_name = "master_orchestrator_agent"
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Create necessary directories
        (self.project_root / "data" / "logs").mkdir(parents=True, exist_ok=True)
        (self.project_root / "data" / "tasks").mkdir(parents=True, exist_ok=True)
        (self.project_root / "data" / "schedules").mkdir(parents=True, exist_ok=True)

        # Task queue
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []

        # Production metrics
        self.metrics = {
            "videos_produced_today": 0,
            "videos_produced_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "uptime_hours": 0,
            "last_health_check": None
        }

        # Running state
        self.is_running = False
        self.start_time = None

        # Load default schedule
        self.schedule = self._create_default_schedule()

    def _create_default_schedule(self) -> List[Task]:
        """
        Create default 24/7 production schedule.

        Returns:
            List of scheduled tasks
        """
        schedule = []

        # Daily tasks
        schedule.append(Task(
            task_id="content_curation_daily",
            agent_name="ContentCuratorAgent",
            action="get_next_topic",
            priority=TaskPriority.HIGH,
            schedule="0 0 * * *",  # Daily at midnight UTC
            dependencies=[]
        ))

        # Every 4 hours - Script generation
        schedule.append(Task(
            task_id="script_generation_4h",
            agent_name="ScriptwriterAgent",
            action="generate_script",
            priority=TaskPriority.HIGH,
            schedule="0 */4 * * *",  # Every 4 hours
            dependencies=["content_curation_daily"]
        ))

        # Immediately after script - Instructional design
        schedule.append(Task(
            task_id="instructional_design",
            agent_name="InstructionalDesignerAgent",
            action="improve_script",
            priority=TaskPriority.HIGH,
            schedule="immediate",  # Runs after script_generation_4h
            dependencies=["script_generation_4h"]
        ))

        # After design - Voice generation
        schedule.append(Task(
            task_id="voice_production",
            agent_name="VoiceProductionAgent",
            action="generate_audio",
            priority=TaskPriority.HIGH,
            schedule="immediate",
            dependencies=["instructional_design"]
        ))

        # After voice - Video assembly
        schedule.append(Task(
            task_id="video_assembly",
            agent_name="VideoAssemblyAgent",
            action="create_video",
            priority=TaskPriority.HIGH,
            schedule="immediate",
            dependencies=["voice_production"]
        ))

        # After assembly - Quality review
        schedule.append(Task(
            task_id="quality_review",
            agent_name="VideoQualityReviewerAgent",
            action="review_video",
            priority=TaskPriority.HIGH,
            schedule="immediate",
            dependencies=["video_assembly"]
        ))

        # After review - Committee vote
        schedule.append(Task(
            task_id="quality_committee_vote",
            agent_name="QualityReviewCommittee",
            action="vote",
            priority=TaskPriority.HIGH,
            schedule="immediate",
            dependencies=["quality_review"]
        ))

        # After approval - A/B variant generation
        schedule.append(Task(
            task_id="ab_test_variants",
            agent_name="ABTestOrchestratorAgent",
            action="create_test",
            priority=TaskPriority.MEDIUM,
            schedule="immediate",
            dependencies=["quality_committee_vote"]
        ))

        # Daily upload batch
        schedule.append(Task(
            task_id="youtube_upload_daily",
            agent_name="YouTubeUploaderAgent",
            action="upload_approved_videos",
            priority=TaskPriority.HIGH,
            schedule="0 12 * * *",  # Daily at noon UTC
            dependencies=["ab_test_variants"]
        ))

        # Every 6 hours - Analytics monitoring
        schedule.append(Task(
            task_id="analytics_monitoring_6h",
            agent_name="AnalyticsCommittee",
            action="review_metrics",
            priority=TaskPriority.MEDIUM,
            schedule="0 */6 * * *",  # Every 6 hours
            dependencies=[]
        ))

        # Weekly - Style guide updates
        schedule.append(Task(
            task_id="style_guide_update_weekly",
            agent_name="TrendScoutAgent",
            action="update_style_guide",
            priority=TaskPriority.LOW,
            schedule="0 0 * * 0",  # Sunday at midnight
            dependencies=[]
        ))

        # Weekly - Gap analysis
        schedule.append(Task(
            task_id="gap_analysis_weekly",
            agent_name="ContentCuratorAgent",
            action="analyze_knowledge_gaps",
            priority=TaskPriority.MEDIUM,
            schedule="0 6 * * 0",  # Sunday at 6 AM
            dependencies=[]
        ))

        return schedule

    async def run_forever(self):
        """
        Run orchestrator in 24/7 daemon mode.

        Main loop that:
        1. Checks schedule for due tasks
        2. Executes tasks based on priority and dependencies
        3. Monitors health and metrics
        4. Handles failures and retries
        5. Logs all activities
        """
        self.is_running = True
        self.start_time = datetime.utcnow()

        logger.info("=" * 70)
        logger.info("MASTER ORCHESTRATOR - STARTING 24/7 OPERATION")
        logger.info("=" * 70)
        logger.info(f"Start time: {self.start_time.isoformat()}")
        logger.info(f"Scheduled tasks: {len(self.schedule)}")
        logger.info(f"Production target: 3 videos/day (90/month)")
        logger.info("=" * 70)

        # Initialize task queue
        self._populate_task_queue()

        iteration = 0
        while self.is_running:
            iteration += 1

            try:
                # Health check every hour
                if iteration % 60 == 0:  # Every 60 minutes
                    await self._perform_health_check()

                # Check for due tasks
                due_tasks = self._get_due_tasks()

                if due_tasks:
                    logger.info(f"[Iteration {iteration}] {len(due_tasks)} tasks due")

                    # Execute tasks by priority
                    for task in sorted(due_tasks, key=lambda t: t.priority.value):
                        if self._can_execute_task(task):
                            await self._execute_task(task)
                        else:
                            logger.debug(f"Task {task.task_id} blocked by dependencies")

                # Update metrics
                self._update_metrics()

                # Save state every 10 minutes
                if iteration % 10 == 0:
                    self._save_state()

                # Sleep for 1 minute
                await asyncio.sleep(60)

            except KeyboardInterrupt:
                logger.info("\n\nReceived shutdown signal")
                break

            except Exception as e:
                logger.error(f"Orchestrator error: {e}", exc_info=True)
                # Don't crash - log and continue
                await asyncio.sleep(60)

        # Cleanup
        await self._shutdown()

    def _populate_task_queue(self):
        """Populate task queue from schedule."""
        for task_template in self.schedule:
            # Create task instance
            task = Task(
                task_id=f"{task_template.task_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                agent_name=task_template.agent_name,
                action=task_template.action,
                priority=task_template.priority,
                schedule=task_template.schedule,
                dependencies=task_template.dependencies,
                created_at=datetime.utcnow().isoformat()
            )
            self.task_queue.append(task)

        logger.info(f"Task queue populated: {len(self.task_queue)} tasks")

    def _get_due_tasks(self) -> List[Task]:
        """
        Get tasks that are due for execution.

        Returns:
            List of tasks ready to run
        """
        due_tasks = []
        now = datetime.utcnow()

        for task in self.task_queue:
            if task.status != TaskStatus.PENDING:
                continue

            # Immediate tasks (dependency-based)
            if task.schedule == "immediate":
                if self._dependencies_met(task):
                    due_tasks.append(task)
                continue

            # Cron-style scheduled tasks
            if self._is_schedule_due(task.schedule, now):
                due_tasks.append(task)

        return due_tasks

    def _is_schedule_due(self, schedule: str, now: datetime) -> bool:
        """
        Check if cron-style schedule is due.

        Args:
            schedule: Cron expression (e.g., "0 */4 * * *")
            now: Current datetime

        Returns:
            True if schedule is due
        """
        # Simple cron parser (production would use croniter library)
        parts = schedule.split()
        if len(parts) != 5:
            return False

        minute, hour, day, month, weekday = parts

        # Check minute
        if minute != "*" and now.minute != int(minute):
            return False

        # Check hour (support */N syntax)
        if hour.startswith("*/"):
            interval = int(hour[2:])
            if now.hour % interval != 0:
                return False
        elif hour != "*" and now.hour != int(hour):
            return False

        # Check day
        if day != "*" and now.day != int(day):
            return False

        # Check month
        if month != "*" and now.month != int(month):
            return False

        # Check weekday (0 = Sunday)
        if weekday != "*" and now.weekday() != int(weekday):
            return False

        return True

    def _can_execute_task(self, task: Task) -> bool:
        """
        Check if task can be executed (dependencies met).

        Args:
            task: Task to check

        Returns:
            True if task can run
        """
        return self._dependencies_met(task)

    def _dependencies_met(self, task: Task) -> bool:
        """
        Check if all task dependencies are completed.

        Args:
            task: Task to check

        Returns:
            True if all dependencies completed
        """
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            # Find matching completed task (prefix match for template IDs)
            matching_tasks = [
                t for t in self.completed_tasks
                if t.task_id.startswith(dep_id)
            ]
            if not matching_tasks:
                return False

        return True

    async def _execute_task(self, task: Task):
        """
        Execute a task (run agent action).

        Args:
            task: Task to execute
        """
        logger.info(f"[EXECUTING] {task.task_id} ({task.agent_name}.{task.action})")

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow().isoformat()
        self.active_tasks[task.task_id] = task

        try:
            # Execute agent action
            result = await asyncio.wait_for(
                self._run_agent_action(task.agent_name, task.action),
                timeout=task.timeout_seconds
            )

            # Mark completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            task.result = result

            self.completed_tasks.append(task)
            del self.active_tasks[task.task_id]
            self.task_queue.remove(task)

            logger.info(f"[COMPLETED] {task.task_id}")
            self.metrics["tasks_completed"] += 1

            # Schedule next occurrence if recurring
            if task.schedule != "immediate":
                self._schedule_next_occurrence(task)

        except asyncio.TimeoutError:
            logger.error(f"[TIMEOUT] {task.task_id} exceeded {task.timeout_seconds}s")
            await self._handle_task_failure(task, "Timeout")

        except Exception as e:
            logger.error(f"[FAILED] {task.task_id}: {e}", exc_info=True)
            await self._handle_task_failure(task, str(e))

    async def _run_agent_action(self, agent_name: str, action: str) -> Dict:
        """
        Run agent action (import and execute).

        Args:
            agent_name: Name of agent to run
            action: Method name to call

        Returns:
            Result dictionary
        """
        # Import agent dynamically
        if agent_name == "ContentCuratorAgent":
            from agents.content.content_curator_agent import ContentCuratorAgent
            agent = ContentCuratorAgent()
            if action == "get_next_topic":
                result = agent.get_next_topic()
            elif action == "analyze_knowledge_gaps":
                result = agent.analyze_knowledge_gaps()
            else:
                raise ValueError(f"Unknown action: {action}")

        elif agent_name == "ScriptwriterAgent":
            from agents.content.scriptwriter_agent import ScriptwriterAgent
            agent = ScriptwriterAgent()
            if action == "generate_script":
                # Get topic from ContentCuratorAgent
                curator = ContentCuratorAgent()
                topic_data = curator.get_next_topic()
                if "topic" in topic_data:
                    topic = topic_data["topic"]["title"]
                    atoms = agent.query_atoms(topic, limit=3)
                    result = agent.generate_script(topic, atoms)
                else:
                    result = {"status": "no_topics", "message": "All topics covered"}
            else:
                raise ValueError(f"Unknown action: {action}")

        elif agent_name == "InstructionalDesignerAgent":
            from agents.content.instructional_designer_agent import InstructionalDesignerAgent
            agent = InstructionalDesignerAgent()
            # Get latest script
            scripts_dir = self.project_root / "data" / "scripts"
            latest_script = sorted(scripts_dir.glob("*.txt"))[-1] if scripts_dir.exists() else None
            if latest_script:
                with open(latest_script, 'r', encoding='utf-8') as f:
                    script_text = f.read()
                result = agent.improve_script(script_text)
            else:
                result = {"status": "no_script", "message": "No script to improve"}

        elif agent_name == "VideoQualityReviewerAgent":
            from agents.content.video_quality_reviewer_agent import VideoQualityReviewerAgent
            agent = VideoQualityReviewerAgent()
            # Get latest script
            scripts_dir = self.project_root / "data" / "scripts"
            latest_script = sorted(scripts_dir.glob("*.txt"))[-1] if scripts_dir.exists() else None
            if latest_script:
                with open(latest_script, 'r', encoding='utf-8') as f:
                    script_text = f.read()
                result = agent.review_video(script_text)
            else:
                result = {"status": "no_script", "message": "No script to review"}

        elif agent_name == "TrendScoutAgent":
            from agents.content.trend_scout_agent import TrendScoutAgent
            agent = TrendScoutAgent()
            if action == "update_style_guide":
                guide = agent.generate_style_guide()
                # Save updated guide
                guide_path = self.project_root / "docs" / "CHANNEL_STYLE_GUIDE.md"
                with open(guide_path, 'w', encoding='utf-8') as f:
                    f.write(guide)
                result = {"status": "updated", "path": str(guide_path)}
            else:
                raise ValueError(f"Unknown action: {action}")

        else:
            # Placeholder for agents not yet implemented
            logger.warning(f"Agent {agent_name} not yet implemented - simulating")
            result = {"status": "simulated", "agent": agent_name, "action": action}

        return result

    async def _handle_task_failure(self, task: Task, error: str):
        """
        Handle task failure with retry logic.

        Args:
            task: Failed task
            error: Error message
        """
        task.error = error
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            logger.warning(f"[RETRY] {task.task_id} (attempt {task.retry_count + 1}/{task.max_retries})")
            task.status = TaskStatus.RETRYING
            # Wait before retry (exponential backoff)
            await asyncio.sleep(60 * (2 ** task.retry_count))
            task.status = TaskStatus.PENDING
        else:
            logger.error(f"[FAILED PERMANENTLY] {task.task_id} after {task.max_retries} retries")
            task.status = TaskStatus.FAILED
            self.failed_tasks.append(task)
            self.task_queue.remove(task)
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.metrics["tasks_failed"] += 1

    def _schedule_next_occurrence(self, task: Task):
        """
        Schedule next occurrence of recurring task.

        Args:
            task: Completed task to reschedule
        """
        # Create new task instance for next occurrence
        next_task = Task(
            task_id=f"{task.task_id.rsplit('_', 2)[0]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            agent_name=task.agent_name,
            action=task.action,
            priority=task.priority,
            schedule=task.schedule,
            dependencies=task.dependencies,
            created_at=datetime.utcnow().isoformat()
        )
        self.task_queue.append(next_task)

    async def _perform_health_check(self):
        """Perform system health check."""
        logger.info("[HEALTH CHECK] Checking system status...")

        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "task_queue_size": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "metrics": self.metrics
        }

        logger.info(f"  Queue: {health['task_queue_size']} | "
                   f"Active: {health['active_tasks']} | "
                   f"Completed: {health['completed_tasks']} | "
                   f"Failed: {health['failed_tasks']}")

        self.metrics["last_health_check"] = health["timestamp"]
        self.metrics["uptime_hours"] = health["uptime_hours"]

        # Save health report
        health_path = self.project_root / "data" / "logs" / f"health_{datetime.utcnow().strftime('%Y%m%d')}.json"
        with open(health_path, 'w') as f:
            json.dump(health, f, indent=2)

    def _update_metrics(self):
        """Update production metrics."""
        # Count videos produced today
        videos_dir = self.project_root / "data" / "videos"
        if videos_dir.exists():
            today = datetime.utcnow().date()
            today_videos = [
                v for v in videos_dir.iterdir()
                if v.is_dir() and v.name.startswith("video_")
                and datetime.fromtimestamp(v.stat().st_mtime).date() == today
            ]
            self.metrics["videos_produced_today"] = len(today_videos)
            self.metrics["videos_produced_total"] = len(list(videos_dir.iterdir()))

    def _save_state(self):
        """Save orchestrator state to disk."""
        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "task_queue": [asdict(t) for t in self.task_queue[:10]],  # Last 10
            "active_tasks": {k: asdict(v) for k, v in self.active_tasks.items()},
            "metrics": self.metrics
        }

        state_path = self.project_root / "data" / "tasks" / "orchestrator_state.json"
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)

    async def _shutdown(self):
        """Graceful shutdown."""
        logger.info("=" * 70)
        logger.info("MASTER ORCHESTRATOR - SHUTTING DOWN")
        logger.info("=" * 70)

        # Save final state
        self._save_state()

        # Wait for active tasks to complete (max 5 minutes)
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            await asyncio.sleep(min(300, 60 * len(self.active_tasks)))

        # Summary
        uptime = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        logger.info(f"\nUptime: {uptime:.1f} hours")
        logger.info(f"Tasks completed: {self.metrics['tasks_completed']}")
        logger.info(f"Tasks failed: {self.metrics['tasks_failed']}")
        logger.info(f"Videos produced: {self.metrics['videos_produced_total']}")
        logger.info("\nShutdown complete")


async def main():
    """Run MasterOrchestratorAgent in daemon mode."""
    orchestrator = MasterOrchestratorAgent()
    await orchestrator.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
