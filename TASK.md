# Active Tasks - Agent Factory

**Last Updated:** 2025-12-10

---

## CURRENT FOCUS: Week 1 - PLC Tutor / Industrial Skills Hub Foundation

**See:** GitHub Issue #49 (Week 1 Complete Checklist), `docs/IMPLEMENTATION_ROADMAP.md`

---

## In Progress

### [WEEK 1] Infrastructure Setup & Voice Training (Issue #44)
**Status:** Ready to Start (User Tasks)
**Priority:** CRITICAL
**Estimated Effort:** 3-4 hours
**Assigned To:** USER

**Tasks (Monday-Tuesday):**
- [ ] Record 10-15 min voice samples (teaching mode, varied emotion)
- [ ] Upload to ElevenLabs Professional Voice Cloning
- [ ] Create Supabase project (enable pgvector extension)
- [ ] Run schema migrations (`docs/supabase_migrations.sql`)
- [ ] Set up `.env` file with API keys (Supabase, ElevenLabs, OpenAI, Claude)
- [ ] Test voice clone (generate 30s sample, verify quality)

**Success Criteria:**
- Voice clone sounds natural (< 10% robotic artifacts)
- Supabase connection test passes (can insert/query atoms)
- All API keys valid (test calls succeed)

**Deliverables:**
- ElevenLabs voice clone ID
- Supabase project URL + anon key
- `.env` configured and tested

---

### [WEEK 1] Create First 10 Knowledge Atoms (Issue #45)
**Status:** Pending (After Issue #44)
**Priority:** HIGH
**Estimated Effort:** 4-6 hours
**Assigned To:** USER

**Tasks (Wednesday-Thursday):**
- [ ] Manually create 5 electrical fundamentals atoms (voltage, current, resistance, ohms-law, power)
- [ ] Manually create 5 PLC basics atoms (what-is-plc, scan-cycle, contacts-coils, io-basics, ladder-fundamentals)
- [ ] Insert atoms into Supabase `knowledge_atoms` table
- [ ] Generate embeddings (OpenAI `text-embedding-3-small`)
- [ ] Test vector search (query "what is voltage" → returns correct atom)

**Deliverables:**
- 10 knowledge atoms (JSON format, IEEE LOM-compliant)
- Embeddings stored in pgvector
- Vector search working (> 0.8 similarity for test queries)

**Files:** `/plc/atoms/*.json` or directly in Supabase

---

### [WEEK 1] Implement Core Pydantic Models (Issue #46)
**Status:** ✅ COMPLETED
**Priority:** HIGH
**Completed:** 2025-12-10

**Deliverables:**
- ✅ `/core/models.py` (600+ lines, all schemas)
- ✅ `/core/__init__.py` (package initialization)
- ✅ `test_models.py` (validation test suite, all tests passing)

**Validation:**
```bash
poetry run python -c "from core.models import PLCAtom, RIVETAtom; print('Models OK')"
poetry run python test_models.py  # All 6 tests pass
```

---

## Upcoming (Week 2-3)

### [WEEK 2] Build Research Agent (Issue #47)
**Status:** Not Started
**Priority:** HIGH
**Estimated Effort:** 4-6 hours
**Dependencies:** Week 1 complete (Supabase setup, models implemented)

**Tasks:**
- Implement `ResearchAgent` class (`/agents/research/research_agent.py`)
- Web scraping (Crawl4AI): Siemens/AB manuals, IEEE standards
- YouTube transcript extraction (yt-dlp): RealPars, PLCGuy, AutomationDirect
- PDF processing (PyMuPDF): Extract text from vendor manuals
- Store raw data in Supabase `research_staging` table
- Implement deduplication (hash-based)

**Success Criteria:**
- 20+ sources ingested (10 web, 5 YouTube, 5 PDFs)
- Zero duplicate sources in database
- Agent runs autonomously (scheduled via APScheduler)

---

### [WEEK 2] Build Scriptwriter Agent (Issue #48)
**Status:** Not Started
**Priority:** HIGH
**Estimated Effort:** 6-8 hours
**Dependencies:** Week 1 atoms created, models implemented

**Tasks:**
- Implement `ScriptwriterAgent` class (`/agents/content/scriptwriter_agent.py`)
- Script structure template (Hook, Explanation, Example, Recap)
- Personality markers ([enthusiastic], [cautionary], [emphasis])
- Visual cues (show diagram, highlight code)
- Citation integration (cite atom sources)
- Generate 3 test scripts (from first 3 atoms)

**Success Criteria:**
- 3 video scripts generated (5-7 min each, full narration)
- All scripts cite sources (no hallucinations)
- YOU approve all 3 scripts (quality gate)

---

### [WEEK 3] Video Production Pipeline
**Status:** Not Started
**Priority:** MEDIUM
**Estimated Effort:** 12-16 hours
**Dependencies:** Week 2 complete (scripts generated)

**Tasks:**
- Build Voice Production Agent (ElevenLabs TTS)
- Build Video Assembly Agent (MoviePy + FFmpeg)
- Build Thumbnail Agent (DALLE or Canva API)
- Build YouTube Uploader Agent (YouTube Data API)
- Produce 3 videos end-to-end (from scripts)

**Success Criteria:**
- 3 videos rendered (1080p MP4)
- 3 videos uploaded to YouTube (unlisted for review)
- YOU approve video quality (set standard)

---

## Backlog (Agent Factory Core)

### [P1] Add MCP Lifespan Context
**Status:** Not Started
**Dependencies:** Settings Service
**Estimated Effort:** 2-3 hours
**Description:** Implement context management pattern from mcp-mem0 to prevent repeated resource initialization

**Reference:** `docs/cole_medin_patterns.md` Section 2.2

---

### [P2] Implement Hybrid Search
**Status:** SQL Ready
**Dependencies:** Settings Service (for toggle)
**Estimated Effort:** 4-6 hours
**Description:** Add PostgreSQL RPC function for hybrid vector + text search

**Files to Create:**
- PostgreSQL function: `hybrid_search_session_memories`
- Python wrapper: `agent_factory/memory/hybrid_search.py`
- Tests: `tests/test_hybrid_search.py`

**Reference:** `docs/archon_architecture_analysis.md` Section 3.2

---

### [P3] Add Batch Processing with Progress
**Status:** Not Started
**Dependencies:** Settings Service
**Estimated Effort:** 3-4 hours
**Description:** Batch memory operations with progress callbacks and retry logic

**Files to Create:**
- `agent_factory/memory/batch_operations.py`
- Tests: `tests/test_batch_operations.py`

**Reference:** `docs/integration_recommendations.md` Section 5

---

### [P4] Multi-Dimensional Embedding Support
**Status:** SQL Ready
**Dependencies:** None
**Estimated Effort:** 2-3 hours
**Description:** Support 768, 1024, 1536, 3072 dimension embeddings

**Note:** SQL migration already adds columns. Just need Python code to use them.

**Reference:** `docs/cole_medin_patterns.md` Section 1.3

---

### [P5] Create PRP Templates
**Status:** Not Started
**Dependencies:** None
**Estimated Effort:** 2-3 hours
**Description:** Product Requirements Prompt templates for agent creation

**Files to Create:**
- `docs/prp_templates/agent_creation.md`
- `docs/prp_templates/tool_creation.md`
- `docs/prp_templates/integration.md`

**Reference:** `docs/cole_medin_patterns.md` Section 4.1

---

## Completed

### ✅ Triune Moonshot Integration & PLC Tutor Strategy
**Completed:** 2025-12-10
**Description:** Comprehensive strategy documentation for PLC Tutor / Industrial Skills Hub launch

**Deliverables:**
- `docs/TRIUNE_STRATEGY.md` (32KB) - Complete integration (RIVET + PLC + Agent Factory), 18-agent system
- `docs/YOUTUBE_WIKI_STRATEGY.md` (17KB) - YouTube-first approach (teach to build KB, voice clone)
- `docs/AGENT_ORGANIZATION.md` (26KB) - All 18 agents with complete specs (responsibilities, tools, metrics)
- `docs/IMPLEMENTATION_ROADMAP.md` (22KB) - Week-by-week plan (12 weeks to autonomous operations)
- `plc/content/CONTENT_ROADMAP_AtoZ.md` (24KB) - 100+ video topics sequenced (electricity → AI)
- `docs/ATOM_SPEC_UNIVERSAL.md` (21KB) - Universal knowledge atom schema (IEEE LOM-based)
- `core/models.py` (600+ lines) - Production-ready Pydantic models (all data types)
- GitHub Issues #44-49 - Week 1 tasks ready to execute
- Updated `CLAUDE.md` - Integrated YouTube-Wiki strategy, 18-agent system
- Updated `TASK.md` - Week 1 priorities, upcoming work (this document)

**Key Insights:**
- YouTube IS the knowledge base (original content = zero copyright)
- Voice clone enables 24/7 autonomous production
- 18 agents handle research → script → video → publish → amplify
- Tiered approval (videos 1-20: human review, 21-50: sample, 51+: autonomous)
- Multi-stream monetization (ads, courses, B2B, DAAS)

**Timeline:**
- Week 1: Infrastructure + voice training (USER tasks)
- Week 4: Public launch (3 videos live)
- Week 12: 30 videos, 1K subs, $500 revenue, 80% autonomous
- Month 12: 100 videos, 20K subs, $5K/mo revenue, fully autonomous

**Validation:**
```bash
# Models validated
poetry run python test_models.py  # All 6 tests pass

# Strategy docs created
ls docs/TRIUNE_STRATEGY.md docs/YOUTUBE_WIKI_STRATEGY.md docs/AGENT_ORGANIZATION.md \
   docs/IMPLEMENTATION_ROADMAP.md docs/ATOM_SPEC_UNIVERSAL.md \
   plc/content/CONTENT_ROADMAP_AtoZ.md core/models.py  # All exist
```

**Impact:** Complete strategic foundation for PLC Tutor autonomous content production system. Ready for Week 1 execution.

---

### ✅ Memory System Consolidation
**Completed:** 2025-12-09
**Description:** Resolved import conflicts and consolidated memory system into single coherent API

**What Was Fixed:**
- Added `SupabaseMemoryStorage` to `agent_factory/memory/__init__.py` exports
- Fixed SupabaseMemoryStorage upsert constraint issue (delete-then-insert pattern)
- Fixed ContextManager test assertions
- All 6 memory tests passing (imports, 3 storage backends, context manager, lifecycle)

**Deliverables:**
- `test_memory_consolidated.py` - Comprehensive test suite (6 tests, all passing)
- `examples/memory_demo.py` - 5 demos showing complete API usage
- Updated `agent_factory/memory/storage.py` - Fixed metadata upsert logic

**Validation:**
```bash
poetry run python test_memory_consolidated.py  # All 6 tests pass
poetry run python examples/memory_demo.py      # All 5 demos work
```

**Impact:** Memory system now has clear, working API with 3 storage backends (InMemory, SQLite, Supabase)

---

### ✅ Cole Medin Research Complete
**Completed:** 2025-12-09
**Description:** Analyzed Archon (13.4k⭐), context-engineering-intro (11.8k⭐), mcp-mem0

**Deliverables:**
- `docs/cole_medin_patterns.md` - 6,000+ words, 9 sections
- `docs/archon_architecture_analysis.md` - 7,000+ words, deep architecture dive
- `docs/integration_recommendations.md` - 8,000+ words, prioritized roadmap

**Key Findings:**
- Hybrid search improves recall 15-30%
- Settings-driven features enable A/B testing
- Multi-dimensional embeddings future-proof model migrations
- Batch processing improves UX for long operations

---

### ✅ Supabase Memory Storage
**Completed:** 2025-12-08
**Description:** Implemented fast Supabase storage for memory atoms

**Performance:** 60-120x faster than file-based storage
**Files:**
- `agent_factory/memory/storage.py`
- `agent_factory/memory/history.py`
- `agent_factory/memory/context_manager.py`

---

## Discovered During Work

### Document Settings Service Usage Patterns
**Found During:** Settings Service implementation
**Description:** Need clear examples of when to use settings vs environment variables
**Priority:** P2

### Add Settings API Endpoints
**Found During:** Planning Phase
**Description:** REST API to update settings at runtime (optional, for future SaaS platform)
**Priority:** P4

---

## Notes

- **Always mark tasks as completed** immediately after finishing
- **Add new tasks** discovered during work to "Discovered During Work" section
- **Update validation commands** after testing features
- **Reference documentation** using relative paths to docs/

---

## Task Management Rules

From `CLAUDE.md`:
- Check TASK.md before starting new tasks
- Mark completed tasks immediately - update status from "In Progress" to "Completed"
- Add discovered tasks to "Discovered During Work" section with context
- Update validation commands after testing features
- Keep TASK.md as single source of truth for active work
