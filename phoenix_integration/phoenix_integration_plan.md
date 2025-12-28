# Phoenix Integration Plan for Your Stack

## Decision Matrix: Where to Use What

| Project | Current | Recommendation | Why |
|---------|---------|----------------|-----|
| **RivetCEO Bot** | LangSmith | Keep LangSmith (for now) | Mid-migration to multi-tenant; don't add risk |
| **Agent Factory** | None | Phoenix | Framework-agnostic, scales to millions, $0 |
| **Friday (Voice App)** | None | Phoenix | New project, clean slate |
| **New Rivet CMMS** | None | Phoenix | Safety-critical evals are essential |

## Phase 1: Claude Code CLI Integration (Today)

### 1.1 Create Phoenix Wrapper for Agent Factory

```bash
# In your agent_factory root
claude "Create a phoenix_tracer.py module that:
1. Auto-initializes Phoenix on import
2. Provides @traced decorator for any agent function
3. Logs to both local Phoenix AND optional remote endpoint
4. Includes metadata: agent_name, llm_provider, user_id, session_id"
```

### 1.2 The Actual Claude Code Commands

```bash
# Step 1: Install Phoenix in agent_factory venv
claude "Add arize-phoenix[evals] to requirements.txt and install it"

# Step 2: Create tracer module
claude "Create agents/core/phoenix_tracer.py with:
- Auto-launch Phoenix session on import
- @traced decorator that captures input/output/latency/tokens
- Support for Groq, OpenAI, Anthropic clients
- Async support for your Telegram handlers"

# Step 3: Integrate with your orchestrator
claude "Modify agents/orchestrators/rivet_orchestrator.py to:
- Import phoenix_tracer
- Wrap each SME agent call with @traced
- Add route_decision as span attribute
- Log OCR results as span events"

# Step 4: Create eval templates for your domain
claude "Create evals/industrial_maintenance_judges.py with:
- TECHNICAL_ACCURACY_TEMPLATE (judge if root cause is correct)
- SAFETY_COMPLIANCE_TEMPLATE (judge if LOTO warnings present)
- MANUAL_CITATION_TEMPLATE (judge if citations are real)
Use my existing knowledge atoms structure for expected outputs"
```

## Phase 2: Golden Dataset from Your Neon DB (This Week)

Your ~2,000 knowledge atoms ARE your golden dataset. Extract them:

```bash
claude "Create scripts/export_golden_dataset.py that:
1. Connects to Neon PostgreSQL (use existing connection)
2. Queries knowledge_atoms table for fault_code entries
3. Structures as JSONL with:
   - test_case_id: atom_id
   - input: {fault_code, equipment_type, symptoms}
   - expected_output: {root_cause, safety_warnings, repair_steps}
4. Exports to datasets/golden_from_neon.jsonl"
```

## Phase 3: Eval Gate for Agent Factory PRs

```bash
claude "Create .github/workflows/agent_eval_gate.yml that:
1. Triggers on PR to agents/** or orchestrators/**
2. Runs Phoenix evals against golden_from_neon.jsonl
3. Fails if accuracy < 85% or safety < 100%
4. Posts eval summary as PR comment"
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR INFRASTRUCTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Telegram    │───▶│ RivetCEO    │───▶│ LangSmith   │     │
│  │ Bot         │    │ Orchestrator│    │ (keep)      │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Agent       │───▶│ Any New     │───▶│ Phoenix     │     │
│  │ Factory     │    │ Agent       │    │ (self-host) │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                            │                                │
│                            ▼                                │
│                     ┌─────────────┐                         │
│                     │ LLM-as-Judge│                         │
│                     │ Evals       │                         │
│                     └─────────────┘                         │
│                            │                                │
│                            ▼                                │
│                     ┌─────────────┐                         │
│                     │ CI/CD Gate  │                         │
│                     │ (85%+ acc)  │                         │
│                     └─────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Concrete Claude Code Session

Here's the exact terminal session to run:

```bash
# Terminal 1: Start Phoenix server
cd ~/agent_factory
source venv/bin/activate
pip install arize-phoenix[evals]
phoenix serve  # Runs at http://localhost:6006

# Terminal 2: Claude Code integration
cd ~/agent_factory

# Create the tracer
claude "Create agents/core/phoenix_tracer.py - a production-ready 
tracing module that:
1. Wraps Groq/OpenAI/Anthropic clients automatically
2. Provides @traced decorator for agent functions
3. Captures: input, output, latency, tokens, cost, model
4. Adds custom attributes: agent_name, route, user_id
5. Works with async functions (for Telegram handlers)
Include docstrings and type hints."

# Test it
claude "Create a test script that:
1. Imports phoenix_tracer
2. Calls a simple Groq completion
3. Verifies trace appears in Phoenix UI
Run it and show me the output."

# Export golden dataset
claude "Create scripts/export_golden_dataset.py that:
1. Uses my existing Neon connection (check .env for DATABASE_URL)
2. Queries for equipment fault knowledge atoms
3. Formats as Phoenix-compatible JSONL
4. Saves to datasets/golden_dataset.jsonl"

# Create judge templates
claude "Create evals/judges.py with industrial maintenance 
eval templates for:
1. Technical accuracy (root cause correctness)
2. Safety compliance (LOTO warnings present)
3. Procedure completeness (repair steps feasible)
4. Citation accuracy (manual references real)
Use GPT-4 as the judge model."

# Run first eval
claude "Create evals/run_eval.py that:
1. Loads golden_dataset.jsonl
2. For first 10 cases, runs my siemens_sme_agent
3. Evaluates with all 4 judge templates
4. Outputs summary to console and JSON
Run it with --dry-run first to show me what it would do."
```

## Cost Comparison (Your Scale)

| Scenario | LangSmith | Phoenix |
|----------|-----------|---------|
| Dev (1K traces/day) | ~$6/month | $0 |
| Production (100K traces/day) | ~$600/month | $15-25 VPS |
| Scale (1M traces/day) | ~$6,000/month | $50-100 VPS |

At "millions of users" scale, Phoenix saves you **$70K+/year**.

## Migration Path (No Disruption)

1. **Week 1**: Phoenix running alongside LangSmith; new agents use Phoenix
2. **Week 2**: Golden dataset extracted; first evals running
3. **Week 3**: CI/CD gate active for Agent Factory
4. **Month 2**: After RivetCEO multi-tenant is stable, migrate it to Phoenix
5. **Month 3**: Deprecate LangSmith entirely

## Your Immediate Next Step

Run this in your terminal right now:

```bash
pip install arize-phoenix[evals]
phoenix serve
# Open http://localhost:6006 in browser
# You should see empty Phoenix UI
```

Then in Claude Code:
```bash
claude "I have Phoenix running at localhost:6006. Create a 
phoenix_tracer.py that integrates with my Groq-based agents 
in agent_factory. Include a test that I can run to verify 
traces appear in Phoenix."
```

## Why This Matters for "AI Amazing + Millions"

1. **Safety-critical evals** = No lawsuit when your bot gives bad LOTO advice
2. **Golden dataset** = Provable accuracy ("Our agents are 92% accurate on 500 real fault cases")
3. **CI/CD gate** = Ship faster without breaking things
4. **$0 at scale** = More margin on your Stripe subscriptions
