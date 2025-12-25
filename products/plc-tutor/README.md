# PLC Tutor

> AI-powered YouTube education for PLC programming

## Status
🔜 Deferred to Month 2+ (Post-SCAFFOLD launch)

**Current State:**
- ✅ 18 agents designed and partially implemented
- ✅ 1,964+ knowledge atoms indexed in Supabase
- ✅ 7-stage ingestion pipeline (LangGraph) complete
- ✅ 100+ video topics planned (A-to-Z curriculum)
- 🔄 Voice clone setup pending
- 🔄 First 3 videos pending

## Quick Start

### Load Skill Context
```bash
# In Claude Code
Skill("PLC_TUTOR")  # Load full PLC Tutor context
```

### Run Content Pipeline
```bash
# Generate video script from topic
poetry run python agents/orchestration/master_orchestrator_agent.py \
  --task generate-script \
  --topic "3-Wire Motor Control"

# Review generated script
cat data/scripts/plc-motor-control-*.md

# Generate voice narration (requires ElevenLabs API key)
poetry run python agents/media/voice_production_agent.py \
  --script data/scripts/plc-motor-control-001.md

# Assemble final video
poetry run python agents/media/video_assembly_agent.py \
  --script data/scripts/plc-motor-control-001.md \
  --voice data/audio/plc-motor-control-001.mp3
```

### Ingest New Knowledge Sources
```bash
# Single PDF ingestion
poetry run python agent_factory/workflows/ingestion_chain.py \
  --url "https://literature.rockwellautomation.com/manual.pdf" \
  --source-type pdf

# Batch ingestion (17 curated PDFs)
poetry run python scripts/knowledge/batch_ingest.py \
  --urls-file scripts/kb_seed_urls.py

# YouTube transcript extraction
poetry run python agent_factory/workflows/ingestion_chain.py \
  --url "https://youtube.com/watch?v=abc123" \
  --source-type youtube
```

### Query Knowledge Base
```bash
# Keyword search
poetry run python -c "
from agents.content.scriptwriter_agent import ScriptwriterAgent
agent = ScriptwriterAgent()
atoms = agent.query_vps_atoms('ControlLogix motor control', limit=5)
print(atoms)
"

# Semantic search (uses embeddings)
poetry run python scripts/knowledge/test_semantic_search.py \
  --query "How to troubleshoot timer instructions"
```

## Architecture

### Skill Definition
- **Location**: `.claude/Skills/PLC_TUTOR/SKILL.md`
- **18 Agents**: Executive (2), Research (4), Content (5), Media (4), Engagement (3)
- **2 Workflows**: Content Pipeline + Ingestion Pipeline
- **Data Models**: PLCAtom (Pydantic), VideoScript, LearningObject

### Agent Locations
```
agents/
├── orchestration/
│   └── master_orchestrator_agent.py      # 24/7 coordinator
├── executive/
│   ├── ai_ceo_agent.py                   # Strategy, metrics, KPIs
│   └── ai_chief_of_staff_agent.py        # Project management
├── research/
│   ├── research_agent.py                 # Web/PDF/YouTube scraping
│   ├── atom_builder_agent.py             # Raw data → Pydantic
│   ├── atom_librarian_agent.py           # Organize atoms
│   └── oem_pdf_scraper_agent.py          # Vendor manual scraping
├── knowledge/
│   ├── quality_checker_agent.py          # 5-dimension validation
│   └── citation_validator_agent.py       # Citation verification
├── content/
│   ├── content_curator_agent.py          # Topic selection
│   ├── scriptwriter_agent.py             # Atom → video script
│   ├── instructional_designer_agent.py   # Pedagogical structure
│   ├── seo_agent.py                      # Keyword research
│   └── trend_scout_agent.py              # Analyze top videos
├── media/
│   ├── voice_production_agent.py         # ElevenLabs narration
│   ├── video_assembly_agent.py           # FFmpeg rendering
│   ├── thumbnail_agent.py                # Eye-catching thumbnails
│   └── youtube_uploader_agent.py         # YouTube API publishing
└── engagement/
    ├── community_agent.py                # Comment moderation
    ├── analytics_agent.py                # Metrics tracking
    └── social_amplifier_agent.py         # TikTok/Instagram clips
```

### Workflow Files
```
agent_factory/workflows/
├── ingestion_chain.py                    # 7-stage LangGraph pipeline
├── graph_orchestrator.py                 # Multi-agent routing
├── collaboration_patterns.py             # Agent coordination
└── shared_memory.py                      # Cross-agent memory
```

### Content & Docs
```
plc/content/
└── CONTENT_ROADMAP_AtoZ.md               # 100+ video topics

docs/architecture/
├── AGENT_ORGANIZATION.md                 # 18-agent system specs
├── ATOM_SPEC_UNIVERSAL.md                # IEEE LOM schema
└── TRIUNE_STRATEGY.md                    # RIVET + PLC integration

docs/implementation/
├── YOUTUBE_WIKI_STRATEGY.md              # Build knowledge BY teaching
└── IMPLEMENTATION_ROADMAP.md             # Week-by-week roadmap
```

## Knowledge Base

### Current State
- **1,964+ atoms** indexed in Supabase
- **Vendors**: Allen-Bradley, Siemens, Mitsubishi, Omron, Schneider
- **Types**: Concepts, patterns, procedures, troubleshooting
- **Vector search**: <100ms queries via OpenAI embeddings

### Schema
```python
from core.models import PLCAtom

atom = PLCAtom(
    atom_id="plc:ab:motor-start-stop",
    type="pattern",
    vendor="allen_bradley",
    platform="control_logix",
    title="3-Wire Motor Start/Stop/Seal-In",
    inputs=[{"tag": "Start_PB", "type": "NO_contact", "address": "I:0/0"}],
    outputs=[{"tag": "Motor_Contactor", "type": "coil", "address": "O:0/0"}],
    logic_description="Parallel seal-in circuit with stop button in series",
    steps=["Press Start_PB → Motor_Contactor energizes", "..."],
    difficulty="beginner",
    prereqs=["plc:generic:io-basics"],
    source="AB ControlLogix Programming Manual Chapter 3",
    citations=["[^1]: Allen-Bradley ControlLogix Manual, pp. 45-48"],
    safety_level="info"
)
```

### VPS KB Factory (Hostinger)
**24/7 ingestion pipeline running on cloud VPS**

- **VPS IP**: `72.60.175.144`
- **Services**: PostgreSQL + pgvector, Redis, Ollama (deepseek-r1:1.5b), RIVET worker
- **Ingestion**: Hourly job scheduling, automatic PDF processing
- **Query from agents**: See `agents/content/scriptwriter_agent.py` for VPS integration

## Production Metrics

### Content Pipeline
- **Target**: 3 videos/day (90 videos/month)
- **Agent Schedule**:
  - ContentCuratorAgent: Daily 00:00 UTC (topic selection)
  - ScriptwriterAgent: Every 4 hours (script generation)
  - VoiceProductionAgent: After script approval
  - YouTubeUploaderAgent: Daily 12:00 UTC (batch upload)

### Cost Optimization
- **LLM Router**: 73% cost reduction ($750/mo → $198/mo)
- **Ingestion**: $0.18 per 1,000 sources
- **Embeddings**: $0.02 per 1M tokens
- **Total**: <$300/month for full autonomous operation

### Quality Targets
- Script approval rate: >90%
- Video quality score: >8/10 average
- Viewer retention: >60% at 3-min mark
- Comment sentiment: >80% positive

### Revenue Targets
- **Week 12**: 30 videos, 1K subs, $500 revenue, 80% autonomous
- **Month 12**: 100 videos, 20K subs, $5K/mo revenue, fully autonomous
- **Year 3**: $2.5M ARR (sustainable business)

## YouTube-Wiki Strategy

**Philosophy**: Build knowledge BY teaching (not scraping THEN teaching)

**Quality Gates**:
- Videos 1-20: Human approval on every one (set quality standard)
- Videos 21-50: Human sample every 3rd (quality gates)
- Videos 51+: Agents autonomous (exception flagging only)

**Content Format**:
- 5-12 minute videos (YouTube long-form)
- 30-60 second clips (TikTok, Instagram, LinkedIn)
- Structured as modules → courses → playlists

## Curriculum (100+ Topics)

### Track A: Electrical Fundamentals (Videos 1-20)
- Module 1: Electricity Basics (V/I/R, Ohm's law, power, AC vs DC)
- Module 2: Safety & Components (LOTO, sensors, actuators)
- Module 3: Industrial Control (relays, contactors, motor control)

### Track B: PLC Fundamentals (Videos 21-50)
- Module 4: PLC Basics (what is PLC, scan cycle, I/O addressing)
- Module 5: Ladder Logic (XIC/XIO/OTE, timers, counters)
- Module 6: Advanced Programming (sequencers, data handling)

### Track C: Platform-Specific (Videos 51-80)
- Module 7: Allen-Bradley ControlLogix
- Module 8: Siemens TIA Portal / S7-1200/1500
- Module 9: CODESYS (OpenPLC)

### Track D: Advanced Topics (Videos 81-100+)
- Module 10: Industrial Networks (Ethernet/IP, Profinet, Modbus)
- Module 11: HMI/SCADA Integration
- Module 12: Troubleshooting & Maintenance
- Module 13: AI-Augmented Automation

Full roadmap: `plc/content/CONTENT_ROADMAP_AtoZ.md`

## Integration with Other Products

### Shared with RIVET Industrial
- Knowledge Atom Standard (IEEE LOM)
- Supabase backend (multi-tenant schema)
- Citation validation (Perplexity-style)
- Quality validation pipeline

### Shared with RESEARCH Skill
- ResearchAgent feeds ingestion pipeline
- AtomBuilderAgent creates PLCAtoms
- QualityCheckerAgent validates all atoms
- CitationValidatorAgent checks sources

## Development

### Environment Setup
```bash
# Install dependencies
poetry install

# Setup .env file
cp .env.example .env
# Edit .env with API keys: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, ELEVENLABS_API_KEY

# Initialize Supabase schema
# Run SQL from: docs/database/supabase_complete_schema.sql

# Test agent imports
poetry run python -c "from agents.content.scriptwriter_agent import ScriptwriterAgent; print('OK')"
```

### Testing
```bash
# Test ingestion pipeline
poetry run python agent_factory/workflows/ingestion_chain.py --test

# Test scriptwriter agent
poetry run python -c "
from agents.content.scriptwriter_agent import ScriptwriterAgent
agent = ScriptwriterAgent()
print('Agent initialized successfully')
"

# Test knowledge base query
poetry run python scripts/knowledge/test_semantic_search.py \
  --query "PLC timer instructions"
```

## References

- **Skill Definition**: `.claude/Skills/PLC_TUTOR/SKILL.md`
- **Agent Specs**: `docs/architecture/AGENT_ORGANIZATION.md`
- **Content Strategy**: `docs/implementation/YOUTUBE_WIKI_STRATEGY.md`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`
- **Roadmap**: `docs/implementation/IMPLEMENTATION_ROADMAP.md`
- **Product Backlog**: `products/plc-tutor/backlog.md`

## Support

For questions or issues:
1. Check skill context: `Skill("PLC_TUTOR")`
2. Read agent specs: `docs/architecture/AGENT_ORGANIZATION.md`
3. Review backlog: `products/plc-tutor/backlog.md`
