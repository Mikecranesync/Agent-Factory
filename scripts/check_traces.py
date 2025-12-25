#!/usr/bin/env python3
"""
Check recent LangSmith traces and analyze bot performance.

Usage:
    python scripts/check_traces.py
    python scripts/check_traces.py --limit 5
"""
import argparse
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from langsmith import Client

# Load environment
load_dotenv()

PROJECT = "rivet-ceo-bot"


def analyze_trace(run: Any) -> Dict[str, Any]:
    """
    Analyze a single trace and extract key metrics.

    Args:
        run: LangSmith Run object

    Returns:
        Dict with analysis results
    """
    # Extract input query
    query = "Unknown"
    if run.inputs:
        update = run.inputs.get("update", {})
        message = update.get("message", {})
        query = message.get("text", "Unknown")

    # Calculate duration
    duration = 0.0
    if run.start_time and run.end_time:
        duration = (run.end_time - run.start_time).total_seconds()

    # Check for errors
    has_error = run.error is not None
    error_msg = run.error if has_error else None

    # Extract route info from child runs
    route = "Unknown"
    kb_atoms_found = 0
    tool_calls = []

    # This would require fetching child runs - simplified for now
    # In full implementation, would call client.list_runs(trace_id=run.trace_id)

    return {
        "run_id": str(run.id),
        "timestamp": run.start_time.isoformat() if run.start_time else "Unknown",
        "query": query,
        "duration": round(duration, 2),
        "status": run.status,
        "has_error": has_error,
        "error": error_msg,
        "route": route,
        "kb_atoms": kb_atoms_found,
        "tool_calls": tool_calls
    }


def print_trace_analysis(analyses: List[Dict[str, Any]]):
    """Pretty print trace analysis."""
    print()
    print("=" * 80)
    print("[TRACE ANALYSIS]")
    print("=" * 80)
    print()

    for i, analysis in enumerate(analyses, 1):
        print(f"[{i}] Run: {analysis['run_id'][:8]}")
        print(f"    Timestamp: {analysis['timestamp']}")
        print(f"    Query: {analysis['query'][:60]}...")
        print(f"    Duration: {analysis['duration']}s")
        print(f"    Status: {analysis['status']}")

        if analysis['has_error']:
            print(f"    Error: {analysis['error'][:100]}...")
        else:
            print(f"    Route: {analysis['route']}")
            print(f"    KB Atoms: {analysis['kb_atoms']}")

        print()

    # Summary stats
    total = len(analyses)
    errors = sum(1 for a in analyses if a['has_error'])
    success = total - errors
    avg_duration = sum(a['duration'] for a in analyses) / total if total > 0 else 0

    print("=" * 80)
    print("[SUMMARY]")
    print(f"  Total traces: {total}")
    print(f"  Successful: {success}")
    print(f"  Errors: {errors}")
    print(f"  Avg duration: {avg_duration:.2f}s")
    print("=" * 80)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze recent LangSmith traces for RIVET CEO Bot"
    )

    parser.add_argument(
        "--project",
        type=str,
        default=PROJECT,
        help=f"LangSmith project name (default: {PROJECT})"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent traces to analyze (default: 10)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of pretty print"
    )

    args = parser.parse_args()

    print(f"[*] Fetching {args.limit} recent traces from '{args.project}'...")

    try:
        client = Client()

        # Fetch recent runs
        runs = list(client.list_runs(
            project_name=args.project,
            is_root=True,
            limit=args.limit
        ))

        if not runs:
            print("[i] No traces found")
            return 0

        print(f"[OK] Found {len(runs)} traces")

        # Analyze each trace
        analyses = [analyze_trace(run) for run in runs]

        # Output
        if args.json:
            print(json.dumps(analyses, indent=2))
        else:
            print_trace_analysis(analyses)

        return 0

    except Exception as e:
        print(f"[ERROR] Failed to fetch traces: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
