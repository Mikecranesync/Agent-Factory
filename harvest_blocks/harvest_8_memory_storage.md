# HARVEST BLOCK 8: PostgreSQL Memory Storage

**Priority**: CRITICAL - Depends on HARVEST 7 (Database Manager)
**Size**: 30KB (953 lines)
**Source**: `agent_factory/memory/storage.py`
**Target**: `rivet/memory/storage.py`

---

## Overview

Memory storage abstraction with 4 backends: InMemory (dev/test), SQLite (local), SupabaseMemoryStorage (cloud REST API), PostgresMemoryStorage (multi-provider with failover).

### What This Adds

- **MemoryStorage ABC**: Abstract interface for all storage backends
- **InMemoryStorage**: Fast ephemeral storage (development/testing)
- **SQLiteStorage**: Local file-based persistence (single-user)
- **SupabaseMemoryStorage**: Cloud storage via REST API (production)
- **PostgresMemoryStorage**: Multi-provider PostgreSQL with failover (PRODUCTION RECOMMENDED)

### Key Features

```python
from rivet.memory import Session, PostgresMemoryStorage

# Production: Multi-provider with automatic failover
storage = PostgresMemoryStorage()  # Uses DatabaseManager from HARVEST 7
session = Session(user_id="alice", storage=storage)
session.add_user_message("My VFD is throwing F0002")
session.save()  # Persists to neon → supabase → railway → local

# Later, load from any available provider
loaded_session = storage.load_session(session.session_id)

# Save custom memory atoms (context, decision, action, issue, log)
storage.save_memory_atom(
    session_id="session_abc123",
    user_id="alice",
    memory_type="decision",
    content={
        "title": "Route to Siemens SME",
        "reasoning": "Detected manufacturer: Siemens S7-1200",
        "confidence": 0.95
    }
)
```

---

## Dependencies

```bash
poetry add supabase  # For SupabaseMemoryStorage
# psycopg already added in HARVEST 7
```

---

## Environment Variables

(Same as HARVEST 7 - uses DatabaseManager)

```bash
DATABASE_PROVIDER=neon
DATABASE_FAILOVER_ENABLED=true
NEON_DB_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_key_here
```

---

## Complete Implementation

SEE FULL SOURCE FILE: `agent_factory/memory/storage.py` (953 lines)

Copy the entire file to `rivet/memory/storage.py` - it contains:

1. **MemoryStorage (ABC)** - Abstract base class with 4 required methods:
   - `save_session(session)`
   - `load_session(session_id)`
   - `delete_session(session_id)`
   - `list_sessions(user_id)`

2. **InMemoryStorage** - Dictionary-based storage (ephemeral)

3. **SQLiteStorage** - Local .db file storage  

4. **SupabaseMemoryStorage** - Cloud storage via Supabase REST API

5. **PostgresMemoryStorage** - Multi-provider PostgreSQL (PRODUCTION)
   - Uses DatabaseManager from HARVEST 7
   - Automatic failover across providers
   - Stores sessions as memory atoms
   - Supports custom atom types (context, decision, action, issue, log)
   - Includes `save_memory_atom()` and `query_memory_atoms()` methods

---

## Quick Implementation Guide

### Step 1: Copy Full Source

```bash
# In Agent Factory repo
cp agent_factory/memory/storage.py /path/to/rivet/memory/storage.py
```

### Step 2: Update Imports

The file already uses:
```python
from agent_factory.core.database_manager import DatabaseManager
```

Change to:
```python
from rivet.core.database_manager import DatabaseManager
```

(Only needed in PostgresMemoryStorage class, line ~602)

### Step 3: Update Session Class

Modify `rivet/memory/session.py` to accept storage parameter:

```python
from rivet.memory.storage import MemoryStorage, PostgresMemoryStorage

class Session:
    def __init__(self, user_id: str, storage: MemoryStorage = None, **kwargs):
        self.storage = storage or PostgresMemoryStorage()  # Default to production
        # ... rest of init
        
    def save(self):
        """Save session to storage."""
        if self.storage:
            self.storage.save_session(self)
```

---

## Validation

```bash
# Test PostgresMemoryStorage
python -c "from rivet.memory.storage import PostgresMemoryStorage; storage = PostgresMemoryStorage(); print('Storage ready')"

# Test session save/load
python -c "
from rivet.memory import Session, PostgresMemoryStorage
storage = PostgresMemoryStorage()
session = Session('alice', storage=storage)
session.add_user_message('Test message')
session.save()
print(f'Session saved: {session.session_id}')

# Load it back
loaded = storage.load_session(session.session_id)
print(f'Session loaded: {len(loaded.history)} messages')
"

# Test memory atoms
python -c "
from rivet.memory.storage import PostgresMemoryStorage
storage = PostgresMemoryStorage()
storage.save_memory_atom(
    session_id='test_123',
    user_id='alice',
    memory_type='decision',
    content={'title': 'Test decision', 'confidence': 0.9}
)
atoms = storage.query_memory_atoms(session_id='test_123', memory_type='decision')
print(f'Memory atoms: {len(atoms)}')
"
```

---

## Key Classes Summary

### PostgresMemoryStorage (Lines 561-953)

**Production-ready multi-provider storage**

```python
class PostgresMemoryStorage(MemoryStorage):
    def __init__(self):
        from rivet.core.database_manager import DatabaseManager
        self.db = DatabaseManager()  # Auto-failover enabled
        self.table_name = "session_memories"
```

**Methods**:
- `save_session(session)` - Save as session_metadata + message atoms
- `load_session(session_id)` - Reconstruct from atoms
- `delete_session(session_id)` - Remove all atoms
- `list_sessions(user_id)` - Get all session IDs
- `save_memory_atom(...)` - Save custom atom (context/decision/action/issue/log)
- `query_memory_atoms(...)` - Query atoms by filters

**Storage Format**:
- Session metadata stored as `memory_type='session_metadata'`
- Messages stored as `memory_type='message_user'` or `memory_type='message_assistant'`
- Custom atoms stored with custom `memory_type` values
- All content stored as JSONB in PostgreSQL

---

## What This Enables

After implementing HARVEST 8, you will have:

- ✅ **Persistent Sessions** - Sessions survive across restarts
- ✅ **Multi-Provider Storage** - Automatic failover (HARVEST 7 foundation)
- ✅ **Memory Atoms** - Structured context storage (decisions, actions, issues)
- ✅ **4 Storage Options** - InMemory, SQLite, Supabase, PostgreSQL
- ✅ **Production Ready** - PostgresMemoryStorage for production
- ✅ **Flexible Querying** - Query memory atoms by type/session/user

This enables agents to maintain context across conversations and store structured decision-making data.

---

## Integration with Existing Code

### Before (in-memory only):
```python
session = Session(user_id="alice")
session.add_user_message("Hello")
# Lost on restart
```

### After (persistent):
```python
from rivet.memory.storage import PostgresMemoryStorage

storage = PostgresMemoryStorage()
session = Session(user_id="alice", storage=storage)
session.add_user_message("Hello")
session.save()  # Persisted to database with failover

# Later (even after restart):
session = storage.load_session(session.session_id)
# Full conversation history restored
```

---

## Next Steps

After implementing HARVEST 8:
1. ✅ Test with all 4 storage backends
2. ✅ Verify PostgresMemoryStorage uses DatabaseManager failover
3. ✅ Proceed to **HARVEST 9** (VPS KB Client) - can be done in parallel
4. Update all agent code to use persistent storage
