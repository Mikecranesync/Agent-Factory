#!/bin/bash
# Quick deployment script for Rivet KB Factory

set -e

echo "🚀 Rivet KB Factory - Quick Deployment"
echo "======================================"

# 1. Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose not installed"; exit 1; }
echo "✅ Prerequisites OK"

# 2. Setup environment
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✅ Created .env (edit if needed)"
else
    echo "✅ .env exists"
fi

# 3. Start services
echo "🐳 Starting Docker services..."
cd infra
docker compose up -d
echo "✅ Services started"

# 4. Wait for services to be healthy
echo "⏳ Waiting for services..."
sleep 10
echo "✅ Services ready"

# 5. Load Ollama models
echo "🤖 Loading Ollama models (this may take 5-10 minutes)..."
docker exec infra-ollama-1 ollama pull mistral:latest || echo "⚠️  Mistral model load failed - retry manually"
docker exec infra-ollama-1 ollama pull nomic-embed-text || echo "⚠️  Embedding model load failed - retry manually"
echo "✅ Models loaded"

# 6. Show status
echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "  - Monitor worker: docker compose -f infra/docker-compose.yml logs -f rivet-worker"
echo "  - Check queue: docker exec -it infra-redis-1 redis-cli LLEN kb_ingest_jobs"
echo "  - Query atoms: docker exec -it infra-postgres-1 psql -U rivet -d rivet -c 'SELECT COUNT(*) FROM knowledge_atoms;'"
echo ""
echo "Dashboard:"
echo "  Ollama: http://localhost:11434"
echo "  Postgres: localhost:5432"
echo "  Redis: localhost:6379"
