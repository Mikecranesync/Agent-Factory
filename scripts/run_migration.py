"""
Run database migrations for Agent Factory

Usage:
    poetry run python scripts/run_migration.py <migration_number>
    poetry run python scripts/run_migration.py 001  # Run specific migration
    poetry run python scripts/run_migration.py all  # Run all pending migrations
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure UTF-8 for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from agent_factory.rivet_pro.database import RIVETProDatabase


def run_migration(db: RIVETProDatabase, migration_file: Path) -> bool:
    """
    Run a single migration file.

    Args:
        db: Database instance
        migration_file: Path to SQL migration file

    Returns:
        True if successful, False otherwise
    """
    print(f"📄 Running migration: {migration_file.name}")

    try:
        # Read migration SQL
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Execute migration
        import psycopg2
        cursor = db.conn.cursor()
        cursor.execute(sql)
        db.conn.commit()
        cursor.close()

        print(f"✅ Migration {migration_file.name} completed successfully")
        return True

    except Exception as e:
        print(f"❌ Migration {migration_file.name} failed: {e}")
        db.conn.rollback()
        return False


def get_migration_files(migrations_dir: Path) -> list:
    """Get all migration files sorted by number"""
    files = list(migrations_dir.glob("*.sql"))
    return sorted(files, key=lambda f: f.name)


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_number|all>")
        print("\nExamples:")
        print("  python run_migration.py 001")
        print("  python run_migration.py all")
        sys.exit(1)

    migration_arg = sys.argv[1]

    # Get migrations directory
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / "docs" / "database" / "migrations"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Connect to database
    print("🔌 Connecting to database...")
    db = RIVETProDatabase()
    print(f"✅ Connected to {db.provider.upper()}")

    # Get migration files
    all_migrations = get_migration_files(migrations_dir)

    if not all_migrations:
        print("⚠️ No migration files found")
        sys.exit(0)

    # Determine which migrations to run
    if migration_arg == "all":
        migrations_to_run = all_migrations
        print(f"\n📦 Running {len(migrations_to_run)} migrations...")
    else:
        # Find specific migration
        matching = [m for m in all_migrations if migration_arg in m.name]
        if not matching:
            print(f"❌ Migration {migration_arg} not found")
            print(f"\nAvailable migrations:")
            for m in all_migrations:
                print(f"  - {m.name}")
            sys.exit(1)
        migrations_to_run = matching
        print(f"\n📦 Running migration: {migrations_to_run[0].name}")

    # Run migrations
    print("="*60)
    success_count = 0
    for migration_file in migrations_to_run:
        if run_migration(db, migration_file):
            success_count += 1
        print()

    # Summary
    print("="*60)
    if success_count == len(migrations_to_run):
        print(f"✅ All {success_count} migrations completed successfully")
    else:
        failed = len(migrations_to_run) - success_count
        print(f"⚠️ {success_count} succeeded, {failed} failed")

    db.close()


if __name__ == "__main__":
    main()
