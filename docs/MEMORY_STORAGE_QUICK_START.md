# Memory Storage Quick Start

## TL;DR

Replace slow file-based memory with Supabase cloud storage.

**Old way:**
- `/content-clear` - 60-120 seconds
- `/content-load` - 30-60 seconds
- Hits line limits

**New way:**
- `/memory-save` - <1 second
- `/memory-load` - <1 second
- Unlimited storage

---

## Setup (15 min)

### 1. Create Supabase Project

1. Go to https://supabase.com
2. New Project → `agent-factory-memory`
3. Copy URL and anon key from Settings → API

### 2. Add to .env

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
```

### 3. Create Table

1. Supabase → SQL Editor
2. Paste `docs/supabase_memory_schema.sql`
3. Run

### 4. Install Package

```bash
poetry add supabase
```

---

## Usage

### Save Session

In Claude CLI:
```
/memory-save
```

Saves:
- Project context
- Decisions made
- Action items
- Issues encountered
- Development log

### Load Session

Start new session:
```
/memory-load
```

Loads most recent session in <1 second.

---

## Advanced

### Query Specific Memories

```python
from agent_factory.memory.storage import SupabaseMemoryStorage

storage = SupabaseMemoryStorage()

# Get all decisions
decisions = storage.query_memory_atoms(
    user_id="your_user",
    memory_type="decision",
    limit=100
)

# Get high-priority actions
actions = storage.query_memory_atoms(
    memory_type="action"
)
high_priority = [a for a in actions if a['content']['priority'] == 'high']
```

### Manual Save

```python
storage.save_memory_atom(
    session_id="my_session",
    user_id="my_user",
    memory_type="decision",
    content={
        "title": "Use Supabase",
        "rationale": "10x faster",
        "impact": "high"
    }
)
```

---

## Files Created

| File | Purpose |
|------|---------|
| `agent_factory/memory/storage.py` | Storage backends (InMemory, SQLite, Supabase) |
| `agent_factory/memory/history.py` | Message and conversation history |
| `agent_factory/memory/session.py` | Session management |
| `agent_factory/memory/context_manager.py` | Token window management |
| `docs/supabase_memory_schema.sql` | Database schema |
| `.claude/commands/memory-save.md` | Save command |
| `.claude/commands/memory-load.md` | Load command |
| `docs/SUPABASE_MEMORY_TESTING_GUIDE.md` | Complete testing guide |

---

## Performance

| Operation | File Storage | Supabase | Speedup |
|-----------|-------------|----------|---------|
| Save | 60-120s | <1s | 60-120x |
| Load | 30-60s | <1s | 30-60x |
| Query | Grep/search | SQL | Indexed |
| Size Limit | Line limits | Unlimited | ∞ |

---

## Next Steps

1. Test connection: See `docs/SUPABASE_MEMORY_TESTING_GUIDE.md`
2. Run `/memory-save` to save first session
3. Run `/memory-load` to restore it
4. Query specific memories as needed

---

## Support

- Full guide: `docs/SUPABASE_MEMORY_TESTING_GUIDE.md`
- Schema: `docs/supabase_memory_schema.sql`
- Code: `agent_factory/memory/`
- Supabase docs: https://supabase.com/docs
