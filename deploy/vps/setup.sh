#!/bin/bash
# First-time VPS setup for Agent Factory Telegram Bot
# Run on VPS: curl -sSL <url> | bash
# Or: scp this file to VPS and run it

set -e

echo "=== Agent Factory VPS Setup ==="

# Install dependencies
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone repo
cd /opt
if [ -d "Agent-Factory" ]; then
    echo "Repo exists, pulling latest..."
    cd Agent-Factory && git pull
else
    echo "Cloning repo..."
    git clone https://github.com/Mikecranesync/Agent-Factory.git
    cd Agent-Factory
fi

# Install Python dependencies
export PATH="$HOME/.local/bin:$PATH"
poetry install --no-dev

# Create .env template if not exists
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit /opt/Agent-Factory/.env with your API keys!"
fi

echo "=== Setup complete ==="
echo "Next steps:"
echo "1. Edit .env: nano /opt/Agent-Factory/.env"
echo "2. Install service: sudo cp deploy/vps/agent-factory-bot.service /etc/systemd/system/"
echo "3. Start bot: sudo systemctl enable --now agent-factory-bot"
