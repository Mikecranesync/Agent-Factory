# SPRINT_STATUS.md

## Sprint: RIVET Live Testing Infrastructure
**Started:** 2026-01-09
**Target:** All agents complete within 4 hours

## Agent Status

| Agent | Branch | Focus | Status | Completion File |
|-------|--------|-------|--------|-----------------|
| 1 | feature/live-testing-workflows | n8n Workflows | 🟡 In Progress | AGENT1_COMPLETE.md |
| 2 | feature/mcp-test-integration | MCP Config | ⚪ Waiting | AGENT2_COMPLETE.md |
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

- **n8n Cloud URL:** [PENDING - Agent 1 to provide]
- **n8n API Key:** [PENDING - Agent 1 to provide]
- **Neon Connection:** See .env in repo
- **Telegram Bot:** @rivet_local_dev_bot
- **Telegram Credential ID:** if4EOJbvMirfWqCC

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
