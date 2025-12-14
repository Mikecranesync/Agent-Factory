"""
CLI tool - Run single ingestion jobs for debugging
"""

import logging
import uuid
import sys
from langgraph_app.state import RivetState
from langgraph_app.graphs.kb_ingest import build_kb_ingest_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def run_single_job(source_url: str):
    """
    Run KB ingestion for a single URL (for debugging)

    Args:
        source_url: URL to process
    """
    logger.info(f"Running single job: {source_url}")

    # Build graph
    graph = build_kb_ingest_graph()

    # Create initial state
    state = RivetState(
        job_id=str(uuid.uuid4()),
        source_url=source_url
    )

    # Run graph
    final_state = None
    for step_state in graph.stream(state):
        final_state = step_state
        logger.info(f"Step completed. Logs: {step_state.logs}")

    # Print results
    if final_state:
        print("\n" + "=" * 80)
        print("JOB COMPLETE")
        print("=" * 80)
        print(f"Job ID: {final_state.job_id}")
        print(f"Source: {final_state.source_url}")
        print(f"Atoms created: {final_state.atoms_created}")
        print(f"Atoms indexed: {final_state.atoms_indexed}")
        print(f"Errors: {len(final_state.errors)}")

        if final_state.errors:
            print("\nERRORS:")
            for error in final_state.errors:
                print(f"  - {error}")

        print("\nLOGS:")
        for log in final_state.logs:
            print(f"  - {log}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m langgraph_app.cli <source_url>")
        sys.exit(1)

    url = sys.argv[1]
    run_single_job(url)
