# RIVET Pro - Stripe Setup Guide

**Purpose:** Configure Stripe for RIVET Pro $29/month subscription
**Created:** January 8, 2026
**Status:** Phase 3 - Stripe Configuration

---

## Prerequisites

Before starting:
- ✅ Phase 1 complete (Database schema deployed)
- ✅ Phase 2 complete (n8n workflows created)
- Stripe account created (test mode first, then production)
- Access to n8n at http://72.60.175.144:5678

---

## Part 1: Stripe Dashboard Setup

### Step 1.1: Create RIVET Pro Product

1. **Navigate to Products**
   - Go to: https://dashboard.stripe.com/products
   - Click **"+ Add product"**

2. **Configure Product**
   ```
   Name: RIVET Pro
   Description: Unlimited equipment lookups + Chat with Print-it
   ```

3. **Configure Pricing**
   ```
   Pricing model: Standard pricing
   Price: $29.00 USD
   Billing period: Monthly
   ```

4. **Additional Settings**
   - Currency: USD
   - Tax behavior: Exclusive (or per your requirements)
   - Click **"Save product"**

5. **Copy Price ID**
   - After saving, you'll see a Price ID like `price_1AbCdEfGhIjKlMnO`
   - **CRITICAL:** Copy this - you'll need it in Step 2.3

---

### Step 1.2: Create Webhook Endpoint

1. **Navigate to Webhooks**
   - Go to: https://dashboard.stripe.com/webhooks
   - Click **"Add endpoint"**

2. **Configure Endpoint**
   ```
   Endpoint URL: http://72.60.175.144:5678/webhook/stripe-webhook-rivet
   Description: RIVET Pro subscription events
   ```

3. **Select Events to Listen For**

   Click **"Select events"** and choose:
   - ✅ `checkout.session.completed` - When user completes payment
   - ✅ `customer.subscription.deleted` - When subscription is cancelled
   - ✅ `invoice.payment_failed` - When payment fails

4. **Add Endpoint**
   - Click **"Add endpoint"**
   - The webhook is created

5. **Optional: Copy Webhook Secret**
   - Click on your new webhook
   - Click **"Reveal signing secret"**
   - Copy the secret (starts with `whsec_`)
   - **Note:** n8n's webhook node doesn't require this for validation, but it's good to have for debugging

---

### Step 1.3: Test Mode vs Live Mode

**For Development/Testing:**
- Use **Test Mode** (toggle in top right)
- Use test API keys (start with `sk_test_`)
- Use test card: 4242 4242 4242 4242

**For Production:**
- Switch to **Live Mode**
- Use live API keys (start with `sk_live_`)
- Real payments will be processed

**⚠️ Important:** Keep test and live configurations separate. Test thoroughly in test mode before going live.

---

## Part 2: n8n Configuration

### Step 2.1: Create Neon RIVET Credential

1. **Open n8n**: http://72.60.175.144:5678
2. **Navigate to Credentials**
   - Click your profile (bottom left)
   - Select **"Credentials"**
   - Click **"+ Add Credential"**

3. **Select PostgreSQL**
   - Search for "Postgres"
   - Click **"Postgres"**

4. **Configure Connection**
   ```
   Name: Neon RIVET
   Host: ep-purple-hall-ahimeyn0-pooler.c-3.us-east-1.aws.neon.tech
   Database: neondb
   User: neondb_owner
   Password: npg_c3UNa4KOlCeL
   Port: 5432
   SSL: Required ✅
   ```

5. **Test Connection**
   - Click **"Test"**
   - Should see "Connection successful ✅"
   - Click **"Save"**

---

### Step 2.2: Create Stripe RIVET Credential

1. **Get Stripe Secret Key**
   - Go to: https://dashboard.stripe.com/apikeys
   - **Test Mode:** Copy "Secret key" (starts with `sk_test_`)
   - **Live Mode:** Copy "Secret key" (starts with `sk_live_`)

2. **In n8n Credentials**
   - Click **"+ Add Credential"**
   - Search for "Stripe"
   - Click **"Stripe API"**

3. **Configure**
   ```
   Name: Stripe RIVET
   Secret Key: sk_test_... (or sk_live_... for production)
   ```

4. **Save**
   - Click **"Save"**

---

### Step 2.3: Update Stripe Price ID in Workflow

**Critical Step:** Replace placeholder with actual Price ID

1. **Open Stripe Checkout Workflow**
   - In n8n, go to **Workflows**
   - Open: **"TEST - RIVET - Stripe Checkout"**

2. **Find "Create Stripe Checkout" Node**
   - Click the node
   - Find the `lineItems` configuration

3. **Replace Price ID**

   **Before:**
   ```json
   "priceId": "REPLACE_WITH_STRIPE_PRICE_ID"
   ```

   **After:**
   ```json
   "priceId": "price_1AbCdEfGhIjKlMnO"
   ```
   (Use your actual Price ID from Step 1.1)

4. **Save Workflow**
   - Click **"Save"** in top right

---

### Step 2.4: Optional - Create Anthropic Credential

For Chat with Print-it feature (currently has placeholder):

1. **Get Anthropic API Key**
   - Go to: https://console.anthropic.com/
   - Navigate to API Keys
   - Create new key, copy it (starts with `sk-ant-`)

2. **In n8n**
   - Add credential
   - Search for "Anthropic" or "LangChain"
   - Select **"Anthropic"** or **"LangChain Chat Model"**

3. **Configure**
   ```
   Name: Anthropic Claude
   API Key: sk-ant-...
   ```

4. **Update Workflow**
   - Open: **"TEST - RIVET - Chat with Print"**
   - Replace the "Claude Chat (PLACEHOLDER)" NoOp node
   - Add an Anthropic/LangChain node
   - Configure to send PDF base64 + user question

---

## Part 3: Import and Activate Workflows

### Step 3.1: Import Workflows to n8n

**Option A: Manual Import (Recommended)**

For each workflow file:

1. **Open n8n**: http://72.60.175.144:5678
2. Click **"+"** → **"Import from File"**
3. Upload workflow JSON:
   - `n8n/workflows/test/rivet_commands.json`
   - `n8n/workflows/test/rivet_stripe_webhook.json`
   - `n8n/workflows/test/rivet_stripe_checkout.json`
   - `n8n/workflows/test/rivet_chat_with_print.json`
   - `n8n/workflows/test/rivet_usage_tracker.json`

4. For each imported workflow:
   - **Configure Credentials**
     - Click each node with a credential
     - Select from dropdown (e.g., "Neon RIVET", "Stripe RIVET")
   - **Save Workflow**
   - **DO NOT ACTIVATE YET** (wait for testing)

---

**Option B: API Import**

If you have n8n API access:

```bash
# Set environment variables
export N8N_URL="http://72.60.175.144:5678"
export N8N_API_KEY="your_n8n_api_key"

# Import all workflows
cd n8n/workflows/test

for file in *.json; do
  echo "Importing $file..."
  curl -X POST "$N8N_URL/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$file"
done
```

**Note:** You'll still need to configure credentials in the UI.

---

### Step 3.2: Activation Order (IMPORTANT)

Activate workflows in this specific order to avoid errors:

1. ✅ **Commands** (`rivet_commands.json`)
   - **Why first:** No external dependencies, just sends messages
   - **Test:** Send `/start`, `/help` to bot

2. ✅ **Stripe Webhook** (`rivet_stripe_webhook.json`)
   - **Why second:** Must be active before checkout creates events
   - **Test:** Use Stripe CLI to send test event (see Part 4)

3. ✅ **Stripe Checkout** (`rivet_stripe_checkout.json`)
   - **Why third:** Depends on webhook being ready
   - **Test:** Send `/upgrade` to bot

4. ✅ **Chat with Print** (`rivet_chat_with_print.json`)
   - **Why fourth:** Pro feature, needs database in working state
   - **Test:** Upload PDF as Pro user

5. ✅ **Usage Tracker** (`rivet_usage_tracker.json`)
   - **Why last:** Replaces main photo processing flow
   - **Test:** Send 11 photos as free user

**⚠️ Important:** Keep your existing production photo bot active until usage tracker is fully tested!

---

## Part 4: Testing

### Step 4.1: Test Commands Workflow

**Test /start**
```
1. Open Telegram
2. Open @rivet_local_dev_bot
3. Send: /start
4. Expected: Welcome message with quick start guide
```

**Test /help**
```
Send: /help
Expected: Full feature list and usage instructions
```

**Test /status (new user)**
```
Send: /status
Expected: "You haven't used RIVET yet!"
```

---

### Step 4.2: Test Stripe Webhook (Using Stripe CLI)

**Install Stripe CLI** (if not installed):
```bash
# macOS
brew install stripe/stripe-cli/stripe

# Windows
scoop install stripe

# Linux
wget https://github.com/stripe/stripe-cli/releases/download/v1.18.0/stripe_1.18.0_linux_x86_64.tar.gz
```

**Login to Stripe**
```bash
stripe login
```

**Forward webhooks to local n8n** (for testing):
```bash
stripe listen --forward-to http://72.60.175.144:5678/webhook/stripe-webhook-rivet
```

**Trigger test event**
```bash
# Test checkout completion
stripe trigger checkout.session.completed

# Expected:
# 1. Webhook receives event
# 2. Database updated (is_pro = true)
# 3. Telegram message sent to user
```

**Verify database update**
```sql
-- Connect to Neon
SELECT telegram_id, is_pro, tier, subscription_status
FROM rivet_users
ORDER BY updated_at DESC
LIMIT 5;
```

---

### Step 4.3: Test Stripe Checkout Flow

**Create test user**
```
1. Open Telegram bot
2. Send a photo (creates user in database)
3. Check database:
   SELECT * FROM rivet_users WHERE telegram_id = YOUR_TELEGRAM_ID;
```

**Test /upgrade command**
```
1. Send: /upgrade
2. Expected: Checkout link with inline button
3. Click button
4. Expected: Stripe checkout page with $29/month
```

**Complete test payment**
```
Card: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

**Verify activation**
```
1. Complete payment
2. Expected: "🎉 Welcome to RIVET Pro!" message in Telegram
3. Check database:
   SELECT is_pro, tier FROM rivet_users WHERE telegram_id = YOUR_ID;
   -- Should show: is_pro = true, tier = 'pro'
```

---

### Step 4.4: Test Usage Tracker

**Test as free user**
```
1. Create new Telegram account OR reset lookup_count in database
2. Send 10 photos
3. Expected: Each photo processed normally
4. Send 11th photo
5. Expected: "You've used all 10 free lookups this month!" message
```

**Verify database**
```sql
SELECT telegram_id, lookup_count, is_pro
FROM rivet_users
WHERE telegram_id = YOUR_TELEGRAM_ID;

-- Free user should show lookup_count = 10
```

**Test as Pro user**
```
1. Upgrade user to Pro (via /upgrade or manual DB update)
2. Send 15+ photos
3. Expected: All photos processed, no limit reached message
```

---

### Step 4.5: Test Chat with Print

**Test as non-Pro user**
```
1. Upload a PDF to bot
2. Expected: "🔒 Chat with Print-it is a Pro feature!" message
```

**Test as Pro user**
```
1. Upgrade to Pro
2. Upload a PDF
3. Expected: "📄 Print indexed successfully!"
4. Send text: "What's on page 1?"
5. Expected: Placeholder response (or Claude response if API configured)
6. Send: /end_chat
7. Expected: "✅ Session closed successfully"
```

**Verify session in database**
```sql
SELECT session_id, pdf_name, is_active
FROM rivet_print_sessions
WHERE telegram_id = YOUR_TELEGRAM_ID
ORDER BY created_at DESC
LIMIT 1;
```

---

## Part 5: Troubleshooting

### Issue: "Credential not found"

**Cause:** Workflow references credential that doesn't exist in n8n

**Fix:**
1. Open workflow in n8n
2. Click node showing credential error
3. In dropdown, select correct credential:
   - PostgreSQL nodes → "Neon RIVET"
   - Stripe nodes → "Stripe RIVET"
   - Telegram nodes → "Telegram Bot"
4. Save workflow

---

### Issue: Stripe Checkout Returns 404

**Possible Causes:**
- Wrong Price ID
- Stripe in wrong mode (test vs live)
- Price not active

**Fix:**
1. Verify Price ID in Stripe dashboard
2. Ensure Stripe credential uses matching key (test vs live)
3. Check Price is active in Stripe dashboard

---

### Issue: Webhook Not Receiving Events

**Possible Causes:**
- Workflow not activated
- Wrong webhook URL
- Firewall blocking webhook

**Fix:**
1. Ensure "TEST - RIVET - Stripe Webhook" is activated
2. Verify webhook URL in Stripe dashboard:
   ```
   http://72.60.175.144:5678/webhook/stripe-webhook-rivet
   ```
3. Test accessibility:
   ```bash
   curl http://72.60.175.144:5678/webhook-test/stripe-webhook-rivet
   ```

**Check Stripe webhook logs:**
1. Go to: https://dashboard.stripe.com/webhooks
2. Click your webhook
3. View "Recent deliveries"
4. Check for delivery failures

---

### Issue: Database Connection Errors

**Possible Causes:**
- Wrong connection string
- SSL not enabled
- Neon database in sleep mode

**Fix:**
1. Verify connection details in n8n credential
2. Ensure SSL is enabled
3. Test connection from n8n credential screen
4. Check Neon dashboard for database status

---

### Issue: Usage Limit Not Working

**Possible Causes:**
- Database function not deployed
- lookup_count not incrementing
- wrong query

**Fix:**
1. Verify function exists:
   ```sql
   SELECT routine_name
   FROM information_schema.routines
   WHERE routine_name = 'check_and_increment_lookup';
   ```

2. Test function manually:
   ```sql
   SELECT * FROM check_and_increment_lookup(123456789);
   ```

3. Check user's lookup_count:
   ```sql
   SELECT telegram_id, lookup_count, is_pro
   FROM rivet_users
   WHERE telegram_id = YOUR_ID;
   ```

---

## Part 6: Go Live Checklist

Before switching to production:

### 6.1: Stripe Configuration
- [ ] Create live Stripe product ($29/month)
- [ ] Copy live Price ID
- [ ] Update workflow with live Price ID
- [ ] Configure live webhook endpoint
- [ ] Test live webhook delivery

### 6.2: n8n Configuration
- [ ] Create new Stripe credential with live API key
- [ ] Update all Stripe nodes to use live credential
- [ ] Test /upgrade with live Stripe (don't complete payment)
- [ ] Verify webhook receives live events

### 6.3: Testing
- [ ] Test free user journey (10 lookup limit)
- [ ] Test Pro upgrade flow (use real payment method)
- [ ] Test Pro features (unlimited lookups, Chat with Print)
- [ ] Test subscription cancellation flow
- [ ] Test payment failure handling

### 6.4: Monitoring
- [ ] Set up Stripe email notifications
- [ ] Monitor n8n execution logs
- [ ] Monitor database for errors
- [ ] Set up revenue tracking in Stripe

### 6.5: Rollback Plan
- [ ] Document how to revert to production bot
- [ ] Keep production workflow ID: 7LMKcMmldZsu1l6g
- [ ] Backup database before go-live
- [ ] Test rollback procedure

---

## Part 7: Post-Launch

### Monitor These Metrics

**Stripe Dashboard:**
- Monthly Recurring Revenue (MRR)
- Churn rate
- Failed payments
- Subscription count

**Database:**
```sql
-- Pro user count
SELECT COUNT(*) FROM rivet_users WHERE is_pro = true;

-- Free users hitting limit
SELECT COUNT(*) FROM rivet_users WHERE lookup_count >= 10 AND is_pro = false;

-- Usage trends
SELECT DATE(created_at), COUNT(*)
FROM rivet_usage_log
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY DATE(created_at);
```

**n8n Execution Logs:**
- Monitor for workflow errors
- Check webhook delivery success rate
- Review failed executions

---

## Quick Reference

### Stripe Price ID
**Location:** Workflows → rivet_stripe_checkout.json → Create Stripe Checkout node
**Format:** `price_1AbCdEfGhIjKlMnO`

### Webhook URL
**Production:** `http://72.60.175.144:5678/webhook/stripe-webhook-rivet`
**Configure at:** https://dashboard.stripe.com/webhooks

### Database Functions Used
- `get_or_create_user()` - User management
- `check_and_increment_lookup()` - Usage tracking
- `update_subscription()` - Stripe event handling
- `get_user_status()` - /status command
- `start_print_session()` - PDF upload
- `get_active_print_session()` - Chat messages
- `add_print_message()` - Save conversation
- `end_print_session()` - /end_chat command

### n8n Credentials Required
- **Telegram Bot** (existing: `if4EOJbvMirfWqCC`)
- **Neon RIVET** (PostgreSQL - create new)
- **Stripe RIVET** (Stripe API - create new)
- **Anthropic Claude** (optional - for Chat with Print)

---

## Next Steps

After completing Stripe setup:

1. **Test thoroughly** in test mode
2. **Create live Stripe products** when ready
3. **Switch to live credentials** in n8n
4. **Monitor first Pro users** closely
5. **Iterate based on feedback**

---

**Status:** Phase 3 Documentation Complete
**Next:** Phase 4 - Production Deployment

