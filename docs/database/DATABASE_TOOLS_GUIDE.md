# Database Tools Guide

## Overview

Three new tools for programmatic database management:

1. **Diagnostic Agent** - Inspect schema, detect mismatches
2. **SQL Executor** - Execute SQL files/statements directly
3. **Schema Fixer** - Auto-detect and fix schema issues

## Quick Fix (No Setup Required)

**Problem**: `column "session_id" does not exist` + `column "content" does not exist`

**Solution**: Run this SQL in Supabase SQL Editor:

```sql
-- Fix 1: Add session_id to agent_messages (B-tree index for text)
ALTER TABLE agent_messages ADD COLUMN IF NOT EXISTS session_id TEXT;
CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id);

-- Fix 2: Add content to knowledge_atoms (TEXT, no index)
ALTER TABLE knowledge_atoms ADD COLUMN IF NOT EXISTS content TEXT;
```

**Note**: `content` is TEXT (not JSONB), so NO GIN index! GIN only works with JSONB/arrays.

See: `docs/MANUAL_SCHEMA_FIX.md` for detailed instructions.

## Automated Tools (Requires DATABASE_URL)

### 1. Schema Diagnostic Agent

**Purpose**: Inspect database schema, compare against expected schema

**Usage**:
```bash
# List all tables
poetry run python agents/database/supabase_diagnostic_agent.py --list

# Inspect specific table
poetry run python agents/database/supabase_diagnostic_agent.py --table agent_messages

# Run full diagnostic (compare all tables)
poetry run python agents/database/supabase_diagnostic_agent.py --full
```

**Output Example**:
```
[MISMATCH] Table: agent_messages
  - Missing column: session_id (expected type: text)
  - Fix SQL: ALTER TABLE agent_messages ADD COLUMN session_id TEXT;
```

### 2. SQL Executor Script

**Purpose**: Execute SQL files or inline SQL without copy/paste

**Usage**:
```bash
# Execute SQL file
poetry run python scripts/execute_supabase_sql.py --file docs/supabase_complete_schema.sql

# Execute inline SQL
poetry run python scripts/execute_supabase_sql.py --sql "ALTER TABLE agent_messages ADD COLUMN session_id TEXT;"

# Dry run (validate without executing)
poetry run python scripts/execute_supabase_sql.py --file schema.sql --dry-run

# Execute without transaction (auto-commit each statement)
poetry run python scripts/execute_supabase_sql.py --file schema.sql --no-transaction
```

**Features**:
- ✅ Transaction support (COMMIT/ROLLBACK)
- ✅ Statement-by-statement error handling
- ✅ Dry-run mode for safety
- ✅ Detailed execution logs

### 3. Schema Fix Script

**Purpose**: One-command schema repair (diagnostic + fix + verify)

**Usage**:
```bash
# Auto-fix all schema issues
poetry run python scripts/fix_schema_mismatches.py

# Fix specific table
poetry run python scripts/fix_schema_mismatches.py --table agent_messages

# Dry run (show fixes without applying)
poetry run python scripts/fix_schema_mismatches.py --dry-run

# Auto-apply without confirmation
poetry run python scripts/fix_schema_mismatches.py --yes
```

**Workflow**:
1. Runs diagnostic to find mismatches
2. Generates ALTER TABLE fix statements
3. Shows fixes and asks for confirmation
4. Applies fixes
5. Verifies fixes worked

## Setup (First Time)

### Get DATABASE_URL

1. Open Supabase Dashboard: https://supabase.com/dashboard
2. Navigate to: **Project Settings** → **Database**
3. Scroll to: **Connection Info** section
4. Copy: **URI** (Transaction mode)
5. Add to `.env`:

```bash
DATABASE_URL=postgresql://postgres:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Important**: Use **Transaction mode** (port 6543), not Session mode (port 5432), for external connections.

### Verify Connection

```bash
# Test connection
poetry run python agents/database/supabase_diagnostic_agent.py --list
```

If connection fails:
- ✅ Check DATABASE_URL is correct
- ✅ Verify password doesn't have special characters that need escaping
- ✅ Confirm you're using Transaction mode (port 6543)
- ✅ Check network allows outbound connections on port 6543

## Architecture

```
User Request
    ↓
Diagnostic Agent (agents/database/supabase_diagnostic_agent.py)
    ├─→ Connect to PostgreSQL (psycopg2)
    ├─→ Inspect schema (information_schema)
    ├─→ Compare vs expected schema
    └─→ Generate fix recommendations
    ↓
Schema Fixer (scripts/fix_schema_mismatches.py)
    ├─→ Uses Diagnostic Agent
    ├─→ Generates ALTER TABLE statements
    ├─→ Applies fixes with confirmation
    └─→ Verifies success
    ↓
SQL Executor (scripts/execute_supabase_sql.py)
    ├─→ Parses SQL files
    ├─→ Executes statements
    └─→ Handles transactions
```

## Expected Schema

The diagnostic agent compares actual database against this expected schema:

### agent_messages
- `id` (uuid, primary key)
- `session_id` (text) ← **This was missing!**
- `agent_name` (text)
- `message_type` (text)
- `content` (jsonb)
- `metadata` (jsonb)
- `created_at` (timestamp with time zone)

### agent_sessions
- `id` (uuid, primary key)
- `user_id` (text)
- `agent_name` (text)
- `started_at` (timestamp with time zone)
- `ended_at` (timestamp with time zone)
- `metadata` (jsonb)

(Plus 5 other tables - see `agents/database/supabase_diagnostic_agent.py` for complete list)

## Troubleshooting

### Error: "could not translate host name"
- **Cause**: Using wrong hostname format
- **Fix**: Use DATABASE_URL from Supabase Dashboard (includes correct pooler hostname)

### Error: "column already exists"
- **Cause**: Column was already added manually
- **Fix**: Safe to ignore - diagnostic will show "no mismatches"

### Error: "connection timeout"
- **Cause**: Network blocking port 6543
- **Fix**: Check firewall settings, or use Supabase SQL Editor manually

### Error: "authentication failed"
- **Cause**: Wrong password in DATABASE_URL
- **Fix**: Copy password from Supabase Dashboard → Database → Connection Info

## Files Created

- `agents/database/supabase_diagnostic_agent.py` (644 lines) - Schema inspection and comparison
- `agents/database/__init__.py` - Package exports
- `scripts/execute_supabase_sql.py` (285 lines) - Direct SQL execution
- `scripts/fix_schema_mismatches.py` (300 lines) - Automated schema repair
- `docs/MANUAL_SCHEMA_FIX.md` - Manual SQL fix guide
- `docs/DATABASE_TOOLS_GUIDE.md` - This file

## Dependencies Added

```toml
psycopg2-binary = "^2.9.11"  # PostgreSQL driver for direct connections
```

## Next Steps

1. **Immediate**: Run manual SQL fix in Supabase SQL Editor (see `docs/MANUAL_SCHEMA_FIX.md`)
2. **Optional**: Add DATABASE_URL to `.env` for automated tools
3. **Verify**: Run full diagnostic to confirm no remaining issues
4. **Upload**: Proceed with uploading 2,045 knowledge atoms

## See Also

- `docs/MANUAL_SCHEMA_FIX.md` - Quick SQL fix (no setup required)
- `.env.example` - DATABASE_URL configuration examples
- `docs/supabase_complete_schema.sql` - Complete expected schema
