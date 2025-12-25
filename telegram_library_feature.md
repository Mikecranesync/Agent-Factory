# Claude CLI Prompt: Build Telegram Machine Library Feature

## Context
You are adding a "Personal Machine Library" feature to RivetCEO Bot - an industrial maintenance AI assistant on Telegram. This lets technicians save their machines for quick reference and context-aware troubleshooting.

## Tech Stack
- Python 3.11+
- python-telegram-bot v21+ (async)
- PostgreSQL + pgvector (Neon)
- Existing bot structure in `agent_factory/`

## Feature Requirements

### 1. Database Schema (add to existing schema)
```sql
-- User's saved machines
CREATE TABLE user_machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,              -- Telegram user ID
    nickname VARCHAR(50) NOT NULL,      -- "Line 3 Robot", "Basement Compressor"
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    location TEXT,
    notes TEXT,
    photo_file_id TEXT,                 -- Telegram file_id for reference photo
    created_at TIMESTAMP DEFAULT NOW(),
    last_queried TIMESTAMP,
    UNIQUE(user_id, nickname)
);

-- Query history per machine
CREATE TABLE user_machine_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID REFERENCES user_machines(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    response_summary TEXT,
    atoms_used TEXT[],                  -- Knowledge atoms referenced
    route_taken VARCHAR(10),            -- A, B, C, or D
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_machines_user ON user_machines(user_id);
CREATE INDEX idx_machine_history_machine ON user_machine_history(machine_id);
```

### 2. Telegram UI Flow

#### Entry Point: `/library` command
Shows main menu with InlineKeyboardMarkup:
```
📚 My Machine Library

[Line 3 Robot    ] [Air Comp #2     ]
[Packaging PLC   ] [Hydraulic Press ]

[➕ Add New Machine]
```

#### View Machine Detail (when user taps a machine):
```
🔧 Line 3 Robot
━━━━━━━━━━━━━━━
Manufacturer: Fanuc
Model: M-20iA
Serial: RF2847291
Location: Building A, Line 3
Notes: Replaced servo amp 2024-03

[🔍 Troubleshoot] [📜 History]
[✏️ Edit        ] [🗑️ Delete ]
[⬅️ Back        ]
```

#### Add Machine Flow (ConversationHandler):
States: NICKNAME → MANUFACTURER → MODEL → SERIAL → LOCATION → NOTES → PHOTO → CONFIRM

Each step can be skipped except NICKNAME (required).

### 3. Key Classes & Functions

```python
# telegram_library.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# Conversation states
NICKNAME, MANUFACTURER, MODEL, SERIAL, LOCATION, NOTES, PHOTO, CONFIRM = range(8)

# Callback data prefixes
CB_VIEW_MACHINE = "lib_view_"      # lib_view_{machine_id}
CB_TROUBLESHOOT = "lib_ts_"        # lib_ts_{machine_id}
CB_HISTORY = "lib_hist_"           # lib_hist_{machine_id}
CB_EDIT = "lib_edit_"              # lib_edit_{machine_id}
CB_DELETE = "lib_del_"             # lib_del_{machine_id}
CB_CONFIRM_DEL = "lib_cdel_"       # lib_cdel_{machine_id}
CB_ADD_NEW = "lib_add"
CB_BACK = "lib_back"
CB_SKIP = "lib_skip"

async def library_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Entry point: /library command - shows user's saved machines"""
    user_id = str(update.effective_user.id)
    machines = await db.get_user_machines(user_id)
    
    keyboard = []
    # Build 2-column grid of machines
    row = []
    for machine in machines:
        btn = InlineKeyboardButton(
            text=f"{machine['nickname'][:14]}",
            callback_data=f"{CB_VIEW_MACHINE}{machine['id']}"
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:  # Add remaining button if odd number
        keyboard.append(row)
    
    # Add "Add New" button
    keyboard.append([InlineKeyboardButton("➕ Add New Machine", callback_data=CB_ADD_NEW)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📚 **My Machine Library**\n\n"
    if not machines:
        text += "_No machines saved yet. Add your first one!_"
    else:
        text += f"_{len(machines)} machine(s) saved_"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def view_machine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show machine detail view with action buttons"""
    query = update.callback_query
    await query.answer()
    
    machine_id = query.data.replace(CB_VIEW_MACHINE, "")
    machine = await db.get_machine(machine_id)
    
    text = f"""🔧 **{machine['nickname']}**
━━━━━━━━━━━━━━━
**Manufacturer:** {machine['manufacturer'] or 'Not set'}
**Model:** {machine['model_number'] or 'Not set'}
**Serial:** {machine['serial_number'] or 'Not set'}
**Location:** {machine['location'] or 'Not set'}
**Notes:** {machine['notes'] or 'None'}
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🔍 Troubleshoot", callback_data=f"{CB_TROUBLESHOOT}{machine_id}"),
            InlineKeyboardButton("📜 History", callback_data=f"{CB_HISTORY}{machine_id}")
        ],
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"{CB_EDIT}{machine_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"{CB_DELETE}{machine_id}")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data=CB_BACK)]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def troubleshoot_machine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set active machine context and prompt for issue description"""
    query = update.callback_query
    await query.answer()
    
    machine_id = query.data.replace(CB_TROUBLESHOOT, "")
    machine = await db.get_machine(machine_id)
    
    # Store in user context for query enrichment
    context.user_data['active_machine'] = machine
    
    await query.edit_message_text(
        f"🔧 **Troubleshooting: {machine['nickname']}**\n\n"
        f"_{machine['manufacturer']} {machine['model_number']}_\n\n"
        "Describe the issue you're experiencing:",
        parse_mode="Markdown"
    )
    # Next message from user goes to orchestrator with machine context


# ConversationHandler for adding machines
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add machine flow"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['new_machine'] = {}
    
    await query.edit_message_text(
        "➕ **Add New Machine**\n\n"
        "What do you want to call this machine?\n"
        "_(e.g., 'Line 3 Robot', 'Basement Compressor')_",
        parse_mode="Markdown"
    )
    return NICKNAME


async def add_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save nickname, ask for manufacturer"""
    context.user_data['new_machine']['nickname'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await update.message.reply_text(
        "What's the **manufacturer**?\n_(e.g., Fanuc, Siemens, Allen-Bradley)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MANUFACTURER


async def add_manufacturer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save manufacturer, ask for model"""
    if update.callback_query:  # Skip pressed
        await update.callback_query.answer()
        context.user_data['new_machine']['manufacturer'] = None
    else:
        context.user_data['new_machine']['manufacturer'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "What's the **model number**?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MODEL


# ... continue pattern for MODEL, SERIAL, LOCATION, NOTES, PHOTO ...


async def add_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show summary and save machine"""
    machine_data = context.user_data['new_machine']
    user_id = str(update.effective_user.id)
    
    # Save to database
    machine_id = await db.create_machine(user_id, machine_data)
    
    await update.message.reply_text(
        f"✅ **{machine_data['nickname']}** saved to your library!\n\n"
        "Use /library to view your machines.",
        parse_mode="Markdown"
    )
    
    context.user_data.pop('new_machine', None)
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel add flow"""
    context.user_data.pop('new_machine', None)
    await update.message.reply_text("Cancelled. Use /library to view your machines.")
    return ConversationHandler.END


# Build the ConversationHandler
add_machine_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_start, pattern=f"^{CB_ADD_NEW}$")],
    states={
        NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_nickname)],
        MANUFACTURER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_manufacturer),
            CallbackQueryHandler(add_manufacturer, pattern=f"^{CB_SKIP}$")
        ],
        MODEL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_model),
            CallbackQueryHandler(add_model, pattern=f"^{CB_SKIP}$")
        ],
        SERIAL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_serial),
            CallbackQueryHandler(add_serial, pattern=f"^{CB_SKIP}$")
        ],
        LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_location),
            CallbackQueryHandler(add_location, pattern=f"^{CB_SKIP}$")
        ],
        NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_notes),
            CallbackQueryHandler(add_notes, pattern=f"^{CB_SKIP}$")
        ],
        PHOTO: [
            MessageHandler(filters.PHOTO, add_photo),
            CallbackQueryHandler(add_photo, pattern=f"^{CB_SKIP}$")
        ],
    },
    fallbacks=[CommandHandler("cancel", add_cancel)],
    name="add_machine",
    persistent=False
)
```

### 4. Query Enrichment Integration

When a user sends a troubleshooting query while a machine is active:

```python
# In your message handler / orchestrator
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Check for active machine context
    active_machine = context.user_data.get('active_machine')
    
    if active_machine:
        # Enrich query with machine context
        enriched_query = f"""
User's equipment: {active_machine['manufacturer']} {active_machine['model_number']}
Serial: {active_machine['serial_number']}
Location: {active_machine['location']}
Notes: {active_machine['notes']}

User's issue: {user_text}
"""
        # Update last_queried timestamp
        await db.update_machine_last_queried(active_machine['id'])
        
        # Log to history after response
        # ... send to orchestrator with enriched_query ...
    else:
        # Normal query flow
        pass
```

### 5. Register Handlers in Bot

```python
# In your main bot setup
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Library handlers
    application.add_handler(CommandHandler("library", library_command))
    application.add_handler(add_machine_handler)  # ConversationHandler
    application.add_handler(CallbackQueryHandler(view_machine, pattern=f"^{CB_VIEW_MACHINE}"))
    application.add_handler(CallbackQueryHandler(troubleshoot_machine, pattern=f"^{CB_TROUBLESHOOT}"))
    application.add_handler(CallbackQueryHandler(view_history, pattern=f"^{CB_HISTORY}"))
    application.add_handler(CallbackQueryHandler(edit_machine, pattern=f"^{CB_EDIT}"))
    application.add_handler(CallbackQueryHandler(delete_machine, pattern=f"^{CB_DELETE}"))
    application.add_handler(CallbackQueryHandler(back_to_library, pattern=f"^{CB_BACK}$"))
    
    # ... other handlers ...
```

## Deliverables

1. `telegram_library.py` - Complete library feature module
2. `migrations/add_user_machines.sql` - Database migration
3. Updated `telegram_bot.py` with handler registration
4. Integration with existing orchestrator for query enrichment

## Constraints

- Callback data max 64 bytes (use UUIDs or short IDs)
- InlineKeyboard max 8 buttons per row
- Total keyboard max 100 buttons
- Handle edge cases: duplicate nicknames, deleted machines, etc.
- Use async/await throughout
- Follow existing code patterns in agent_factory/

## Testing Commands

After implementation, test with:
```
/library                    # View empty library
(tap Add New)              # Start add flow
"Test Robot"               # Enter nickname
"Fanuc"                    # Enter manufacturer
(tap Skip)                 # Skip model
...
/library                    # See saved machine
(tap machine)              # View detail
(tap Troubleshoot)         # Set context
"arm won't move"           # Query with context
(tap History)              # See query history
```

Build this feature. Start with the database migration, then the core library module, then integrate with the existing bot.
