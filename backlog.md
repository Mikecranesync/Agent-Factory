# Agent Factory - Master Backlog

**Multi-product AI automation platform powering SCAFFOLD, PLC Tutor, and RIVET Industrial**

---

## 🎯 Current Priority: SCAFFOLD SaaS Platform

**Status**: IN PROGRESS (Week 13, Phase 2 Validation)

**Why Priority #1**:
- Fastest revenue path ($1M-$3.2M Year 1 potential)
- Validates Agent Factory platform at scale
- Funds PLC Tutor and RIVET development

**Next Milestone**: MVP launch (Week 13), beta testing (10-20 early adopters)

See: `PRODUCTS.md` for complete strategy, `products/scaffold/backlog.md` for detailed tasks

---

## 📦 Products

| Product | Status | Priority | Backlog | Revenue Target |
|---------|--------|----------|---------|----------------|
| **SCAFFOLD** | 🔴 In Progress | #1 | [products/scaffold/backlog.md](products/scaffold/backlog.md) | $1M-$3.2M Year 1 |
| **PLC Tutor** | 🔜 Deferred (Month 2+) | #2 | [products/plc-tutor/backlog.md](products/plc-tutor/backlog.md) | $2.5M Year 3 |
| **RIVET Industrial** | 🔜 Deferred (Month 4+) | #3 | [products/rivet-industrial/backlog.md](products/rivet-industrial/backlog.md) | $2.5M Year 3 |

**Product Launch Sequence**:
1. **SCAFFOLD** (Week 13): Validates platform economics, generates revenue
2. **PLC Tutor** (Month 2+): Validates multi-vertical strategy, education GTM
3. **RIVET Industrial** (Month 4+): Validates community GTM, B2B integrations

---

## 🏗️ Platform Infrastructure

### ✅ Phase 1: Orchestration (COMPLETE)
- [x] AgentFactory core class (`agent_factory/core/agent_factory.py`)
- [x] Multi-agent routing (`agent_factory/core/orchestrator.py`)
- [x] Callback system (`agent_factory/core/callbacks.py`)
- [x] LangGraph integration (`agent_factory/workflows/graph_orchestrator.py`)
- [x] Collaboration patterns (`agent_factory/workflows/collaboration_patterns.py`)

**Validation**:
```bash
poetry run python -c "from agent_factory.core.orchestrator import AgentOrchestrator; print('OK')"
```

### ✅ Phase 2: Cost Optimization (COMPLETE)
- [x] LLMRouter - Capability-based model selection (`agent_factory/llm/router.py`)
- [x] RoutedChatModel - LangChain adapter (`agent_factory/llm/langchain_adapter.py`)
- [x] Model Registry - 12 models with pricing (`agent_factory/llm/config.py`)
- [x] Cost Tracker - Usage metrics (`agent_factory/llm/tracker.py`)
- [x] **73% cost reduction achieved** ($750/mo → $198/mo in testing)

**Validation**:
```bash
poetry run python -c "from agent_factory.llm.langchain_adapter import create_routed_chat_model; print('OK')"
```

### 🔄 Phase 3: Database & Memory (IN PROGRESS)
- [x] SettingsService - Database-backed config (`agent_factory/core/settings_service.py`)
- [x] DatabaseManager - Multi-provider PostgreSQL (`agent_factory/core/database_manager.py`)
- [x] PostgresMemoryStorage - Vector + relational (`agent_factory/memory/storage.py`)
- [ ] **Hybrid Search** - BM25 + semantic (pgvector + full-text)
- [ ] **Conversation History** - Multi-session, context window management
- [ ] **Agent Memory** - Cross-session memory, shared context

**Validation**:
```bash
poetry run python -c "from agent_factory.core.settings_service import settings; print(settings)"
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.health_check_all())"
```

### 🟡 Phase 4: Hooks & History (PLANNED)
- [ ] **Event System** - Hook registration, event dispatching (`agent_factory/core/hooks.py`)
- [ ] **History Tracking** - UOCS (Use Of Claude Sessions) pattern
- [ ] **Windows Integration** - PowerShell wrappers, context sync (`agent_factory/integrations/windows/`)
- [ ] **Configuration Versioning** - Rollback support, migration scripts

**Inspired by**: PAI (Personal AI Infrastructure) patterns from Archon (13.4k⭐)

### 🟡 Phase 5: Observability (PLANNED)
- [ ] **OpenTelemetry** - Distributed tracing (`agent_factory/observability/tracing.py`)
- [ ] **Prometheus Metrics** - Agent execution times, error rates (`agent_factory/observability/metrics.py`)
- [ ] **Grafana Dashboards** - Real-time monitoring, alerts
- [ ] **Error Tracking** - Sentry integration, exception grouping

---

## 🔧 Infrastructure Tasks

### Database
- [x] Supabase schema deployment (`docs/database/supabase_complete_schema.sql`)
- [x] Multi-provider failover (Supabase, Neon, Railway, Render)
- [ ] Database connection pooling (PgBouncer)
- [ ] Automated backups (daily snapshots)
- [ ] Schema migrations (Alembic)

### Security & Compliance
- [x] Security standards documented (`docs/patterns/SECURITY_STANDARDS.md`)
- [ ] SOC 2 compliance checklist
- [ ] GDPR compliance (data retention, deletion)
- [ ] Audit logging (who did what, when)
- [ ] Rate limiting (prevent abuse)
- [ ] Input validation (allow-lists, sanitization)

### CI/CD
- [ ] GitHub Actions - Automated testing, linting
- [ ] Pre-commit hooks - Prevent commits to main, run tests
- [ ] Multi-product deploys - Deploy SCAFFOLD/PLC/RIVET independently
- [ ] Staging environments - Test before production
- [ ] Rollback strategy - Revert bad deploys

### Documentation
- [x] CLAUDE.md - AI assistant instructions (root)
- [x] PRODUCTS.md - Product portfolio strategy
- [x] PROJECT_STRUCTURE.md - Complete codebase map
- [x] Skills - CORE, PLC_TUTOR, RIVET_INDUSTRIAL, SCAFFOLD, RESEARCH (`.claude/Skills/`)
- [x] PAI Contract - What PAI controls vs products (`.claude/PAI_CONTRACT.md`)
- [ ] API documentation - OpenAPI/Swagger specs
- [ ] User guides - Setup, deployment, troubleshooting

---

## 📚 Knowledge Extraction (EPIC)

**Goal**: Extract reusable patterns from CORE repositories (Backlog.md MCP, pai-config-windows, Agent Factory)

**Status**: 🟡 In Progress

See: `backlog/tasks/task-86 - EPIC-Knowledge-Extraction-from-CORE-Repositories.md`

### Subtasks (9 Total)
- [ ] **task-86.1**: Identify high-value patterns from CORE repos
- [ ] **task-86.2**: Document Backlog.md MCP architecture patterns
- [ ] **task-86.3**: Document pai-config-windows patterns
- [ ] **task-86.4**: Document cross-repository integration patterns
- [ ] **task-86.5**: Add inline documentation to critical files
- [ ] **task-86.6**: Deploy knowledge atoms to database, validate search
- [ ] **task-86.7**: Generate 50-70 knowledge atoms with embeddings
- [ ] **task-86.8**: Document Agent Factory architecture patterns
- [ ] **task-86.9**: Implement 3-6 reusable pattern classes

**Why This Matters**:
- Captures institutional knowledge (MCP architecture, Windows integration, multi-app context sync)
- Enables LLM agents to learn from existing patterns (via RAG)
- Reduces "reinventing the wheel" across products
- Creates searchable knowledge base for future development

---

## 🔗 Cross-Product Integration

### Shared Infrastructure
- **Knowledge Atom Standard** - IEEE LOM-based schema (PLC, RIVET, SCAFFOLD)
- **Supabase Backend** - Multi-tenant schema, pgvector indexes
- **Citation Validation** - Perplexity-style footnotes
- **LLM Router** - Cost optimization (73% reduction)
- **Agent Orchestration** - Multi-agent routing, collaboration patterns

### Integration Points
```
SCAFFOLD (Priority #1)
  ↓ validates platform
PLC Tutor (Month 2+)
  ↓ validates multi-vertical + education GTM
RIVET (Month 4+)
  ↓ validates community GTM + B2B
```

**Cross-Promotion**:
- PLC videos link to RIVET for troubleshooting
- RIVET users discover PLC education content
- SCAFFOLD used to build/maintain PLC + RIVET features

---

## 📊 Success Metrics

### Platform Health
- **Uptime**: >99.9% (Supabase + Railway)
- **Latency**: <100ms (database queries), <10ms (LLM router overhead)
- **Cost**: <$500/month (all products, all infrastructure)
- **Error Rate**: <1% (agent execution failures)

### Product Metrics (Year 1)
| Product | Users | Revenue | Key Metric |
|---------|-------|---------|------------|
| SCAFFOLD | 200 | $600K-$960K ARR | 50-80 paying customers (Month 12) |
| PLC Tutor | 20K | $60K ARR | 100 videos, 20K subs (Month 12) |
| RIVET | 10K | $80K ARR | 100 answered questions (Month 12) |
| **Total** | **30K+** | **$740K-$1.1M ARR** | **Platform validated** |

---

## 🗂️ Decisions Log

**Major decisions tracked in**: `DECISIONS_LOG.md`

Recent decisions:
- **2025-12-09**: SCAFFOLD Priority #1 (deferred PLC Tutor, RIVET)
- **2025-12-15**: LLM Router cost optimization (73% reduction)
- **2025-12-20**: Multi-provider database failover (4 providers)
- **2025-12-22**: PAI foundation (Skills, hooks, history)

---

## 🔍 Backlog Management

### Active Backlogs
- **Platform**: This file (`backlog.md`)
- **SCAFFOLD**: `products/scaffold/backlog.md`
- **PLC Tutor**: `products/plc-tutor/backlog.md`
- **RIVET**: `products/rivet-industrial/backlog.md`

### Backlog.md MCP Integration
- **MCP Tools**: `backlog task create/edit/view/list` for task management
- **Sync Script**: `poetry run python scripts/backlog/sync_tasks.py` (sync to `TASK.md`)
- **Source of Truth**: `backlog/tasks/*.md` (structured YAML + Markdown)
- **View Layer**: `TASK.md` (auto-generated, read-only sync zones)

See: `backlog/README.md` for full workflow

---

## 📖 References

### Essential Docs
- **CLAUDE.md** - AI assistant instructions (you are here)
- **PRODUCTS.md** - Product portfolio strategy
- **PROJECT_STRUCTURE.md** - Complete codebase map
- **TASK.md** - Active task tracking (auto-synced from Backlog.md)

### Architecture
- **Platform**: `docs/architecture/00_architecture_platform.md`
- **Database**: `docs/database/00_database_schema.md`
- **Patterns**: `docs/patterns/` (Security, Git Worktrees, PAI)

### Implementation
- **Roadmap**: `docs/implementation/00_platform_roadmap.md`
- **YouTube-Wiki**: `docs/implementation/YOUTUBE_WIKI_STRATEGY.md`
- **Agent Organization**: `docs/architecture/AGENT_ORGANIZATION.md`

### Skills
- **CORE**: `.claude/Skills/CORE/SKILL.md`
- **PLC_TUTOR**: `.claude/Skills/PLC_TUTOR/SKILL.md`
- **RIVET_INDUSTRIAL**: `.claude/Skills/RIVET_INDUSTRIAL/SKILL.md`
- **SCAFFOLD**: `.claude/Skills/SCAFFOLD/SKILL.md`
- **RESEARCH**: `.claude/Skills/RESEARCH/SKILL.md`

---

**Last Updated**: 2025-12-22
**Next Review**: After SCAFFOLD MVP launch (Week 13)
