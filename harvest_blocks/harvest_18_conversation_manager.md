# HARVEST BLOCK 18: Conversation Manager

**Priority**: MEDIUM
**Size**: 14.06KB (380 lines)
**Source**: `agent_factory/integrations/telegram/conversation_manager.py`
**Target**: `rivet/integrations/telegram/conversation_manager.py`

---

## Overview

Multi-turn conversation state management for Telegram bot - enables context-aware conversations by maintaining session history, extracting conversation context, and persisting state across bot restarts.

### What This Adds

- **Session persistence**: Sessions survive bot restarts (stored in database)
- **Conversation history**: Last 10 messages in context window
- **Context extraction**: Last topic, equipment, intents, unresolved issues
- **In-memory cache**: Active sessions cached for performance
- **Automatic cleanup**: Old sessions auto-deleted after inactivity
- **Follow-up detection**: Counts follow-up messages in conversation
- **Equipment tracking**: Mentioned equipment across conversation

### Key Features

```python
from rivet.integrations.telegram.conversation_manager import ConversationManager

# Initialize manager
manager = ConversationManager()

# Get or create session
session = manager.get_or_create_session(
    user_id="telegram_123",
    telegram_username="@engineer_joe"
)

# Add user message
msg = manager.add_user_message(
    session,
    content="Motor is running hot",
    metadata={"intent": "troubleshooting", "equipment": "motor"}
)

# Add bot response
manager.add_bot_message(
    session,
    content="Let me help diagnose that overheating issue...",
    metadata={"confidence": 0.85, "atoms_used": 3}
)

# Get conversation context
context = manager.get_context(session)
print(context.last_topic)  # "motor overheating"
print(context.mentioned_equipment)  # ["motor"]
print(context.follow_up_count)  # 1

# Save session to database
manager.save_session(session)
```

---

## ConversationContext Model

```python
@dataclass
class ConversationContext:
    last_topic: Optional[str] = None
    last_equipment_type: Optional[str] = None
    last_intent_type: Optional[str] = None
    mentioned_equipment: List[str] = []
    unresolved_issues: List[str] = []
    follow_up_count: int = 0

# Example extracted context:
context = ConversationContext(
    last_topic="motor overheating",
    last_equipment_type="motor",
    last_intent_type="troubleshooting",
    mentioned_equipment=["motor", "vfd"],
    unresolved_issues=["high temperature"],
    follow_up_count=2
)
```

---

## Session Management

```python
# Session lifecycle

# 1. Create new session
session = manager.get_or_create_session(user_id="123")

# 2. Add messages
manager.add_user_message(session, "Help with fault F003")
manager.add_bot_message(session, "F003 is a communication error...")

# 3. Get history (last 10 messages)
history = manager.get_history(session, limit=10)
for msg in history:
    print(f"{msg.role}: {msg.content}")

# 4. Extract context
context = manager.get_context(session)

# 5. Save to database (automatic on message add)
manager.save_session(session)

# 6. Cleanup old sessions (run periodically)
manager.cleanup_old_sessions(days=30)
```

---

## Context Window (Last 10 Messages)

```python
# Configure context window size
manager.context_window_size = 10  # default

# Get recent history for context
history = session.get_history(limit=manager.context_window_size)

# Format for LLM prompt
context_messages = [
    {"role": msg.role, "content": msg.content}
    for msg in history
]

# Example context window:
[
    {"role": "user", "content": "Motor running hot"},
    {"role": "assistant", "content": "Check motor temperature..."},
    {"role": "user", "content": "Temperature is 85°C"},
    {"role": "assistant", "content": "That's above normal..."},
    # ... last 10 messages
]
```

---

## Dependencies

```bash
# Already installed from previous blocks
# - memory (Session, Message, MessageHistory)
# - database (RIVETProDatabase)
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/integrations/telegram/conversation_manager.py rivet/integrations/telegram/conversation_manager.py`
2. Dependencies already installed
3. Validate: `python -c "from rivet.integrations.telegram.conversation_manager import ConversationManager; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.integrations.telegram.conversation_manager import ConversationManager, ConversationContext; print('OK')"

# Test session creation
python -c "
from rivet.integrations.telegram.conversation_manager import ConversationManager

manager = ConversationManager()
session = manager.get_or_create_session(user_id='test_123')
print(f'Session created: {session.user_id}')
"
```

---

## Integration Notes

**Telegram Bot Integration**:
```python
# In Telegram message handler
async def handle_message(update, context):
    user_id = str(update.message.from_user.id)

    # Get session
    session = conv_manager.get_or_create_session(
        user_id=user_id,
        telegram_username=update.message.from_user.username
    )

    # Add user message
    conv_manager.add_user_message(session, update.message.text)

    # Get conversation context
    conv_context = conv_manager.get_context(session)

    # Generate response with context awareness
    response = await orchestrator.route_query(
        request=build_request(update.message.text),
        conversation_context=conv_context  # Include past context
    )

    # Add bot response
    conv_manager.add_bot_message(session, response.response_text)

    # Send to user
    await update.message.reply_text(response.response_text)
```

**Context-Aware Responses**:
```python
# Use conversation context to improve responses

# Example: Follow-up question
if conv_context.follow_up_count > 0:
    # User is asking follow-up question
    # Reference last topic
    prompt = f"User is asking about {conv_context.last_topic}. Previous equipment: {conv_context.mentioned_equipment}"

# Example: Unresolved issues
if conv_context.unresolved_issues:
    # Remind user about unresolved issues
    response += f"\n\nNote: You still have unresolved issues with: {', '.join(conv_context.unresolved_issues)}"
```

**Session Cleanup** (cron job):
```bash
# Run daily to cleanup old sessions
0 2 * * * python -c "
from rivet.integrations.telegram.conversation_manager import ConversationManager
manager = ConversationManager()
deleted = manager.cleanup_old_sessions(days=30)
print(f'Deleted {deleted} old sessions')
"
```

---

## What This Enables

- ✅ Multi-turn conversations (remember context across messages)
- ✅ Session continuity (survive bot restarts)
- ✅ Context extraction (last topic, equipment, intents)
- ✅ Follow-up detection (count conversation depth)
- ✅ Equipment tracking (mentioned equipment across conversation)
- ✅ Performance optimization (in-memory cache for active sessions)
- ✅ Automatic cleanup (delete old inactive sessions)

---

## Next Steps

After implementing HARVEST 18, proceed to **HARVEST 19: RAG Retriever** for vector-based similarity search with pgvector.

SEE FULL SOURCE: `agent_factory/integrations/telegram/conversation_manager.py` (380 lines - copy as-is)
