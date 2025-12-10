#!/usr/bin/env python3
"""
Agent Factory Orchestrator - 24/7 Automation Loop

Based on Complete GitHub Strategy:
- GitHub as single source of truth (git pull every cycle)
- Process jobs from webhook queue
- Route tasks to appropriate agents
- Report status via Telegram

This process runs continuously in the background (tmux/systemd/supervisor).

Usage:
    python orchestrator.py                    # Run foreground
    tmux new -s orchestrator "python orchestrator.py"  # Background
    systemctl start orchestrator              # With systemd

"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment first
load_dotenv()

# Now import after path is set
from core.models import AgentJob, AgentStatus, AgentMessage
from agent_factory.memory.storage import SupabaseMemoryStorage

# ============================================================================
# Configuration
# ============================================================================

# Orchestrator settings
TICK_INTERVAL_SECONDS = 60  # How often to check for work
GIT_SYNC_ENABLED = True  # Whether to git pull each cycle
MAX_CONCURRENT_JOBS = 3  # How many jobs to process simultaneously
HEARTBEAT_INTERVAL_SECONDS = 300  # How often to send heartbeat (5 min)

# Logging
LOG_LEVEL = os.getenv("ORCHESTRATOR_LOG_LEVEL", "INFO")
LOG_FILE = project_root / "logs" / "orchestrator.log"

# Ensure logs directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("orchestrator")


# ============================================================================
# Agent Registry
# ============================================================================

# Maps job types to agent classes/modules
# As agents are implemented, add them here
AGENT_REGISTRY: Dict[str, str] = {
    # Week 2 agents
    "research_web": "agents.research.research_agent.ResearchAgent",
    "build_atom": "agents.research.atom_builder_agent.AtomBuilderAgent",
    "write_script": "agents.content.scriptwriter_agent.ScriptwriterAgent",

    # Week 3 agents
    "generate_voice": "agents.media.voice_production_agent.VoiceProductionAgent",
    "assemble_video": "agents.media.video_assembly_agent.VideoAssemblyAgent",
    "generate_thumbnail": "agents.content.thumbnail_agent.ThumbnailAgent",
    "upload_youtube": "agents.media.youtube_uploader_agent.YouTubeUploaderAgent",

    # Week 4 agents
    "optimize_seo": "agents.content.seo_agent.SEOAgent",
    "schedule_publish": "agents.media.publishing_strategy_agent.PublishingStrategyAgent",

    # Week 5 agents
    "plan_curriculum": "agents.content.master_curriculum_agent.MasterCurriculumAgent",
    "plan_content": "agents.content.content_strategy_agent.ContentStrategyAgent",
    "organize_atoms": "agents.research.atom_librarian_agent.AtomLibrarianAgent",

    # Week 6 agents
    "analyze_metrics": "agents.engagement.analytics_agent.AnalyticsAgent",
    "respond_comments": "agents.engagement.community_agent.CommunityAgent",
    "amplify_social": "agents.engagement.social_amplifier_agent.SocialAmplifierAgent",

    # Week 7 agents
    "validate_quality": "agents.research.quality_checker_agent.QualityCheckerAgent",
    "manage_strategy": "agents.executive.ai_ceo_agent.AICEOAgent",
    "manage_tasks": "agents.executive.ai_chief_of_staff_agent.AIChiefOfStaffAgent",

    # Compound workflows
    "sync_and_generate_content": "orchestrator_workflows.video_production_pipeline",
    "full_video_pipeline": "orchestrator_workflows.video_production_pipeline",
}


# ============================================================================
# Orchestrator Class
# ============================================================================

class Orchestrator:
    """
    24/7 automation loop for Agent Factory.

    Responsibilities:
    - Sync code from GitHub (git pull)
    - Fetch pending jobs from Supabase
    - Route jobs to appropriate agents
    - Monitor agent health
    - Report status
    """

    def __init__(self):
        """Initialize orchestrator with Supabase connection"""
        self.storage = SupabaseMemoryStorage()
        self.running = False
        self.last_heartbeat = datetime.now()
        self.last_git_sync = datetime.now()

        # Register orchestrator status
        self._register_status()

        logger.info("Orchestrator initialized")

    def _register_status(self):
        """Register orchestrator in agent_status table"""
        try:
            # Create orchestrator status record
            status_data = {
                "agent_name": "orchestrator",
                "status": "idle",
                "last_heartbeat": datetime.now().isoformat(),
                "tasks_completed_today": 0,
                "tasks_failed_today": 0
            }

            # Insert or update (upsert)
            self.storage.client.table("agent_status").upsert(status_data).execute()

            logger.info("Orchestrator status registered")

        except Exception as e:
            logger.error(f"Failed to register orchestrator status: {e}")

    def sync_from_github(self) -> bool:
        """
        Sync repository from GitHub (git pull).

        Returns:
            bool: True if sync succeeded, False otherwise
        """
        if not GIT_SYNC_ENABLED:
            return True

        try:
            logger.info("Syncing from GitHub...")

            # Change to project root
            os.chdir(project_root)

            # Run git pull
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Git sync successful: {result.stdout.strip()}")
                self.last_git_sync = datetime.now()
                return True
            else:
                logger.warning(f"Git sync failed: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Git sync timed out after 30 seconds")
            return False
        except Exception as e:
            logger.error(f"Git sync error: {e}")
            return False

    def fetch_pending_jobs(self) -> List[Dict[str, Any]]:
        """
        Fetch pending jobs from Supabase.

        Returns:
            List of job records sorted by priority
        """
        try:
            response = self.storage.client.table("agent_jobs") \\
                .select("*") \\
                .eq("status", "pending") \\
                .order("priority", desc=False) \\
                .order("created_at", desc=False) \\
                .limit(MAX_CONCURRENT_JOBS) \\
                .execute()

            jobs = response.data
            logger.info(f"Fetched {len(jobs)} pending jobs")
            return jobs

        except Exception as e:
            logger.error(f"Failed to fetch jobs: {e}")
            return []

    def route_job_to_agent(self, job: Dict[str, Any]) -> bool:
        """
        Route a job to the appropriate agent.

        Args:
            job: Job record from agent_jobs table

        Returns:
            bool: True if job was successfully routed
        """
        job_id = job["id"]
        job_type = job["job_type"]
        payload = job["payload"]

        logger.info(f"Routing job {job_id} (type: {job_type})")

        # Look up agent class
        agent_class_path = AGENT_REGISTRY.get(job_type)

        if not agent_class_path:
            logger.error(f"No agent registered for job type: {job_type}")
            self._mark_job_failed(job_id, f"No agent for job type: {job_type}")
            return False

        # Update job status to assigned
        self._update_job_status(job_id, "assigned", agent_class_path.split(".")[-1])

        # TODO: Implement actual agent execution
        # For now, just log and mark as completed (skeleton)
        logger.info(f"Would execute {agent_class_path} with payload: {payload}")

        # Simulate work
        time.sleep(1)

        # Mark completed (temporary until agents implemented)
        self._update_job_status(job_id, "completed")

        return True

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        assigned_agent: Optional[str] = None
    ):
        """Update job status in database"""
        try:
            update_data: Dict[str, Any] = {"status": status}

            if status == "assigned" and assigned_agent:
                update_data["assigned_agent"] = assigned_agent
            elif status == "running":
                update_data["started_at"] = datetime.now().isoformat()
            elif status in ("completed", "failed"):
                update_data["completed_at"] = datetime.now().isoformat()

            self.storage.client.table("agent_jobs") \\
                .update(update_data) \\
                .eq("id", job_id) \\
                .execute()

            logger.debug(f"Updated job {job_id} status to {status}")

        except Exception as e:
            logger.error(f"Failed to update job status: {e}")

    def _mark_job_failed(self, job_id: str, error_message: str):
        """Mark job as failed with error message"""
        try:
            self.storage.client.table("agent_jobs") \\
                .update({
                    "status": "failed",
                    "error_message": error_message,
                    "completed_at": datetime.now().isoformat()
                }) \\
                .eq("id", job_id) \\
                .execute()

            logger.error(f"Job {job_id} failed: {error_message}")

        except Exception as e:
            logger.error(f"Failed to mark job as failed: {e}")

    def send_heartbeat(self):
        """Send heartbeat to agent_status table"""
        try:
            self.storage.client.table("agent_status") \\
                .update({
                    "last_heartbeat": datetime.now().isoformat(),
                    "status": "running" if self.running else "idle"
                }) \\
                .eq("agent_name", "orchestrator") \\
                .execute()

            self.last_heartbeat = datetime.now()
            logger.debug("Heartbeat sent")

        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def run(self):
        """
        Main orchestrator loop.

        Runs continuously until interrupted (Ctrl+C).
        """
        self.running = True
        logger.info("=" * 70)
        logger.info("Agent Factory Orchestrator Started")
        logger.info("=" * 70)
        logger.info(f"Tick interval: {TICK_INTERVAL_SECONDS}s")
        logger.info(f"Git sync: {'enabled' if GIT_SYNC_ENABLED else 'disabled'}")
        logger.info(f"Max concurrent jobs: {MAX_CONCURRENT_JOBS}")
        logger.info("=" * 70)

        try:
            cycle_count = 0

            while self.running:
                cycle_count += 1
                cycle_start = time.time()

                logger.info(f"--- Cycle {cycle_count} ---")

                # 1. Sync from GitHub (every cycle)
                if GIT_SYNC_ENABLED:
                    self.sync_from_github()

                # 2. Fetch pending jobs
                jobs = self.fetch_pending_jobs()

                # 3. Process jobs
                if jobs:
                    for job in jobs:
                        self.route_job_to_agent(job)
                else:
                    logger.debug("No pending jobs")

                # 4. Send heartbeat (every 5 minutes)
                seconds_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
                if seconds_since_heartbeat >= HEARTBEAT_INTERVAL_SECONDS:
                    self.send_heartbeat()

                # 5. Sleep until next cycle
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, TICK_INTERVAL_SECONDS - cycle_duration)

                if sleep_time > 0:
                    logger.debug(f"Cycle took {cycle_duration:.2f}s, sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Cycle took {cycle_duration:.2f}s, longer than interval!")

        except KeyboardInterrupt:
            logger.info("Shutting down gracefully (Ctrl+C received)...")
        except Exception as e:
            logger.error(f"Orchestrator crashed: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown - update status, close connections"""
        self.running = False

        try:
            # Update status to stopped
            self.storage.client.table("agent_status") \\
                .update({
                    "status": "stopped",
                    "last_heartbeat": datetime.now().isoformat()
                }) \\
                .eq("agent_name", "orchestrator") \\
                .execute()

            logger.info("Orchestrator stopped")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point"""
    # Check environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        logger.error("Copy .env.example to .env and configure your Supabase credentials")
        sys.exit(1)

    # Create and run orchestrator
    orchestrator = Orchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
