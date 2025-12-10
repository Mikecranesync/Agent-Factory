# memory-save

Save current session context to Supabase cloud database.

## Prompt

You are saving the current session to Supabase for fast retrieval later.

**This command replaces slow file-based storage with cloud database storage.**

### Instructions

1. **Analyze Current Session:**
   - What work was completed?
   - What decisions were made?
   - What issues were encountered?
   - What tasks are pending?
   - What's the current project status?

2. **Save Memory Atoms to Supabase:**

   Use the SupabaseMemoryStorage class from agent_factory.memory:

   ```python
   from agent_factory.memory.storage import SupabaseMemoryStorage
   from datetime import datetime
   import uuid

   # Initialize storage
   storage = SupabaseMemoryStorage()

   # Generate session ID (or use existing)
   session_id = f"claude_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
   user_id = "claude_user"  # Or get from context

   # Save different types of memories:

   # 1. PROJECT CONTEXT
   storage.save_memory_atom(
       session_id=session_id,
       user_id=user_id,
       memory_type="context",
       content={
           "project": "Agent Factory",
           "phase": "Current phase name",
           "status": "Current status",
           "recent_changes": ["Change 1", "Change 2"],
           "blockers": [],
           "next_steps": ["Step 1", "Step 2"]
       }
   )

   # 2. DECISIONS
   for decision in decisions_made_this_session:
       storage.save_memory_atom(
           session_id=session_id,
           user_id=user_id,
           memory_type="decision",
           content={
               "title": "Decision title",
               "rationale": "Why this was chosen",
               "alternatives": ["Alt 1", "Alt 2"],
               "impact": "high|medium|low",
               "date": datetime.now().isoformat()
           }
       )

   # 3. ACTION ITEMS
   for action in pending_actions:
       storage.save_memory_atom(
           session_id=session_id,
           user_id=user_id,
           memory_type="action",
           content={
               "task": "Task description",
               "priority": "critical|high|medium|low",
               "status": "pending|in_progress|completed",
               "due_date": "YYYY-MM-DD",
               "tags": ["tag1", "tag2"]
           }
       )

   # 4. ISSUES
   for issue in issues_encountered:
       storage.save_memory_atom(
           session_id=session_id,
           user_id=user_id,
           memory_type="issue",
           content={
               "title": "Issue title",
               "description": "Problem description",
               "status": "open|resolved",
               "severity": "critical|high|medium|low",
               "root_cause": "What caused it",
               "solution": "How it was fixed (if resolved)"
           }
       )

   # 5. DEVELOPMENT LOG
   storage.save_memory_atom(
       session_id=session_id,
       user_id=user_id,
       memory_type="log",
       content={
           "session_title": "What was accomplished",
           "activities": [
               "Created X",
               "Modified Y",
               "Fixed Z"
           ],
           "files_created": ["file1.py", "file2.md"],
           "files_modified": ["existing.py"],
           "tests_run": "Results of testing"
       }
   )
   ```

3. **Report What Was Saved:**

   After saving, report:
   ```
   Session saved to Supabase: {session_id}

   Memories saved:
   - 1 context update
   - {N} decisions
   - {N} action items
   - {N} issues
   - 1 development log

   Query speed: ~50ms (vs 1-2 seconds with files)

   To load this session later, use: /memory-load
   ```

## Success Criteria

- [x] All session information saved to Supabase
- [x] Memories categorized by type (context, decision, action, issue, log)
- [x] Session ID returned for future retrieval
- [x] Saves complete in <1 second (vs 1-2 min with files)
- [x] Can be queried by type, date, priority, etc.

## Benefits Over File-Based Storage

| Metric | File Storage | Supabase Storage |
|--------|-------------|------------------|
| Save Time | 60-120 seconds | <1 second |
| Load Time | 30-60 seconds | <1 second |
| Query Speed | Full file read | Indexed queries (50ms) |
| Size Limits | Line limits | Unlimited |
| Search | Grep/text search | SQL + full-text search |
| Multi-user | Single file conflicts | Concurrent access |

## Environment Variables Required

Make sure these are set in your .env file:
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Get these from: https://supabase.com/dashboard/project/_/settings/api

## Example Usage

```bash
# At end of session
/memory-save
```

Expected output:
```
Analyzing current session...

Session saved to Supabase: claude_session_20251209_143052

Memories saved:
- 1 context update (Phase 1 Complete)
- 3 decisions (Use Supabase, Implement orchestrator, Add callbacks)
- 5 action items (2 high priority, 3 medium)
- 2 issues (1 resolved, 1 open)
- 1 development log (Created 8 files, modified 3 files)

Database size: 4.2 KB
Save time: 0.3 seconds ✓

Next session: Use /memory-load to restore this context
```

## Notes

- Session IDs are timestamped for easy identification
- Memories are queryable by type, date, priority, status
- Supports full-text search across all content
- No file size limits
- Automatic indexing for fast retrieval
- Can load partial context (e.g., only decisions from last week)

## Troubleshooting

If save fails:
1. Check SUPABASE_URL and SUPABASE_KEY in .env
2. Verify table exists: Run docs/supabase_memory_schema.sql
3. Check connection: `poetry run python -c "from agent_factory.memory.storage import SupabaseMemoryStorage; s = SupabaseMemoryStorage(); print('Connected')"`
