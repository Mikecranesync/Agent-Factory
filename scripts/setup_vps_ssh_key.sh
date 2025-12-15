#!/bin/bash
#
# VPS SSH Key Setup Script
# Adds the GitHub Actions SSH key to VPS authorized_keys
#
# Usage:
#   1. Copy your PUBLIC key (vps_deploy_key.pub) to clipboard
#   2. SSH into VPS: ssh root@72.60.175.144
#   3. Run: curl -sSL https://raw.githubusercontent.com/Mikecranesync/Agent-Factory/main/scripts/setup_vps_ssh_key.sh | bash -s -- "YOUR_PUBLIC_KEY_HERE"
#
# Or run locally after SSH:
#   ./setup_vps_ssh_key.sh "ssh-ed25519 AAAAC3NzaC1... github-actions@agent-factory"

set -e

PUBLIC_KEY="$1"

if [ -z "$PUBLIC_KEY" ]; then
    echo "❌ Error: No public key provided"
    echo ""
    echo "Usage: $0 \"ssh-ed25519 AAAAC3NzaC1... github-actions@agent-factory\""
    echo ""
    echo "Get your public key by running on your local machine:"
    echo "  cat ~/.ssh/vps_deploy_key.pub"
    echo "  # or on Windows:"
    echo "  cat C:/Users/hharp/.ssh/vps_deploy_key.pub"
    exit 1
fi

echo "🔐 Setting up SSH key for VPS deployment..."
echo ""

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add public key to authorized_keys
if grep -q "$PUBLIC_KEY" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "✅ SSH key already exists in authorized_keys"
else
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    echo "✅ Added SSH key to authorized_keys"
fi

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys

echo ""
echo "✅ SSH key setup complete!"
echo ""
echo "Test authentication from your local machine:"
echo "  ssh -i ~/.ssh/vps_deploy_key root@72.60.175.144"
echo "  # or on Windows:"
echo "  ssh -i C:/Users/hharp/.ssh/vps_deploy_key root@72.60.175.144"
echo ""
echo "Next steps:"
echo "  1. Add VPS_SSH_KEY to GitHub Secrets"
echo "  2. Add VPS_ENV_FILE to GitHub Secrets"
echo "  3. Trigger GitHub Actions workflow"
