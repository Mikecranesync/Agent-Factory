# PLC Tutor Skill

## Purpose
Autonomous YouTube content production for PLC education. Transforms knowledge atoms into educational videos with 24/7 production pipeline.

## Status
🔜 Deferred to Month 2+ (Post-SCAFFOLD launch)

## Architecture Overview

### Content Production Pipeline
```
Research → Script → Review → Voice → Video → SEO → Upload
```

### Knowledge Base
- **Storage**: Supabase with pgvector
- **Atoms Indexed**: 1,964+ (Allen-Bradley, Siemens, Mitsubishi, Omron, Schneider)
- **Vector Search**: <100ms semantic queries via OpenAI embeddings
- **Schema**: IEEE LOM-based (see `docs/architecture/ATOM_SPEC_UNIVERSAL.md`)

## Agents (18 Total)

### Executive Team (2 agents)
| Agent | Location | Function |
|-------|----------|----------|
| **MasterOrchestratorAgent** | `agents/orchestration/` | 24/7 daemon, schedules all agents, manages task queues |
| **AIChiefOfStaffAgent** | `agents/executive/` | Project management, issue tracking, KPI monitoring |

### Research & Knowledge Team (4 agents)
| Agent | Location | Function |
|-------|----------|----------|
| **ResearchAgent** | `agents/research/` | Web scraping, YouTube transcripts, PDF extraction |
| **AtomBuilderAgent** | `agents/research/` | Convert raw data → structured Pydantic models |
| **AtomLibrarianAgent** | `agents/research/` | Organize atoms, build prerequisite chains |
| **QualityCheckerAgent** | `agents/knowledge/` | Validate accuracy, safety compliance, citations |

### Content Production Team (5 agents)
| Agent | Location | Function |
|-------|----------|----------|
| **ContentCuratorAgent** | `agents/content/` | Topic selection, trend analysis |
| **ScriptwriterAgent** | `agents/content/` | Transform atoms → video scripts with personality markers |
| **InstructionalDesignerAgent** | `agents/content/` | Pedagogical structure, learning objectives |
| **SEOAgent** | `agents/content/` | Keyword research, titles, descriptions, tags |
| **TrendScoutAgent** | `agents/content/` | Analyze top videos, extract style patterns |

### Media & Publishing Team (4 agents)
| Agent | Location | Function |
|-------|----------|----------|
| **VoiceProductionAgent** | `agents/media/` | ElevenLabs voice clone, narration generation |
| **VideoAssemblyAgent** | `agents/media/` | FFmpeg rendering, sync audio + visuals |
| **ThumbnailAgent** | `agents/media/` | Eye-catching thumbnails with A/B testing |
| **YouTubeUploaderAgent** | `agents/media/` | YouTube Data API v3 publishing |

### Engagement & Analytics Team (3 agents)
| Agent | Location | Function |
|-------|----------|----------|
| **CommunityAgent** | `agents/engagement/` | Comment moderation, viewer engagement |
| **AnalyticsAgent** | `agents/engagement/` | Track metrics, detect trends, generate insights |
| **SocialAmplifierAgent** | `agents/engagement/` | Extract clips for TikTok/Instagram/LinkedIn |

## Workflows

### 1. Content Pipeline (Primary)
```python
# Triggered by MasterOrchestratorAgent
ContentCuratorAgent.select_topic()           # Daily 00:00 UTC
→ ScriptwriterAgent.generate_script()        # Every 4 hours
→ InstructionalDesignerAgent.add_pedagogy()  # Immediate
→ VideoQualityReviewerAgent.score()          # Score 0-10, approve/reject
→ VoiceProductionAgent.generate_narration()  # After approval
→ VideoAssemblyAgent.render_video()          # 1080p60, FFmpeg
→ SEOAgent.optimize_metadata()               # Titles, tags
→ YouTubeUploaderAgent.publish()             # Daily 12:00 UTC
```

### 2. Ingestion Pipeline (7 Stages)
```python
# Located in: agent_factory/workflows/ingestion_chain.py
# Built with: LangGraph StateGraph

Stage 1: Source Acquisition       # Download PDFs, fetch transcripts
Stage 2: Content Extraction        # Parse text, preserve structure
Stage 3: Semantic Chunking         # 200-400 word coherent chunks
Stage 4: Atom Generation           # LLM → Pydantic models
Stage 5: Quality Validation        # 5-dimension scoring
Stage 6: Embedding Generation      # OpenAI text-embedding-3-small
Stage 7: Storage & Indexing        # Supabase with deduplication

# Performance: 600 atoms/hour (parallel), $0.18/1000 sources
```

## Content Curriculum

### 100+ Video Topics (A-to-Z)
Source: `plc/content/CONTENT_ROADMAP_AtoZ.md`

**Track A: Electrical Fundamentals (Videos 1-20)**
- Module 1: Electricity Basics (what is electricity, V/I/R, Ohm's law, power, AC vs DC)
- Module 2: Safety & Components (LOTO, sensors, actuators, circuits)
- Module 3: Industrial Control (relays, contactors, motor control)

**Track B: PLC Fundamentals (Videos 21-50)**
- Module 4: PLC Basics (what is a PLC, scan cycle, I/O addressing)
- Module 5: Ladder Logic (XIC/XIO/OTE, timers, counters, patterns)
- Module 6: Advanced Programming (sequencers, data handling, diagnostics)

**Track C: Platform-Specific (Videos 51-80)**
- Module 7: Allen-Bradley ControlLogix
- Module 8: Siemens TIA Portal / S7-1200/1500
- Module 9: CODESYS (OpenPLC, CoDeSys)

**Track D: Advanced Topics (Videos 81-100+)**
- Module 10: Industrial Networks (Ethernet/IP, Profinet, Modbus)
- Module 11: HMI/SCADA Integration
- Module 12: Troubleshooting & Maintenance
- Module 13: AI-Augmented Automation

## YouTube-Wiki Strategy

**Philosophy**: Build knowledge BY teaching (not scraping THEN teaching)

**Workflow**:
1. **Learn** → Research topic from manuals
2. **Script** → AI generates teaching script
3. **Voice** → ElevenLabs voice clone narration
4. **Video** → FFmpeg assembly (5-12 min long-form)
5. **Extract** → Atom Builder extracts knowledge atom from video
6. **Amplify** → Social Amplifier creates 30-60s clips

**Quality Gates**:
- Videos 1-20: Human approval on every one (set quality standard)
- Videos 21-50: Human sample every 3rd (quality gates)
- Videos 51+: Agents autonomous (exception flagging only)

**Success Metrics**:
- Week 12: 30 videos, 1K subs, $500 revenue, 80% autonomous
- Month 12: 100 videos, 20K subs, $5K/mo revenue, fully autonomous

## Commands

### Skill Loading
```bash
Skill("PLC_TUTOR")  # Load this skill context
```

### Pipeline Commands
```bash
# Run full content pipeline for a topic
run-pipeline "3-Wire Motor Control"

# Ingest new source material
ingest-source "https://example.com/manual.pdf"

# Generate script from specific atoms
generate-script atom-123 atom-456 atom-789

# Review video quality
review-video video-042

# Check production status
status-report
```

### Development Commands
```bash
# Test scriptwriter agent
poetry run python -c "from agents.content.scriptwriter_agent import ScriptwriterAgent; print('OK')"

# Test ingestion pipeline
poetry run python agent_factory/workflows/ingestion_chain.py --test

# Run orchestrator (24/7 daemon)
poetry run python agents/orchestration/master_orchestrator_agent.py --daemon
```

## Data Models

### PLCAtom (Pydantic)
```python
from core.models import PLCAtom

atom = PLCAtom(
    atom_id="plc:ab:motor-start-stop",
    type="pattern",
    vendor="allen_bradley",
    platform="control_logix",
    title="3-Wire Motor Start/Stop/Seal-In",
    inputs=[...],
    outputs=[...],
    logic_description="Parallel seal-in circuit...",
    steps=["Press Start_PB → ...", "..."],
    difficulty="beginner",
    prereqs=["plc:generic:io-basics"],
    source="AB ControlLogix Manual Ch. 3",
    safety_level="info"
)
```

### VideoScript (Output)
```python
{
    "title": "3-Wire Motor Control Explained",
    "duration_target": "7-9 min",
    "hook": "This one pattern controls 90% of motors...",
    "sections": [
        {
            "narration": "Let's start with the start button...",
            "visual_cue": "show diagram: start_button_wiring.png",
            "personality": "[enthusiastic]"
        }
    ],
    "quiz": "What happens when you release the start button?",
    "atom_citations": ["plc:ab:motor-start-stop"]
}
```

## Key Files & Directories

```
agents/
├── orchestration/master_orchestrator_agent.py  # 24/7 coordinator
├── content/scriptwriter_agent.py               # Atom → script
├── content/video_quality_reviewer_agent.py     # Score 0-10
├── media/voice_production_agent.py             # ElevenLabs
├── media/video_assembly_agent.py               # FFmpeg
├── media/youtube_uploader_agent.py             # YouTube API
└── research/research_agent.py                  # Web/PDF/YouTube

agent_factory/workflows/
└── ingestion_chain.py                          # 7-stage LangGraph pipeline

plc/content/
└── CONTENT_ROADMAP_AtoZ.md                     # 100+ video topics

docs/architecture/
├── AGENT_ORGANIZATION.md                       # 18-agent system specs
├── ATOM_SPEC_UNIVERSAL.md                      # IEEE LOM schema
└── TRIUNE_STRATEGY.md                          # RIVET + PLC integration

core/
└── models.py                                   # Pydantic schemas (LearningObject, PLCAtom)
```

## Integration Points

### With RIVET_INDUSTRIAL
- Shared Knowledge Atom Standard (IEEE LOM)
- Shared Supabase backend (multi-tenant schema)
- Shared citation validation (Perplexity-style footnotes)

### With RESEARCH Skill
- ResearchAgent feeds ingestion pipeline
- AtomBuilderAgent uses research outputs
- QualityCheckerAgent validates all atoms

### With Agent Factory Core
- All agents use `agent_factory.core.agent_factory.AgentFactory`
- Memory storage via `agent_factory.memory.storage.SupabaseMemoryStorage`
- LLM routing via `agent_factory.llm.router.LLMRouter`

## Production Metrics

### Cost Optimization
- LLM Router: 73% cost reduction ($750/mo → $198/mo)
- Caching: 40% fewer API calls
- Batch processing: 10x throughput

### Production Targets
- **Week 4**: 3 videos live, voice clone validated
- **Week 12**: 30 videos, 1K subs, $500 revenue, agents 80% autonomous
- **Month 12**: 100 videos, 20K subs, $5K/mo revenue, fully autonomous

### Quality Metrics
- Script approval rate: >90% (after tuning)
- Video quality score: >8/10 average
- Viewer retention: >60% (3-min mark)
- Comment sentiment: >80% positive

## References

- **Agent Specs**: `docs/architecture/AGENT_ORGANIZATION.md`
- **Content Strategy**: `docs/implementation/YOUTUBE_WIKI_STRATEGY.md`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`
- **Ingestion Pipeline**: `agent_factory/workflows/ingestion_chain.py`
- **Full Roadmap**: `docs/implementation/IMPLEMENTATION_ROADMAP.md`

---

**Note**: PLC Tutor is deferred to Month 2+ (post-SCAFFOLD launch). SCAFFOLD validates the platform first.
