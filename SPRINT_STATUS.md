# SPRINT_STATUS.md

## Sprint: RIVET Live Testing Infrastructure
**Started:** 2026-01-09
**Target:** All agents complete within 4 hours

## Agent Status

| Agent | Branch | Focus | Status | Completion File |
|-------|--------|-------|--------|-----------------|
| 1 | feature/live-testing-workflows | n8n Workflows | ✅ COMPLETE | AGENT1_COMPLETE.md |
| 2 | feature/mcp-test-integration | MCP Config | 🟢 Ready to Start | AGENT2_COMPLETE.md |
| 3 | feature/debug-harness | Debug Tools | ⚪ Waiting | AGENT3_COMPLETE.md |

## Dependencies
```
Agent 1 (Workflows)
    ↓
Agent 2 (MCP Config) ← needs workflow URLs
    ↓
Agent 3 (Debug Harness) ← needs MCP working
```

## Shared Resources

- **n8n Cloud URL:** https://mikecranesync.app.n8n.cloud
- **n8n API Key:** Get from n8n Cloud → Settings → API (needed for deployment)
- **Webhook Base URL:** https://mikecranesync.app.n8n.cloud/webhook/
- **Neon Connection:** See .env.production in repo
- **Telegram Bot:** @rivet_local_dev_bot
- **Telegram Credential ID:** if4EOJbvMirfWqCC

## Agent 1 Deliverables (✅ Complete)

**Test Workflows Created:**
- Echo Webhook (rivet-test-echo) - Validates n8n connectivity
- Database Health (rivet-test-db-health) - Tests Postgres connection
- Telegram Bot (rivet-test-telegram) - Validates bot credentials

**Documentation:**
- docs/TESTING_WORKFLOWS.md - Complete API documentation
- docs/DEPLOYMENT_GUIDE.md - Deployment instructions (manual + automated)
- scripts/import_test_workflows.py - Automated import script

**Status:** Workflows ready for deployment
**Branch:** feature/live-testing-workflows
**Commits:** 2 commits (workflows + deployment guide)

## Infrastructure Constants

| Resource | Value |
|----------|-------|
| VPS IP | 72.60.175.144 |
| n8n Port | 5678 |
| Production Workflow | 7LMKcMmldZsu1l6g |
| Webhook Path | rivet-photo-bot-v2 |

## Merge Order

1. Agent 1 → main (workflows first)
2. Agent 3 → main (fixtures needed)
3. Agent 2 → main (final integration)

## Notes

- Priority: n8n workflows FIRST (they persist)
- All logic must be codified before integration
- Test independently before merging
- Worktrees created: rivet-agent1-workflows, rivet-agent2-mcp, rivet-agent3-harness
