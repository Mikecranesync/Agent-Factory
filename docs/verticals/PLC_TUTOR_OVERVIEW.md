# The PLC Vertical (Parallel Track)

Agent Factory powers **TWO verticals** simultaneously:
1. **RIVET** - Industrial Maintenance (described above)
2. **PLC Tutor** - PLC Programming Education + Automation (NEW)

## What is PLC Tutor?

PLC Tutor is an AI-powered platform that teaches PLC programming AND evolves into an autonomous PLC coding assistant.

**For Learners:**
- Interactive AI tutor for Allen-Bradley & Siemens PLC programming
- Works with real hardware (or simulation)
- Backed by PLC knowledge atoms (no hallucinations)
- Progresses from basics → advanced → autonomous coding

**For Professionals:**
- Autonomous PLC programmer (spec → verified code)
- Uses computer-use to drive Studio 5000 / TIA Portal / CODESYS
- Proposes ladder/ST code, runs verification loops
- Human-in-loop for production deployments

**For Organizations:**
- White-label PLC tutor for trade schools, OEMs
- Pre-built curriculum with exercises
- B2B training programs

## Why PLC Tutor Matters

**1. Validates Multi-Vertical Platform:**
- Proves Agent Factory works across domains
- Same Knowledge Atom Standard, different vertical
- Same DAAS monetization pattern

**2. Faster Monetization:**
- Month 4: First paid subscribers ($29-$99/mo)
- Month 6: B2B training contracts ($10K-$20K/org)
- Year 1: ~$35K ARR (proof of concept)
- Year 3: ~$2.5M ARR (same as RIVET target)

**3. Different GTM Strategy:**
- RIVET = community-driven (Reddit, forums)
- PLC Tutor = education-driven (YouTube courses)
- Validates multiple acquisition channels

**4. Cross-Selling:**
- PLC programmers ALSO do industrial maintenance
- RIVET users may need PLC training
- Bundle pricing potential

## PLC Agents Agent Factory Must Build (18 Total)

**Executive Team (2 agents):**
1. **AICEOAgent** - Strategy, metrics, KPIs, resource allocation
2. **AIChiefOfStaffAgent** - Project management, issue tracking, orchestration

**Research & Knowledge Base Team (4 agents):**
3. **ResearchAgent** - Web scraping, YouTube transcripts, PDF processing (Issue #47)
4. **AtomBuilderAgent** - Convert raw data → structured atoms (Pydantic models)
5. **AtomLibrarianAgent** - Organize atoms, build prerequisite chains, detect gaps
6. **QualityCheckerAgent** - Validate accuracy, safety compliance, citation integrity

**Content Production Team (5 agents):**
7. **MasterCurriculumAgent** - A-to-Z roadmap, learning paths, sequencing
8. **ContentStrategyAgent** - Keyword research, topic selection, SEO optimization
9. **ScriptwriterAgent** - Transform atoms → engaging video scripts (Issue #48)
10. **SEOAgent** - Optimize metadata (titles, descriptions, tags)
11. **ThumbnailAgent** - Generate eye-catching thumbnails, A/B testing

**Media & Publishing Team (4 agents):**
12. **VoiceProductionAgent** - ElevenLabs voice clone, narration generation
13. **VideoAssemblyAgent** - Sync audio + visuals, render final video
14. **PublishingStrategyAgent** - Schedule uploads, optimal timing, playlists
15. **YouTubeUploaderAgent** - Execute uploads, set metadata, handle errors

**Engagement & Analytics Team (3 agents):**
16. **CommunityAgent** - Respond to comments, moderate, engage viewers
17. **AnalyticsAgent** - Track metrics, detect trends, generate insights
18. **SocialAmplifierAgent** - Extract clips, post to TikTok/Instagram/LinkedIn

**See:** `docs/AGENT_ORGANIZATION.md` for complete specifications (responsibilities, tools, success metrics)

## The PLC Knowledge Atom Standard

**PLC Atom Types:**
- `concept`: What is a PLC, digital I/O, scan cycle
- `pattern`: Start/stop/seal-in motor, timer patterns
- `fault`: Common error codes, diagnostic procedures
- `procedure`: Step-by-step troubleshooting, setup wizards

**Example PLC Pattern Atom:**
```json
{
  "atom_id": "plc:ab:motor-start-stop-seal",
  "type": "pattern",
  "vendor": "allen_bradley",
  "platform": "control_logix",
  "title": "3-Wire Motor Start/Stop/Seal-In",
  "summary": "Basic motor control with maintained contact seal-in",
  "inputs": [
    {"tag": "Start_PB", "type": "NO_contact", "address": "I:0/0"},
    {"tag": "Stop_PB", "type": "NC_contact", "address": "I:0/1"},
    {"tag": "Motor_Run", "type": "auxiliary_contact", "address": "O:0/0"}
  ],
  "outputs": [
    {"tag": "Motor_Contactor", "type": "coil", "address": "O:0/0"}
  ],
  "logic_description": "Parallel seal-in circuit with stop button in series",
  "steps": [
    "Press Start_PB → Motor_Contactor energizes",
    "Motor_Run auxiliary contact seals in",
    "Release Start_PB → Motor stays running (sealed)",
    "Press Stop_PB → Motor_Contactor de-energizes"
  ],
  "constraints": [
    "Stop button must be NC for fail-safe operation",
    "Seal-in contact must be sized for coil current",
    "Requires overload protection (not shown in logic)"
  ],
  "difficulty": "beginner",
  "prereqs": ["plc:generic:io-basics", "plc:generic:ladder-fundamentals"],
  "source": "AB ControlLogix Programming Manual Chapter 3",
  "last_reviewed_at": "2025-12-09",
  "safety_level": "info"
}
```

## PLC Tutor Timeline

**Month 2:** Knowledge base ingestion (50-100 atoms from manuals + YouTube)
**Month 3:** PLC Tutor v0.1 (Lessons 1-5 functional)
**Month 4:** YouTube series launch + first paid subscribers
**Month 6:** Autonomous PLC coder prototype
**Month 12:** Full multi-platform tutor (Siemens + Allen-Bradley)

**Year 1 Target:** $35K ARR (50 subscribers + courses)
**Year 3 Target:** $2.5M ARR (sustainable business)

## Strategy: Same Infrastructure, Different Domain

```
Layer 1: Agent Factory (powers both)
    ↓
Layer 2: Knowledge Atom Standard
    ├── Industrial Maintenance Atoms (RIVET)
    └── PLC Programming Atoms (PLC Tutor)
    ↓
Layer 3: Multi-Vertical Products
    ├── RIVET ($2.5M ARR)
    └── PLC Tutor ($2.5M ARR)
    ↓
Layer 4: DAAS (sell both knowledge bases)
    ↓
Layer 5: Robot Licensing (both are robot-ready)
```

---

## The YouTube-Wiki Strategy (CRITICAL)

**"YouTube IS the knowledge base"**

Instead of scraping first then creating content, we **build the knowledge base BY creating original educational content**.

### Why This Changes Everything

1. **Zero Copyright Issues** - Original content = you own 100% of rights, immediate monetization
2. **Learning-by-Teaching** - You retain 90% of what you teach vs 10% of what you read
3. **Voice Clone = 24/7 Production** - ElevenLabs voice clone enables autonomous content creation
4. **Multi-Use Content** - One video → knowledge atom → blog post → social clips → course module

### The YouTube-Wiki Pipeline

```
YOU learn concept → Research Agent compiles sources
    ↓
Scriptwriter Agent drafts teaching script
    ↓
Voice Production Agent generates narration (your voice clone)
    ↓
Video Assembly Agent combines audio + visuals
    ↓
YouTube Uploader Agent publishes
    ↓
Atom Builder Agent extracts knowledge atom from video
    ↓
Social Amplifier Agent creates clips for TikTok/Instagram
```

### Key Principles

- **Videos 1-20:** YOU approve every one (set quality standard)
- **Videos 21-50:** YOU sample every 3rd (quality gates)
- **Videos 51+:** Agents autonomous (exception flagging only)
- **Content Roadmap:** 100+ videos pre-planned (A-to-Z curriculum)
- **Voice Training:** 10-15 min samples → ElevenLabs Pro → natural-sounding narration
- **SEO-First:** Every video targets low-competition, high-volume keywords

### Success Metrics

- **Week 4:** 3 videos live, voice clone validated
- **Week 12:** 30 videos, 1K subs, $500 revenue, agents 80% autonomous
- **Month 12:** 100 videos, 20K subs, $5K/mo revenue, fully autonomous

**See:** `docs/implementation/YOUTUBE_WIKI_STRATEGY.md` for complete details.

---

## PLC Implementation References

**Complete Strategy Suite (Updated Dec 2025):**
- **Master Strategy:** `docs/architecture/TRIUNE_STRATEGY.md` - Complete integration (RIVET + PLC Tutor + Agent Factory), 18-agent system, revenue models
- **YouTube-Wiki Approach:** `docs/implementation/YOUTUBE_WIKI_STRATEGY.md` - Build knowledge BY teaching (original content, voice clone, 24/7 production)
- **18-Agent System:** `docs/architecture/AGENT_ORGANIZATION.md` - Complete specs for all autonomous agents (Executive, Research, Content, Media, Engagement)
- **Implementation Plan:** `docs/implementation/IMPLEMENTATION_ROADMAP.md` - Week-by-week roadmap (Week 1-12, then Month 4-12)
- **Content A-to-Z:** `plc/content/CONTENT_ROADMAP_AtoZ.md` - 100+ video topics sequenced (electricity → AI automation)
- **Universal Atom Spec:** `docs/architecture/ATOM_SPEC_UNIVERSAL.md` - IEEE LOM-based schema for all verticals
- **Pydantic Models:** `core/models.py` - Production-ready schemas (LearningObject, PLCAtom, RIVETAtom, VideoScript, etc.)

**Legacy/Research:** (Moved to `archive/legacy-docs/`)
- `MASTER_ROADMAP.md` - Original 5-layer vision
- `PLan_fullauto_plc.md` - Initial PLC implementation plan
- `Computers, programming PLCs..md` - Market research + business insights

## PLC Validation Commands

```bash
# Verify PLC atom schema
poetry run python -c "from plc.atoms.pydantic_models import PLCAtom; print('PLC schema OK')"

# Test PLC tutor agent
poetry run python -c "from plc.agents.plc_tutor_agent import PLCTutorAgent; print('Tutor OK')"

# Run PLC atom builder
poetry run python plc/agents/plc_atom_builder_agent.py --source plc/sources/siemens/s7-1200/

# Test with real hardware
poetry run python examples/plc_tutor_demo.py --platform siemens --lesson 1
```
