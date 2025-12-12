#!/usr/bin/env python3
"""
SUPABASE DIAGNOSTIC AGENT - Database Schema Inspection & Validation

Programmatically connects to Supabase PostgreSQL database to:
1. Inspect actual table schemas (columns, types, indexes)
2. Compare against expected schema (from SQL migration files)
3. Detect mismatches (missing columns, tables, indexes)
4. Generate detailed diagnostic reports
5. Recommend fixes (ALTER TABLE statements)

Usage:
    # Full diagnostic (all tables)
    diagnostic = SupabaseDiagnosticAgent()
    report = diagnostic.run_full_diagnostic()

    # Check specific table
    result = diagnostic.inspect_table("agent_messages")

    # Compare against expected schema
    mismatches = diagnostic.compare_schemas()

Author: Agent Factory
Created: 2025-12-11
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================================================
# CONFIGURATION
# ============================================================================

# Expected schema from migration file
EXPECTED_TABLES = {
    "knowledge_atoms": {
        "columns": [
            ("id", "uuid"),
            ("atom_id", "text"),
            ("atom_type", "text"),
            ("title", "text"),
            ("summary", "text"),
            ("content", "text"),
            ("manufacturer", "text"),
            ("product_family", "text"),
            ("product_version", "text"),
            ("difficulty", "text"),
            ("prerequisites", "ARRAY"),
            ("related_atoms", "ARRAY"),
            ("source_document", "text"),
            ("source_pages", "ARRAY"),
            ("source_url", "text"),
            ("quality_score", "double precision"),
            ("safety_level", "text"),
            ("safety_notes", "text"),
            ("keywords", "ARRAY"),
            ("embedding", "vector"),
            ("created_at", "timestamp with time zone"),
            ("last_validated_at", "timestamp with time zone")
        ]
    },
    "research_staging": {
        "columns": [
            ("id", "uuid"),
            ("source_url", "text"),
            ("source_type", "text"),
            ("content_hash", "text"),
            ("raw_content", "text"),
            ("metadata", "jsonb"),
            ("status", "text"),
            ("error_message", "text"),
            ("created_at", "timestamp with time zone"),
            ("processed_at", "timestamp with time zone")
        ]
    },
    "video_scripts": {
        "columns": [
            ("id", "uuid"),
            ("script_id", "text"),
            ("title", "text"),
            ("hook", "text"),
            ("main_content", "text"),
            ("recap", "text"),
            ("atom_ids", "ARRAY"),
            ("citations", "jsonb"),
            ("estimated_duration_seconds", "integer"),
            ("keywords", "ARRAY"),
            ("target_difficulty", "text"),
            ("status", "text"),
            ("approval_notes", "text"),
            ("metadata", "jsonb"),
            ("created_at", "timestamp with time zone"),
            ("approved_at", "timestamp with time zone")
        ]
    },
    "upload_jobs": {
        "columns": [
            ("id", "uuid"),
            ("job_id", "text"),
            ("video_path", "text"),
            ("script_id", "text"),
            ("youtube_title", "text"),
            ("youtube_description", "text"),
            ("youtube_tags", "ARRAY"),
            ("thumbnail_path", "text"),
            ("status", "text"),
            ("youtube_video_id", "text"),
            ("error_message", "text"),
            ("metadata", "jsonb"),
            ("created_at", "timestamp with time zone"),
            ("started_at", "timestamp with time zone"),
            ("completed_at", "timestamp with time zone")
        ]
    },
    "agent_messages": {
        "columns": [
            ("id", "uuid"),
            ("session_id", "text"),  # THIS IS THE MISSING COLUMN!
            ("agent_name", "text"),
            ("message_type", "text"),
            ("content", "jsonb"),
            ("metadata", "jsonb"),
            ("created_at", "timestamp with time zone")
        ]
    },
    "session_memories": {
        "columns": [
            ("id", "uuid"),
            ("session_id", "text"),
            ("user_id", "text"),
            ("memory_type", "text"),
            ("content", "jsonb"),
            ("metadata", "jsonb"),
            ("created_at", "timestamp with time zone")
        ]
    },
    "settings": {
        "columns": [
            ("id", "uuid"),
            ("setting_key", "text"),
            ("setting_value", "text"),
            ("category", "text"),
            ("description", "text"),
            ("created_at", "timestamp with time zone"),
            ("updated_at", "timestamp with time zone")
        ]
    }
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ColumnInfo:
    """Information about a database column"""
    column_name: str
    data_type: str
    is_nullable: str
    column_default: Optional[str]
    character_maximum_length: Optional[int]

@dataclass
class TableInfo:
    """Information about a database table"""
    table_name: str
    columns: List[ColumnInfo]
    indexes: List[str]
    constraints: List[str]

@dataclass
class SchemaMismatch:
    """Schema mismatch between expected and actual"""
    table_name: str
    mismatch_type: str  # "missing_table", "missing_column", "missing_index", "type_mismatch"
    expected: Any
    actual: Any
    fix_sql: str

@dataclass
class DiagnosticReport:
    """Complete diagnostic report"""
    timestamp: str
    connection_status: str
    tables_found: int
    tables_expected: int
    total_mismatches: int
    mismatches: List[SchemaMismatch]
    table_details: Dict[str, TableInfo]

# ============================================================================
# SUPABASE DIAGNOSTIC AGENT
# ============================================================================

class SupabaseDiagnosticAgent:
    """
    Autonomous agent for Supabase database schema diagnostics.

    Connects directly to PostgreSQL database to inspect schema,
    compare with expected state, and recommend fixes.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize diagnostic agent"""
        self.agent_name = "supabase_diagnostic_agent"
        self.logger = logger or self._setup_logger()

        # Get credentials - support both direct connection string and individual components
        database_url = os.getenv("DATABASE_URL")
        db_host = os.getenv("SUPABASE_DB_HOST")
        db_port = os.getenv("SUPABASE_DB_PORT", "5432")
        db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
        db_user = os.getenv("SUPABASE_DB_USER", "postgres")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")

        if database_url:
            # Use connection string
            self.logger.info("Using DATABASE_URL connection string")
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
            self.logger.info("Using individual database credentials")
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

        self.logger.info(f"{self.agent_name} initialized")
        self.logger.info(f"Database host: {self.db_config['host']}")

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for agent"""
        logger = logging.getLogger(self.agent_name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def connect(self) -> psycopg2.extensions.connection:
        """
        Connect to Supabase PostgreSQL database.

        Returns:
            PostgreSQL connection object
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            self.logger.info("Connected to Supabase PostgreSQL")
            return conn
        except psycopg2.OperationalError as e:
            self.logger.error(f"Connection failed: {e}")
            raise

    # ========================================================================
    # TABLE INSPECTION
    # ========================================================================

    def list_tables(self, schema: str = "public") -> List[str]:
        """
        List all tables in schema.

        Args:
            schema: Schema name (default: public)

        Returns:
            List of table names
        """
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (schema,))
                tables = [row[0] for row in cur.fetchall()]

        self.logger.info(f"Found {len(tables)} tables in schema '{schema}'")
        return tables

    def inspect_table(self, table_name: str, schema: str = "public") -> TableInfo:
        """
        Inspect table structure (columns, indexes, constraints).

        Args:
            table_name: Name of table to inspect
            schema: Schema name (default: public)

        Returns:
            TableInfo object with complete table details
        """
        # Get columns
        columns_query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """

        # Get indexes
        indexes_query = """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = %s AND tablename = %s;
        """

        # Get constraints
        constraints_query = """
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_schema = %s AND table_name = %s;
        """

        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get columns
                cur.execute(columns_query, (schema, table_name))
                columns = [ColumnInfo(**row) for row in cur.fetchall()]

                # Get indexes
                cur.execute(indexes_query, (schema, table_name))
                indexes = [row['indexname'] for row in cur.fetchall()]

                # Get constraints
                cur.execute(constraints_query, (schema, table_name))
                constraints = [row['constraint_name'] for row in cur.fetchall()]

        return TableInfo(
            table_name=table_name,
            columns=columns,
            indexes=indexes,
            constraints=constraints
        )

    # ========================================================================
    # SCHEMA COMPARISON
    # ========================================================================

    def compare_table(self, table_name: str) -> List[SchemaMismatch]:
        """
        Compare actual table against expected schema.

        Args:
            table_name: Name of table to compare

        Returns:
            List of schema mismatches found
        """
        mismatches = []

        # Get expected schema
        if table_name not in EXPECTED_TABLES:
            self.logger.warning(f"No expected schema defined for table: {table_name}")
            return mismatches

        expected = EXPECTED_TABLES[table_name]
        expected_columns = {col[0]: col[1] for col in expected["columns"]}

        # Get actual schema
        try:
            actual = self.inspect_table(table_name)
            actual_columns = {col.column_name: col.data_type for col in actual.columns}
        except Exception as e:
            # Table doesn't exist
            mismatches.append(SchemaMismatch(
                table_name=table_name,
                mismatch_type="missing_table",
                expected=f"Table should exist with {len(expected_columns)} columns",
                actual="Table does not exist",
                fix_sql=f"-- See docs/supabase_complete_schema.sql to create {table_name} table"
            ))
            return mismatches

        # Compare columns
        for expected_col, expected_type in expected_columns.items():
            if expected_col not in actual_columns:
                # Missing column
                fix_sql = f"ALTER TABLE {table_name} ADD COLUMN {expected_col} {self._pg_type(expected_type)};"

                mismatches.append(SchemaMismatch(
                    table_name=table_name,
                    mismatch_type="missing_column",
                    expected=f"{expected_col} {expected_type}",
                    actual="Column does not exist",
                    fix_sql=fix_sql
                ))

            elif not self._types_compatible(expected_type, actual_columns[expected_col]):
                # Type mismatch
                mismatches.append(SchemaMismatch(
                    table_name=table_name,
                    mismatch_type="type_mismatch",
                    expected=f"{expected_col}: {expected_type}",
                    actual=f"{expected_col}: {actual_columns[expected_col]}",
                    fix_sql=f"-- Manual review needed: {table_name}.{expected_col} type mismatch"
                ))

        return mismatches

    def compare_all_tables(self) -> List[SchemaMismatch]:
        """
        Compare all expected tables against actual database.

        Returns:
            List of all schema mismatches found
        """
        all_mismatches = []

        for table_name in EXPECTED_TABLES.keys():
            mismatches = self.compare_table(table_name)
            all_mismatches.extend(mismatches)

        return all_mismatches

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _pg_type(self, expected_type: str) -> str:
        """Convert expected type to PostgreSQL type"""
        type_mapping = {
            "text": "TEXT",
            "uuid": "UUID",
            "integer": "INTEGER",
            "double precision": "DOUBLE PRECISION",
            "timestamp with time zone": "TIMESTAMPTZ",
            "jsonb": "JSONB",
            "ARRAY": "TEXT[]",
            "vector": "vector(1536)"
        }
        return type_mapping.get(expected_type, expected_type.upper())

    def _types_compatible(self, expected: str, actual: str) -> bool:
        """Check if expected and actual types are compatible"""
        # Normalize types
        expected_lower = expected.lower().replace(" ", "")
        actual_lower = actual.lower().replace(" ", "")

        # Direct match
        if expected_lower == actual_lower:
            return True

        # ARRAY types
        if "ARRAY" in expected.upper() and "[]" in actual:
            return True

        # Timestamp variations
        timestamp_types = ["timestampwithtimezone", "timestamptz", "timestamp"]
        if expected_lower in timestamp_types and actual_lower in timestamp_types:
            return True

        # Double precision variations
        if expected_lower in ["doubleprecision", "float8"] and actual_lower in ["doubleprecision", "float8"]:
            return True

        return False

    # ========================================================================
    # MAIN DIAGNOSTIC
    # ========================================================================

    def run_full_diagnostic(self) -> DiagnosticReport:
        """
        Run complete database diagnostic.

        Returns:
            DiagnosticReport with all findings
        """
        from datetime import datetime

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("SUPABASE DATABASE DIAGNOSTIC")
        self.logger.info("=" * 80)
        self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("")

        # Test connection
        try:
            with self.connect() as conn:
                connection_status = "OK"
                self.logger.info("[OK] Database connection successful")
        except Exception as e:
            connection_status = f"FAILED: {str(e)}"
            self.logger.error(f"[FAILED] Database connection failed: {e}")

        # List actual tables
        actual_tables = self.list_tables()

        # Compare schemas
        mismatches = self.compare_all_tables()

        # Get detailed info for existing tables
        table_details = {}
        for table in actual_tables:
            try:
                table_details[table] = self.inspect_table(table)
            except Exception as e:
                self.logger.error(f"Failed to inspect table {table}: {e}")

        # Create report
        report = DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            connection_status=connection_status,
            tables_found=len(actual_tables),
            tables_expected=len(EXPECTED_TABLES),
            total_mismatches=len(mismatches),
            mismatches=mismatches,
            table_details=table_details
        )

        # Log report
        self._log_report(report)

        return report

    def _log_report(self, report: DiagnosticReport):
        """Log diagnostic report"""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("DIAGNOSTIC REPORT")
        self.logger.info("=" * 80)
        self.logger.info(f"Connection Status: {report.connection_status}")
        self.logger.info(f"Tables Found: {report.tables_found}")
        self.logger.info(f"Tables Expected: {report.tables_expected}")
        self.logger.info(f"Total Mismatches: {report.total_mismatches}")
        self.logger.info("")

        if report.total_mismatches == 0:
            self.logger.info("[SUCCESS] Schema is correct! No mismatches found.")
        else:
            self.logger.warning(f"[WARNING] Found {report.total_mismatches} schema mismatches:")
            self.logger.info("")

            # Group by type
            missing_tables = [m for m in report.mismatches if m.mismatch_type == "missing_table"]
            missing_columns = [m for m in report.mismatches if m.mismatch_type == "missing_column"]
            type_mismatches = [m for m in report.mismatches if m.mismatch_type == "type_mismatch"]

            if missing_tables:
                self.logger.warning(f"\nMISSING TABLES ({len(missing_tables)}):")
                for m in missing_tables:
                    self.logger.warning(f"  - {m.table_name}")
                    self.logger.info(f"    Fix: {m.fix_sql}")

            if missing_columns:
                self.logger.warning(f"\nMISSING COLUMNS ({len(missing_columns)}):")
                for m in missing_columns:
                    self.logger.warning(f"  - {m.table_name}: {m.expected}")
                    self.logger.info(f"    Fix: {m.fix_sql}")

            if type_mismatches:
                self.logger.warning(f"\nTYPE MISMATCHES ({len(type_mismatches)}):")
                for m in type_mismatches:
                    self.logger.warning(f"  - {m.table_name}")
                    self.logger.warning(f"    Expected: {m.expected}")
                    self.logger.warning(f"    Actual: {m.actual}")

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("")


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test diagnostic agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Supabase Database Diagnostic Agent")
    parser.add_argument("--table", help="Inspect specific table")
    parser.add_argument("--list", action="store_true", help="List all tables")

    args = parser.parse_args()

    diagnostic = SupabaseDiagnosticAgent()

    if args.list:
        tables = diagnostic.list_tables()
        print("\nTables in database:")
        for table in tables:
            print(f"  - {table}")

    elif args.table:
        info = diagnostic.inspect_table(args.table)
        print(f"\nTable: {info.table_name}")
        print(f"\nColumns ({len(info.columns)}):")
        for col in info.columns:
            nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
            print(f"  - {col.column_name:<30} {col.data_type:<20} {nullable}")
        print(f"\nIndexes ({len(info.indexes)}):")
        for idx in info.indexes:
            print(f"  - {idx}")

    else:
        # Run full diagnostic
        report = diagnostic.run_full_diagnostic()

        if report.total_mismatches > 0:
            print("\n" + "=" * 80)
            print("RECOMMENDED FIXES")
            print("=" * 80)
            print("\nRun these SQL statements to fix schema mismatches:\n")
            for mismatch in report.mismatches:
                if mismatch.fix_sql and not mismatch.fix_sql.startswith("--"):
                    print(mismatch.fix_sql)


if __name__ == "__main__":
    main()
