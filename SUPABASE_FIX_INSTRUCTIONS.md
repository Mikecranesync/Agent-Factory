# Supabase Schema Fix - Quick Instructions

**Problem:** Old `agent_messages` table missing `agent_name` column
**Solution:** Drop all tables and recreate with correct schema
**Time:** 2 minutes

---

## Steps (Copy-Paste Ready)

### 1. Open Supabase SQL Editor
🔗 https://mggqgrxwumnnujojndub.supabase.co

Navigate to: **SQL Editor** (left sidebar)

### 2. Open the Fix SQL File
```
scripts/deployment/supabase_fix_schema.sql
```

- Open in Notepad, VS Code, or any text editor
- Select ALL (Ctrl+A)
- Copy (Ctrl+C)

### 3. Execute in SQL Editor
- Click **"New query"** in Supabase SQL Editor
- Paste (Ctrl+V) the SQL content
- Click **"Run"** (or press Ctrl+Enter)

### 4. Verify Success
You should see output like:
```
DROP TABLE
DROP TABLE
...
CREATE TABLE
CREATE TABLE
...
INSERT 0 4
```

This means:
- ✅ 7 tables dropped
- ✅ 7 tables created with correct schema
- ✅ 4 sample settings inserted

### 5. Verify Schema via Script
```bash
poetry run python scripts/deployment/fix_supabase_schema.py --verify
```

Expected output:
```
[OK] Connected to Supabase
[OK] knowledge_atoms table exists
[OK] agent_messages table exists
[OK] Schema is correctly deployed!
```

---

## After Success

### Next Step: Upload 2,049 Atoms
```bash
poetry run python scripts/knowledge/upload_atoms_to_supabase.py
```

This will:
- Upload 2,049 atoms in batches of 50
- Show progress bar
- Take ~5 minutes
- Result: Complete knowledge base ready for queries

---

## What This Fixes

**Before:**
```
agent_messages table (OLD):
├── id
├── session_id
├── message_type
├── content
└── [MISSING: agent_name] ❌
```

**After:**
```
agent_messages table (NEW):
├── id
├── session_id
├── agent_name ✅
├── message_type
├── content
└── metadata
```

**Impact:**
- ✅ Index creation works
- ✅ All 7 tables have correct schema
- ✅ Ready for Week 2 agent development

---

## Troubleshooting

### If SQL execution fails:
1. Check error message in SQL Editor
2. Common issues:
   - Extension not installed: Run `CREATE EXTENSION IF NOT EXISTS vector;`
   - Permissions: Make sure you're using service role key

### If verification fails:
1. Check Supabase dashboard → Table Editor
2. Manually verify tables exist: knowledge_atoms, agent_messages, etc.
3. Check agent_messages columns include `agent_name`

---

## Files Generated

- `scripts/deployment/supabase_fix_schema.sql` (350 lines)
  - DROP statements (7 tables)
  - Complete schema (7 tables + indexes)
  - Sample settings

---

**Ready to execute? Follow steps 1-5 above!**
