# Rivet KB Factory - Automated VPS Deployment
# Usage: .\deploy_rivet_vps.ps1
# Deploys the 24/7 KB ingestion pipeline to Hostinger VPS

$VPS_IP = "72.60.175.144"
$SSH_USER = "root"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Rivet KB Factory - VPS Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target: $SSH_USER@$VPS_IP" -ForegroundColor Yellow
Write-Host ""

# Step 1: Test SSH
Write-Host "[1/6] Testing SSH connection..." -ForegroundColor Yellow
try {
    ssh -o ConnectTimeout=10 "$SSH_USER@$VPS_IP" "echo 'Connected'" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "SSH failed" }
    Write-Host "  [OK] SSH connection working" -ForegroundColor Green
} catch {
    Write-Host "  [!] Enter SSH password when prompted" -ForegroundColor Yellow
}

# Step 2: Install Docker
Write-Host ""
Write-Host "[2/6] Installing Docker on VPS..." -ForegroundColor Yellow

$dockerInstall = @'
#!/bin/bash
set -e

# Check if Docker exists
if command -v docker &> /dev/null; then
    echo "Docker already installed: $(docker --version)"
else
    echo "Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo "Docker installed: $(docker --version)"
fi

# Install Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose already installed"
else
    echo "Installing Docker Compose..."
    apt-get install -y -qq docker-compose
fi

echo "Docker setup complete"
'@

$dockerInstall | ssh "$SSH_USER@$VPS_IP" "bash"
Write-Host "  [OK] Docker installed" -ForegroundColor Green

# Step 3: Create rivet directory and upload code
Write-Host ""
Write-Host "[3/6] Uploading Rivet KB Factory code..." -ForegroundColor Yellow

# Create the rivet structure on VPS
ssh "$SSH_USER@$VPS_IP" "mkdir -p /opt/rivet/langgraph_app/nodes /opt/rivet/langgraph_app/graphs /opt/rivet/infra"

# Upload files using scp
$localRivet = "C:\Users\hharp\OneDrive\Desktop\Agent Factory\rivet"
scp -r "$localRivet\langgraph_app" "$SSH_USER@${VPS_IP}:/opt/rivet/"
scp -r "$localRivet\infra\*" "$SSH_USER@${VPS_IP}:/opt/rivet/infra/"
scp "$localRivet\requirements.txt" "$SSH_USER@${VPS_IP}:/opt/rivet/"
scp "$localRivet\.env" "$SSH_USER@${VPS_IP}:/opt/rivet/"

Write-Host "  [OK] Code uploaded" -ForegroundColor Green

# Step 4: Update .env with production password
Write-Host ""
Write-Host "[4/6] Configuring environment..." -ForegroundColor Yellow

ssh "$SSH_USER@$VPS_IP" @'
cd /opt/rivet
# Update password in .env
sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=rivet_prod_2025!/' .env
chmod 600 .env
echo "Environment configured"
'@

Write-Host "  [OK] Environment configured" -ForegroundColor Green

# Step 5: Build and start services
Write-Host ""
Write-Host "[5/6] Building and starting Docker services..." -ForegroundColor Yellow
Write-Host "  (This takes 3-5 minutes on first run)" -ForegroundColor Gray

ssh "$SSH_USER@$VPS_IP" @'
cd /opt/rivet/infra
docker-compose down 2>/dev/null || true
docker-compose build
docker-compose up -d
echo ""
echo "Services started:"
docker-compose ps
'@

Write-Host "  [OK] Services started" -ForegroundColor Green

# Step 6: Pull Ollama models
Write-Host ""
Write-Host "[6/6] Pulling Ollama models..." -ForegroundColor Yellow
Write-Host "  (This takes 2-3 minutes)" -ForegroundColor Gray

ssh "$SSH_USER@$VPS_IP" @'
echo "Waiting for Ollama to be ready..."
sleep 10

echo "Pulling deepseek-r1:1.5b (1.1GB)..."
docker exec rivet-ollama-1 ollama pull deepseek-r1:1.5b 2>/dev/null || \
docker exec infra-ollama-1 ollama pull deepseek-r1:1.5b

echo "Pulling nomic-embed-text (274MB)..."
docker exec rivet-ollama-1 ollama pull nomic-embed-text 2>/dev/null || \
docker exec infra-ollama-1 ollama pull nomic-embed-text

echo ""
echo "Models available:"
docker exec rivet-ollama-1 ollama list 2>/dev/null || \
docker exec infra-ollama-1 ollama list
'@

Write-Host "  [OK] Models pulled" -ForegroundColor Green

# Step 7: Initialize database
Write-Host ""
Write-Host "[7/7] Initializing database..." -ForegroundColor Yellow

ssh "$SSH_USER@$VPS_IP" @'
cd /opt/rivet/infra
echo "Creating database schema..."
cat init_db.sql | docker exec -i infra-postgres-1 psql -U rivet -d rivet 2>/dev/null || \
cat init_db.sql | docker exec -i rivet-postgres-1 psql -U rivet -d rivet

echo ""
echo "Database tables:"
docker exec infra-postgres-1 psql -U rivet -d rivet -c "\dt" 2>/dev/null || \
docker exec rivet-postgres-1 psql -U rivet -d rivet -c "\dt"
'@

Write-Host "  [OK] Database initialized" -ForegroundColor Green

# Final summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Rivet KB Factory is now running 24/7 on your VPS!" -ForegroundColor Cyan
Write-Host ""
Write-Host "VPS: $VPS_IP" -ForegroundColor White
Write-Host ""
Write-Host "Services Running:" -ForegroundColor Yellow
Write-Host "  - PostgreSQL + pgvector (port 5432)"
Write-Host "  - Redis job queue (port 6379)"
Write-Host "  - Ollama LLM (port 11434)"
Write-Host "  - Rivet Worker (processing jobs)"
Write-Host "  - Rivet Scheduler (hourly jobs)"
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Yellow
Write-Host "  # Check services:"
Write-Host "  ssh root@$VPS_IP 'cd /opt/rivet/infra && docker-compose ps'"
Write-Host ""
Write-Host "  # View worker logs:"
Write-Host "  ssh root@$VPS_IP 'docker logs infra-rivet-worker-1 --tail 50'"
Write-Host ""
Write-Host "  # Add URL to process:"
Write-Host "  ssh root@$VPS_IP 'docker exec infra-redis-1 redis-cli RPUSH kb_ingest_jobs ""https://example.com/manual.pdf""'"
Write-Host ""
Write-Host "  # Check atom count:"
Write-Host "  ssh root@$VPS_IP 'docker exec infra-postgres-1 psql -U rivet -d rivet -c ""SELECT COUNT(*) FROM knowledge_atoms;""'"
Write-Host ""
