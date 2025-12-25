# RIVET Industrial Backlog

**Status**: 🔜 Deferred to Month 4+ (Post-SCAFFOLD and PLC Tutor validation)

**Priority**: #3 (After SCAFFOLD and PLC Tutor prove platform)

---

## 🔴 Blocked (Awaiting PLC Tutor Launch)

### Platform Dependencies
- [ ] **Shared Knowledge Atom Standard validated** (via PLC Tutor)
- [ ] **Supabase multi-tenant schema** tested at scale
- [ ] **Citation validation pipeline** proven (Perplexity-style)
- [ ] **Agent orchestration patterns** refined from PLC Tutor experience

---

## 🟡 Ready to Start (When PLC Tutor Complete)

### Month 4: Knowledge Factory Foundation (Week 1-4)
- [ ] **Ingest 1K atoms** from industrial maintenance sources
  - Reddit: r/HVAC, r/Plumbing, r/IndustrialMaintenance (top 100 solved problems)
  - Stack Overflow: HVAC, PLC, electrical tags (top 50 Q&A)
  - PDFs: Carrier, Trane, Lennox service manuals (5-10 sources)
  - Forums: HVAC-Talk.com, ControlLogicETC (curated threads)

- [ ] **Create RIVETAtom schema** in Supabase
  - Tables: `rivet_atoms`, `equipment_classes`, `troubleshooting_atoms`
  - Indexes: `equipment_class`, `make`, `model`, `symptom` (full-text)
  - RLS policies: Public read, admin write

- [ ] **Safety compliance validation** - NFPA/OSHA/ANSI standards
  - Flag LOTO requirements automatically
  - Detect arc flash hazards
  - Validate PPE requirements

### Month 5: Reddit Agent Channel (Week 5-8)
- [ ] **RedditMonitor-v1.0** - Find unanswered questions
  - Subreddits: r/HVAC, r/Plumbing, r/IndustrialMaintenance
  - Schedule: Every 2 hours
  - Filter: Unanswered, <24 hours old, >50 words

- [ ] **KnowledgeAnswerer-v1.0** - Generate answers with citations
  - Query: Semantic search (pgvector + OpenAI embeddings)
  - Generate: Answer with Perplexity-style footnotes
  - Score: Confidence (0.0-1.0) based on atom relevance

- [ ] **RedditResponder-v1.0** - Post comments (human-in-loop)
  - Approval: Human review if confidence <0.9
  - Post: Reddit API (PRAW library)
  - Monitor: Follow-up questions, upvotes, replies

- [ ] **HumanFlagger-v1.0** - Escalate complex issues
  - SLA: 10 minutes for expert claim
  - Pool: 5-10 vetted technicians (Discord/Slack)
  - Compensation: $50-100/hour premium calls

### Month 6: Content Generation (Week 9-12)
- [ ] **YouTubePublisher-v1.0** - Create faceless videos from solved problems
  - Input: Solved Reddit thread (question + answer + upvotes)
  - Generate: 3-5 min video (text overlays, diagrams, narration)
  - Upload: YouTube (unlisted → public after review)

- [ ] **SocialAmplifier-v1.0** - Extract clips for TikTok/Instagram/LinkedIn
  - Extract: 30-60s key moments (hook + solution)
  - Format: Vertical (9:16), horizontal (16:9), square (1:1)
  - Post: TikTok, Instagram Reels, LinkedIn (with cross-links)

- [ ] **AnalyticsAgent** - Track engagement metrics
  - Reddit: Upvotes, comments, follow-ups
  - YouTube: Views, retention, CTR
  - Social: Likes, shares, comments
  - Report: Weekly summary (top performers, trends)

### Month 7-8: Premium Escalation (Week 13-16)
- [ ] **Premium call workflow** - $50-100/hour consultations
  - Stripe: Payment links (one-time, subscriptions)
  - Calendly: Scheduling integration
  - Zoom: Video consultation
  - Post-call: Extract atoms from solution, publish case study

- [ ] **Expert network onboarding** - 50+ fractional consultants
  - Vetting: Certifications (EPA 608, NATE, journeyman license)
  - Onboarding: Discord server, payment setup, SLA training
  - Compensation: 70% revenue share on calls

- [ ] **Reputation system** - Karma for helpful answers (Reddit-style)
  - Points: +10 per upvote, +50 per solved problem, +100 per premium call
  - Tiers: Novice (0-99), Contributor (100-499), Expert (500-999), Master (1000+)
  - Badges: Top contributor, safety expert, fast responder

---

## 🟢 Completed

### Design & Planning
- [x] **RIVET_INDUSTRIAL Skill** - Complete platform documentation (`.claude/Skills/RIVET_INDUSTRIAL/SKILL.md`)
- [x] **RIVETAtom schema designed** - Troubleshooting, procedures, specs, safety (`core/models.py`)
- [x] **Revenue model defined** - Year 1 ($80K), Year 3 ($2.5M), Year 5 ($10-50M)
- [x] **B2B integration strategy** - CMMS platforms (ServiceTitan, MaintainX, UpKeep, Fiix)
- [x] **Distribution strategy** - Reddit, YouTube, TikTok, expert network
- [x] **Quality assurance plan** - 6-stage validation, safety standards (NFPA/OSHA/ANSI)

---

## 📊 Metrics & Targets

### Month 4 (Knowledge Factory)
- **Atoms**: 1K (industrial maintenance focus)
- **Quality**: >90% pass rate (6-stage validation)
- **Safety**: 100% LOTO/PPE flagging

### Month 5 (Reddit Channel)
- **Questions Answered**: 50-100 (with human approval)
- **Confidence**: >0.9 average
- **Upvotes**: >5 average per answer

### Month 6 (Content Generation)
- **Videos**: 10-20 faceless videos published
- **Views**: 1K-5K total views
- **Social Clips**: 50-100 clips posted

### Month 7-8 (Premium Escalation)
- **Premium Calls**: 10-20 consultations
- **Revenue**: $500-2K (proof of concept)
- **Expert Pool**: 5-10 vetted technicians

### Year 1 ($80K ARR)
- **Reddit Karma**: 10K+ (build trust)
- **YouTube Subs**: 5K-10K
- **Premium Calls**: $30K revenue
- **B2B Integrations**: $20K revenue (1-2 CMMS partners)
- **Data Licensing**: $30K revenue (OEM deals)

### Year 3 ($2.5M ARR)
- **Users**: 100K+ (global technician community)
- **Premium Subscriptions**: $1M revenue ($29-99/month unlimited AI support)
- **B2B Enterprise**: $1M revenue ($5K-10K/month CMMS integrations)
- **Data Licensing**: $500K revenue (ongoing royalties)

---

## 🔗 B2B Integration Roadmap

### Target CMMS Platforms
1. **ServiceTitan** - HVAC/plumbing field service software (200K+ users)
2. **MaintainX** - Mobile-first CMMS for manufacturing (10K+ companies)
3. **UpKeep** - Cloud CMMS for facilities maintenance (5K+ companies)
4. **Fiix** - AI-powered maintenance management (2K+ companies)

### Integration Milestones
- **Month 6**: API prototype, developer docs
- **Month 8**: First integration (ServiceTitan pilot)
- **Month 10**: Second integration (MaintainX)
- **Month 12**: Third integration (UpKeep or Fiix)

### API Pricing
- **Free Tier**: 100 API calls/month (trial)
- **Starter**: $500/month (10K calls, 2 integrations)
- **Professional**: $2K/month (100K calls, 10 integrations)
- **Enterprise**: Custom pricing (unlimited calls, white-label)

---

## 🔗 Related Backlogs

- **Agent Factory Core**: `backlog.md` (root)
- **PLC Tutor**: `products/plc-tutor/backlog.md`
- **SCAFFOLD**: `products/scaffold/backlog.md`
- **RESEARCH Skill**: Shared infrastructure (no separate backlog)

---

## 📚 References

- **Skill**: `.claude/Skills/RIVET_INDUSTRIAL/SKILL.md`
- **Strategy**: `docs/architecture/TRIUNE_STRATEGY.md`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`
- **Full Vision**: `CLAUDE.md` (RIVET section)
- **Roadmap**: `docs/implementation/IMPLEMENTATION_ROADMAP.md`

---

**Last Updated**: 2025-12-22
**Next Review**: After PLC Tutor launch (Month 4+)
