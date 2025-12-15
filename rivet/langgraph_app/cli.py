"""
CLI - Command-line interface for testing and debugging

Run individual jobs without Redis queue.
"""

import uuid
import logging
import argparse
from langgraph_app.state import RivetState
from langgraph_app.graphs.kb_ingest import build_kb_ingest_graph
from langgraph_app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_job(source_url: str) -> None:
    """
    Run single ingestion job

    Args:
        source_url: URL of document to ingest
    """
    logger.info(f"Running job for: {source_url}")

    # Build graph
    graph = build_kb_ingest_graph()

    # Create state
    job_id = str(uuid.uuid4())
    state = RivetState(
        job_id=job_id,
        source_url=source_url,
        workflow="kb_ingest"
    )

    # Execute
    logger.info(f"[{job_id}] Starting ingestion...")

    try:
        final_state = None

        for step_state in graph.stream(state.dict()):
            final_state = step_state

            # Print progress
            if "logs" in step_state:
                for log in step_state["logs"]:
                    logger.info(f"[{job_id}] {log}")

        # Print results
        if final_state:
            errors = final_state.get("errors", [])
            atoms = final_state.get("atoms", [])

            print("\n" + "="*80)
            print("JOB RESULTS")
            print("="*80)
            print(f"Job ID: {job_id}")
            print(f"Source: {source_url}")
            print(f"Atoms extracted: {len(atoms)}")
            print(f"Errors: {len(errors)}")

            if errors:
                print("\nERRORS:")
                for error in errors:
                    print(f"  - {error}")

            if atoms:
                print(f"\nFIRST ATOM SAMPLE:")
                first_atom = atoms[0]
                print(f"  Type: {first_atom.get('atom_type')}")
                print(f"  Title: {first_atom.get('title')}")
                print(f"  Summary: {first_atom.get('summary')}")

            print("="*80)

    except Exception as e:
        logger.error(f"[{job_id}] Job failed: {e}", exc_info=True)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Rivet KB Ingestion CLI")
    parser.add_argument(
        "url",
        help="URL of document to ingest"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_job(args.url)


if __name__ == "__main__":
    main()
