"""
Fix Schema Constraints Across All Providers

Automatically fixes the session_memories memory_type CHECK constraint
on all configured database providers (Supabase, Railway, Neon).

Run:
    poetry run python scripts/ops/fix_schema_constraints.py

Options:
    --provider <name>    Fix only specific provider (supabase, railway, neon)
    --dry-run            Show what would be done without making changes
    --verify             Verify constraint after fixing
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# SQL to fix the constraint
FIX_SQL = """
-- Drop existing constraint
ALTER TABLE session_memories
DROP CONSTRAINT IF EXISTS session_memories_memory_type_check;

-- Add updated constraint with all allowed values
ALTER TABLE session_memories
ADD CONSTRAINT session_memories_memory_type_check
CHECK (memory_type IN (
    'session_metadata',
    'message_user',
    'message_assistant',
    'message_system',
    'context',
    'action',
    'issue',
    'decision',
    'log'
));
"""

# SQL to verify the constraint
VERIFY_SQL = """
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'session_memories'::regclass
  AND conname LIKE '%memory_type%';
"""


def fix_provider(provider_name: str, db_manager, dry_run: bool = False) -> bool:
    """
    Fix schema constraint for a specific provider.

    Args:
        provider_name: Name of provider (supabase, railway, neon)
        db_manager: DatabaseManager instance
        dry_run: If True, only show what would be done

    Returns:
        True if successful, False otherwise
    """
    print(f"\n[INFO] Fixing schema constraint for {provider_name}...")

    try:
        # Check if provider is configured
        if provider_name not in db_manager.providers:
            print(f"[SKIP] Provider '{provider_name}' not configured")
            return True

        # Check health first
        provider = db_manager.providers[provider_name]
        if not provider.health_check():
            print(f"[ERROR] Provider '{provider_name}' is unhealthy - cannot apply fix")
            return False

        if dry_run:
            print(f"[DRY-RUN] Would execute on {provider_name}:")
            print(FIX_SQL)
            return True

        # Apply the fix
        db_manager.set_provider(provider_name)

        # Execute the fix SQL
        db_manager.execute_query(FIX_SQL, fetch_mode="none")

        print(f"[OK] Schema constraint fixed for {provider_name}")

        # Verify the fix
        result = db_manager.execute_query(VERIFY_SQL, fetch_mode="all")

        if result:
            for row in result:
                constraint_name, constraint_def = row
                print(f"[INFO] Constraint: {constraint_name}")
                print(f"[INFO] Definition: {constraint_def}")

                # Check if session_metadata is in the constraint
                if 'session_metadata' in constraint_def:
                    print(f"[OK] Constraint includes 'session_metadata'")
                else:
                    print(f"[WARN] Constraint may not include 'session_metadata'")
        else:
            print(f"[WARN] No memory_type constraint found (may not exist yet)")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to fix {provider_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fix schema constraints across providers")
    parser.add_argument("--provider", help="Fix only specific provider (supabase, railway, neon)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--verify", action="store_true", help="Verify constraint after fixing")

    args = parser.parse_args()

    print("="*60)
    print("SCHEMA CONSTRAINT FIX - session_memories.memory_type")
    print("="*60)

    # Initialize DatabaseManager
    try:
        from agent_factory.core.database_manager import DatabaseManager

        db = DatabaseManager()

        print(f"\n[INFO] Configured providers: {list(db.providers.keys())}")
        print(f"[INFO] Primary provider: {db.primary_provider}")
        print(f"[INFO] Dry run: {args.dry_run}")

    except Exception as e:
        print(f"[ERROR] Failed to initialize DatabaseManager: {e}")
        sys.exit(1)

    # Determine which providers to fix
    if args.provider:
        providers_to_fix = [args.provider]
    else:
        providers_to_fix = list(db.providers.keys())

    print(f"\n[INFO] Will fix providers: {providers_to_fix}")

    # Fix each provider
    results = {}
    for provider_name in providers_to_fix:
        success = fix_provider(provider_name, db, dry_run=args.dry_run)
        results[provider_name] = success

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for provider_name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {provider_name}")

    print("-"*60)
    print(f"Total: {total} | Success: {passed} | Failed: {failed}")

    if failed == 0:
        print("[OK] All providers fixed successfully")
        if not args.dry_run:
            print("\n[NEXT] Run verification: poetry run python scripts/ops/verify_memory_deployment.py")
        return 0
    else:
        print(f"[ERROR] {failed} provider(s) failed - see errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
