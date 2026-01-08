# RIVET Test Repo - Claude CLI Protection Rules

## IDENTITY
This is the RIVET Pro test repository for n8n workflow development.

## CRITICAL RULES

### NEVER DO
- Modify files in n8n/workflows/production/ - these are READ-ONLY backups
- Use HTTP Request node when a native n8n node exists
- Hardcode API keys in workflow JSON files
- Deploy directly to production workflow ID 7LMKcMmldZsu1l6g

### ALWAYS DO
- Use NATIVE n8n nodes (Telegram, Stripe, Postgres, Anthropic, etc.)
- Reference credentials by ID only, never embed secrets
- Test workflows in n8n UI before marking complete
- Put new workflows in n8n/workflows/test/ directory
- Validate workflow JSON structure before committing
- Commit after each phase completion

## INFRASTRUCTURE CONSTANTS

| Resource | Value |
|----------|-------|
| VPS IP | 72.60.175.144 |
| n8n Port | 5678 |
| Production Workflow | 7LMKcMmldZsu1l6g |
| Webhook Path | rivet-photo-bot-v2 |
| Telegram Bot | @rivet_local_dev_bot |
| Telegram Credential ID | if4EOJbvMirfWqCC |

## CREDENTIAL PATTERNS

Telegram - EXISTING:
  id: if4EOJbvMirfWqCC
  name: Telegram Bot

PostgreSQL - CREATE NEW in n8n UI:
  name: Neon RIVET

Stripe - CREATE NEW in n8n UI:
  name: Stripe RIVET

Anthropic - CREATE NEW in n8n UI:
  name: Anthropic Claude

## NATIVE NODE REQUIREMENTS

| Function | Use This Node |
|----------|---------------|
| Telegram messages | n8n-nodes-base.telegram |
| Database queries | n8n-nodes-base.postgres |
| Stripe payments | n8n-nodes-base.stripe |
| Claude API | n8n-nodes-langchain.lmChatAnthropic |
| Conditionals | n8n-nodes-base.if or n8n-nodes-base.switch |

## WORKFLOW NAMING
- Test: TEST - RIVET - [Feature Name]
- Production: RIVET Pro - [Feature Name]
