"""
Check evaluation results against thresholds.

Reads eval results JSON and verifies all blocking evals pass their thresholds.
Exits with code 0 if gate passes, 1 if fails.

Usage:
    python evals/check_results.py <results_file.json>
    python evals/check_results.py evals/eval_results.json
"""

import sys
import json
from pathlib import Path


def check_results(results_file: str) -> bool:
    """
    Check if evaluation gate passes.

    Args:
        results_file: Path to eval results JSON

    Returns:
        True if gate passes, False otherwise
    """
    # Load results
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Results file not found: {results_file}")
        return False
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in results file: {results_file}")
        return False

    summary = results.get('summary', {})
    by_eval = summary.get('by_eval', {})
    gate_passed = summary.get('gate_passed', False)

    # Print header
    print("=" * 70)
    print("EVALUATION GATE CHECK")
    print("=" * 70)
    print()

    # Print each eval
    for eval_name, stats in by_eval.items():
        pass_rate = stats.get('pass_rate', 0.0)
        threshold = stats.get('threshold', 0.0)
        passed = stats.get('passed', False)
        blocking = stats.get('blocking', False)

        status = "[PASS]" if passed else "[FAIL]"
        blocking_flag = " (BLOCKING)" if blocking else ""

        print(f"{status} {eval_name}{blocking_flag}")
        print(f"       Pass rate: {pass_rate * 100:.1f}%")
        print(f"       Threshold: {threshold * 100:.0f}%")

        if not passed and blocking:
            print(f"       ^^^^ GATE BLOCKER ^^^^")

        print()

    # Print summary
    print("=" * 70)
    if gate_passed:
        print("[PASS] GATE PASSED - All blocking evals met thresholds")
    else:
        print("[FAIL] GATE FAILED - One or more blocking evals failed")
    print("=" * 70)
    print()

    # Print failure details
    if not gate_passed:
        print("Failed blocking evals:")
        for eval_name, stats in by_eval.items():
            if stats.get('blocking') and not stats.get('passed'):
                print(f"  - {eval_name}: {stats['pass_rate']*100:.1f}% (need {stats['threshold']*100:.0f}%)")
        print()

    return gate_passed


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_results.py <results_file.json>")
        print("Example: python check_results.py evals/eval_results.json")
        sys.exit(1)

    results_file = sys.argv[1]
    gate_passed = check_results(results_file)

    # Exit with appropriate code
    sys.exit(0 if gate_passed else 1)


if __name__ == "__main__":
    main()
