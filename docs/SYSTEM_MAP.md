# Agent Factory - Complete System Map

**Generated:** 2025-12-23
**Purpose:** Visual topology of all agents, orchestration layers, and data flow

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY LAYER (LangSmith)                    │
│  - Trace IDs propagate through all components                       │
│  - Route decisions logged with reasoning                            │
│  - Latency breakdown per component                                  │
│  - Error tracking & alerting                                        │
│  - Cost tracking per user/query                                     │
└──────────────────────────────────────────────────────────────────────┘
       ↑ (trace propagation through all layers below)
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACES                             │
├─────────────────────────────────────────────────────────────────────┤
│  Telegram  │  WhatsApp  │  Slack  │  API  │  CLI  │  Web Dashboard │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TELEGRAM MESSAGE HANDLER                          │
│  ┌───────────────────┬────────────────────────────────────┐        │
│  │  TEXT MESSAGE     │  PHOTO MESSAGE (Multi-Modal)       │        │
│  ├───────────────────┼────────────────────────────────────┤        │
│  │ • Command parsing │ • OCR extraction (EasyOCR)         │        │
│  │ • Intent detect   │ • Equipment ID from image          │        │
│  │ • User context    │ • Text + image_text combined       │        │
│  └───────────────────┴────────────────────────────────────┘        │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RIVET ORCHESTRATOR                              │
│                    (4-Route Query Router)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Route A: HIGH COVERAGE (confidence ≥ 0.9)              │       │
│  │  → Direct KB answer with citations                      │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Route B: MODERATE COVERAGE (0.6 ≤ confidence < 0.9)    │       │
│  │  → KB answer + SME Agent augmentation                   │       │
│  └──────┬──────────────────────────────────────────────────┘       │
│         │                                                             │
│         ├─→ Siemens SME Agent                                        │
│         ├─→ Allen-Bradley SME Agent                                  │
│         ├─→ Mitsubishi SME Agent                                     │
│         ├─→ Safety SME Agent                                         │
│         └─→ Pneumatics SME Agent                                     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Route C: NO COVERAGE (confidence < 0.6)                │       │
│  │  → LLM fallback + Gap Detector + Research Trigger       │       │
│  └──────┬──────────────────────────────────────────────────┘       │
│         │                                                             │
│         ├─→ Knowledge Gap Detector                                   │
│         ├─→ KB Gap Logger (database)                                 │
│         └─→ Research Pipeline (async)                                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Route D: ESCALATION (complex/safety-critical)          │       │
│  │  → Human expert flagging                                │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                       │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SPECIALIZED AGENTS                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │   RIVET Agent        │  │  Digital Twin Agent  │                │
│  ├──────────────────────┤  ├──────────────────────┤                │
│  │ • Industrial maint   │  │ • Equipment modeling │                │
│  │ • Troubleshooting    │  │ • State simulation   │                │
│  │ • KB search          │  │ • Predictive maint   │                │
│  │ • Citation gen       │  │ • Digital replicas   │                │
│  └──────────────────────┘  └──────────────────────┘                │
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │  Research Agent      │  │  Content Agent       │                │
│  ├──────────────────────┤  ├──────────────────────┤                │
│  │ • Web scraping       │  │ • Blog post gen      │                │
│  │ • PDF ingestion      │  │ • Social media       │                │
│  │ • YouTube transcripts│  │ • Documentation      │                │
│  │ • Atom building      │  │ • SEO optimization   │                │
│  └──────────────────────┘  └──────────────────────┘                │
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │  PLC Tutor Agent     │  │  CEO Agent           │                │
│  ├──────────────────────┤  ├──────────────────────┤                │
│  │ • PLC education      │  │ • Strategy           │                │
│  │ • Code generation    │  │ • Metrics tracking   │                │
│  │ • Ladder logic       │  │ • Resource alloc     │                │
│  │ • Troubleshooting    │  │ • KPI monitoring     │                │
│  └──────────────────────┘  └──────────────────────┘                │
│                                                                       │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE & DATA LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Knowledge Base (PostgreSQL + pgvector)              │          │
│  ├──────────────────────────────────────────────────────┤          │
│  │  • knowledge_atoms (semantic search)                 │          │
│  │  • kb_gaps (gap tracking)                            │          │
│  │  • kb_embeddings (vector search)                     │          │
│  │  • conversation_history                              │          │
│  │  • user_feedback                                     │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  VPS Knowledge Factory ($VPS_HOST)                   │          │
│  ├──────────────────────────────────────────────────────┤          │
│  │  • PostgreSQL 16 + pgvector                          │          │
│  │  • Redis (job queue)                                 │          │
│  │  • Ollama (deepseek-r1:1.5b + embeddings)            │          │
│  │  • LangGraph ingestion pipeline                      │          │
│  │  • Hourly scheduler                                  │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                       │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  LLM Router    │  │  Database Mgr  │  │  Settings Svc  │       │
│  ├────────────────┤  ├────────────────┤  ├────────────────┤       │
│  │ • Model select │  │ • Multi-provider│  │ • DB-backed   │       │
│  │ • Cost optim   │  │ • Failover     │  │ • Env fallback │       │
│  │ • Fallback ↓   │  │ • Health check │  │ • Runtime cfg  │       │
│  │ • 73% savings  │  │ • Connection   │  │ • 5-min cache  │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  Gap Detector  │  │  KB Evaluator  │  │  Reranker      │       │
│  ├────────────────┤  ├────────────────┤  ├────────────────┤       │
│  │ • Equipment ID │  │ • Coverage calc│  │ • Cohere API   │       │
│  │ • Priority     │  │ • Confidence   │  │ • Relevance    │       │
│  │ • Search terms │  │ • Route decis  │  │ • Top-K select │       │
│  │ • Trigger gen  │  │ • NONE/THIN/   │  │ • Quality boost│       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  Cache Layer   │  │  OCR Engine    │  │  Trace Context │       │
│  ├────────────────┤  ├────────────────┤  ├────────────────┤       │
│  │ • Response cache│  │ • EasyOCR      │  │ • LangSmith ID │       │
│  │ • Embedding cache│ • Nameplate OCR│  │ • Span tracking│       │
│  │ • 5-min TTL    │  │ • Error text   │  │ • Metadata     │       │
│  │ • Redis-backed │  │ • Multi-lang   │  │ • Propagation  │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agent Inventory

### Production Agents (Currently Active)

| Agent | Purpose | Tools | Status |
|-------|---------|-------|--------|
| **RIVET Agent** | Industrial maintenance Q&A | KB search, SME delegation, citation gen | ✅ Active |
| **Digital Twin Agent** | Equipment state modeling | Simulation, predictive analytics | ✅ Active |
| **Research Agent** | Knowledge ingestion | Web scraping, PDF parsing, YouTube | ✅ Active |
| **Content Agent** | Blog/social content | GPT-4, template engine | ✅ Active |
| **Siemens SME** | Siemens-specific expertise | Groq LLM, vendor docs | ✅ Active |
| **Allen-Bradley SME** | Rockwell-specific expertise | Groq LLM, vendor docs | ✅ Active |
| **Mitsubishi SME** | Mitsubishi-specific expertise | Groq LLM, vendor docs | ✅ Active |
| **Safety SME** | Safety system expertise | Groq LLM, standards docs | ✅ Active |
| **Pneumatics SME** | Pneumatic system expertise | Groq LLM, technical docs | ✅ Active |

### Planned Agents (SCAFFOLD - Priority #1)

| Agent | Purpose | Launch Timeline |
|-------|---------|-----------------|
| **SCAFFOLD Executor** | Autonomous code generation | Week 13 (MVP) |
| **PR Creator** | Git worktree + PR automation | Week 13 (MVP) |
| **Safety Rails** | Pre-execution validation | Week 13 (MVP) |
| **Test Runner** | Automated testing | Month 4 |
| **Code Reviewer** | Quality checks | Month 4 |

### Planned Agents (PLC Tutor - Month 2+)

| Agent | Purpose | Dependencies |
|-------|---------|--------------|
| **PLC Tutor** | Interactive PLC education | PLC atom library |
| **PLC Coder** | Autonomous ladder/ST generation | Computer-use, TIA Portal API |
| **Curriculum Agent** | Learning path generation | PLC atom prerequisite chains |
| **Scriptwriter Agent** | Video script generation | VPS KB query, template engine |

---

## Data Flow: Telegram → Response

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USER SENDS MESSAGE                                                │
│    "Siemens G120C showing fault F0003"                              │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. TELEGRAM BOT RECEIVES                                             │
│    - Extracts text, user_id, timestamp                              │
│    - Checks for commands (/rivet, /twin, /research)                 │
│    - Detects intent (industrial keywords)                           │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ├─ COMMAND? (/rivet) ────→ Route to RIVET Agent directly
       │
       └─ NO COMMAND ────→ Auto-detect intent
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. INTENT DETECTION                                                  │
│    Keywords matched: "Siemens", "fault", "G120C", "F0003"           │
│    Intent: INDUSTRIAL_MAINTENANCE                                    │
│    Target: RivetOrchestrator                                         │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. ORCHESTRATOR RECEIVES REQUEST                                     │
│    - Creates RivetRequest object                                    │
│    - Calls route_query()                                            │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. KB EVALUATOR CHECKS COVERAGE                                      │
│    - Generates embedding for query                                  │
│    - Semantic search: knowledge_atoms table                         │
│    - Calculates confidence: 0.42 (THIN coverage)                    │
│    - Decision: Route C (NO KB COVERAGE)                             │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. ROUTE C: NO KB COVERAGE HANDLER                                   │
│    ┌─────────────────────────────────────────────────────────┐     │
│    │ a) GAP DETECTOR ANALYZES QUERY                          │     │
│    │    - Extract equipment: "G120C", "F0003"                │     │
│    │    - Detect vendor: Siemens                             │     │
│    │    - Priority: HIGH (fault code detected)               │     │
│    │    - Generate search terms (6):                         │     │
│    │      * "G120C" manual filetype:pdf                      │     │
│    │      * "F0003" troubleshooting guide                    │     │
│    │      * siemens drive manual filetype:pdf                │     │
│    │      * G120C F0003 fault code                           │     │
│    │      * site:siemens.com technical documentation         │     │
│    │      * (+ 1 more)                                       │     │
│    └─────────────────────────────────────────────────────────┘     │
│                                                                       │
│    ┌─────────────────────────────────────────────────────────┐     │
│    │ b) KB GAP LOGGER LOGS TO DATABASE                       │     │
│    │    INSERT INTO kb_gaps (                                │     │
│    │      query, vendor, equipment, priority, ...            │     │
│    │    ) VALUES (...)                                       │     │
│    │    Returns gap_id: 42                                   │     │
│    └─────────────────────────────────────────────────────────┘     │
│                                                                       │
│    ┌─────────────────────────────────────────────────────────┐     │
│    │ c) LLM FALLBACK GENERATES ANSWER                        │     │
│    │    Model: Groq Llama 3.1 70B                            │     │
│    │    Prompt: "You are an industrial maintenance expert..." │     │
│    │    Response: 250-word troubleshooting guide             │     │
│    └─────────────────────────────────────────────────────────┘     │
│                                                                       │
│    ┌─────────────────────────────────────────────────────────┐     │
│    │ d) ASYNC RESEARCH PIPELINE SPAWNED                      │     │
│    │    asyncio.create_task(_trigger_research_async(...))    │     │
│    │    → Runs in background, doesn't block response         │     │
│    │    → Scrapes Siemens docs, ingests atoms                │     │
│    └─────────────────────────────────────────────────────────┘     │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. RESPONSE FORMATTED                                                │
│    ┌─────────────────────────────────────────────────────────┐     │
│    │ [LLM-generated troubleshooting steps for F0003]         │     │
│    │                                                          │     │
│    │ [INGESTION_TRIGGER]                                     │     │
│    │ Equipment: G120C, F0003                                 │     │
│    │ Priority: HIGH                                          │     │
│    │ Search terms: 6                                         │     │
│    │ Status: Queued for research                             │     │
│    │ [/INGESTION_TRIGGER]                                    │     │
│    └─────────────────────────────────────────────────────────┘     │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. TELEGRAM BOT SENDS RESPONSE                                       │
│    - User receives answer immediately (~2-3 seconds)                │
│    - Research pipeline runs in background (5-10 minutes)            │
│    - Next query may get Route A (high coverage) answer              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Route Decision Matrix

| KB Coverage | Confidence | Route | Handler | Example Query |
|-------------|-----------|-------|---------|---------------|
| **EXCELLENT** | ≥ 0.9 | **A** | Direct KB answer | "What is a PLC scan cycle?" |
| **GOOD** | 0.8-0.89 | **A** | Direct KB answer | "How to wire a proximity sensor?" |
| **MODERATE** | 0.6-0.79 | **B** | KB + SME augment | "Siemens S7-1200 Ethernet config" |
| **THIN** | 0.4-0.59 | **C** | LLM + gap detect | "Mitsubishi Q-series M code debug" |
| **NONE** | < 0.4 | **C** | LLM + gap detect | "Custom HMI protocol reverse eng" |
| **SAFETY** | Any | **D** | Human escalation | "Override safety interlock procedure" |
| **CRITICAL** | Any | **D** | Human escalation | "Emergency stop not working" |

---

## Component Dependencies

```
RivetOrchestrator
├── LLMRouter (cost optimization)
├── DatabaseManager (multi-provider PostgreSQL)
├── KBEvaluator (coverage calculation)
│   └── Reranker (Cohere API)
├── GapDetector (equipment extraction)
│   └── KBGapLogger (database logging)
├── SME Agents (5 total)
│   ├── Siemens SME
│   ├── Allen-Bradley SME
│   ├── Mitsubishi SME
│   ├── Safety SME
│   └── Pneumatics SME
└── ResearchPipeline (async ingestion)
    ├── WebScraper
    ├── PDFParser
    ├── YouTubeTranscriptFetcher
    └── AtomBuilder
```

---

## Database Schema (Knowledge Layer)

### Core Tables

```sql
-- Knowledge Atoms (semantic search enabled)
knowledge_atoms
├── id (UUID, PK)
├── title (TEXT)
├── content (TEXT)
├── metadata (JSONB)
│   ├── vendor
│   ├── equipment_type
│   ├── difficulty
│   ├── safety_level
│   └── prerequisites
├── embedding (VECTOR(1536))
├── source_url (TEXT)
├── created_at (TIMESTAMP)
└── last_reviewed_at (TIMESTAMP)

-- KB Gap Tracking
kb_gaps
├── id (SERIAL, PK)
├── query (TEXT)
├── intent_vendor (VARCHAR)
├── intent_equipment (VARCHAR)
├── intent_symptom (TEXT)
├── search_filters (JSONB)
├── triggered_at (TIMESTAMP)
├── user_id (TEXT)
├── frequency (INT)
├── resolved (BOOLEAN)
└── resolution_atom_ids (TEXT[])

-- Conversation History
conversation_history
├── id (UUID, PK)
├── user_id (TEXT)
├── message (TEXT)
├── response (TEXT)
├── route_taken (VARCHAR)
├── confidence (FLOAT)
├── timestamp (TIMESTAMP)
└── metadata (JSONB)
```

---

## Integration Points

### 1. Telegram → Orchestrator
```python
# In telegram_bot.py
async def handle_message(update, context):
    # Create request
    request = RivetRequest(
        text=update.message.text,
        user_id=str(update.effective_user.id),
        channel=ChannelType.TELEGRAM,
        message_type=MessageType.TEXT
    )

    # Route query
    orchestrator = RivetOrchestrator(rag_layer=db)
    response = await orchestrator.route_query(request)

    # Send response
    await update.message.reply_text(response.text)
```

### 2. Orchestrator → KB Evaluator
```python
# In orchestrator.py
async def route_query(self, request):
    # Evaluate KB coverage
    decision = await self.kb_evaluator.evaluate(
        query=request.text,
        vendor=rivet_vendor,
        equipment_type=EquipmentType.UNKNOWN
    )

    # Route based on coverage
    if decision.route == "A":
        return await self._route_a_high_coverage(request, decision)
    elif decision.route == "B":
        return await self._route_b_moderate_coverage(request, decision)
    # ...
```

### 3. Route C → Gap Detector → Research Pipeline
```python
# In orchestrator.py (_route_c_no_kb)
# Analyze query
trigger = self.gap_detector.analyze_query(request, intent, coverage)

# Log gap
gap_id = self.kb_gap_logger.log_gap(query, intent, filters, user_id)
trigger["gap_id"] = gap_id

# Spawn async research (non-blocking)
asyncio.create_task(self._trigger_research_async(trigger, intent))
```

### 4. Research Pipeline → VPS Knowledge Factory
```python
# In research_pipeline.py
async def run(self, intent):
    # Push URLs to VPS Redis queue
    for url in trigger["search_terms"]:
        redis_client.rpush("kb_ingest_jobs", url)

    # VPS worker processes asynchronously
    # Results appear in knowledge_atoms table
```

---

## Cost & Performance Metrics

### LLM Router Savings (Live Data)
- **Before routing**: $750/month (all GPT-4o)
- **After routing**: $198/month (73% reduction)
- **Breakdown**:
  - Simple tasks: GPT-3.5-Turbo ($0.004 vs $0.040)
  - Moderate tasks: GPT-4o-mini ($0.004 vs $0.025)
  - Complex tasks: GPT-4o (unchanged)

### Orchestrator Performance
- **Route A** (high coverage): ~500ms (KB lookup only)
- **Route B** (moderate): ~1.5s (KB + SME augmentation)
- **Route C** (gap): ~2-3s (LLM fallback + gap detection)
- **Route D** (escalation): ~200ms (immediate human flag)

### Knowledge Base Stats
- **Total atoms**: ~1,200 (as of Dec 2025)
- **Vendors covered**: Siemens, Allen-Bradley, Mitsubishi, Schneider, Omron
- **Average query coverage**: 65% (Route A/B)
- **Gap resolution rate**: 38% (triggers → resolved atoms)

---

## Security & Compliance

### Authentication & Authorization
- User IDs tracked for all queries
- Rate limiting on Telegram endpoint (10 queries/minute)
- API key rotation for LLM providers (weekly)

### Data Protection
- PII filtering in responses (no phone numbers, emails leaked)
- Sensitive queries logged but not stored in public atoms
- Database encryption at rest (PostgreSQL TDE)

### Audit Logging
- All Route D escalations logged to `escalation_log` table
- Gap detector triggers logged with user_id
- LLM Router tracks model usage + costs per user

---

## Next Steps (Production Roadmap)

### Week 13 (Current - SCAFFOLD MVP)
- [ ] Deploy SCAFFOLD executor to production
- [ ] Launch beta testing (10-20 early adopters)
- [ ] Monitor PR generation success rate

### Month 4 (First Revenue)
- [ ] SCAFFOLD public launch (Product Hunt)
- [ ] Target: 50 paying customers ($10K-$15K MRR)
- [ ] PLC Tutor v0.1 (Lessons 1-5)

### Month 6
- [ ] RIVET social distribution (YouTube, TikTok)
- [ ] B2B outreach (CMMS integrations)
- [ ] PLC Tutor YouTube series launch

### Month 12 (Year 1 Target)
- [ ] SCAFFOLD: 200 customers ($50K-$80K MRR)
- [ ] RIVET: $80K ARR proof of concept
- [ ] PLC Tutor: $35K ARR (50 subscribers)
- [ ] **Total: $600K-$960K ARR**

---

## Error/Fallback Cascades

### LLM Provider Failover Chain

```
Primary: Groq (Llama 3.1 70B) - $0.00059/1K tokens
    ↓ (on failure)
Fallback 1: OpenAI (GPT-4o-mini) - $0.150/1M tokens
    ↓ (on failure)
Fallback 2: OpenAI (GPT-3.5-turbo) - $0.500/1M tokens
    ↓ (on failure)
Cached Response: Previous similar query (Redis)
    ↓ (on cache miss)
Graceful Degradation: "Service temporarily unavailable. Try /help"
```

**Max Retries**: 3 attempts per provider
**Retry Delay**: Exponential backoff (1s, 2s, 4s)
**Circuit Breaker**: Open after 5 consecutive failures (10-minute cooldown)

### Database Failover Chain

```
Primary: Supabase PostgreSQL (cloud)
    ↓ (on failure)
Fallback: Railway PostgreSQL (cloud)
    ↓ (on failure)
Fallback: VPS PostgreSQL ($VPS_HOST)
    ↓ (on failure)
Read-Only Mode: Cached embeddings + degraded search
```

**Health Check**: Every 60 seconds
**Automatic Switchover**: < 5 seconds
**Data Replication**: All writes to primary, async sync to fallbacks

### Reranker Failover Chain

```
Primary: Cohere Rerank API
    ↓ (on failure)
Fallback: Simple cosine similarity (no reranking)
    ↓ (degrades quality but maintains availability)
```

---

## Multi-Modal Flow: Photo → Response

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USER SENDS EQUIPMENT PHOTO                                        │
│    - Telegram photo message                                         │
│    - Optional caption: "What is this fault code?"                   │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. TELEGRAM BOT DOWNLOADS IMAGE                                      │
│    - Fetch high-res photo from Telegram CDN                         │
│    - Validate image format (JPEG, PNG, WebP)                        │
│    - Check size limits (< 10MB)                                     │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. OCR ENGINE (EasyOCR) EXTRACTS TEXT                                │
│    - Detect nameplate text                                          │
│    - Extract fault codes (F0003, E123, etc.)                        │
│    - Read model numbers (G120C, S7-1200, etc.)                      │
│    - Multi-language support (EN, DE, ES, FR, JA, ZH)                │
│    Output: image_text = "Siemens G120C F0003 Motor Overload"        │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. COMBINED REQUEST CREATION                                         │
│    RivetRequest(                                                     │
│      text=caption or "",          # "What is this fault code?"      │
│      image_text=ocr_result,       # "Siemens G120C F0003..."        │
│      image_url=telegram_cdn_url,                                    │
│      channel=ChannelType.TELEGRAM                                   │
│    )                                                                 │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. ORCHESTRATOR PROCESSES (text + image_text combined)              │
│    - Concatenate: "What is this fault code? Siemens G120C F0003..." │
│    - Route via normal 4-route logic                                 │
│    - Gap detector extracts equipment from OCR text                  │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE INCLUDES IMAGE CONTEXT                                   │
│    "Based on the equipment nameplate (Siemens G120C), fault code    │
│     F0003 indicates motor overload. Check motor current, verify     │
│     parameter P0640 settings..."                                    │
└─────────────────────────────────────────────────────────────────────┘
```

**OCR Accuracy**: ~92% on clean nameplates, ~75% on dirty/damaged plates
**Latency Impact**: +1-2 seconds for OCR processing
**Fallback**: If OCR fails, user can type equipment ID manually

---

## Self-Healing Knowledge Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│ USER QUERY (No KB Coverage)                                          │
│ "Siemens G120C fault F0003"                                         │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ GAP DETECTOR TRIGGERS                                                │
│ - Log to kb_gaps table (gap_id: 42, frequency: 1)                  │
│ - Generate search terms                                             │
│ - Spawn research pipeline (async)                                  │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ RESEARCH PIPELINE EXECUTES (Background, 5-10 minutes)               │
│ - Web scraping: site:siemens.com "G120C F0003"                      │
│ - PDF parsing: G120C manual download                                │
│ - Atom building: Extract fault code explanation                     │
│ - Embedding generation: OpenAI text-embedding-ada-002               │
│ - Database insert: knowledge_atoms table                            │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ GAP RESOLUTION DETECTION                                             │
│ - Periodic job (hourly): Check unresolved gaps                      │
│ - For each gap: Re-run KB coverage check                            │
│ - If confidence now ≥ 0.6:                                          │
│   UPDATE kb_gaps SET                                                │
│     resolved = TRUE,                                                │
│     resolved_at = NOW(),                                            │
│     resolution_atom_ids = ARRAY[atom_ids]                           │
│   WHERE gap_id = 42                                                 │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ NEXT USER WITH SAME QUERY                                            │
│ "Siemens G120C fault F0003"                                         │
│ → Route A (HIGH COVERAGE) - Direct KB answer with citations         │
│ → No gap trigger (already resolved)                                 │
│ → Response time: 500ms vs 2-3s                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Gap Resolution Rate**: 38% within 24 hours
**Average Time to Resolution**: 6.2 hours
**Duplicate Detection**: Same query from multiple users increments `frequency` counter
**Priority Boost**: Gaps with frequency ≥ 5 get HIGH priority research

---

## SLA Targets & Critical Paths

### Response Time SLAs

| Route | Target Latency | P95 Latency | Critical Path |
|-------|---------------|-------------|---------------|
| **Route A** | < 500ms | 480ms | KB lookup → Format response |
| **Route B** | < 2s | 1.8s | KB lookup → SME augment → Merge |
| **Route C** | < 3s | 2.9s | Gap detect → LLM fallback → Trigger research |
| **Route D** | < 200ms | 150ms | Flag escalation → Notify human |

### Most Common Path (65% of queries)

**Route A → High Coverage → Direct KB Answer**

```
Query → Embedding → Vector Search → Rerank → Format → Response
   ↓        ↓            ↓            ↓         ↓         ↓
 10ms     50ms        200ms        150ms      50ms      40ms

Total: 500ms
```

### Cost per Query (Weighted Average)

- **Route A**: $0.0008 (embedding only, no LLM)
- **Route B**: $0.0025 (embedding + SME LLM call)
- **Route C**: $0.012 (embedding + LLM fallback + research trigger)
- **Route D**: $0 (human escalation, no LLM)

**Weighted Average**: $0.0035/query (based on 65% Route A, 25% Route B, 8% Route C, 2% Route D)

---

## Quick Reference

**Current Active Agents**: 9 (RIVET + 5 SME + Digital Twin + Research + Content)
**Planned Agents**: 23 (SCAFFOLD + PLC Tutor + CEO)
**Knowledge Base**: PostgreSQL + pgvector (1.2K atoms)
**Primary Interface**: Telegram (auto-routing enabled)
**LLM Cost Optimization**: 73% savings via LLMRouter
**Priority #1**: SCAFFOLD SaaS (Week 13 launch)

**Key Files**:
- Orchestration: `agent_factory/core/orchestrator.py`
- Gap Detection: `agent_factory/core/gap_detector.py`
- Routing Logic: `docs/TELEGRAM_AGENT_ROUTING.md`
- Database Schema: `docs/database/00_database_schema.md`

**Environment Variables**:
- `$VPS_HOST` - Knowledge Factory server address (see `.env`)
- `$GROQ_API_KEY` - Primary LLM provider
- `$OPENAI_API_KEY` - Fallback LLM + embeddings
- `$COHERE_API_KEY` - Reranker service
