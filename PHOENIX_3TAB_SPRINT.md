# Phoenix Eval Integration: 3-Tab Parallel Sprint

## Setup: Create 3 Git Worktrees

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Create worktrees for parallel work
git worktree add ../agent-factory-tab1-infra -b phoenix/infrastructure
git worktree add ../agent-factory-tab2-evals -b phoenix/eval-pipeline  
git worktree add ../agent-factory-tab3-prod -b phoenix/production-integration
```

---

# TAB 1: INFRASTRUCTURE & GOLDEN DATASET

**Worktree:** `agent-factory-tab1-infra`
**Focus:** Phoenix server, Neon export, datasets

## Prompt 1.1 - Install Phoenix & Dependencies

```
Install Phoenix and all dependencies for the eval system. Add to requirements.txt:
- arize-phoenix[evals]
- groq
- openai  
- psycopg2-binary
- python-dotenv

Then install them. Verify Phoenix works by running `phoenix serve --port 6006` and confirm the UI is accessible.
```

## Prompt 1.2 - Create Golden Dataset Export Script

```
Create scripts/export_golden_dataset.py that:

1. Connects to Neon PostgreSQL using DATABASE_URL from .env
2. Queries knowledge_atoms table for fault-related content (fault, error, alarm, troubleshoot, repair keywords)
3. Extracts from each atom:
   - fault_code (regex patterns: F47, E001, ALM-123, etc)
   - manufacturer (detect Siemens, Rockwell, ABB, etc from content)
   - equipment model (S7-1200, CompactLogix, G120, etc)
   - root_cause (find "caused by", "due to" patterns)
   - safety_warnings (LOTO, PPE, voltage keywords)
4. Outputs JSONL to datasets/golden_from_neon.jsonl with structure:
   {
     "test_case_id": "atom_{id}",
     "equipment": {"manufacturer", "model", "subsystem"},
     "input": {"fault_code", "fault_description", "sensor_data", "context"},
     "expected_output": {"root_cause", "safety_critical_warnings", "repair_steps", "manual_citations"},
     "metadata": {"atom_id", "exported_at", "needs_review": true}
   }
5. Include --limit flag for testing, --validate flag to check existing dataset
6. Print summary stats (cases by manufacturer, top fault codes)

Create the datasets/ directory if it doesn't exist.
```

## Prompt 1.3 - Export & Validate Dataset

```
Run the export script with limit 50 to test:
python scripts/export_golden_dataset.py --limit 50

Then validate it:
python scripts/export_golden_dataset.py --validate

Show me the first 3 cases and the summary stats. If any issues found, fix them.
```

## Prompt 1.4 - Expand Dataset

```
Export the full golden dataset (no limit):
python scripts/export_golden_dataset.py

Review the validation results. For any cases with UNKNOWN fault codes or missing root causes, check if there's a pattern we can improve in the extraction logic. Update export_golden_dataset.py if needed.

Target: 100+ usable cases with fault codes identified.
```

---

# TAB 2: EVAL PIPELINE

**Worktree:** `agent-factory-tab2-evals`
**Focus:** Judge templates, eval runner, quick test

## Prompt 2.1 - Review & Enhance Judge Templates

```
Read phoenix_integration/evals/judges.py and enhance it:

1. Add RETRIEVAL_QUALITY_TEMPLATE - judges if retrieved knowledge atoms are relevant to the fault
2. Add RESPONSE_COMPLETENESS_TEMPLATE - judges if agent covered all aspects (cause, safety, steps, citations)
3. Update EVAL_CONFIG to include new judges with appropriate thresholds:
   - retrieval_quality: 80% threshold, non-blocking
   - response_completeness: 85% threshold, blocking
4. Add helper function get_all_templates() that returns dict of all templates
5. Add function format_judge_prompt(template_name, case, agent_output) to easily fill templates

Keep existing templates intact, just add to them.
```

## Prompt 2.2 - Create Quick Eval Script

```
Create phoenix_integration/quick_eval.py for fast pipeline validation:

1. Load 3 cases from golden dataset
2. For each case:
   - Call Groq llama-3.1-70b-versatile with a diagnosis prompt
   - Use JSON response format
   - Extract: root_cause, safety_warnings, repair_steps, manual_citations
3. Run simplified judge (OpenAI gpt-4-turbo) with TECHNICAL_ACCURACY template
4. Print results inline with timing
5. Save to quick_eval_results.json
6. Exit with summary: PASSED if 50%+ correct/partial, else show issues

Include --dataset and --cases args. Default to 3 cases.
This is for rapid iteration - should complete in <60 seconds.
```

## Prompt 2.3 - Wire Real Agent Into run_eval.py

```
Update phoenix_integration/evals/run_eval.py:

1. Replace mock get_agent_diagnosis() with real implementation:
   - Try importing from agent_factory.orchestrators.rivet_orchestrator
   - Fallback to direct Groq call if import fails
   - Use llama-3.1-70b-versatile model
   - Request JSON response with root_cause, safety_warnings, repair_steps, manual_citations

2. Add Phoenix tracing to eval runs:
   - Import from phoenix_tracer
   - Wrap the Groq/OpenAI clients
   - Add @traced decorator to get_agent_diagnosis

3. Add --parallel flag to run multiple cases concurrently (asyncio)
4. Add --model flag to switch between groq/openai for agent
5. Improve progress output with tqdm if available

Test with: python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 5
```

## Prompt 2.4 - Run Full Eval & Generate Report

```
Run full evaluation on 30 cases:
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 30 --output evals/sprint_results.json

Then create evals/generate_report.py that:
1. Loads eval results JSON
2. Generates markdown report with:
   - Overall pass rates per judge
   - Cases that failed safety (list them)
   - Cases with INCORRECT accuracy (list them)
   - Trend comparison if previous results exist
3. Outputs to evals/EVAL_REPORT.md

Run it and show me the report.
```

---

# TAB 3: PRODUCTION INTEGRATION

**Worktree:** `agent-factory-tab3-prod`
**Focus:** Tracer wiring, CI/CD, orchestrator updates

## Prompt 3.1 - Verify Tracer Module

```
Read phoenix_integration/phoenix_tracer.py and test it:

1. Create phoenix_integration/test_tracer_live.py that:
   - Starts Phoenix session (launch_app=False, assumes server running)
   - Wraps a Groq client
   - Makes one completion call
   - Logs a route decision
   - Logs a knowledge retrieval
   - Verifies traces appear (check Phoenix API or just print confirmation)

2. Run the test and confirm output

3. If any issues, fix phoenix_tracer.py
```

## Prompt 3.2 - Integrate Tracer Into Orchestrator

```
Find the main orchestrator file (likely agent_factory/orchestrators/ or similar).

Add Phoenix tracing:
1. Import init_phoenix, traced, wrap_client, log_route_decision from phoenix_integration.phoenix_tracer
2. Initialize Phoenix at module load (launch_app=False)
3. Wrap the LLM client (Groq) 
4. Add @traced decorator to main diagnosis/routing functions
5. Add log_route_decision() call when routing to SME agents
6. Add log_knowledge_retrieval() call when querying Neon

If orchestrator doesn't exist yet, create a minimal one at agent_factory/orchestrators/rivet_orchestrator.py that:
- Routes to appropriate SME based on manufacturer detection
- Calls Groq for diagnosis
- Returns structured response

Test by importing and calling it directly.
```

## Prompt 3.3 - Verify CI/CD Workflow

```
Read phoenix_integration/.github/workflows/eval_gate.yml and verify it will work:

1. Check that it triggers on the right paths (agents/**, orchestrators/**, evals/**)
2. Ensure it installs dependencies correctly
3. Verify the eval command will work with our dataset path
4. Check the result checker logic

If the workflow references files that don't exist, create them:
- evals/check_results.py if missing (threshold enforcement)
- Ensure dataset path is correct

Move the workflow to the root .github/workflows/ if needed.
```

## Prompt 3.4 - Create Test PR

```
Create a simple test to verify the CI gate works:

1. Make a trivial change to an agent file (add a comment)
2. Commit with message "test: verify phoenix eval gate"
3. Show me the git diff and commit
4. Create instructions for pushing and opening a PR

Also create a local test script .github/test_eval_gate_local.sh that simulates what CI would do:
- Install deps
- Run evals with limit 10
- Check thresholds
- Exit 0 if passed, 1 if failed

Run the local test and show results.
```

---

# SYNC POINTS

## After Tab 1 Prompt 1.3 completes:
- Tab 2 can start (needs golden dataset)

## After Tab 2 Prompt 2.2 completes:
- Tab 3 Prompt 3.2 can reference the tracer patterns

## Final Merge Order:
```bash
# After all tabs complete
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Merge in order
git merge phoenix/infrastructure
git merge phoenix/eval-pipeline
git merge phoenix/production-integration

# Clean up worktrees
git worktree remove ../agent-factory-tab1-infra
git worktree remove ../agent-factory-tab2-evals
git worktree remove ../agent-factory-tab3-prod
```

---

# QUICK REFERENCE

## Tab 1 Commands
```bash
cd ../agent-factory-tab1-infra
phoenix serve --port 6006  # Keep running
python scripts/export_golden_dataset.py --limit 50
```

## Tab 2 Commands
```bash
cd ../agent-factory-tab2-evals
python phoenix_integration/quick_eval.py
python phoenix_integration/evals/run_eval.py --limit 10
```

## Tab 3 Commands
```bash
cd ../agent-factory-tab3-prod
python phoenix_integration/test_tracer_live.py
bash .github/test_eval_gate_local.sh
```

---

# SUCCESS CRITERIA

| Tab | Deliverable | Done When |
|-----|-------------|-----------|
| Tab 1 | Golden dataset | 100+ cases exported, validated |
| Tab 2 | Eval pipeline | 30-case run completes, report generated |
| Tab 3 | Production integration | Tracer in orchestrator, CI gate passes locally |

**Sprint Complete When:** All three branches merged, `python evals/run_eval.py --limit 30` shows 85%+ accuracy, local CI test passes.
