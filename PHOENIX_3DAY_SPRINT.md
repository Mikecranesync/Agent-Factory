# Phoenix Eval Integration: 3-Day Sprint Plan

**Goal:** Get Phoenix evals running against your Agent Factory golden dataset with CI/CD gate blocking bad commits.

**Revenue Impact:** Provable accuracy stats ("92% accurate on 500 real fault cases") = customer confidence = faster sales cycles.

---

## Current State Assessment

### ✅ Already Built (in `phoenix_integration/`)
| Component | Status | Notes |
|-----------|--------|-------|
| `phoenix_tracer.py` | Ready | @traced decorator, client wrapping, custom logging |
| `test_phoenix_integration.py` | Ready | Validation script |
| `evals/judges.py` | Ready | 4 LLM-as-judge templates (accuracy, safety, procedure, citations) |
| `evals/run_eval.py` | Scaffolded | Needs real agent integration |
| `.github/workflows/eval_gate.yml` | Ready | CI/CD blocking workflow |

### ❌ Missing (Build This Sprint)
| Component | Blocker | Priority |
|-----------|---------|----------|
| Golden dataset from Neon | No `export_golden_dataset.py` | P0 |
| Real agent integration in `run_eval.py` | Mock function placeholder | P0 |
| Phoenix server running | Not installed/started | P0 |
| Datasets directory structure | Doesn't exist | P1 |
| Production tracer integration | Not wired to orchestrators | P2 |

---

## Day 1: Foundation & Golden Dataset

### Morning (2-3 hours)

#### 1.1 Install & Verify Phoenix
```bash
# In Agent Factory root
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Create/activate venv if needed
python -m venv .venv
.\.venv\Scripts\activate

# Install Phoenix
pip install arize-phoenix[evals] groq openai psycopg2-binary python-dotenv

# Start Phoenix server
phoenix serve --port 6006
# Keep this terminal open - Phoenix UI at http://localhost:6006
```

#### 1.2 Verify Tracer Works
```bash
# In new terminal
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory\phoenix_integration"
python test_phoenix_integration.py
```

**Success Criteria:** See traces in Phoenix UI at http://localhost:6006

---

### Afternoon (3-4 hours)

#### 1.3 Run Golden Dataset Export

```bash
# Create datasets directory
mkdir -p datasets

# Export first 50 for testing
python scripts/export_golden_dataset.py --output datasets/golden_from_neon.jsonl --limit 50

# Quick review
head -n 5 datasets/golden_from_neon.jsonl | python -m json.tool
```

---

### Day 1 End-of-Day Checklist
- [ ] Phoenix server running at http://localhost:6006
- [ ] Test traces visible in UI
- [ ] `datasets/golden_from_neon.jsonl` exists with 50+ cases
- [ ] Reviewed 5-10 cases to verify data quality

---

## Day 2: Agent Integration & First Evals

### Morning (2-3 hours)

#### 2.1 Wire Real Agent Into Eval Runner

Update `phoenix_integration/evals/run_eval.py` - replace the mock `get_agent_diagnosis()` with your real orchestrator call.

#### 2.2 Run Quick Test

```bash
cd phoenix_integration
python quick_eval.py
```

---

### Afternoon (3-4 hours)

#### 2.3 Run Full Eval on 10 Cases

```bash
cd phoenix_integration

# Dry run first
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 10 --dry-run

# If that looks good, run real evals
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 10 --output evals/first_run_results.json
```

#### 2.4 Review Results & Calibrate

```bash
# View summary
cat evals/first_run_results.json | python -m json.tool | head -100

# Check Phoenix UI for traces
# http://localhost:6006 -> Traces tab
```

---

### Day 2 End-of-Day Checklist
- [ ] `quick_eval.py` runs without errors
- [ ] Full 10-case eval completes
- [ ] `evals/first_run_results.json` has results
- [ ] Identified top 3 issues to fix
- [ ] At least 60% accuracy on first run (baseline)

---

## Day 3: CI/CD & Production-Ready

### Morning (2-3 hours)

#### 3.1 Fix Top Issues from Day 2

Based on results, likely actions:
- **If accuracy < 70%:** Improve golden dataset expected outputs
- **If safety ratings poor:** Add safety warnings to golden dataset
- **If citations hallucinated:** Add retrieval step before agent diagnosis

#### 3.2 Run Expanded Eval (30 cases)

```bash
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --limit 30 --output evals/expanded_results.json
```

**Target:** 85% accuracy, 100% safety, 90% procedure completeness

---

### Afternoon (3-4 hours)

#### 3.3 Integrate Tracer into Production Agents

See `phoenix_tracer.py` for usage patterns:
```python
from phoenix_tracer import init_phoenix, traced, wrap_client

init_phoenix(project_name="rivet_production", launch_app=False)

@traced(agent_name="siemens_sme", route="technical")
async def diagnose_fault(fault_code: str) -> dict:
    ...
```

#### 3.4 Set Up GitHub Secrets

Go to your repo → Settings → Secrets → Actions:
- `OPENAI_API_KEY`: For judge LLM
- `DATABASE_URL`: Neon connection string
- `GROQ_API_KEY`: Optional

#### 3.5 Create PR to Test CI Gate

```bash
git checkout -b test/phoenix-eval-gate
echo "# Test change" >> agents/sme/siemens_agent.py
git add . && git commit -m "test: Verify eval gate"
git push -u origin test/phoenix-eval-gate
```

---

### Day 3 End-of-Day Checklist
- [ ] 30-case eval passes (85%+ accuracy)
- [ ] Production orchestrator has tracing
- [ ] GitHub secrets configured
- [ ] CI gate runs on test PR
- [ ] Gate blocks if thresholds not met

---

## Success Metrics

| Metric | Day 1 | Day 2 | Day 3 | Target |
|--------|-------|-------|-------|--------|
| Phoenix Running | ✓ | ✓ | ✓ | ✓ |
| Golden Cases | 50 | 50 | 50+ | 100+ |
| Accuracy | - | 60% | 85% | 85%+ |
| Safety | - | - | 100% | 100% |
| CI Gate Active | - | - | ✓ | ✓ |

---

## Quick Reference Commands

```bash
# Start Phoenix
phoenix serve --port 6006

# Run quick test
cd phoenix_integration && python quick_eval.py

# Run full eval
python evals/run_eval.py --dataset ../datasets/golden_from_neon.jsonl --output evals/results.json

# Export more golden cases
python scripts/export_golden_dataset.py --limit 100

# View results
cat evals/results.json | python -m json.tool | head -50
```

---

## Files Created This Sprint

```
Agent Factory/
├── datasets/
│   └── golden_from_neon.jsonl          # Day 1
├── scripts/
│   └── export_golden_dataset.py        # Day 1 (NEW)
├── phoenix_integration/
│   ├── quick_eval.py                   # Day 2 (NEW)
│   └── evals/
│       ├── first_run_results.json      # Day 2
│       └── expanded_results.json       # Day 3
└── PHOENIX_3DAY_SPRINT.md              # This file
```
