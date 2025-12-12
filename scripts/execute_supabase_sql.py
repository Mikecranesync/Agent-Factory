#!/usr/bin/env python3
"""
SUPABASE SQL EXECUTOR - Direct SQL Execution Tool

Execute SQL files or inline SQL statements directly on Supabase PostgreSQL database.
No more copy/pasting into SQL Editor!

Features:
- Execute SQL files (.sql)
- Execute inline SQL statements
- Dry-run mode (validate without executing)
- Transaction support (COMMIT/ROLLBACK)
- Detailed execution logs
- Error handling and rollback on failure

Usage:
    # Execute SQL file
    poetry run python scripts/execute_supabase_sql.py --file docs/supabase_complete_schema.sql

    # Execute inline SQL
    poetry run python scripts/execute_supabase_sql.py --sql "ALTER TABLE agent_messages ADD COLUMN session_id TEXT;"

    # Dry run (validate only, don't execute)
    poetry run python scripts/execute_supabase_sql.py --file schema.sql --dry-run

    # Execute without transaction (auto-commit each statement)
    poetry run python scripts/execute_supabase_sql.py --file schema.sql --no-transaction

Author: Agent Factory
Created: 2025-12-11
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ============================================================================
# CONFIGURATION
# ============================================================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SQL EXECUTOR
# ============================================================================

class SupabaseSQLExecutor:
    """
    Execute SQL files or statements on Supabase PostgreSQL database.
    """

    def __init__(self, dry_run: bool = False, use_transaction: bool = True):
        """
        Initialize SQL executor.

        Args:
            dry_run: If True, validate SQL but don't execute
            use_transaction: If True, wrap all statements in transaction
        """
        self.dry_run = dry_run
        self.use_transaction = use_transaction

        # Get credentials - support both connection string and individual components
        database_url = os.getenv("DATABASE_URL")
        db_host = os.getenv("SUPABASE_DB_HOST")
        db_port = os.getenv("SUPABASE_DB_PORT", "5432")
        db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
        db_user = os.getenv("SUPABASE_DB_USER", "postgres")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")

        if database_url:
            # Use connection string
            logger.info("Using DATABASE_URL connection string")
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            self.db_config = {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip('/') or "postgres",
                "user": parsed.username or "postgres",
                "password": parsed.password or db_password
            }
        elif db_host and db_password:
            # Use individual components
            logger.info("Using individual database credentials")
            self.db_config = {
                "host": db_host,
                "port": int(db_port),
                "database": db_name,
                "user": db_user,
                "password": db_password
            }
        else:
            raise ValueError(
                "Missing database credentials. Need either:\n"
                "  Option 1: DATABASE_URL (full connection string)\n"
                "  Option 2: SUPABASE_DB_HOST + SUPABASE_DB_PASSWORD\n"
                "\nGet these from: Supabase Dashboard → Project Settings → Database → Connection Info"
            )

        logger.info(f"SQL Executor initialized (dry_run={dry_run}, transaction={use_transaction})")
        logger.info(f"Database: {self.db_config['host']}")

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info("Connected to Supabase PostgreSQL")
            return conn
        except psycopg2.OperationalError as e:
            logger.error(f"Connection failed: {e}")
            raise

    def parse_sql_file(self, file_path: Path) -> List[str]:
        """
        Parse SQL file into individual statements.

        Args:
            file_path: Path to SQL file

        Returns:
            List of SQL statements
        """
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")

        logger.info(f"Reading SQL file: {file_path}")

        sql_content = file_path.read_text(encoding='utf-8')

        # Split by semicolons (simple parser)
        # Note: This won't handle semicolons inside strings perfectly, but works for most SQL
        statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            # Skip comments
            if line.strip().startswith('--'):
                continue

            # Skip empty lines
            if not line.strip():
                continue

            current_statement.append(line)

            # End of statement
            if ';' in line:
                stmt = '\n'.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []

        logger.info(f"Parsed {len(statements)} SQL statements from file")
        return statements

    def execute_sql(self, sql: str, conn=None) -> Tuple[bool, str]:
        """
        Execute single SQL statement.

        Args:
            sql: SQL statement to execute
            conn: Database connection (optional, will create if not provided)

        Returns:
            (success: bool, message: str)
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute:\n{sql[:200]}...")
            return True, "Dry run - not executed"

        close_conn = False
        if conn is None:
            conn = self.connect()
            close_conn = True

        try:
            with conn.cursor() as cur:
                cur.execute(sql)

            if close_conn:
                conn.commit()

            return True, "Success"

        except psycopg2.Error as e:
            if close_conn:
                conn.rollback()
            error_msg = f"{e.pgcode}: {e.pgerror}" if hasattr(e, 'pgcode') else str(e)
            return False, error_msg

        finally:
            if close_conn:
                conn.close()

    def execute_file(self, file_path: Path) -> Tuple[int, int, List[str]]:
        """
        Execute all statements from SQL file.

        Args:
            file_path: Path to SQL file

        Returns:
            (success_count, fail_count, errors)
        """
        statements = self.parse_sql_file(file_path)

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"EXECUTING SQL FILE: {file_path.name}")
        logger.info("=" * 80)
        logger.info(f"Total statements: {len(statements)}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Use transaction: {self.use_transaction}")
        logger.info("")

        success_count = 0
        fail_count = 0
        errors = []

        if self.use_transaction and not self.dry_run:
            # Execute all statements in single transaction
            conn = self.connect()
            try:
                for i, stmt in enumerate(statements, 1):
                    logger.info(f"[{i}/{len(statements)}] Executing statement...")

                    success, message = self.execute_sql(stmt, conn)

                    if success:
                        success_count += 1
                        logger.info(f"[{i}/{len(statements)}] SUCCESS")
                    else:
                        fail_count += 1
                        error_msg = f"Statement {i}: {message}"
                        errors.append(error_msg)
                        logger.error(f"[{i}/{len(statements)}] FAILED: {message}")

                        # Rollback entire transaction on any error
                        logger.error("Rolling back entire transaction...")
                        conn.rollback()
                        break

                # Commit if all succeeded
                if fail_count == 0:
                    conn.commit()
                    logger.info("Transaction committed successfully")

            finally:
                conn.close()

        else:
            # Execute each statement independently (auto-commit)
            for i, stmt in enumerate(statements, 1):
                logger.info(f"[{i}/{len(statements)}] Executing statement...")

                success, message = self.execute_sql(stmt)

                if success:
                    success_count += 1
                    logger.info(f"[{i}/{len(statements)}] SUCCESS")
                else:
                    fail_count += 1
                    error_msg = f"Statement {i}: {message}"
                    errors.append(error_msg)
                    logger.error(f"[{i}/{len(statements)}] FAILED: {message}")

        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total statements: {len(statements)}")
        logger.info(f"Succeeded: {success_count}")
        logger.info(f"Failed: {fail_count}")

        if errors:
            logger.info("")
            logger.error("ERRORS:")
            for error in errors:
                logger.error(f"  - {error}")

        logger.info("=" * 80)
        logger.info("")

        return success_count, fail_count, errors

    def execute_inline(self, sql: str) -> Tuple[bool, str]:
        """
        Execute inline SQL statement.

        Args:
            sql: SQL statement to execute

        Returns:
            (success: bool, message: str)
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("EXECUTING INLINE SQL")
        logger.info("=" * 80)
        logger.info(f"SQL:\n{sql}")
        logger.info("")

        success, message = self.execute_sql(sql)

        if success:
            logger.info("[SUCCESS] SQL executed successfully")
        else:
            logger.error(f"[FAILED] {message}")

        logger.info("=" * 80)
        logger.info("")

        return success, message


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Execute SQL files or statements on Supabase PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute SQL file
  python scripts/execute_supabase_sql.py --file docs/supabase_complete_schema.sql

  # Execute inline SQL
  python scripts/execute_supabase_sql.py --sql "ALTER TABLE agent_messages ADD COLUMN session_id TEXT;"

  # Dry run (validate without executing)
  python scripts/execute_supabase_sql.py --file schema.sql --dry-run

  # Execute without transaction (auto-commit each statement)
  python scripts/execute_supabase_sql.py --file schema.sql --no-transaction
        """
    )

    parser.add_argument("--file", type=Path, help="SQL file to execute")
    parser.add_argument("--sql", help="Inline SQL statement to execute")
    parser.add_argument("--dry-run", action="store_true", help="Validate SQL without executing")
    parser.add_argument("--no-transaction", action="store_true", help="Don't use transaction (auto-commit each statement)")

    args = parser.parse_args()

    # Validate arguments
    if not args.file and not args.sql:
        parser.error("Must specify either --file or --sql")

    if args.file and args.sql:
        parser.error("Cannot specify both --file and --sql")

    # Create executor
    executor = SupabaseSQLExecutor(
        dry_run=args.dry_run,
        use_transaction=not args.no_transaction
    )

    # Execute
    try:
        if args.file:
            success_count, fail_count, errors = executor.execute_file(args.file)
            sys.exit(0 if fail_count == 0 else 1)

        elif args.sql:
            success, message = executor.execute_inline(args.sql)
            sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
