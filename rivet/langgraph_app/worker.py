"""
Worker process - Consumes jobs from Redis and runs LangGraph workflows
"""

import logging
import redis
import uuid
from langgraph_app.state import RivetState
from langgraph_app.graphs.kb_ingest import build_kb_ingest_graph
from langgraph_app.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def run_worker():
    """
    Main worker loop - pulls jobs from Redis and runs KB ingestion graph
    """
    logger.info("Starting Rivet worker...")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Postgres DSN: {settings.POSTGRES_DSN}")
    logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")

    # Connect to Redis
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    # Build graph once (reusable)
    graph = build_kb_ingest_graph()

    logger.info("Worker ready. Waiting for jobs...")

    while True:
        try:
            # Blocking pop from Redis queue (waits until job available)
            job_data = r.blpop("kb_ingest_jobs", timeout=settings.WORKER_POLL_INTERVAL)

            if not job_data:
                continue  # Timeout, retry

            _, source_url = job_data

            logger.info(f"Processing job: {source_url}")

            # Create initial state
            state = RivetState(
                job_id=str(uuid.uuid4()),
                source_url=source_url
            )

            # Run graph
            final_state = None
            for step_state in graph.stream(state):
                final_state = step_state

            # Log results
            if final_state:
                if final_state.errors:
                    logger.error(f"Job failed: {source_url}")
                    logger.error(f"Errors: {final_state.errors}")
                else:
                    logger.info(f"Job succeeded: {source_url}")
                    logger.info(f"Indexed {final_state.atoms_indexed} atoms")

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            # Continue processing other jobs


if __name__ == "__main__":
    run_worker()
