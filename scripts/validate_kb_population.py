#!/usr/bin/env python3
"""
Validate Knowledge Base Population

Verifies that the knowledge_atoms table is populated with atoms.

Usage:
    poetry run python scripts/validate_kb_population.py

Expected Result:
    PASS: If atoms are found in the database
    FAIL: If database is empty or connection fails
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core.database_manager import DatabaseManager


def validate_kb_population() -> bool:
    """
    Validate that the knowledge base has been populated with atoms.

    Returns:
        bool: True if atoms exist, False otherwise
    """
    print("=" * 70)
    print("KNOWLEDGE BASE POPULATION VALIDATION")
    print("=" * 70)

    # Initialize database manager
    print("\nConnecting to database...")
    try:
        db = DatabaseManager()
        print("[OK] Database connection established")
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False

    # Query atom count
    print("\nQuerying knowledge_atoms table...")
    try:
        query = "SELECT COUNT(*) FROM knowledge_atoms"
        result = db.execute_query(query)
        atom_count = result[0][0] if result else 0
        print(f"[OK] Query successful")
    except Exception as e:
        print(f"[FAIL] Query failed: {e}")
        return False

    # Validate count
    print("\nValidation Results:")
    print("-" * 70)

    if atom_count == 0:
        print(f"[FAIL] Knowledge Base is EMPTY (0 atoms)")
        print("\nAction Required:")
        print("  Run: poetry run python upload_atoms_to_neon.py")
        return False
    else:
        print(f"[PASS] Knowledge Base populated with {atom_count} atoms")

        # Sample some atoms to verify data quality
        print("\nSample Atoms (first 3):")
        try:
            sample_query = """
                SELECT atom_id, title, atom_type, manufacturer
                FROM knowledge_atoms
                LIMIT 3
            """
            samples = db.execute_query(sample_query)

            for idx, (atom_id, title, atom_type, manufacturer) in enumerate(samples, 1):
                print(f"  {idx}. [{atom_type}] {title}")
                print(f"     ID: {atom_id}, Vendor: {manufacturer}")
        except Exception as e:
            print(f"  [WARNING] Could not fetch sample atoms: {e}")

        return True


def main():
    """Main validation entry point."""
    success = validate_kb_population()

    print("\n" + "=" * 70)
    if success:
        print("VALIDATION: PASS")
        print("=" * 70)
        print("\nKnowledge Base is ready!")
        print("\nNext Steps:")
        print("  - Bot will display correct atom count")
        print("  - Startup health check will pass")
        print("  - Ready to merge to main branch")
        sys.exit(0)
    else:
        print("VALIDATION: FAIL")
        print("=" * 70)
        print("\nKnowledge Base is NOT ready!")
        print("Fix the issue above before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
