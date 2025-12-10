# PLC Tutor & Autonomous PLC Programmer

**Status:** Phase 1 - Foundation
**Version:** 0.1.0
**Revenue Target:** $2.5M ARR by Year 3
**Combined (RIVET + PLC):** $5M+ ARR

---

## What This Is

PLC Tutor is the **second vertical** built on Agent Factory, proving the platform works across different domains:

- **RIVET:** Industrial maintenance troubleshooting (error codes, procedures)
- **PLC Tutor:** PLC programming education + autonomous code generation
- **Agent Factory:** The orchestration engine powering both

This validates Agent Factory as a true multi-vertical platform, not just a single-product tool.

---

## Strategic Vision

### Why PLC Tutor?

1. **De-Risk RIVET:** Don't put all eggs in one basket
2. **Validate Platform:** Prove Knowledge Atom Standard works across domains
3. **Faster Revenue:** Smaller market, easier to dominate
4. **Licensing Revenue:** PLC vendor atoms → DAAS model
5. **Robot Licensing:** PLC code generation → perpetual licensing (Year 5+)

### The 70/30 Strategy

- **70% Resources → RIVET** (primary revenue driver)
- **30% Resources → PLC Tutor** (validation + de-risk)

If RIVET hits $2.5M ARR and PLC Tutor hits $2.5M ARR, that's $5M+ combined with same infrastructure.

---

## Product Offering

### Phase 1: Learning Platform (Months 1-3)
**Target:** 500 free users, 50 paying subscribers
**Revenue:** ~$35K ARR (proof of concept)

- YouTube tutorials (SEO-optimized, faceless videos)
- Free web-based flashcards and quizzes
- Basic subscription ($29/mo): Access to 1,000+ atoms, learning paths
- Plus subscription ($99/mo): Code examples, downloadable projects

### Phase 2: Code Generation (Months 4-8)
**Target:** 100+ Pro subscribers
**Revenue:** ~$150K ARR

- LLM4PLC pattern: Spec → Code → Verify
- Computer-use integration (Playwright/PyAutoGUI → Studio 5000/TIA Portal)
- "Autonomous PLC Programmer" tool ($499/mo individual, $5K-$20K/mo enterprise)
- White-label for training organizations

### Phase 3: Platform Ecosystem (Months 9-12)
**Target:** 1,000 subscribers, B2B partnerships
**Revenue:** ~$500K ARR

- DAAS (Data-as-a-Service): PLC atom API licensing to vendors
- B2B integrations: Training platforms, PLCnext, CODESYS
- Community marketplace: User-contributed atoms
- Certification program (with community experts)

---

## Technology Stack

### Same Infrastructure as RIVET
- **Agent Factory** - Orchestration layer
- **Knowledge Atom Standard** - Extended for PLC domain
- **Supabase + pgvector** - Vector database (same instance)
- **LangChain** - Agent composition
- **Pydantic** - Data validation
- **Poetry** - Dependency management

### PLC-Specific Technologies
- **LLM4PLC Pattern** - Spec → code → verify loop (UC Irvine research)
- **Computer-Use** - Playwright/PyAutoGUI for driving PLC software
- **IEC 61131-3** - Standard PLC programming languages
- **IEC 62061** - Safety of machinery standards

### Target Platforms
- **Siemens S7-1200/S7-1500** (start here - user has hardware)
- **Allen-Bradley ControlLogix/CompactLogix**
- **CODESYS** (multi-vendor)

---

## The 15-Agent Agentic Organization

### Product & Engineering Team (Agents 1-5)

**Agent 1: PLC Textbook Scraper**
- Scrapes university textbooks, online courses
- Extracts concepts, patterns, procedures
- Runs: Daily
- Output: Raw markdown → sources/

**Agent 2: Vendor Manual Scraper**
- Scrapes Siemens, AB, Schneider official docs
- Focuses on patterns and fault codes
- Runs: Daily
- Output: Raw PDF chunks → sources/

**Agent 3: Atom Validator**
- Validates atoms against PLC_ATOM_SPEC.md JSON Schema
- Checks safety requirements for high-risk atoms
- Verifies prerequisite chains
- Runs: On atom submission
- Output: Valid atoms → atoms/, invalid atoms flagged

**Agent 4: Atom Publisher**
- Publishes validated atoms to Supabase
- Generates embeddings (text-embedding-3-large)
- Updates atom status (draft → validated → tested_on_hardware)
- Runs: After validation
- Output: Atoms in production database

**Agent 5: Duplicate Detector**
- Finds near-duplicate atoms (cosine similarity >0.95)
- Merges duplicates, preserves best source
- Runs: Nightly
- Output: Deduplicated atom database

### Content & Media Team (Agents 6-9)

**Agent 6: Tutorial Writer**
- Generates educational blog posts from concept atoms
- SEO-optimized (keyword: "PLC timer tutorial", "ladder logic basics")
- Runs: 3x per week
- Output: Blog posts, YouTube scripts

**Agent 7: Code Generator (LLM4PLC)**
- Generates PLC code from natural language specs
- Uses pattern atoms as templates
- Verifies code in PLC software (computer-use)
- Runs: On-demand (user requests)
- Output: Ladder logic, structured text, verification results

**Agent 8: Video Producer**
- Creates 5-10 minute faceless educational videos
- Uses HeyGen or similar for narration
- Adds screen recordings of PLC software
- Runs: 2x per week
- Output: YouTube videos

**Agent 9: Social Media Manager**
- Distributes content to TikTok, Instagram, Twitter, LinkedIn
- Monitors engagement, adjusts strategy
- Runs: Daily
- Output: Social media posts, engagement analytics

### Business & GTM Team (Agents 10-15)

**Agent 10: Pricing Analyst**
- Tracks competitor pricing (Udemy, PLC Academy, training orgs)
- Optimizes tiers ($29 / $99 / $499)
- Runs: Weekly
- Output: Pricing recommendations

**Agent 11: Sales Agent (BDR)**
- Identifies enterprise leads (training orgs, manufacturing)
- Sends personalized outreach emails
- Books demos with human closer
- Runs: Daily
- Output: Qualified leads, booked meetings

**Agent 12: Community Manager**
- Monitors Discord, forum, Reddit
- Answers questions, surfaces FAQs
- Escalates complex issues to human experts
- Runs: 24/7
- Output: Community engagement, FAQ database

**Agent 13: Analytics Agent**
- Tracks MRR, CAC, LTV, churn
- Identifies power users and at-risk subscribers
- Generates weekly executive summary
- Runs: Daily
- Output: Dashboard, alerts, recommendations

**Agent 14: Partnership Agent**
- Identifies DAAS licensing opportunities (PLC vendors)
- Tracks B2B integration leads (CMMS, training platforms)
- Drafts partnership proposals
- Runs: Weekly
- Output: Partnership pipeline, proposals

**Agent 15: Customer Success Agent**
- Onboards new subscribers
- Tracks usage, sends tips
- Prevents churn (flags inactive users)
- Runs: Daily
- Output: Onboarding emails, usage reports, retention metrics

---

## Directory Structure

```
plc/
├── README.md                   # This file
├── __init__.py                 # Package initialization
│
├── sources/                    # Raw scraped content
│   ├── textbooks/              # University textbooks, PDFs
│   ├── vendor_manuals/         # Siemens, AB, Schneider docs
│   └── community/              # Stack Overflow, forums
│
├── chunks/                     # Chunked content (pre-processing)
│   └── *.json                  # Chunked text ready for atom extraction
│
├── atoms/                      # Validated PLC atoms
│   ├── concepts/               # Concept atoms (scan cycle, timers, etc.)
│   ├── patterns/               # Pattern atoms (motor control, state machines)
│   ├── faults/                 # Fault atoms (error codes, diagnostics)
│   └── procedures/             # Procedure atoms (commissioning, testing)
│
├── agents/                     # 15 autonomous agents
│   ├── __init__.py
│   ├── product_engineering/    # Agents 1-5
│   │   ├── textbook_scraper_agent.py
│   │   ├── vendor_manual_scraper_agent.py
│   │   ├── atom_validator_agent.py
│   │   ├── atom_publisher_agent.py
│   │   └── duplicate_detector_agent.py
│   ├── content_media/          # Agents 6-9
│   │   ├── tutorial_writer_agent.py
│   │   ├── code_generator_agent.py
│   │   ├── video_producer_agent.py
│   │   └── social_media_agent.py
│   └── business_gtm/           # Agents 10-15
│       ├── pricing_analyst_agent.py
│       ├── sales_agent_bdr.py
│       ├── community_manager_agent.py
│       ├── analytics_agent.py
│       ├── partnership_agent.py
│       └── customer_success_agent.py
│
├── tutor/                      # PLC Tutor chatbot (user-facing)
│   ├── chatbot.py              # Main chatbot interface
│   ├── query_router.py         # Routes queries to relevant agents
│   └── response_generator.py  # Generates responses with citations
│
├── config/                     # Configuration files
│   ├── database_schema.sql     # Supabase table definitions
│   ├── agent_schedules.yaml    # When each agent runs
│   └── vendor_config.yaml      # Vendor-specific settings
│
└── utils/                      # Shared utilities
    ├── validation.py           # Atom validation functions
    ├── embeddings.py           # Vector embedding generation
    ├── computer_use.py         # PLC software automation
    └── safety.py               # Safety requirement checking
```

---

## Data: The PLC Atom Standard

See `docs/PLC_ATOM_SPEC.md` for full specification.

### 4 Atom Types

1. **Concept Atoms** - Fundamentals (scan cycle, timers, counters)
2. **Pattern Atoms** - Reusable code patterns (motor control, state machines)
3. **Fault Atoms** - Error codes and diagnostics
4. **Procedure Atoms** - Step-by-step guides (commissioning, testing)

### Example: Pattern Atom (3-Wire Motor Control)

```json
{
  "@id": "plc:ab:motor-start-stop-seal",
  "atom_type": "pattern",
  "plc:vendor": "allen_bradley",
  "plc:platform": "control_logix",
  "plc:inputs": [
    {"tag": "Start_PB", "type": "BOOL", "io_type": "DI"},
    {"tag": "Stop_PB", "type": "BOOL", "io_type": "DI"}
  ],
  "plc:outputs": [
    {"tag": "Motor_Contactor", "type": "BOOL", "io_type": "DO"}
  ],
  "plc:logicDescription": "Parallel seal-in with series stop button",
  "plc:ladderLogicSteps": [
    "Rung 0: Start_PB (XIC) || Motor_Running (XIC) && Stop_PB (XIC) → Motor_Contactor (OTE)"
  ],
  "plc:safetyRequirements": [
    "Stop button MUST be NC for fail-safe operation"
  ],
  "plc:safetyLevel": "caution"
}
```

---

## Business Model

### Revenue Streams

**B2C Subscriptions** (Primary, Year 1)
- Basic: $29/mo (learning platform, 1K atoms)
- Plus: $99/mo (code examples, projects)
- Pro: $499/mo (autonomous code generator)

**B2B Individual** (Year 2)
- Professional: $99-$499/mo (engineers, integrators)
- Autonomous Coder: $499/mo (spec → working code)

**B2B Enterprise** (Year 2-3)
- White-label: $5K-$20K/mo (training organizations)
- Site licenses: Custom pricing

**DAAS Licensing** (Year 3+)
- PLC Atom API: $50K-$100K/year (vendors license atoms)

### Revenue Projections

**Year 1:** $35K ARR (500 free, 50 Basic @ $29/mo)
**Year 2:** $500K ARR (1K users, 100 Pro, 5 Enterprise)
**Year 3:** $2.5M ARR (10K users, 100 Pro, 50 Enterprise, DAAS licensing)

### Unit Economics

- **CAC:** $20-$50 (organic YouTube + Reddit)
- **LTV:** $500-$5,000 (12-month retention)
- **Gross Margin:** 80%+ (same infra as RIVET)

---

## Implementation Timeline

### Month 1: Foundation
- [x] Create PLC_ATOM_SPEC.md
- [x] Create plc/ directory structure
- [ ] Create 15 agent skeleton classes
- [ ] Create 10 example atoms (3 patterns, 3 concepts, 2 faults, 2 procedures)
- [ ] Set up Supabase tables (extend RIVET schema)

### Month 2: Agent Implementation (Product & Engineering)
- [ ] Agent 1: PLC Textbook Scraper
- [ ] Agent 2: Vendor Manual Scraper
- [ ] Agent 3: Atom Validator
- [ ] Agent 4: Atom Publisher
- [ ] Agent 5: Duplicate Detector
- [ ] Goal: 100 validated atoms

### Month 3: Content & Code Generation
- [ ] Agent 6: Tutorial Writer
- [ ] Agent 7: Code Generator (LLM4PLC)
- [ ] Agent 8: Video Producer
- [ ] Agent 9: Social Media Manager
- [ ] Launch YouTube channel
- [ ] Goal: 500 free users

### Month 4: Business & Launch
- [ ] Agents 10-15: Business team
- [ ] Launch Basic subscription ($29/mo)
- [ ] First 10 paying customers
- [ ] Goal: $1,450 MRR

---

## Testing Hardware

**User Has:**
- Siemens S7-1200 (test PLC)
- Allen-Bradley test unit
- TIA Portal installed
- Studio 5000 access

**Testing Strategy:**
1. Start with Siemens S7-1200 (user-familiar platform)
2. Validate all pattern atoms on hardware
3. Mark atoms as `tested_on_hardware` status
4. Expand to Allen-Bradley once Siemens patterns validated

---

## Success Metrics

### Data Quality
- **Atom Coverage:** 1,000+ atoms by Month 3
- **Vendor Coverage:** Siemens + Allen-Bradley + CODESYS
- **Validation Rate:** 80%+ atoms tested on hardware
- **Safety Compliance:** 100% high-safety atoms documented

### User Engagement
- **Free Users:** 500 by Month 3
- **Paying Subscribers:** 50 by Month 3 (10% conversion)
- **Code Gen Success:** 70%+ generated code compiles
- **User Satisfaction:** 4.5+ stars

### Business
- **MRR:** $1,450 by Month 3
- **CAC:** <$50
- **LTV:** $500+
- **Autonomous Coder Usage:** 10+ customers by Month 6

---

## Competitive Advantage

**What Others Have:**
- Online courses (Udemy, PLC Academy)
- Static tutorials (YouTube)
- Forum communities (PLCS.net, Reddit)

**What We Have:**
- **Validated knowledge base** (1,000+ atoms, tested on hardware)
- **Autonomous code generation** (LLM4PLC + computer-use)
- **Multi-vendor support** (not locked to one platform)
- **Agentic organization** (15 AI employees, 24/7 operation)
- **Data moat** (Knowledge Atom Standard, can't replicate)

---

## Risk Mitigation

**Risk:** PLC vendors create competing tools
**Mitigation:** Become their data provider (DAAS licensing)

**Risk:** Market too small
**Mitigation:** RIVET is primary, PLC is validation (70/30 split)

**Risk:** Code generation liability
**Mitigation:** User testing requirement, verification step, disclaimer

**Risk:** Hardware testing bottleneck
**Mitigation:** Community testers, simulation first

---

## Next Steps

1. **Create 15 agent skeleton classes** (Week 1)
2. **Create 10 example atoms** (Week 1)
3. **Set up Supabase tables** (Week 2)
4. **Implement Agents 1-5** (Month 2)
5. **Test on S7-1200 hardware** (Month 2)
6. **Launch YouTube channel** (Month 3)
7. **First 10 paying customers** (Month 4)

---

**Built on Agent Factory. Powered by Knowledge Atoms. Validated with RIVET.**

See `docs/PLC_VISION.md` for full strategic vision.
