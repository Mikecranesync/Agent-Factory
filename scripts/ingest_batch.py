#!/usr/bin/env python3
"""
Batch Knowledge Base Ingestion CLI

Usage:
    poetry run python scripts/ingest_batch.py --source <url>
    poetry run python scripts/ingest_batch.py --batch data/sources/urls.txt

Examples:
    # Single source
    poetry run python scripts/ingest_batch.py --source https://example.com/plc-basics.pdf

    # Batch from file (one URL per line)
    poetry run python scripts/ingest_batch.py --batch data/sources/industrial_pdfs.txt

    # With parallel processing (10 workers)
    poetry run python scripts/ingest_batch.py --batch data/sources/urls.txt --parallel 10
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import List
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.workflows.ingestion_chain import ingest_source

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("data/ingestion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Batch Knowledge Base Ingestion")

    parser.add_argument("--source", type=str, help="Single source URL to ingest")
    parser.add_argument("--batch", type=str, help="File with URLs (one per line)")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel workers (default: 1)")

    args = parser.parse_args()

    if args.source:
        # Single source ingestion
        logger.info(f"Ingesting single source: {args.source}")
        result = ingest_source(args.source)

        print("\n" + "="*80)
        print("INGESTION RESULTS")
        print("="*80)
        print(f"Source: {args.source}")
        print(f"Success: {result['success']}")
        print(f"Atoms Created: {result['atoms_created']}")
        print(f"Atoms Failed: {result['atoms_failed']}")
        if result['errors']:
            print(f"Errors: {', '.join(result['errors'])}")
        print("="*80)

    elif args.batch:
        # Batch ingestion from file
        urls_file = Path(args.batch)

        if not urls_file.exists():
            logger.error(f"File not found: {urls_file}")
            return

        # Read URLs
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        logger.info(f"Loaded {len(urls)} URLs from {urls_file}")

        # Ingest (sequential for now)
        # TODO: Implement parallel processing with asyncio.gather()
        total_created = 0
        total_failed = 0
        total_errors = 0

        for i, url in enumerate(urls, 1):
            logger.info(f"Processing {i}/{len(urls)}: {url}")

            try:
                result = ingest_source(url)

                total_created += result['atoms_created']
                total_failed += result['atoms_failed']

                if not result['success']:
                    total_errors += 1

            except Exception as e:
                logger.error(f"Ingestion failed for {url}: {e}")
                total_errors += 1

        # Final summary
        print("\n" + "="*80)
        print("BATCH INGESTION SUMMARY")
        print("="*80)
        print(f"Total Sources: {len(urls)}")
        print(f"Total Atoms Created: {total_created}")
        print(f"Total Atoms Failed: {total_failed}")
        print(f"Total Errors: {total_errors}")
        print(f"Success Rate: {(len(urls) - total_errors) / len(urls) * 100:.1f}%")
        print("="*80)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
