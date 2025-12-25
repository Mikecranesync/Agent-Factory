# PLC Tutor Backlog

**Status**: 🔜 Deferred to Month 2+ (Post-SCAFFOLD launch)

**Priority**: #2 (After SCAFFOLD validates platform)

---

## 🔴 Blocked (Awaiting SCAFFOLD Launch)

### Infrastructure Dependencies
- [ ] **Voice Clone Setup** - Record 10-15 min voice samples → ElevenLabs Pro
  - Requires: Microphone setup, recording environment
  - Blockers: None (can start immediately)
  - Estimate: 2 hours

- [ ] **YouTube Partner Program** - Apply for monetization
  - Requires: 1K subscribers, 4K watch hours
  - Blockers: Need published videos first
  - Estimate: Milestone (Month 6+)

- [ ] **VPS Ingestion Pipeline** - Deploy to Hostinger VPS (72.60.175.144)
  - Requires: Docker Compose setup, Ollama + Postgres + Redis
  - Blockers: None (VPS already provisioned)
  - Estimate: 4 hours

---

## 🟡 Ready to Start (When SCAFFOLD Complete)

### Month 2: Knowledge Base Foundation (Week 1-4)
- [ ] **Ingest 50-100 atoms** from Allen-Bradley ControlLogix manual
  - Run: `poetry run python scripts/knowledge/batch_ingest.py`
  - Source: `scripts/kb_seed_urls.py` (17 curated PDFs)
  - Validate: 5-dimension quality scoring >4.0

- [ ] **Test semantic search** with 10 sample queries
  - Run: `poetry run python scripts/knowledge/test_semantic_search.py`
  - Queries: Timer instructions, motor control, LOTO procedures
  - Target: <100ms query time, >80% relevance

- [ ] **Deploy ingestion_chain_migration.sql** to Supabase
  - Location: `agent_factory/workflows/ingestion_chain.py` (embedded SQL)
  - Tables: `source_fingerprints`, `ingestion_jobs`, `atom_quality_scores`
  - Verify: Foreign keys, indexes, RLS policies

### Month 2-3: First 3 Videos (Week 5-8)
- [ ] **Video 1**: "What is Electricity? (Industrial Skills Hub #1)"
  - Topic: Electricity basics (atoms, electrons, flow of charge)
  - Duration: 5-7 min
  - Atoms: `plc:generic:electricity-intro`
  - Human approval: Required (set quality standard)

- [ ] **Video 2**: "Voltage, Current, and Resistance Explained"
  - Topic: V/I/R definitions, units, relationships
  - Duration: 7-9 min
  - Atoms: `plc:generic:voltage`, `plc:generic:current`, `plc:generic:resistance`
  - Human approval: Required

- [ ] **Video 3**: "Ohm's Law - The Foundation of Electrical Engineering"
  - Topic: V=I×R, calculations, applications
  - Duration: 8-10 min
  - Atoms: `plc:generic:ohms-law`
  - Human approval: Required

### Month 3-4: Agent Tuning (Week 9-12)
- [ ] **ScriptwriterAgent tuning** - Improve script quality (target >90% approval)
  - Analyze: Failed scripts (low quality scores)
  - Tune: LLM prompts, personality markers, visual cues
  - Test: Generate 10 scripts, measure approval rate

- [ ] **VoiceProductionAgent validation** - Test voice clone quality
  - Generate: 5 test narrations (30-60s each)
  - Evaluate: Natural-sounding, pacing, emotion
  - Iterate: ElevenLabs settings (stability, similarity, style)

- [ ] **VideoAssemblyAgent optimization** - Reduce render time
  - Current: ~10 min/video (FFmpeg)
  - Target: <5 min/video
  - Optimize: Preset settings, hardware acceleration, batch processing

---

## 🟢 Completed

### Infrastructure
- [x] **18-agent system designed** (`docs/architecture/AGENT_ORGANIZATION.md`)
- [x] **Ingestion pipeline implemented** (7-stage LangGraph, `agent_factory/workflows/ingestion_chain.py`)
- [x] **Knowledge base schema** (Supabase tables, pgvector indexes)
- [x] **1,964+ atoms indexed** (Allen-Bradley, Siemens, Mitsubishi, Omron, Schneider)
- [x] **Content roadmap created** (100+ topics A-to-Z, `plc/content/CONTENT_ROADMAP_AtoZ.md`)

### Agents
- [x] **MasterOrchestratorAgent** - 24/7 daemon, task scheduling (`agents/orchestration/`)
- [x] **ResearchAgent** - Web/PDF/YouTube scraping (`agents/research/`)
- [x] **ScriptwriterAgent** - Atom → video script (`agents/content/`)
- [x] **VoiceProductionAgent** - ElevenLabs integration (`agents/media/`)
- [x] **VideoAssemblyAgent** - FFmpeg rendering (`agents/media/`)
- [x] **YouTubeUploaderAgent** - YouTube Data API (`agents/media/`)
- [x] **SEOAgent** - Keyword research, metadata (`agents/content/`)
- [x] **QualityCheckerAgent** - 5-dimension validation (`agents/knowledge/`)
- [x] **AnalyticsAgent** - Metrics tracking (`agents/engagement/`)

### Documentation
- [x] **PLC_TUTOR Skill** - Comprehensive skill definition (`.claude/Skills/PLC_TUTOR/SKILL.md`)
- [x] **YouTube-Wiki Strategy** - Build knowledge BY teaching (`docs/implementation/YOUTUBE_WIKI_STRATEGY.md`)
- [x] **Atom Schema** - IEEE LOM-based universal schema (`docs/architecture/ATOM_SPEC_UNIVERSAL.md`)
- [x] **Product README** - Quick start guide (`products/plc-tutor/README.md`)

---

## 📊 Metrics & Targets

### Month 2 (Knowledge Base)
- **Atoms**: 50-100 (Allen-Bradley focus)
- **Quality**: >90% pass rate (5-dimension scoring)
- **Search**: <100ms semantic queries

### Month 3 (First Videos)
- **Videos**: 3 published
- **Quality**: >8/10 average score
- **Approval**: Human review on all 3

### Month 4 (Agent Tuning)
- **Script Approval**: >90% (ScriptwriterAgent)
- **Voice Quality**: Natural-sounding (ElevenLabs)
- **Render Time**: <5 min/video (VideoAssemblyAgent)

### Month 12 (Production Scale)
- **Videos**: 100 published
- **Subscribers**: 20K
- **Revenue**: $5K/month
- **Autonomy**: Fully autonomous (exception flagging only)

---

## 🔗 Related Backlogs

- **Agent Factory Core**: `backlog.md` (root)
- **RIVET Industrial**: `products/rivet-industrial/backlog.md`
- **SCAFFOLD**: `products/scaffold/backlog.md`
- **RESEARCH Skill**: Shared infrastructure (no separate backlog)

---

## 📚 References

- **Skill**: `.claude/Skills/PLC_TUTOR/SKILL.md`
- **Agent Specs**: `docs/architecture/AGENT_ORGANIZATION.md`
- **Content Roadmap**: `plc/content/CONTENT_ROADMAP_AtoZ.md`
- **YouTube Strategy**: `docs/implementation/YOUTUBE_WIKI_STRATEGY.md`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`

---

**Last Updated**: 2025-12-22
**Next Review**: After SCAFFOLD launch (Month 2+)
