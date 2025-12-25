# Telegram Integration Test - Research Pipeline

## Test Bot: @RivetCeo_bot

Bot Status: ✅ Active (running on VPS 72.60.175.144)

---

## Test Scenario 1: Siemens G120C Fault (Route C → Research → Atoms)

**Goal**: Verify Route C triggers research pipeline and creates searchable atoms

### Steps:

1. **Send query to bot:**
   ```
   Siemens G120C F0003 overvoltage fault
   ```

2. **Expected Response (Route C - No KB Coverage):**
   ```
   [LLM-generated answer about F0003 overvoltage fault]

   ⚠️ Limited knowledge base coverage

   🔍 Research triggered:
   - Equipment: G120C (Siemens VFD)
   - Symptom: F0003 overvoltage fault
   - Priority: HIGH
   - Sources queued: 3-8
   - Estimated: 3-5 minutes
   ```

3. **What Happens in Background:**
   - Forum scraper finds Stack Overflow + Reddit posts
   - Research pipeline queues unique sources
   - 7-stage ingestion chain processes each source
   - New atoms created in knowledge_atoms table

4. **Wait 5-10 minutes**, then send **same query again**:
   ```
   Siemens G120C F0003 overvoltage fault
   ```

5. **Expected Response (Route A/B - KB Coverage Improved):**
   ```
   [KB-sourced answer with higher confidence]

   ✅ Knowledge base coverage: STRONG

   Sources:
   - [Stack Overflow post about G120C F0003]
   - [Siemens forum troubleshooting guide]

   Confidence: 0.85-0.95
   ```

---

## Test Scenario 2: Allen-Bradley ControlLogix (Different Vendor)

**Goal**: Verify research works for multiple vendors

### Query:
```
Allen-Bradley ControlLogix 1756-L83E communication fault
```

**Expected**: Route C → Research → New atoms for ControlLogix

---

## Test Scenario 3: Generic PLC Question (No Specific Model)

**Goal**: Verify graceful handling when model detection fails

### Query:
```
How to troubleshoot PLC communication errors
```

**Expected**: Route D (Clarification) or Route C with generic search

---

## Success Indicators

### ✅ Research Pipeline Working:
- Route C response includes "🔍 Research triggered"
- Response shows sources queued (count > 0)
- Estimated completion time shown

### ✅ Ingestion Working:
- After 5-10 min, same query returns Route A/B (not Route C)
- Higher confidence score (>0.8)
- KB-sourced answer with citations

### ✅ Atoms Searchable:
- Database query shows new atoms:
  ```sql
  SELECT COUNT(*) FROM knowledge_atoms WHERE keywords @> ARRAY['G120C']
  ```
- Semantic search returns relevant atoms
- Atoms have quality_score ≥ 60

---

## Monitoring Commands (VPS)

### Check bot logs (real-time):
```bash
ssh vps "journalctl -u orchestrator-bot -f"
```

### Check recent ingestion activity:
```bash
ssh vps "journalctl -u orchestrator-bot --since '5 minutes ago' | grep ingestion"
```

### Check database for new atoms:
```bash
ssh vps "cd /root/Agent-Factory && poetry run python -c \"
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
result = db.execute_query('SELECT COUNT(*) FROM knowledge_atoms WHERE created_at > NOW() - INTERVAL \\'10 minutes\\'')
print(f'New atoms (last 10 min): {result[0][0]}')
\""
```

---

## Troubleshooting

### Issue: Bot doesn't respond
**Check**: `ssh vps "systemctl status orchestrator-bot"`
**Fix**: `ssh vps "systemctl restart orchestrator-bot"`

### Issue: Route C but no "Research triggered" message
**Check**: Gap detector integration in orchestrator.py
**Fix**: Verify `_log_and_trigger_research()` is called

### Issue: Sources queued but no atoms created
**Check**: Ingestion chain logs for errors
**Fix**: Verify OpenAI API key, database connection

### Issue: Same query still returns Route C after 10 minutes
**Check**: Database for new atoms with model number keywords
**Fix**: Check ingestion_logs table for failure reasons

---

## Phase 2 Features (Not Yet Implemented)

- [ ] Telegram notification when ingestion completes
- [ ] Product family expansion approval (inline keyboard)
- [ ] Progress updates during ingestion
- [ ] "Ask again" reminder after 5 minutes

---

## Current Limitations

1. **No user notification**: User must manually re-ask after 5-10 min
2. **No progress tracking**: No way to see ingestion status
3. **Fire-and-forget**: Once queued, no feedback to user
4. **No product family expansion**: Only immediate query is researched

**These will be addressed in Week 2 (Tier 2 implementation)**
