"""
Deploy management dashboard tables to database.

Creates:
- video_approval_queue - Videos awaiting CEO approval
- agent_status - Real-time agent tracking
- alert_history - Alert log

Usage:
    poetry run python scripts/deploy_management_schema.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.core.database_manager import DatabaseManager


def deploy_schema():
    """Deploy management schema to database."""

    print("=" * 70)
    print("MANAGEMENT DASHBOARD SCHEMA DEPLOYMENT")
    print("=" * 70)

    # Load SQL migration file
    sql_file = project_root / "docs" / "database" / "management_tables_migration.sql"

    if not sql_file.exists():
        print(f"[FAIL] SQL file not found: {sql_file}")
        return False

    print(f"[OK] Found SQL migration: {sql_file.name}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"[OK] Loaded SQL ({len(sql_content)} bytes)")

    # Connect to database
    db = DatabaseManager()
    current_provider = os.getenv("DATABASE_PROVIDER", "neon")

    print(f"[OK] Target database: {current_provider.upper()}")
    print("")

    # Execute migration
    try:
        print("Executing migration...")

        conn = db.get_connection()
        cursor = conn.cursor()

        # Execute the SQL file
        cursor.execute(sql_content)
        conn.commit()

        print("[OK] Migration executed successfully")
        print("")

        # Verify tables created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('video_approval_queue', 'agent_status', 'alert_history')
            ORDER BY table_name
        """)

        tables = cursor.fetchall()

        print("Tables Created:")
        for table in tables:
            print(f"  [OK] {table[0]}")

        print("")

        # Verify agent_status populated
        cursor.execute("""
            SELECT team, COUNT(*) as agent_count
            FROM agent_status
            GROUP BY team
            ORDER BY team
        """)

        team_counts = cursor.fetchall()

        print("Agent Status Populated:")
        for team, count in team_counts:
            print(f"  [OK] {team:15} {count} agents")

        print("")

        # Verify sample alert
        cursor.execute("""
            SELECT alert_type, title
            FROM alert_history
            ORDER BY sent_at DESC
            LIMIT 1
        """)

        alert = cursor.fetchone()
        if alert:
            print("Sample Alert:")
            print(f"  [OK] {alert[0]}: {alert[1]}")

        cursor.close()
        conn.close()

        print("")
        print("=" * 70)
        print("DEPLOYMENT COMPLETE")
        print("=" * 70)
        print("")
        print("Next steps:")
        print("  1. Test bot import: poetry run python -c \"from agent_factory.integrations.telegram import management_handlers; print('OK')\"")
        print("  2. Test bot locally (optional)")
        print("  3. Deploy to Render.com for 24/7 operation")
        print("")

        return True

    except Exception as e:
        print(f"[FAIL] Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = deploy_schema()
    sys.exit(0 if success else 1)
