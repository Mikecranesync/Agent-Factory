#!/usr/bin/env python3
"""
Generate Markdown Evaluation Report

Reads eval results JSON and generates a human-readable markdown report.

Usage:
    python generate_report.py --input evals/sprint_results.json
    python generate_report.py --input evals/ci_results.json --output evals/CI_REPORT.md
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def load_results(input_path: str) -> dict:
    """Load evaluation results from JSON file."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def generate_markdown_report(data: dict) -> str:
    """
    Generate markdown report from eval results.

    Args:
        data: Results dict with 'summary' and 'results' keys

    Returns:
        Markdown formatted report string
    """
    summary = data.get("summary", {})
    results = data.get("results", [])
    timestamp = summary.get("timestamp", datetime.now().isoformat())
    total_cases = summary.get("total_cases", len(results))
    gate_passed = summary.get("gate_passed", False)

    # Build markdown
    lines = []

    # Header
    lines.append("# Phoenix Evaluation Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Cases Evaluated:** {total_cases}")
    lines.append(f"**Gate Status:** {'PASSED' if gate_passed else 'FAILED'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary Table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Evaluation | Pass Rate | Threshold | Status |")
    lines.append("|-----------|-----------|-----------|--------|")

    by_eval = summary.get("by_eval", {})
    for eval_name, stats in by_eval.items():
        pass_rate = stats.get("pass_rate", 0.0)
        threshold = stats.get("threshold", 0.0)
        passed = stats.get("passed", False)
        blocking = stats.get("blocking", False)

        status_icon = "PASS" if passed else "FAIL"
        blocking_label = " (BLOCKING)" if blocking else ""

        lines.append(
            f"| {eval_name}{blocking_label} | "
            f"{pass_rate*100:.1f}% | "
            f"{threshold*100:.0f}% | "
            f"{status_icon} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Safety Compliance Failures
    lines.append("## Safety Compliance Failures")
    lines.append("")

    safety_failures = []
    for result in results:
        safety_eval = result.get("evals", {}).get("safety_compliance", {})
        label = safety_eval.get("label", "")

        if label in ["PARTIAL", "UNSAFE"]:
            safety_failures.append({
                "case_id": result.get("case_id", ""),
                "fault_code": result.get("fault_code", ""),
                "label": label,
                "reason": safety_eval.get("reason", ""),
            })

    if safety_failures:
        lines.append("**CRITICAL:** The following cases have safety compliance issues:")
        lines.append("")
        for fail in safety_failures:
            lines.append(f"- **{fail['case_id']}** ({fail['fault_code']})")
            lines.append(f"  - Label: `{fail['label']}`")
            lines.append(f"  - Reason: {fail['reason']}")
            lines.append("")
    else:
        lines.append("No safety compliance failures")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Technical Accuracy Failures
    lines.append("## Technical Accuracy Failures")
    lines.append("")

    accuracy_failures = []
    for result in results:
        accuracy_eval = result.get("evals", {}).get("technical_accuracy", {})
        label = accuracy_eval.get("label", "")

        if label == "INCORRECT":
            accuracy_failures.append({
                "case_id": result.get("case_id", ""),
                "fault_code": result.get("fault_code", ""),
                "reason": accuracy_eval.get("reason", ""),
            })

    if accuracy_failures:
        lines.append("The following cases have incorrect technical diagnoses:")
        lines.append("")
        for fail in accuracy_failures:
            lines.append(f"- **{fail['case_id']}** ({fail['fault_code']})")
            lines.append(f"  - Reason: {fail['reason']}")
            lines.append("")
    else:
        lines.append("No technical accuracy failures")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Overall Gate Status
    lines.append("## Gate Decision")
    lines.append("")

    if gate_passed:
        lines.append("### GATE PASSED")
        lines.append("")
        lines.append("All blocking thresholds met. Safe to merge.")
    else:
        lines.append("### GATE FAILED")
        lines.append("")
        lines.append("One or more blocking thresholds not met. Do not merge until issues are resolved.")
        lines.append("")

        # List failed blocking evals
        failed_blocking = [
            eval_name
            for eval_name, stats in by_eval.items()
            if stats.get("blocking", False) and not stats.get("passed", False)
        ]

        if failed_blocking:
            lines.append("**Failed Blocking Evaluations:**")
            lines.append("")
            for eval_name in failed_blocking:
                lines.append(f"- {eval_name}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Phoenix Evaluation System on {timestamp}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate markdown evaluation report")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to eval results JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evals/EVAL_REPORT.md",
        help="Output markdown file path (default: evals/EVAL_REPORT.md)",
    )

    args = parser.parse_args()

    # Load results
    print(f"Loading results from {args.input}...")
    data = load_results(args.input)

    # Generate report
    print("Generating markdown report...")
    report_md = generate_markdown_report(data)

    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Report saved to {output_path}")

    # Print to console
    print("\n" + "=" * 70)
    print("EVALUATION REPORT")
    print("=" * 70)
    print(report_md)
    print("=" * 70)


if __name__ == "__main__":
    main()
