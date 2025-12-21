# Telegram Bot - Testing Manual

**Purpose:** Step-by-step guide to test your Agent Factory Telegram Bot
**Time Required:** 15-20 minutes
**Prerequisites:** Python, Poetry, and Telegram account

---

## Quick Summary

You'll be testing whether you can control Agent Factory from your phone/desktop via Telegram. Success means sending commands to the bot and receiving intelligent responses about your repository.

---

## Before You Start

**What You Need:**
- ✅ Agent Factory installed on your computer
- ✅ Telegram account (iOS, Android, or Desktop)
- ✅ Python 3.10+ and Poetry installed
- ✅ Command line access (Terminal, PowerShell, or Command Prompt)

**What You'll Get:**
- Remote control of Agent Factory from your phone
- Real-time notifications about PR commits
- Natural language queries about your codebase
- Agent status monitoring

---

## Step 1: Create Your Telegram Bot (One-Time Setup)

### 1.1 Open Telegram and Find BotFather

1. Open Telegram app (on phone or desktop)
2. Search for: **@BotFather**
3. Start a chat by clicking **START**

**What you should see:**
```
BotFather
I can help you create and manage Telegram bots.

/newbot - create a new bot
/mybots - edit your bots
...
```

### 1.2 Create New Bot

1. Send message: `/newbot`
2. BotFather asks: **"Alright, a new bot. How are we going to call it?"**
3. Reply with your bot name (example: `Agent Factory Controller`)
4. BotFather asks: **"Good. Now let's choose a username for your bot."**
5. Reply with username ending in "bot" (example: `agent_factory_mike_bot`)

**Important:** Username must be unique across all Telegram bots

### 1.3 Save Your Bot Token

**BotFather will reply with:**
```
Done! Congratulations on your new bot.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

Keep your token secure and store it safely, it can be
used by anyone to control your bot.
```

**Copy the token** (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Save it somewhere safe** - you'll need it in Step 2

### 1.4 Get Your Telegram User ID

1. In Telegram, search for: **@userinfobot**
2. Click **START**
3. Bot will reply with your user ID

**Example response:**
```
Id: 987654321
First name: Mike
...
```

**Copy your ID** (example: `987654321`) - you'll need it in Step 2

---

## Step 2: Configure Environment Variables

### 2.1 Navigate to Agent Factory Directory

**On Windows:**
```powershell
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
```

**On Mac/Linux:**
```bash
cd ~/path/to/Agent\ Factory
```

**Verify location:**
```bash
ls .env
```

**Expected output:**
```
.env
```

**If file doesn't exist:** Create it with `touch .env` (Mac/Linux) or `type nul > .env` (Windows)

### 2.2 Edit .env File

**Open .env in a text editor:**

**Windows:**
```powershell
notepad .env
```

**Mac:**
```bash
open -e .env
```

**Linux:**
```bash
nano .env
```

### 2.3 Add Bot Configuration

**Add these lines to your .env file:**

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
AUTHORIZED_TELEGRAM_USERS=987654321

# Optional: Daily standup time (24-hour format)
STANDUP_HOUR=8
STANDUP_MINUTE=0
```

**Replace:**
- `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` → Your bot token from Step 1.3
- `987654321` → Your user ID from Step 1.4

**Multiple users?** Separate IDs with commas:
```bash
AUTHORIZED_TELEGRAM_USERS=987654321,123456789,555555555
```

### 2.4 Save and Verify

**Save the file** (Ctrl+S or Cmd+S)

**Verify configuration:**
```bash
grep TELEGRAM_BOT_TOKEN .env
```

**Expected output:**
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## Step 3: Install Bot Dependencies

### 3.1 Install Required Packages

```bash
poetry install
```

**Expected output:**
```
Installing dependencies from lock file
...
Installing the current project: agent-factory (0.x.x)
```

**Wait time:** 1-3 minutes (first time)

### 3.2 Verify Installation

```bash
poetry run python -c "from agent_factory.integrations.telegram.bot import Application; print('OK')"
```

**Expected output:**
```
OK
```

**If you see an error:** Run `poetry install` again or check error message

---

## Step 4: Start the Bot

### 4.1 Start Bot (Method 1: Simple)

```bash
poetry run python scripts/automation/bot_manager.py start
```

**Expected output:**
```
============================================================
Agent Factory Telegram Bot Manager
============================================================
Command: START
============================================================
Starting bot...

✅ Bot started successfully
   PID: 12345
   Health endpoint: http://localhost:9876
   Status: Running
```

**Copy the PID** (example: 12345) - you'll need it to stop the bot later

### 4.2 Start Bot (Method 2: Windows Batch File)

**Alternative for Windows users:**

```bash
scripts\start_telegram_bot.bat
```

**Expected output:**
```
============================================================
Starting Agent Factory Telegram Bot
============================================================
[OK] Starting bot...
[SUCCESS] Bot started
```

### 4.3 Verify Bot is Running

```bash
poetry run python scripts/automation/bot_manager.py status
```

**Expected output:**
```
============================================================
Agent Factory Telegram Bot Manager
============================================================
Command: STATUS
============================================================

✅ Bot is RUNNING
   PID: 12345
   Uptime: 45 seconds
   Health: OK
   Endpoint: http://localhost:9876
```

**If you see:** `❌ Bot is NOT running`
**Fix:** Check Step 4.4 (Troubleshooting)

### 4.4 Troubleshooting Bot Start

#### Issue A: "Bot is already running"

**Cause:** Another instance is running

**Fix:**
```bash
poetry run python scripts/automation/bot_manager.py stop
poetry run python scripts/automation/bot_manager.py start
```

#### Issue B: "TELEGRAM_BOT_TOKEN not set"

**Cause:** .env file not configured or not loaded

**Fix:**
1. Verify .env file exists: `ls .env`
2. Verify token is set: `grep TELEGRAM_BOT_TOKEN .env`
3. Restart terminal (reload environment variables)
4. Try starting again

#### Issue C: "Invalid bot token"

**Cause:** Incorrect token format or typo

**Fix:**
1. Check token format: Must be `NUMBER:LETTERS` (e.g., `123456:ABCdef`)
2. No extra spaces in .env file
3. Get new token from @BotFather: `/token`
4. Update .env and restart

#### Issue D: "Port 9876 already in use"

**Cause:** Health endpoint port is occupied

**Fix:**
```bash
# Windows
netstat -ano | findstr :9876
taskkill /F /PID <PID>

# Mac/Linux
lsof -i :9876
kill -9 <PID>
```

---

## Step 5: Test the Bot on Telegram

### 5.1 Open Your Bot on Telegram

1. Open Telegram app
2. Search for your bot username (example: `@agent_factory_mike_bot`)
3. Click **START**

**What you should see:**
```
Welcome to Agent Factory! 🤖

I'm your remote control interface for the Agent Factory system.

Available commands:
/help - Show all commands
/status - Check system status
/agents - List active agents
/metrics - View performance metrics
...
```

### 5.2 Test Basic Commands

**Command 1: Check Status**

Send: `/status`

**Expected response:**
```
System Status 🟢

Agents: 3 active
Memory: 45% used
CPU: 23%
Uptime: 2 hours

Last activity: 5 minutes ago
```

**Command 2: List Agents**

Send: `/agents`

**Expected response:**
```
Active Agents (3)

1. 🔍 Researcher - Idle
2. 💻 Coder - Processing
3. 📊 Analyst - Idle

Send /agent <name> for details
```

**Command 3: Get Help**

Send: `/help`

**Expected response:**
```
Available Commands

📊 Monitoring
/status - System status
/agents - List agents
/metrics - Performance metrics

🔧 Control
/approve - Approve pending items
/reject - Reject pending items

📝 Tasks
/issue <title> - Create new issue
/task <description> - Queue task

For detailed help: /help <command>
```

### 5.3 Test Natural Language Queries

**The bot should understand natural language!**

**Query 1: Ask about code**

Send: `What does the orchestrator do?`

**Expected response:**
```
🔍 Found in `agent_factory/core/orchestrator.py`

The orchestrator is the main routing engine that:
- Receives user queries
- Selects the best specialist agent
- Routes the query to that agent
- Returns the response

Used in Phase 1 for multi-agent routing.
```

**Query 2: Ask for recent changes**

Send: `What changed recently?`

**Expected response:**
```
📝 Recent Commits (last 5)

1. [2h ago] feat: Add SafetyRails validation
2. [5h ago] docs: Update testing manual
3. [1d ago] fix: Orchestrator timeout issue
4. [1d ago] test: Add integration tests
5. [2d ago] refactor: Simplify memory storage

Git branch: main
Status: Clean (no uncommitted changes)
```

**Query 3: Request analysis**

Send: `Check for security issues`

**Expected response:**
```
🔒 Security Analysis

Scanning codebase...
✅ No SQL injection vulnerabilities
✅ Environment variables properly secured
⚠️ Found 2 TODO items:
  - Add rate limiting to API endpoints
  - Implement request validation

Recommendation: Address warnings before production deploy
```

### 5.4 Test Notifications (Optional)

**If you have autonomous agents running, you should receive notifications:**

**Example notification:**
```
🤖 Agent Update

Agent: PRCreator
Status: Completed
Task: Create PR for feature-123

PR: https://github.com/user/repo/pull/123
✅ Tests passed
⏳ Awaiting review

Reply /approve to merge, /reject to close
```

---

## Step 6: Verify Two-Way Communication

### 6.1 Test Outbound (Bot → You)

**Trigger:** Create a test PR or run an agent task

**What you should see:**
- Notification appears in Telegram chat within 30 seconds
- Message includes relevant details (files changed, tests status, PR link)
- Action buttons for approve/reject

### 6.2 Test Inbound (You → Bot)

**Send commands to bot:**

1. `/status` → Immediate response
2. `What files are in src/` → Intelligent response with file list
3. `Run tests` → Confirmation + test results
4. `/approve` → Processes approval + confirms

**Success criteria:**
- All commands receive responses within 5 seconds
- Natural language queries are understood and answered correctly
- Bot provides context-aware responses (file paths, line numbers, links)

---

## Step 7: Stop the Bot (Cleanup)

### 7.1 Stop Bot Gracefully

```bash
poetry run python scripts/automation/bot_manager.py stop
```

**Expected output:**
```
============================================================
Agent Factory Telegram Bot Manager
============================================================
Command: STOP
============================================================

Found bot process: PID 12345
Sending SIGTERM...
✅ Bot stopped (PID 12345)
```

### 7.2 Verify Bot Stopped

```bash
poetry run python scripts/automation/bot_manager.py status
```

**Expected output:**
```
❌ Bot is NOT running
   Lock file: Released
   Health endpoint: Unreachable
```

### 7.3 Clean Up (Optional)

**Remove test messages from Telegram:**
1. Open chat with your bot
2. Long-press on message → Delete
3. Select "Delete for me" or "Delete for everyone"

**Keep the bot token:** You'll use it again for production

---

## Step 8: Production Deployment (Optional)

### 8.1 Windows Service (24/7 Auto-Start)

**For running bot continuously on Windows:**

```powershell
# Run as Administrator
PowerShell -ExecutionPolicy Bypass -File scripts\install_telegram_service.ps1
```

**Expected output:**
```
Installing Agent Factory Telegram Bot as Windows Service...
Service installed successfully
Starting service...
Service started

Status: Running
Startup type: Automatic (starts on boot)

View logs: logs\telegram_bot_stdout.log
```

**Verify service:**
```powershell
nssm status AgentFactoryTelegramBot
```

**Expected output:**
```
SERVICE_RUNNING
```

### 8.2 Linux/Mac Systemd Service

**For running bot on Linux/Mac server:**

1. Create systemd service file:
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

2. Add configuration:
```ini
[Unit]
Description=Agent Factory Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Agent Factory
ExecStart=/usr/local/bin/poetry run python scripts/automation/bot_manager.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### 8.3 VPS Deployment

**For running on cloud server (Railway, DigitalOcean, etc.):**

See: `Guides for Users/deployment/PRODUCTION_DEPLOYMENT.md`

---

## Success Checklist

After completing this manual, you should have:

- [x] Created Telegram bot via @BotFather
- [x] Configured environment variables in .env
- [x] Started bot successfully (verified with `/status` command)
- [x] Tested basic commands (/help, /status, /agents)
- [x] Tested natural language queries (code questions, recent changes)
- [x] Verified two-way communication (outbound notifications + inbound commands)
- [x] Stopped bot gracefully
- [x] Optional: Set up production deployment (Windows Service or systemd)

---

## Common Use Cases

### Use Case 1: Check Repo Status from Phone

**Scenario:** You're away from computer, want to check if PRs are merged

**Command:** Send to bot: `status`

**Result:** Immediate status update with recent commits, open PRs, test status

### Use Case 2: Approve PR from Anywhere

**Scenario:** Bot notifies you of completed PR, you approve from phone

**Steps:**
1. Receive notification: "PR #123 ready for review"
2. Reply: `/approve`
3. Bot merges PR and confirms

### Use Case 3: Query Codebase

**Scenario:** Need to remember how a function works

**Command:** `What does the parse_task function do?`

**Result:** Bot searches repo, finds function, explains with code snippet + file path

### Use Case 4: Monitor Autonomous Agents

**Scenario:** Agents running overnight, you want updates

**Command:** `/agents`

**Result:** List of all active agents with current status, time running, task queue

### Use Case 5: Create Issues on the Go

**Scenario:** Notice a bug, want to log it immediately

**Command:** `/issue Fix authentication timeout on mobile`

**Result:** Bot creates GitHub issue and confirms with link

---

## Troubleshooting Reference

### Bot Not Responding

**Check 1:** Is bot running?
```bash
poetry run python scripts/automation/bot_manager.py status
```

**Check 2:** Is token correct?
```bash
grep TELEGRAM_BOT_TOKEN .env
```

**Check 3:** Are you authorized?
```bash
grep AUTHORIZED_TELEGRAM_USERS .env
# Your user ID should be in the list
```

**Fix:** Restart bot:
```bash
poetry run python scripts/automation/bot_manager.py restart
```

### Bot Responds Slowly (>5 seconds)

**Cause:** Large repo or complex query

**Fix:**
- Use more specific queries: "What does X do?" instead of "Explain everything"
- Check CPU usage: `poetry run python scripts/automation/bot_manager.py status`
- Restart bot if memory usage >80%

### Bot Says "Unauthorized"

**Cause:** Your Telegram user ID not in AUTHORIZED_TELEGRAM_USERS

**Fix:**
1. Get your user ID from @userinfobot
2. Add to .env: `AUTHORIZED_TELEGRAM_USERS=987654321,<new-id>`
3. Restart bot

### Bot Crashes on Startup

**Check logs:**
```bash
# Windows
type logs\telegram_bot_stdout.log

# Mac/Linux
cat logs/telegram_bot_stdout.log
```

**Common errors:**
- `ModuleNotFoundError` → Run `poetry install`
- `Port already in use` → Kill process on port 9876
- `Invalid token` → Check token format in .env

---

## Advanced Features

### Custom Commands

**Add your own commands by editing:**
`agent_factory/integrations/telegram/handlers.py`

**Example:**
```python
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mycustom command"""
    await update.message.reply_text("Custom response!")

# Register in main bot file
application.add_handler(CommandHandler("mycustom", custom_command))
```

### Webhook Mode (Instead of Polling)

**For faster response times on production server:**

See: `scripts/deployment/set_telegram_webhook.py`

**Benefits:**
- Instant message delivery (no polling delay)
- Lower resource usage
- Better for high-traffic bots

**Requirements:**
- Public HTTPS endpoint
- SSL certificate
- Webhook URL configuration

### Natural Language Processing

**Bot uses intent classification to understand queries:**

**Question Intent:** "What", "How", "Explain", "Show me"
→ Searches repo for answer

**Command Intent:** "Create", "Make", "Add", "Delete"
→ Asks for confirmation, executes

**Analysis Intent:** "Check", "Review", "Find bugs", "Test"
→ Runs analysis, reports findings

**Status Intent:** "Status", "Recent", "What's new"
→ Shows git status + recent commits

---

## Quick Reference Card

**Start bot:**
```bash
poetry run python scripts/automation/bot_manager.py start
```

**Check status:**
```bash
poetry run python scripts/automation/bot_manager.py status
```

**Stop bot:**
```bash
poetry run python scripts/automation/bot_manager.py stop
```

**Restart bot:**
```bash
poetry run python scripts/automation/bot_manager.py restart
```

**View logs:**
```bash
# Windows
type logs\telegram_bot_stdout.log

# Mac/Linux
tail -f logs/telegram_bot_stdout.log
```

**Telegram commands:**
- `/help` - Show all commands
- `/status` - System status
- `/agents` - List active agents
- `/metrics` - Performance metrics
- `/approve` - Approve pending item
- `/reject` - Reject pending item
- `/issue <title>` - Create issue

**Natural language:**
- `What does X do?` - Ask about code
- `Show me recent changes` - Git history
- `Check for errors` - Run analysis
- `Explain authentication` - Search docs

---

## Support

**Documentation:**
- Setup Guide: `Guides for Users/deployment/BOT_DEPLOYMENT_GUIDE.md`
- Reliability Guide: `Guides for Users/deployment/TELEGRAM_BOT_100_PERCENT_RELIABLE.md`
- Auto-start Guide: `Guides for Users/deployment/TELEGRAM_AUTO_START_GUIDE.md`

**Telegram Resources:**
- BotFather: @BotFather (create/manage bots)
- User ID Bot: @userinfobot (get your user ID)
- Telegram Bot API: https://core.telegram.org/bots/api

**Troubleshooting:**
- Check bot manager: `scripts/automation/bot_manager.py`
- Check health endpoint: http://localhost:9876/health
- Check logs: `logs/telegram_bot_stdout.log`

---

**Created:** 2025-12-20
**Version:** 1.0
**Author:** Claude Code
**Purpose:** User-friendly testing manual for Agent Factory Telegram Bot
