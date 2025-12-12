# Manual Schema Fix - Missing Columns

## Quick Fix (Run in Supabase SQL Editor)

**Status**: 2 schema issues found - `agent_messages.session_id` and `knowledge_atoms.content`

```sql
-- Fix 1: Add missing session_id column to agent_messages table
ALTER TABLE agent_messages ADD COLUMN IF NOT EXISTS session_id TEXT;
CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id);

-- Fix 2: Add missing content column to knowledge_atoms table
ALTER TABLE knowledge_atoms ADD COLUMN IF NOT EXISTS content TEXT;
```

**Why No GIN Index on content?**
- `content` is a **TEXT** column (not JSONB)
- GIN indexes only work with JSONB, arrays, or full-text search vectors
- Large text fields typically don't need indexes
- Attempting `USING gin(content)` on TEXT causes: "ERROR: data type text has no default operator class for access method gin"

## How to Run

1. Open Supabase Dashboard → https://supabase.com/dashboard
2. Navigate to: **SQL Editor**
3. Click: **New Query**
4. Paste the SQL above
5. Click: **Run** (or press Ctrl/Cmd + Enter)

This will:
- ✅ Add the `session_id` column to `agent_messages` table (TEXT with B-tree index)
- ✅ Add the `content` column to `knowledge_atoms` table (TEXT, no index needed)
- ✅ Use `IF NOT EXISTS` so it's safe to run multiple times
- ✅ Avoid the GIN index error by NOT indexing large text fields

## Why This Was Needed

The original migration used `CREATE TABLE IF NOT EXISTS`, which:
- ✅ Creates table if it doesn't exist
- ❌ **Does NOT update schema if table already exists**

Since both tables already existed (from earlier migrations), the new columns were never added.

## Impact

**Before Fix**:
- ❌ All 2,045 knowledge atom uploads failing with "content column does not exist"
- ❌ Agent messages can't be grouped by session
- ❌ Knowledge base is empty

**After Fix**:
- ✅ 2,045 atoms ready to upload
- ✅ Session-based conversation tracking works
- ✅ Full knowledge base operational

## Verify Fix Worked

After running the SQL, verify with:

```sql
-- Check both tables
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('agent_messages', 'knowledge_atoms')
  AND column_name IN ('session_id', 'content')
ORDER BY table_name, column_name;
```

Expected output:
```
 table_name       | column_name | data_type
------------------+-------------+-----------
 agent_messages   | session_id  | text
 knowledge_atoms  | content     | text
```

## Re-Upload Atoms After Fix

Once the schema is fixed, re-upload the 2,045 atoms:

```bash
poetry run python scripts/FULL_AUTO_KB_BUILD.py
```

Expected output:
```
[3/3] UPLOADING 2045 ATOMS TO SUPABASE...
  Uploaded 100/2045 (4.89%)...
  Uploaded 200/2045 (9.78%)...
  ...
[SUCCESS] 2045/2045 atoms uploaded (100.00%)
```

## Automated Tools (Requires DATABASE_URL)

Once you add `DATABASE_URL` to `.env`, you can use:

```bash
# Auto-detect and fix all schema issues
poetry run python scripts/fix_schema_mismatches.py

# Execute SQL files directly
poetry run python scripts/execute_supabase_sql.py --file docs/supabase_complete_schema.sql
```

**Get DATABASE_URL from:** Supabase Dashboard → Project Settings → Database → Connection Info → URI
