# Claude Code CLI - VPS Remote Connection Setup

**Connect Claude Code CLI directly to your Hostinger VPS for real-time debugging and deployment.**

---

## Prerequisites

✅ SSH key pair generated (see `GITHUB_SECRETS_SETUP.md`)
✅ Public key added to VPS `/root/.ssh/authorized_keys`
✅ Claude Code CLI installed

---

## SSH Key Location

**Private key path (Windows):**
```
C:\Users\hharp\.ssh\vps_deploy_key
```

**Public key path (Windows):**
```
C:\Users\hharp\.ssh\vps_deploy_key.pub
```

**Public key content:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKBgDPBWVB4QS5COYGFzf0S9xRkNSGAFi+nlQlTf6WJM github-actions@agent-factory
```

---

## Configure Claude Code CLI Connection

### Step 1: Add VPS Public Key to `authorized_keys`

**Option A: Manual (if not already done)**
```bash
# SSH into VPS with password
ssh root@72.60.175.144

# Add public key
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKBgDPBWVB4QS5COYGFzf0S9xRkNSGAFi+nlQlTf6WJM github-actions@agent-factory" >> ~/.ssh/authorized_keys

# Set permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Test (exit and reconnect with key)
exit
ssh -i C:/Users/hharp/.ssh/vps_deploy_key root@72.60.175.144
```

**Option B: Automated (from Windows)**
```bash
# Copy public key to VPS
ssh-copy-id -i C:/Users/hharp/.ssh/vps_deploy_key.pub root@72.60.175.144

# Test connection
ssh -i C:/Users/hharp/.ssh/vps_deploy_key root@72.60.175.144
```

### Step 2: Configure Remote SSH in Claude Code CLI

**In Claude Code CLI app:**

1. Open **Remote SSH** settings
2. Click **Add New Connection**
3. Enter connection details:

```
Host: 72.60.175.144
User: root
Authentication: SSH Key
Identity File: C:\Users\hharp\.ssh\vps_deploy_key
```

4. **Save** the connection profile
5. Click **Connect**

### Step 3: Test Connection

Once connected, Claude Code CLI should show:
```
Connected to: root@72.60.175.144
Working directory: /root
```

Navigate to the project:
```bash
cd /root/Agent-Factory
```

---

## Usage - Deploy & Debug on VPS

Once connected via Claude Code CLI, you can:

### 1. Inspect Deployment Files
```bash
# Check current state
ls -la /root/Agent-Factory/

# View deployment script
cat deploy_rivet_pro.sh

# Check if bot is running
ps aux | grep telegram_bot
```

### 2. Install Dependencies
```bash
# Check Poetry
poetry --version

# If missing, install:
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"

# Install Python packages
poetry install --no-dev
```

### 3. Deploy Bot
```bash
# Make script executable
chmod +x deploy_rivet_pro.sh

# Run deployment
./deploy_rivet_pro.sh
```

### 4. Check Health Endpoint
```bash
# Test locally on VPS
curl http://localhost:9876/health

# Expected output:
# {"status":"running","pid":12345,"uptime_seconds":60}
```

### 5. Manage systemd Service
```bash
# Install service
sudo cp rivet-pro.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rivet-pro

# Control service
sudo systemctl start rivet-pro
sudo systemctl status rivet-pro
sudo systemctl restart rivet-pro

# View logs
sudo journalctl -u rivet-pro -f
```

### 6. Debug Issues
```bash
# Check bot logs
tail -f /root/Agent-Factory/logs/bot.log
tail -f /root/Agent-Factory/logs/bot-error.log

# Check environment
cat .env | head -10  # Don't print secrets!

# Test Python imports
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"
```

---

## Handoff Prompt for Claude Code CLI

Once connected to VPS, give Claude Code CLI this prompt:

```
You are connected via SSH to my Hostinger VPS in /root/Agent-Factory.

The goal is to get the "RIVET Pro" Telegram bot fully deployed and reliable with the existing GitHub Actions workflow and deploy_rivet_pro.sh.

1. Inspect this repo and deploy_rivet_pro.sh, the systemd unit, and .github/workflows/deploy-vps.yml.
2. Ensure Poetry and all runtime dependencies are installed correctly on the VPS.
3. Fix any issues so the GitHub Actions workflow can run end-to-end without manual intervention.
4. Make sure the bot process is managed by systemd (auto-restart on failure and on reboot).
5. Confirm the health endpoint and Telegram notifications work, and tell me exactly which URL/port I can use to verify it from my browser.
6. At the end, summarize: how to deploy (GitHub Actions and any manual command), where logs live, and how to restart the bot manually if needed.
```

---

## Troubleshooting

### "Permission denied (publickey)"

**Solution:**
```bash
# Verify public key is on VPS
ssh root@72.60.175.144 "cat ~/.ssh/authorized_keys"

# Should contain:
# ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKBgDPBWVB4QS5COYGFzf0S9xRkNSGAFi+nlQlTf6WJM github-actions@agent-factory
```

### "Could not resolve hostname"

**Solution:**
- Check VPS IP is correct: `72.60.175.144`
- Test connectivity: `ping 72.60.175.144`

### "Connection refused"

**Solution:**
```bash
# Check SSH service is running on VPS
ssh root@72.60.175.144 "systemctl status sshd"

# Check firewall allows SSH
ssh root@72.60.175.144 "sudo ufw status"
```

---

## Benefits of Claude Code CLI on VPS

**Real-time debugging:**
- Edit files directly on VPS
- Run commands in actual production environment
- Test deployment script immediately
- View logs in real-time

**Faster iteration:**
- No git push → wait → check logs cycle
- Fix issues on VPS, then commit working code
- Test systemd service integration
- Verify health endpoint responds

**Complete visibility:**
- See exact Python/Poetry versions
- Check environment variables
- Monitor process status
- Debug networking issues

---

## Security Notes

**✅ DO:**
- Use SSH key authentication (no password)
- Rotate keys periodically
- Use dedicated deploy key (not personal key)
- Keep private key secure (never commit to git)

**❌ DON'T:**
- Share private key via email/Slack
- Use same key for multiple services
- Commit private key to repository
- Leave Claude Code CLI session unattended

---

## Quick Reference

**Connect:**
```
Host: 72.60.175.144
User: root
Key: C:\Users\hharp\.ssh\vps_deploy_key
```

**Project directory:**
```
/root/Agent-Factory
```

**Key commands:**
```bash
./deploy_rivet_pro.sh                      # Deploy bot
curl http://localhost:9876/health          # Check health
sudo systemctl status rivet-pro            # Check service
tail -f /root/Agent-Factory/logs/bot.log   # View logs
```

---

**You're ready!** Connect Claude Code CLI to your VPS and let it handle the deployment debugging. 🚀
