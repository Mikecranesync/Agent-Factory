"""
Deploy RIVET Pro Database Schema to Supabase/Neon/Railway

This script deploys the complete RIVET Pro schema (5 tables + helper functions)
to the configured PostgreSQL database.

Usage:
    poetry run python scripts/deploy_rivet_pro_schema.py [--provider supabase|neon]

Environment Variables Required:
    - SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD (if using Supabase)
    - NEON_DB_URL (if using Neon)
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Configure UTF-8 output for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()


def get_db_connection(provider="supabase"):
    """
    Get database connection based on provider.

    Args:
        provider: Database provider (supabase or neon)

    Returns:
        psycopg2 connection object
    """
    if provider == "supabase":
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_DB_HOST"),
            port=os.getenv("SUPABASE_DB_PORT", "5432"),
            database=os.getenv("SUPABASE_DB_NAME", "postgres"),
            user=os.getenv("SUPABASE_DB_USER", "postgres"),
            password=os.getenv("SUPABASE_DB_PASSWORD"),
        )
    elif provider == "neon":
        conn = psycopg2.connect(os.getenv("NEON_DB_URL"))
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return conn


def deploy_schema(provider="supabase"):
    """
    Deploy RIVET Pro schema to database.

    Args:
        provider: Database provider (supabase or neon)
    """
    # Read schema file
    schema_path = Path(__file__).parent.parent / "docs" / "database" / "rivet_pro_schema.sql"

    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False

    print(f"📄 Reading schema from: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # For non-Supabase providers, remove RLS policies (they use auth.uid() which is Supabase-specific)
    if provider != "supabase":
        print(f"⚙️ Removing Supabase-specific RLS policies for {provider.upper()}...")
        # Find the RLS section and remove it
        rls_start = schema_sql.find("-- Enable RLS on all tables")
        if rls_start != -1:
            # Find the end of RLS section (before SEED DATA)
            rls_end = schema_sql.find("-- =============================================================================\n-- SEED DATA", rls_start)
            if rls_end != -1:
                schema_sql = schema_sql[:rls_start] + schema_sql[rls_end:]
                print(f"✅ RLS policies removed (application-level auth will be used)")

    print(f"📊 Schema size: {len(schema_sql)} characters, {len(schema_sql.splitlines())} lines")

    # Connect to database
    print(f"🔌 Connecting to {provider.upper()} database...")
    try:
        conn = get_db_connection(provider)
        cursor = conn.cursor()
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Execute schema
    print(f"🚀 Deploying RIVET Pro schema...")
    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Schema deployed successfully")
    except Exception as e:
        conn.rollback()
        print(f"❌ Deployment failed: {e}")
        cursor.close()
        conn.close()
        return False

    # Verify tables created
    print("\n🔍 Verifying tables...")
    tables_to_check = [
        "user_subscriptions",
        "troubleshooting_sessions",
        "expert_profiles",
        "expert_bookings",
        "conversion_events"
    ]

    all_tables_exist = True
    for table in tables_to_check:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table,))
        exists = cursor.fetchone()[0]
        status = "✅" if exists else "❌"
        print(f"{status} Table: {table}")
        if not exists:
            all_tables_exist = False

    # Verify helper functions
    print("\n🔍 Verifying helper functions...")
    functions_to_check = [
        "get_user_limits",
        "increment_question_count",
        "reset_daily_question_counts",
        "get_available_experts",
        "get_rivet_pro_metrics"
    ]

    all_functions_exist = True
    for func in functions_to_check:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname = %s
                AND n.nspname = 'public'
            );
        """, (func,))
        exists = cursor.fetchone()[0]
        status = "✅" if exists else "❌"
        print(f"{status} Function: {func}()")
        if not exists:
            all_functions_exist = False

    # Test a helper function
    if all_functions_exist:
        print("\n🧪 Testing helper function: get_user_limits()...")
        try:
            cursor.execute("SELECT get_user_limits('test_user_123');")
            result = cursor.fetchone()[0]
            print(f"✅ Function returned: {result}")
        except Exception as e:
            print(f"⚠️ Function test failed (expected if user doesn't exist): {e}")

    # Close connection
    cursor.close()
    conn.close()

    # Final summary
    print("\n" + "="*60)
    if all_tables_exist and all_functions_exist:
        print("✅ RIVET Pro Schema Deployment: SUCCESS")
        print(f"📊 5 tables created")
        print(f"⚙️ 5 helper functions created")
        print(f"🎯 Database: {provider.upper()}")
        print("\n🚀 RIVET Pro is ready for integration!")
        return True
    else:
        print("⚠️ RIVET Pro Schema Deployment: PARTIAL SUCCESS")
        print("Some tables or functions may not have been created.")
        print("Check the output above for details.")
        return False


if __name__ == "__main__":
    # Parse command line arguments
    provider = "supabase"
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--provider", "-p"]:
            provider = sys.argv[2] if len(sys.argv) > 2 else "supabase"
        else:
            provider = sys.argv[1]

    print("="*60)
    print("🚀 RIVET Pro Schema Deployment Script")
    print("="*60)
    print(f"Target: {provider.upper()}")
    print()

    success = deploy_schema(provider)
    sys.exit(0 if success else 1)
