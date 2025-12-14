# Environment Files Guide

## Overview: Why Multiple .env Files?

Agent Factory has **3 separate .env files** for different purposes. **Do NOT merge them** - they serve distinct use cases.

---

## 1. `.env` (Main Project - Agent Factory)

**Location:** `C:\Users\hharp\OneDrive\Desktop\Agent Factory\.env`

**Purpose:** Main Agent Factory deployment (Telegram PLC knowledge bot)

**Used By:**
- `telegram_bot.py` - Main production bot
- Render.com deployment
- All core agents (Research, Scriptwriter, SEO, Thumbnail, etc.)
- Knowledge base automation

**Key Configuration:**
```bash
TELEGRAM_BOT_TOKEN=8264955123:AAHLiOZmJXrOepJ82XGs_pcGwk6BIfEgGAs
TELEGRAM_ADMIN_CHAT_ID=8445149012
AUTHORIZED_TELEGRAM_USERS=8445149012

# Database
DATABASE_PROVIDER=neon
NEON_DB_URL=postgresql://neondb_owner:npg...@ep-bitter-shadow-ah70vrun...
SUPABASE_URL=https://mggqgrxwumnnujojndub.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_x67ttLFGhQY...

# LLM APIs
OPENAI_API_KEY=sk-proj-SHyU5DPZ...
ANTHROPIC_API_KEY=sk-ant-api03-Q-XfQG0Y4VxQ...
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o

# Deployment
RENDER_API_KEY=rnd_E28gCMELQo0upAgxmjliHyve4C8X
RAILWAY_API_KEY=2db9f13b-9fe2-4063-b2d6-4609a0ac2ffb

# Voice
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural
```

**Size:** 108 lines
**Status:** ✅ Clean, ready for deployment

---

## 2. `.env.phone_control` (Phone Control Bot)

**Location:** `C:\Users\hharp\OneDrive\Desktop\Agent Factory\.env.phone_control`

**Purpose:** **SEPARATE** Telegram bot for phone automation/control

**Used By:**
- `phone_control_bot.py` - Phone automation bot (different from main bot)

**Why Separate?**
- Different bot token (different bot from @BotFather)
- Different purpose (phone control vs PLC knowledge)
- Prevents conflicts with main Agent Factory bot

**Key Configuration:**
```bash
# DIFFERENT BOT TOKEN
TELEGRAM_BOT_TOKEN=8208278660:AAGz6v7dIPMnfepp-UFMCwdUpOAeqYeOT84
AUTHORIZED_TELEGRAM_USERS=8445149012

# Shares some credentials with main .env
ANTHROPIC_API_KEY=sk-ant-api03-Q-XfQG0Y4VxQ... (same)
NEON_DB_URL=postgresql://neondb_owner:npg... (same)
```

**Size:** 62 lines
**Status:** ✅ Keep separate (different bot)

**⚠️ DO NOT MERGE INTO MAIN .env** - This would cause the wrong bot to respond to commands!

---

## 3. `rivet/.env` (Rivet Industrial KB Factory)

**Location:** `C:\Users\hharp\OneDrive\Desktop\Agent Factory\rivet\.env`

**Purpose:** Rivet subsystem - Docker-based Industrial Knowledge Base Factory

**Used By:**
- `rivet/docker-compose.yml` - Containerized KB processing
- Rivet Postgres database (isolated)
- Rivet Redis cache
- Rivet Ollama LLM server

**Why Separate?**
- **Docker isolated network** - runs in containers
- Different database (local Postgres, not Neon/Supabase)
- Different LLM setup (local Ollama, not OpenAI/Anthropic)
- Designed for self-contained operation

**Key Configuration:**
```bash
# Docker Postgres (NOT Neon/Supabase)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=rivet
POSTGRES_USER=rivet
POSTGRES_PASSWORD=change_me_in_production

# Docker Redis
REDIS_URL=redis://redis:6379/0

# Docker Ollama (local LLM)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_LLM_MODEL=deepseek-r1:1.5b
OLLAMA_EMBED_MODEL=nomic-embed-text
```

**Size:** 26 lines
**Status:** ✅ Keep separate (Docker subsystem)

**⚠️ DO NOT MERGE INTO MAIN .env** - This would break Docker container networking!

---

## Summary Table

| File | Purpose | Bot Token | Database | LLM Provider | Keep Separate? |
|------|---------|-----------|----------|--------------|----------------|
| **`.env`** | Main Agent Factory | `8264955123...` | Neon/Supabase | OpenAI/Anthropic | N/A (main) |
| **`.env.phone_control`** | Phone Control Bot | `8208278660...` | Neon (shared) | Anthropic (shared) | ✅ YES |
| **`rivet/.env`** | Rivet Docker | N/A | Local Postgres | Local Ollama | ✅ YES |

---

## When to Use Each File

### Use `.env` (Main) When:
- Deploying to Render.com
- Running `telegram_bot.py`
- Running core agents
- Production PLC knowledge bot

### Use `.env.phone_control` When:
- Running `phone_control_bot.py`
- Testing phone automation
- Separate bot instance needed

### Use `rivet/.env` When:
- Running `docker-compose up` in `rivet/` directory
- Using Rivet Industrial KB Factory
- Local Ollama-based processing

---

## Quick Reference: Deployment Variables

**For Render.com deployment, you need (from main `.env`):**

```bash
# Core
TELEGRAM_BOT_TOKEN=8264955123:AAHLiOZmJXrOepJ82XGs_pcGwk6BIfEgGAs
TELEGRAM_ADMIN_CHAT_ID=8445149012
AUTHORIZED_TELEGRAM_USERS=8445149012

# Database
DATABASE_PROVIDER=neon
NEON_DB_URL=postgresql://neondb_owner:npg_N4SDwv1IfmUX@ep-bitter-shadow-ah70vrun-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# LLM
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o

# Voice
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural

# System
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

**Render API Key (for automated deployment):**
```bash
RENDER_API_KEY=rnd_E28gCMELQo0upAgxmjliHyve4C8X
```

---

## Changes Made (2025-12-13)

### Cleanup Applied to `.env` (Main)

**Fixed:**
1. ✅ Removed duplicate `RAILWAY_API_KEY` entries (lines 60-63)
2. ✅ Added proper `RENDER_API_KEY` variable
3. ✅ Added missing deployment variables:
   - `TELEGRAM_ADMIN_CHAT_ID`
   - `AUTHORIZED_TELEGRAM_USERS`
   - `DEFAULT_LLM_PROVIDER`
   - `DEFAULT_MODEL`
   - `PYTHONUNBUFFERED`
   - `LOG_LEVEL`

**Before:**
```bash
RAILWAY_API_KEY=77a1ca6c-35dd-4b40-8024-26d627bff7ef

new
RAILWAY_API_KEY=2db9f13b-9fe2-4063-b2d6-4609a0ac2ffb

# ... later in file ...
Render API key rnd_E28gCMELQo0upAgxmjliHyve4C8X  # Informal text
```

**After:**
```bash
RAILWAY_API_KEY=2db9f13b-9fe2-4063-b2d6-4609a0ac2ffb

# ... later in file ...
# ============================================================================
# DEPLOYMENT CONFIGURATION
# ============================================================================

RENDER_API_KEY=rnd_E28gCMELQo0upAgxmjliHyve4C8X
TELEGRAM_ADMIN_CHAT_ID=8445149012
AUTHORIZED_TELEGRAM_USERS=8445149012
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

---

## Security Notes

**⚠️ NEVER commit .env files to git!**

All .env files are in `.gitignore`:
```
.env
.env.*
rivet/.env
```

**What IS committed (safe):**
- `.env.example` - Template with no real credentials
- `rivet/.env.example` - Template with no real credentials

**What is NOT committed (secrets):**
- `.env` - Real production credentials
- `.env.phone_control` - Real phone bot credentials
- `rivet/.env` - Real Rivet credentials

---

## Troubleshooting

### "Wrong bot responding to commands"

**Cause:** Using `.env.phone_control` bot token in main `.env` (or vice versa)

**Fix:** Check which file your script is loading:
- `telegram_bot.py` → Should use `.env` (token `8264955123...`)
- `phone_control_bot.py` → Should use `.env.phone_control` (token `8208278660...`)

### "Database connection failed in Rivet"

**Cause:** Trying to use Neon/Supabase URLs in `rivet/.env`

**Fix:** Rivet uses local Docker Postgres:
```bash
POSTGRES_HOST=postgres  # NOT ep-bitter-shadow...
POSTGRES_DB=rivet       # NOT neondb
```

### "Environment variable not found"

**Cause:** Script loading wrong .env file

**Fix:** Check your script's `load_dotenv()` call:
```python
# Main bot
load_dotenv()  # Loads .env

# Phone control bot
load_dotenv(".env.phone_control")  # Loads phone control env

# Rivet
load_dotenv("rivet/.env")  # Loads Rivet env
```

---

## Next Steps for Deployment

1. ✅ Main `.env` is now clean and ready
2. ✅ All deployment variables configured
3. ⏳ Get Render service ID from dashboard
4. ⏳ Run configuration script:
   ```bash
   python scripts/deployment/configure_render_service.py \
     --api-key rnd_E28gCMELQo0upAgxmjliHyve4C8X \
     --service-id srv-YOUR_SERVICE_ID
   ```

---

**Last Updated:** 2025-12-13
**Status:** ✅ All .env files organized and documented
