# .claude/hooks/windows/sync_context.ps1
# Sync Agent Factory context to Windows registry for cross-app access
# Version: 1.0.0

Write-Host "🔄 Syncing Agent Factory context to Windows registry..." -ForegroundColor Cyan

# Read current session context
$sessionFile = ".claude/history/last_session.json"

if (Test-Path $sessionFile) {
    try {
        $context = Get-Content $sessionFile -Raw | ConvertFrom-Json

        # Registry path for Agent Factory context
        $regPath = "HKCU:\Software\AgentFactory\Context"

        # Create registry key if it doesn't exist
        if (!(Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
            Write-Host "   Created registry key: $regPath" -ForegroundColor Gray
        }

        # Store context values
        Set-ItemProperty -Path $regPath -Name "SessionID" -Value $context.session_id
        Set-ItemProperty -Path $regPath -Name "Timestamp" -Value $context.timestamp
        Set-ItemProperty -Path $regPath -Name "GitBranch" -Value $context.git_branch
        Set-ItemProperty -Path $regPath -Name "GitCommit" -Value $context.git_commit
        Set-ItemProperty -Path $regPath -Name "ActiveSkill" -Value ($context.context.active_skill ?? "none")
        Set-ItemProperty -Path $regPath -Name "ProductFocus" -Value $context.context.product_focus
        Set-ItemProperty -Path $regPath -Name "LastSync" -Value (Get-Date -Format "o")

        Write-Host "✅ Context synced to registry!" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Session ID:    $($context.session_id)" -ForegroundColor Gray
        Write-Host "   Branch:        $($context.git_branch)" -ForegroundColor Gray
        Write-Host "   Active Skill:  $($context.context.active_skill ?? 'none')" -ForegroundColor Gray
        Write-Host "   Product Focus: $($context.context.product_focus)" -ForegroundColor Gray

    } catch {
        Write-Host "❌ Failed to sync context: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  No session file found at: $sessionFile" -ForegroundColor Yellow
    Write-Host "   Skipping registry sync." -ForegroundColor Gray
}
