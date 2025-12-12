# 24/7 Production & Scraping Schedule - Complete Guide

## Overview

This guide covers the **fully automated 24/7 knowledge base building and video production system** for Agent Factory.

**What it does:**
- Scrapes OEM PDFs automatically (daily)
- Builds knowledge atoms with embeddings
- Uploads to Supabase for vector search
- Monitors system health (every 15 min)
- Performs weekly maintenance
- Sends Telegram notifications

**Status:** ✅ READY TO DEPLOY

---

## Quick Start (10 Minutes)

### Step 1: Fix Supabase Schema (YOU - 5 min)

**Current Issue:** Upload failing because `knowledge_atoms` table missing `content` column

**Fix:**
1. Open Supabase SQL Editor
2. Paste contents of `docs/supabase_complete_schema.sql`
3. Click "RUN"
4. Wait ~30 seconds for migration to complete

**Verify:**
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'knowledge_atoms' AND column_name = 'content';
-- Should return 1 row
```

### Step 2: Upload Existing 2045 Atoms (AUTOMATED - 5 min)

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
poetry run python scripts/FULL_AUTO_KB_BUILD.py
```

**Expected output:**
```
Uploaded: 2045
Failed: 0
Total Atoms: 2045
```

### Step 3: Set Up Automation (AUTOMATED - 10 seconds)

```powershell
# Run as Administrator
PowerShell -ExecutionPolicy Bypass -File scripts\setup_windows_scheduler.ps1
```

**Creates 3 scheduled tasks:**
- **Daily KB Building** - 2:00 AM every day
- **Weekly Maintenance** - Sunday 12:00 AM
- **Health Monitor** - Every 15 minutes

### Step 4: Verify Setup

```powershell
# Check tasks are registered
schtasks /query /tn "AgentFactory_KB_Daily"
schtasks /query /tn "AgentFactory_KB_Weekly"
schtasks /query /tn "AgentFactory_HealthMonitor"

# Run health check manually
poetry run python scripts/health_monitor.py
```

**Done!** Your 24/7 automation is running.

---

## Architecture

### Daily KB Building (2:00 AM)

```
┌─────────────────────────────────────────┐
│ scheduler_kb_daily.py                   │
├─────────────────────────────────────────┤
│ Phase 1: Scrape PDFs                    │
│   • Download new PDFs from OEM sources  │
│   • Extract text, tables, images        │
│   • Cache to avoid re-downloads         │
├─────────────────────────────────────────┤
│ Phase 2: Build Atoms                    │
│   • Convert PDF extractions → atoms     │
│   • Generate embeddings (OpenAI API)    │
│   • Detect type, difficulty, safety     │
├─────────────────────────────────────────┤
│ Phase 3: Upload to Supabase             │
│   • Batch upload (100 atoms/batch)      │
│   • Skip duplicates (by atom_id)        │
│   • Validate upload success             │
├─────────────────────────────────────────┤
│ Phase 4: Validate & Quality Check       │
│   • Count total atoms                   │
│   • Count valid embeddings              │
│   • Flag low-quality atoms              │
├─────────────────────────────────────────┤
│ Phase 5: Generate Report                │
│   • Create daily stats report           │
│   • Save to data/reports/               │
│   • Send Telegram notification          │
└─────────────────────────────────────────┘
```

**Runtime:** ~15-30 minutes (depends on PDFs)
**Logs:** `data/logs/kb_daily_YYYYMMDD.log`
**Reports:** `data/reports/kb_daily_YYYYMMDD.md`

### Weekly Maintenance (Sunday 12:00 AM)

```
┌─────────────────────────────────────────┐
│ scheduler_kb_weekly.py                  │
├─────────────────────────────────────────┤
│ Phase 1: Reindex                        │
│   • Rebuild full-text search indexes    │
│   • Count total atoms                   │
│   • Check embedding coverage            │
├─────────────────────────────────────────┤
│ Phase 2: Deduplicate                    │
│   • Find similar atoms (cosine > 0.95)  │
│   • Flag for manual review              │
│   • Generate duplicate report           │
├─────────────────────────────────────────┤
│ Phase 3: Quality Audit                  │
│   • Count by type (concept, procedure)  │
│   • Count by difficulty (beginner-expert)│
│   • Count by manufacturer               │
│   • Flag low-quality atoms              │
├─────────────────────────────────────────┤
│ Phase 4: Growth Report                  │
│   • Atoms added this week               │
│   • Week-over-week growth rate          │
│   • Project to next milestone           │
└─────────────────────────────────────────┘
```

**Runtime:** ~5-10 minutes
**Logs:** `data/logs/kb_weekly_weekNN.log`
**Reports:** `data/reports/weekly_weekNN.json`

### Health Monitor (Every 15 Minutes)

```
┌─────────────────────────────────────────┐
│ health_monitor.py                       │
├─────────────────────────────────────────┤
│ ✅ Supabase Connection                  │
│ ✅ Last Atom Upload Time                │
│ ✅ Recent Log Errors                    │
│ ✅ Scheduled Tasks Registered           │
│ ✅ Disk Space Available                 │
├─────────────────────────────────────────┤
│ Overall Status:                         │
│   • Healthy (all green)                 │
│   • Warning (yellow flags)              │
│   • Critical (red flags → Telegram!)    │
└─────────────────────────────────────────┘
```

**Runtime:** <10 seconds
**Logs:** `data/logs/health_monitor.log`
**Status:** `data/health/latest.json`

---

## Telegram Notifications

### Setup (Optional but Recommended)

1. Create Telegram bot (talk to [@BotFather](https://t.me/BotFather))
2. Get bot token: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
3. Get your chat ID: Talk to [@userinfobot](https://t.me/userinfobot)
4. Add to `.env`:

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_CHAT_ID=123456789
```

### Notification Types

**Daily Success:**
```
✅ Daily KB Building Complete

PHASE 1: PDF Scraping
- PDFs Scraped: 3
- Pages Extracted: 1200
- Tables Extracted: 150

PHASE 2: Atom Building
- Total Atoms Generated: 125
- Embeddings Generated: 125

PHASE 3: Supabase Upload
- Uploaded: 125
- Failed: 0

Total Atoms in DB: 4170
```

**Critical Alerts:**
```
🚨 HEALTH ALERT

Critical Issues Detected:
• last_upload: No atom uploads in 25.3 hours (threshold: 24h)
• supabase: Supabase unreachable: Connection timeout
```

---

## Expected Output

### Week 1

- **Atoms:** 2,045 (current) + ~500 = **2,545 atoms**
- **Manufacturers:** Allen-Bradley, Siemens
- **Cost:** $0.01 (embeddings)

### Week 4

- **Atoms:** 2,045 (current) + ~1,500 = **3,545 atoms**
- **Manufacturers:** Allen-Bradley, Siemens, Mitsubishi, Omron
- **Cost:** ~$0.03/week

### Month 3 (Week 12)

- **Atoms:** 2,045 (current) + ~4,500 = **6,545 atoms**
- **Manufacturers:** All 6 (Allen-Bradley, Siemens, Mitsubishi, Omron, Schneider, ABB)
- **Cost:** ~$0.10/month

---

## Monitoring & Debugging

### View Real-Time Status

```bash
# Check health status
poetry run python scripts/health_monitor.py

# View latest health check
cat data/health/latest.json
```

### View Logs

```bash
# Today's daily KB building log
type data\logs\kb_daily_20251211.log

# This week's weekly maintenance log
type data\logs\kb_weekly_week50.log

# Health monitor log (continuous)
type data\logs\health_monitor.log
```

### View Reports

```bash
# Today's KB stats
cat data/reports/kb_daily_20251211.md

# This week's growth report
cat data/reports/weekly_week50.json
```

### Manual Test Runs

```bash
# Test daily KB building
poetry run python scripts/scheduler_kb_daily.py

# Test weekly maintenance
poetry run python scripts/scheduler_kb_weekly.py

# Test health monitor
poetry run python scripts/health_monitor.py
```

### Telegram Test

```bash
# Send test notification
poetry run python -c "
import os
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {'chat_id': chat_id, 'text': '✅ Test notification'}
requests.post(url, json=data)
"
```

---

## Troubleshooting

### Issue: Daily task not running

**Check:**
```powershell
schtasks /query /tn "AgentFactory_KB_Daily" /v
```

**If "Last Result" is not 0:**
- Check logs: `data/logs/kb_daily_*.log`
- Run manually: `schtasks /run /tn "AgentFactory_KB_Daily"`
- Check Python path in task definition

**If task doesn't exist:**
- Re-run setup: `PowerShell -ExecutionPolicy Bypass -File scripts\setup_windows_scheduler.ps1`

### Issue: "Supabase unreachable"

**Check:**
1. Is Supabase project active?
2. Are credentials correct in `.env`?
3. Is internet connection working?

**Test connection:**
```bash
poetry run python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

client = create_client(url, key)
result = client.table('knowledge_atoms').select('id', count='exact').execute()
print(f'Total atoms: {result.count}')
"
```

### Issue: "No atom uploads in 24 hours"

**Possible causes:**
1. Daily task failed (check logs)
2. No new PDFs to scrape (expected behavior)
3. Supabase upload failing (check schema)

**Fix:**
- Check daily task logs
- Run manual test: `poetry run python scripts/scheduler_kb_daily.py`

### Issue: High disk usage

**Check usage:**
```bash
# See data directory size
du -sh data/
```

**Clean up:**
```bash
# Delete old logs (keep last 7 days)
find data/logs -name "*.log" -mtime +7 -delete

# Delete old reports (keep last 30 days)
find data/reports -name "*.md" -mtime +30 -delete
```

---

## Advanced Configuration

### Add More PDF Sources

**Edit:** `scripts/scheduler_kb_daily.py`

```python
PDF_SOURCES = {
    "allen_bradley": [
        "https://...",  # Add more URLs
    ],
    "siemens": [
        "https://...",
    ],
    # Add new manufacturers
    "mitsubishi": [
        "https://www.mitsubishielectric.com/fa/products/...",
    ],
}
```

### Change Schedule Times

```powershell
# Daily task at 3:00 AM instead of 2:00 AM
schtasks /change /tn "AgentFactory_KB_Daily" /st 03:00

# Weekly task on Friday instead of Sunday
schtasks /delete /tn "AgentFactory_KB_Weekly" /f
schtasks /create /tn "AgentFactory_KB_Weekly" /tr "..." /sc weekly /d FRI /st 00:00
```

### Adjust Health Check Thresholds

**Edit:** `scripts/health_monitor.py`

```python
MAX_HOURS_NO_ACTIVITY = 48  # Alert if no uploads in 48h (instead of 24h)
MAX_ERRORS_IN_LOG = 20      # Alert if >20 errors (instead of 10)
```

---

## Cost Breakdown

**Daily (per run):**
- OpenAI embeddings: ~$0.001 (for ~25 new atoms)
- Supabase: $0 (free tier)
- **Total: <$0.01/day**

**Monthly (30 days):**
- OpenAI embeddings: ~$0.30
- Supabase: $0 (free tier sufficient)
- **Total: ~$0.30/month**

**Annual:**
- OpenAI: ~$3.60
- Supabase: $0
- **Total: ~$3.60/year**

**Note:** This is for KB building only. Video production adds ~$35/month (ElevenLabs voice + OpenAI scripts).

---

## Success Metrics

**Week 1:**
- ✅ 3 scheduled tasks running
- ✅ Health checks passing every 15 min
- ✅ Daily KB updates (even if 0 new atoms)
- ✅ Telegram notifications working

**Week 4:**
- ✅ 4,000+ atoms in database
- ✅ 100% uptime (no missed daily tasks)
- ✅ <5 critical alerts in month
- ✅ Zero manual intervention required

**Month 3:**
- ✅ 6,000+ atoms in database
- ✅ All 6 manufacturers covered
- ✅ <1% duplicate rate
- ✅ System runs autonomously

---

## Next Steps After Setup

1. **Monitor for 1 week** - Make sure daily tasks run successfully
2. **Fix Supabase schema** (if upload still failing)
3. **Add more PDF sources** (Mitsubishi, Omron, Schneider, ABB)
4. **Set up Telegram** (for notifications)
5. **Plan video production** (Phase 2 - Week 5+)

---

## Summary

**What You Have Now:**
- ✅ Fully automated 24/7 KB building
- ✅ 2045 atoms ready to upload
- ✅ Scheduled tasks for daily/weekly/health checks
- ✅ Logging and reporting infrastructure
- ✅ Telegram notifications (optional)

**What Happens Next:**
- **2:00 AM every day:** System scrapes PDFs, builds atoms, uploads to Supabase
- **Every 15 min:** Health monitor checks system status
- **Sunday 12:00 AM:** Weekly maintenance (deduplication, quality audit)
- **You:** Review Telegram notifications, check reports weekly

**Result:** Knowledge base grows automatically from ~2K to ~6K atoms in 3 months with **zero manual intervention**.

🚀 **Your 24/7 automation is ready to go!**
