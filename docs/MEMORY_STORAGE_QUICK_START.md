# Memory Storage Quick Start

## TL;DR

Multi-provider PostgreSQL memory storage with conversation intelligence.

**For RIVET Pro Telegram Bot:**
- Conversation memory (Phase 1) - Context-aware multi-turn conversations
- Session persistence - Conversations survive bot restarts
- Natural language evolution - Gradual progression to full intelligence

**For Development/Claude Sessions:**
- `/memory-save` - <1 second
- `/memory-load` - <1 second
- Unlimited storage across Supabase/Neon/Railway

---

## Setup (15 min)

### 1. Database Configuration

Already configured with multi-provider PostgreSQL:
- Primary: Neon (current)
- Backup: Supabase, Railway

Environment variables in `.env`:
```bash
DATABASE_PROVIDER=neon  # or supabase, railway
DATABASE_URL=postgresql://...
```

### 2. RIVET Pro Setup (Conversation Memory)

Deploy conversation memory schema:
```bash
poetry run python scripts/run_migration.py 001
```

This creates `conversation_sessions` table for Phase 1 natural language intelligence.

### 3. Clear Memory (Fresh Start)

```bash
poetry run python scripts/clear_conversation_memory.py
```

Clears all conversation sessions for testing fresh conversations.

---

## Usage

### RIVET Pro Conversation Memory (Phase 1)

**Automatic** - No commands needed. The bot now:
- Remembers previous messages in conversation
- Understands follow-up questions like "What about bearings?" after discussing motors
- Maintains context across topics
- Persists sessions across bot restarts

**Test it:**
```
User: "Motor running hot"
Bot: [Answers about motors]

User: "What about bearings?"
Bot: ✅ Understands you're still talking about the motor from previous message
```

### Development Session Memory (Claude CLI)

In Claude Code sessions:
```
/memory-save  # Save current session
/memory-load  # Restore previous session
```

Saves:
- Project context
- Decisions made
- Action items
- Issues encountered
- Development log

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

## Files

| File | Purpose |
|------|---------|
| **Conversation Memory (RIVET Pro Phase 1)** | |
| `agent_factory/integrations/telegram/conversation_manager.py` | Conversation session management |
| `docs/database/migrations/001_add_conversation_sessions.sql` | Conversation schema |
| `scripts/run_migration.py` | Migration runner |
| `scripts/clear_conversation_memory.py` | Clear conversations |
| `PHASE_1_CONVERSATION_MEMORY_COMPLETE.md` | Phase 1 documentation |
| **Session Memory (Development)** | |
| `agent_factory/memory/storage.py` | Storage backends (PostgreSQL/Supabase/Railway) |
| `agent_factory/memory/history.py` | Message history |
| `agent_factory/memory/session.py` | Session management |
| `agent_factory/rivet_pro/database.py` | Multi-provider PostgreSQL adapter |
| `docs/database/rivet_pro_schema.sql` | RIVET Pro tables |

---

## Performance

| Operation | File Storage | PostgreSQL | Speedup |
|-----------|-------------|------------|---------|
| Save conversation | N/A | <100ms | Real-time |
| Load conversation | N/A | <50ms | Instant |
| Context search | N/A | <10ms | JSONB indexed |
| Session memory save | 60-120s | <1s | 60-120x |
| Session memory load | 30-60s | <1s | 30-60x |
| Size Limit | Line limits | Unlimited | ∞ |

---

## Next Steps

### For RIVET Pro Testing (Phase 1)
1. ✅ Schema deployed (conversation_sessions table)
2. ✅ Memory cleared (fresh start)
3. 🧪 **Test multi-turn conversations** - See `PHASE_1_CONVERSATION_MEMORY_COMPLETE.md`
4. 📊 Verify context awareness works

### For Development
1. Test connection: See `docs/SUPABASE_MEMORY_TESTING_GUIDE.md`
2. Run `/memory-save` to save session
3. Run `/memory-load` to restore session

---

## Support

**RIVET Pro Conversation Memory:**
- Complete guide: `PHASE_1_CONVERSATION_MEMORY_COMPLETE.md`
- Schema: `docs/database/migrations/001_add_conversation_sessions.sql`
- Code: `agent_factory/integrations/telegram/conversation_manager.py`

**Development Session Memory:**
- Schema: `docs/supabase_memory_schema.sql`
- Code: `agent_factory/memory/`
- Database: `agent_factory/rivet_pro/database.py`
