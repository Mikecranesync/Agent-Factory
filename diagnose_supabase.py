"""
Diagnose Supabase Connection Issues

Tests:
1. DNS resolution
2. TCP connection
3. PostgreSQL authentication
4. API health check
"""

import os
import socket
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[INFO] Loaded .env file")
except ImportError:
    print("[WARN] python-dotenv not installed, using system environment only")

def test_dns_resolution():
    """Test if Supabase hostname resolves"""
    print("\n[TEST 1] DNS Resolution...")

    host = os.getenv("SUPABASE_DB_HOST", "db.mggqgrxwumnnujojndub.supabase.co")

    print(f"[INFO] Resolving: {host}")

    try:
        ip_addresses = socket.getaddrinfo(host, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)

        print(f"[OK] DNS resolved successfully")
        for addr in ip_addresses:
            print(f"  - {addr[4][0]}")

        return True

    except socket.gaierror as e:
        print(f"[FAIL] DNS resolution failed: {e}")
        print("[INFO] Possible causes:")
        print("  1. Supabase project deleted or paused")
        print("  2. Incorrect hostname in .env")
        print("  3. Network/firewall blocking DNS")
        print("  4. DNS server issues")
        return False


def test_tcp_connection():
    """Test TCP connection to PostgreSQL port"""
    print("\n[TEST 2] TCP Connection...")

    host = os.getenv("SUPABASE_DB_HOST", "db.mggqgrxwumnnujojndub.supabase.co")
    port = int(os.getenv("SUPABASE_DB_PORT", "5432"))

    print(f"[INFO] Connecting to: {host}:{port}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print("[OK] TCP connection successful")
            return True
        else:
            print(f"[FAIL] TCP connection failed (error code: {result})")
            print("[INFO] Port 5432 may be firewalled or service not running")
            return False

    except Exception as e:
        print(f"[FAIL] TCP connection error: {e}")
        return False


def test_postgresql_connection():
    """Test PostgreSQL authentication"""
    print("\n[TEST 3] PostgreSQL Connection...")

    try:
        import psycopg

        connection_string = (
            f"postgresql://{os.getenv('SUPABASE_DB_USER', 'postgres')}:"
            f"{os.getenv('SUPABASE_DB_PASSWORD')}@"
            f"{os.getenv('SUPABASE_DB_HOST')}:"
            f"{os.getenv('SUPABASE_DB_PORT', '5432')}/"
            f"{os.getenv('SUPABASE_DB_NAME', 'postgres')}"
            "?sslmode=require"
        )

        print("[INFO] Attempting PostgreSQL connection...")
        print(f"[INFO] Host: {os.getenv('SUPABASE_DB_HOST')}")
        print(f"[INFO] User: {os.getenv('SUPABASE_DB_USER', 'postgres')}")

        conn = psycopg.connect(connection_string, connect_timeout=10)

        # Test query
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0] == 1:
            print("[OK] PostgreSQL connection and query successful")
            return True
        else:
            print("[FAIL] Query returned unexpected result")
            return False

    except psycopg.OperationalError as e:
        print(f"[FAIL] PostgreSQL connection failed: {e}")
        print("[INFO] Check credentials and SSL requirements")
        return False

    except ImportError:
        print("[WARN] psycopg not installed - skipping PostgreSQL test")
        return None

    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_supabase_api():
    """Test Supabase REST API health"""
    print("\n[TEST 4] Supabase API Health...")

    supabase_url = os.getenv("SUPABASE_URL", "https://mggqgrxwumnnujojndub.supabase.co")

    print(f"[INFO] Checking API: {supabase_url}")

    try:
        import requests

        response = requests.get(f"{supabase_url}/rest/v1/", timeout=10)

        if response.status_code == 200:
            print("[OK] Supabase API is healthy")
            return True
        elif response.status_code == 401:
            print("[OK] Supabase API is up (401 = needs auth, which is expected)")
            return True
        else:
            print(f"[WARN] Supabase API returned status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"[FAIL] Cannot connect to Supabase API: {e}")
        print("[INFO] Project may be paused or deleted")
        return False

    except ImportError:
        print("[WARN] requests not installed - skipping API test")
        return None

    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def check_env_configuration():
    """Check .env configuration"""
    print("\n[CONFIG] Environment Variables...")

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_PASSWORD",
        "SUPABASE_DB_USER",
        "SUPABASE_DB_NAME",
        "SUPABASE_DB_PORT"
    ]

    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            if "PASSWORD" in var and len(value) > 3:
                masked_value = value[:3] + "*" * (len(value) - 3)
                print(f"[OK] {var}: {masked_value}")
            else:
                print(f"[OK] {var}: {value}")
        else:
            print(f"[MISSING] {var}")
            all_present = False

    return all_present


def main():
    """Run all diagnostic tests"""
    print("="*60)
    print("SUPABASE CONNECTION DIAGNOSTIC")
    print("="*60)

    # Check configuration
    config_ok = check_env_configuration()

    if not config_ok:
        print("\n[ERROR] Missing required environment variables")
        print("[ACTION] Check .env file for Supabase configuration")
        return 1

    # Run tests
    results = {
        "DNS Resolution": test_dns_resolution(),
        "TCP Connection": test_tcp_connection(),
        "PostgreSQL Connection": test_postgresql_connection(),
        "Supabase API": test_supabase_api()
    }

    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)

    for test_name, result in results.items():
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"

        print(f"{status} {test_name}")

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)

    print("-"*60)
    print(f"Passed: {passed} | Failed: {failed}")

    if failed == 0 and passed > 0:
        print("\n[OK] Supabase is reachable and operational")
        return 0
    elif failed > 0:
        print("\n[ACTION] Follow troubleshooting steps for failed tests")
        return 1
    else:
        print("\n[WARN] No tests completed - check dependencies")
        return 2


if __name__ == "__main__":
    sys.exit(main())
