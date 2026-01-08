# RIVET Pro Sprint - Claude CLI Execution Prompt
## Build Date: January 2026 | Target: Sellable by Next Weekend

---

## MISSION

Build RIVET Pro's monetization layer: **usage tracking**, **Stripe payments**, and **Chat with Print-it** feature. Deploy as n8n workflows to the test repo without breaking existing production workflows.

**End State:** 
- Free tier: 10 lookups/month
- Pro tier: $29/month - unlimited lookups + Chat with Print-it
- All payments via Stripe
- All workflows using NATIVE n8n nodes (NO HTTP Request when native exists)

---

## INFRASTRUCTURE CONTEXT

| Resource | Value |
|----------|-------|
| VPS | 72.60.175.144 |
| n8n URL | http://72.60.175.144:5678 |
| n8n API Key | Starts with `eyJhbG...` (check .env) |
| Production Workflow ID | `7LMKcMmldZsu1l6g` |
| Production Webhook Path | `rivet-photo-bot-v2` |
| Telegram Bot | @rivet_local_dev_bot |
| Telegram Token | `8161680636:AAGF8eyldKWGF2I0qVSWXxveonRy02GH_nE` |
| Telegram Credential ID | `if4EOJbvMirfWqCC` |
| Database | Neon PostgreSQL |
| ngrok | For webhook tunneling |

---

## PHASE 0: SETUP WORKTREE & TEST REPO

### Step 0.1: Create GitHub Test Repo

```bash
# From Agent Factory root
cd ~/OneDrive/Desktop/Agent\ Factory

# Create rivet-test as a worktree (isolated from main)
git worktree add -b rivet-test-sprint ../rivet-test origin/main

# Enter the worktree
cd ../rivet-test

# Create project structure
mkdir -p n8n/workflows/{production,test,templates}
mkdir -p docs scripts sql
```

### Step 0.2: Export Existing Workflows from VPS

Use n8n MCP to pull existing workflows:

```bash
# List all workflows on VPS
# (Configure MCP to point to VPS first)
```

Or manually via API:

```bash
curl -X GET "http://72.60.175.144:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: YOUR_API_KEY" \
  | jq '.' > n8n/workflows/production/existing_workflows.json
```

### Step 0.3: Create CLAUDE.md Protection File

Create `CLAUDE.md` in the rivet-test root:

```markdown
# RIVET Test Repo - Claude CLI Rules

## NEVER DO
- Modify files in `n8n/workflows/production/` - these are backups
- Use HTTP Request node when a native n8n node exists
- Hardcode API keys in workflow JSON
- Deploy directly to production workflow ID `7LMKcMmldZsu1l6g`

## ALWAYS DO
- Use native n8n nodes (Telegram, Stripe, Postgres, etc.)
- Reference credentials by ID, not by embedding secrets
- Test workflows in n8n UI before marking complete
- Add workflows to `n8n/workflows/test/` first
- Validate workflow JSON before committing

## CREDENTIAL IDS (Existing)
- Telegram: `if4EOJbvMirfWqCC`
- Anthropic: [CREATE NEW - name it "Anthropic Claude"]
- Stripe: [CREATE NEW - name it "Stripe RIVET"]
- Neon PostgreSQL: [CREATE NEW - name it "Neon RIVET"]

## WORKFLOW NAMING CONVENTION
- Production: `RIVET Pro - [Feature Name]`
- Test: `TEST - RIVET - [Feature Name]`
```

---

## PHASE 1: DATABASE SCHEMA (Neon PostgreSQL)

### Step 1.1: Create Users & Usage Table

Create `sql/001_users_and_usage.sql`:

```sql
-- RIVET Pro User Management
-- Run against Neon PostgreSQL

CREATE TABLE IF NOT EXISTS rivet_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(100),
    telegram_first_name VARCHAR(100),
    is_pro BOOLEAN DEFAULT FALSE,
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    subscription_status VARCHAR(20) DEFAULT 'none', -- none, active, cancelled, past_due
    subscription_started_at TIMESTAMP,
    subscription_ends_at TIMESTAMP,
    lookup_count INTEGER DEFAULT 0,
    lookup_reset_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rivet_users_telegram ON rivet_users(telegram_id);
CREATE INDEX idx_rivet_users_stripe ON rivet_users(stripe_customer_id);

-- Usage log for analytics
CREATE TABLE IF NOT EXISTS rivet_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    telegram_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- photo_lookup, chat_print, manual_search
    request_data JSONB,
    response_summary TEXT,
    tokens_used INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rivet_usage_user ON rivet_usage_log(user_id);
CREATE INDEX idx_rivet_usage_date ON rivet_usage_log(created_at DESC);

-- Chat with Print sessions
CREATE TABLE IF NOT EXISTS rivet_print_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    telegram_id BIGINT NOT NULL,
    pdf_url TEXT,
    pdf_name VARCHAR(255),
    pdf_base64 TEXT, -- Store for Claude API
    conversation_history JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rivet_print_sessions_user ON rivet_print_sessions(telegram_id, is_active);

-- Function to reset monthly lookups
CREATE OR REPLACE FUNCTION reset_monthly_lookups()
RETURNS void AS $$
BEGIN
    UPDATE rivet_users
    SET lookup_count = 0,
        lookup_reset_at = NOW()
    WHERE lookup_reset_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Function to increment lookup and check limit
CREATE OR REPLACE FUNCTION check_and_increment_lookup(p_telegram_id BIGINT)
RETURNS TABLE (
    allowed BOOLEAN,
    remaining INTEGER,
    is_pro BOOLEAN,
    user_id UUID
) AS $$
DECLARE
    v_user rivet_users%ROWTYPE;
BEGIN
    -- Get or create user
    INSERT INTO rivet_users (telegram_id)
    VALUES (p_telegram_id)
    ON CONFLICT (telegram_id) DO NOTHING;
    
    SELECT * INTO v_user FROM rivet_users WHERE telegram_id = p_telegram_id;
    
    -- Reset if needed
    IF v_user.lookup_reset_at < NOW() - INTERVAL '30 days' THEN
        UPDATE rivet_users SET lookup_count = 0, lookup_reset_at = NOW()
        WHERE telegram_id = p_telegram_id;
        v_user.lookup_count := 0;
    END IF;
    
    -- Pro users always allowed
    IF v_user.is_pro THEN
        RETURN QUERY SELECT TRUE, 999, TRUE, v_user.id;
        RETURN;
    END IF;
    
    -- Free users: check limit
    IF v_user.lookup_count >= 10 THEN
        RETURN QUERY SELECT FALSE, 0, FALSE, v_user.id;
        RETURN;
    END IF;
    
    -- Increment and return
    UPDATE rivet_users SET lookup_count = lookup_count + 1, updated_at = NOW()
    WHERE telegram_id = p_telegram_id;
    
    RETURN QUERY SELECT TRUE, (10 - v_user.lookup_count - 1)::INTEGER, FALSE, v_user.id;
END;
$$ LANGUAGE plpgsql;
```

### Step 1.2: Deploy Schema

```bash
# Using psql or your preferred method
psql $NEON_DATABASE_URL -f sql/001_users_and_usage.sql
```

---

## PHASE 2: WORKFLOW 1 - USAGE TRACKING

### File: `n8n/workflows/test/rivet_usage_tracker.json`

This workflow wraps the existing photo bot and adds usage tracking.

**Flow:**
```
Telegram Trigger (photo) 
    → Postgres: check_and_increment_lookup()
    → IF allowed?
        → YES: Continue to existing OCR flow
        → NO: Send upgrade prompt
```

**CRITICAL: Use Native Nodes**

| Task | WRONG ❌ | RIGHT ✅ |
|------|----------|----------|
| Telegram messages | HTTP Request to API | `n8n-nodes-base.telegram` |
| Database queries | HTTP Request to REST | `n8n-nodes-base.postgres` |
| Conditionals | Code node | `n8n-nodes-base.if` |

### Workflow JSON Structure:

```json
{
  "name": "TEST - RIVET - Usage Tracker",
  "nodes": [
    {
      "parameters": {
        "updates": ["message"]
      },
      "id": "telegram-trigger",
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1.1,
      "position": [0, 300],
      "credentials": {
        "telegramApi": {
          "id": "if4EOJbvMirfWqCC",
          "name": "Telegram Bot"
        }
      }
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM check_and_increment_lookup({{ $json.message.from.id }})",
        "options": {}
      },
      "id": "check-usage",
      "name": "Check Usage Limit",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.5,
      "position": [220, 300],
      "credentials": {
        "postgres": {
          "id": "CREATE_NEW",
          "name": "Neon RIVET"
        }
      }
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ $json.allowed }}",
              "value2": true
            }
          ]
        }
      },
      "id": "if-allowed",
      "name": "Usage Allowed?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [440, 300]
    },
    {
      "parameters": {
        "operation": "sendMessage",
        "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
        "text": "⚡ You've used all 10 free lookups this month!\n\nUpgrade to RIVET Pro for unlimited access:\n👉 /upgrade\n\nPro includes:\n✓ Unlimited equipment lookups\n✓ Chat with your electrical prints\n✓ Priority support",
        "additionalFields": {}
      },
      "id": "send-limit-reached",
      "name": "Send Limit Reached",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [660, 450],
      "credentials": {
        "telegramApi": {
          "id": "if4EOJbvMirfWqCC",
          "name": "Telegram Bot"
        }
      }
    }
    // Continue with existing photo processing nodes...
  ],
  "connections": {
    "Telegram Trigger": {
      "main": [[{"node": "Check Usage Limit", "type": "main", "index": 0}]]
    },
    "Check Usage Limit": {
      "main": [[{"node": "Usage Allowed?", "type": "main", "index": 0}]]
    },
    "Usage Allowed?": {
      "main": [
        [{"node": "EXISTING_OCR_FLOW", "type": "main", "index": 0}],
        [{"node": "Send Limit Reached", "type": "main", "index": 0}]
      ]
    }
  }
}
```

---

## PHASE 3: WORKFLOW 2 - STRIPE CHECKOUT

### File: `n8n/workflows/test/rivet_stripe_checkout.json`

**Trigger:** `/upgrade` command from Telegram

**Flow:**
```
Telegram Trigger (text = "/upgrade")
    → Postgres: Get or create user
    → Stripe: Create Checkout Session
    → Telegram: Send checkout link
```

### Prerequisites in Stripe Dashboard:
1. Create Product: "RIVET Pro" 
2. Create Price: $29/month recurring
3. Copy Price ID (starts with `price_`)
4. Create Webhook endpoint for your domain
5. Copy Webhook Secret (starts with `whsec_`)

### Workflow Uses These Native Nodes:

- `n8n-nodes-base.telegramTrigger` - Receive /upgrade command
- `n8n-nodes-base.postgres` - Get/create Stripe customer ID
- `n8n-nodes-base.stripe` - Create Checkout Session  
- `n8n-nodes-base.telegram` - Send checkout URL

### Key Stripe Node Configuration:

```json
{
  "parameters": {
    "resource": "checkout",
    "operation": "create",
    "lineItems": {
      "item": [
        {
          "price": "price_YOUR_PRICE_ID",
          "quantity": 1
        }
      ]
    },
    "mode": "subscription",
    "successUrl": "https://t.me/rivet_local_dev_bot?start=payment_success",
    "cancelUrl": "https://t.me/rivet_local_dev_bot?start=payment_cancelled",
    "additionalFields": {
      "clientReferenceId": "={{ $('Telegram Trigger').item.json.message.from.id }}",
      "customerEmail": "",
      "metadata": {
        "metadataValues": [
          {
            "name": "telegram_id",
            "value": "={{ $('Telegram Trigger').item.json.message.from.id }}"
          }
        ]
      }
    }
  },
  "id": "stripe-checkout",
  "name": "Create Stripe Checkout",
  "type": "n8n-nodes-base.stripe",
  "typeVersion": 2,
  "credentials": {
    "stripeApi": {
      "id": "CREATE_NEW",
      "name": "Stripe RIVET"
    }
  }
}
```

---

## PHASE 4: WORKFLOW 3 - STRIPE WEBHOOK HANDLER

### File: `n8n/workflows/test/rivet_stripe_webhook.json`

**Trigger:** Stripe webhook events

**Flow:**
```
Webhook Trigger (Stripe events)
    → Switch on event type
        → checkout.session.completed: Set is_pro = true
        → customer.subscription.deleted: Set is_pro = false
        → invoice.payment_failed: Send Telegram warning
```

### Native Nodes Used:

- `n8n-nodes-base.webhook` - Receive Stripe events
- `n8n-nodes-base.switch` - Route by event type
- `n8n-nodes-base.postgres` - Update user subscription status
- `n8n-nodes-base.telegram` - Notify user

### Webhook Configuration:

```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "stripe-webhook-rivet",
    "options": {
      "rawBody": true
    }
  },
  "id": "stripe-webhook",
  "name": "Stripe Webhook",
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 2,
  "position": [0, 300],
  "webhookId": "stripe-webhook-rivet"
}
```

### Switch Node for Event Types:

```json
{
  "parameters": {
    "rules": {
      "rules": [
        {
          "value": "checkout.session.completed",
          "outputIndex": 0
        },
        {
          "value": "customer.subscription.deleted",
          "outputIndex": 1
        },
        {
          "value": "invoice.payment_failed",
          "outputIndex": 2
        }
      ]
    },
    "dataType": "string",
    "mode": "rules",
    "value": "={{ $json.body.type }}"
  },
  "id": "event-switch",
  "name": "Event Type",
  "type": "n8n-nodes-base.switch",
  "typeVersion": 3
}
```

---

## PHASE 5: WORKFLOW 4 - CHAT WITH PRINT-IT

### File: `n8n/workflows/test/rivet_chat_with_print.json`

**This is the PRO-ONLY feature.**

**Flow A: PDF Upload**
```
Telegram Trigger (document/PDF)
    → Check is_pro
    → IF Pro:
        → Download PDF
        → Convert to Base64
        → Store in rivet_print_sessions
        → Reply "Print indexed! Ask me anything about it."
    → ELSE:
        → Send upgrade prompt
```

**Flow B: Chat Message (while session active)**
```
Telegram Trigger (text, not command)
    → Check for active print session
    → IF session exists:
        → Load PDF base64 + conversation history
        → Send to Claude API with PDF + history + new question
        → Store response in history
        → Reply with answer
    → ELSE:
        → Normal flow (or prompt to upload print)
```

### Claude API Call with PDF (Native Anthropic Node):

```json
{
  "parameters": {
    "model": "claude-sonnet-4-20250514",
    "messages": {
      "values": [
        {
          "role": "user",
          "content": {
            "contentValues": [
              {
                "type": "document",
                "source": {
                  "type": "base64",
                  "mediaType": "application/pdf",
                  "data": "={{ $json.pdf_base64 }}"
                }
              },
              {
                "type": "text",
                "text": "You are RIVET, a maintenance technician's assistant. You're helping a field tech understand this electrical print/schematic.\n\nPrevious conversation:\n{{ $json.conversation_history }}\n\nTechnician's question: {{ $json.user_message }}\n\nProvide a concise, helpful answer. Reference specific components, page numbers, or wire numbers when relevant. If you can't find the answer in the document, say so."
              }
            ]
          }
        }
      ]
    },
    "options": {
      "maxTokens": 1024
    }
  },
  "id": "claude-pdf-chat",
  "name": "Claude PDF Chat",
  "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
  "typeVersion": 1,
  "credentials": {
    "anthropicApi": {
      "id": "CREATE_NEW",
      "name": "Anthropic Claude"
    }
  }
}
```

### Session Management Queries:

**Start Session:**
```sql
INSERT INTO rivet_print_sessions (user_id, telegram_id, pdf_name, pdf_base64)
VALUES (
    (SELECT id FROM rivet_users WHERE telegram_id = $1),
    $1,
    $2,
    $3
)
RETURNING id;
```

**Get Active Session:**
```sql
SELECT id, pdf_base64, conversation_history 
FROM rivet_print_sessions 
WHERE telegram_id = $1 AND is_active = TRUE
ORDER BY created_at DESC LIMIT 1;
```

**Update Conversation:**
```sql
UPDATE rivet_print_sessions 
SET conversation_history = conversation_history || $2::jsonb,
    last_message_at = NOW()
WHERE id = $1;
```

**End Session:**
```sql
UPDATE rivet_print_sessions SET is_active = FALSE WHERE telegram_id = $1;
```

---

## PHASE 6: COMMANDS WORKFLOW

### File: `n8n/workflows/test/rivet_commands.json`

Handle all slash commands in one workflow:

| Command | Action |
|---------|--------|
| `/start` | Welcome message + quick start |
| `/help` | Usage instructions |
| `/status` | Show lookups remaining, pro status |
| `/upgrade` | → Route to Stripe Checkout workflow |
| `/end_chat` | End active print session |

### Switch on Command:

```json
{
  "parameters": {
    "rules": {
      "rules": [
        { "value": "/start", "outputIndex": 0 },
        { "value": "/help", "outputIndex": 1 },
        { "value": "/status", "outputIndex": 2 },
        { "value": "/upgrade", "outputIndex": 3 },
        { "value": "/end_chat", "outputIndex": 4 }
      ]
    },
    "fallbackOutput": 5,
    "mode": "rules",
    "value": "={{ $json.message.text.split(' ')[0] }}"
  },
  "type": "n8n-nodes-base.switch"
}
```

---

## PHASE 7: CREDENTIALS SETUP

### Create These Credentials in n8n UI:

1. **Neon RIVET** (Postgres)
   - Host: Your Neon host
   - Database: Your database name
   - User: Your user
   - Password: Your password
   - SSL: Required

2. **Stripe RIVET** (Stripe)
   - Secret Key: sk_live_xxx (or sk_test_xxx for testing)
   - Webhook Secret: whsec_xxx

3. **Anthropic Claude** (Anthropic/LangChain)
   - API Key: sk-ant-xxx

4. **Telegram Bot** (already exists: `if4EOJbvMirfWqCC`)

---

## PHASE 8: DEPLOYMENT SEQUENCE

### Step 8.1: Import Workflows to n8n

```bash
# For each workflow JSON:
curl -X POST "http://72.60.175.144:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @n8n/workflows/test/rivet_usage_tracker.json
```

Or use n8n MCP:
```
n8n_create_workflow with workflow JSON
```

### Step 8.2: Configure Credentials in UI

1. Open each workflow in n8n
2. Click nodes with missing credentials
3. Create/select appropriate credential

### Step 8.3: Test Each Workflow

| Workflow | Test Method |
|----------|-------------|
| Usage Tracker | Send photo, check DB for increment |
| Stripe Checkout | Send /upgrade, verify checkout link |
| Stripe Webhook | Use Stripe CLI to send test event |
| Chat with Print | Upload PDF, ask question |
| Commands | Test each slash command |

### Step 8.4: Activate in Order

1. Commands (lowest risk)
2. Stripe Webhook (needs to be ready before Checkout)
3. Stripe Checkout
4. Chat with Print
5. Usage Tracker (replaces main photo flow)

---

## VALIDATION CHECKLIST

Before marking complete:

- [ ] All workflows use NATIVE n8n nodes
- [ ] No hardcoded API keys in JSON
- [ ] All credentials referenced by ID
- [ ] Database schema deployed to Neon
- [ ] Stripe products created ($29/month)
- [ ] Stripe webhook endpoint configured
- [ ] All workflows imported to n8n
- [ ] All workflows tested individually
- [ ] Free user hits limit at 10 lookups
- [ ] Pro user has unlimited access
- [ ] PDF upload starts chat session
- [ ] Chat session maintains context
- [ ] Payment flow: /upgrade → checkout → is_pro = true

---

## FILE STRUCTURE

```
rivet-test/
├── CLAUDE.md                              # Protection rules
├── README.md                              # Project overview
├── n8n/
│   └── workflows/
│       ├── production/                    # Backups only - DO NOT MODIFY
│       │   └── rivet_photo_bot_v2.json   # Export of working bot
│       └── test/                          # New workflows
│           ├── rivet_usage_tracker.json
│           ├── rivet_stripe_checkout.json
│           ├── rivet_stripe_webhook.json
│           ├── rivet_chat_with_print.json
│           └── rivet_commands.json
├── sql/
│   └── 001_users_and_usage.sql
├── scripts/
│   ├── deploy_schema.sh
│   ├── import_workflows.sh
│   └── test_stripe_webhook.sh
└── docs/
    ├── STRIPE_SETUP.md
    └── TESTING_GUIDE.md
```

---

## EXECUTION COMMAND

```bash
# Run with Claude CLI from Agent Factory root
cd ~/OneDrive/Desktop/Agent\ Factory

claude --dangerously-skip-permissions "Execute RIVET_PRO_SPRINT_CLAUDE_CLI.md. Start with Phase 0 worktree setup, then build each phase sequentially. Create all workflow JSON files with NATIVE n8n nodes only. Deploy SQL schema to Neon. Import workflows to n8n at 72.60.175.144:5678. Test each workflow before moving to next phase. Commit after each phase completion."
```

---

## SUCCESS METRICS

When this sprint is complete:

1. **Free User Journey:**
   - Opens bot → Gets welcome
   - Sends 10 photos → Gets analysis each time
   - Sends 11th photo → Gets "upgrade to Pro" prompt
   - Runs /status → Sees "0 of 10 remaining"

2. **Pro User Journey:**
   - Runs /upgrade → Gets Stripe checkout link
   - Completes payment → is_pro = true in database
   - Sends unlimited photos → Always gets analysis
   - Uploads PDF → "Print indexed!"
   - Asks question → Gets answer from Claude
   - Runs /end_chat → Session closed

3. **Revenue Tracking:**
   - Stripe dashboard shows subscription
   - Database has stripe_customer_id
   - Webhook updates subscription_status

---

**This is the monetization layer. Build it. Test it. Ship it.**
