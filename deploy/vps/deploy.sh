#!/bin/bash
# Deploy latest code and restart bot
# Run: ssh root@72.60.175.144 'bash -s' < deploy/vps/deploy.sh

set -e

echo "=== Deploying Agent Factory Bot ==="

cd /opt/Agent-Factory

# Pull latest
echo "[1/4] Pulling latest code..."
git pull origin main

# Update dependencies
echo "[2/4] Updating dependencies..."
export PATH="$HOME/.local/bin:$PATH"
poetry install --no-dev

# Restart service
echo "[3/4] Restarting bot..."
sudo systemctl restart agent-factory-bot

# Check status
echo "[4/4] Checking status..."
sleep 3
sudo systemctl status agent-factory-bot --no-pager

echo "=== Deploy complete ==="
