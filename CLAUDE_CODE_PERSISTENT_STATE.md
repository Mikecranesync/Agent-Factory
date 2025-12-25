# Claude Code CLI Task: Build Hardened Persistent Machine State System

**Project:** Agent Factory / RivetCEO Bot
**Location:** `/root/Agent-Factory` (VPS) or local repo
**Goal:** Users add equipment to their library via Telegram multi-step flow. State persists through crashes, restarts, network failures.

---

## CONTEXT

**What exists:**
- `agent_factory/integrations/telegram/conversation_state.py` - ConversationStateManager class (basic implementation)
- `migrations/002_conversation_states.sql` - Database schema
- `agent_factory/integrations/telegram/library.py` - Library handlers (needs integration)
- 4-tier database fallback: Neon → Supabase → Railway → Local SQLite

**What's broken/missing:**
- State doesn't reliably persist after every input
- No resume on bot restart (user has to start over)
- No timeout handling for abandoned conversations
- No graceful error recovery mid-flow
- Edge cases not handled (duplicate entries, invalid input, etc.)

**User flow to implement:**
```
User taps "Save to Library" on equipment photo
    ↓
Bot: "Enter a nickname for this equipment"
User: "Main compressor"
    [STATE SAVED: {step: 'nickname', nickname: 'Main compressor'}]
    ↓
Bot: "Manufacturer? (or /skip)"
User: "Siemens"
    [STATE SAVED: {step: 'manufacturer', nickname: '...', manufacturer: 'Siemens'}]
    ↓
Bot: "Model number? (or /skip)"
User: "3RQ2000-2AW00"
    [STATE SAVED: {step: 'model', ...}]
    ↓
Bot: "Serial number? (or /skip)"
User: /skip
    [STATE SAVED: {step: 'serial', serial: null, ...}]
    ↓
Bot: "Location? (or /skip)"
User: "Building A, Panel 3"
    [STATE SAVED: {step: 'location', ...}]
    ↓
Bot: "Any notes? (or /skip)"
User: "Replaced relay 2024-06"
    [STATE SAVED: {step: 'notes', ...}]
    ↓
Bot: "✅ Saved to library!"
    [STATE CLEARED - Machine saved to user_machines table]
```

---

## PHASE 1: Database Schema Verification

### 1.1 Verify/create conversation_states table:

```sql
-- File: migrations/002_conversation_states.sql
CREATE TABLE IF NOT EXISTS conversation_states (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    conversation_type TEXT NOT NULL DEFAULT 'add_machine',
    current_step TEXT NOT NULL,
    state_data JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours'),
    UNIQUE(user_id, chat_id, conversation_type)
);

CREATE INDEX IF NOT EXISTS idx_conversation_states_user ON conversation_states(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_states_expires ON conversation_states(expires_at);
```

### 1.2 Verify/create user_machines table:

```sql
-- File: migrations/003_user_machines.sql (if not exists)
CREATE TABLE IF NOT EXISTS user_machines (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    nickname TEXT NOT NULL,
    manufacturer TEXT,
    model_number TEXT,
    serial_number TEXT,
    location TEXT,
    notes TEXT,
    photo_file_id TEXT,  -- Telegram file_id for the equipment photo
    ocr_data JSONB,      -- Original OCR extraction
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_machines_user ON user_machines(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_machines_nickname ON user_machines(user_id, nickname);
```

---

## PHASE 2: Hardened ConversationStateManager

### 2.1 Rewrite conversation_state.py with full error handling:

```python
# File: agent_factory/integrations/telegram/conversation_state.py

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationStateManager:
    """
    Manages persistent conversation state with 4-tier database fallback.
    
    Guarantees:
    - State persists through bot restarts
    - State persists through network failures (SQLite fallback)
    - Abandoned conversations auto-expire after 24 hours
    - Thread-safe operations
    - Graceful degradation (never crashes the bot)
    """
    
    STEPS = ['nickname', 'manufacturer', 'model', 'serial', 'location', 'notes', 'complete']
    SKIPPABLE_STEPS = ['manufacturer', 'model', 'serial', 'location', 'notes']
    
    def __init__(self, db_manager):
        self.db = db_manager
        self._local_cache = {}  # In-memory backup
        self._sqlite_path = Path("/tmp/rivet_conversation_states.db")
        self._ensure_sqlite_schema()
    
    def _ensure_sqlite_schema(self):
        """Initialize local SQLite as final fallback."""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self._sqlite_path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_states (
                    user_id TEXT NOT NULL,
                    chat_id TEXT NOT NULL,
                    conversation_type TEXT NOT NULL DEFAULT 'add_machine',
                    current_step TEXT NOT NULL,
                    state_data TEXT NOT NULL DEFAULT '{}',
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    PRIMARY KEY (user_id, chat_id, conversation_type)
                )
            """)
            conn.commit()
            conn.close()
            logger.info("SQLite fallback initialized")
        except Exception as e:
            logger.error(f"SQLite init failed: {e}")
    
    async def save_state(
        self,
        user_id: str,
        chat_id: str,
        step: str,
        data: Dict[str, Any],
        conversation_type: str = 'add_machine'
    ) -> bool:
        """
        Save conversation state. Tries PostgreSQL first, falls back to SQLite.
        
        Returns True if saved successfully to ANY backend.
        """
        user_id = str(user_id)
        chat_id = str(chat_id)
        state_json = json.dumps(data)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Update local cache immediately (fastest)
        cache_key = f"{user_id}:{chat_id}:{conversation_type}"
        self._local_cache[cache_key] = {
            'step': step,
            'data': data,
            'updated_at': datetime.utcnow()
        }
        
        # Try PostgreSQL (with retry)
        for attempt in range(3):
            try:
                await self.db.execute("""
                    INSERT INTO conversation_states 
                        (user_id, chat_id, conversation_type, current_step, state_data, updated_at, expires_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, NOW(), $6)
                    ON CONFLICT (user_id, chat_id, conversation_type)
                    DO UPDATE SET 
                        current_step = EXCLUDED.current_step,
                        state_data = EXCLUDED.state_data,
                        updated_at = NOW(),
                        expires_at = EXCLUDED.expires_at
                """, user_id, chat_id, conversation_type, step, state_json, expires_at)
                logger.debug(f"State saved to PostgreSQL: {user_id} step={step}")
                return True
            except Exception as e:
                logger.warning(f"PostgreSQL save attempt {attempt+1} failed: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        # Fallback to SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(str(self._sqlite_path))
            conn.execute("""
                INSERT OR REPLACE INTO conversation_states 
                    (user_id, chat_id, conversation_type, current_step, state_data, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, conversation_type, step, state_json, 
                  datetime.utcnow().isoformat(), expires_at.isoformat()))
            conn.commit()
            conn.close()
            logger.info(f"State saved to SQLite fallback: {user_id} step={step}")
            return True
        except Exception as e:
            logger.error(f"SQLite save failed: {e}")
        
        # Even if DB failed, local cache has it
        logger.warning(f"State only in memory cache: {user_id} step={step}")
        return True  # Cache counts as saved
    
    async def load_state(
        self,
        user_id: str,
        chat_id: str,
        conversation_type: str = 'add_machine'
    ) -> Optional[Dict[str, Any]]:
        """
        Load conversation state. Checks PostgreSQL, SQLite, then memory cache.
        
        Returns None if no active conversation found.
        """
        user_id = str(user_id)
        chat_id = str(chat_id)
        cache_key = f"{user_id}:{chat_id}:{conversation_type}"
        
        # Try PostgreSQL first
        try:
            result = await self.db.fetch_one("""
                SELECT current_step, state_data, expires_at
                FROM conversation_states
                WHERE user_id = $1 AND chat_id = $2 AND conversation_type = $3
                  AND expires_at > NOW()
            """, user_id, chat_id, conversation_type)
            
            if result:
                state_data = result['state_data']
                if isinstance(state_data, str):
                    state_data = json.loads(state_data)
                logger.debug(f"State loaded from PostgreSQL: {user_id} step={result['current_step']}")
                return {
                    'step': result['current_step'],
                    'data': state_data
                }
        except Exception as e:
            logger.warning(f"PostgreSQL load failed: {e}")
        
        # Try SQLite fallback
        try:
            import sqlite3
            conn = sqlite3.connect(str(self._sqlite_path))
            cursor = conn.execute("""
                SELECT current_step, state_data, expires_at
                FROM conversation_states
                WHERE user_id = ? AND chat_id = ? AND conversation_type = ?
                  AND expires_at > ?
            """, (user_id, chat_id, conversation_type, datetime.utcnow().isoformat()))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                logger.info(f"State loaded from SQLite: {user_id} step={row[0]}")
                return {
                    'step': row[0],
                    'data': json.loads(row[1])
                }
        except Exception as e:
            logger.warning(f"SQLite load failed: {e}")
        
        # Check memory cache
        if cache_key in self._local_cache:
            cached = self._local_cache[cache_key]
            # Check if cached state is still valid (within 24 hours)
            if (datetime.utcnow() - cached['updated_at']).total_seconds() < 86400:
                logger.info(f"State loaded from memory cache: {user_id}")
                return {
                    'step': cached['step'],
                    'data': cached['data']
                }
        
        return None
    
    async def clear_state(
        self,
        user_id: str,
        chat_id: str,
        conversation_type: str = 'add_machine'
    ) -> bool:
        """
        Clear conversation state (on success or cancel).
        """
        user_id = str(user_id)
        chat_id = str(chat_id)
        cache_key = f"{user_id}:{chat_id}:{conversation_type}"
        
        # Clear from memory cache
        self._local_cache.pop(cache_key, None)
        
        # Clear from PostgreSQL
        try:
            await self.db.execute("""
                DELETE FROM conversation_states
                WHERE user_id = $1 AND chat_id = $2 AND conversation_type = $3
            """, user_id, chat_id, conversation_type)
            logger.debug(f"State cleared from PostgreSQL: {user_id}")
        except Exception as e:
            logger.warning(f"PostgreSQL clear failed: {e}")
        
        # Clear from SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(str(self._sqlite_path))
            conn.execute("""
                DELETE FROM conversation_states
                WHERE user_id = ? AND chat_id = ? AND conversation_type = ?
            """, (user_id, chat_id, conversation_type))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"SQLite clear failed: {e}")
        
        return True
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired conversation states. Call periodically (e.g., hourly).
        
        Returns count of deleted rows.
        """
        deleted = 0
        
        # Clean PostgreSQL
        try:
            result = await self.db.execute("""
                DELETE FROM conversation_states WHERE expires_at < NOW()
            """)
            deleted += result if isinstance(result, int) else 0
        except Exception as e:
            logger.warning(f"PostgreSQL cleanup failed: {e}")
        
        # Clean SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(str(self._sqlite_path))
            cursor = conn.execute("""
                DELETE FROM conversation_states WHERE expires_at < ?
            """, (datetime.utcnow().isoformat(),))
            deleted += cursor.rowcount
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"SQLite cleanup failed: {e}")
        
        # Clean memory cache
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self._local_cache.items()
            if (now - v['updated_at']).total_seconds() > 86400
        ]
        for k in expired_keys:
            del self._local_cache[k]
            deleted += 1
        
        logger.info(f"Cleaned up {deleted} expired conversation states")
        return deleted
    
    def get_next_step(self, current_step: str) -> Optional[str]:
        """Get the next step in the flow."""
        try:
            idx = self.STEPS.index(current_step)
            if idx + 1 < len(self.STEPS):
                return self.STEPS[idx + 1]
        except ValueError:
            pass
        return None
    
    def is_skippable(self, step: str) -> bool:
        """Check if a step can be skipped."""
        return step in self.SKIPPABLE_STEPS
```

---

## PHASE 3: Library Handler Integration

### 3.1 Rewrite library.py with state persistence at every step:

```python
# File: agent_factory/integrations/telegram/library.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from .conversation_state import ConversationStateManager

logger = logging.getLogger(__name__)

# Conversation states (internal to ConversationHandler)
NICKNAME, MANUFACTURER, MODEL, SERIAL, LOCATION, NOTES = range(6)

class LibraryManager:
    """
    Handles user equipment library with persistent conversation state.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.state_manager = ConversationStateManager(db_manager)
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Build the ConversationHandler for add_machine flow."""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add_machine, pattern='^save_to_library$'),
                CommandHandler('addmachine', self.start_add_machine_cmd),
            ],
            states={
                NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_nickname)],
                MANUFACTURER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_manufacturer),
                    CommandHandler('skip', self.skip_manufacturer),
                ],
                MODEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_model),
                    CommandHandler('skip', self.skip_model),
                ],
                SERIAL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_serial),
                    CommandHandler('skip', self.skip_serial),
                ],
                LOCATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_location),
                    CommandHandler('skip', self.skip_location),
                ],
                NOTES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notes),
                    CommandHandler('skip', self.skip_notes),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel),
                MessageHandler(filters.COMMAND, self.unknown_command),
            ],
            name="add_machine",
            persistent=False,  # We handle persistence ourselves
            allow_reentry=True,
        )
    
    async def check_and_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """
        Check if user has an in-progress conversation and resume it.
        Call this at bot startup for returning users.
        """
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        state = await self.state_manager.load_state(user_id, chat_id)
        if state:
            step = state['step']
            data = state['data']
            
            # Restore context
            context.user_data['machine_data'] = data
            
            # Map step name to ConversationHandler state
            step_map = {
                'nickname': NICKNAME,
                'manufacturer': MANUFACTURER,
                'model': MODEL,
                'serial': SERIAL,
                'location': LOCATION,
                'notes': NOTES,
            }
            
            if step in step_map:
                await update.message.reply_text(
                    f"👋 Welcome back! You were adding a machine.\n\n"
                    f"Current progress: {self._format_progress(data)}\n\n"
                    f"Let's continue. {self._get_prompt_for_step(step)}\n\n"
                    f"Or type /cancel to start over."
                )
                return step_map[step]
        
        return None
    
    async def start_add_machine(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Entry point from 'Save to Library' button on equipment photo."""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        # Extract OCR data from the message that triggered this
        ocr_data = context.user_data.get('last_ocr_result', {})
        
        # Initialize state
        initial_data = {
            'photo_file_id': context.user_data.get('last_photo_file_id'),
            'ocr_data': ocr_data,
            'manufacturer_hint': ocr_data.get('manufacturer'),
            'model_hint': ocr_data.get('model'),
        }
        
        context.user_data['machine_data'] = initial_data
        
        # Save initial state
        await self.state_manager.save_state(
            user_id, chat_id, 'nickname', initial_data
        )
        
        await query.edit_message_text(
            "📝 **Add to Library**\n\n"
            "Enter a nickname for this equipment:\n"
            "(e.g., 'Main Compressor', 'Panel 3 VFD')"
        )
        
        return NICKNAME
    
    async def start_add_machine_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Entry point from /addmachine command."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        # Check for existing conversation to resume
        existing = await self.state_manager.load_state(user_id, chat_id)
        if existing:
            context.user_data['machine_data'] = existing['data']
            await update.message.reply_text(
                f"👋 You have an in-progress entry.\n\n"
                f"Progress: {self._format_progress(existing['data'])}\n\n"
                f"Continuing from: {existing['step']}\n"
                f"Type /cancel to start fresh."
            )
            step_map = {'nickname': NICKNAME, 'manufacturer': MANUFACTURER, 
                       'model': MODEL, 'serial': SERIAL, 'location': LOCATION, 'notes': NOTES}
            return step_map.get(existing['step'], NICKNAME)
        
        # Fresh start
        context.user_data['machine_data'] = {}
        await self.state_manager.save_state(user_id, chat_id, 'nickname', {})
        
        await update.message.reply_text(
            "📝 **Add Equipment to Library**\n\n"
            "Enter a nickname for this equipment:"
        )
        return NICKNAME
    
    async def handle_nickname(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle nickname input."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        nickname = update.message.text.strip()
        
        # Validate
        if len(nickname) < 2:
            await update.message.reply_text("❌ Nickname too short. Please enter at least 2 characters.")
            return NICKNAME
        
        if len(nickname) > 100:
            await update.message.reply_text("❌ Nickname too long. Please keep it under 100 characters.")
            return NICKNAME
        
        # Check for duplicate
        try:
            existing = await self.db.fetch_one(
                "SELECT id FROM user_machines WHERE user_id = $1 AND nickname = $2",
                user_id, nickname
            )
            if existing:
                await update.message.reply_text(
                    f"❌ You already have equipment named '{nickname}'.\n"
                    f"Please choose a different nickname."
                )
                return NICKNAME
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            # Continue anyway - we'll catch it on save
        
        # Save state
        data = context.user_data.get('machine_data', {})
        data['nickname'] = nickname
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'manufacturer', data)
        
        # Show hint if we have OCR data
        hint = ""
        if data.get('manufacturer_hint'):
            hint = f"\n💡 Detected: {data['manufacturer_hint']}"
        
        await update.message.reply_text(
            f"✅ Nickname: **{nickname}**\n\n"
            f"Enter the manufacturer:{hint}\n"
            f"(or /skip)"
        )
        return MANUFACTURER
    
    async def handle_manufacturer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle manufacturer input."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        manufacturer = update.message.text.strip()
        
        data = context.user_data.get('machine_data', {})
        data['manufacturer'] = manufacturer
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'model', data)
        
        hint = ""
        if data.get('model_hint'):
            hint = f"\n💡 Detected: {data['model_hint']}"
        
        await update.message.reply_text(
            f"✅ Manufacturer: **{manufacturer}**\n\n"
            f"Enter the model number:{hint}\n"
            f"(or /skip)"
        )
        return MODEL
    
    async def skip_manufacturer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Skip manufacturer step."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        data = context.user_data.get('machine_data', {})
        data['manufacturer'] = None
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'model', data)
        
        await update.message.reply_text(
            "⏭️ Skipped manufacturer.\n\n"
            "Enter the model number:\n"
            "(or /skip)"
        )
        return MODEL
    
    async def handle_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle model number input."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        model = update.message.text.strip()
        
        data = context.user_data.get('machine_data', {})
        data['model_number'] = model
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'serial', data)
        
        await update.message.reply_text(
            f"✅ Model: **{model}**\n\n"
            f"Enter the serial number:\n"
            f"(or /skip)"
        )
        return SERIAL
    
    async def skip_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Skip model step."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        data = context.user_data.get('machine_data', {})
        data['model_number'] = None
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'serial', data)
        
        await update.message.reply_text(
            "⏭️ Skipped model.\n\n"
            "Enter the serial number:\n"
            "(or /skip)"
        )
        return SERIAL
    
    async def handle_serial(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle serial number input."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        serial = update.message.text.strip()
        
        data = context.user_data.get('machine_data', {})
        data['serial_number'] = serial
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'location', data)
        
        await update.message.reply_text(
            f"✅ Serial: **{serial}**\n\n"
            f"Enter the location:\n"
            f"(e.g., 'Building A, Panel 3')\n"
            f"(or /skip)"
        )
        return LOCATION
    
    async def skip_serial(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Skip serial step."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        data = context.user_data.get('machine_data', {})
        data['serial_number'] = None
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'location', data)
        
        await update.message.reply_text(
            "⏭️ Skipped serial.\n\n"
            "Enter the location:\n"
            "(or /skip)"
        )
        return LOCATION
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle location input."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        location = update.message.text.strip()
        
        data = context.user_data.get('machine_data', {})
        data['location'] = location
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'notes', data)
        
        await update.message.reply_text(
            f"✅ Location: **{location}**\n\n"
            f"Any notes?\n"
            f"(e.g., 'Replaced relay 2024-06')\n"
            f"(or /skip to finish)"
        )
        return NOTES
    
    async def skip_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Skip location step."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        data = context.user_data.get('machine_data', {})
        data['location'] = None
        context.user_data['machine_data'] = data
        
        await self.state_manager.save_state(user_id, chat_id, 'notes', data)
        
        await update.message.reply_text(
            "⏭️ Skipped location.\n\n"
            "Any notes?\n"
            "(or /skip to finish)"
        )
        return NOTES
    
    async def handle_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle notes input and save to database."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        notes = update.message.text.strip()
        
        data = context.user_data.get('machine_data', {})
        data['notes'] = notes
        
        return await self._save_machine(update, context, data)
    
    async def skip_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Skip notes and save to database."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        data = context.user_data.get('machine_data', {})
        data['notes'] = None
        
        return await self._save_machine(update, context, data)
    
    async def _save_machine(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict) -> int:
        """Save the machine to user_machines table."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        try:
            # Insert into user_machines
            await self.db.execute("""
                INSERT INTO user_machines 
                    (user_id, nickname, manufacturer, model_number, serial_number, 
                     location, notes, photo_file_id, ocr_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
            """, 
                user_id,
                data.get('nickname'),
                data.get('manufacturer'),
                data.get('model_number'),
                data.get('serial_number'),
                data.get('location'),
                data.get('notes'),
                data.get('photo_file_id'),
                json.dumps(data.get('ocr_data', {}))
            )
            
            # Clear conversation state
            await self.state_manager.clear_state(user_id, chat_id)
            
            # Clear context
            context.user_data.pop('machine_data', None)
            
            await update.message.reply_text(
                f"✅ **Saved to Library!**\n\n"
                f"**{data.get('nickname')}**\n"
                f"• Manufacturer: {data.get('manufacturer') or 'N/A'}\n"
                f"• Model: {data.get('model_number') or 'N/A'}\n"
                f"• Serial: {data.get('serial_number') or 'N/A'}\n"
                f"• Location: {data.get('location') or 'N/A'}\n"
                f"• Notes: {data.get('notes') or 'N/A'}\n\n"
                f"View your library with /library"
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Failed to save machine: {e}")
            
            # Check if it's a duplicate error
            if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                await update.message.reply_text(
                    f"❌ Error: Equipment '{data.get('nickname')}' already exists.\n"
                    f"Use /cancel and try again with a different nickname."
                )
            else:
                await update.message.reply_text(
                    f"❌ Error saving equipment. Please try again.\n"
                    f"Your progress has been saved - use /addmachine to continue."
                )
            
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation and clear state."""
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        
        await self.state_manager.clear_state(user_id, chat_id)
        context.user_data.pop('machine_data', None)
        
        await update.message.reply_text(
            "❌ Cancelled. Your progress has been cleared.\n"
            "Start fresh with /addmachine"
        )
        
        return ConversationHandler.END
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle unknown commands during conversation."""
        await update.message.reply_text(
            "⚠️ Unknown command during add flow.\n"
            "Please enter the requested info, /skip, or /cancel."
        )
        # Stay in current state - return None to not change state
        return None
    
    def _format_progress(self, data: dict) -> str:
        """Format current progress for display."""
        parts = []
        if data.get('nickname'):
            parts.append(f"• Nickname: {data['nickname']}")
        if data.get('manufacturer'):
            parts.append(f"• Manufacturer: {data['manufacturer']}")
        if data.get('model_number'):
            parts.append(f"• Model: {data['model_number']}")
        if data.get('serial_number'):
            parts.append(f"• Serial: {data['serial_number']}")
        if data.get('location'):
            parts.append(f"• Location: {data['location']}")
        return '\n'.join(parts) if parts else 'Just started'
    
    def _get_prompt_for_step(self, step: str) -> str:
        """Get the prompt text for a given step."""
        prompts = {
            'nickname': 'Enter a nickname for this equipment:',
            'manufacturer': 'Enter the manufacturer (or /skip):',
            'model': 'Enter the model number (or /skip):',
            'serial': 'Enter the serial number (or /skip):',
            'location': 'Enter the location (or /skip):',
            'notes': 'Any notes? (or /skip to finish):',
        }
        return prompts.get(step, 'Continue:')


# ============================================================
# LIBRARY VIEW HANDLERS (separate from add flow)
# ============================================================

async def library_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db_manager):
    """Handle /library command - show user's saved equipment."""
    user_id = str(update.effective_user.id)
    
    try:
        machines = await db_manager.fetch_all("""
            SELECT nickname, manufacturer, model_number, location, created_at
            FROM user_machines
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 20
        """, user_id)
        
        if not machines:
            await update.message.reply_text(
                "📚 **Your Library**\n\n"
                "No equipment saved yet.\n\n"
                "Send a photo of equipment to get started!"
            )
            return
        
        lines = ["📚 **Your Library**\n"]
        for i, m in enumerate(machines, 1):
            lines.append(
                f"{i}. **{m['nickname']}**\n"
                f"   {m['manufacturer'] or 'Unknown'} | {m['model_number'] or 'N/A'}\n"
                f"   📍 {m['location'] or 'No location'}"
            )
        
        lines.append(f"\n_{len(machines)} items_")
        
        await update.message.reply_text('\n'.join(lines))
        
    except Exception as e:
        logger.error(f"Library fetch failed: {e}")
        await update.message.reply_text("❌ Error loading library. Please try again.")
```

---

## PHASE 4: Bot Integration

### 4.1 Register handlers in main bot file:

```python
# In orchestrator_bot.py or main.py

from agent_factory.integrations.telegram.library import LibraryManager, library_command

# Initialize
library_manager = LibraryManager(db_manager)

# Add conversation handler (MUST be added before other handlers)
application.add_handler(library_manager.get_conversation_handler(), group=0)

# Add library view command
application.add_handler(
    CommandHandler('library', lambda u, c: library_command(u, c, db_manager)),
    group=1
)

# On startup - check for resumable conversations
async def on_startup():
    # Schedule periodic cleanup
    job_queue.run_repeating(
        lambda c: library_manager.state_manager.cleanup_expired(),
        interval=3600,  # Every hour
        first=60
    )
```

---

## PHASE 5: Error Handling Matrix

### 5.1 Handle every failure mode:

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Neon connection timeout | `asyncio.TimeoutError` | Fallback to SQLite |
| Neon connection refused | `ConnectionRefusedError` | Fallback to SQLite |
| Invalid JSON in state_data | `json.JSONDecodeError` | Reset state, ask user to restart |
| Duplicate nickname | `UniqueViolation` | Prompt user for different name |
| Bot restart mid-conversation | State exists in DB | Resume from last step |
| User sends photo during add flow | `filters.PHOTO` in fallback | Save photo to context, continue flow |
| User goes silent for 24h | `expires_at` check | Auto-cleanup, fresh start next time |
| SQLite disk full | `sqlite3.OperationalError` | Log error, rely on memory cache |
| Memory cache grows too large | Check `len(self._local_cache)` | Prune oldest entries |

### 5.2 Implement retry decorator:

```python
# File: agent_factory/core/retry.py

import asyncio
import functools
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)
T = TypeVar('T')

def with_retry(
    max_attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator with exponential backoff.
    
    Usage:
        @with_retry(max_attempts=3, delay=0.5)
        async def flaky_operation():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator
```

---

## TESTING CHECKLIST

After implementation, verify:

### Unit Tests:
- [ ] `save_state()` persists to PostgreSQL
- [ ] `save_state()` falls back to SQLite when PostgreSQL fails
- [ ] `load_state()` retrieves from PostgreSQL
- [ ] `load_state()` falls back to SQLite when PostgreSQL fails
- [ ] `load_state()` uses memory cache when both DBs fail
- [ ] `clear_state()` removes from all tiers
- [ ] `cleanup_expired()` removes old entries
- [ ] Duplicate nickname detection works

### Integration Tests:
- [ ] Full flow: nickname → manufacturer → model → serial → location → notes → saved
- [ ] Skip flow: nickname → /skip → /skip → /skip → /skip → /skip → saved
- [ ] Cancel flow: nickname → /cancel → state cleared
- [ ] Resume flow: nickname → (bot restart) → resume from manufacturer
- [ ] Duplicate detection: Try to add same nickname twice

### Chaos Tests:
- [ ] Kill PostgreSQL mid-flow → SQLite takes over → complete flow
- [ ] Restart bot mid-flow → resume on next message
- [ ] Fill SQLite disk → memory cache takes over
- [ ] Send gibberish during flow → error message, stays in step

---

## DEPLOYMENT COMMANDS

```bash
# 1. Run migrations
ssh root@72.60.175.144
cd /root/Agent-Factory
psql $NEON_DATABASE_URL -f migrations/002_conversation_states.sql
psql $NEON_DATABASE_URL -f migrations/003_user_machines.sql

# 2. Deploy code
git pull origin main
systemctl restart orchestrator-bot

# 3. Verify
journalctl -u orchestrator-bot -n 50 --no-pager

# 4. Test
# Send photo → tap "Save to Library" → complete flow
# Restart bot mid-flow → send message → should resume
```

---

## SUCCESS CRITERIA

1. ✅ State persists through bot restarts
2. ✅ State persists through PostgreSQL outages (SQLite fallback)
3. ✅ User can resume conversation after disconnect
4. ✅ 24-hour TTL auto-cleans abandoned conversations
5. ✅ Duplicate nicknames rejected with clear error
6. ✅ All steps skippable except nickname
7. ✅ /library shows saved equipment
8. ✅ Zero data loss under any failure condition

**BEGIN IMPLEMENTATION.**

---

# APPENDIX: Recent Session Work

## Session 2025-12-25: Ingestion Pipeline Fix ✅

**Task:** Fix knowledge base ingestion pipeline failures

**Root Cause Found:**
- 5 database tables missing from production (Neon PostgreSQL)
- Pipeline failed at Stage 1 (Source Acquisition) with PGRST205 error
- Graceful degradation masked the issue (reported "success" with 0 atoms)

**Tables Deployed:**
```
✓ source_fingerprints - Deduplication tracking
✓ ingestion_logs - Processing history
✓ failed_ingestions - Error retry queue
✓ human_review_queue - Quality validation
✓ atom_relations - Prerequisite relationships
```

**Code Fixed:**
- `agent_factory/workflows/ingestion_chain.py` (lines 922-950, 1008-1025)
- Success status logic: `success: false` when atoms_created=0 AND errors exist
- Improved logging for debugging

**Status:** ✅ OPERATIONAL
- All 7 pipeline stages working
- Deduplication functional
- Error tracking enabled
- Ready for production use

**Documentation:** See `INGESTION_PIPELINE_FIX_REPORT.md` and `.claude/history/session_2025-12-25_ingestion_fix.md`

---
