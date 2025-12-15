# VPS Deployment Setup - Automated SSH Key Configuration
# Windows PowerShell Script
#
# This script automates:
# 1. SSH key generation (if needed)
# 2. Display keys for GitHub Secrets
# 3. Provide setup instructions
#
# Usage:
#   .\scripts\setup_vps_deployment.ps1

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "VPS Deployment Setup - Agent Factory" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Paths
$sshDir = "$env:USERPROFILE\.ssh"
$privateKeyPath = "$sshDir\vps_deploy_key"
$publicKeyPath = "$sshDir\vps_deploy_key.pub"

# Check if keys exist
$keysExist = (Test-Path $privateKeyPath) -and (Test-Path $publicKeyPath)

if ($keysExist -and -not $Force) {
    Write-Host "[OK] SSH keys already exist at:" -ForegroundColor Green
    Write-Host "     Private: $privateKeyPath"
    Write-Host "     Public:  $publicKeyPath"
    Write-Host ""
} else {
    # Generate SSH key pair
    Write-Host "[+] Generating SSH key pair..." -ForegroundColor Yellow
    Write-Host ""

    # Ensure .ssh directory exists
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir | Out-Null
    }

    # Generate key
    & ssh-keygen -t ed25519 -C "github-actions@agent-factory" -f $privateKeyPath -N '""'

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] SSH key pair generated successfully!" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Failed to generate SSH key pair" -ForegroundColor Red
        exit 1
    }
}

# Read keys
$privateKey = Get-Content $privateKeyPath -Raw
$publicKey = Get-Content $publicKeyPath -Raw

# Display keys
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "SSH Keys - Copy for GitHub Secrets and VPS Setup" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "PUBLIC KEY (for VPS authorized_keys):" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow
Write-Host $publicKey
Write-Host ""

Write-Host "PRIVATE KEY (for GitHub Secret: VPS_SSH_KEY):" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
Write-Host $privateKey
Write-Host ""

# Next steps
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "STEP 1: Add Public Key to VPS" -ForegroundColor Green
Write-Host "------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "Option A: Copy public key to VPS (automatic)"
Write-Host "  ssh-copy-id -i $publicKeyPath root@72.60.175.144"
Write-Host ""
Write-Host "Option B: Manual SSH (if ssh-copy-id not available)"
Write-Host "  ssh root@72.60.175.144"
Write-Host "  echo `"$($publicKey.Trim())`" >> ~/.ssh/authorized_keys"
Write-Host "  chmod 600 ~/.ssh/authorized_keys"
Write-Host "  exit"
Write-Host ""
Write-Host "Option C: Use setup script on VPS"
Write-Host "  ssh root@72.60.175.144"
Write-Host "  curl -sSL https://raw.githubusercontent.com/Mikecranesync/Agent-Factory/main/scripts/setup_vps_ssh_key.sh | bash -s -- `"$($publicKey.Trim())`""
Write-Host ""

Write-Host "STEP 2: Test SSH Key Authentication" -ForegroundColor Green
Write-Host "------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "  ssh -i $privateKeyPath root@72.60.175.144"
Write-Host ""
Write-Host "  Should connect without password prompt!"
Write-Host ""

Write-Host "STEP 3: Add GitHub Secrets" -ForegroundColor Green
Write-Host "--------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "  URL: https://github.com/Mikecranesync/Agent-Factory/settings/secrets/actions"
Write-Host ""
Write-Host "  Secret 1: VPS_SSH_KEY"
Write-Host "    Value: (PRIVATE KEY above - copy entire block including BEGIN/END lines)"
Write-Host ""
Write-Host "  Secret 2: VPS_ENV_FILE"
Write-Host "    Value: (contents of .env.vps file)"
Write-Host ""
Write-Host "  Secret 3: TELEGRAM_BOT_TOKEN"
Write-Host "    Value: 8264955123:AAHLiOZmJXrOepJ82XGs_pcGwk6BIfEgGAs"
Write-Host ""
Write-Host "  Secret 4: TELEGRAM_ADMIN_CHAT_ID"
Write-Host "    Value: 8445149012"
Write-Host ""

Write-Host "STEP 4: Configure Claude Code CLI Remote Connection" -ForegroundColor Green
Write-Host "-----------------------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "  In Claude Code CLI app:"
Write-Host "    Host: 72.60.175.144"
Write-Host "    User: root"
Write-Host "    Authentication: SSH Key"
Write-Host "    Identity File: $privateKeyPath"
Write-Host ""
Write-Host "  See: docs/CLAUDE_CODE_CLI_VPS_SETUP.md for detailed guide"
Write-Host ""

Write-Host "STEP 5: Test GitHub Actions Workflow" -ForegroundColor Green
Write-Host "-------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "  URL: https://github.com/Mikecranesync/Agent-Factory/actions"
Write-Host ""
Write-Host "  Click: 'Deploy RIVET Pro to VPS' -> 'Run workflow'"
Write-Host ""

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "For detailed instructions, see:" -ForegroundColor Gray
Write-Host "  - docs/CLAUDE_CODE_CLI_VPS_SETUP.md" -ForegroundColor Gray
Write-Host "  - GITHUB_SECRETS_SETUP.md" -ForegroundColor Gray
Write-Host ""
