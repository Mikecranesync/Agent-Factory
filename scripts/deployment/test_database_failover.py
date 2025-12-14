#!/usr/bin/env python3
"""
Database Failover Testing Script

Tests database connection failover between Neon, Supabase, and Railway

Usage:
    python scripts/deployment/test_database_failover.py

This script:
1. Tests connection to all database providers
2. Verifies knowledge base accessibility
3. Tests failover logic
4. Reports health status of each provider

Providers tested:
- Neon PostgreSQL (primary)
- Supabase (backup)
- Railway PostgreSQL (tertiary, if configured)
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseFailoverTester:
    """Test database failover capabilities"""

    def __init__(self):
        self.providers = {
            "neon": os.getenv("NEON_DB_URL"),
            "supabase": os.getenv("SUPABASE_DB_URL"),
            "railway": os.getenv("RAILWAY_DB_URL")
        }

        self.results = {}

    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}\n")

    def test_connection(self, provider_name: str, db_url: str) -> dict:
        """
        Test connection to a database provider

        Returns:
            dict with status, response_time, atom_count
        """
        if not db_url:
            return {
                "status": "NOT_CONFIGURED",
                "message": "Database URL not set",
                "response_time_ms": None,
                "atom_count": None
            }

        try:
            import psycopg

            start_time = time.time()

            # Attempt connection with 10-second timeout
            with psycopg.connect(db_url, connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    # Test query
                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms;")
                    atom_count = cur.fetchone()[0]

                    # Check embeddings
                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms WHERE embedding IS NOT NULL;")
                    with_embeddings = cur.fetchone()[0]

                    elapsed_ms = (time.time() - start_time) * 1000

                    return {
                        "status": "HEALTHY",
                        "message": "Connection successful",
                        "response_time_ms": elapsed_ms,
                        "atom_count": atom_count,
                        "embeddings_count": with_embeddings,
                        "coverage": with_embeddings / max(atom_count, 1)
                    }

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "status": "ERROR",
                "message": str(e),
                "response_time_ms": elapsed_ms,
                "atom_count": None
            }

    def test_all_providers(self):
        """Test all configured database providers"""
        self.print_header("DATABASE FAILOVER TEST")

        print(f"Testing {len(self.providers)} database provider(s)")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for provider_name, db_url in self.providers.items():
            print(f"\n[{provider_name.upper()}] Testing connection...")

            if not db_url:
                print(f"  Status: NOT CONFIGURED")
                print(f"  Environment variable not set")
                self.results[provider_name] = {
                    "status": "NOT_CONFIGURED"
                }
                continue

            result = self.test_connection(provider_name, db_url)
            self.results[provider_name] = result

            # Print results
            status = result["status"]
            print(f"  Status: {status}")

            if status == "HEALTHY":
                print(f"  Response Time: {result['response_time_ms']:.0f}ms")
                print(f"  Atoms: {result['atom_count']:,}")
                print(f"  Embeddings: {result['embeddings_count']:,} ({result['coverage']*100:.1f}%)")
                print(f"  Result: PASS")
            elif status == "ERROR":
                print(f"  Error: {result['message']}")
                print(f"  Response Time: {result['response_time_ms']:.0f}ms")
                print(f"  Result: FAIL")
            else:
                print(f"  Message: {result['message']}")
                print(f"  Result: SKIP")

    def test_failover_logic(self):
        """Test failover priority order"""
        self.print_header("FAILOVER LOGIC TEST")

        print("Testing failover priority: Neon → Supabase → Railway\n")

        # Check priority order
        priority = ["neon", "supabase", "railway"]
        working_providers = []

        for provider in priority:
            result = self.results.get(provider, {})
            status = result.get("status")

            if status == "HEALTHY":
                working_providers.append(provider)
                print(f"  [{provider.upper()}] Available (priority {len(working_providers)})")
            elif status == "NOT_CONFIGURED":
                print(f"  [{provider.upper()}] Not configured (skip)")
            else:
                print(f"  [{provider.upper()}] Unavailable")

        print()

        if working_providers:
            primary = working_providers[0]
            print(f"PRIMARY DATABASE: {primary.upper()}")

            if len(working_providers) > 1:
                backups = ", ".join([p.upper() for p in working_providers[1:]])
                print(f"BACKUP DATABASE(S): {backups}")
                print(f"\nFailover capability: ENABLED")
            else:
                print(f"\nFailover capability: NO BACKUP (single provider)")
                print(f"RECOMMENDATION: Configure Supabase as backup")
        else:
            print("ERROR: No working database providers!")
            print("RECOMMENDATION: Fix database connections immediately")

    def test_failover_simulation(self):
        """Simulate failover scenario"""
        self.print_header("FAILOVER SIMULATION")

        print("Simulating Neon database outage...\n")

        # Simulate Neon failure
        neon_result = self.results.get("neon", {})
        supabase_result = self.results.get("supabase", {})

        print("Scenario: Neon database becomes unavailable")
        print()

        if supabase_result.get("status") == "HEALTHY":
            print("  [1] Detect Neon failure")
            print("  [2] Switch DATABASE_PROVIDER to 'supabase'")
            print("  [3] Reconnect to Supabase")
            print(f"  [4] Knowledge base accessible: {supabase_result['atom_count']:,} atoms")
            print()
            print("RESULT: Failover successful! Bot continues operating.")
        elif supabase_result.get("status") == "NOT_CONFIGURED":
            print("  [1] Detect Neon failure")
            print("  [2] Attempt Supabase failover")
            print("  [3] ERROR: Supabase not configured")
            print()
            print("RESULT: Failover FAILED. Bot will be offline.")
            print("RECOMMENDATION: Configure SUPABASE_URL in environment")
        else:
            print("  [1] Detect Neon failure")
            print("  [2] Attempt Supabase failover")
            print("  [3] ERROR: Supabase also unavailable")
            print()
            print("RESULT: Failover FAILED. Both databases down.")
            print("RECOMMENDATION: Contact database provider support")

    def print_summary(self):
        """Print test summary"""
        self.print_header("FAILOVER TEST SUMMARY")

        # Count results
        healthy = sum(1 for r in self.results.values() if r.get("status") == "HEALTHY")
        errors = sum(1 for r in self.results.values() if r.get("status") == "ERROR")
        not_configured = sum(1 for r in self.results.values() if r.get("status") == "NOT_CONFIGURED")

        print(f"Providers Tested:     {len(self.results)}")
        print(f"Healthy:              {healthy}")
        print(f"Errors:               {errors}")
        print(f"Not Configured:       {not_configured}")
        print()

        if healthy >= 2:
            print("STATUS: EXCELLENT")
            print("  Multiple database providers available")
            print("  Failover capability fully operational")
        elif healthy == 1:
            print("STATUS: ACCEPTABLE")
            print("  Single database provider available")
            print("  Recommend configuring backup for failover")
        else:
            print("STATUS: CRITICAL")
            print("  No working database providers!")
            print("  Fix database connections immediately")

        print()
        print("Recommendations:")

        # Neon check
        neon_status = self.results.get("neon", {}).get("status")
        if neon_status != "HEALTHY":
            print("  - Fix Neon connection (primary database)")

        # Supabase check
        supabase_status = self.results.get("supabase", {}).get("status")
        if supabase_status == "NOT_CONFIGURED":
            print("  - Configure Supabase as backup (SUPABASE_URL)")
        elif supabase_status == "ERROR":
            print("  - Fix Supabase connection (backup database)")

        # Railway check
        railway_status = self.results.get("railway", {}).get("status")
        if railway_status == "NOT_CONFIGURED":
            print("  - (Optional) Configure Railway as tertiary backup")

        if healthy >= 2:
            print("  - No action needed - failover ready!")

    def run_all_tests(self):
        """Run complete failover test suite"""
        print("="*60)
        print("DATABASE FAILOVER TESTING")
        print("="*60)
        print()
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test all providers
        self.test_all_providers()

        # Test failover logic
        self.test_failover_logic()

        # Simulate failover
        self.test_failover_simulation()

        # Summary
        self.print_summary()

        # Return success if at least one provider healthy
        healthy_count = sum(1 for r in self.results.values() if r.get("status") == "HEALTHY")
        return healthy_count > 0


def main():
    print("\nDatabase Failover Test")
    print("This script tests connectivity to all configured database providers\n")

    tester = DatabaseFailoverTester()
    success = tester.run_all_tests()

    print()
    print("="*60)
    print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
