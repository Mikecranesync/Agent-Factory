# RIVET MVP - 3 TAB PARALLEL SPRINT

## Quick Start (1 Computer, 3 Tabs)

### Step 1: Create Branches (Run Once)
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

git checkout main
git pull origin main

# Create 3 branches
git branch rivet-backend
git branch rivet-frontend
git branch rivet-bot

git push origin --all
```

### Step 2: Open 3 Terminal Tabs

| Tab | Branch | Prompt File |
|-----|--------|-------------|
| **Tab 1** | rivet-backend | `sprint/WS1_BACKEND_PROMPT.md` |
| **Tab 2** | rivet-frontend | `sprint/WS2_FRONTEND_PROMPT.md` |
| **Tab 3** | rivet-bot | `sprint/WS3_BOT_PROMPT.md` |

### Step 3: Start Each Claude CLI Session

**Tab 1 - Backend:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout rivet-backend
claude
# Paste contents of sprint/WS1_BACKEND_PROMPT.md
```

**Tab 2 - Frontend:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout rivet-frontend
claude
# Paste contents of sprint/WS2_FRONTEND_PROMPT.md
```

**Tab 3 - Bot:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout rivet-bot
claude
# Paste contents of sprint/WS3_BOT_PROMPT.md
```

---

## What Each Tab Builds

| Tab | Focus | Deliverables |
|-----|-------|--------------|
| **1: Backend** | Atlas CMMS + FastAPI | Work order API, user provisioning, asset search |
| **2: Frontend** | Landing + Stripe | Marketing site, pricing page, checkout flow |
| **3: Bot** | Telegram AI | Voice transcription, Claude vision, clarification |

---

## Timeline

| Day | Tab 1 (Backend) | Tab 2 (Frontend) | Tab 3 (Bot) |
|-----|-----------------|------------------|-------------|
| **1** | Atlas research + client | Next.js setup + landing | Voice module + Whisper |
| **2** | Wire up APIs | Pricing + checkout | Claude vision + print Q&A |
| **3** | Database + health | Success page + deploy | Clarification + testing |

---

## Merge Strategy

After Day 3:
```bash
git checkout main
git merge rivet-backend
git merge rivet-frontend
git merge rivet-bot
git push origin main
```

---

## Environment Variables Needed

All tabs use the same `.env` file:
```bash
# Already have
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
TELEGRAM_BOT_TOKEN=xxx
NEON_DB_URL=postgresql://xxx

# Stripe (create products first)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_PRICE_BASIC=price_xxx
STRIPE_PRICE_PRO=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx
```

---

## Success Criteria (End of Day 3)

- [ ] `POST /api/work-orders` creates work order in Atlas
- [ ] Landing page live on Vercel
- [ ] Stripe checkout works (test mode)
- [ ] Voice message → transcription → work order
- [ ] Photo → Claude analysis → Q&A
- [ ] Ambiguous input → clarification prompt

---

## Monitoring Progress

Check each branch:
```bash
git log rivet-backend --oneline -5
git log rivet-frontend --oneline -5
git log rivet-bot --oneline -5
```

---

## If a Tab Gets Stuck

1. Check `/sprint/STATUS_WS{1,2,3}.md` for blockers
2. Tab can move to next task while blocked
3. Mock dependencies if another tab isn't ready

---

**LET'S SHIP IT! 🚀**
