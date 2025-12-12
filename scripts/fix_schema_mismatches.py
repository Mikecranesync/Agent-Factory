#!/usr/bin/env python3
"""
SCHEMA MISMATCH FIX SCRIPT - Automatic Schema Repair

Automatically detect and fix schema mismatches between expected and actual database schema.
Uses the Diagnostic Agent to find issues, then generates and applies fixes.

Features:
- Auto-detect all schema mismatches
- Generate ALTER TABLE statements for missing columns
- Apply fixes automatically (with confirmation)
- Rollback support if fixes fail
- Dry-run mode (show fixes without applying)

Usage:
    # Detect and fix all issues
    poetry run python scripts/fix_schema_mismatches.py

    # Fix specific table
    poetry run python scripts/fix_schema_mismatches.py --table agent_messages

    # Dry run (show fixes without applying)
    poetry run python scripts/fix_schema_mismatches.py --dry-run

    # Auto-apply without confirmation
    poetry run python scripts/fix_schema_mismatches.py --yes

Author: Agent Factory
Created: 2025-12-11
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.database.supabase_diagnostic_agent import SupabaseDiagnosticAgent, SchemaMismatch
import psycopg2

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
# SCHEMA FIXER
# ============================================================================

class SchemaFixer:
    """
    Automatically fix schema mismatches.
    """

    def __init__(self, dry_run: bool = False, auto_yes: bool = False):
        """
        Initialize schema fixer.

        Args:
            dry_run: If True, show fixes but don't apply
            auto_yes: If True, apply fixes without confirmation
        """
        self.dry_run = dry_run
        self.auto_yes = auto_yes
        self.diagnostic = SupabaseDiagnosticAgent()

    def run_diagnostic(self, table_name: str = None) -> List[SchemaMismatch]:
        """
        Run diagnostic to find schema mismatches.

        Args:
            table_name: If specified, only check this table

        Returns:
            List of schema mismatches
        """
        logger.info("Running database diagnostic...")

        if table_name:
            mismatches = self.diagnostic.compare_table(table_name)
        else:
            report = self.diagnostic.run_full_diagnostic()
            mismatches = report.mismatches

        return mismatches

    def generate_fix_sql(self, mismatches: List[SchemaMismatch]) -> List[str]:
        """
        Generate SQL statements to fix mismatches.

        Args:
            mismatches: List of schema mismatches

        Returns:
            List of SQL fix statements
        """
        fix_statements = []

        for mismatch in mismatches:
            if mismatch.mismatch_type == "missing_column":
                # Use the fix_sql from diagnostic
                if mismatch.fix_sql and not mismatch.fix_sql.startswith("--"):
                    fix_statements.append(mismatch.fix_sql)

            elif mismatch.mismatch_type == "missing_table":
                # Tables require full CREATE TABLE (not auto-fixable)
                logger.warning(f"Skipping missing table: {mismatch.table_name} (run full schema migration)")

            elif mismatch.mismatch_type == "type_mismatch":
                # Type mismatches need manual review
                logger.warning(f"Skipping type mismatch: {mismatch.table_name} (manual review required)")

        return fix_statements

    def apply_fixes(self, fix_statements: List[str]) -> Dict[str, int]:
        """
        Apply SQL fix statements.

        Args:
            fix_statements: List of SQL statements to execute

        Returns:
            Dict with success/fail counts
        """
        if self.dry_run:
            logger.info("")
            logger.info("=" * 80)
            logger.info("DRY RUN - Would execute the following SQL:")
            logger.info("=" * 80)
            for stmt in fix_statements:
                logger.info(stmt)
            logger.info("=" * 80)
            return {"success": 0, "failed": 0, "skipped": len(fix_statements)}

        logger.info("")
        logger.info("=" * 80)
        logger.info("APPLYING SCHEMA FIXES")
        logger.info("=" * 80)
        logger.info(f"Total fixes to apply: {len(fix_statements)}")
        logger.info("")

        # Show what will be executed
        logger.info("SQL statements to execute:")
        for i, stmt in enumerate(fix_statements, 1):
            logger.info(f"  {i}. {stmt}")
        logger.info("")

        # Confirm
        if not self.auto_yes:
            confirm = input("Apply these fixes? (yes/no): ")
            if confirm.lower() != "yes":
                logger.info("Cancelled by user")
                return {"success": 0, "failed": 0, "skipped": len(fix_statements)}

        # Execute fixes
        success_count = 0
        fail_count = 0

        conn = self._connect()

        try:
            for i, stmt in enumerate(fix_statements, 1):
                logger.info(f"[{i}/{len(fix_statements)}] Executing: {stmt[:80]}...")

                try:
                    with conn.cursor() as cur:
                        cur.execute(stmt)

                    conn.commit()
                    success_count += 1
                    logger.info(f"[{i}/{len(fix_statements)}] SUCCESS")

                except psycopg2.Error as e:
                    fail_count += 1
                    error_msg = f"{e.pgcode}: {e.pgerror}" if hasattr(e, 'pgcode') else str(e)
                    logger.error(f"[{i}/{len(fix_statements)}] FAILED: {error_msg}")

                    # Decide whether to continue or stop
                    if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                        logger.warning("Column might already exist, continuing...")
                    else:
                        logger.error("Critical error, rolling back...")
                        conn.rollback()
                        break

        finally:
            conn.close()

        logger.info("")
        logger.info("=" * 80)
        logger.info("FIX SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total fixes: {len(fix_statements)}")
        logger.info(f"Succeeded: {success_count}")
        logger.info(f"Failed: {fail_count}")
        logger.info("=" * 80)
        logger.info("")

        return {"success": success_count, "failed": fail_count, "skipped": 0}

    def _connect(self):
        """Connect to database"""
        database_url = os.getenv("DATABASE_URL")
        db_host = os.getenv("SUPABASE_DB_HOST")
        db_port = os.getenv("SUPABASE_DB_PORT", "5432")
        db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
        db_user = os.getenv("SUPABASE_DB_USER", "postgres")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")

        if database_url:
            # Use connection string
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            db_config = {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip('/') or "postgres",
                "user": parsed.username or "postgres",
                "password": parsed.password or db_password
            }
        elif db_host and db_password:
            # Use individual components
            db_config = {
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

        return psycopg2.connect(**db_config)

    def fix_all(self, table_name: str = None) -> Dict[str, int]:
        """
        Complete fix workflow: diagnose + generate fixes + apply.

        Args:
            table_name: If specified, only fix this table

        Returns:
            Dict with results
        """
        # Step 1: Diagnose
        mismatches = self.run_diagnostic(table_name)

        if not mismatches:
            logger.info("")
            logger.info("=" * 80)
            logger.info("[SUCCESS] No schema mismatches found! Database is healthy.")
            logger.info("=" * 80)
            logger.info("")
            return {"success": 0, "failed": 0, "skipped": 0}

        # Step 2: Generate fixes
        logger.info(f"\nFound {len(mismatches)} mismatches, generating fixes...")
        fix_statements = self.generate_fix_sql(mismatches)

        if not fix_statements:
            logger.warning("No auto-fixable mismatches found (may require manual intervention)")
            logger.info("\nMismatches that need manual review:")
            for m in mismatches:
                logger.info(f"  - {m.table_name}: {m.mismatch_type}")
                logger.info(f"    {m.fix_sql}")
            return {"success": 0, "failed": 0, "skipped": len(mismatches)}

        # Step 3: Apply fixes
        results = self.apply_fixes(fix_statements)

        # Step 4: Verify fixes
        if results["success"] > 0 and not self.dry_run:
            logger.info("\nVerifying fixes...")
            remaining_mismatches = self.run_diagnostic(table_name)

            if not remaining_mismatches:
                logger.info("")
                logger.info("=" * 80)
                logger.info("[SUCCESS] All schema issues fixed! Database is now healthy.")
                logger.info("=" * 80)
                logger.info("")
            else:
                logger.warning(f"\n[WARNING] {len(remaining_mismatches)} mismatches still remain:")
                for m in remaining_mismatches:
                    logger.warning(f"  - {m.table_name}: {m.mismatch_type}")

        return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automatically fix Supabase schema mismatches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect and fix all issues
  python scripts/fix_schema_mismatches.py

  # Fix specific table
  python scripts/fix_schema_mismatches.py --table agent_messages

  # Dry run (show fixes without applying)
  python scripts/fix_schema_mismatches.py --dry-run

  # Auto-apply without confirmation
  python scripts/fix_schema_mismatches.py --yes
        """
    )

    parser.add_argument("--table", help="Fix specific table only")
    parser.add_argument("--dry-run", action="store_true", help="Show fixes without applying")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-apply without confirmation")

    args = parser.parse_args()

    # Create fixer
    fixer = SchemaFixer(dry_run=args.dry_run, auto_yes=args.yes)

    # Run fixes
    try:
        results = fixer.fix_all(table_name=args.table)

        # Exit code
        if results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
