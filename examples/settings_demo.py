"""
Settings Service Demo

Demonstrates how to use the Settings Service for runtime configuration.

Usage:
    poetry run python examples/settings_demo.py
"""

from agent_factory.core.settings_service import settings


def main():
    print("=" * 60)
    print("Settings Service Demo")
    print("=" * 60)
    print()

    # Display service status
    print(f"Service Status: {settings}")
    print()

    # Example 1: Get string settings
    print("Example 1: String Settings")
    print("-" * 40)
    model = settings.get("DEFAULT_MODEL", category="llm")
    print(f"LLM Default Model: {model}")
    print()

    # Example 2: Get boolean settings
    print("Example 2: Boolean Settings")
    print("-" * 40)
    use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")
    print(f"Use Hybrid Search: {use_hybrid}")
    print()

    # Example 3: Get integer settings
    print("Example 3: Integer Settings")
    print("-" * 40)
    batch_size = settings.get_int("BATCH_SIZE", default=50, category="memory")
    print(f"Memory Batch Size: {batch_size}")

    max_retries = settings.get_int("MAX_RETRIES", default=3, category="orchestration")
    print(f"Max Retries: {max_retries}")
    print()

    # Example 4: Get float settings
    print("Example 4: Float Settings")
    print("-" * 40)
    temperature = settings.get_float("DEFAULT_TEMPERATURE", default=0.7, category="llm")
    print(f"LLM Temperature: {temperature}")
    print()

    # Example 5: Get all settings by category
    print("Example 5: Get All Settings by Category")
    print("-" * 40)
    llm_settings = settings.get_all(category="llm")
    if llm_settings:
        for key, value in llm_settings.items():
            print(f"  {key}: {value}")
    else:
        print("  (No settings in database - using environment variables)")
    print()

    # Example 6: Fallback to environment variables
    print("Example 6: Environment Variable Fallback")
    print("-" * 40)
    import os
    os.environ["CUSTOM_SETTING"] = "from_environment"
    custom = settings.get("CUSTOM_SETTING", category="general")
    print(f"Custom Setting: {custom}")
    print("  (Loaded from environment variable)")
    print()

    # Example 7: Programmatically set a value (if database available)
    print("Example 7: Set Value Programmatically")
    print("-" * 40)
    if settings.client:
        success = settings.set(
            "DEMO_SETTING",
            "test_value",
            category="general",
            description="Demo setting created by example script"
        )
        if success:
            print("✓ Setting created in database")
            # Retrieve it
            value = settings.get("DEMO_SETTING", category="general")
            print(f"  Value: {value}")
        else:
            print("✗ Failed to create setting")
    else:
        print("  (Skipped - no database connection)")
    print()

    # Example 8: Reload settings from database
    print("Example 8: Reload Settings")
    print("-" * 40)
    if settings.client:
        settings.reload()
        print("✓ Settings reloaded from database")
    else:
        print("  (Skipped - no database connection)")
    print()

    # Summary
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print()
    print("Key Takeaways:")
    print("  1. Settings automatically fall back to environment variables")
    print("  2. Type conversion helpers: get_bool(), get_int(), get_float()")
    print("  3. Category-based organization (llm, memory, orchestration)")
    print("  4. Cache expires after 5 minutes (auto-reload)")
    print("  5. Can set values programmatically via set() method")
    print()
    print("Next Steps:")
    print("  - Run SQL migration: docs/supabase_migrations.sql")
    print("  - Add settings via Supabase UI or API")
    print("  - Use settings in your agent code")
    print()


if __name__ == "__main__":
    main()
