"""
Validates that retriever.py column references match actual database schema.
Run before deploying to catch schema mismatches.

Usage:
    poetry run python scripts/validate_schema.py

Exit codes:
    0 - Schema matches
    1 - Schema mismatch found
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg

# Load environment
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)


def get_actual_columns():
    """Query database for actual knowledge_atoms columns."""
    db_url = os.getenv("NEON_DB_URL")
    if not db_url:
        print("[ERROR] NEON_DB_URL not found in .env")
        sys.exit(1)

    try:
        conn = psycopg.connect(db_url, connect_timeout=10)
        cursor = conn.cursor()

        # Get column names from information_schema
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'knowledge_atoms'
            ORDER BY ordinal_position
        """)

        columns = [row[0] for row in cursor.fetchall()]
        conn.close()
        return set(columns)

    except Exception as e:
        print(f"[ERROR] Database query failed: {e}")
        sys.exit(1)


def get_expected_columns():
    """Extract columns used in retriever.py SELECT statement."""
    retriever_path = project_root / "agent_factory" / "rivet_pro" / "rag" / "retriever.py"

    if not retriever_path.exists():
        print(f"[ERROR] File not found: {retriever_path}")
        sys.exit(1)

    content = retriever_path.read_text()

    # Find SELECT statement (lines 159-176)
    # Look for columns between SELECT and FROM
    import re
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM knowledge_atoms', content, re.DOTALL)

    if not select_match:
        print("[ERROR] Could not find SELECT statement in retriever.py")
        sys.exit(1)

    select_clause = select_match.group(1)

    # Extract column names (ignoring aliases and comments)
    columns = []
    for line in select_clause.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Remove trailing commas and comments
        if '--' in line:
            line = line.split('--')[0].strip()
        # Remove trailing commas and aliases (e.g., "source_document as source")
        parts = line.split()
        if parts:
            col = parts[0].rstrip(',')
            # Skip numeric literals like "0.8"
            if col and not col.startswith('--') and not col.replace('.', '').isdigit():
                columns.append(col)

    return set(columns)


def main():
    print("=== Schema Validation ===")
    print()

    print("[1/3] Fetching actual database schema...")
    actual = get_actual_columns()
    print(f"   Found {len(actual)} columns in knowledge_atoms table")

    print("[2/3] Parsing retriever.py SELECT statement...")
    expected = get_expected_columns()
    print(f"   Found {len(expected)} columns in SELECT")

    print("[3/3] Comparing schemas...")
    print()

    missing = expected - actual
    extra = actual - expected

    if missing:
        print(f"[FAIL] Columns in retriever.py but NOT in database:")
        for col in sorted(missing):
            print(f"   - {col}")
        print()

    if extra:
        print(f"[INFO] Columns in database but not used in retriever.py:")
        for col in sorted(extra):
            print(f"   - {col}")
        print()

    if missing:
        print("[RESULT] Schema mismatch detected!")
        print("Action: Update retriever.py to use existing columns")
        sys.exit(1)
    else:
        print("[RESULT] Schema validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
