#!/bin/bash
# Check bot status
# Run: ssh root@72.60.175.144 'bash -s' < deploy/vps/status.sh

echo "=== Agent Factory Bot Status ==="

# Service status
echo ""
echo "[Service]"
systemctl status agent-factory-bot --no-pager -l | head -20

# Recent logs
echo ""
echo "[Recent Logs]"
journalctl -u agent-factory-bot -n 20 --no-pager

# Memory/CPU
echo ""
echo "[Resources]"
ps aux | grep -E "(telegram|agent_factory)" | grep -v grep

echo ""
echo "=== End Status ==="
