# Render API Setup Guide

## Quick Start: Configure Your Render Service Automatically

**You've created a Render project and added `TELEGRAM_BOT_TOKEN`. Now let's add all the rest automatically!**

---

## Step 1: Get Your Render API Key (30 seconds)

1. **Go to Account Settings:**
   ```
   https://dashboard.render.com/account/settings
   ```

2. **Scroll down to "API Keys" section**

3. **Click "Create API Key"**
   - Give it a name: `Agent Factory Deployment`
   - Click "Create"

4. **COPY THE KEY IMMEDIATELY**
   - It looks like: `rnd_xxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **This is shown only once!** Save it somewhere safe
   - You'll use this in the next step

---

## Step 2: Get Your Service ID (10 seconds)

1. **Go to your Render dashboard:**
   ```
   https://dashboard.render.com
   ```

2. **Click on your Telegram bot service**

3. **Look at the URL in your browser:**
   ```
   https://dashboard.render.com/web/srv-XXXXXXXXXXXXX
   ```

4. **Copy the part that starts with `srv-`**
   - Example: `srv-abc123xyz456`
   - This is your Service ID

---

## Step 3: Run the Configuration Script (5 seconds)

**Open a terminal in your Agent Factory directory and run:**

```bash
python scripts/deployment/configure_render_service.py \
  --api-key rnd_YOUR_API_KEY_HERE \
  --service-id srv-YOUR_SERVICE_ID_HERE
```

**Example:**
```bash
python scripts/deployment/configure_render_service.py \
  --api-key rnd_abc123xyz456 \
  --service-id srv-def789uvw012
```

---

## What the Script Does

**Automatically:**
1. ✅ Reads ALL environment variables from your `.env` file
2. ✅ Connects to Render API
3. ✅ Adds these variables to your service:
   - `TELEGRAM_ADMIN_CHAT_ID`
   - `AUTHORIZED_TELEGRAM_USERS`
   - `NEON_DB_URL`
   - `DATABASE_PROVIDER=neon`
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `VOICE_MODE=edge`
   - `EDGE_VOICE=en-US-GuyNeural`
   - `DEFAULT_LLM_PROVIDER=openai`
   - `DEFAULT_MODEL=gpt-4o`
   - `PYTHONUNBUFFERED=1`
   - `LOG_LEVEL=INFO`
   - Plus optional: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, etc.

4. ✅ Triggers a new deployment
5. ✅ Shows you the deployment URL

**Total time: 5 seconds** (vs 30+ minutes manual)

---

## Expected Output

```
======================================================================
RENDER.COM SERVICE CONFIGURATION
======================================================================

[1/5] Fetching service information...
  Service: agent-factory-telegram-bot
  Type: web
  ID: srv-abc123xyz456

[2/5] Fetching current environment variables...
  Currently configured: 1 variables
  Existing keys: TELEGRAM_BOT_TOKEN

[3/5] Loading environment variables from .env...
  Loaded: 13 variables
  Keys: TELEGRAM_ADMIN_CHAT_ID, AUTHORIZED_TELEGRAM_USERS, NEON_DB_URL...

  New variables to add: 12
    TELEGRAM_ADMIN_CHAT_ID, AUTHORIZED_TELEGRAM_USERS, NEON_DB_URL, ...

[4/5] Updating environment variables...
✅ Successfully updated 13 environment variables

[5/5] Triggering deployment...
✅ Deployment triggered: dpl-xyz789

======================================================================
✅ CONFIGURATION COMPLETE
======================================================================

Next steps:
  1. Monitor deployment: https://dashboard.render.com/web/srv-abc123xyz456
  2. Check logs for any errors
  3. Test health endpoint once deployed
```

---

## Optional: Dry Run First (Test Without Changes)

**Want to see what would be configured before making changes?**

```bash
python scripts/deployment/configure_render_service.py \
  --api-key rnd_YOUR_KEY \
  --service-id srv-YOUR_ID \
  --dry-run
```

**This shows you:**
- What variables will be added
- Their values (first 20 characters)
- **No changes made** (safe to test)

---

## Troubleshooting

### Error: "Invalid API key or unauthorized"

**Problem:** API key is incorrect or doesn't have permissions

**Fix:**
1. Go back to: https://dashboard.render.com/account/settings
2. Create a new API key
3. Copy the FULL key (starts with `rnd_`)
4. Try again

---

### Error: "Service srv-xxxxx not found"

**Problem:** Service ID is incorrect or you don't have access

**Fix:**
1. Go to your Render dashboard
2. Click on your service
3. Check the URL carefully: `https://dashboard.render.com/web/srv-XXXXX`
4. Copy the FULL service ID including `srv-`

---

### Error: "No environment variables loaded from .env"

**Problem:** `.env` file not found or empty

**Fix:**
1. Check that `.env` file exists in your project root
2. Verify it has the required variables (see `.env.example`)
3. Run from the correct directory (Agent Factory root)

---

### Warning: "Required variable XXX not found"

**Problem:** Some required variables are missing from `.env`

**What to do:**
- The script will still run with available variables
- Add missing variables to `.env` and run again
- Or manually add them in Render dashboard

---

## After Configuration

### 1. Monitor Deployment (5-10 min)

Go to your service dashboard:
```
https://dashboard.render.com/web/srv-YOUR_SERVICE_ID
```

**Look for:**
- Status: "Live" (green)
- Logs show: "Bot lock acquired" + "Bot is running"

### 2. Test Health Endpoint

Once deployed, test:
```bash
curl https://YOUR-SERVICE-NAME.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "pid": 7,
  "uptime_seconds": 42
}
```

### 3. Configure Webhook

Once health check passes, set the webhook:
```bash
python scripts/deployment/set_telegram_webhook.py \
  --service-url https://YOUR-SERVICE-NAME.onrender.com
```

### 4. Test Bot

Send `/start` to your Telegram bot → Should respond within 2 seconds!

---

## Next: Deploy Cron Job

After your web service is running, deploy the cron job:

**Same process:**
1. Create another service in Render (Cron Job type)
2. Get its service ID: `srv-YYYYYY`
3. Run the configuration script again with the new service ID:
   ```bash
   python scripts/deployment/configure_render_service.py \
     --api-key rnd_YOUR_KEY \
     --service-id srv-CRON_JOB_SERVICE_ID
   ```

---

## Security Notes

**API Key Security:**
- ⚠️ **NEVER** commit your API key to git
- ⚠️ **NEVER** share it publicly
- ⚠️ If compromised, revoke it immediately in Render dashboard
- ✅ Store it securely (password manager recommended)

**The API key provides FULL access to:**
- All your Render services
- All environment variables
- Deployment triggers
- Billing information

**If you suspect compromise:**
1. Go to: https://dashboard.render.com/account/settings
2. Find the API key
3. Click "Revoke"
4. Create a new one

---

## Summary

**What you need:**
- ✅ Render API key (from Account Settings)
- ✅ Service ID (from service dashboard URL)
- ✅ `.env` file with all variables

**What you run:**
```bash
python scripts/deployment/configure_render_service.py \
  --api-key rnd_xxx \
  --service-id srv-xxx
```

**Time saved:** ~25 minutes (vs manual entry)
**Accuracy:** 100% (no copy/paste errors)

---

**Questions?** Check the main deployment guide: `DEPLOYMENT_QUICK_START.md`
