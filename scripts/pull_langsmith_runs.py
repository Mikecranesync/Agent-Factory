#!/usr/bin/env python3
"""
LangSmith API Inspector - Pull runs and write to markdown for autonomous debugging.

Usage:
    python scripts/pull_langsmith_runs.py --project rivet-ceo-bot --errors-only --limit 10
    python scripts/pull_langsmith_runs.py --project rivet-ceo-bot --limit 20
    python scripts/pull_langsmith_runs.py --help
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langsmith import Client

# Load environment variables
load_dotenv()


def format_timestamp(dt: Optional[datetime]) -> str:
    """Format datetime for filename (safe for all OS)."""
    if dt is None:
        return "unknown"
    return dt.strftime("%Y%m%d_%H%M%S")


def format_display_timestamp(dt: Optional[datetime]) -> str:
    """Format datetime for display."""
    if dt is None:
        return "Unknown"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate long text for display."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (truncated, {len(text)} total chars)"


def write_run_to_markdown(run, output_dir: Path, verbose: bool = False):
    """Write a single run to a markdown file."""
    # Extract run details
    run_id = str(run.id)
    timestamp = format_timestamp(run.start_time)
    display_timestamp = format_display_timestamp(run.start_time)
    status = run.status or "unknown"
    error = run.error or None

    # Create filename: timestamp_runid.md
    filename = f"{timestamp}_{run_id[:8]}.md"
    filepath = output_dir / filename

    # Write markdown
    with open(filepath, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"# LangSmith Run: {run_id}\n\n")
        f.write(f"**Timestamp:** {display_timestamp}\n")
        f.write(f"**Status:** `{status}`\n")
        f.write(f"**Run Type:** {run.run_type}\n")

        if run.name:
            f.write(f"**Name:** {run.name}\n")

        if error:
            f.write(f"**Error:** YES\n")

        f.write("\n---\n\n")

        # Input
        f.write("## Input\n\n")
        if run.inputs:
            input_str = json.dumps(run.inputs, indent=2, ensure_ascii=False)
            f.write(f"```json\n{truncate_text(input_str, 1000)}\n```\n\n")
        else:
            f.write("*No input data*\n\n")

        # Output
        f.write("## Output\n\n")
        if run.outputs:
            output_str = json.dumps(run.outputs, indent=2, ensure_ascii=False)
            f.write(f"```json\n{truncate_text(output_str, 1000)}\n```\n\n")
        else:
            f.write("*No output data*\n\n")

        # Error (if present)
        if error:
            f.write("## Error\n\n")
            f.write(f"```\n{error}\n```\n\n")

        # Metadata
        f.write("## Metadata\n\n")

        # Calculate duration if start/end times exist
        duration = "N/A"
        if run.start_time and run.end_time:
            duration_seconds = (run.end_time - run.start_time).total_seconds()
            duration = f"{duration_seconds:.2f}s"

        f.write(f"- **Duration:** {duration}\n")
        f.write(f"- **Total Tokens:** {getattr(run, 'total_tokens', 'N/A') or 'N/A'}\n")
        f.write(f"- **Prompt Tokens:** {getattr(run, 'prompt_tokens', 'N/A') or 'N/A'}\n")
        f.write(f"- **Completion Tokens:** {getattr(run, 'completion_tokens', 'N/A') or 'N/A'}\n")

        if hasattr(run, 'tags') and run.tags:
            f.write(f"- **Tags:** {', '.join(run.tags)}\n")

        f.write("\n---\n\n")

        # Footer
        f.write(f"*Full Run ID: `{run_id}`*\n")
        f.write(f"*View in LangSmith: https://smith.langchain.com/o/.../projects/p/.../r/{run_id}*\n")

    if verbose:
        print(f"[OK] Wrote {filepath.name}")

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Pull LangSmith runs and write to markdown files for debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pull last 10 errors from production
  python scripts/pull_langsmith_runs.py --project rivet-ceo-bot --errors-only --limit 10

  # Pull last 20 runs (all statuses)
  python scripts/pull_langsmith_runs.py --project rivet-ceo-bot --limit 20

  # Quiet mode
  python scripts/pull_langsmith_runs.py --project rivet-ceo-bot --errors-only --quiet
        """
    )

    parser.add_argument(
        "--project",
        type=str,
        default="rivet-ceo-bot",
        help="LangSmith project name (default: rivet-ceo-bot)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of runs to fetch (default: 20)"
    )

    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Only fetch runs with errors"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (only show summary)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="evals/langsmith/runs",
        help="Output directory for markdown files (default: evals/langsmith/runs)"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize LangSmith client (uses LANGSMITH_API_KEY from env)
    try:
        client = Client()
    except Exception as e:
        print(f"[ERROR] Failed to initialize LangSmith client: {e}")
        print("        Make sure LANGSMITH_API_KEY is set in .env")
        return 1

    # Fetch runs
    if not args.quiet:
        print(f"[*] Fetching runs from project '{args.project}'...")
        if args.errors_only:
            print(f"    Filter: errors only")
        print(f"    Limit: {args.limit}")
        print()

    try:
        # Fetch all runs (filter in Python for simplicity)
        all_runs = list(client.list_runs(
            project_name=args.project,
            is_root=True,  # Only parent runs
            limit=args.limit * 2  # Fetch more, filter later
        ))

        # Filter by errors if requested
        if args.errors_only:
            runs = [r for r in all_runs if r.error][:args.limit]
        else:
            runs = all_runs[:args.limit]

        if not runs:
            print("[i] No runs found matching criteria")
            return 0

        if not args.quiet:
            print(f"[OK] Found {len(runs)} runs\n")

        # Write each run to markdown
        error_count = 0
        success_count = 0

        for run in runs:
            filepath = write_run_to_markdown(run, output_dir, verbose=not args.quiet)

            if run.error:
                error_count += 1
            else:
                success_count += 1

        # Summary
        print()
        print("=" * 60)
        print(f"[SUMMARY]")
        print(f"  Total runs processed: {len(runs)}")
        print(f"  Errors: {error_count}")
        print(f"  Success: {success_count}")
        print(f"  Output directory: {output_dir.absolute()}")
        print("=" * 60)
        print()
        print("[NEXT STEPS]")
        print(f"  1. Read the files: ls {output_dir}")
        print(f"  2. Hand to Claude: 'Read {output_dir}/*.md and fix the bugs'")

        return 0

    except Exception as e:
        print(f"[ERROR] Failed to fetch runs: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
