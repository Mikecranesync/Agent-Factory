# RIVET Industrial

> Industrial maintenance knowledge platform with validated troubleshooting, community engagement, and B2B integrations

## Status
🔜 Deferred to Month 4+ (Post-SCAFFOLD and PLC Tutor validation)

**Priority**: #3 (After SCAFFOLD and PLC Tutor prove platform)

## Vision

**Core Insight**: Build a brand + community + distribution network that technicians discover organically, trust immediately, and evangelize to peers.

**The Data is the Moat**: Competitors can copy tools, but they can't replicate 100k+ validated Knowledge Atoms with citations, safety compliance, and human expert verification.

## Quick Start

### Load Skill Context
```bash
# In Claude Code
Skill("RIVET_INDUSTRIAL")  # Load full RIVET context
```

### Query Knowledge Base (When Available)
```bash
# Semantic search for troubleshooting atoms
poetry run python -c "
from agent_factory.memory.storage import SupabaseMemoryStorage
storage = SupabaseMemoryStorage()
# Search for HVAC troubleshooting atoms
results = storage.search_atoms('compressor noise diagnosis', limit=5)
print(results)
"
```

## Architecture

### Skill Definition
- **Location**: `.claude/Skills/RIVET_INDUSTRIAL/SKILL.md`
- **6 Core Agents**: RedditMonitor, KnowledgeAnswerer, RedditResponder, YouTubePublisher, SocialAmplifier, HumanFlagger
- **3 Workflows**: Reddit Response, Content Generation, Premium Escalation
- **Data Model**: RIVETAtom (troubleshooting, procedures, specifications, safety)

### Agent Locations (Planned)
```
agent_factory/rivet_pro/
├── agents/
│   ├── reddit_monitor_v1_0.py        # Find unanswered questions
│   ├── knowledge_answerer_v1_0.py    # Generate answers with citations
│   ├── reddit_responder_v1_0.py      # Post comments (human-in-loop)
│   ├── youtube_publisher_v1_0.py     # Create faceless videos
│   ├── social_amplifier_v1_0.py      # TikTok/Instagram clips
│   └── human_flagger_v1_0.py         # Escalate to experts
└── rag/
    └── __init__.py                   # RAG implementation (hybrid search)
```

## Knowledge Base

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
- **ServiceTitan**: HVAC/plumbing field service software (200K+ users)
- **MaintainX**: Mobile-first CMMS for manufacturing (10K+ companies)
- **UpKeep**: Cloud CMMS for facilities maintenance (5K+ companies)
- **Fiix**: AI-powered maintenance management (2K+ companies)

### API Pricing
- **Free Tier**: 100 API calls/month (trial)
- **Starter**: $500/month (10K calls, 2 integrations)
- **Professional**: $2K/month (100K calls, 10 integrations)
- **Enterprise**: Custom pricing (unlimited calls, white-label)

## Distribution Strategy

### Organic Channels
1. **Reddit**: Answer real questions in r/HVAC, r/Plumbing, r/IndustrialMaintenance
2. **YouTube**: Faceless videos (3-5 min), SEO-optimized titles
3. **TikTok/Instagram**: 30-60s clips with viral hooks
4. **Twitter/LinkedIn**: Expert commentary, industry news

### Community Building
- **Discord Server**: 10K+ members (free tier)
- **Expert Network**: 50+ fractional consultants (vetted)
- **User-Generated Content**: Technicians submit solved problems
- **Reputation System**: Karma for helpful answers (Reddit-style)

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

**Month 4**: Knowledge Factory foundation (1K atoms indexed)
**Month 5**: Reddit agent channel (monitoring + manual approval)
**Month 6**: Content generation (YouTube channel launch)
**Month 7-8**: Premium escalation (expert calls, $50-100/hour)

**Year 1 Target**: $80K revenue, proof of concept
**Year 3 Target**: $2.5M revenue, sustainable business
**Year 5 Vision**: $10-50M ARR, 1M+ users, 50+ experts

## Integration with Other Products

### Shared with PLC Tutor
- Knowledge Atom Standard (IEEE LOM)
- Supabase backend (multi-tenant schema)
- Citation validation (Perplexity-style)
- Quality validation pipeline

### Shared with RESEARCH Skill
- ResearchAgent scrapes industrial forums (Reddit, Stack Overflow)
- AtomBuilderAgent extracts RIVETAtoms from solved problems
- QualityCheckerAgent validates safety compliance

## References

- **Skill Definition**: `.claude/Skills/RIVET_INDUSTRIAL/SKILL.md`
- **Strategy**: `docs/architecture/TRIUNE_STRATEGY.md`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`
- **Full Vision**: `CLAUDE.md` (RIVET section)
- **Product Backlog**: `products/rivet-industrial/backlog.md`

## Support

For questions or issues:
1. Check skill context: `Skill("RIVET_INDUSTRIAL")`
2. Read strategy: `docs/architecture/TRIUNE_STRATEGY.md`
3. Review backlog: `products/rivet-industrial/backlog.md`
