# Agent Factory - Refactor Plan

**Generated**: 2025-12-21
**Strategy**: Incremental, safe refactors (not rewrites)
**Pattern**: Expand → Migrate → Contract (behind tests)

---

## Guiding Principles

1. **Small Steps**: Each step fits in one PR
2. **Reversible**: Can roll back if issues arise
3. **Tested**: Run tests before/after each step
4. **No Rewrites**: Move/improve code, don't rewrite from scratch
5. **Preserve Behavior**: Project integrity is paramount

---

## Phase 1: Cleanup & Documentation (Low Risk)

### Step 1: Remove Dead Files
**Goal**: Clean up root directory

**Actions**:
- Delete `Repos.jpg` (screenshot, not needed)
- Create `archive/deployment-guides/` directory
- Move old deployment guides to archive:
  - `Prompt telegram.md` → `archive/deployment-guides/`
  - `codebase fixer.md` → `archive/deployment-guides/`
  - Any other obsolete guides

**Files Changed**: ~5 files
**Risk**: None (just moving/deleting)
**Test**: Verify app still runs: `poetry run python agent_factory/examples/demo.py`

---

### Step 2: Update LLM Model Pricing (Q1 2025)
**Goal**: Ensure cost optimization uses current prices

**Actions**:
- Open `agent_factory/llm/config.py`
- Verify pricing for each model (check OpenAI/Anthropic/Google pricing pages)
- Update `MODEL_PRICING` dict if changed
- Update `last_verified_date` comment
- Re-run cost optimization tests to verify savings still accurate

**Files Changed**: `agent_factory/llm/config.py`
**Risk**: Low (just data update)
**Test**: `poetry run pytest tests/test_llm_router.py -k pricing`

---

### Step 3: Add Missing Docstrings to SCRUB Files
**Goal**: Document partial implementations before completing them

**Actions**:
- Add module-level docstrings to:
  - `agent_factory/llm/cache.py`
  - `agent_factory/llm/streaming.py`
  - `agent_factory/memory/hybrid_search.py`
- Include status (e.g., "Stub: Not yet implemented")
- Document intended behavior

**Files Changed**: 3 files
**Risk**: None (just documentation)
**Test**: `poetry run python -c "import agent_factory.llm.cache; help(agent_factory.llm.cache)"`

---

## Phase 2: Complete Partial Features (Medium Risk)

### Step 4: Implement LRU Cache for LLM Responses
**Goal**: Reduce repeat API calls, save costs

**Actions**:
1. In `agent_factory/llm/cache.py`, implement `LRUCache` class:
   - Use `functools.lru_cache` or custom implementation
   - Hash prompt + model → cache key
   - TTL: 1 hour (configurable)
   - Max size: 1000 entries
2. Add cache to `LLMRouter.route()` method
3. Add cache statistics method (`get_hit_rate()`)
4. Write unit tests for cache hit/miss/expiry

**Files Changed**:
- `agent_factory/llm/cache.py` (new implementation)
- `agent_factory/llm/router.py` (integrate cache)
- `tests/test_llm_cache.py` (new tests)

**Risk**: Low (optional feature, doesn't break existing)
**Test**:
```bash
poetry run pytest tests/test_llm_cache.py
poetry run python examples/llm_router_demo.py --with-cache
```

---

### Step 5: Complete Streaming Support
**Goal**: Enable streaming responses for better UX

**Actions**:
1. In `agent_factory/llm/streaming.py`, implement `StreamingRouter`:
   - Async generator for token-by-token responses
   - Support OpenAI, Anthropic, Google streaming APIs
   - Fallback to batch if streaming unavailable
2. Add streaming examples
3. Update `RoutedChatModel` to support streaming
4. Write integration tests

**Files Changed**:
- `agent_factory/llm/streaming.py` (implement)
- `agent_factory/llm/langchain_adapter.py` (add streaming support)
- `examples/streaming_demo.py` (new example)
- `tests/test_streaming.py` (new tests)

**Risk**: Medium (async complexity)
**Test**:
```bash
poetry run pytest tests/test_streaming.py
poetry run python examples/streaming_demo.py
```

---

### Step 6: Implement Hybrid Search (Vector + Keyword)
**Goal**: Improve retrieval accuracy for KB queries

**Actions**:
1. In `agent_factory/memory/hybrid_search.py`, implement `HybridSearcher`:
   - Combine pgvector semantic search with PostgreSQL full-text search
   - Weighted scoring: 70% vector, 30% keyword (configurable)
   - Reranking logic
2. Add to `PostgresMemoryStorage` as optional feature
3. Write benchmarks comparing pure vector vs hybrid
4. Add integration tests

**Files Changed**:
- `agent_factory/memory/hybrid_search.py` (implement)
- `agent_factory/memory/storage.py` (integrate)
- `tests/test_hybrid_search.py` (new tests)
- `benchmarks/search_comparison.py` (new benchmark)

**Risk**: Medium (database queries, performance)
**Test**:
```bash
poetry run pytest tests/test_hybrid_search.py
poetry run python benchmarks/search_comparison.py
```

---

## Phase 3: Production Blockers (High Priority)

### Step 7: Create SME Agent Template
**Goal**: Standardize agent implementations before building real agents

**Actions**:
1. Create `agent_factory/templates/sme_agent_template.py`:
   - Standard structure for all SME agents
   - Required methods: `analyze_query()`, `search_kb()`, `generate_answer()`, `score_confidence()`
   - Error handling patterns
   - Logging/tracing hooks
2. Document in `docs/patterns/SME_AGENT_PATTERN.md`
3. Create example implementation

**Files Changed**:
- `agent_factory/templates/sme_agent_template.py` (new)
- `docs/patterns/SME_AGENT_PATTERN.md` (new)
- `examples/sme_agent_example.py` (new)

**Risk**: Low (just a template)
**Test**: `poetry run python examples/sme_agent_example.py`

---

### Step 8: Implement Real Motor Control SME Agent
**Goal**: Replace mock with production agent (Phase 3, task-3.1)

**Actions**:
1. Use SME template from Step 7
2. Implement `MotorControlSMEAgent`:
   - Query analysis for motor-related questions
   - KB search with vendor filtering
   - Answer generation with citations
   - Confidence scoring
3. Integration test with real KB
4. Deploy to staging

**Files Changed**:
- `agent_factory/rivet_pro/agents/motor_control_sme.py` (replace mock)
- `tests/integration/test_motor_control_sme.py` (new tests)

**Risk**: Medium (production feature)
**Test**:
```bash
poetry run pytest tests/integration/test_motor_control_sme.py
poetry run python -c "from agent_factory.rivet_pro.agents.motor_control_sme import MotorControlSMEAgent; agent = MotorControlSMEAgent(); print(agent.analyze_query('Why is my motor overheating?'))"
```

---

### Step 9: Implement Remaining SME Agents (Phase 3)
**Goal**: Complete Phase 3 agent suite

**Actions**:
1. `ProgrammingSMEAgent` (PLC code questions) - task-3.2
2. `TroubleshootingSMEAgent` (diagnostics) - task-3.3
3. `NetworkingSMEAgent` (industrial networks) - task-3.4
4. All follow template from Step 7
5. Comprehensive integration tests

**Files Changed**:
- 3 new agent files
- 3 new test files

**Risk**: Medium (multiple production agents)
**Test**: End-to-end RIVET query test with all agents
```bash
poetry run pytest tests/integration/test_rivet_end_to_end.py
```

---

### Step 10: Add RAG Reranking
**Goal**: Improve answer quality with reranking

**Actions**:
1. In `agent_factory/rivet_pro/rag/reranker.py`, implement `Reranker`:
   - Cross-encoder model (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`)
   - Score query-document pairs
   - Rerank top-k candidates
2. Integrate into retrieval pipeline
3. Benchmark improvement over pure vector search
4. Add to RIVET orchestrator

**Files Changed**:
- `agent_factory/rivet_pro/rag/reranker.py` (new)
- `agent_factory/rivet_pro/rag/__init__.py` (integrate)
- `benchmarks/rag_quality.py` (new benchmark)
- `tests/test_reranker.py` (new tests)

**Risk**: Medium (ML model, inference time)
**Test**:
```bash
poetry run pytest tests/test_reranker.py
poetry run python benchmarks/rag_quality.py
```

---

## Phase 4: Testing & Observability

### Step 11: Optimize Slow Tests (task-16)
**Goal**: Improve test execution speed

**Actions**:
1. Profile test suite: `poetry run pytest --durations=10`
2. Identify slow tests (likely integration tests with external services)
3. Options:
   - Mock external services (Supabase, OpenAI) for unit tests
   - Parallelize with `pytest-xdist`
   - Split into fast/slow test suites
4. Update CI/CD to run fast tests on every PR, slow tests nightly

**Files Changed**:
- `tests/conftest.py` (add fixtures/mocks)
- `.github/workflows/tests.yml` (split fast/slow)
- `pytest.ini` (configure parallel execution)

**Risk**: Low (test improvements)
**Test**: Measure before/after execution time
```bash
# Before
time poetry run pytest

# After
time poetry run pytest -n auto  # parallel execution
```

---

### Step 12: Wire Langfuse Integration
**Goal**: LLM observability in production

**Actions**:
1. Complete `agent_factory/observability/langfuse_tracker.py`:
   - Initialize Langfuse client with API keys
   - Track every LLM call (model, prompt, response, latency, cost)
   - Link traces to user sessions
2. Add to `LLMRouter` as optional feature
3. Dashboard setup docs
4. Integration tests

**Files Changed**:
- `agent_factory/observability/langfuse_tracker.py` (complete)
- `agent_factory/llm/router.py` (integrate)
- `docs/deployment/LANGFUSE_SETUP.md` (new)
- `tests/test_langfuse_integration.py` (new)

**Risk**: Low (optional feature)
**Test**:
```bash
poetry run pytest tests/test_langfuse_integration.py
# Verify traces in Langfuse dashboard
```

---

### Step 13: Add Distributed Tracing
**Goal**: Track requests across agents

**Actions**:
1. Complete `agent_factory/observability/tracer.py`:
   - OpenTelemetry-compatible tracing
   - Generate trace IDs for each request
   - Span creation for agent calls
   - Export to Jaeger or Honeycomb
2. Integrate into `AgentOrchestrator`
3. Add trace visualization docs

**Files Changed**:
- `agent_factory/observability/tracer.py` (complete)
- `agent_factory/core/orchestrator.py` (integrate)
- `docs/deployment/TRACING_SETUP.md` (new)
- `tests/test_tracing.py` (new)

**Risk**: Medium (distributed systems complexity)
**Test**:
```bash
poetry run pytest tests/test_tracing.py
# Verify traces in Jaeger UI
```

---

### Step 14: Implement Prometheus Metrics
**Goal**: Production monitoring

**Actions**:
1. Complete `agent_factory/observability/metrics.py`:
   - Counter: agent invocations
   - Histogram: response latencies
   - Gauge: active sessions
   - Counter: LLM token usage
2. Add `/metrics` endpoint to FastAPI app
3. Grafana dashboard example

**Files Changed**:
- `agent_factory/observability/metrics.py` (implement)
- `agent_factory/api/app.py` (add /metrics endpoint)
- `docs/deployment/MONITORING_SETUP.md` (new)
- `grafana_dashboards/agent_factory.json` (new)

**Risk**: Low (read-only metrics)
**Test**:
```bash
poetry run python -m agent_factory.api.app
curl http://localhost:8000/metrics
```

---

## Phase 5: Advanced Features (Optional)

### Step 15: Template PLC Agents
**Goal**: Reduce duplication across 35+ PLC agents

**Actions**:
1. Analyze `agents/plc_business/` for common patterns
2. Create `AgentTemplate` base class:
   - Standard structure
   - Parameterized behavior
   - Shared utilities
3. Refactor 3-5 agents to use template
4. Document pattern

**Files Changed**:
- `agent_factory/templates/plc_agent_template.py` (new)
- `agents/plc_business/*.py` (refactor 3-5 agents)
- `docs/patterns/PLC_AGENT_TEMPLATE.md` (new)

**Risk**: Medium (refactoring existing agents)
**Test**: Verify all refactored agents produce identical outputs
```bash
poetry run pytest tests/integration/test_plc_agents.py
```

---

### Step 16: Complete Refs System (Phase 5)
**Goal**: Enable agents to reason about codebase

**Actions**:
1. Complete `refs/code_analyzer.py`:
   - Full AST traversal
   - Extract classes, functions, imports
2. Complete `refs/knowledge_graph.py`:
   - Build graph of code relationships
3. Complete `refs/project_twin.py`:
   - AI-readable project model
4. Complete `refs/twin_agent.py`:
   - Agent that operates on twin

**Files Changed**:
- 4 files in `agent_factory/refs/`
- New tests for each component

**Risk**: High (complex feature)
**Test**: End-to-end test of twin agent modifying codebase model
```bash
poetry run pytest tests/test_refs_system.py
```

---

### Step 17: Validate Field Eye with Real Data
**Goal**: Test industrial video analysis

**Actions**:
1. Collect 10 sample industrial maintenance videos
2. Run through Field Eye pipeline
3. Validate pause detection accuracy
4. Benchmark processing time
5. Document findings and iterate

**Files Changed**:
- `field_eye/utils/video_processing.py` (improvements)
- `field_eye/utils/pause_detection.py` (tune algorithm)
- `docs/validation/FIELD_EYE_RESULTS.md` (new)

**Risk**: Medium (depends on video quality)
**Test**: Manual validation of 10 videos
```bash
poetry run python field_eye/agents/data_ingest_agent.py --video sample1.mp4
```

---

## Execution Guidelines

### Before Each Step:
1. Read the current state of files to be modified
2. Run existing tests to establish baseline
3. Create a git worktree for the changes: `agentcli worktree-create step-N-name`
4. Work in the worktree, not main directory

### During Each Step:
1. Make small, incremental changes
2. Test frequently (after every logical change)
3. Commit checkpoints: `git commit -m "WIP: Step N - description"`

### After Each Step:
1. Run full test suite: `poetry run pytest`
2. Run linters: `poetry run black .` and `poetry run pylint agent_factory/`
3. Commit final: `git commit -m "feat: Step N - description"`
4. Create PR from worktree branch
5. Merge after tests pass

### If Step Fails:
1. Analyze failure (tests, linting, runtime error)
2. Roll back: `git reset --hard` to last checkpoint
3. Investigate root cause
4. Adjust approach or ask for guidance
5. Don't proceed to next step until current step works

---

## Recommended Execution Order

### **Week 1**: Quick Wins (Steps 1-3)
- Low risk, immediate value
- Clean up codebase
- Update documentation

### **Week 2**: Partial Features (Steps 4-6)
- Medium risk, high value
- Complete caching, streaming, hybrid search
- Improves performance and quality

### **Week 3-4**: Production Blockers (Steps 7-10)
- High priority for RIVET launch
- SME agents + reranking
- Most critical refactors

### **Week 5-6**: Observability (Steps 11-14)
- Production monitoring
- Test optimization
- Langfuse, tracing, metrics

### **Month 2+**: Advanced Features (Steps 15-17)
- Optional improvements
- PLC agent templates
- Refs system
- Field Eye validation

---

## Success Metrics

### After Week 1:
- ✅ Codebase cleaned up (no dead files)
- ✅ Pricing updated, cost optimization verified

### After Week 2:
- ✅ LLM response caching working (measure hit rate)
- ✅ Streaming responses available
- ✅ Hybrid search improves retrieval accuracy

### After Week 4:
- ✅ All 4 RIVET SME agents implemented
- ✅ RAG reranking working
- ✅ RIVET ready for production launch

### After Week 6:
- ✅ Tests run 50% faster
- ✅ Langfuse tracks all LLM calls
- ✅ Distributed tracing operational
- ✅ Metrics dashboard available

### After Month 2:
- ✅ PLC agents use template (less duplication)
- ✅ Refs system functional
- ✅ Field Eye validated with real data

---

## Risk Mitigation

### High-Risk Steps (8, 9, 16):
- Extra testing (manual + automated)
- Staging deployment before production
- Rollback plan documented
- Feature flags for gradual rollout

### Medium-Risk Steps (5, 6, 10, 13, 15):
- Comprehensive unit tests
- Integration tests with mocked services
- Code review by second developer (if available)

### Low-Risk Steps (1-4, 7, 11, 12, 14, 17):
- Standard process
- Automated tests sufficient
- Quick iteration

---

## Final Notes

- **No step should take more than 1 week** - if it does, break it down further
- **Always run tests before moving on** - broken tests = blocked progress
- **Document as you go** - update docs/patterns/ for new patterns
- **Ask for help if stuck** - don't waste time on blocked steps

This plan preserves the excellent work already done while systematically completing partial features and cleaning up technical debt. The 90% SAVE rate means most refactoring is "enhancement" not "repair".
