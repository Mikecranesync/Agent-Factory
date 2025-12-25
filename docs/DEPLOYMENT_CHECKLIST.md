# Deployment Checklist

**CRITICAL: Always follow this checklist to prevent duplicate instance conflicts.**

## Pre-Deployment Steps

### 1. Kill Old Instances (MANDATORY)

**Before deploying ANY bot or service, ALWAYS check for and kill existing instances first.**

#### VPS Deployment
```bash
# Step 1: Stop systemd service
ssh vps "systemctl stop orchestrator-bot"

# Step 2: Kill any remaining processes
ssh vps "pkill -f orchestrator_bot || true"

# Step 3: Verify no instances running
ssh vps "ps aux | grep orchestrator_bot | grep -v grep"
# Should return: nothing

# Step 4: Wait for cleanup
sleep 3
```

#### Local Development
```powershell
# Windows: Kill all local bot instances
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# Verify no Python processes running
Get-Process -Name python* -ErrorAction SilentlyContinue
```

```bash
# Linux/Mac: Kill local bot instances
pkill -f orchestrator_bot || true

# Verify
ps aux | grep orchestrator_bot | grep -v grep
```

### 2. Verify Telegram Bot Status

```bash
# Check for webhook conflicts
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
# webhook "url" should be empty for polling bots

# Check for pending updates
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates?limit=1"
```

## Deployment Steps

### 1. Push Code to VPS

```bash
# Push latest code
ssh vps "cd /root/Agent-Factory && git pull origin main"
```

### 2. Start Service

```bash
# Start systemd service
ssh vps "systemctl start orchestrator-bot"

# Verify status
ssh vps "systemctl status orchestrator-bot --no-pager"
```

### 3. Verify Single Instance

```bash
# Check process count (should be 1)
ssh vps "ps aux | grep orchestrator_bot | grep -v grep | wc -l"

# Expected output: 1
```

## Post-Deployment Verification

### 1. Monitor Logs for Conflicts (60 seconds)

```bash
timeout 60 ssh vps "journalctl -u orchestrator-bot -f -n 20" || true
```

**Look for:**
- ✅ HTTP 200 OK (good - successful polling)
- ❌ HTTP 409 Conflict (bad - duplicate instance exists)

### 2. Test Bot Functionality

```bash
# Send test message to @RivetCeo_bot
# Verify response received
```

### 3. Check Knowledge Base Connection

Look for in logs:
```
Database initialized with 1964 knowledge atoms
Orchestrator initialized successfully with RAG layer
```

## Rollback Plan

If deployment fails:

```bash
# 1. Stop new deployment
ssh vps "systemctl stop orchestrator-bot"

# 2. Revert code
ssh vps "cd /root/Agent-Factory && git reset --hard HEAD~1"

# 3. Restart service
ssh vps "systemctl start orchestrator-bot"

# 4. Verify
ssh vps "systemctl status orchestrator-bot"
```

## Common Issues

### Issue: HTTP 409 Conflict (Telegram getUpdates)

**Cause:** Multiple bot instances polling Telegram simultaneously

**Solution:**
1. Stop all instances (VPS + local)
2. Verify no processes running
3. Start only ONE instance
4. Monitor logs for 60 seconds

### Issue: Bot not responding

**Cause:** Database connection failure or RAG layer not initialized

**Solution:**
```bash
# Check logs for errors
ssh vps "journalctl -u orchestrator-bot -n 100 --no-pager | grep -E 'ERROR|WARNING'"

# Verify environment variables
ssh vps "cd /root/Agent-Factory && cat .env | grep -E 'DB_|BOT_TOKEN'"

# Restart service
ssh vps "systemctl restart orchestrator-bot"
```

### Issue: Service won't start

**Cause:** Port already in use or systemd configuration error

**Solution:**
```bash
# Check systemd service file
ssh vps "cat /etc/systemd/system/orchestrator-bot.service"

# Reload daemon
ssh vps "systemctl daemon-reload"

# Try starting again
ssh vps "systemctl start orchestrator-bot"

# Check detailed status
ssh vps "systemctl status orchestrator-bot -l"
```

## Success Criteria

- [ ] Only ONE bot instance running (verified with `ps aux`)
- [ ] No HTTP 409 Conflict errors in logs
- [ ] Continuous HTTP 200 OK polling every ~10 seconds
- [ ] Bot responds to Telegram messages
- [ ] Database shows 1,964 knowledge atoms loaded
- [ ] RAG layer initialized successfully

## Last Updated

2025-12-22 - Added mandatory pre-deployment instance cleanup

## Notes

- **NEVER leave local bot instances running** - they conflict with VPS deployment
- Always verify single instance before considering deployment complete
- Monitor logs for at least 60 seconds to catch intermittent conflicts
- Document any changes to this checklist in git commit messages
