# Deploy Supabase Schema - Instructions

**Goal:** Deploy the updated schema with citations JSONB field

---

## Quick Deploy (5 minutes)

### Step 1: Open Supabase SQL Editor

URL: https://supabase.com/dashboard/project/mggqgrxwumnnujojndub/sql/new

Or navigate to:
1. Go to https://supabase.com/dashboard
2. Select project: `mggqgrxwumnnujojndub`
3. Click "SQL Editor" in left sidebar
4. Click "New query"

### Step 2: Copy Schema File

Open this file: `docs/supabase_complete_schema.sql`

**Full path:**
```
C:\Users\hharp\OneDrive\Desktop\Agent Factory\docs\supabase_complete_schema.sql
```

### Step 3: Paste and Run

1. Copy entire contents of `supabase_complete_schema.sql`
2. Paste into SQL Editor
3. Click **"Run"** button (or press Ctrl+Enter)

### Step 4: Verify

Check for success messages:
- ✅ Extensions created (uuid-ossp, vector)
- ✅ Tables created (7 tables)
- ✅ Indexes created
- ✅ Comments added

---

## What This Schema Includes

### Tables (7)
1. **knowledge_atoms** - Knowledge base with embeddings (UPDATED: includes `citations` JSONB)
2. **research_staging** - Research Agent raw data
3. **video_scripts** - Scriptwriter Agent output
4. **upload_jobs** - YouTube Uploader queue
5. **agent_messages** - Inter-agent communication
6. **session_memories** - Memory atoms
7. **settings** - Runtime configuration

### NEW: Citations Field

```sql
citations JSONB DEFAULT '[]'::jsonb
```

**Format:**
```json
[
  {
    "id": 1,
    "url": "https://worktrek.com/blog/what-is-5s-principal-for-maintenance/",
    "title": "What is 5S principal for maintenance",
    "accessed_at": "2025-12-12T10:30:00Z"
  },
  {
    "id": 2,
    "url": "https://www.milliken.com/...",
    "title": "What is 5S and how does it apply",
    "accessed_at": "2025-12-12T10:30:00Z"
  }
]
```

---

## Troubleshooting

### Error: "extension vector does not exist"

**Solution:** Enable pgvector extension first
```sql
CREATE EXTENSION IF NOT EXISTS "vector";
```

### Error: "table already exists"

**Solution:** Schema uses `IF NOT EXISTS`, so this is safe. The citations column will be added if it doesn't exist.

### Error: "column citations already exists"

**Solution:** Schema already deployed! No action needed.

---

## After Deployment

### Verify Citations Column

Run this query in SQL Editor:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'knowledge_atoms'
  AND column_name = 'citations';
```

**Expected result:**
```
column_name | data_type
------------|----------
citations   | jsonb
```

### Test Citation Insert

```sql
INSERT INTO knowledge_atoms (
    atom_id,
    atom_type,
    title,
    summary,
    content,
    manufacturer,
    difficulty,
    source_document,
    source_pages,
    citations
) VALUES (
    'test:citation:demo',
    'concept',
    'Test Citation',
    'Testing citation format',
    'This is a test atom with citations',
    'test',
    'beginner',
    'test.pdf',
    ARRAY[1],
    '[{"id": 1, "url": "https://example.com", "title": "Test Source"}]'::jsonb
);
```

**Verify:**
```sql
SELECT atom_id, citations
FROM knowledge_atoms
WHERE atom_id = 'test:citation:demo';
```

---

## Next Steps After Deployment

1. ✅ Schema deployed with citations field
2. Upload 2,049 atoms: `poetry run python scripts/upload_atoms_to_supabase.py`
3. Test citation parsing: `poetry run python examples/perplexity_citation_demo.py`
4. Week 3: Add Perplexity API to ResearchAgent

---

**Need Help?** See `Guides for Users/PRODUCTION_DEPLOYMENT.md` for complete deployment guide
