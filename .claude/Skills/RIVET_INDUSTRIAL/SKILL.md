# RIVET Industrial Skill

## Purpose
Industrial maintenance knowledge platform with validated troubleshooting, community engagement, and B2B integrations.

## Status
🔜 Deferred to Month 4+ (Post-SCAFFOLD and PLC Tutor validation)

## Vision

**Core Insight**: Build a brand + community + distribution network that technicians discover organically, trust immediately, and evangelize to peers.

**The Data is the Moat**: Competitors can copy tools, but they can't replicate 100k+ validated Knowledge Atoms with citations, safety compliance, and human expert verification.

## Architecture Overview

### The Full System (3 Layers)

**Layer 1: Knowledge Factory**
- Scrapers harvest industrial maintenance data (Reddit, Stack Overflow, PDFs, forums, YouTube)
- Validators verify accuracy against official documentation
- Vector database (Supabase + pgvector) storing validated "Knowledge Atoms"
- 6-stage validation pipeline ensures data integrity

**Layer 2: Agent Orchestration**
- Agents route queries, generate responses, publish content, flag for human help
- RedditMonitor → KnowledgeAnswerer → RedditResponder (with approval)
- YouTubePublisher creates faceless videos from solved problems
- SocialAmplifier distributes across TikTok, Instagram, Twitter, LinkedIn

**Layer 3: Distribution & Monetization**
- Social media distribution (organic discovery)
- Premium troubleshooting calls ($50-100/hour)
- B2B integrations (CMMS vendors: ServiceTitan, MaintainX, UpKeep)
- Data licensing (clean industrial datasets to OEMs)

## Agents (6 Core Production Agents)

| Agent | Schedule | Function |
|-------|----------|----------|
| **RedditMonitor-v1.0** | Every 2 hours | Find unanswered technical questions in r/HVAC, r/Plumbing, r/IndustrialMaintenance |
| **KnowledgeAnswerer-v1.0** | On-demand | Query atoms, generate answers with citations, confidence scoring |
| **RedditResponder-v1.0** | After approval | Post comments with human-in-loop approval (confidence <0.9) |
| **YouTubePublisher-v1.0** | Daily | Create 3-5 min faceless videos from solved problems |
| **SocialAmplifier-v1.0** | Daily | Extract clips, cross-post to TikTok/Instagram/LinkedIn |
| **HumanFlagger-v1.0** | Real-time | Escalate to human expert when confidence <0.9 (10min SLA) |

## Knowledge Atom Standard

### RIVETAtom Schema
```python
from core.models import RIVETAtom

atom = RIVETAtom(
    atom_id="rivet:hvac:compressor-noise-diag",
    type="troubleshooting",
    equipment_class="HVAC",
    make="Carrier",
    model="30RB",
    symptom="Loud rattling noise from compressor",
    root_causes=[
        "Loose mounting bolts",
        "Worn compressor bearings",
        "Refrigerant flooding"
    ],
    diagnostic_steps=[
        "Isolate compressor electrically (LOTO)",
        "Inspect mounting bolts for tightness",
        "Check oil level in sight glass",
        "Listen for bearing noise with stethoscope"
    ],
    corrective_actions=[
        "Tighten bolts to 45 ft-lb torque",
        "Replace compressor if bearings worn",
        "Add oil if low, check for leaks"
    ],
    safety_level="CAUTION",
    loto_required=True,
    ppe_required=["safety_glasses", "gloves"],
    citations=[
        "[^1]: Carrier 30RB Service Manual, Section 4.2",
        "[^2]: ASHRAE Refrigeration Handbook, Ch. 7"
    ]
)
```

### Atom Types
- **troubleshooting**: Symptom → diagnosis → fix
- **procedure**: Step-by-step maintenance tasks
- **specification**: Equipment specs, tolerances, ratings
- **safety**: LOTO procedures, hazard warnings, PPE requirements

## Workflows

### 1. Reddit Response Workflow
```
RedditMonitor (every 2 hours)
→ Detect unanswered question
→ KnowledgeAnswerer queries atoms
→ Generate answer with citations
→ Confidence scoring (0.0 - 1.0)
→ IF confidence ≥0.9: Auto-post (RedditResponder)
→ IF confidence <0.9: Flag for human review (HumanFlagger)
→ Human expert approves/edits/rejects
→ Post to Reddit
→ Monitor for follow-up questions
```

### 2. Content Generation Workflow
```
Solved problem on Reddit
→ YouTubePublisher extracts key points
→ Generate faceless video (text overlays, diagrams, narration)
→ Upload to YouTube (3-5 min)
→ SocialAmplifier extracts 30-60s clips
→ Post to TikTok, Instagram, LinkedIn
→ Cross-link back to full YouTube video
→ Track engagement metrics (AnalyticsAgent)
```

### 3. Premium Escalation Workflow
```
User posts complex question
→ KnowledgeAnswerer confidence <0.9
→ HumanFlagger escalates to expert pool
→ Expert claims ticket (10min SLA)
→ Expert posts free initial guidance
→ Offer premium call ($50-100/hour) for deep dive
→ Stripe payment link
→ Schedule Calendly consultation
→ Post-call: Extract atoms from solution
→ Publish anonymized case study
```

## Revenue Model

### Year 1 Targets ($80K ARR)
- **Reddit Karma / YouTube Subs**: Free tier (build trust)
- **Premium Calls**: $50-100/hour consultations ($30K/year)
- **B2B CMMS Integrations**: $500-2K/month per vendor ($20K/year)
- **Data Licensing**: $10K-30K one-time deals ($30K/year)

### Year 3 Targets ($2.5M ARR)
- **Premium Subscriptions**: $29-99/month for unlimited AI support ($1M/year)
- **B2B Enterprise**: $5K-10K/month CMMS integrations ($1M/year)
- **Data Licensing**: Ongoing royalties ($500K/year)

### Year 5 Vision ($10-50M ARR)
- **1M+ Users**: Global technician community
- **50+ Human Experts**: Fractional consulting network
- **Robot Licensing**: Equipment OEMs license data for AI-powered diagnostics
- **Industry Standard**: RIVET becomes the "Wikipedia of industrial maintenance"

## B2B Integration Points

### CMMS Platforms (Target Partners)
- **ServiceTitan**: HVAC/plumbing field service software
- **MaintainX**: Mobile-first CMMS for manufacturing
- **UpKeep**: Cloud CMMS for facilities maintenance
- **Fiix**: AI-powered maintenance management

### Integration Model
```
Technician reports issue in CMMS
→ CMMS API calls RIVET API
→ RIVET returns troubleshooting atoms
→ Display in CMMS mobile app
→ Technician follows diagnostic steps
→ Log resolution in CMMS
→ RIVET learns from successful fixes
```

### API Pricing
- **Free Tier**: 100 API calls/month (trial)
- **Starter**: $500/month (10K calls, 2 integrations)
- **Professional**: $2K/month (100K calls, 10 integrations)
- **Enterprise**: Custom pricing (unlimited calls, white-label)

## Distribution Strategy

### Organic Channels
1. **Reddit**: Answer real questions, build credibility
2. **YouTube**: Faceless videos, SEO-optimized titles
3. **TikTok/Instagram**: 30-60s clips, viral hooks
4. **Twitter/LinkedIn**: Expert commentary, industry news

### Community Building
- **Discord Server**: 10K+ members (free tier)
- **Expert Network**: 50+ fractional consultants (vetted)
- **User-Generated Content**: Technicians submit solved problems
- **Reputation System**: Karma for helpful answers (Reddit-style)

### Partnerships
- **Trade Schools**: White-label training content
- **Equipment OEMs**: Co-branded troubleshooting guides
- **Trade Associations**: HVACR, NFPA, IEEE sponsorships

## Quality Assurance

### 6-Stage Validation Pipeline
1. **Source Verification**: Check citations against official manuals
2. **Safety Compliance**: Flag LOTO requirements, PPE, arc flash hazards
3. **Accuracy Check**: Cross-reference with multiple sources
4. **Peer Review**: Human expert validation (10% sample)
5. **User Feedback**: Upvote/downvote on answers
6. **Continuous Learning**: Update atoms based on field results

### Safety Standards
- **NFPA 70E**: Arc flash protection
- **OSHA 1910**: LOTO, confined spaces, electrical safety
- **ANSI Z10**: Occupational health & safety
- **ASHRAE**: HVAC refrigeration safety

## Timeline (Deferred to Month 4+)

**Month 1**: Knowledge Factory foundation (1K atoms indexed)
**Month 2**: First agent channel (Reddit monitoring + manual approval)
**Month 3**: Content generation (YouTube channel launch)
**Month 4**: Multi-platform distribution (TikTok, Instagram, LinkedIn)
**Month 5**: Human-in-the-loop escalation (premium calls)
**Month 6**: B2B outreach (CMMS integrations)

**Year 1 Target**: $80K revenue, proof of concept
**Year 3 Target**: $2.5M revenue, sustainable business
**Year 5 Vision**: $10-50M ARR, 1M+ users, 50+ experts

## Key Files & Directories

```
docs/architecture/
├── TRIUNE_STRATEGY.md           # RIVET + PLC Tutor integration
└── ATOM_SPEC_UNIVERSAL.md       # Shared atom schema

core/
└── models.py                    # RIVETAtom Pydantic schema

agent_factory/rivet_pro/
├── agents/mock_agents.py        # Planned agent stubs
└── rag/                         # RAG implementation (hybrid search)

scripts/knowledge/
├── generate_embeddings.py       # OpenAI embeddings
└── upload_embeddings.py         # Supabase ingestion
```

## Integration Points

### With PLC_TUTOR
- Shared Knowledge Atom Standard (IEEE LOM)
- Shared Supabase backend (multi-tenant schema)
- Shared citation validation (Perplexity-style footnotes)
- Cross-promotion (PLC videos link to RIVET for troubleshooting)

### With RESEARCH Skill
- ResearchAgent scrapes industrial forums (Reddit, Stack Overflow)
- AtomBuilderAgent extracts RIVETAtoms from solved problems
- QualityCheckerAgent validates safety compliance

### With Agent Factory Core
- All agents use `agent_factory.core.agent_factory.AgentFactory`
- Memory storage via `agent_factory.memory.storage.SupabaseMemoryStorage`
- LLM routing via `agent_factory.llm.router.LLMRouter`

## Competitive Advantages

1. **Data Moat**: 100K+ validated atoms (cannot be replicated quickly)
2. **Community Network**: 1M+ users evangelize to peers
3. **Human-in-Loop**: Expert validation prevents hallucinations
4. **Safety Compliance**: NFPA/OSHA/ANSI standards built-in
5. **Multi-Platform**: Organic discovery across Reddit/YouTube/TikTok
6. **B2B Revenue**: CMMS integrations = recurring revenue

## References

- **Strategy**: `docs/architecture/TRIUNE_STRATEGY.md`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`
- **Full Vision**: `CLAUDE.md` (RIVET section)
- **Roadmap**: `docs/implementation/IMPLEMENTATION_ROADMAP.md`

---

**Note**: RIVET is deferred to Month 4+ (post-SCAFFOLD and PLC Tutor validation). SCAFFOLD proves platform economics first.
