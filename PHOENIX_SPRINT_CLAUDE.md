# Phoenix Eval Integration: 3-Tab Parallel Sprint

> **Instructions for Claude Code CLI:** This document contains 12 prompts split across 3 parallel workstreams. Execute each tab in a separate terminal. Wait for sync points before proceeding where noted.

---

## INITIAL SETUP (Run Once)

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Create 3 worktrees for parallel development
git worktree add ../agent-factory-tab1-infra -b phoenix/infrastructure
git worktree add ../agent-factory-tab2-evals -b phoenix/eval-pipeline  
git worktree add ../agent-factory-tab3-prod -b phoenix/production-integration
```

---

# TAB 1: INFRASTRUCTURE & GOLDEN DATASET

**Directory:** `cd ../agent-factory-tab1-infra`

---

## TAB1-PROMPT-1: Install Phoenix & Dependencies

Install Phoenix and all dependencies for the eval system. Add these to requirements.txt if not present:
- arize-phoenix[evals]
- groq
- openai  
- psycopg2-binary
- python-dotenv

Install them with pip. Then verify Phoenix works by running `phoenix serve --port 6006`. Confirm the UI is accessible at http://localhost:6006. Keep Phoenix running in background for the rest of the sprint.

---

## TAB1-PROMPT-2: Create Golden Dataset Export Script

Create `scripts/export_golden_dataset.py` that:

1. Connects to Neon PostgreSQL using DATABASE_URL from .env
2. Queries knowledge_atoms table for fault-related content using ILIKE patterns for: fault, error, alarm, troubleshoot, diagnosis, repair
3. For each atom, extracts:
   - fault_code using regex patterns (F47, E001, ALM-123, FAULT-01, ERR-42)
   - manufacturer by detecting keywords (siemens, rockwell, allen-bradley, abb, schneider)
   - equipment model patterns (S7-1200, S7-1500, CompactLogix, G120, PowerFlex)
   - root_cause by finding trigger phrases ("caused by", "due to", "results from", "indicates")
   - safety_warnings by detecting keywords (lockout, tagout, loto, ppe, arc flash, high voltage)
4. Outputs JSONL to datasets/golden_from_neon.jsonl with this structure per line:
```json
{
  "test_case_id": "atom_{id}",
  "equipment": {"manufacturer": "...", "model": "...", "subsystem": "..."},
  "input": {"fault_code": "...", "fault_description": "...", "sensor_data": {}, "context": "..."},
  "expected_output": {"root_cause": "...", "safety_critical_warnings": [], "repair_steps": [], "manual_citations": []},
  "metadata": {"atom_id": "...", "exported_at": "...", "needs_review": true, "content_length": 0}
}
```
5. Include CLI args: --output, --limit, --table, --validate
6. Print summary stats showing cases by manufacturer and top fault codes
7. Create datasets/ directory if missing

---

## TAB1-PROMPT-3: Export & Validate Dataset

Run the export script with limit 50:
```bash
python scripts/export_golden_dataset.py --limit 50
```

Then validate:
```bash
python scripts/export_golden_dataset.py --validate
```

Show me the first 3 cases formatted with `head -n 3 datasets/golden_from_neon.jsonl | python -m json.tool`. Show the summary stats. Fix any extraction issues found.

**>>> SYNC POINT: Tab 2 can start after this completes (needs golden dataset)**

---

## TAB1-PROMPT-4: Full Dataset Export

Export the complete golden dataset without limit:
```bash
python scripts/export_golden_dataset.py
```

Run validation. Target: 100+ usable cases with identified fault codes. If many cases have UNKNOWN fault codes or missing root causes, improve the regex patterns in export_golden_dataset.py and re-export.

Commit all changes:
```bash
git add -A
git commit -m "feat(phoenix): golden dataset export from Neon"
```

---

# TAB 2: EVAL PIPELINE

**Directory:** `cd ../agent-factory-tab2-evals`

**Prerequisite:** Wait for TAB1-PROMPT-3 to complete (golden dataset must exist)

---

## TAB2-PROMPT-1: Enhance Judge Templates

Read `phoenix_integration/evals/judges.py` and add:

1. New template RETRIEVAL_QUALITY_TEMPLATE that judges if retrieved knowledge atoms are relevant to the fault being diagnosed. Rails: RELEVANT, PARTIAL, IRRELEVANT. 

2. New template RESPONSE_COMPLETENESS_TEMPLATE that judges if agent response covers all required aspects (root cause identification, safety warnings, repair steps, manual citations). Rails: COMPLETE, PARTIAL, INCOMPLETE.

3. Update EVAL_CONFIG dict to include:
   - retrieval_quality: threshold 0.80, weight 0.15, blocking False
   - response_completeness: threshold 0.85, weight 0.15, blocking True

4. Add helper function `get_all_templates()` returning dict of template_name -> template_string

5. Add function `format_judge_prompt(template_name: str, case: dict, agent_output: dict) -> str` that fills a template with case and agent data

Keep all existing templates intact.

---

## TAB2-PROMPT-2: Create Quick Eval Script

Create `phoenix_integration/quick_eval.py` for rapid pipeline validation:

1. Accept args: --dataset (default ../datasets/golden_from_neon.jsonl), --cases (default 3)
2. Load N cases from the golden dataset
3. For each case:
   - Build a diagnosis prompt with equipment, fault_code, fault_description, context
   - Call Groq llama-3.1-70b-versatile with response_format={"type": "json_object"}
   - Parse response to extract: root_cause, safety_warnings, repair_steps, manual_citations
   - Call OpenAI gpt-4-turbo as judge using TECHNICAL_ACCURACY template
   - Parse judge response for CORRECT/PARTIAL/INCORRECT label
   - Print inline: case_id, fault_code, agent response preview, judge label, timing
4. Save results to quick_eval_results.json with timestamp
5. Print summary: counts per label, total time, avg time per case
6. Exit message: "PASSED - pipeline working" if 50%+ are CORRECT or PARTIAL, else "ISSUES FOUND"

Target: Complete in under 60 seconds for 3 cases.

**>>> SYNC POINT: Tab 3 can reference tracer patterns after this**

---

## TAB2-PROMPT-3: Wire Real Agent Into run_eval.py

Update `phoenix_integration/evals/run_eval.py`:

1. Replace the mock `get_agent_diagnosis()` function with real implementation:
   - First try: `from agent_factory.orchestrators.rivet_orchestrator import RivetOrchestrator` and call its diagnose method
   - Fallback: Direct Groq API call using llama-3.1-70b-versatile
   - Always use JSON response format
   - Return dict with keys: root_cause, safety_warnings, repair_steps, manual_citations

2. Add Phoenix tracing:
   - Import init_phoenix, traced, wrap_client from phoenix_tracer (add to path if needed)
   - Initialize Phoenix with launch_app=False at module load
   - Wrap the Groq and OpenAI clients
   - Add @traced(agent_name="eval_runner") decorator to get_agent_diagnosis

3. Add new CLI args:
   - --parallel: Run cases concurrently using asyncio (default False)
   - --model: Choose "groq" or "openai" for agent calls (default groq)
   - --judge-model: Choose judge model (default gpt-4-turbo)

4. Add progress indicator (tqdm if available, else simple print)

Test with:
```bash
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 5
```

---

## TAB2-PROMPT-4: Full Eval Run & Report Generator

Run evaluation on 30 cases:
```bash
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 30 --output evals/sprint_results.json
```

Then create `evals/generate_report.py` that:
1. Loads eval results from JSON file (accept --input arg)
2. Generates markdown report to evals/EVAL_REPORT.md containing:
   - Summary table: eval_name | pass_rate | threshold | status (✅/❌)
   - List of cases that failed safety_compliance (case_id, fault_code, reason)
   - List of cases with INCORRECT technical_accuracy (case_id, fault_code, reason)
   - Overall gate status: PASSED or FAILED
   - Timestamp and case count
3. Print the report to console as well

Run it:
```bash
python evals/generate_report.py --input evals/sprint_results.json
```

Commit:
```bash
git add -A
git commit -m "feat(phoenix): eval pipeline with judges and reporting"
```

---

# TAB 3: PRODUCTION INTEGRATION

**Directory:** `cd ../agent-factory-tab3-prod`

**Prerequisite:** Can start after TAB1-PROMPT-1. Benefits from TAB2-PROMPT-2 patterns.

---

## TAB3-PROMPT-1: Verify Tracer Module

Read `phoenix_integration/phoenix_tracer.py` and create a live test.

Create `phoenix_integration/test_tracer_live.py` that:
1. Imports init_phoenix, wrap_client, traced, log_route_decision, log_knowledge_retrieval
2. Initializes Phoenix with launch_app=False (assumes phoenix serve running on 6006)
3. Creates and wraps a Groq client
4. Makes one chat completion call asking about a PLC fault
5. Calls log_route_decision() with sample data (query, selected_route, confidence, all_routes dict)
6. Calls log_knowledge_retrieval() with sample data (query, list of 3 fake atoms, retrieval_time_ms)
7. Prints success message with Phoenix UI URL

Run it:
```bash
python phoenix_integration/test_tracer_live.py
```

Verify traces appear in Phoenix UI at http://localhost:6006. Fix any issues in phoenix_tracer.py if needed.

---

## TAB3-PROMPT-2: Integrate Tracer Into Orchestrator

Find or create the main orchestrator. Check these locations:
- agent_factory/orchestrators/rivet_orchestrator.py
- agent_factory/orchestrators/main.py
- agents/orchestrators/

If no orchestrator exists, create `agent_factory/orchestrators/rivet_orchestrator.py` with:

```python
class RivetOrchestrator:
    def __init__(self):
        # Initialize Groq client, wrap with Phoenix
        pass
    
    def diagnose(self, fault_code: str, equipment_type: str, manufacturer: str = None, 
                 sensor_data: dict = None, context: str = None) -> dict:
        # 1. Determine route based on manufacturer
        # 2. Log route decision to Phoenix
        # 3. Call appropriate SME prompt
        # 4. Return structured response
        pass
```

Add Phoenix integration:
1. Import from phoenix_integration.phoenix_tracer: init_phoenix, traced, wrap_client, log_route_decision, log_knowledge_retrieval
2. Call init_phoenix(project_name="rivet_production", launch_app=False) at module load
3. Wrap the Groq client with wrap_client()
4. Add @traced(agent_name="rivet_orchestrator", route="main") to diagnose method
5. Add log_route_decision() call after determining which SME to use
6. If there's a knowledge retrieval step, add log_knowledge_retrieval()

Test by importing and calling:
```python
from agent_factory.orchestrators.rivet_orchestrator import RivetOrchestrator
orch = RivetOrchestrator()
result = orch.diagnose("F47", "S7-1200", manufacturer="Siemens")
print(result)
```

---

## TAB3-PROMPT-3: Setup CI/CD Workflow

Check `phoenix_integration/.github/workflows/eval_gate.yml` exists and is correct.

1. Move it to root `.github/workflows/eval_gate.yml` if not already there

2. Verify/update the workflow:
   - Triggers on PR to paths: agents/**, orchestrators/**, evals/**, prompts/**, phoenix_integration/**
   - Uses Python 3.11
   - Installs from requirements.txt plus arize-phoenix[evals]
   - Runs: `python phoenix_integration/evals/run_eval.py --dataset datasets/golden_from_neon.jsonl --limit 50 --output evals/ci_results.json`
   - Checks thresholds and fails if not met
   - Posts results as PR comment

3. Create `evals/check_results.py` if missing:
   - Loads results JSON
   - Checks each blocking eval against its threshold
   - Prints summary
   - Exits 0 if all blocking thresholds met, 1 otherwise

4. Ensure dataset path datasets/golden_from_neon.jsonl is committed or the CI has access to Neon to generate it

---

## TAB3-PROMPT-4: Local CI Test & Final Verification

Create `.github/test_eval_gate_local.sh`:
```bash
#!/bin/bash
set -e

echo "=== LOCAL CI GATE TEST ==="

# Install deps
pip install -q arize-phoenix[evals] groq openai psycopg2-binary

# Run evals (limit 10 for speed)
echo "Running evals..."
python phoenix_integration/evals/run_eval.py \
    --dataset datasets/golden_from_neon.jsonl \
    --limit 10 \
    --output evals/local_ci_results.json

# Check thresholds
echo "Checking thresholds..."
python phoenix_integration/evals/check_results.py evals/local_ci_results.json

echo "=== LOCAL CI TEST COMPLETE ==="
```

Make it executable and run:
```bash
chmod +x .github/test_eval_gate_local.sh
./.github/test_eval_gate_local.sh
```

If it passes, commit everything:
```bash
git add -A
git commit -m "feat(phoenix): production integration with CI gate"
```

---

# FINAL MERGE

After all 3 tabs complete their prompts:

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Merge branches in order
git checkout main
git merge phoenix/infrastructure --no-ff -m "merge: phoenix infrastructure"
git merge phoenix/eval-pipeline --no-ff -m "merge: phoenix eval pipeline"
git merge phoenix/production-integration --no-ff -m "merge: phoenix production integration"

# Clean up worktrees
git worktree remove ../agent-factory-tab1-infra
git worktree remove ../agent-factory-tab2-evals
git worktree remove ../agent-factory-tab3-prod

# Clean up branches
git branch -d phoenix/infrastructure
git branch -d phoenix/eval-pipeline
git branch -d phoenix/production-integration
```

---

# VERIFICATION CHECKLIST

Run these to confirm sprint success:

```bash
# Phoenix UI accessible
curl -s http://localhost:6006 > /dev/null && echo "✅ Phoenix running"

# Golden dataset exists
test -f datasets/golden_from_neon.jsonl && echo "✅ Golden dataset exists"
wc -l datasets/golden_from_neon.jsonl

# Quick eval works
python phoenix_integration/quick_eval.py --cases 3

# Full eval passes thresholds
python phoenix_integration/evals/run_eval.py --limit 30 --output evals/final_check.json
python phoenix_integration/evals/check_results.py evals/final_check.json

# Tracer integration works
python phoenix_integration/test_tracer_live.py

# Local CI passes
./.github/test_eval_gate_local.sh
```

---

# SUCCESS METRICS

| Component | Target | Validation |
|-----------|--------|------------|
| Golden Dataset | 100+ cases | `wc -l datasets/golden_from_neon.jsonl` |
| Technical Accuracy | ≥85% | Check eval report |
| Safety Compliance | 100% | Check eval report |
| Procedure Completeness | ≥90% | Check eval report |
| Citation Accuracy | ≥95% | Check eval report |
| CI Gate | Passes locally | `.github/test_eval_gate_local.sh` exits 0 |
| Phoenix Traces | Visible in UI | Check http://localhost:6006 |

**Sprint Complete When:** All verification checks pass and `python phoenix_integration/evals/run_eval.py --limit 30` shows all blocking thresholds met.
