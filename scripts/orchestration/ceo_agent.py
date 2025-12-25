#!/usr/bin/env python3
"""CEO Agent Orchestrator

Master orchestrator for autonomous agent ecosystem.

Workflow:
    1. Read backlog tasks (status: To Do, priority: high/medium)
    2. For each task: check if atoms exist (data/atoms-{task-id}.json)
    3. Judge atoms (quality + product discovery)
    4. Extract fastest monetization pick (confidence >= 4)
    5. Generate product spec (docs/products/{slug}.md)
    6. Create BUILD task (backlog/tasks/task-build-{slug}.md)
    7. Send Telegram notification
    8. Mark original task as Done

Usage:
    # Run once
    poetry run python scripts/orchestration/ceo_agent.py --once

    # Run continuous loop
    poetry run python scripts/orchestration/ceo_agent.py --loop
"""

import json
import logging
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from agent_factory.judges import GeminiJudge, JudgmentResult
from agent_factory.generators import ProductSpecGenerator
from agent_factory.scaffold.backlog_parser import BacklogParser, TaskSpec

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CEOAgentOrchestrator:
    """Master orchestrator for autonomous agent ecosystem."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize CEO Agent orchestrator.

        Args:
            config_path: Path to config YAML (default: config/ceo_agent.yml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "ceo_agent.yml"

        self.config = self._load_config(config_path)
        self.backlog_parser = BacklogParser()
        self.judge = GeminiJudge(model=self.config.get("judge_model", "gemini-2.0-flash"))
        self.spec_generator = ProductSpecGenerator()

        # Optional Telegram integration (graceful fallback if not available)
        self.telegram_enabled = self.config.get("telegram_enabled", False)
        self.telegram = None
        if self.telegram_enabled:
            try:
                from scripts.autonomous.telegram_notifier import TelegramNotifier
                self.telegram = TelegramNotifier()
                logger.info("Telegram notifications enabled")
            except Exception as e:
                logger.warning(f"Telegram not available: {e}")
                self.telegram_enabled = False

        logger.info("CEO Agent Orchestrator initialized")
        logger.info(f"Judge model: {self.config.get('judge_model')}")
        logger.info(f"Min product confidence: {self.config.get('min_product_confidence')}")

    def _load_config(self, path: Path) -> Dict:
        """Load configuration from YAML file.

        Args:
            path: Path to config file

        Returns:
            Config dict

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return self._default_config()

        with open(path, encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get("ceo_agent", {})

    def _default_config(self) -> Dict:
        """Return default configuration.

        Returns:
            Default config dict
        """
        return {
            "loop_type": "continuous",
            "loop_interval_seconds": 300,
            "judge_model": "gemini-2.0-flash",
            "task_priority_filter": ["high", "medium"],
            "telegram_enabled": False,
            "log_file": "logs/ceo-agent.log",
            "backlog_path": "backlog/tasks",
            "atoms_path": "data",
            "products_path": "docs/products",
            "max_tasks_per_run": 5,
            "min_product_confidence": 4
        }

    def run_once(self) -> int:
        """Run one iteration of the CEO loop.

        Returns:
            Number of tasks processed
        """
        logger.info("=" * 70)
        logger.info("CEO AGENT - RUN ONCE")
        logger.info("=" * 70)

        tasks_processed = 0

        try:
            # 1. Read To Do tasks
            logger.info("Reading backlog tasks...")
            tasks = self._get_tasks_to_process()

            if not tasks:
                logger.info("No tasks to process")
                return 0

            logger.info(f"Found {len(tasks)} task(s) to process")

            # 2. Process each task
            max_tasks = self.config.get("max_tasks_per_run", 5)
            for task in tasks[:max_tasks]:
                try:
                    if self._process_task(task):
                        tasks_processed += 1
                except Exception as e:
                    logger.error(f"Error processing task {task.task_id}: {e}", exc_info=True)
                    continue

            logger.info(f"Processed {tasks_processed} task(s)")
            return tasks_processed

        except Exception as e:
            logger.error(f"CEO Agent run failed: {e}", exc_info=True)
            return 0

    def _get_tasks_to_process(self) -> List[TaskSpec]:
        """Get tasks that are ready to process.

        Returns:
            List of TaskSpec objects
        """
        try:
            # Get To Do tasks with high/medium priority
            priority_filter = self.config.get("task_priority_filter", ["high", "medium"])
            tasks = self.backlog_parser.list_tasks(
                status="To Do",
                priority=priority_filter
            )

            # Filter to tasks that have atoms files
            atoms_path = Path(self.config.get("atoms_path", "data"))
            tasks_with_atoms = []

            for task in tasks:
                atoms_file = atoms_path / f"atoms-{task.task_id}.json"
                if atoms_file.exists():
                    tasks_with_atoms.append(task)
                    logger.debug(f"Task {task.task_id} has atoms file")
                else:
                    logger.debug(f"Task {task.task_id} has no atoms file, skipping")

            return tasks_with_atoms

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    def _process_task(self, task: TaskSpec) -> bool:
        """Process a single task through the CEO workflow.

        Args:
            task: Task to process

        Returns:
            True if processed successfully, False otherwise
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESSING TASK: {task.task_id}")
        logger.info(f"Title: {task.title}")
        logger.info(f"{'='*70}")

        try:
            # 1. Load atoms
            atoms_file = Path(self.config.get("atoms_path", "data")) / f"atoms-{task.task_id}.json"
            atoms = self._load_atoms(atoms_file)
            logger.info(f"[1/7] Loaded {len(atoms)} atoms")

            # 2. Judge atoms
            logger.info("[2/7] Judging atoms (calling Gemini)...")
            judgment = self.judge.judge_atoms(
                atoms=atoms,
                task_context=task.description,
                task_id=task.task_id
            )
            logger.info(f"  Median quality: {judgment.median_quality_score:.2f}/5")
            logger.info(f"  Product candidates: {len(judgment.all_product_candidates)}")

            # 3. Save evaluation
            eval_file = atoms_file.with_suffix('').name + "-eval.json"
            eval_path = atoms_file.parent / eval_file
            self._save_evaluation(judgment, eval_path)
            logger.info(f"[3/7] Saved evaluation: {eval_path}")

            # 4. Extract top product (confidence >= min threshold)
            min_confidence = self.config.get("min_product_confidence", 4)
            top_product = judgment.fastest_monetization_pick

            if not top_product:
                logger.info("[4/7] No products found (no fastest_monetization_pick)")
                return False

            if top_product.get("product_confidence", 0) < min_confidence:
                logger.info(
                    f"[4/7] Product confidence too low: "
                    f"{top_product.get('product_confidence')}/{min_confidence}"
                )
                return False

            logger.info(f"[4/7] Top product: {top_product['chosen_product_name']}")
            logger.info(f"  Confidence: {top_product['product_confidence']}/5")
            logger.info(f"  Effort: {top_product['effort_to_productize']}")

            # 5. Generate product spec
            logger.info("[5/7] Generating product spec...")
            spec_path = self.spec_generator.generate_product_spec(
                product=top_product,
                task_id=task.task_id,
                source_repo="agent-factory"
            )
            logger.info(f"  Created: {spec_path}")

            # 6. Create BUILD task
            logger.info("[6/7] Creating BUILD task...")
            build_task_id, build_task_path = self.spec_generator.generate_build_task(
                product=top_product,
                task_id=task.task_id,
                source_repo="agent-factory",
                milestone="Product Discovery"
            )
            logger.info(f"  Created: {build_task_id}")

            # 7. Send Telegram notification
            if self.telegram_enabled and self.telegram:
                logger.info("[7/7] Sending Telegram notification...")
                self._notify_telegram(task, judgment, top_product, build_task_id)
            else:
                logger.info("[7/7] Telegram disabled, skipping notification")

            # Mark original task as complete
            logger.info(f"\nMarking task {task.task_id} as Done")
            self.backlog_parser.update_status(task.task_id, "Done")

            logger.info(f"\n✅ Task {task.task_id} processed successfully")
            return True

        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {e}", exc_info=True)
            return False

    def _load_atoms(self, path: Path) -> List[Dict]:
        """Load atoms from JSON file.

        Args:
            path: Path to atoms JSON file

        Returns:
            List of atom dicts

        Raises:
            FileNotFoundError: If atoms file doesn't exist
            ValueError: If JSON structure is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Atoms file not found: {path}")

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        # Handle both list and wrapped dict structure
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'atoms' in data:
            return data['atoms']
        else:
            raise ValueError("Invalid JSON structure: expected list or dict with 'atoms' key")

    def _save_evaluation(self, judgment: JudgmentResult, path: Path):
        """Save judgment evaluation to JSON file.

        Args:
            judgment: JudgmentResult to save
            path: Output path
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(judgment.to_dict(), f, indent=2, ensure_ascii=False)

    def _notify_telegram(
        self,
        task: TaskSpec,
        judgment: JudgmentResult,
        product: Dict,
        build_task_id: str
    ):
        """Send Telegram notification about discovered product.

        Args:
            task: Original task
            judgment: Judgment result
            product: Product dict from fastest_monetization_pick
            build_task_id: ID of created BUILD task
        """
        try:
            message = f"""🤖 **CEO Agent Update**

**Task Processed:** {task.task_id}
**Atoms Evaluated:** {judgment.atoms_evaluated}
**Quality Median:** {judgment.median_quality_score:.1f}/5

💡 **Top Product Pick:**
{product['chosen_product_name']} (Confidence: {product['product_confidence']}/5)
Effort: {product['effort_to_productize']}
Target: {product.get('target_market', 'TBD')}

⚙️ **Next Steps:**
"""
            for i, step in enumerate(product.get('next_steps', [])[:3], 1):
                message += f"{i}. {step}\n"

            message += f"\n✅ **New BUILD task created:** {build_task_id}"

            self.telegram.send_message(message)

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    def run_loop(self):
        """Run continuous loop with interval from config."""
        loop_interval = self.config.get("loop_interval_seconds", 300)

        logger.info("=" * 70)
        logger.info("CEO AGENT - CONTINUOUS LOOP MODE")
        logger.info("=" * 70)
        logger.info(f"Loop interval: {loop_interval} seconds")
        logger.info("Press Ctrl+C to stop\n")

        try:
            while True:
                tasks_processed = self.run_once()

                if tasks_processed > 0:
                    logger.info(f"\n✅ Run complete: {tasks_processed} task(s) processed")
                else:
                    logger.info("\n⏸️  Run complete: No tasks processed")

                logger.info(f"\nSleeping for {loop_interval} seconds...")
                time.sleep(loop_interval)

        except KeyboardInterrupt:
            logger.info("\n\n🛑 CEO Agent stopped by user")
        except Exception as e:
            logger.error(f"\n\n❌ CEO Agent crashed: {e}", exc_info=True)


def main():
    """Main entry point for CEO Agent orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(description="CEO Agent Orchestrator")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default: continuous loop)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config YAML (default: config/ceo_agent.yml)"
    )
    args = parser.parse_args()

    # Create orchestrator
    config_path = Path(args.config) if args.config else None
    orchestrator = CEOAgentOrchestrator(config_path=config_path)

    # Run
    if args.once:
        tasks_processed = orchestrator.run_once()
        return 0 if tasks_processed >= 0 else 1
    else:
        orchestrator.run_loop()
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
