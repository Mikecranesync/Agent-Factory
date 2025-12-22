# VPS Deployment Guide

## First-Time Setup

1. SSH into VPS:
```bash
ssh root@72.60.175.144
```

2. Run setup script:
```bash
curl -sSL https://raw.githubusercontent.com/Mikecranesync/Agent-Factory/main/deploy/vps/setup.sh | bash
```

3. Add your API keys:
```bash
nano /opt/Agent-Factory/.env
```

4. Install and start service:
```bash
cp /opt/Agent-Factory/deploy/vps/agent-factory-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable agent-factory-bot
systemctl start agent-factory-bot
```

5. Verify it's running:
```bash
systemctl status agent-factory-bot
```

## Daily Operations

### Deploy updates (from your local machine):
```bash
ssh root@72.60.175.144 'bash -s' < deploy/vps/deploy.sh
```

### Check status:
```bash
ssh root@72.60.175.144 'bash -s' < deploy/vps/status.sh
```

### View live logs:
```bash
ssh root@72.60.175.144 'journalctl -u agent-factory-bot -f'
```

### Restart bot:
```bash
ssh root@72.60.175.144 'systemctl restart agent-factory-bot'
```

### Stop bot:
```bash
ssh root@72.60.175.144 'systemctl stop agent-factory-bot'
```

## Troubleshooting

### Bot won't start
```bash
# Check logs for errors
journalctl -u agent-factory-bot -n 50

# Verify .env exists and has keys
cat /opt/Agent-Factory/.env | grep -E "^[A-Z]"

# Try running manually
cd /opt/Agent-Factory
poetry run python -m agent_factory.integrations.telegram
```

### Bot keeps crashing
```bash
# Check memory
free -h

# Check disk
df -h

# View crash logs
journalctl -u agent-factory-bot --since "1 hour ago"
```
