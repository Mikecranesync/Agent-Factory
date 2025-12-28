import sys
sys.path.insert(0, '.')

try:
    from agent_factory.integrations.telegram.public_auth import auth, admin_only, rate_limited
    print("public_auth OK")

    from agent_factory.integrations.telegram.rivet_pro_handlers import RIVETProHandlers
    print("rivet_pro_handlers OK")

    from agent_factory.integrations.telegram.tier0_handlers import TIER0Handlers
    print("tier0_handlers OK")

    from agent_factory.integrations.telegram.print_handlers import add_machine_command
    print("print_handlers OK")

    from agent_factory.integrations.telegram.manual_handlers import upload_manual_command
    print("manual_handlers OK")

    print("\nAll imports successful - ready to launch!")
except ImportError as e:
    print(f"Import error: {e}")
