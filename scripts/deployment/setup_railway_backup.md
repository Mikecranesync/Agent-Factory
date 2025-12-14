# Railway.app Backup Deployment Guide

**Purpose:** Deploy Agent Factory to Railway.app as a backup/failover service

**Status:** STANDBY (inactive unless Render fails)

**Cost:** ~$5/month (500 hours execution time)

---

## Why Railway.app Backup?

**Redundancy:**
- If Render.com goes down, switch to Railway instantly
- Different infrastructure provider (reduces single-point-of-failure)
- Keep backup service in STANDBY mode (no cost until activated)

**Failover Strategy:**
1. Render.com = Primary (free tier, 24/7 with UptimeRobot)
2. Railway.app = Secondary ($5/mo, activated on Render failure)
3. Local machine = Tertiary (manual fallback)

---

## Railway.app Setup (15 minutes)

### Step 1: Create Account

1. Go to: https://railway.app
2. Sign in with GitHub
3. Verify email

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **"Agent-Factory"** repository
4. Click **"Deploy"**

### Step 3: Configure Service

Railway will auto-detect Dockerfile and deploy automatically.

**Configuration:**
- Name: `agent-factory-backup-bot`
- Branch: `main`
- Root Directory: `/` (default)
- Build Command: Auto-detected (Docker)
- Start Command: Auto-detected from Dockerfile

### Step 4: Add Environment Variables

**Click "Variables" tab → Add all variables from your `.env` file:**

```bash
# Copy these from your .env or Render.com
TELEGRAM_BOT_TOKEN=<YOUR_VALUE>
TELEGRAM_ADMIN_CHAT_ID=<YOUR_VALUE>
AUTHORIZED_TELEGRAM_USERS=<YOUR_VALUE>

# Database
NEON_DB_URL=<YOUR_VALUE>
SUPABASE_URL=<YOUR_VALUE>
SUPABASE_KEY=<YOUR_VALUE>
DATABASE_PROVIDER=neon

# LLM
OPENAI_API_KEY=<YOUR_VALUE>
ANTHROPIC_API_KEY=<YOUR_VALUE>
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o

# Voice
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural

# System
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

**Fastest method:**
1. Export from Render.com as JSON
2. Import to Railway.app

### Step 5: Get Service URL

After deployment completes:

- Service URL: `https://agent-factory-backup-bot.up.railway.app`
- Health Check: `https://agent-factory-backup-bot.up.railway.app/health`

**Copy this URL** for failover procedures.

### Step 6: Set to STANDBY Mode

**IMPORTANT:** Railway charges for execution time. Keep service paused until needed.

**To pause service:**
1. Click service name
2. Click "Settings"
3. Scroll to "Service" section
4. Click **"Sleep Service"** or reduce instance count to 0

**Service will NOT run until you manually activate it.**

---

## Failover Activation Procedure

### When to Activate Backup

Activate Railway backup if:
1. Render.com service is down for >15 minutes
2. UptimeRobot shows <95% uptime over 1 hour
3. Multiple failed health checks
4. Render platform-wide outage

### Activation Steps (5 minutes)

#### 1. Wake Railway Service

```bash
# Railway Dashboard → agent-factory-backup-bot → Wake Service
```

Or via CLI:
```bash
railway up
```

#### 2. Wait for Health Check

Test health endpoint:
```bash
curl https://agent-factory-backup-bot.up.railway.app/health
```

Expected: `{"status": "healthy", ...}`

#### 3. Switch Telegram Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://agent-factory-backup-bot.up.railway.app/telegram-webhook", "max_connections": 40}'
```

#### 4. Verify Bot Responding

Send `/start` to bot → Should respond within 2 seconds

#### 5. Update Monitoring

Point UptimeRobot to Railway URL:
- Old: `https://agent-factory-telegram-bot.onrender.com/health`
- New: `https://agent-factory-backup-bot.up.railway.app/health`

---

## Return to Render (When Restored)

### When to Switch Back

Switch back to Render when:
1. Render service is stable for >1 hour
2. UptimeRobot shows 100% uptime
3. Health checks passing consistently

### Steps

#### 1. Verify Render Health

```bash
curl https://agent-factory-telegram-bot.onrender.com/health
```

Expected: 10 consecutive successful checks (5 minutes)

#### 2. Switch Webhook Back to Render

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://agent-factory-telegram-bot.onrender.com/telegram-webhook", "max_connections": 40}'
```

#### 3. Test Bot

Send `/start` → Verify response from Render service

#### 4. Sleep Railway Service

```bash
# Railway Dashboard → agent-factory-backup-bot → Sleep Service
```

#### 5. Restore Monitoring

Update UptimeRobot back to Render URL

---

## Cost Management

### Railway.app Pricing

**Free Trial:**
- $5 credit per month
- Good for ~500 hours execution time
- ~20 days of 24/7 operation

**Paid Plan:**
- $0.000463/GB-hour (memory)
- $0.000231/vCPU-hour (compute)
- Estimated: $5-10/month for 24/7 standby

**STANDBY Mode:**
- Cost: $0/month (service paused)
- Activation time: <60 seconds
- Use this for backup/failover only

### Cost Optimization

**Best Practice:**
1. Keep Railway service **paused** unless needed
2. Only activate during Render outages
3. Switch back to Render ASAP (free tier)
4. Monitor Railway usage via dashboard

**Alert when Railway active for >24 hours** (indicates Render still down)

---

## Testing Backup Service

### Test Procedure (Do NOT use in production)

1. **Activate Railway service**
2. **Set webhook to Railway temporarily**
3. **Send test commands** (/start, /help, /status)
4. **Verify responses**
5. **Switch webhook back to Render**
6. **Pause Railway service**

**Estimated test cost:** <$0.01

---

## Database Failover

Railway service uses the **same databases** as Render:

**Primary:** Neon PostgreSQL (`NEON_DB_URL`)
**Backup:** Supabase (`SUPABASE_URL`)

**No additional database setup required.**

---

## Monitoring Both Services

### Dual Monitoring Strategy

**Option 1: UptimeRobot (Free)**
- Monitor 1: Render service (primary)
- Monitor 2: Railway service (paused check)
- Alert if Render down for >15 min → Manual activation

**Option 2: Automated Failover (Advanced)**
- Use Cloudflare Load Balancer
- Automatic failover between Render/Railway
- Cost: $5/month (Cloudflare Pro)

**Recommendation:** Start with Option 1 (manual failover)

---

## Emergency Contacts

**Railway Support:**
- Dashboard: https://railway.app/dashboard
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**Failover Decision Tree:**
```
Render Down?
│
├─ Yes → Check UptimeRobot (>15 min down?)
│   │
│   ├─ Yes → Activate Railway backup
│   └─ No → Wait, monitor
│
└─ No → Normal operation (Render primary)
```

---

## Deployment Summary

**Primary:** Render.com (Free tier, 24/7 with UptimeRobot)
**Backup:** Railway.app (Paused until needed)
**Tertiary:** Local machine (Manual emergency fallback)

**Monthly Cost:**
- Render: $1 (cron job)
- Railway: $0 (paused)
- UptimeRobot: $0 (free tier)
- **Total: $1/month**

**Uptime Target:** 99.9% (includes failover)

---

**Last Updated:** 2025-12-13
**Status:** READY FOR DEPLOYMENT
