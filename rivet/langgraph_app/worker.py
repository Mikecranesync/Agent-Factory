"""
Worker Process - Consumes jobs from Redis and executes ingestion graph

Runs continuously, pulling jobs from Redis queue and processing them through LangGraph.
"""

import uuid
import logging
import time
import redis
from langgraph_app.state import RivetState
from langgraph_app.graphs.kb_ingest import build_kb_ingest_graph
from langgraph_app.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_worker():
    """
    Main worker loop

    Continuously:
    1. Pull job from Redis queue (blocking)
    2. Execute ingestion graph
    3. Log results
    4. Repeat
    """
    logger.info("Worker starting...")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Postgres: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

    # Connect to Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return

    # Build graph
    try:
        graph = build_kb_ingest_graph()
        logger.info("Ingestion graph compiled")
    except Exception as e:
        logger.error(f"Graph compilation failed: {e}")
        return

    logger.info("Worker ready, waiting for jobs...")

    # Main loop
    while True:
        try:
            # Block waiting for job (timeout after 60s to allow logging)
            job_data = r.blpop("kb_ingest_jobs", timeout=60)

            if not job_data:
                # Timeout - just log heartbeat and continue
                logger.debug("Waiting for jobs...")
                continue

            # Extract job payload
            queue_name, payload = job_data
            source_url = payload.decode("utf-8")

            logger.info(f"Processing job: {source_url}")

            # Create initial state
            job_id = str(uuid.uuid4())
            state = RivetState(
                job_id=job_id,
                source_url=source_url,
                workflow="kb_ingest"
            )

            # Execute graph
            start_time = time.time()

            try:
                # Stream through graph
                final_state = None
                for step_state in graph.stream(state.dict()):
                    final_state = step_state
                    logger.debug(f"[{job_id}] Graph step complete")

                duration = time.time() - start_time

                # Log results
                if final_state:
                    errors = final_state.get("errors", [])
                    atoms_count = len(final_state.get("atoms", []))

                    if errors:
                        logger.error(f"[{job_id}] Job completed with errors: {errors}")
                    else:
                        logger.info(f"[{job_id}] Job completed successfully: {atoms_count} atoms indexed")

                    logger.info(f"[{job_id}] Duration: {duration:.2f}s")

                else:
                    logger.warning(f"[{job_id}] Job completed but final state is None")

            except Exception as e:
                logger.error(f"[{job_id}] Graph execution failed: {e}", exc_info=True)

        except KeyboardInterrupt:
            logger.info("Worker shutting down (keyboard interrupt)")
            break

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            time.sleep(5)  # Back off before retrying


if __name__ == "__main__":
    run_worker()
