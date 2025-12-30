#!/bin/bash
# Deploy Slack Supervisor to Production VPS
# Usage: ./scripts/deploy_slack_supervisor.sh

set -e

VPS_HOST="${VPS_HOST:-72.60.175.144}"
VPS_USER="${VPS_USER:-root}"
VPS_PATH="${VPS_PATH:-/root/Agent-Factory}"

echo "=========================================="
echo "Deploying Slack Supervisor to VPS"
echo "=========================================="
echo ""
echo "VPS: $VPS_USER@$VPS_HOST"
echo "Path: $VPS_PATH"
echo ""

# Step 1: Copy Python modules
echo "[1/6] Copying observability modules..."
scp -r agent_factory/observability/*.py "$VPS_USER@$VPS_HOST:$VPS_PATH/agent_factory/observability/"

# Step 2: Copy SQL schema
echo "[2/6] Copying database schema..."
scp sql/supervisor_schema.sql "$VPS_USER@$VPS_HOST:$VPS_PATH/sql/"

# Step 3: Copy systemd service
echo "[3/6] Copying systemd service..."
scp rivet/supervisor.service "$VPS_USER@$VPS_HOST:/etc/systemd/system/"

# Step 4: Deploy database schema
echo "[4/6] Deploying database schema..."
ssh "$VPS_USER@$VPS_HOST" "cd $VPS_PATH && psql \$DATABASE_URL -f sql/supervisor_schema.sql"

# Step 5: Install dependencies
echo "[5/6] Installing dependencies..."
ssh "$VPS_USER@$VPS_HOST" "cd $VPS_PATH && poetry add asyncpg httpx"

# Step 6: Start/restart service
echo "[6/6] Starting supervisor service..."
ssh "$VPS_USER@$VPS_HOST" "
    systemctl daemon-reload
    systemctl enable supervisor
    systemctl restart supervisor
    sleep 2
    systemctl status supervisor --no-pager
"

echo ""
echo "=========================================="
echo "✓ Deployment Complete"
echo "=========================================="
echo ""
echo "Health check:"
echo "  curl http://$VPS_HOST:3001/health"
echo ""
echo "View logs:"
echo "  ssh $VPS_USER@$VPS_HOST journalctl -u supervisor -f"
echo ""
echo "View tasks:"
echo "  curl http://$VPS_HOST:3001/tasks"
echo ""
