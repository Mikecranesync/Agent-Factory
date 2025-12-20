#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Telegram bot handler initialization.
Identifies which handlers crash during import/init.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("Testing Telegram Bot Handler Initialization")
print("=" * 60)

# Test RIVET handlers
print("\n[1/5] Testing RIVET Pro handlers...")
try:
    from agent_factory.integrations.telegram.rivet_pro_handlers import RIVETProHandlers
    rivet = RIVETProHandlers()
    print("[OK] RIVET Pro: SUCCESS")
except Exception as e:
    print(f"[FAIL] RIVET Pro: {e}")
    import traceback
    traceback.print_exc()

# Test LangGraph handlers
print("\n[2/5] Testing LangGraph handlers...")
try:
    from agent_factory.integrations.telegram.langgraph_handlers import LangGraphHandlers
    lg = LangGraphHandlers()
    print("[OK] LangGraph: SUCCESS")
except Exception as e:
    print(f"[FAIL] LangGraph: {e}")

# Test Admin handlers
print("\n[3/5] Testing Admin handlers...")
try:
    from agent_factory.integrations.telegram.admin import AdminDashboard
    admin = AdminDashboard()
    print("[OK] Admin: SUCCESS")
except Exception as e:
    print(f"[FAIL] Admin: {e}")

# Test SCAFFOLD handlers
print("\n[4/5] Testing SCAFFOLD handlers...")
try:
    from agent_factory.integrations.telegram.scaffold_handlers import ScaffoldHandlers
    scaffold = ScaffoldHandlers(repo_root=project_root)
    print("[OK] SCAFFOLD: SUCCESS")
except Exception as e:
    print(f"[FAIL] SCAFFOLD: {e}")

# Test TIER 0 handlers
print("\n[5/5] Testing TIER 0.1 handlers...")
try:
    from agent_factory.integrations.telegram.tier0_handlers import TIER0Handlers
    from agent_factory.memory.storage import SupabaseMemoryStorage
    tier0 = TIER0Handlers(
        storage=SupabaseMemoryStorage(),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    print("[OK] TIER 0.1: SUCCESS")
except Exception as e:
    print(f"[FAIL] TIER 0.1: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
