#!/usr/bin/env python3
"""
Validate Knowledge Atoms Script

Quick script to validate atoms during generation workflow.
Demonstrates automatic validation without manual steps.

Usage:
    poetry run python scripts/validate_atoms.py
    poetry run python scripts/validate_atoms.py --verbose
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.knowledge.atom_validator import (
    load_and_validate_atoms,
    print_validation_report
)


def main():
    parser = argparse.ArgumentParser(description="Validate knowledge atoms")
    parser.add_argument(
        "--file",
        default="data/atoms-core-repos.json",
        help="Path to atoms JSON file (default: data/atoms-core-repos.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed error messages"
    )
    args = parser.parse_args()

    print(f"Validating atoms from: {args.file}")
    print("-" * 60)

    try:
        # Load and validate atoms
        report = load_and_validate_atoms(args.file)

        # Print formatted report
        print_validation_report(report, verbose=args.verbose)

        # Exit with appropriate code
        if report['invalid'] > 0:
            print(f"\nERROR: {report['invalid']} atoms failed validation")
            print("Fix errors and run validation again")
            sys.exit(1)
        else:
            print("\nSUCCESS: All atoms are valid and ready for embedding generation")
            sys.exit(0)

    except FileNotFoundError:
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
