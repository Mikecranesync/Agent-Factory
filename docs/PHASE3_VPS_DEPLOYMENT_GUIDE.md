# Phase 3 SME Agents - VPS Deployment Guide

**Date:** 2025-12-23
**Target:** Hostinger VPS (72.60.175.144)
**Service:** orchestrator-bot.service (systemd)

---

## Pre-Deployment Checklist

### ✅ Code Status:
- [x] All 4 SME agents implemented
- [x] Schema updates complete
- [x] KB evaluator updated
- [x] Orchestrator integrated
- [x] Compilation validated locally

### ⏳ Ready to Deploy:
- [ ] Git commit created
- [ ] Changes pushed to GitHub
- [ ] VPS service restarted
- [ ] Test queries executed
- [ ] Response quality verified

---

## Step 1: Commit and Push Changes

### Option A: From Windows (Current Directory)

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Stage all changes
git add agent_factory/rivet_pro/agents/generic_agent.py
git add agent_factory/rivet_pro/agents/siemens_agent.py
git add agent_factory/rivet_pro/agents/rockwell_agent.py
git add agent_factory/rivet_pro/agents/safety_agent.py
git add agent_factory/rivet_pro/agents/__init__.py
git add agent_factory/schemas/routing.py
git add agent_factory/routers/kb_evaluator.py
git add agent_factory/core/orchestrator.py
git add agent_factory/rivet_pro/agents/mock_agents.py
git add docs/PHASE3_SME_AGENTS_IMPLEMENTATION.md
git add docs/PHASE3_VPS_DEPLOYMENT_GUIDE.md

# Create commit
git commit -m "$(cat <<'EOF'
feat(rivet-pro): Phase 3 SME Agents - PRODUCTION

Implemented real SME agents to replace mock placeholders.

## Changes Made:

**New Agents (4 files):**
- GenericAgent: Cross-vendor industrial automation (270 lines)
- SiemensAgent: Siemens equipment specialist (120 lines)
- RockwellAgent: Allen-Bradley specialist (125 lines)
- SafetyAgent: Safety systems specialist (140 lines)

**Schema Updates:**
- KBCoverage: Added retrieved_docs field
- kb_evaluator: Returns KB atoms with coverage

**Orchestrator Integration:**
- Loads real agents (replaced mocks)
- Passes kb_coverage to agents
- Agents use KB atoms + LLM for responses

**Impact:**
- Bot now generates real answers instead of "[MOCK]" placeholders
- KB atoms (5-8 per query) used as LLM context
- Proper citations with source documents
- Vendor-specific terminology and expertise

**Root Cause Fixed:**
Diagnostic session (2025-12-23 AM) identified that KB search was
working (finding atoms) but agents weren't using them. Now agents
receive KB atoms and generate informed responses.

**Testing:**
- All files compile successfully
- Ready for VPS deployment
- Expected cost: ~$0.0001 per query (gpt-4o-mini)

**Files Created:** 6
**Files Modified:** 4
**Lines of Code:** ~800

See: docs/PHASE3_SME_AGENTS_IMPLEMENTATION.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Push to GitHub
git push origin main
```

### Option B: Manual Steps

1. Review changes: `git status`
2. Stage changes: `git add <files>`
3. Commit with message above
4. Push: `git push origin main`

---

## Step 2: Deploy to VPS

### SSH into VPS:

```bash
ssh root@72.60.175.144
```

### Navigate to repo:

```bash
cd /root/Agent-Factory
```

### Pull latest changes:

```bash
git pull origin main
```

**Expected output:**
```
remote: Enumerating objects...
remote: Counting objects...
Updating c504b5c..NEW_COMMIT_HASH
Fast-forward
 agent_factory/core/orchestrator.py                    |  12 +-
 agent_factory/rivet_pro/agents/__init__.py            |  15 ++
 agent_factory/rivet_pro/agents/generic_agent.py       | 270 ++++++++++++++++
 agent_factory/rivet_pro/agents/rockwell_agent.py      | 125 ++++++++
 agent_factory/rivet_pro/agents/safety_agent.py        | 140 +++++++++
 agent_factory/rivet_pro/agents/siemens_agent.py       | 120 +++++++
 agent_factory/routers/kb_evaluator.py                 |   9 +-
 agent_factory/schemas/routing.py                      |   6 +-
 docs/PHASE3_SME_AGENTS_IMPLEMENTATION.md              | 475 +++++++++++++++++++++++++++++
 docs/PHASE3_VPS_DEPLOYMENT_GUIDE.md                   | XXX ++++++++++++++++++++
 10 files changed, XXXX insertions(+), XX deletions(-)
```

### Verify files exist:

```bash
ls -la agent_factory/rivet_pro/agents/
```

**Expected:**
```
-rw-r--r-- 1 root root   XXX generic_agent.py
-rw-r--r-- 1 root root   XXX siemens_agent.py
-rw-r--r-- 1 root root   XXX rockwell_agent.py
-rw-r--r-- 1 root root   XXX safety_agent.py
-rw-r--r-- 1 root root   XXX mock_agents.py
-rw-r--r-- 1 root root   XXX __init__.py
```

### Restart bot service:

```bash
systemctl restart orchestrator-bot.service
```

### Verify service started:

```bash
systemctl status orchestrator-bot.service
```

**Expected output:**
```
● orchestrator-bot.service - RIVET Pro Telegram Orchestrator Bot
     Loaded: loaded (/etc/systemd/system/orchestrator-bot.service; enabled)
     Active: active (running) since [TIMESTAMP]
   Main PID: XXXXX (python3)
      Tasks: X
     Memory: XXX.XM
        CPU: X.XXXs
     CGroup: /system.slice/orchestrator-bot.service
             └─XXXXX python3 telegram_bot.py

[TIMESTAMP] orchestrator-bot.service: Started RIVET Pro Telegram Orchestrator Bot
```

### Monitor logs in real-time:

```bash
journalctl -u orchestrator-bot.service -f
```

**Expected startup logs:**
```
INFO: Supabase provider initialized
INFO: Neon provider initialized
INFO: DatabaseManager initialized: primary=neon, failover=enabled
INFO: Database initialized with 1964 knowledge atoms
INFO: Orchestrator initialized successfully with RAG layer
INFO: Bot polling started
```

**Look for:** No import errors, no crashes, "Bot polling started" message

---

## Step 3: Test Queries via Telegram

### Test 1: Generic Query (Route B - Thin KB)

**Send to bot:** `Diagnose VFD overheating`

**Expected logs:**
```
INFO: Query: Diagnose VFD overheating
INFO: Retrieved 5 documents
INFO: KB REAL: atoms=5, rel=0.80, conf=0.61, level=THIN
INFO: ROUTING: route=B, KB_atoms=5, confidence=0.61
INFO: GenericAgent generating response with 5 KB atoms
INFO: LLM call: gpt-4o-mini (300 tokens)
INFO: Response sent (200 OK)
```

**Expected response:**
```
VFD overheating is typically caused by:

**Common Causes:**
1. Excessive ambient temperature (>40°C)
2. Insufficient cooling airflow
3. Drive overload (motor drawing too much current)
4. High switching frequency

**Diagnostic Steps:**
1. Check drive display for fault codes
2. Measure heatsink temperature
3. Verify cooling fan operation
4. Check motor current vs drive rating

**Immediate Actions:**
- Reduce load or switching frequency
- Clean air filters
- Check for proper grounding

**Safety Warning:** Allow drive to cool before servicing...

[Source 1] [Source 2] [Source 3]

Route: B_sme_enrich | Confidence: 87%
KB Atoms: 5
```

**If you see `[MOCK]` instead:** Deployment failed, check error logs

---

### Test 2: Siemens-Specific Query (Route A or B)

**Send to bot:** `What does F0001 mean on SINAMICS G120?`

**Expected logs:**
```
INFO: Query: What does F0001 mean on SINAMICS G120?
INFO: Vendor detected: Siemens (confidence: 0.95, keywords: ['sinamics', 'g120'])
INFO: Retrieved 8 documents
INFO: KB REAL: atoms=8, rel=0.85, conf=0.78, level=STRONG
INFO: ROUTING: route=A, KB_atoms=8, confidence=0.78
INFO: SiemensAgent generating response with 8 KB atoms
INFO: LLM call: gpt-4o-mini (350 tokens)
INFO: Response sent (200 OK)
```

**Expected response:**
```
F0001 on SINAMICS G120 indicates **Overcurrent** fault.

**Meaning:** The drive detected current above the permissible limit...

**Common Causes:**
- Short circuit in motor cables or motor
- Drive output stage fault
- Motor overload
- Incorrect drive parameters (motor data)

**Diagnostic Steps:**
1. Check Parameter r0949 (fault value) for actual current
2. Verify motor cable insulation resistance
3. Check Parameter P0307 (rated motor current) matches motor nameplate
4. Review Parameter P1082 (maximum current) setting

**Resolution:**
1. Acknowledge fault: Set P0952 = 0 or cycle power
2. Check motor and cables for short circuit
3. Verify motor parameters in P0304-P0311
4. If persists, contact Siemens support

[Source 1] [Source 2]

Route: A_direct_sme | Confidence: 92%
```

---

### Test 3: Rockwell-Specific Query

**Send to bot:** `How to configure PowerFlex 525 parameter 58?`

**Expected:** RockwellAgent response with Allen-Bradley terminology

---

### Test 4: Safety Query

**Send to bot:** `How do I bypass a safety light curtain?`

**Expected:** SafetyAgent response with **CRITICAL WARNING** and refusal to provide bypass instructions

---

## Step 4: Verify Response Quality

### Check logs for:
- ✅ Correct agent selection (SiemensAgent for Siemens queries, etc.)
- ✅ KB atom count matches logs (e.g., "5 KB atoms" in response = 5 atoms retrieved)
- ✅ LLM model used (should be gpt-4o-mini for most, gpt-4o for SafetyAgent)
- ✅ No errors or exceptions
- ✅ Response time <5 seconds

### Check responses for:
- ✅ No `[MOCK]` prefix
- ✅ Real technical content
- ✅ Proper citations `[Source 1]`
- ✅ Vendor-specific terminology (e.g., "FB" for Siemens, "AOI" for Rockwell)
- ✅ Safety warnings when applicable

---

## Step 5: Monitor Performance

### Track in logs:

```bash
# Count queries processed
journalctl -u orchestrator-bot.service --since "1 hour ago" | grep "Query:" | wc -l

# Count successful responses
journalctl -u orchestrator-bot.service --since "1 hour ago" | grep "Response sent (200 OK)" | wc -l

# Check for errors
journalctl -u orchestrator-bot.service --since "1 hour ago" | grep ERROR
```

### Monitor LLM costs:

**Expected costs:**
- GenericAgent: ~$0.0001 per query
- SiemensAgent: ~$0.00012 per query
- RockwellAgent: ~$0.00012 per query
- SafetyAgent: ~$0.0015 per query (premium model)

**100 queries per day:** ~$0.01-0.02/day = **$0.30-0.60/month**

---

## Troubleshooting

### Issue: `[MOCK]` responses still appearing

**Cause:** Code not deployed or service not restarted

**Fix:**
```bash
cd /root/Agent-Factory
git pull origin main
systemctl restart orchestrator-bot.service
journalctl -u orchestrator-bot.service -f  # Watch for import errors
```

---

### Issue: Import errors for new agents

**Error:** `ModuleNotFoundError: No module named 'agent_factory.rivet_pro.agents.generic_agent'`

**Cause:** Agent files not synced or Python cache

**Fix:**
```bash
# Clear Python cache
find /root/Agent-Factory -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Verify files exist
ls -la /root/Agent-Factory/agent_factory/rivet_pro/agents/*.py

# Restart service
systemctl restart orchestrator-bot.service
```

---

### Issue: Bot crashes on startup

**Cause:** Syntax errors or missing dependencies

**Fix:**
```bash
# Check full error log
journalctl -u orchestrator-bot.service -n 100

# Test imports manually
cd /root/Agent-Factory
python3 -c "from agent_factory.rivet_pro.agents.generic_agent import GenericAgent; print('OK')"

# If missing dependency:
poetry install --no-dev
systemctl restart orchestrator-bot.service
```

---

### Issue: LLM generation fails

**Error:** `OpenAI API error` or `Rate limit exceeded`

**Causes:**
1. Missing/invalid OPENAI_API_KEY in VPS .env
2. Rate limit hit (unlikely with gpt-4o-mini)
3. OpenAI service outage

**Fix:**
```bash
# Check environment variable
grep OPENAI_API_KEY /root/Agent-Factory/.env

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# If key missing, add to .env and restart
systemctl restart orchestrator-bot.service
```

---

### Issue: KB atoms not found

**Error:** `KB REAL: atoms=0, rel=0.00, conf=0.00, level=NONE`

**Cause:** Database connection issue or empty knowledge_atoms table

**Fix:**
```bash
# Check database connection
cd /root/Agent-Factory
python3 -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.health_check_all())"

# Count atoms in database
python3 -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); result = db._execute_one('SELECT COUNT(*) FROM knowledge_atoms'); print(f'Atoms: {result}')"

# If 0 atoms, re-run upload script (from local machine)
```

---

## Success Criteria

### ✅ Deployment Successful:
- [ ] Git pull completed without conflicts
- [ ] Service restarted without errors
- [ ] Bot responds to Telegram messages
- [ ] No `[MOCK]` responses
- [ ] Real technical content generated
- [ ] Proper citations included
- [ ] Vendor-specific terminology used
- [ ] Response time <5 seconds
- [ ] No crashes or exceptions in logs

### ✅ Quality Validation:
- [ ] Generic queries use GenericAgent
- [ ] Siemens queries use SiemensAgent
- [ ] Rockwell queries use RockwellAgent
- [ ] Safety queries use SafetyAgent
- [ ] Responses cite KB sources
- [ ] No hallucinations (content matches KB)
- [ ] Safety warnings present when needed

---

## Rollback Plan (If Issues)

### If deployment fails:

```bash
# Revert to previous commit
cd /root/Agent-Factory
git log --oneline -5  # Find previous commit hash
git reset --hard PREVIOUS_COMMIT_HASH

# Restart service
systemctl restart orchestrator-bot.service

# Verify mock agents working again
# Send test message - should see [MOCK] responses
```

### If partial success (some agents work, others fail):

- Keep deployment active
- Monitor error logs
- Report specific agent failures
- Can hot-patch individual agent files via SSH

---

## Post-Deployment

### After successful deployment:

1. **Document actual responses** - Save real bot responses for analysis
2. **Measure costs** - Track LLM API costs for 24 hours
3. **Monitor latency** - Record average response times
4. **Collect feedback** - Ask user if responses are helpful
5. **Tune parameters** - Adjust temperature, max_tokens if needed

### Update diagnostic docs:

```markdown
## Post-Phase 3 Status (2025-12-23)

✅ RESOLVED: Mock agents replaced with real SME agents
✅ RESOLVED: KB atoms now used for LLM generation
✅ RESOLVED: Proper citations included in responses

**New Flow:**
Query → KB Search (5 atoms) → Route B → GenericAgent → LLM generation → Real answer

**Sample Response:** [paste actual bot response]
**Cost:** $0.XX per query
**Latency:** X.XX seconds average
```

---

## Contact

**If deployment fails:**
- Check logs: `journalctl -u orchestrator-bot.service -n 100`
- Report errors with full traceback
- Include test query used

**If responses are poor quality:**
- Save exact bot response
- Note which KB atoms were retrieved
- Suggest improvements to prompts

---

*Deployment guide created: 2025-12-23*
*Target deployment: Immediate (VPS ready)*
*Estimated deployment time: 10 minutes*
*Rollback time: 2 minutes*
