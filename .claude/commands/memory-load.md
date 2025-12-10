# memory-load

Load session context from Supabase cloud database.

## Prompt

You are loading a previous session from Supabase for instant context restoration.

**This command replaces slow file-based loading with cloud database queries.**

### Instructions

**IMPORTANT:** The easiest way to load a session is to run the standalone script:

```bash
poetry run python load_session.py
```

This script handles .env loading automatically and displays a full session resume.

### Alternative: Manual Python Code

If you need to customize the loading logic:

1. **Connect to Supabase:**

   ```python
   import os
   from pathlib import Path
   from dotenv import load_dotenv

   # CRITICAL: Load .env first
   load_dotenv(Path(__file__).parent / ".env")

   from agent_factory.memory.storage import SupabaseMemoryStorage
   from datetime import datetime, timedelta

   # Initialize storage (now finds SUPABASE_SERVICE_ROLE_KEY automatically)
   storage = SupabaseMemoryStorage()
   ```

2. **Find Recent Sessions:**

   ```python
   # Try to find sessions for known users
   sessions = []
   for user_id in ["claude_user", "test_user"]:
       result = storage.query_memory_atoms(
           user_id=user_id,
           memory_type="context",
           limit=5
       )
       if result:
           sessions.extend(result)
           break

   # Fall back to finding ANY context entries if no user-specific sessions
   if not sessions:
       all_contexts = storage.client.table('session_memories').select('*').eq('memory_type', 'context').order('created_at', desc=True).limit(5).execute()
       sessions = all_contexts.data

   if not sessions:
       print("No previous sessions found. Use /memory-save to create your first session.")
       return

   # Get latest session
   latest = sessions[0]
   session_id = latest['session_id']
   user_id = latest['user_id']
   print(f"Loading session: {session_id}")
   print(f"User: {user_id}")
   print(f"Last active: {latest['created_at']}")
   ```

3. **Load All Memory Types:**

   ```python
   # Get all memories for the session
   all_memories = storage.query_memory_atoms(
       session_id=session_id,
       limit=1000
   )

   # Organize by type
   context = [m for m in all_memories if m['memory_type'] == 'context']
   decisions = [m for m in all_memories if m['memory_type'] == 'decision']
   actions = [m for m in all_memories if m['memory_type'] == 'action']
   issues = [m for m in all_memories if m['memory_type'] == 'issue']
   logs = [m for m in all_memories if m['memory_type'] == 'log']
   ```

4. **Format Session Resume:**

   Provide a structured resume in this format:

   ```
   # Session Resume [{date}]
   Session ID: {session_id}
   Loaded from: Supabase (query time: 50ms)

   ## Current Status
   Project: {project_name}
   Phase: {current_phase}
   Status: {status_description}

   Recent Changes:
   - {change 1}
   - {change 2}
   - {change 3}

   Blockers: {blockers_list or "None"}

   ## Immediate Actions ({N} total)

   HIGH PRIORITY:
   1. [{status}] {task_description}
   2. [{status}] {task_description}

   MEDIUM PRIORITY:
   3. [{status}] {task_description}

   ## Recent Decisions ({N} total)

   1. **{decision_title}** ({date})
      - Rationale: {rationale}
      - Impact: {impact_level}

   2. **{decision_title}** ({date})
      - Rationale: {rationale}
      - Impact: {impact_level}

   ## Open Issues ({N} total)

   1. [{severity}] {issue_title}
      - Status: {status}
      - Root cause: {cause}

   ## Last Session Summary

   {session_title}
   Activities:
   - {activity 1}
   - {activity 2}

   Files: {N} created, {N} modified

   ## Ready to Continue
   {Yes/No - are there blockers?}

   ---
   Load time: {X}ms from Supabase
   Memory atoms loaded: {N} context, {N} decisions, {N} actions, {N} issues, {N} logs
   ```

## Example Output

```
# Session Resume [2025-12-09]
Session ID: claude_session_20251209_143052
Loaded from: Supabase (query time: 45ms)

## Current Status
Project: Agent Factory
Phase: Supabase Memory Integration (Phase 1 Extension)
Status: ✅ Storage backend complete, testing in progress

Recent Changes:
- Created SupabaseMemoryStorage class with CRUD operations
- Added memory-save and memory-load slash commands
- Created SQL schema for session_memories table
- Updated .env.example with Supabase credentials

Blockers: None

## Immediate Actions (5 total)

HIGH PRIORITY:
1. [pending] Test memory-save command with live Supabase instance
2. [pending] Test memory-load command retrieval speed

MEDIUM PRIORITY:
3. [pending] Create comprehensive testing guide
4. [pending] Document migration from file-based to Supabase storage
5. [pending] Add memory-query command for advanced searches

## Recent Decisions (3 total)

1. **Use Supabase for Memory Storage** (2025-12-09)
   - Rationale: 10-100x faster than file I/O, no line limits, better querying
   - Impact: high

2. **Implement Memory Atoms Pattern** (2025-12-09)
   - Rationale: Flexible schema allows different memory types in same table
   - Impact: medium

3. **Keep File-Based Commands as Backup** (2025-12-09)
   - Rationale: Allow gradual migration, users can choose storage backend
   - Impact: low

## Open Issues (1 total)

1. [medium] Need to create Supabase project and run schema script
   - Status: open
   - Root cause: First-time setup required

## Last Session Summary

Supabase Memory Integration Implementation
Activities:
- Created storage.py with 3 backend implementations
- Created history.py for message management
- Created context_manager.py for token windows
- Created SQL schema with indexes and examples
- Created slash commands for save/load operations

Files: 5 created, 2 modified

## Ready to Continue
Yes - Backend complete, ready for testing

---
Load time: 45ms from Supabase
Memory atoms loaded: 1 context, 3 decisions, 5 actions, 1 issue, 1 log
```

## Advanced Queries

You can also load specific memories:

```python
# Get only high-priority actions
high_priority = storage.query_memory_atoms(
    user_id=user_id,
    memory_type="action",
    limit=50
)
high_priority = [a for a in high_priority if a['content'].get('priority') == 'high']

# Get decisions from last 7 days
week_ago = datetime.now() - timedelta(days=7)
recent_decisions = storage.query_memory_atoms(
    user_id=user_id,
    memory_type="decision",
    limit=100
)
# Filter by date in content

# Get all open issues
issues = storage.query_memory_atoms(
    user_id=user_id,
    memory_type="issue",
    limit=100
)
open_issues = [i for i in issues if i['content'].get('status') == 'open']
```

## Success Criteria

- [x] Session loaded in <1 second (vs 30-60 seconds with files)
- [x] All memory types retrieved (context, decisions, actions, issues, logs)
- [x] Formatted resume provided
- [x] Clear indication of what to do next
- [x] No file reading required

## Benefits Over File-Based Loading

| Metric | File Storage | Supabase Storage |
|--------|-------------|------------------|
| Load Time | 30-60 seconds | <1 second |
| Context Size | Limited by line count | Unlimited |
| Partial Loading | Must read full files | Query specific types |
| Search | Text search only | SQL + full-text |
| Multi-session | One at a time | Query across sessions |

## Environment Variables Required

Make sure these are set in your .env file:
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

## Example Usage

```bash
# At start of new session
/memory-load
```

Expected output:
```
Finding recent sessions...

Latest session: claude_session_20251209_143052
Last active: 2025-12-09 14:30:52

Loading session context...
✓ Context loaded
✓ 3 decisions loaded
✓ 5 actions loaded
✓ 1 issue loaded
✓ 1 development log loaded

[Full session resume displayed above]

Query time: 45ms
Ready to continue working!
```

## Options

### Load specific session:
```python
# If you know the session ID
specific_session = storage.query_memory_atoms(
    session_id="claude_session_20251208_100000"
)
```

### Load last N sessions:
```python
# Get context from last 3 sessions
sessions = storage.query_memory_atoms(
    user_id=user_id,
    memory_type="context",
    limit=3
)
```

### Search across all sessions:
```python
# Find all sessions mentioning "Supabase"
# (Use full-text search in Postgres)
```

## Troubleshooting

If load fails:
1. Check SUPABASE_URL and SUPABASE_KEY in .env
2. Verify you've run /memory-save at least once
3. Check table exists: Run docs/supabase_memory_schema.sql
4. Test connection: `poetry run python -c "from agent_factory.memory.storage import SupabaseMemoryStorage; s = SupabaseMemoryStorage(); print('Connected')"`
