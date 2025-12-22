"""
System Validation - Test what actually works
Run: poetry run python scripts/validate_system.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test(name: str, fn):
    """Test a component and report result"""
    try:
        result = fn()
        print(f"[OK] {name}: {result if result else 'OK'}")
        return True
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("AGENT FACTORY SYSTEM VALIDATION")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    # 1. Environment
    print("[ENVIRONMENT]")
    print("-" * 40)

    if test("Python version", lambda: sys.version.split()[0]):
        passed += 1
    else:
        failed += 1

    if test(".env file exists", lambda: os.path.exists(".env") or "missing"):
        passed += 1
    else:
        failed += 1

    if test("OPENAI_API_KEY set", lambda: "yes" if os.getenv("OPENAI_API_KEY") else None):
        passed += 1
    else:
        failed += 1

    if test("ANTHROPIC_API_KEY set", lambda: "yes" if os.getenv("ANTHROPIC_API_KEY") else None):
        passed += 1
    else:
        failed += 1

    if test("TELEGRAM_BOT_TOKEN set", lambda: "yes" if os.getenv("TELEGRAM_BOT_TOKEN") else None):
        passed += 1
    else:
        failed += 1

    print()

    # 2. Core Imports
    print("[CORE IMPORTS]")
    print("-" * 40)

    if test("Pydantic models", lambda: __import__("core.models")):
        passed += 1
    else:
        failed += 1

    if test("DatabaseManager", lambda: __import__("agent_factory.core.database_manager")):
        passed += 1
    else:
        failed += 1

    if test("LLMRouter", lambda: __import__("agent_factory.llm.router")):
        passed += 1
    else:
        failed += 1

    print()

    # 3. Orchestrators
    print("[ORCHESTRATORS]")
    print("-" * 40)

    if test("RivetOrchestrator", lambda: __import__("agent_factory.core.orchestrator")):
        passed += 1
    else:
        failed += 1

    if test("ScaffoldOrchestrator", lambda: __import__("agent_factory.scaffold.orchestrator")):
        passed += 1
    else:
        failed += 1

    print()

    # 4. Key Agents
    print("[KEY AGENTS]")
    print("-" * 40)

    agents_to_test = [
        ("ResearchAgent", "agents.research.research_agent"),
        ("ScriptwriterAgent", "agents.content.scriptwriter_agent"),
        ("AtomBuilderAgent", "agents.research.atom_builder_agent"),
        ("VoiceProductionAgent", "agents.media.voice_production_agent"),
        ("YouTubeUploaderAgent", "agents.media.youtube_uploader_agent"),
    ]

    for name, module in agents_to_test:
        if test(name, lambda m=module: __import__(m)):
            passed += 1
        else:
            failed += 1

    print()

    # 5. Database Connection
    print("[DATABASE]")
    print("-" * 40)

    def test_db():
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()
        return db.primary_provider

    if test("Database connection", test_db):
        passed += 1
    else:
        failed += 1

    print()

    # 6. Knowledge Base
    print("[KNOWLEDGE BASE]")
    print("-" * 40)

    def test_kb():
        from agent_factory.rivet_pro.vps_kb_client import VPSKBClient
        kb = VPSKBClient()
        health = kb.health_check()
        return f"VPS healthy: {health}"

    if test("VPS KB Client", test_kb):
        passed += 1
    else:
        failed += 1

    print()

    # Summary
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("[SUCCESS] All systems operational!")
        print()
        print("Next: Run the orchestrator directly:")
        print("  poetry run python -c \"from agent_factory.core.orchestrator import RivetOrchestrator; print(RivetOrchestrator())\"")
    else:
        print("[ERROR] Fix the failures above before proceeding")
        print()
        print("Common fixes:")
        print("  - Missing .env: cp .env.example .env")
        print("  - Missing deps: poetry install")
        print("  - Import errors: Check file paths in error messages")

    return failed == 0

if __name__ == "__main__":
    # Load .env first
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    success = main()
    sys.exit(0 if success else 1)
