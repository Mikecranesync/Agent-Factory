# RIVET Pro - Database Setup Guide
## Phase 1: Deploying PostgreSQL Schema to Neon

This guide walks you through deploying the RIVET Pro database schema to Neon PostgreSQL.

---

## Prerequisites

### 1. Neon PostgreSQL Account
- Sign up at https://console.neon.tech (free tier available)
- Create a new project or use an existing one
- Note your database connection string

### 2. PostgreSQL Client (psql)
Choose your platform:

**macOS:**
```bash
brew install postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-client
```

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Or use chocolatey: `choco install postgresql`

**Verify installation:**
```bash
psql --version
# Should output: psql (PostgreSQL) 14.0 or higher
```

---

## Step 1: Get Your Neon Connection String

1. Log into Neon Console: https://console.neon.tech
2. Select your project
3. Click **"Connection Details"** in the sidebar
4. Copy the connection string that looks like:
   ```
   postgresql://user:password@ep-cool-sound-12345.us-east-2.aws.neon.tech/rivet_db?sslmode=require
   ```

**Important:** Keep this secure! Never commit it to Git.

---

## Step 2: Set Environment Variable

**macOS/Linux (Bash/Zsh):**
```bash
export NEON_DB_URL="postgresql://user:password@host.neon.tech/database?sslmode=require"
```

**Windows (PowerShell):**
```powershell
$env:NEON_DB_URL="postgresql://user:password@host.neon.tech/database?sslmode=require"
```

**Windows (Command Prompt):**
```cmd
set NEON_DB_URL=postgresql://user:password@host.neon.tech/database?sslmode=require
```

**Verify it's set:**
```bash
# macOS/Linux
echo $NEON_DB_URL

# Windows PowerShell
echo $env:NEON_DB_URL
```

---

## Step 3: Deploy the Schema

### Option A: Automated Deployment (Recommended)

**macOS/Linux:**
```bash
# Navigate to project root
cd ~/OneDrive/Desktop/rivet-test

# Make script executable
chmod +x scripts/deploy_schema.sh

# Run deployment
./scripts/deploy_schema.sh
```

**Windows PowerShell:**
```powershell
# Navigate to project root
cd C:\Users\hharp\OneDrive\Desktop\rivet-test

# Run deployment
.\scripts\deploy_schema.ps1
```

The script will:
- ✅ Check prerequisites (psql installed, NEON_DB_URL set)
- ✅ Display schema information
- ✅ Confirm deployment
- ✅ Deploy all tables and functions
- ✅ Run verification tests
- ✅ Create test user and verify functionality
- ✅ Clean up test data

### Option B: Manual Deployment

```bash
cd ~/OneDrive/Desktop/rivet-test
psql "$NEON_DB_URL" -f sql/rivet_pro_schema.sql
```

### Option C: Neon SQL Editor

1. Open Neon Console
2. Go to **SQL Editor** tab
3. Copy the entire contents of `sql/rivet_pro_schema.sql`
4. Paste into the editor
5. Click **Run** or press `Ctrl+Enter`

---

## Step 4: Verify Deployment

### Quick Verification
```bash
psql "$NEON_DB_URL" -f scripts/verify_schema.sql
```

This runs 12 comprehensive tests including:
- Table existence checks
- Index verification
- Function testing
- Free tier limit enforcement
- Pro tier unlimited access
- Print session management
- Full user journey simulation

### Manual Verification

**Check tables exist:**
```sql
psql "$NEON_DB_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'rivet_%';"
```

Expected output:
```
 table_name
─────────────────────
 rivet_print_sessions
 rivet_stripe_events
 rivet_usage_log
 rivet_users
(4 rows)
```

**Test a function:**
```sql
psql "$NEON_DB_URL" -c "SELECT * FROM get_or_create_user(123456789, 'test', 'Test User');"
```

Should return user data with `is_new_user = true`.

---

## Step 5: Understand the Schema

### Tables Overview

#### `rivet_users`
**Purpose:** Core user management with Telegram & Stripe integration

**Key Fields:**
- `telegram_id` - Unique Telegram user identifier
- `is_pro` - Boolean: Pro subscription status
- `tier` - Enum: 'free', 'pro', 'team'
- `stripe_customer_id` - Links to Stripe customer
- `stripe_subscription_id` - Active subscription
- `lookup_count` - Monthly lookup counter (resets every 30 days)
- `lookup_reset_at` - When counter resets

**Indexes:**
- Fast Telegram ID lookup
- Fast Stripe customer lookup
- Tier-based queries

#### `rivet_usage_log`
**Purpose:** Analytics and usage tracking

**Key Fields:**
- `action_type` - photo_lookup, chat_print, manual_search, command
- `request_data` - JSONB: Full request context
- `tokens_used` - Claude API token consumption
- `latency_ms` - Response time tracking
- `workflow_id` - Which n8n workflow processed this

**Use Cases:**
- Billing/usage analytics
- Performance monitoring
- User behavior analysis

#### `rivet_print_sessions`
**Purpose:** Chat with Print-it feature (Pro only)

**Key Fields:**
- `pdf_file_id` - Telegram file reference
- `pdf_base64` - Stored PDF data for Claude API
- `conversation_history` - JSONB: Full chat context
- `is_active` - Boolean: Session state
- `questions_asked` - Counter for analytics

**Indexes:**
- Active session lookup (filtered index)
- User session history

#### `rivet_stripe_events`
**Purpose:** Webhook event logging for debugging

**Key Fields:**
- `stripe_event_id` - Unique event ID (prevents duplicates)
- `event_type` - checkout.session.completed, etc.
- `payload` - JSONB: Full Stripe webhook payload
- `processed` - Boolean: Processing status

---

### Functions Overview

#### User Management

**`get_or_create_user(telegram_id, username, first_name)`**
- Creates user if doesn't exist
- Updates last_active_at on every call
- Auto-resets monthly lookup counter if expired
- Returns: user_id, is_pro, tier, lookup_count, lookups_remaining, is_new_user

**`get_user_status(telegram_id)`**
- Used for `/status` command
- Returns: tier, lookup counts, subscription info, days until reset

#### Usage Tracking

**`check_and_increment_lookup(telegram_id)`**
- **THE CORE FUNCTION** - Call this before every photo lookup
- Auto-creates user if doesn't exist
- Enforces 10 lookup limit for free tier
- Pro users always allowed (returns 999 remaining)
- Increments counter on success
- Returns: allowed (boolean), remaining (int), is_pro (boolean), user_id, message

**Usage in n8n:**
```
Telegram Trigger → check_and_increment_lookup() → IF allowed? → Process Photo
                                                  → ELSE → Send Upgrade Prompt
```

#### Stripe Integration

**`update_subscription(telegram_id, customer_id, subscription_id, status, is_pro)`**
- Called from Stripe webhook workflow
- Updates user subscription status
- Sets/removes Pro access
- Updates tier automatically

**Webhook events to handle:**
- `checkout.session.completed` → Set is_pro = TRUE
- `customer.subscription.deleted` → Set is_pro = FALSE
- `invoice.payment_failed` → Send warning to user

#### Print Sessions (Pro Feature)

**`start_print_session(telegram_id, pdf_file_id, pdf_name, pdf_base64)`**
- Checks if user is Pro (returns error if not)
- Ends any existing active session
- Creates new session with PDF data
- Returns: session_id, success, message

**`get_active_print_session(telegram_id)`**
- Returns active session with full PDF and conversation history
- Used when user sends a question
- Returns: session_id, pdf_base64, pdf_name, conversation_history, message_count

**`add_print_message(session_id, role, content)`**
- Appends message to conversation_history JSONB array
- role = 'user' or 'assistant'
- Updates last_message_at timestamp

**`end_print_session(telegram_id)`**
- Closes active session
- Returns summary with questions_answered count

---

## Step 6: Test the Free Tier Limit

**Simulate a free user:**
```sql
-- Create user
SELECT * FROM get_or_create_user(999888777, 'freetester', 'Free');

-- Send 10 lookups
SELECT allowed, remaining, message
FROM check_and_increment_lookup(999888777);
-- Repeat 10 times (or use generate_series)

-- 11th lookup should fail
SELECT allowed, remaining, message
FROM check_and_increment_lookup(999888777);
-- Expected: allowed = FALSE, remaining = 0, message = "Free limit reached..."
```

---

## Step 7: Test Pro Tier Access

**Simulate subscription:**
```sql
-- Upgrade user to Pro
SELECT update_subscription(
    999888777,
    'cus_test123',
    'sub_test123',
    'active',
    TRUE
);

-- Verify unlimited access
SELECT allowed, remaining, is_pro, message
FROM check_and_increment_lookup(999888777);
-- Expected: allowed = TRUE, remaining = 999, is_pro = TRUE
```

---

## Step 8: Test Print Sessions

**Simulate PDF upload:**
```sql
-- Start session (Pro user required)
SELECT * FROM start_print_session(
    999888777,
    'telegram_file_id_abc123',
    'electrical_schematic_rev3.pdf',
    'JVBERi0xLjQKJeLjz9MKMy...'  -- Base64 PDF data
);

-- Get session
SELECT * FROM get_active_print_session(999888777);

-- Add user question
SELECT add_print_message(
    (SELECT id FROM rivet_print_sessions WHERE telegram_id = 999888777 AND is_active = TRUE LIMIT 1),
    'user',
    'What does breaker B123 control?'
);

-- Add Claude response
SELECT add_print_message(
    (SELECT id FROM rivet_print_sessions WHERE telegram_id = 999888777 AND is_active = TRUE LIMIT 1),
    'assistant',
    'Breaker B123 controls the main panel feed on page 12...'
);

-- End session
SELECT * FROM end_print_session(999888777);
```

---

## Step 9: Clean Up Test Data

```sql
-- Remove test users
DELETE FROM rivet_print_sessions WHERE telegram_id IN (123456789, 999888777);
DELETE FROM rivet_usage_log WHERE telegram_id IN (123456789, 999888777);
DELETE FROM rivet_users WHERE telegram_id IN (123456789, 999888777);

-- Verify cleanup
SELECT COUNT(*) FROM rivet_users WHERE telegram_id < 1000000000;
-- Expected: 0
```

---

## Troubleshooting

### Error: "psql: command not found"
**Solution:** Install PostgreSQL client (see Prerequisites)

### Error: "NEON_DB_URL environment variable not set"
**Solution:** Set the environment variable with your connection string (see Step 2)

### Error: "connection refused" or "timeout"
**Solution:**
- Verify connection string is correct
- Check if Neon project is active (not paused)
- Ensure `?sslmode=require` is in connection string
- Try accessing from Neon Console SQL Editor

### Error: "permission denied for schema public"
**Solution:**
- Your Neon user might not have sufficient permissions
- Run from Neon Console with project owner account
- Or grant permissions: `GRANT ALL ON SCHEMA public TO your_user;`

### Error: "relation already exists"
**Solution:**
- Schema already deployed (not an error!)
- To redeploy, first drop tables (see Rollback section)

---

## Rollback / Reset

**⚠️ WARNING: This destroys ALL data!**

```sql
-- Drop all tables (cascades to related data)
DROP TABLE IF EXISTS rivet_stripe_events CASCADE;
DROP TABLE IF EXISTS rivet_print_sessions CASCADE;
DROP TABLE IF EXISTS rivet_usage_log CASCADE;
DROP TABLE IF EXISTS rivet_users CASCADE;

-- Drop all functions
DROP FUNCTION IF EXISTS get_or_create_user CASCADE;
DROP FUNCTION IF EXISTS check_and_increment_lookup CASCADE;
DROP FUNCTION IF EXISTS update_subscription CASCADE;
DROP FUNCTION IF EXISTS get_user_status CASCADE;
DROP FUNCTION IF EXISTS start_print_session CASCADE;
DROP FUNCTION IF EXISTS get_active_print_session CASCADE;
DROP FUNCTION IF EXISTS add_print_message CASCADE;
DROP FUNCTION IF EXISTS end_print_session CASCADE;

-- Now redeploy
psql "$NEON_DB_URL" -f sql/rivet_pro_schema.sql
```

---

## What's Next?

After Phase 1 is complete:

### Phase 2: Create n8n Workflows
1. `rivet_usage_tracker.json` - Wraps photo bot with usage limits
2. `rivet_stripe_checkout.json` - Handles /upgrade command
3. `rivet_stripe_webhook.json` - Processes Stripe events
4. `rivet_chat_with_print.json` - Chat with Print-it (Pro feature)
5. `rivet_commands.json` - Bot commands (/start, /help, /status, /end_chat)

### Phase 3: Stripe Configuration
- Create "RIVET Pro" product
- Set price to $29/month
- Configure webhook endpoint
- Test payment flow

### Phase 4: Testing & Validation
- Test free user journey (10 lookup limit)
- Test Pro user journey (unlimited + Chat with Print)
- Verify Stripe integration end-to-end

---

## Support & Resources

**Documentation:**
- Neon PostgreSQL: https://neon.tech/docs
- n8n: https://docs.n8n.io
- Stripe: https://stripe.com/docs

**Project Files:**
- Schema: `sql/rivet_pro_schema.sql`
- Deployment Scripts: `scripts/deploy_schema.sh`, `scripts/deploy_schema.ps1`
- Verification: `scripts/verify_schema.sql`
- Sprint Doc: `RIVET_PRO_SPRINT_CLAUDE_CLI.md`

**Need Help?**
- Check `docs/DEPLOYMENT_LOG.md` for deployment history
- Review error messages in terminal output
- Test individual queries in Neon Console SQL Editor

---

**Version:** 1.0
**Last Updated:** January 2026
**Status:** Phase 1 - Database Schema Deployment
