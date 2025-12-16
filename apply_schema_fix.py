"""
Apply Schema Fix to Neon Database - ACTUAL EXECUTION

This script directly connects to Neon and fixes the schema constraint.
No dry-run, no mock - real database operations.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Apply schema fix to Neon"""
    print("="*60)
    print("APPLYING SCHEMA FIX TO NEON DATABASE")
    print("="*60)

    # Import DatabaseManager
    try:
        from agent_factory.core.database_manager import DatabaseManager
        print("[OK] Imports successful")
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        sys.exit(1)

    # Initialize DatabaseManager
    try:
        db = DatabaseManager()
        print(f"[OK] DatabaseManager initialized")
        print(f"[INFO] Primary provider: {db.primary_provider}")
        print(f"[INFO] Available providers: {list(db.providers.keys())}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize DatabaseManager: {e}")
        sys.exit(1)

    # Check Neon health
    print("\n[STEP 1] Checking Neon health...")
    if 'neon' not in db.providers:
        print("[ERROR] Neon provider not configured")
        sys.exit(1)

    neon_provider = db.providers['neon']
    is_healthy = neon_provider.health_check()

    if not is_healthy:
        print("[ERROR] Neon is unhealthy - cannot apply fix")
        print("[INFO] Check network connectivity and credentials")
        sys.exit(1)

    print("[OK] Neon is healthy")

    # Switch to Neon
    print("\n[STEP 2] Switching to Neon provider...")
    db.set_provider('neon')
    print("[OK] Using Neon for all operations")

    # Check current constraint
    print("\n[STEP 3] Checking current constraint...")
    try:
        result = db.execute_query("""
            SELECT
                conname AS constraint_name,
                pg_get_constraintdef(oid) AS constraint_definition
            FROM pg_constraint
            WHERE conrelid = 'session_memories'::regclass
              AND conname LIKE '%memory_type%'
        """, fetch_mode="all")

        if result:
            for row in result:
                constraint_name, constraint_def = row
                print(f"[INFO] Current constraint: {constraint_name}")
                print(f"[INFO] Definition: {constraint_def}")

                if 'session_metadata' in constraint_def:
                    print("[OK] Constraint already includes 'session_metadata' - no fix needed")
                    return 0
        else:
            print("[WARN] No memory_type constraint found - will create new one")

    except Exception as e:
        print(f"[WARN] Could not check constraint (table may not exist): {e}")

    # Apply the fix
    print("\n[STEP 4] Applying schema fix...")

    fix_sql = """
-- Drop existing constraint if exists
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

    try:
        db.execute_query(fix_sql, fetch_mode="none")
        print("[OK] Schema constraint updated successfully")
    except Exception as e:
        print(f"[ERROR] Failed to apply fix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verify the fix
    print("\n[STEP 5] Verifying fix...")
    try:
        result = db.execute_query("""
            SELECT
                conname AS constraint_name,
                pg_get_constraintdef(oid) AS constraint_definition
            FROM pg_constraint
            WHERE conrelid = 'session_memories'::regclass
              AND conname LIKE '%memory_type%'
        """, fetch_mode="all")

        if result:
            for row in result:
                constraint_name, constraint_def = row
                print(f"[INFO] New constraint: {constraint_name}")
                print(f"[INFO] Definition: {constraint_def}")

                if 'session_metadata' in constraint_def:
                    print("[OK] Constraint now includes 'session_metadata'")
                else:
                    print("[ERROR] Constraint does not include 'session_metadata'")
                    return 1
        else:
            print("[ERROR] Constraint not found after fix")
            return 1

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return 1

    # Test insert
    print("\n[STEP 6] Testing session insert...")
    try:
        from agent_factory.memory.storage import PostgresMemoryStorage
        from agent_factory.memory.session import Session

        storage = PostgresMemoryStorage()

        # Create test session
        session = Session(user_id="schema_test_user", storage=storage)
        session.add_user_message("Test message after schema fix")
        session.add_assistant_message("Test response")

        # Save
        storage.save_session(session)
        print(f"[OK] Session saved: {session.session_id}")

        # Load
        loaded = storage.load_session(session.session_id)
        if loaded:
            print(f"[OK] Session loaded: {len(loaded.history.get_messages())} messages")
        else:
            print("[ERROR] Failed to load session")
            return 1

        # Cleanup
        storage.delete_session(session.session_id)
        print("[OK] Test session deleted")

    except Exception as e:
        print(f"[ERROR] Session test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "="*60)
    print("SCHEMA FIX COMPLETE - NEON DATABASE OPERATIONAL")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
