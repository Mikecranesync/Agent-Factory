#!/usr/bin/env python3
"""Test Gemini Judge with knowledge atoms.

Usage:
    poetry run python scripts/knowledge/test_judge.py \
        --input data/atoms-core-repos.json \
        --output data/atoms-core-repos-eval.json
"""

import argparse
import json
import logging
from pathlib import Path

from agent_factory.judges import GeminiJudge, JudgmentResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_atoms(input_path: Path):
    """Load atoms from JSON file."""
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)
        # Handle both raw list and wrapped structure
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'atoms' in data:
            return data['atoms']
        else:
            raise ValueError("Invalid JSON structure: expected list or dict with 'atoms' key")


def save_judgment(judgment: JudgmentResult, output_path: Path):
    """Save judgment result to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(judgment.to_dict(), f, indent=2, ensure_ascii=False)

    logger.info(f"Judgment saved to: {output_path}")


def print_summary(judgment: JudgmentResult):
    """Print human-readable summary of judgment."""
    print("\n" + "=" * 70)
    print("JUDGMENT SUMMARY")
    print("=" * 70)

    print(f"\nTask ID: {judgment.task_id}")
    print(f"Atoms Evaluated: {judgment.atoms_evaluated}")
    print(f"Median Quality Score: {judgment.median_quality_score:.2f}/5")

    print("\nQuality Distribution:")
    dist = judgment.quality_distribution
    print(f"  Excellent (5): {dist.get('excellent', 0)}")
    print(f"  Good (4):      {dist.get('good', 0)}")
    print(f"  Fair (3):      {dist.get('fair', 0)}")
    print(f"  Poor (2):      {dist.get('poor', 0)}")
    print(f"  Unusable (1):  {dist.get('unusable', 0)}")

    print(f"\nProduct Candidates Found: {len(judgment.all_product_candidates)}")

    if judgment.fastest_monetization_pick:
        pick = judgment.fastest_monetization_pick
        print("\n" + "-" * 70)
        print("FASTEST MONETIZATION PICK")
        print("-" * 70)
        print(f"Product: {pick['chosen_product_name']}")
        print(f"Confidence: {pick['product_confidence']}/5")
        print(f"Effort: {pick['effort_to_productize']}")
        print(f"\nIdea: {pick['product_idea']}")
        print(f"\nTarget Market: {pick.get('target_market', 'N/A')}")
        print(f"Price Tier: {pick.get('price_tier', 'N/A')}")
        print(f"\nNext Steps:")
        for i, step in enumerate(pick.get('next_steps', []), 1):
            print(f"  {i}. {step}")
    else:
        print("\nNo high-confidence products found (confidence < 4)")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Test Gemini Judge with knowledge atoms")
    parser.add_argument("--input", default="data/atoms-core-repos.json", help="Input atoms JSON file")
    parser.add_argument("--output", default="data/atoms-core-repos-eval.json", help="Output evaluation JSON file")
    parser.add_argument("--task-id", default="test-core-atoms", help="Task ID for evaluation")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model to use")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print("=" * 70)
    print("GEMINI JUDGE TEST")
    print("=" * 70)
    print(f"\nInput:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Model:  {args.model}")

    # Load atoms
    logger.info(f"Loading atoms from: {input_path}")
    atoms = load_atoms(input_path)
    logger.info(f"Loaded {len(atoms)} atoms")

    # Create judge
    judge = GeminiJudge(model=args.model)

    # Judge atoms
    task_context = "Agent Factory CORE patterns - LLM routing, database failover, memory management"

    try:
        logger.info("Calling Gemini judge...")
        judgment = judge.judge_atoms(
            atoms=atoms,
            task_context=task_context,
            task_id=args.task_id
        )

        # Save result
        save_judgment(judgment, output_path)

        # Print summary
        print_summary(judgment)

        # Success metrics
        success = True
        if judgment.median_quality_score < 4:
            logger.warning("Median quality score below target (4.0)")
            success = False

        if len(judgment.all_product_candidates) == 0:
            logger.warning("No product candidates found")
            success = False

        if success:
            print("\n✅ Judge test PASSED")
        else:
            print("\n⚠️  Judge test completed with warnings")

        return success

    except Exception as e:
        logger.error(f"Judge test failed: {e}", exc_info=True)
        print(f"\n❌ Judge test FAILED: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
