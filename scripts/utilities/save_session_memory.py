#!/usr/bin/env python3
"""Save current session to Supabase memory storage"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.memory.storage import SupabaseMemoryStorage
from datetime import datetime

print("Initializing Supabase memory storage...")
storage = SupabaseMemoryStorage()

# Generate session ID
session_id = f"claude_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
user_id = "claude_user"

print(f"Session ID: {session_id}\n")

# 1. PROJECT CONTEXT
print("[1/5] Saving project context...")
storage.save_memory_atom(
    session_id=session_id,
    user_id=user_id,
    memory_type="context",
    content={
        "project": "Agent Factory - PLC Knowledge Base",
        "phase": "Phase 1: Knowledge Base Build - COMPLETE",
        "status": "Ready for Content Generation",
        "recent_changes": [
            "Scraped 6 PLC manuals (Allen-Bradley + Siemens)",
            "Generated 2,045 knowledge atoms with embeddings",
            "Uploaded 1,964 atoms to Supabase (96%)",
            "Created database tools (diagnostic, executor, fixer)",
            "Fixed schema issues (GIN index error, content column)",
            "Verified all atoms have embeddings"
        ],
        "blockers": [
            "PostgREST schema cache blocking 81 atoms (low priority)",
            "Vector search needs pgvector setup (user action required)"
        ],
        "next_steps": [
            "User runs setup_vector_search.sql in Supabase",
            "Test vector search functionality",
            "Build ScriptwriterAgent",
            "Generate first video script",
            "Build voice + video pipeline"
        ],
        "metrics": {
            "total_atoms": 2045,
            "atoms_in_db": 1964,
            "completion_rate": "96%",
            "embedding_cost": "$0.0082",
            "manufacturers": ["Allen-Bradley", "Siemens"]
        }
    }
)

# 2. DECISIONS
print("[2/5] Saving decisions...")

decisions = [
    {
        "title": "Proceed with 96% knowledge base instead of fighting PostgREST cache",
        "rationale": "Value creation (content generation) is more important than 100% completion. 1,964 atoms are sufficient to start. Can fix remaining 81 later.",
        "alternatives": ["Wait for cache refresh", "Use direct PostgreSQL upload", "Reload schema manually"],
        "impact": "high",
        "outcome": "Unblocked content generation pipeline"
    },
    {
        "title": "Use vector search for semantic knowledge retrieval",
        "rationale": "Atoms have embeddings, pgvector enables fast similarity search (<100ms), better than keyword matching",
        "alternatives": ["Full-text search", "Keyword matching", "Manual atom selection"],
        "impact": "high",
        "outcome": "Setup SQL created, ready to enable"
    },
    {
        "title": "Build database tools instead of manual SQL execution",
        "rationale": "User requested programmatic database access without copy/paste. Tools enable automation and repeatability.",
        "alternatives": ["Manual SQL execution", "Supabase Dashboard only"],
        "impact": "medium",
        "outcome": "Created 3 production tools (644+285+300 lines)"
    }
]

for decision in decisions:
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="decision",
        content={**decision, "date": datetime.now().isoformat()}
    )

# 3. ACTION ITEMS
print("[3/5] Saving action items...")

actions = [
    {
        "task": "Run docs/setup_vector_search.sql in Supabase SQL Editor",
        "priority": "critical",
        "status": "pending",
        "assignee": "user",
        "estimated_time": "5 minutes",
        "tags": ["vector-search", "database", "user-action"]
    },
    {
        "task": "Test vector search with test_vector_search.py",
        "priority": "high",
        "status": "pending",
        "depends_on": "Vector search SQL setup",
        "estimated_time": "2 minutes",
        "tags": ["testing", "vector-search"]
    },
    {
        "task": "Build ScriptwriterAgent (atoms -> video script)",
        "priority": "high",
        "status": "pending",
        "estimated_time": "30 minutes",
        "tags": ["content-generation", "agent"]
    },
    {
        "task": "Build VoiceProductionAgent (Edge-TTS)",
        "priority": "medium",
        "status": "pending",
        "estimated_time": "20 minutes",
        "tags": ["content-generation", "voice"]
    },
    {
        "task": "Build VideoAssemblyAgent (audio + visuals)",
        "priority": "medium",
        "status": "pending",
        "estimated_time": "30 minutes",
        "tags": ["content-generation", "video"]
    },
    {
        "task": "Fix PostgREST schema cache for remaining 81 atoms",
        "priority": "low",
        "status": "pending",
        "estimated_time": "15 minutes",
        "tags": ["database", "upload", "low-priority"]
    }
]

for action in actions:
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="action",
        content=action
    )

# 4. ISSUES
print("[4/5] Saving issues...")

issues = [
    {
        "title": "GIN Index Error on TEXT Column",
        "description": "Attempted to create GIN index on knowledge_atoms.content (TEXT type). ERROR 42704",
        "status": "resolved",
        "severity": "critical",
        "root_cause": "Incorrectly assumed content was JSONB. Actually TEXT. GIN only works with JSONB, arrays, tsvector.",
        "solution": "Removed GIN index from all SQL files. Created comprehensive root cause analysis."
    },
    {
        "title": "PostgREST Schema Cache Not Refreshing",
        "description": "Error PGRST204: Could not find content column in schema cache.",
        "status": "workaround",
        "severity": "medium",
        "root_cause": "PostgREST caches schema, refreshes every 1-2 minutes.",
        "solution": "Proceeding with 1,964 atoms (96%). Will fix remaining 81 later."
    },
    {
        "title": "PostgreSQL Connection Hostname Issues",
        "description": "Initial connection attempts failed with hostname translation error",
        "status": "resolved",
        "severity": "medium",
        "root_cause": "Tried to construct hostname from SUPABASE_URL format incorrectly.",
        "solution": "Updated all database tools to support both DATABASE_URL and individual connection components."
    }
]

for issue in issues:
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="issue",
        content=issue
    )

# 5. DEVELOPMENT LOG
print("[5/5] Saving development log...")

storage.save_memory_atom(
    session_id=session_id,
    user_id=user_id,
    memory_type="log",
    content={
        "session_title": "PLC Knowledge Base Build + Database Infrastructure",
        "duration": "Full session (2+ hours)",
        "files_created": [
            "agents/database/supabase_diagnostic_agent.py (644 lines)",
            "scripts/execute_supabase_sql.py (285 lines)",
            "scripts/fix_schema_mismatches.py (300 lines)",
            "scripts/verify_kb_live.py",
            "scripts/test_vector_search.py",
            "scripts/check_embeddings.py",
            "docs/setup_vector_search.sql",
            "docs/KB_UPLOAD_SUCCESS_REPORT.md",
            "docs/GIN_INDEX_ERROR_ROOT_CAUSE.md",
            "STATUS_REPORT.md"
        ],
        "metrics": {
            "lines_of_code_written": "1500+",
            "atoms_generated": 2045,
            "atoms_uploaded": 1964,
            "embedding_cost": "$0.0082",
            "pdf_size_processed": "52MB"
        }
    }
)

print()
print("="*80)
print("SESSION SAVED TO SUPABASE")
print("="*80)
print()
print(f"Session ID: {session_id}")
print(f"User ID: {user_id}")
print()
print("Memories saved:")
print("  - 1 context update (Phase 1 Complete)")
print(f"  - {len(decisions)} decisions")
print(f"  - {len(actions)} action items")
print(f"  - {len(issues)} issues")
print("  - 1 development log")
print()
print("Query speed: ~50ms (vs 1-2 seconds with files)")
print()
print("To load this session later, use: /memory-load")
print()
