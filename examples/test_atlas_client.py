"""Manual validation script for Atlas CMMS integration.

This script tests all AtlasClient functionality against a live Atlas CMMS instance.
Run this after deploying Atlas locally with Docker.

Prerequisites:
    1. Atlas CMMS running on localhost:8080
    2. Docker Desktop started
    3. cd deploy/atlas && docker-compose up -d

Usage:
    python examples/test_atlas_client.py
"""

import asyncio
import sys
from datetime import datetime
from agent_factory.integrations.atlas import AtlasClient, atlas_config
from agent_factory.integrations.atlas.exceptions import (
    AtlasError,
    AtlasNotFoundError,
    AtlasConfigError
)


async def test_health_check(client: AtlasClient) -> bool:
    """Test Atlas health endpoint (no auth required)."""
    print("\n" + "=" * 70)
    print("TEST 1: Health Check (No Authentication)")
    print("=" * 70)

    try:
        health = await client.health_check()
        print(f"✓ Health check successful")
        print(f"  Status: {health.get('status', 'UNKNOWN')}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


async def test_authentication(client: AtlasClient) -> bool:
    """Test JWT authentication."""
    print("\n" + "=" * 70)
    print("TEST 2: Authentication")
    print("=" * 70)

    try:
        # Force authentication by clearing cache
        await client._token_cache.clear()

        # Authenticate
        token = await client._authenticate()
        print(f"✓ Authentication successful")
        print(f"  Token: {token[:20]}... (truncated)")
        print(f"  Token cached: {client._token_cache.is_valid}")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False


async def test_token_caching(client: AtlasClient) -> bool:
    """Test token caching and reuse."""
    print("\n" + "=" * 70)
    print("TEST 3: Token Caching")
    print("=" * 70)

    try:
        # First authentication
        await client._token_cache.clear()
        token1 = await client._authenticate()

        # Second request should reuse cached token
        token2 = await client._token_cache.get_token()

        if token1 == token2:
            print(f"✓ Token caching works")
            print(f"  Cached token reused successfully")
            return True
        else:
            print(f"✗ Token caching failed: tokens don't match")
            return False
    except Exception as e:
        print(f"✗ Token caching test failed: {e}")
        return False


async def test_create_work_order(client: AtlasClient) -> tuple[bool, str]:
    """Test creating a work order."""
    print("\n" + "=" * 70)
    print("TEST 4: Create Work Order")
    print("=" * 70)

    try:
        work_order_data = {
            "title": f"Test Work Order - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "description": "Created by AtlasClient validation script",
            "priority": "MEDIUM"
        }

        work_order = await client.create_work_order(work_order_data)
        work_order_id = work_order.get("id")

        print(f"✓ Work order created")
        print(f"  ID: {work_order_id}")
        print(f"  Title: {work_order.get('title')}")
        print(f"  Priority: {work_order.get('priority')}")
        return True, work_order_id
    except Exception as e:
        print(f"✗ Create work order failed: {e}")
        return False, None


async def test_get_work_order(client: AtlasClient, work_order_id: str) -> bool:
    """Test retrieving a work order by ID."""
    print("\n" + "=" * 70)
    print("TEST 5: Get Work Order")
    print("=" * 70)

    if not work_order_id:
        print("⊘ Skipped (no work order ID from previous test)")
        return False

    try:
        work_order = await client.get_work_order(work_order_id)
        print(f"✓ Work order retrieved")
        print(f"  ID: {work_order.get('id')}")
        print(f"  Title: {work_order.get('title')}")
        print(f"  Status: {work_order.get('status')}")
        return True
    except AtlasNotFoundError:
        print(f"✗ Work order not found: {work_order_id}")
        return False
    except Exception as e:
        print(f"✗ Get work order failed: {e}")
        return False


async def test_update_work_order(client: AtlasClient, work_order_id: str) -> bool:
    """Test updating a work order."""
    print("\n" + "=" * 70)
    print("TEST 6: Update Work Order")
    print("=" * 70)

    if not work_order_id:
        print("⊘ Skipped (no work order ID from previous test)")
        return False

    try:
        updates = {
            "priority": "HIGH",
            "description": "Updated by validation script - priority raised to HIGH"
        }

        work_order = await client.update_work_order(work_order_id, updates)
        print(f"✓ Work order updated")
        print(f"  ID: {work_order.get('id')}")
        print(f"  Priority: {work_order.get('priority')} (updated to HIGH)")
        return True
    except Exception as e:
        print(f"✗ Update work order failed: {e}")
        return False


async def test_list_work_orders(client: AtlasClient) -> bool:
    """Test listing work orders."""
    print("\n" + "=" * 70)
    print("TEST 7: List Work Orders")
    print("=" * 70)

    try:
        result = await client.list_work_orders(page=0, limit=5)
        work_orders = result.get("content", [])

        print(f"✓ Work orders listed")
        print(f"  Total found: {len(work_orders)}")
        print(f"  Page: {result.get('number', 0)}")
        print(f"  Total pages: {result.get('totalPages', 0)}")

        if work_orders:
            print(f"\n  Recent work orders:")
            for wo in work_orders[:3]:
                print(f"    - {wo.get('id')}: {wo.get('title')}")

        return True
    except Exception as e:
        print(f"✗ List work orders failed: {e}")
        return False


async def test_search_assets(client: AtlasClient) -> bool:
    """Test asset search."""
    print("\n" + "=" * 70)
    print("TEST 8: Search Assets")
    print("=" * 70)

    try:
        assets = await client.search_assets("pump", limit=5)

        print(f"✓ Asset search successful")
        print(f"  Assets found: {len(assets)}")

        if assets:
            print(f"\n  Matching assets:")
            for asset in assets[:3]:
                print(f"    - {asset.get('id')}: {asset.get('name')}")
        else:
            print(f"  (No assets match 'pump' - this is OK for empty database)")

        return True
    except Exception as e:
        print(f"✗ Asset search failed: {e}")
        return False


async def test_complete_work_order(client: AtlasClient, work_order_id: str) -> bool:
    """Test completing a work order."""
    print("\n" + "=" * 70)
    print("TEST 9: Complete Work Order")
    print("=" * 70)

    if not work_order_id:
        print("⊘ Skipped (no work order ID from previous test)")
        return False

    try:
        work_order = await client.complete_work_order(work_order_id)
        print(f"✓ Work order completed")
        print(f"  ID: {work_order.get('id')}")
        print(f"  Status: {work_order.get('status')}")
        return True
    except Exception as e:
        print(f"✗ Complete work order failed: {e}")
        return False


async def test_error_handling(client: AtlasClient) -> bool:
    """Test error handling for non-existent resource."""
    print("\n" + "=" * 70)
    print("TEST 10: Error Handling (404)")
    print("=" * 70)

    try:
        # Try to get non-existent work order
        await client.get_work_order("NONEXISTENT-ID-999")
        print(f"✗ Error handling failed: should have raised AtlasNotFoundError")
        return False
    except AtlasNotFoundError as e:
        print(f"✓ Error handling works correctly")
        print(f"  Caught AtlasNotFoundError: {e.message}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


async def run_validation():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("ATLAS CMMS CLIENT VALIDATION")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Base URL: {atlas_config.atlas_base_url}")
    print(f"  Email: {atlas_config.atlas_email}")
    print(f"  Timeout: {atlas_config.atlas_timeout}s")
    print(f"  Max Retries: {atlas_config.atlas_max_retries}")
    print(f"  Enabled: {atlas_config.atlas_enabled}")

    # Validate configuration
    config_errors = atlas_config.validate_config()
    if config_errors:
        print(f"\n✗ Configuration errors:")
        for error in config_errors:
            print(f"  - {error}")
        return False

    results = {}
    work_order_id = None

    try:
        async with AtlasClient() as client:
            # Run tests in sequence
            results["health"] = await test_health_check(client)
            results["auth"] = await test_authentication(client)
            results["token_cache"] = await test_token_caching(client)

            success, wo_id = await test_create_work_order(client)
            results["create_wo"] = success
            work_order_id = wo_id

            results["get_wo"] = await test_get_work_order(client, work_order_id)
            results["update_wo"] = await test_update_work_order(client, work_order_id)
            results["list_wo"] = await test_list_work_orders(client)
            results["search_assets"] = await test_search_assets(client)
            results["complete_wo"] = await test_complete_work_order(client, work_order_id)
            results["error_handling"] = await test_error_handling(client)

    except AtlasConfigError as e:
        print(f"\n✗ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name:20s} {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL TESTS PASSED - Atlas integration is working correctly!")
        return True
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED - Review errors above")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
