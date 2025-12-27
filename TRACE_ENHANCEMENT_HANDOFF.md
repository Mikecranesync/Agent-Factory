# Enhanced Trace Debugging - Session Handoff

**Date:** 2025-12-27
**Status:** Step 1/6 Complete - Ready for Resumption
**Plan File:** `C:\Users\hharp\.claude\plans\lively-wiggling-kernighan.md`

---

## What Was Completed This Session

### ✅ Step 1: Enhanced RequestTrace (15 minutes)

**File Modified:** `agent_factory/core/trace_logger.py` (+140 lines)

**New Methods Added:**
- `trace.decision()` - Capture routing decisions with alternatives considered
- `trace.agent_reasoning()` - Capture agent internal thought process
- `trace.research_pipeline_status()` - Capture research pipeline execution
- `trace.langgraph_execution()` - Capture LangGraph workflow traces
- `trace.kb_retrieval()` - Capture KB atom retrieval scores

**New Getter Methods:**
- `get_decisions()` - Get all routing decisions
- `get_agent_reasoning()` - Get agent reasoning data
- `get_research_pipeline_status()` - Get pipeline status
- `get_langgraph_trace()` - Get workflow trace
- `get_kb_retrieval_info()` - Get KB retrieval details
- `get_all_timings()` - Get performance timings
- `get_errors()` - Get all errors
- `total_duration_ms` - Property for total duration

**Validation:** ✅ Code compiles successfully
```bash
poetry run python -c "from agent_factory.core.trace_logger import RequestTrace; print('[OK]')"
# Output: [OK] Enhanced RequestTrace compiles successfully
```

---

## Remaining Work (Steps 2-6)

### Step 2: Add Trace Calls to Orchestrator (10 min)

**File to Modify:** `agent_factory/core/orchestrator.py`

**Changes Required:**
```python
# In route_query() method, add trace calls:

# After vendor detection
trace.decision(
    decision_point="vendor_detection",
    outcome=vendor_type.value,
    reasoning=f"Keywords: {detected_keywords}",
    confidence=detection_confidence
)

# After KB coverage evaluation
trace.decision(
    decision_point="kb_coverage_evaluation",
    outcome=f"route_{selected_route.value[-1].lower()}",
    reasoning=f"Coverage: {kb_coverage:.2f}, Threshold A: 0.8, Threshold C: 0.3",
    alternatives={
        "route_a": "coverage >= 0.8" if kb_coverage >= 0.8 else "insufficient coverage",
        "route_b": "0.3 <= coverage < 0.8" if 0.3 <= kb_coverage < 0.8 else "out of range",
        "route_c": "coverage < 0.3" if kb_coverage < 0.3 else "coverage too high"
    },
    kb_atoms_found=len(kb_atoms),
    top_atom_scores=[(a.atom_id, s) for a, s in top_5_matches]
)

# After agent execution
trace.agent_reasoning(
    agent=agent_id.value,
    query=query,
    kb_atoms_used=[a.atom_id for a in atoms_used],
    response_length=len(response_text),
    confidence=final_confidence
)
```

**Location in Code:**
- Look for `async def route_query()` method
- Find vendor detection logic
- Find KB coverage evaluation logic
- Find agent execution logic

---

### Step 3: Add LangGraph Trace Capture (10 min)

**File to Modify:** `agent_factory/integrations/telegram/langgraph_handlers.py`

**Changes Required:**
```python
# In each workflow handler (/research, /consensus, /analyze):

workflow_trace = {
    "workflow": "research",  # or "consensus", "analyze"
    "nodes_executed": ["researcher", "analyzer", "writer"],
    "state_transitions": transitions_list,
    "retry_count": 0,
    "quality_gate_results": quality_scores,
    "total_duration_ms": duration
}

trace.langgraph_execution(workflow_trace)
```

---

### Step 4: Create VPS Log Monitor (15 min)

**File to Create:** `agent_factory/integrations/telegram/log_monitor.py`

**Implementation:**
```python
import paramiko
from typing import List, Optional
from pathlib import Path

class VPSLogMonitor:
    """Monitor VPS logs via SSH for real-time troubleshooting."""

    def __init__(self):
        self.host = "72.60.175.144"
        self.username = "root"
        self.key_file = Path.home() / ".ssh" / "vps_deploy_key"

    def tail_recent_errors(self, last_n_lines: int = 20) -> List[str]:
        """Tail last N lines of error log."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.username, key_filename=str(self.key_file))

        stdin, stdout, stderr = ssh.exec_command(
            f"tail -n {last_n_lines} /root/Agent-Factory/logs/bot-error.log"
        )
        errors = stdout.read().decode('utf-8').split('\n')
        ssh.close()
        return [e for e in errors if e.strip()]

    def search_recent_traces(self, trace_id: str) -> Optional[str]:
        """Search for specific trace ID in logs."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.username, key_filename=str(self.key_file))

        stdin, stdout, stderr = ssh.exec_command(
            f"grep '{trace_id}' /root/Agent-Factory/logs/traces.jsonl | tail -n 1"
        )
        result = stdout.read().decode('utf-8').strip()
        ssh.close()
        return result if result else None
```

**Dependency:** Add to `pyproject.toml`:
```toml
paramiko = "^3.4.0"
```

---

### Step 5: Enhanced Admin Trace Message (15 min)

**File to Modify:** `agent_factory/integrations/telegram/orchestrator_bot.py`

**Find:** `send_admin_trace()` method
**Replace with:** `send_admin_trace_enhanced()` method (see plan file for full implementation)

**Key Sections:**
1. Request Info (user, query, timestamp)
2. Routing Decision (route, confidence, decision logic)
3. KB Coverage Details (coverage %, top 5 matches)
4. Agent Reasoning (SME agent thought process)
5. Research Pipeline (if triggered, sources found)
6. LangGraph Workflow (if used, execution trace)
7. Performance Timing (breakdown per operation)
8. VPS Recent Errors (last 5 lines via SSH)
9. Errors (any errors that occurred)

---

### Step 6: Add /trace Command (5 min)

**File to Modify:** `agent_factory/integrations/telegram/orchestrator_bot.py`

**Add Command Handler:**
```python
async def cmd_trace(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle trace verbosity level."""
    args = context.args

    if not args:
        level = os.getenv("TRACE_LEVEL", "normal")
        await update.message.reply_text(f"Current trace level: {level}")
        return

    level = args[0].lower()
    if level not in ["minimal", "normal", "verbose", "debug"]:
        await update.message.reply_text("Usage: /trace [minimal|normal|verbose|debug]")
        return

    os.environ["TRACE_LEVEL"] = level
    await update.message.reply_text(f"✓ Trace level set to: {level}")
```

**Register Command:** Add to `application.add_handler()` calls

---

## Git Commit Message

```
feat(trace): Enhanced trace debugging with routing logic capture (Step 1/6)

Step 1 Complete: Enhanced RequestTrace with detailed trace capture methods

Added Methods:
- trace.decision() - Capture routing decisions with alternatives
- trace.agent_reasoning() - Capture agent thought process
- trace.research_pipeline_status() - Capture pipeline info
- trace.langgraph_execution() - Capture workflow traces
- trace.kb_retrieval() - Capture KB atom scores

Getter Methods:
- get_decisions(), get_agent_reasoning(), get_research_pipeline_status()
- get_langgraph_trace(), get_kb_retrieval_info()
- get_all_timings(), get_errors(), total_duration_ms

Files Modified:
- agent_factory/core/trace_logger.py (+140 lines)

Next Steps (on resume):
- Step 2: Add trace calls to orchestrator routing logic
- Step 3: Add LangGraph execution trace capture
- Step 4: Create VPS log monitoring via SSH
- Step 5: Enhance admin trace message format
- Step 6: Add /trace command for verbosity control

Estimated Time Remaining: 55 minutes

Plan File: C:\Users\hharp\.claude\plans\lively-wiggling-kernighan.md
```

---

## Resumption Instructions

**Command to Resume:**
```bash
# On next session, tell Claude:
"Resume trace enhancement implementation. Complete Steps 2-6 from the plan at C:\Users\hharp\.claude\plans\lively-wiggling-kernighan.md. Reference TRACE_ENHANCEMENT_HANDOFF.md for current state."
```

**Quick Validation:**
```bash
# Verify Step 1 is working
poetry run python -c "from agent_factory.core.trace_logger import RequestTrace; t = RequestTrace('text', '123'); t.decision('test', 'outcome', 'reasoning'); print('[OK] Step 1 functional')"
```

**Files to Review Before Resuming:**
1. `TRACE_ENHANCEMENT_HANDOFF.md` (this file)
2. `C:\Users\hharp\.claude\plans\lively-wiggling-kernighan.md` (complete plan)
3. `agent_factory/core/trace_logger.py` (completed Step 1)

---

## Testing Plan (After All Steps Complete)

**Test 1: Send Text Query**
```
Send to RIVET Pro bot: "Siemens G120C shows F3002 fault"
Expected: User gets answer + Admin gets enhanced trace with routing logic
```

**Test 2: Send Photo**
```
Send equipment nameplate photo
Expected: User gets OCR + answer + Admin gets enhanced trace with OCR details
```

**Test 3: Trigger Route C**
```
Send unknown equipment query: "Mitsubishi iQ-R PLC ethernet issue"
Expected: Admin trace shows research pipeline triggered with source URLs
```

**Test 4: Toggle Trace Level**
```
Send command: /trace debug
Expected: Admin traces become more verbose
```

---

## Environment Setup (if needed)

**Add paramiko to pyproject.toml:**
```bash
poetry add paramiko
```

**Verify SSH key exists:**
```bash
ls ~/.ssh/vps_deploy_key
# Should exist from GitHub Actions setup
```

---

## Success Criteria

- [ ] All 6 steps implemented
- [ ] Code compiles without errors
- [ ] Admin receives comprehensive trace message
- [ ] Trace shows routing decision logic
- [ ] Trace shows KB atom retrieval scores
- [ ] Trace shows agent reasoning (if SME agent used)
- [ ] Trace shows research pipeline (if Route C triggered)
- [ ] Trace shows VPS error logs
- [ ] /trace command works
- [ ] Git committed and pushed

---

**Session End - Ready for Context Clear**
