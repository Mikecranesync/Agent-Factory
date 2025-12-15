#!/usr/bin/env python3
"""
Test Suite for VPS KB Integration

Tests the VPS KB Client and RIVET Pro Telegram handlers
with real VPS database queries.

Usage:
    poetry run python tests/test_vps_integration.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.rivet_pro.vps_kb_client import VPSKBClient


def test_health_check():
    """Test VPS health check"""
    print("\n" + "=" * 70)
    print("TEST 1: VPS Health Check")
    print("=" * 70)

    try:
        client = VPSKBClient()
        health = client.health_check()

        print(f"Status: {health.get('status')}")
        print(f"Database Connected: {health.get('database_connected')}")
        print(f"Atom Count: {health.get('atom_count')}")
        print(f"Last Ingestion: {health.get('last_ingestion')}")
        print(f"Ollama Available: {health.get('ollama_available')}")
        print(f"Response Time: {health.get('response_time_ms')}ms")

        if health.get('status') == 'healthy':
            print("\n✅ TEST PASSED: VPS is healthy")
            return True
        else:
            print(f"\n⚠️ TEST WARNING: VPS status is {health.get('status')}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_basic_query():
    """Test 1: Basic keyword search"""
    print("\n" + "=" * 70)
    print("TEST 2: Basic Query (Keyword Search)")
    print("=" * 70)

    try:
        client = VPSKBClient()
        atoms = client.query_atoms("ControlLogix", limit=3)

        print(f"Found {len(atoms)} atoms for 'ControlLogix'")

        if atoms:
            for i, atom in enumerate(atoms[:3], 1):
                print(f"\n{i}. {atom.get('title')}")
                print(f"   Type: {atom.get('atom_type')}")
                print(f"   Vendor: {atom.get('vendor')}")
                print(f"   Summary: {atom.get('summary', '')[:100]}...")

            print("\n✅ TEST PASSED: Basic query returned results")
            return True
        else:
            print("\n⚠️ TEST WARNING: No results found")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_equipment_search():
    """Test 2: Equipment-specific search"""
    print("\n" + "=" * 70)
    print("TEST 3: Equipment-Specific Search")
    print("=" * 70)

    try:
        client = VPSKBClient()
        atoms = client.search_by_equipment(
            equipment_type="plc",
            manufacturer="allen_bradley",
            limit=3
        )

        print(f"Found {len(atoms)} atoms for Allen-Bradley PLCs")

        if atoms:
            for i, atom in enumerate(atoms[:3], 1):
                print(f"\n{i}. {atom.get('title')}")
                print(f"   Vendor: {atom.get('vendor')}")
                print(f"   Product: {atom.get('product')}")

            print("\n✅ TEST PASSED: Equipment search returned results")
            return True
        else:
            print("\n⚠️ TEST WARNING: No results found")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_semantic_search():
    """Test 3: Semantic search with embeddings"""
    print("\n" + "=" * 70)
    print("TEST 4: Semantic Search (Embeddings)")
    print("=" * 70)

    try:
        client = VPSKBClient()
        atoms = client.query_atoms_semantic(
            query_text="How do I troubleshoot a motor that won't start?",
            limit=3,
            similarity_threshold=0.7
        )

        print(f"Found {len(atoms)} atoms with semantic search")

        if atoms:
            for i, atom in enumerate(atoms[:3], 1):
                similarity = atom.get('similarity', 0)
                print(f"\n{i}. {atom.get('title')} (similarity: {similarity:.2f})")
                print(f"   Type: {atom.get('atom_type')}")
                print(f"   Summary: {atom.get('summary', '')[:100]}...")

            print("\n✅ TEST PASSED: Semantic search returned results")
            return True
        else:
            print("\n⚠️ TEST WARNING: No results found (may fallback to keyword)")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_no_results():
    """Test 4: Query with no results"""
    print("\n" + "=" * 70)
    print("TEST 5: No Results Query")
    print("=" * 70)

    try:
        client = VPSKBClient()
        atoms = client.query_atoms("xyzabc123nonexistent", limit=3)

        if not atoms:
            print("No results found (as expected)")
            print("\n✅ TEST PASSED: Handled no results gracefully")
            return True
        else:
            print(f"Found {len(atoms)} atoms (unexpected)")
            print("\n⚠️ TEST WARNING: Expected no results")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_vps_down_fallback():
    """Test 5: VPS down scenario (simulated)"""
    print("\n" + "=" * 70)
    print("TEST 6: VPS Down Fallback")
    print("=" * 70)

    try:
        # Create client with invalid host to simulate VPS down
        import os
        original_host = os.getenv('VPS_KB_HOST')
        os.environ['VPS_KB_HOST'] = '1.1.1.1'  # Invalid host

        client = VPSKBClient()

        # This should fail gracefully
        try:
            atoms = client.query_atoms("test", limit=3)
            print(f"Fallback: Returned {len(atoms)} atoms (empty list expected)")

            if not atoms:
                print("\n✅ TEST PASSED: Handled VPS down gracefully")
                result = True
            else:
                print("\n⚠️ TEST WARNING: Should return empty list")
                result = False
        except Exception as query_error:
            print(f"Query raised exception: {query_error}")
            print("\n⚠️ TEST WARNING: Should handle gracefully, not raise")
            result = False

        # Restore original host
        if original_host:
            os.environ['VPS_KB_HOST'] = original_host

        return result

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("VPS KB INTEGRATION TEST SUITE")
    print("=" * 70)
    print(f"Testing VPS at: {VPSKBClient().config['host']}")
    print("=" * 70)

    tests = [
        ("Health Check", test_health_check),
        ("Basic Query", test_basic_query),
        ("Equipment Search", test_equipment_search),
        ("Semantic Search", test_semantic_search),
        ("No Results", test_no_results),
        ("VPS Down Fallback", test_vps_down_fallback),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    print("=" * 70)
    print(f"Total: {passed_count}/{total_count} tests passed")
    print("=" * 70)

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
