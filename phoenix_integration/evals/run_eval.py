#!/usr/bin/env python3
"""
Run Phoenix Evaluations on Golden Dataset

Evaluates your maintenance agents against the golden dataset using
LLM-as-judge methodology.

Usage:
    # Run on first 10 cases (test)
    python run_eval.py --limit 10
    
    # Run full eval
    python run_eval.py
    
    # Dry run (show what would happen)
    python run_eval.py --dry-run

Requires:
    - Phoenix server running (phoenix serve)
    - Golden dataset exported (datasets/golden_dataset.jsonl)
    - OpenAI API key for judge LLM
"""

import os
import json
import argparse
from datetime import datetime
from typing import Optional
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# Import judge templates
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from evals.judges import (
    TECHNICAL_ACCURACY_TEMPLATE,
    SAFETY_COMPLIANCE_TEMPLATE,
    PROCEDURE_COMPLETENESS_TEMPLATE,
    MANUAL_CITATION_TEMPLATE,
    EVAL_CONFIG,
    get_blocking_evals,
)

# Phoenix tracing integration
try:
    # Try to import from phoenix_tracer module
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, parent_dir)
    from phoenix_tracer import init_phoenix, traced, wrap_client

    # Initialize Phoenix (assumes server running on port 6006)
    init_phoenix(project_name="rivet_evals", launch_app=False)
    PHOENIX_AVAILABLE = True
    logger.info("[OK] Phoenix tracing enabled")
except ImportError as e:
    logger.warning(f"[WARN] Phoenix tracing not available: {e}")
    # Fallback no-op decorators
    def traced(agent_name="", route=""):
        def decorator(func):
            return func
        return decorator
    def wrap_client(client):
        return client
    PHOENIX_AVAILABLE = False

# Progress indicator (try tqdm, fallback to simple print)
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.info("tqdm not available - using simple progress")


def load_golden_dataset(path: str, limit: Optional[int] = None) -> list[dict]:
    """Load golden dataset from JSONL file."""
    cases = []
    with open(path) as f:
        for line in f:
            cases.append(json.loads(line.strip()))
            if limit and len(cases) >= limit:
                break
    
    logger.info(f"Loaded {len(cases)} golden cases from {path}")
    return cases


@traced(agent_name="eval_runner", route="diagnosis")
def get_agent_diagnosis(case: dict, model: str = "groq") -> dict:
    """
    Call agent to get a diagnosis.

    First tries to use RivetOrchestrator if available,
    then falls back to direct Groq/OpenAI API call.

    Args:
        case: Test case dict with input, equipment, expected_output
        model: "groq" or "openai" for fallback API

    Returns:
        Dict with root_cause, safety_warnings, repair_steps, manual_citations
    """
    # Try RivetOrchestrator first
    try:
        # Attempt to import orchestrator
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from agent_factory.orchestrators.rivet_orchestrator import RivetOrchestrator

        orchestrator = RivetOrchestrator()

        result = orchestrator.diagnose(
            fault_code=case.get("input", {}).get("fault_code", "UNKNOWN"),
            equipment_type=case.get("equipment", {}).get("model", ""),
            manufacturer=case.get("equipment", {}).get("manufacturer", "Unknown"),
            sensor_data=case.get("input", {}).get("sensor_data", {}),
            context=case.get("input", {}).get("context", ""),
        )

        # Ensure dict format
        if isinstance(result, dict):
            return {
                "root_cause": result.get("root_cause", ""),
                "safety_warnings": result.get("safety_warnings", []),
                "repair_steps": result.get("repair_steps", []),
                "manual_citations": result.get("manual_citations", []),
            }

    except ImportError:
        logger.debug("RivetOrchestrator not found - using fallback API")
    except Exception as e:
        logger.warning(f"RivetOrchestrator failed: {e} - using fallback")

    # Fallback: Direct API call
    try:
        equipment = case.get("equipment", {})
        input_data = case.get("input", {})

        prompt = f"""You are an expert industrial maintenance technician.

EQUIPMENT:
- Manufacturer: {equipment.get('manufacturer', 'Unknown')}
- Model: {equipment.get('model', '')}

FAULT:
- Code: {input_data.get('fault_code', 'UNKNOWN')}
- Description: {input_data.get('fault_description', '')}

CONTEXT:
{input_data.get('context', '')}

Provide a complete diagnosis in JSON format with these exact fields:
- root_cause: Explanation of what's causing the fault
- safety_warnings: List of critical safety warnings
- repair_steps: Step-by-step repair procedure
- manual_citations: Relevant manual references

Respond ONLY with valid JSON."""

        if model == "groq":
            import groq
            client = groq.Groq()
            client = wrap_client(client)  # Wrap for Phoenix tracing

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            result = json.loads(response.choices[0].message.content)

        else:  # openai
            import openai
            client = openai.OpenAI()
            client = wrap_client(client)  # Wrap for Phoenix tracing

            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            result = json.loads(response.choices[0].message.content)

        # Ensure all required fields exist
        return {
            "root_cause": result.get("root_cause", ""),
            "safety_warnings": result.get("safety_warnings", []),
            "repair_steps": result.get("repair_steps", []),
            "manual_citations": result.get("manual_citations", []),
        }

    except Exception as e:
        logger.error(f"Fallback API call failed: {e}")
        return {
            "root_cause": f"ERROR: {str(e)}",
            "safety_warnings": [],
            "repair_steps": [],
            "manual_citations": [],
        }


def run_judge_eval(
    client,
    template: str,
    case: dict,
    agent_output: dict,
    rails: list[str]
) -> dict:
    """
    Run a single LLM-as-judge evaluation.
    
    Returns:
        {"label": str, "reason": str, "raw_response": str}
    """
    # Format the template with case data and agent output
    prompt = template.format(
        # Equipment info
        equipment=case.get("equipment", {}).get("model", "Unknown"),
        manufacturer=case.get("equipment", {}).get("manufacturer", "Unknown"),
        
        # Fault info
        fault_code=case.get("input", {}).get("fault_code", "Unknown"),
        fault_description=case.get("input", {}).get("fault_description", ""),
        sensor_data=json.dumps(case.get("input", {}).get("sensor_data", {})),
        
        # Agent outputs
        agent_root_cause=agent_output.get("root_cause", ""),
        agent_safety_warnings="\n".join(agent_output.get("safety_warnings", [])),
        agent_repair_steps="\n".join(agent_output.get("repair_steps", [])),
        agent_citations="\n".join(agent_output.get("manual_citations", [])),
        
        # Expected outputs (reference)
        expected_root_cause=case.get("expected_output", {}).get("root_cause", ""),
        expected_safety_warnings="\n".join(
            case.get("expected_output", {}).get("safety_critical_warnings", [])
        ),
        expected_repair_steps="\n".join(
            case.get("expected_output", {}).get("repair_steps", [])
        ),
        known_valid_manuals="\n".join(
            case.get("expected_output", {}).get("manual_citations", [])
        ),
        
        # Additional fields for specific templates
        voltage_level=case.get("equipment", {}).get("voltage", "Unknown"),
        safety_classification=case.get("expected_output", {}).get(
            "business_impact", {}
        ).get("safety_critical", False),
        complexity_level="Medium",
    )
    
    # Call judge LLM
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,  # Deterministic judging
        max_tokens=500
    )
    
    raw_response = response.choices[0].message.content
    
    # Parse response to extract label
    label = "UNKNOWN"
    reason = raw_response
    
    for rail in rails:
        if f"LABEL: {rail}" in raw_response or raw_response.strip().startswith(rail):
            label = rail
            # Extract reason if present
            if "REASON:" in raw_response:
                reason = raw_response.split("REASON:")[1].split("\n")[0].strip()
            break
    
    return {
        "label": label,
        "reason": reason,
        "raw_response": raw_response
    }


def run_full_eval(
    cases: list[dict],
    client,
    model: str = "groq",
    judge_model: str = "gpt-4-turbo",
    dry_run: bool = False,
    use_parallel: bool = False
) -> list[dict]:
    """
    Run all evaluations on all cases.

    Args:
        cases: List of test cases from golden dataset
        client: OpenAI client for judge
        model: "groq" or "openai" for agent calls
        judge_model: Model name for judge LLM
        dry_run: If True, don't actually run evals
        use_parallel: If True, run cases concurrently

    Returns:
        List of eval results
    """
    if use_parallel:
        logger.info("Running cases in parallel mode...")
        return asyncio.run(_run_parallel_eval(cases, client, model, judge_model, dry_run))
    else:
        return _run_sequential_eval(cases, client, model, judge_model, dry_run)


def _run_sequential_eval(
    cases: list[dict],
    client,
    model: str,
    judge_model: str,
    dry_run: bool
) -> list[dict]:
    """Run evals sequentially with progress indicator."""
    results = []

    # Setup progress indicator
    if TQDM_AVAILABLE:
        iterator = tqdm(cases, desc="Evaluating cases", unit="case")
    else:
        iterator = cases
        total = len(cases)

    for i, case in enumerate(iterator, 1):
        case_id = case.get("test_case_id", f"case_{i}")

        if not TQDM_AVAILABLE:
            logger.info(f"[{i}/{total}] Evaluating: {case_id}")

        if dry_run:
            logger.info(f"  DRY RUN: Would evaluate case {case_id}")
            continue

        # Step 1: Get agent diagnosis
        agent_output = get_agent_diagnosis(case, model=model)
        
        # Step 2: Run each judge
        case_results = {
            "case_id": case_id,
            "fault_code": case.get("input", {}).get("fault_code"),
            "equipment": case.get("equipment", {}).get("model"),
            "timestamp": datetime.utcnow().isoformat(),
            "evals": {}
        }
        
        # Technical accuracy
        accuracy_result = run_judge_eval(
            client,
            TECHNICAL_ACCURACY_TEMPLATE,
            case,
            agent_output,
            EVAL_CONFIG["technical_accuracy"]["rails"]
        )
        case_results["evals"]["technical_accuracy"] = accuracy_result
        
        # Safety compliance
        safety_result = run_judge_eval(
            client,
            SAFETY_COMPLIANCE_TEMPLATE,
            case,
            agent_output,
            EVAL_CONFIG["safety_compliance"]["rails"]
        )
        case_results["evals"]["safety_compliance"] = safety_result
        
        # Procedure completeness
        procedure_result = run_judge_eval(
            client,
            PROCEDURE_COMPLETENESS_TEMPLATE,
            case,
            agent_output,
            EVAL_CONFIG["procedure_completeness"]["rails"]
        )
        case_results["evals"]["procedure_completeness"] = procedure_result
        
        # Citation accuracy
        citation_result = run_judge_eval(
            client,
            MANUAL_CITATION_TEMPLATE,
            case,
            agent_output,
            EVAL_CONFIG["citation_accuracy"]["rails"]
        )
        case_results["evals"]["citation_accuracy"] = citation_result
        
        # Print summary for this case
        logger.info(f"  Accuracy: {accuracy_result['label']}")
        logger.info(f"  Safety: {safety_result['label']}")
        logger.info(f"  Procedure: {procedure_result['label']}")
        logger.info(f"  Citations: {citation_result['label']}")
        
        results.append(case_results)
    
    return results


async def _run_parallel_eval(
    cases: list[dict],
    client,
    model: str,
    judge_model: str,
    dry_run: bool
) -> list[dict]:
    """
    Run evals in parallel using asyncio.

    Note: This requires async-compatible API clients.
    For now, we'll use concurrent.futures for parallelism.
    """
    import concurrent.futures

    def eval_single_case(case_with_index):
        idx, case = case_with_index
        case_id = case.get("test_case_id", f"case_{idx}")

        if dry_run:
            logger.info(f"  DRY RUN: Would evaluate case {case_id}")
            return None

        # Get agent diagnosis
        agent_output = get_agent_diagnosis(case, model=model)

        # Run judges
        case_results = {
            "case_id": case_id,
            "fault_code": case.get("input", {}).get("fault_code"),
            "equipment": case.get("equipment", {}).get("model"),
            "timestamp": datetime.utcnow().isoformat(),
            "evals": {}
        }

        # Run all judge evals
        for eval_name, config in EVAL_CONFIG.items():
            template = config["template"]
            rails = config["rails"]
            result = run_judge_eval(client, template, case, agent_output, rails)
            case_results["evals"][eval_name] = result

        return case_results

    # Run cases in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(eval_single_case, (i, case)): case
            for i, case in enumerate(cases, 1)
        }

        # Progress indicator
        if TQDM_AVAILABLE:
            futures_iter = tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Evaluating cases",
                unit="case"
            )
        else:
            futures_iter = concurrent.futures.as_completed(futures)

        for future in futures_iter:
            try:
                result = future.result()
                if result:  # Skip None (dry run)
                    results.append(result)
            except Exception as e:
                logger.error(f"Parallel eval failed: {e}")

    return results


def compute_summary(results: list[dict]) -> dict:
    """Compute summary statistics from eval results."""
    if not results:
        return {}
    
    summary = {
        "total_cases": len(results),
        "timestamp": datetime.utcnow().isoformat(),
        "by_eval": {}
    }
    
    # Count by eval type
    for eval_name in EVAL_CONFIG.keys():
        counts = {}
        for result in results:
            label = result.get("evals", {}).get(eval_name, {}).get("label", "UNKNOWN")
            counts[label] = counts.get(label, 0) + 1
        
        config = EVAL_CONFIG[eval_name]
        pass_labels = [config["rails"][0]]  # First rail is usually the "pass" label
        pass_count = sum(counts.get(label, 0) for label in pass_labels)
        pass_rate = pass_count / len(results) if results else 0
        
        summary["by_eval"][eval_name] = {
            "counts": counts,
            "pass_rate": pass_rate,
            "threshold": config["threshold"],
            "passed": pass_rate >= config["threshold"],
            "blocking": config["blocking"]
        }
    
    # Overall pass/fail
    blocking_evals = get_blocking_evals()
    summary["gate_passed"] = all(
        summary["by_eval"][eval_name]["passed"]
        for eval_name in blocking_evals
        if eval_name in summary["by_eval"]
    )
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Run Phoenix evaluations on golden dataset"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/golden_dataset.jsonl",
        help="Path to golden dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evals/eval_results.json",
        help="Output file for results"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of cases to evaluate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without running evals"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run cases concurrently using asyncio (default: sequential)"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["groq", "openai"],
        default="groq",
        help="Model to use for agent diagnosis (default: groq)"
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default="gpt-4-turbo",
        help="Model to use for judge LLM (default: gpt-4-turbo)"
    )

    args = parser.parse_args()
    
    print("=" * 60)
    print("PHOENIX EVALUATION RUN")
    print("=" * 60)
    print(f"  Dataset: {args.dataset}")
    print(f"  Output: {args.output}")
    print(f"  Limit: {args.limit or 'None (all)'}")
    print(f"  Dry run: {args.dry_run}")
    print("=" * 60)
    
    # Check for dataset
    if not os.path.exists(args.dataset):
        logger.error(f"Dataset not found: {args.dataset}")
        logger.error("Run export_golden_dataset.py first")
        exit(1)
    
    # Initialize OpenAI client for judge
    try:
        from openai import OpenAI
        client = OpenAI()
        client = wrap_client(client)  # Wrap for Phoenix tracing
        logger.info("[OK] OpenAI client initialized (Phoenix tracing enabled)")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        logger.error("Set OPENAI_API_KEY in your environment")
        exit(1)
    
    # Load dataset
    cases = load_golden_dataset(args.dataset, limit=args.limit)
    
    if not cases:
        logger.error("No cases found in dataset")
        exit(1)
    
    # Run evaluations
    logger.info(f"\n🔍 Running evals on {len(cases)} cases...")
    logger.info(f"  Agent model: {args.model}")
    logger.info(f"  Judge model: {args.judge_model}")
    logger.info(f"  Parallel mode: {args.parallel}")

    results = run_full_eval(
        cases,
        client,
        model=args.model,
        judge_model=args.judge_model,
        dry_run=args.dry_run,
        use_parallel=args.parallel
    )
    
    if args.dry_run:
        print("\n🔍 DRY RUN complete. No actual evals run.")
        return
    
    # Compute summary
    summary = compute_summary(results)
    
    # Save results
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({
            "summary": summary,
            "results": results
        }, f, indent=2)

    logger.info(f"\n[OK] Results saved to {args.output}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    
    for eval_name, stats in summary.get("by_eval", {}).items():
        status = "[PASS]" if stats["passed"] else "[FAIL]"
        blocking = " [BLOCKING]" if stats["blocking"] else ""
        print(f"  {eval_name}:")
        print(f"    {status} {stats['pass_rate']*100:.1f}% >= {stats['threshold']*100:.0f}%{blocking}")
        print(f"    Counts: {stats['counts']}")

    print("=" * 60)

    if summary.get("gate_passed"):
        print("[SUCCESS] GATE PASSED: All blocking thresholds met")
        exit(0)
    else:
        print("[FAILED] GATE FAILED: Fix regressions before merging")
        exit(1)


if __name__ == "__main__":
    main()
