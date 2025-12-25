#!/usr/bin/env python3
"""Deploy Supabase knowledge schema with RPC functions."""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load environment
load_dotenv()


def get_postgres_connection():
    """Create direct PostgreSQL connection."""
    # Try Neon first (where atoms are stored)
    neon_url = os.getenv('NEON_DB_URL')
    if neon_url:
        return psycopg2.connect(neon_url)

    # Fallback to Supabase
    password = os.getenv('SUPABASE_DB_PASSWORD')
    host = os.getenv('SUPABASE_DB_HOST')
    conn_string = f"postgresql://postgres:{password}@{host}:5432/postgres"
    return psycopg2.connect(conn_string)


def deploy_schema():
    """Deploy the knowledge schema SQL file."""
    # Read schema file
    schema_path = Path(__file__).parent.parent.parent / "docs" / "database" / "supabase_knowledge_schema.sql"

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        return False

    print(f"Reading schema from: {schema_path}")
    schema_sql = schema_path.read_text(encoding='utf-8')

    # Connect and execute
    print("Connecting to Supabase PostgreSQL...")
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()

        print("Executing schema deployment...")
        cursor.execute(schema_sql)
        conn.commit()

        print("Schema deployed successfully!")

        # Verify deployment
        print("\nVerifying deployment...")

        # Check pgvector extension
        cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
        result = cursor.fetchone()
        if result:
            print(f"pgvector extension: {result[1]}")
        else:
            print("WARNING: pgvector extension not found")

        # Check RPC function
        cursor.execute("""
            SELECT proname, pronargs
            FROM pg_proc
            WHERE proname = 'search_atoms_by_embedding'
        """)
        result = cursor.fetchone()
        if result:
            print(f"RPC function: {result[0]} ({result[1]} parameters)")
        else:
            print("WARNING: RPC function not found")

        # Check index
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'knowledge_atoms'
            AND indexname = 'idx_knowledge_atoms_embedding'
        """)
        result = cursor.fetchone()
        if result:
            print(f"HNSW index: {result[0]}")
        else:
            print("WARNING: HNSW index not found (may still be building)")

        # Count atoms
        cursor.execute("SELECT COUNT(*) FROM knowledge_atoms")
        count = cursor.fetchone()[0]
        print(f"Knowledge atoms in database: {count}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = deploy_schema()
    sys.exit(0 if success else 1)
