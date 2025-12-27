#!/usr/bin/env python3
"""
Execute database migration using psycopg2 directly.

Usage:
    python scripts/run_migration.py migrations/001_create_rivet_users.sql
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import psycopg2


def run_migration(migration_file: str):
    """Execute SQL migration file."""
    print(f"Loading migration: {migration_file}")

    with open(migration_file, 'r') as f:
        sql = f.read()

    # Get database connection from environment
    provider = os.getenv("DATABASE_PROVIDER", "neon")

    print(f"Connecting to database ({provider})...")

    if provider == "neon":
        conn_string = os.getenv("NEON_DB_URL")
    elif provider == "supabase":
        conn_string = f"host={os.getenv('SUPABASE_DB_HOST')} port={os.getenv('SUPABASE_DB_PORT', '5432')} dbname={os.getenv('SUPABASE_DB_NAME', 'postgres')} user={os.getenv('SUPABASE_DB_USER', 'postgres')} password={os.getenv('SUPABASE_DB_PASSWORD')}"
    elif provider == "railway":
        conn_string = os.getenv("RAILWAY_DB_URL")
    else:
        print(f"ERROR: Unknown provider: {provider}")
        sys.exit(1)

    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True

        print(f"Executing migration on {provider}...")

        # Execute migration
        cursor = conn.cursor()
        cursor.execute(sql)

        print("[SUCCESS] Migration executed successfully")

        # Verify table exists
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'rivet_users'
        """)
        result = cursor.fetchone()

        if result:
            print(f"[SUCCESS] Table verified: {result[0]}")
        else:
            print("[ERROR] Table verification failed")
            sys.exit(1)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <migration_file>")
        sys.exit(1)

    run_migration(sys.argv[1])
