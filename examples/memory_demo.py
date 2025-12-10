"""
Memory System Demo - Consolidated API

Demonstrates the unified memory system with multiple storage backends.

Usage:
    poetry run python examples/memory_demo.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def demo_in_memory():
    """Demo 1: InMemoryStorage (fast, ephemeral)"""
    print("\n" + "=" * 60)
    print("DEMO 1: InMemoryStorage (Development/Testing)")
    print("=" * 60)

    from agent_factory.memory import Session, InMemoryStorage

    # Create session with in-memory storage
    storage = InMemoryStorage()
    session = Session(user_id="alice", storage=storage)

    # Add conversation
    session.add_user_message("What's the capital of France?")
    session.add_assistant_message("The capital of France is Paris.")
    session.save()

    # Load session
    loaded = Session.load(session.session_id, storage=storage)
    print(f"Session ID: {session.session_id}")
    print(f"Messages: {len(loaded)}")
    print(f"User: {loaded.user_id}")

    for msg in loaded.get_recent_messages():
        print(f"  [{msg.role}] {msg.content}")


def demo_sqlite():
    """Demo 2: SQLiteStorage (persistent, local)"""
    print("\n" + "=" * 60)
    print("DEMO 2: SQLiteStorage (Single-User Apps)")
    print("=" * 60)

    from agent_factory.memory import Session, SQLiteStorage

    # Create session with SQLite storage
    db_path = "demo_sessions.db"
    storage = SQLiteStorage(db_path)
    session = Session(user_id="bob", storage=storage)

    # Add conversation with metadata
    session.add_user_message("Tell me about Agent Factory", metadata={"intent": "question"})
    session.add_assistant_message(
        "Agent Factory is a framework for building multi-agent AI systems.",
        metadata={"confidence": 0.95}
    )
    session.set_metadata("topic", "agent_factory")
    session.save()

    # Load in new session
    loaded = Session.load(session.session_id, storage=storage)
    print(f"Session ID: {session.session_id}")
    print(f"Messages: {len(loaded)}")
    print(f"Topic: {loaded.get_metadata('topic')}")

    for msg in loaded.get_recent_messages():
        confidence = msg.metadata.get("confidence") if msg.metadata else None
        print(f"  [{msg.role}] {msg.content}")
        if confidence:
            print(f"    Confidence: {confidence}")

    # Cleanup
    storage.delete_session(session.session_id)
    os.remove(db_path)


def demo_supabase():
    """Demo 3: SupabaseMemoryStorage (cloud, production)"""
    print("\n" + "=" * 60)
    print("DEMO 3: SupabaseMemoryStorage (Production Multi-User)")
    print("=" * 60)

    # Check if credentials available
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("[SKIP] SUPABASE_URL or SUPABASE_KEY not set")
        return

    from agent_factory.memory import Session, SupabaseMemoryStorage

    # Create session with Supabase storage
    storage = SupabaseMemoryStorage()
    session = Session(user_id="charlie", storage=storage)

    # Add multi-turn conversation
    session.add_user_message("I'm building a chatbot")
    session.add_assistant_message("Great! What platform are you targeting?")
    session.add_user_message("Telegram and WhatsApp")
    session.add_assistant_message("I can help with that. Agent Factory supports both platforms.")
    session.save()

    # Load session
    loaded = Session.load(session.session_id, storage=storage)
    print(f"Session ID: {session.session_id}")
    print(f"Messages: {len(loaded)}")
    print(f"User: {loaded.user_id}")

    for msg in loaded.get_recent_messages():
        print(f"  [{msg.role}] {msg.content}")

    # Save custom memory atom (decision, action, context, etc.)
    storage.save_memory_atom(
        session_id=session.session_id,
        user_id="charlie",
        memory_type="decision",
        content={
            "title": "Use Agent Factory for multi-platform chatbot",
            "rationale": "Supports Telegram and WhatsApp out of the box",
            "date": "2025-12-09"
        }
    )

    # Query memory atoms
    decisions = storage.query_memory_atoms(
        session_id=session.session_id,
        memory_type="decision"
    )
    print(f"\nDecisions recorded: {len(decisions)}")
    for decision in decisions:
        print(f"  - {decision['content']['title']}")

    # Cleanup
    storage.delete_session(session.session_id)


def demo_context_manager():
    """Demo 4: ContextManager (token window management)"""
    print("\n" + "=" * 60)
    print("DEMO 4: ContextManager (Token Window Management)")
    print("=" * 60)

    from agent_factory.memory import MessageHistory, ContextManager

    # Create long conversation
    history = MessageHistory()
    history.add_message("system", "You are a helpful AI assistant.")
    history.add_message("user", "Explain quantum computing " * 50)  # Long message
    history.add_message("assistant", "Quantum computing uses quantum mechanics...")
    history.add_message("user", "What are qubits?")
    history.add_message("assistant", "Qubits are quantum bits...")

    print(f"Total messages: {len(history)}")

    # Fit to token window (small)
    manager = ContextManager(max_tokens=200, preserve_system=True)
    fitted = manager.fit_to_window(history)

    print(f"Messages that fit in 200 tokens: {len(fitted)}")
    print(f"System message preserved: {any(m.role == 'system' for m in fitted)}")

    # Larger window
    manager_large = ContextManager(max_tokens=1000, preserve_system=True)
    fitted_large = manager_large.fit_to_window(history)

    print(f"Messages that fit in 1000 tokens: {len(fitted_large)}")


def demo_session_lifecycle():
    """Demo 5: Complete session lifecycle"""
    print("\n" + "=" * 60)
    print("DEMO 5: Session Lifecycle (Create, Update, Load)")
    print("=" * 60)

    from agent_factory.memory import Session, SQLiteStorage

    db_path = "lifecycle_demo.db"
    storage = SQLiteStorage(db_path)

    # Day 1: Create session
    session = Session(user_id="dave", storage=storage)
    session.add_user_message("I want to build an AI agent")
    session.save()
    session_id = session.session_id
    print(f"Day 1: Created session {session_id[:12]}... with 1 message")

    # Day 2: Continue conversation
    loaded = Session.load(session_id, storage=storage)
    loaded.add_assistant_message("I can help with that! What does your agent do?")
    loaded.add_user_message("It monitors Reddit for questions")
    loaded.save()
    print(f"Day 2: Added 2 more messages (total: {len(loaded)})")

    # Day 3: Add metadata
    loaded2 = Session.load(session_id, storage=storage)
    loaded2.set_metadata("project_name", "RedditMonitor")
    loaded2.set_metadata("status", "active")
    loaded2.save()
    print(f"Day 3: Added metadata (project: {loaded2.get_metadata('project_name')})")

    # Day 4: Review history
    final = Session.load(session_id, storage=storage)
    print(f"\nFinal session state:")
    print(f"  Total messages: {len(final)}")
    print(f"  Project: {final.get_metadata('project_name')}")
    print(f"  Status: {final.get_metadata('status')}")

    # Cleanup
    storage.delete_session(session_id)
    os.remove(db_path)


def main():
    """Run all demos."""
    print("=" * 60)
    print("  AGENT FACTORY - MEMORY SYSTEM DEMO")
    print("  Consolidated API for Session Management")
    print("=" * 60)

    try:
        demo_in_memory()
        demo_sqlite()
        demo_supabase()
        demo_context_manager()
        demo_session_lifecycle()

        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
