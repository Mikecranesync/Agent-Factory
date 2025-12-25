# Decision History

**Tracks major architectural and strategic decisions for Agent Factory**

---

## Purpose

This log captures **why** decisions were made, not just **what** was done:
- Architecture choices
- Technology selections
- Product priorities
- Process changes
- Deferred features

**Format**: Decision records with context, rationale, consequences, and alternatives considered.

---

## Template

```markdown
## [YYYY-MM-DD] Decision Title

**Context**: What situation led to this decision?

**Decision**: What was decided?

**Rationale**: Why was this the right choice?

**Consequences**: What does this enable/prevent?

**Alternatives Considered**:
1. Option A - Pros/Cons
2. Option B - Pros/Cons
3. Option C - Pros/Cons

**Status**: Active | Superseded | Deprecated

**Related Decisions**: Links to other decisions
```

---

## 2025 Decisions

### [2025-12-22] PAI Foundation with Bash Hooks

**Context**: Agent Factory needed event-driven automation and session tracking (UOCS pattern). Two options: TypeScript (type-safe, requires compilation) vs Bash (native, no build step).

**Decision**: Use Bash hooks for all PAI automation (session, task, git, agent hooks).

**Rationale**:
- **Immediate usability**: No compilation step, works now
- **Git integration**: Native support for git hooks (pre-commit, pre-push)
- **Cross-platform**: Works on Windows (Git Bash), Linux, Mac
- **Proven patterns**: Based on Archon (13.4k⭐) PAI architecture
- **Comprehensive**: 11 hooks covering session, task, tool, agent, git events

**Consequences**:
- ✅ Hooks work immediately without build tooling
- ✅ Git safety enforced (worktree pattern, no secrets, tests required)
- ✅ Session continuity via UOCS pattern
- ✅ Windows integration via PowerShell wrappers
- ❌ No TypeScript type safety (acceptable for shell scripts)

**Alternatives Considered**:
1. **TypeScript hooks** - Type-safe but requires Node.js + tsc compilation
2. **Python hooks** - More portable but slower startup, requires Python interpreter
3. **Hybrid (Bash + TypeScript)** - Best of both worlds but added complexity

**Status**: Active

**Related Decisions**: Windows Integration (PowerShell), UOCS Pattern

---

### [2025-12-22] Multi-Product Backlog Structure

**Context**: Agent Factory powers 3 products (SCAFFOLD, PLC Tutor, RIVET). Single backlog was becoming cluttered.

**Decision**: Create product-specific backlogs (`products/*/backlog.md`) + master backlog (root `backlog.md`).

**Rationale**:
- **Separation of concerns**: Each product has its own roadmap
- **Clear priorities**: SCAFFOLD #1, PLC Tutor #2, RIVET #3
- **Independent timelines**: Products launch at different times
- **Master overview**: Root backlog shows cross-product integration

**Consequences**:
- ✅ Easier to navigate product-specific tasks
- ✅ Clear launch sequence (SCAFFOLD → PLC → RIVET)
- ✅ Product READMEs provide quick start guides
- ❌ Must sync between Backlog.md MCP and markdown files

**Alternatives Considered**:
1. **Single backlog** - Simple but cluttered, hard to prioritize
2. **Separate repos** - Clean but breaks shared infrastructure
3. **Monorepo with workspaces** - Overkill for current scale

**Status**: Active

**Related Decisions**: SCAFFOLD Priority #1, Backlog.md MCP Integration

---

### [2025-12-20] Multi-Provider Database Failover

**Context**: Relying on single database provider (Supabase) is risky. Outages block all products.

**Decision**: Implement DatabaseManager with 4-provider failover (Supabase → Neon → Railway → Render).

**Rationale**:
- **Resilience**: If Supabase is down, auto-failover to Neon
- **Cost optimization**: Can switch providers for best pricing
- **Vendor independence**: Not locked into single provider
- **Health checks**: Proactive monitoring of all providers

**Consequences**:
- ✅ 99.9%+ uptime (4 providers unlikely to all fail)
- ✅ Seamless failover (transparent to agents)
- ✅ Cost flexibility (switch for best pricing)
- ❌ More complexity in connection management

**Alternatives Considered**:
1. **Single provider (Supabase)** - Simple but single point of failure
2. **Manual failover** - Requires human intervention, slow recovery
3. **Read replicas** - Doesn't solve provider downtime

**Status**: Active

**Related Decisions**: PostgresMemoryStorage, SettingsService

---

### [2025-12-15] LLM Router Cost Optimization

**Context**: Autonomous agents were using expensive models (GPT-4o) for simple tasks (classification, extraction). Costs projected at $750/month.

**Decision**: Implement capability-based LLM routing (SIMPLE → gpt-3.5-turbo, COMPLEX → gpt-4o, CODING → gpt-4-turbo).

**Rationale**:
- **Cost reduction**: 73% savings ($750/mo → $198/mo)
- **No accuracy loss**: Match model to task complexity
- **Automatic selection**: Agents don't choose models, router does
- **Fallback chain**: If primary fails, try 2 more before erroring

**Consequences**:
- ✅ 73% cost reduction achieved in testing
- ✅ Same accuracy (capability-matched models)
- ✅ Transparent to agents (drop-in LangChain adapter)
- ❌ Small latency overhead (<10ms, negligible vs API call)

**Alternatives Considered**:
1. **Manual model selection** - Requires agent code changes, error-prone
2. **Always use cheapest** - Would degrade quality on complex tasks
3. **Prompt-based routing** - Less reliable than explicit capabilities

**Status**: Active

**Related Decisions**: RoutedChatModel, ModelCapability enum

---

### [2025-12-09] SCAFFOLD Priority #1 (Defer PLC Tutor, RIVET)

**Context**: 3 products ready to build (SCAFFOLD, PLC Tutor, RIVET). Limited resources (1 developer, no team).

**Decision**: SCAFFOLD Priority #1, defer PLC Tutor to Month 2+, defer RIVET to Month 4+.

**Rationale**:
- **Fastest revenue**: SCAFFOLD can generate $10K-$15K MRR by Month 4
- **Platform validation**: Proves Agent Factory works at scale before verticals
- **Funds other products**: SCAFFOLD revenue enables PLC Tutor & RIVET development
- **Market demand**: Agencies paying $10K-$50K/month for dev resources now

**Consequences**:
- ✅ Clear focus (1 product at a time, finish what we start)
- ✅ Revenue by Month 4 ($10K-$15K MRR)
- ✅ Platform proven before launching verticals
- ❌ PLC Tutor & RIVET delayed (acceptable tradeoff)

**Alternatives Considered**:
1. **Build all 3 in parallel** - Spread too thin, nothing ships
2. **PLC Tutor first** - Slower revenue, unproven market demand
3. **RIVET first** - Requires human expert network (chicken-egg problem)

**Status**: Active

**Related Decisions**: Multi-Product Backlog, Product Launch Sequence

---

### [2025-11-15] Knowledge Atom Standard (IEEE LOM-based)

**Context**: Need unified schema for knowledge across PLC Tutor, RIVET, SCAFFOLD. Must support citations, safety compliance, prerequisites.

**Decision**: Adopt IEEE LOM (Learning Object Metadata) as base, extend for domain-specific fields.

**Rationale**:
- **Industry standard**: IEEE LOM is proven for educational content
- **Extensible**: Can add domain fields (vendor, equipment_class, safety_level)
- **Interoperable**: PLC atoms, RIVET atoms, code atoms share base schema
- **Supports prerequisites**: Built-in prerequisite chains

**Consequences**:
- ✅ Shared infrastructure (ingestion, validation, search)
- ✅ Cross-product knowledge base (PLC atoms link to RIVET)
- ✅ Citation validation (Perplexity-style footnotes)
- ✅ Safety compliance (NFPA, OSHA, ANSI standards)

**Alternatives Considered**:
1. **Custom schema from scratch** - More flexibility but reinventing wheel
2. **Schema.org** - Web-focused, not education-specific
3. **Dublin Core** - Too minimal, missing prerequisites

**Status**: Active

**Related Decisions**: Perplexity-Style Citations, Multi-Vertical Strategy

---

## Decision Categories

### Architecture (6 decisions)
- PAI Foundation with Bash Hooks
- Multi-Provider Database Failover
- LLM Router Cost Optimization
- Knowledge Atom Standard (IEEE LOM)
- SettingsService (Database-backed Config)
- Git Worktree Pattern (Safety)

### Product Strategy (3 decisions)
- SCAFFOLD Priority #1
- Multi-Product Backlog Structure
- YouTube-Wiki Strategy (Build knowledge BY teaching)

### Infrastructure (2 decisions)
- Supabase + pgvector (Vector + Relational)
- Multi-Provider Failover (4 databases)

---

## Superseded Decisions

### [2025-11-01] Single Monolithic Agent (SUPERSEDED)

**Original Decision**: Build single "master agent" that does everything.

**Why Superseded**: Realized multi-agent orchestration is more scalable, debuggable, and cost-effective. Each agent has clear responsibility (Research, Script, Voice, Video, Upload).

**Superseded By**: Multi-Agent Orchestration (Phase 1)

**Date Superseded**: 2025-11-15

---

## Deprecated Decisions

### [2025-10-15] OpenAI-Only LLM Provider (DEPRECATED)

**Original Decision**: Use only OpenAI models (GPT-4, GPT-3.5).

**Why Deprecated**: LLM Router now supports 12 models across 4 providers (OpenAI, Anthropic, Google, DeepSeek). Vendor lock-in is risk.

**Deprecated By**: LLM Router Multi-Provider

**Date Deprecated**: 2025-12-15

---

**Note**: Major decisions should be logged here before implementation. Update status when superseded/deprecated.
