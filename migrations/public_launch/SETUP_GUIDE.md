# 🚀 RIVET CMMS - Public Bot Setup Guide

## Step 1: Create New Bot with BotFather (2 minutes)

Open Telegram and message [@BotFather](https://t.me/botfather):

```
/newbot
```

When prompted:

1. **Bot Name** (display name): `Rivet CMMS`
2. **Username** (must end in 'bot'): `RivetCMMS_bot`

If `RivetCMMS_bot` is taken, try:
- `RivetCMMS_AI_bot`
- `RivetFieldService_bot`  
- `Rivet_CMMS_bot`

**BotFather will give you a token like:**
```
8123456789:AAH8xyz123abc456def789ghi012jkl345
```

Copy this token!

---

## Step 2: Configure the Bot (BotFather commands)

Send these commands to BotFather:

### Set Description (shows before user starts bot)
```
/setdescription
```
Select your bot, then send:
```
🔧 AI-Powered Field Service Assistant

• Voice-first troubleshooting for technicians
• OCR equipment nameplates instantly  
• Search electrical prints & OEM manuals
• Get answers in seconds, not hours

Free tier: 10 questions/month
Pro: Unlimited + priority support

Start now with /start
```

### Set About Text (profile page)
```
/setabouttext
```
Select your bot, then send:
```
Rivet CMMS helps field technicians troubleshoot equipment faster with AI. Upload electrical prints, search OEM manuals, and get instant answers via voice or text.

Built for maintenance pros. 🔧
```

### Set Commands (menu button)
```
/setcommands
```
Select your bot, then send:
```
start - Get started with Rivet
help - Command reference
troubleshoot - Start AI troubleshooting
add_machine - Add equipment to track
list_machines - View your equipment
upload_print - Upload electrical print PDF
chat_print - Q&A with your prints
manual_search - Search OEM manuals
upgrade - View Pro plans
```

### Set Profile Photo (optional but recommended)
```
/setuserpic
```
Upload a logo image (512x512 recommended)

---

## Step 3: Update Environment Variables

Add to your `.env.production`:

```bash
# ═══════════════════════════════════════════════════════════════════
# PUBLIC BOT TOKEN (from BotFather)
# ═══════════════════════════════════════════════════════════════════
PUBLIC_TELEGRAM_BOT_TOKEN=8123456789:AAH8xyz123abc456def789ghi012jkl345

# Keep your personal bot token for dev/testing
TELEGRAM_BOT_TOKEN=8208278660:AAGz6v7dIPMnfepp-UFMCwdUpOAeqYeOT84
```

---

## Step 4: Run Database Migration

```bash
# Connect to Neon and run the migration
psql $NEON_DB_URL -f migrations/public_launch/001_public_ready_schema.sql
```

This creates:
- `rate_limits` table for abuse prevention
- `usage_events` table for analytics/billing
- `tier_limits` table for configurable restrictions
- `admin_users` table (adds you as super_admin)

---

## Step 5: Deploy Public Bot

### Option A: Local Testing
```bash
python rivet_public_bot.py
```

### Option B: VPS Deployment
```bash
# Copy to VPS
scp rivet_public_bot.py root@72.60.175.144:/opt/rivet/

# SSH and run
ssh root@72.60.175.144
cd /opt/rivet
python rivet_public_bot.py
```

### Option C: Systemd Service (recommended)
Create `/etc/systemd/system/rivet-public.service`:
```ini
[Unit]
Description=Rivet CMMS Public Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rivet
Environment=PATH=/opt/rivet/venv/bin
EnvironmentFile=/opt/rivet/.env.production
ExecStart=/opt/rivet/venv/bin/python rivet_public_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rivet-public
sudo systemctl start rivet-public
sudo systemctl status rivet-public
```

---

## Step 6: Verify Everything Works

1. **Find your bot**: Search `@RivetCMMS_bot` in Telegram
2. **Start it**: Send `/start`
3. **Check onboarding**: Should see welcome + tier selection
4. **Test troubleshooting**: "My VFD shows fault F001"
5. **Check admin**: `/admin` should work for you only

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    @RivetCMMS_bot                           │
│                  (Single Public Bot)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User A (free)     User B (pro)     User C (enterprise)    │
│       │                 │                  │                │
│       └────────────────┴──────────────────┘                │
│                         │                                   │
│              ┌──────────▼──────────┐                       │
│              │   rivet_users       │                       │
│              │   (tenant table)    │                       │
│              └──────────┬──────────┘                       │
│                         │                                   │
│    ┌───────────────────┼───────────────────┐               │
│    │                   │                   │               │
│    ▼                   ▼                   ▼               │
│ machines           prints           chat_history           │
│ (user_id)         (user_id)          (user_id)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

All users share ONE bot. Data isolation happens at the database level via `user_id` foreign keys.

---

## Admin Access

You're auto-added as `super_admin` in the migration. To add more admins:

```sql
INSERT INTO admin_users (telegram_id, username, role)
VALUES (123456789, 'newadmin', 'admin');
```

Roles:
- `super_admin` - Full access (deployments, system control)
- `admin` - Dashboard, metrics, content review
- `support` - User management, content review only

---

## What's Next?

1. **Set up Stripe** for payment processing
2. **Configure webhook** for subscription events
3. **Add landing page** with `/start?start=API_KEY` deep links
4. **Monitor with LangSmith** for usage analytics

Good luck! 🚀
