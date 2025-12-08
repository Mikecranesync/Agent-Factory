---
name: 🤖 Rivet Discovery Control Panel
about: Mobile control interface for manual discovery agent
title: '🤖 Rivet Manual Discovery Control Panel'
labels: ['automation', 'control-panel', 'rivet']
assignees: ''
---

# 🤖 Rivet Manual Discovery Control Panel

Control the discovery agent from your phone via GitHub app.

## 🎮 Available Commands

### Start Discovery
```
/discover [manufacturers]
```
**Examples:**
- `/discover ABB Siemens` - Scrape 2 specific manufacturers
- `/discover Rockwell` - Scrape single manufacturer
- `/discover all` - Scrape all configured manufacturers (takes longer)

### Check Status
```
/status
```
Shows current discovery status and last run results.

### View Statistics
```
/stats
```
Shows total manuals discovered, database size, success rates.

### Emergency Stop
To stop a running discovery, go to Actions tab → Cancel workflow

---

## 📊 Dashboard

**Last Run:** _Auto-updated after each cycle_
**Status:** _Awaiting first run_
**Duration:** _N/A_
**Manuals Found:** _0_

**Total Database:** 0 manuals from 5 manufacturers

**Next Scheduled Run:** _Check Actions tab for schedule_

---

## 📈 Recent Activity
_(Auto-updated by bot after each run)_

| Time | Trigger | Manufacturers | Found | Status |
|------|---------|---------------|-------|--------|
| _Awaiting first run_ | - | - | - | - |

---

## 🔧 Configuration

**Manufacturers Configured:**
- ABB (motor drives, VFDs, switchgear)
- Siemens (PLCs, automation, building systems)
- Rockwell Automation (ControlLogix, CompactLogix PLCs)
- Carrier (commercial HVAC, chillers)
- Schneider Electric (contactors, breakers, automation)

**Schedule:** Every 8 hours (2 AM, 10 AM, 6 PM UTC)

**Rotation Pattern:**
- 2 AM: ABB + Siemens
- 10 AM: Rockwell + Carrier
- 6 PM: Schneider + ABB

**Quality Threshold:** 0.5 (Medium confidence minimum)

**Manual Types Targeted:**
- Installation Guides
- Service Manuals
- Troubleshooting Guides
- Wiring Diagrams
- Parts Lists
- Maintenance Procedures

---

## 📱 Mobile Usage Tips

**From GitHub Mobile App:**
1. Open this issue
2. Scroll to comments
3. Type command (e.g., `/discover ABB`)
4. Submit comment
5. Get instant acknowledgment
6. Check Actions tab for live progress
7. Return here for mobile-friendly summary

**Notifications:**
- Enable GitHub notifications in app settings
- Get alerts when discovery completes
- Optional: Configure Telegram bot for push notifications

---

## 🆘 Troubleshooting

**If discovery fails:**
1. Check [Actions tab](../../actions) for error logs
2. Common issues:
   - Timeout (manufacturer site slow) → Will retry next cycle
   - Rate limit (too many requests) → Automatically backs off
   - Site structure changed → May need scraper update

**If commands not working:**
1. Ensure comment starts with `/` (slash)
2. Check spelling (case-sensitive)
3. Verify you have write access to repository

**If workflow not running:**
1. Check if another run is in progress (only 1 at a time)
2. Verify GitHub Actions enabled in repository settings
3. Check secrets are configured (Settings → Secrets)

---

## 🔑 Required Secrets

Ensure these are configured in repository settings:

- `SUPABASE_DATABASE_URL` - PostgreSQL database connection
- `OPENAI_API_KEY` - For LLM-powered quality validation (optional)
- `GOOGLE_CSE_API_KEY` - Google Custom Search API key
- `GOOGLE_CSE_ENGINE_ID` - Custom Search Engine ID
- `TELEGRAM_BOT_TOKEN` - (Optional) For mobile push notifications
- `TELEGRAM_CHAT_ID` - (Optional) Your Telegram chat ID

---

## 📞 Support

**Issues with the agent itself:** Open a new issue with `bug` label

**Feature requests:** Open a new issue with `enhancement` label

**Questions:** Ask in issue comments below

---

_💡 **Pro Tip:** Pin this issue to keep it at the top of your issues list for quick mobile access!_

_🤖 This control panel is powered by GitHub Actions and runs on free tier (2000 min/month)._
