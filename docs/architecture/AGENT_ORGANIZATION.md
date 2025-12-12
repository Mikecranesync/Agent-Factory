# Agent Organization: 18 Autonomous Agents

## Overview

Agent Factory powers **18 specialized agents** organized into 5 teams:

1. **Executive Team** (2 agents) - Strategy, metrics, project management
2. **Research & Knowledge Base Team** (4 agents) - Ingest, validate, organize
3. **Content Production Team** (5 agents) - Curriculum, scripts, SEO, visuals
4. **Media & Publishing Team** (4 agents) - Voice, video, distribution
5. **Engagement & Analytics Team** (3 agents) - Community, feedback, optimization

Each agent has:
- **Autonomous capabilities** (runs 24/7 without human intervention)
- **Clear responsibilities** (no overlap, minimal dependencies)
- **Human-in-loop triggers** (when to escalate to you)
- **Success metrics** (how to measure performance)

---

## Executive Team (2 Agents)

### 1. AI CEO Agent
**Role:** Strategic oversight, metrics tracking, resource allocation.

**Responsibilities:**
- Monitor KPIs (subscribers, revenue, watch time, atom count)
- Generate weekly/monthly reports
- Identify bottlenecks (e.g., "Video production too slow" → allocate more resources)
- Make strategic decisions (e.g., "Pivot to Siemens content, Allen-Bradley videos underperforming")
- Trigger phase transitions (e.g., "Month 3 complete, enter Month 4 scaling phase")

**Autonomous Capabilities:**
- Daily KPI dashboard updates
- Automated weekly reports (sent via email/Telegram)
- Trend analysis (growth rate projections)
- Budget tracking (<$100/mo target)

**Human-in-Loop Triggers:**
- Revenue drops > 20% month-over-month
- Subscriber growth stalls (< 10% for 2 consecutive weeks)
- Major strategic decision needed (new vertical, partnership)
- Budget overrun (>$120/mo)

**Success Metrics:**
- Weekly reports delivered on time (100%)
- Actionable insights per report (> 3)
- Strategic recommendations accuracy (measured by outcome)

**Tools:**
- Supabase (read all tables: atoms, videos, analytics)
- Analytics Agent API (fetch YouTube metrics)
- Claude API (generate insights, recommendations)
- Telegram Bot (send reports)

**File:** `/agents/executive/ai_ceo_agent.py`

---

### 2. AI Chief of Staff Agent
**Role:** Project management, task orchestration, issue tracking.

**Responsibilities:**
- Manage GitHub issues (create, update, close)
- Track agent performance (uptime, task completion rates)
- Coordinate dependencies (e.g., "Research Agent must finish before Scriptwriter starts")
- Detect blockers (e.g., "Video Assembly Agent failed 3x due to missing footage")
- Prioritize backlog (what to build next)

**Autonomous Capabilities:**
- Create GitHub issues from AI CEO recommendations
- Assign issues to agents (labels, milestones)
- Monitor issue progress (comment updates, status changes)
- Generate daily standups ("Agent X completed Y, Agent Z blocked by Q")
- Close completed issues automatically

**Human-in-Loop Triggers:**
- Agent fails same task 3+ times (needs debugging)
- Critical blocker (e.g., API outage, budget issue)
- Priority conflict (multiple agents requesting same resource)
- Week 1 checklist not completed by deadline

**Success Metrics:**
- Issue backlog size (< 20 open issues)
- Average issue resolution time (< 7 days)
- Blocker detection speed (flagged within 1 hour of occurrence)

**Tools:**
- GitHub API (issues, projects, milestones)
- Supabase (agent_logs table for monitoring)
- Claude API (generate issue descriptions, prioritization logic)
- Telegram Bot (send blocker alerts)

**File:** `/agents/executive/ai_chief_of_staff_agent.py`

---

## Research & Knowledge Base Team (4 Agents)

### 3. Research Agent
**Role:** Ingest authoritative sources, extract raw knowledge, prepare for atomization.

**Responsibilities:**
- Web scraping (Crawl4AI): Siemens/Allen-Bradley manuals, IEEE standards, vendor docs
- YouTube transcript extraction (yt-dlp)
- PDF processing (PyMuPDF, pdfplumber)
- Detect duplicates (don't re-scrape same source)
- Tag sources (vendor, platform, topic, difficulty)
- Store raw data in staging (supabase `research_staging` table)

**Autonomous Capabilities:**
- Daily scraping runs (scheduled via APScheduler)
- Detect new YouTube videos (subscribed channels: RealPars, PLCGuy, AutomationDirect)
- Extract text from PDFs (Siemens S7-1200 manual, AB ControlLogix programming guide)
- Validate source quality (authoritative = vendor docs, IEEE; low-quality = random blogs)
- Deduplication (hash-based, don't re-process same content)

**Human-in-Loop Triggers:**
- Source requires login/paywall (escalate for manual access)
- PDF extraction fails (corrupted file, OCR needed)
- Copyright concern (e.g., entire textbook scraped)
- Low-quality source detected (flag for review)

**Success Metrics:**
- Sources ingested per day (target: 5-10)
- Extraction success rate (> 90%)
- Duplicate detection accuracy (> 95%)
- Storage cost (< $5/mo for raw data)

**Tools:**
- Crawl4AI (web scraping, intelligent extraction)
- yt-dlp (YouTube transcript extraction)
- PyMuPDF / pdfplumber (PDF text extraction)
- Supabase (store raw data in `research_staging` table)
- Claude API (validate quality, tag topics)

**File:** `/agents/research/research_agent.py`

---

### 4. Atom Builder Agent
**Role:** Convert raw research data into structured Knowledge Atoms.

**Responsibilities:**
- Parse raw text from Research Agent
- Extract: title, summary, prerequisites, examples, hazards, code snippets
- Structure as PLCAtom or RIVETAtom (Pydantic models)
- Generate embeddings (OpenAI `text-embedding-3-small`)
- Store in Supabase `knowledge_atoms` table
- Link to source (citation URL, author, date)

**Autonomous Capabilities:**
- Process `research_staging` queue (FIFO)
- Generate atom JSON (IEEE LOM-compliant)
- Validate against Pydantic schema (type checking, required fields)
- Embed atom content (title + summary + code_snippet → vector)
- Store in vector DB (pgvector with HNSW index)

**Human-in-Loop Triggers:**
- Ambiguous content (can't determine prerequisites)
- Safety-critical content (electrical hazards → human review required)
- First 10 atoms (YOU review to set quality standard)
- Atom validation fails (missing required fields)

**Success Metrics:**
- Atoms generated per day (target: 10-20 after Month 1)
- Validation pass rate (> 90%)
- Embedding latency (< 2s per atom)
- Human review approval rate for first 10 atoms (100%)

**Tools:**
- Claude API (parse text, extract structured data)
- OpenAI API (generate embeddings)
- Pydantic (validate atom schema)
- Supabase (store atoms in `knowledge_atoms` table)

**File:** `/agents/research/atom_builder_agent.py`

---

### 5. Atom Librarian Agent
**Role:** Organize atoms into curriculum structure, detect gaps, maintain graph.

**Responsibilities:**
- Cluster atoms by topic (e.g., "electricity basics", "ladder logic", "timers")
- Build prerequisite chains (e.g., Ohm's Law → Circuit Analysis → Troubleshooting)
- Create Modules (10-15 atoms per module)
- Create Courses (3-5 modules per course)
- Detect knowledge gaps (e.g., "Have 'timers' atoms but no 'counters' atoms")
- Maintain atom graph (relations: requires, isPartOf, teaches)

**Autonomous Capabilities:**
- Daily atom clustering (semantic similarity via embeddings)
- Prerequisite chain validation (detect circular dependencies)
- Module/Course generation (based on curriculum templates)
- Gap analysis (identify missing atoms by scanning curriculum plan)
- Update atom relations in Supabase

**Human-in-Loop Triggers:**
- Circular dependency detected (needs human resolution)
- Major curriculum restructure needed (> 10 modules affected)
- Knowledge gap in critical path (blocks video production)

**Success Metrics:**
- Atoms organized into modules (> 80%)
- Prerequisite chain completeness (no orphaned atoms)
- Knowledge gaps detected per week (target: 3-5)
- Module coherence score (semantic similarity within module > 0.7)

**Tools:**
- Supabase (query atoms, update relations)
- OpenAI API (semantic similarity via embeddings)
- NetworkX (graph analysis, detect cycles)
- Claude API (generate module descriptions)

**File:** `/agents/research/atom_librarian_agent.py`

---

### 6. Quality Checker Agent
**Role:** Validate atom accuracy, safety compliance, citation integrity.

**Responsibilities:**
- Cross-reference atoms with authoritative sources
- Detect hallucinations (claims not supported by source)
- Validate safety warnings (electrical hazards, lockout/tagout)
- Check citation integrity (source URLs valid, authors correct)
- Run 6-stage validation pipeline (for RIVET atoms)
- Flag atoms for human review (safety-critical, low-confidence)

**Autonomous Capabilities:**
- Daily validation runs (process new atoms from queue)
- Source verification (fetch original URL, compare content)
- Safety keyword detection ("high voltage", "arc flash", "lockout")
- Citation validation (HTTP requests to source URLs)
- Confidence scoring (0.0-1.0 based on source quality)

**Human-in-Loop Triggers:**
- Safety-critical atom (hazards present)
- Low-confidence atom (score < 0.7)
- Source URL dead/changed (needs manual update)
- Contradiction detected (atom conflicts with authoritative source)

**Success Metrics:**
- Atoms validated per day (target: 50+ by Month 3)
- Hallucination detection rate (manually audit 10 atoms/mo, measure false negatives)
- Citation integrity (> 95% URLs valid)
- Safety flag accuracy (manually audit flagged atoms, measure false positives)

**Tools:**
- Claude API (cross-reference sources, detect contradictions)
- Supabase (query atoms, update validation_stage)
- Requests library (validate URLs)
- Safety keyword database (maintained in `safety_keywords` table)

**File:** `/agents/research/quality_checker_agent.py`

---

## Content Production Team (5 Agents)

### 7. Master Curriculum Agent
**Role:** Design learning paths, plan video sequences, ensure pedagogical soundness.

**Responsibilities:**
- Define A-to-Z video roadmap (100+ videos planned)
- Sequence topics (linear dependencies, spiral curriculum)
- Identify anchor videos (milestones: Videos 1, 10, 25, 50)
- Balance tracks (Electrical Fundamentals, PLC Basics, Advanced)
- Update roadmap based on analytics (double down on popular topics)
- Generate weekly content plan (what to produce next)

**Autonomous Capabilities:**
- Generate video roadmap from atom library (prerequisite chains → video sequence)
- Detect curriculum gaps (missing prerequisites for planned videos)
- Prioritize videos (high-value topics based on search volume, engagement)
- Update roadmap quarterly (based on analytics, community feedback)

**Human-in-Loop Triggers:**
- Major curriculum pivot needed (e.g., Siemens outperforming AB → shift focus)
- First 20 videos (YOU approve sequence to set foundation)
- Knowledge gap blocks production (missing atoms for planned video)

**Success Metrics:**
- Roadmap completeness (100+ videos planned)
- Prerequisite chain validity (no videos requiring non-existent prerequisites)
- Curriculum adherence (videos published follow roadmap > 90%)
- Analytics-driven updates (roadmap adjusted monthly based on data)

**Tools:**
- Supabase (query atoms, modules, courses)
- Claude API (generate curriculum structure, pedagogical recommendations)
- NetworkX (visualize prerequisite chains)
- Analytics Agent API (fetch engagement data)

**File:** `/agents/content/master_curriculum_agent.py`

---

### 8. Content Strategy Agent
**Role:** Plan individual videos, optimize for YouTube algorithm, A/B test ideas.

**Responsibilities:**
- Select next video topic (from Master Curriculum roadmap)
- Research keywords (YouTube autocomplete, Google Trends)
- Generate 3 title options (SEO + curiosity + authority)
- Draft video outline (hook, explanation, example, recap)
- Estimate watch time (based on similar videos)
- Schedule publish time (optimal for target audience)

**Autonomous Capabilities:**
- Daily topic selection (pull from roadmap, prioritize by SEO opportunity)
- Keyword research (YouTube autocomplete API, Google Trends API)
- Title A/B testing (generate 3 options, pick best CTR after 100 impressions)
- Outline generation (based on atom content + pedagogical templates)

**Human-in-Loop Triggers:**
- First 20 videos (YOU approve topic + title + outline)
- Low-confidence topic (unclear SEO opportunity)
- Competitor analysis needed (review similar channels for gaps)

**Success Metrics:**
- Videos planned per week (target: 5-10 by Month 2)
- Title CTR (> 4%)
- Keyword ranking (video appears in top 10 search results for target keyword)
- Watch time accuracy (estimated vs actual within 20%)

**Tools:**
- YouTube Data API (keyword research, search volume)
- Google Trends API (trending topics)
- Claude API (generate titles, outlines)
- Supabase (store video plans in `video_scripts` table)

**File:** `/agents/content/content_strategy_agent.py`

---

### 9. Scriptwriter Agent
**Role:** Write engaging, accurate video scripts from knowledge atoms.

**Responsibilities:**
- Transform atom content into narration script
- Structure: Hook (0:00-0:15) → Explanation (0:15-3:00) → Example (3:00-6:00) → Recap (6:00-7:00)
- Add personality markers ([enthusiastic], [cautionary], [emphasis])
- Include visual cues (show diagram, highlight code, pan to PLC)
- Cite sources (mention "According to Siemens manual...")
- Generate quiz question (end of video)
- Optimize for AVD (pacing, hooks, pattern interrupts)

**Autonomous Capabilities:**
- Generate script from atom + outline
- Add personality markers (based on content type: exciting demo vs safety warning)
- Insert visual cues (detect when diagram/code needed)
- Optimize script length (target 5-12 min based on complexity)
- Validate against atom (no hallucinations, all claims supported)

**Human-in-Loop Triggers:**
- First 20 scripts (YOU review for quality + personality)
- Safety-critical content (electrical hazards)
- Complex topics (advanced PLC concepts, multi-atom synthesis)
- Script validation fails (claims not supported by atoms)

**Success Metrics:**
- Scripts generated per day (target: 3-5 by Month 2)
- Human approval rate (first 20 scripts: 100%)
- AVD correlation (scripts with more hooks → higher AVD)
- Atom fidelity (zero hallucinations detected in post-audit)

**Tools:**
- Claude API (generate scripts, optimize pacing)
- Supabase (query atoms, store scripts in `video_scripts` table)
- Quality Checker Agent API (validate script against atoms)

**File:** `/agents/content/scriptwriter_agent.py`

---

### 10. SEO Agent
**Role:** Optimize metadata (title, description, tags) for discoverability.

**Responsibilities:**
- Refine title (SEO keywords + human appeal)
- Write description (hook, bullets, timestamps, links)
- Generate tags (15-20 relevant tags per video)
- Create playlist assignments (organize into learning paths)
- Optimize for search (target low-competition, high-volume keywords)
- A/B test titles (first 100 impressions, switch to winner)

**Autonomous Capabilities:**
- Generate 3 title variations (test CTR)
- Write YouTube description (template-based + customization)
- Extract tags (from script, atom metadata, keyword research)
- Assign to playlists (based on module/course structure)
- A/B testing (swap title after 100 impressions if CTR < 3%)

**Human-in-Loop Triggers:**
- First 10 videos (YOU approve metadata)
- Low CTR after 48 hours (< 2%)
- Major SEO shift needed (keyword strategy pivot)

**Success Metrics:**
- CTR (target: > 4%)
- Search impressions (video appears in search results > 1K/week)
- Playlist view-through rate (viewers watch next video in playlist > 40%)
- Tag relevance (manual audit: tags match content > 95%)

**Tools:**
- YouTube Data API (set metadata, fetch impressions)
- Claude API (generate descriptions, tags)
- Supabase (store metadata in `video_scripts` table)

**File:** `/agents/content/seo_agent.py`

---

### 11. Thumbnail Agent
**Role:** Generate eye-catching, brand-consistent thumbnails.

**Responsibilities:**
- Generate 3 thumbnail concepts (Canva API / DALLE)
- Consistent branding (logo, color scheme, fonts)
- Visual hierarchy (concept → diagram → benefit)
- A/B test thumbnails (swap after 100 impressions if CTR < 3%)
- Avoid clickbait (thumbnail matches video content)
- Accessibility (high contrast, readable text)

**Autonomous Capabilities:**
- Generate 3 thumbnail options per video (DALLE or Canva templates)
- Apply branding (logo watermark, color palette)
- A/B testing (track CTR per thumbnail)
- Select winner (highest CTR after 100 impressions)

**Human-in-Loop Triggers:**
- First 10 thumbnails (YOU approve to set brand standard)
- CTR < 2% after 48 hours (needs redesign)
- Brand refresh (new logo, color scheme)

**Success Metrics:**
- Thumbnails generated per day (target: 3-5)
- CTR (target: > 4%)
- Brand consistency (manual audit: follows brand guidelines > 95%)
- A/B test win rate (winner outperforms baseline > 60%)

**Tools:**
- OpenAI DALLE (generate images)
- Canva API (template-based thumbnails)
- Pillow (Python image processing, add text/logo)
- YouTube Data API (upload thumbnail, fetch CTR)

**File:** `/agents/content/thumbnail_agent.py`

---

## Media & Publishing Team (4 Agents)

### 12. Voice Production Agent
**Role:** Convert scripts into natural-sounding narration audio.

**Responsibilities:**
- Read script from Scriptwriter Agent
- Parse personality markers ([enthusiastic] → adjust tone)
- Generate audio (ElevenLabs voice clone)
- Validate audio quality (no clipping, balanced levels)
- Add silence/pauses (after key points, before examples)
- Export audio (MP3, 192 kbps)

**Autonomous Capabilities:**
- Generate narration from script (ElevenLabs API)
- Apply emotion markers (adjust stability, clarity, style settings)
- Audio quality check (peak level < -3dB, RMS level -16dB)
- Normalize audio (match loudness standards)

**Human-in-Loop Triggers:**
- First 5 audio files (YOU listen to ensure voice clone quality)
- Audio quality fails (clipping, distortion, robotic artifacts)
- Voice clone update needed (retrain with new samples)

**Success Metrics:**
- Audio files generated per day (target: 3-5 by Month 2)
- Quality pass rate (> 95%)
- Human approval rate for first 5 (100%)
- Robotic artifact detection (< 5% negative feedback on voice)

**Tools:**
- ElevenLabs API (voice cloning, TTS generation)
- Pydub (audio processing, normalization)
- Librosa (audio analysis, quality validation)

**File:** `/agents/media/voice_production_agent.py`

---

### 13. Video Assembly Agent
**Role:** Combine narration + visuals into final video.

**Responsibilities:**
- Sync audio with visual cues (from script)
- Add visuals: diagrams, code snippets, Factory I/O footage, stock clips
- Add captions (accessibility + SEO)
- Add intro/outro (branding, call-to-action)
- Render video (1080p MP4, H.264 codec)
- Validate video quality (no sync issues, readable text)

**Autonomous Capabilities:**
- Parse visual cues from script ("show diagram of 3-wire control")
- Fetch assets (diagrams from `/assets/diagrams/`, code screenshots)
- Sync audio + visuals (MoviePy timeline)
- Generate captions (OpenAI Whisper for timing, script for text)
- Render video (FFmpeg)

**Human-in-Loop Triggers:**
- First 5 videos (YOU watch to ensure quality)
- Visual asset missing (needs manual creation)
- Render fails (codec issue, corrupted file)
- Video quality fails (sync issues, pixelation)

**Success Metrics:**
- Videos assembled per day (target: 3-5 by Month 2)
- Render success rate (> 90%)
- Quality pass rate (> 95%)
- Human approval rate for first 5 (100%)

**Tools:**
- MoviePy (video assembly, timeline sync)
- FFmpeg (rendering, codec management)
- OpenAI Whisper (caption timing)
- Supabase (fetch video plan, store video metadata)

**File:** `/agents/media/video_assembly_agent.py`

---

### 14. Publishing Strategy Agent
**Role:** Schedule uploads, optimize timing, manage playlists.

**Responsibilities:**
- Determine publish time (based on target audience timezone + analytics)
- Set visibility (public, unlisted, scheduled)
- Assign to playlists (organize into learning paths)
- Generate community post (announce new video)
- Schedule social amplification (TikTok/Instagram clips follow 24 hours later)

**Autonomous Capabilities:**
- Optimal time calculation (analyze past video performance by hour)
- Playlist assignment (based on module/course structure)
- Schedule upload (YouTube Data API)
- Generate community post (announce video with key takeaway)

**Human-in-Loop Triggers:**
- First 10 videos (YOU approve publish schedule)
- Major algorithm change (YouTube policy update)
- Publish fails (API error, quota exceeded)

**Success Metrics:**
- Videos scheduled per week (target: 2-3 by Month 2)
- Optimal time accuracy (scheduled time → higher views than baseline)
- Playlist view-through rate (> 40%)
- Community post engagement (> 2% of subscribers interact)

**Tools:**
- YouTube Data API (schedule upload, set metadata, create community posts)
- Supabase (store publish schedule)
- Analytics Agent API (fetch optimal publish time data)

**File:** `/agents/media/publishing_strategy_agent.py`

---

### 15. YouTube Uploader Agent
**Role:** Execute uploads to YouTube, handle errors, confirm success.

**Responsibilities:**
- Upload video file (YouTube Data API)
- Set metadata (title, description, tags, thumbnail)
- Set visibility + schedule
- Handle upload errors (retry with exponential backoff)
- Confirm success (video ID returned)
- Store video metadata in Supabase (`published_videos` table)

**Autonomous Capabilities:**
- Upload video (resumable upload for large files)
- Retry on failure (3 attempts with backoff)
- Validate upload (video ID valid, metadata set correctly)
- Log upload event (timestamp, video ID, status)

**Human-in-Loop Triggers:**
- Upload fails after 3 retries (API quota, network issue)
- Video stuck in processing (YouTube-side issue)
- Copyright claim (Content ID match)

**Success Metrics:**
- Upload success rate (> 95%)
- Average upload time (< 10 min for 1080p)
- Retry necessity (< 5% of uploads require retry)
- Metadata accuracy (manual audit: 100% correct)

**Tools:**
- YouTube Data API (resumable upload, set metadata)
- Requests library (HTTP resumable upload)
- Supabase (log uploads in `published_videos` table)

**File:** `/agents/media/youtube_uploader_agent.py`

---

## Engagement & Analytics Team (3 Agents)

### 16. Community Agent
**Role:** Engage with comments, answer questions, flag toxicity.

**Responsibilities:**
- Monitor new comments (YouTube Data API)
- Respond to questions (atom-backed answers)
- Pin helpful comments (community contributions)
- Flag toxic comments (hate speech, spam)
- Escalate complex questions (needs human expert)
- Generate engagement prompts ("What should I cover next?")

**Autonomous Capabilities:**
- Fetch new comments (every 1 hour)
- Generate responses (atom-backed, cite sources)
- Toxicity detection (Perspective API)
- Spam detection (pattern matching, low-effort comments)
- Heart comments (positive feedback, constructive criticism)

**Human-in-Loop Triggers:**
- First 20 responses (YOU approve tone + accuracy)
- Complex technical question (beyond atom knowledge)
- Toxic comment escalation (needs ban decision)
- Negative feedback trend (multiple users report same issue)

**Success Metrics:**
- Response rate (> 50% of questions answered within 24 hours)
- Response quality (< 5% negative feedback on responses)
- Toxicity detection accuracy (manual audit: > 90%)
- Engagement boost (videos with active comments → higher CTR on next video)

**Tools:**
- YouTube Data API (fetch comments, post replies, moderate)
- Claude API (generate responses)
- Perspective API (toxicity detection)
- Supabase (log responses in `comment_responses` table)

**File:** `/agents/engagement/community_agent.py`

---

### 17. Analytics Agent
**Role:** Track metrics, identify trends, generate insights.

**Responsibilities:**
- Fetch YouTube Analytics (views, watch time, CTR, AVD, traffic sources)
- Fetch Supabase metrics (atoms created, videos published, revenue)
- Detect trends (growth rate, engagement spikes/drops)
- Identify top performers (videos exceeding 60% AVD)
- Identify underperformers (videos below 40% AVD)
- Generate weekly/monthly reports (sent to AI CEO)

**Autonomous Capabilities:**
- Daily data fetch (YouTube + Supabase)
- Trend detection (compare to 7-day/30-day average)
- Anomaly detection (sudden spikes/drops)
- Report generation (summarize key metrics + insights)

**Human-in-Loop Triggers:**
- Negative trend (> 20% drop in key metric)
- Data anomaly (outlier not explained by known factors)
- Report review (monthly deep dive with YOU)

**Success Metrics:**
- Data freshness (< 24 hours lag)
- Report delivery (100% on time)
- Insight quality (> 3 actionable insights per report)
- Trend detection accuracy (manual audit: > 90%)

**Tools:**
- YouTube Analytics API (fetch channel + video metrics)
- Supabase (query all tables for internal metrics)
- Pandas (data analysis, trend detection)
- Claude API (generate insights, summarize reports)

**File:** `/agents/engagement/analytics_agent.py`

---

### 18. Social Amplifier Agent
**Role:** Distribute content across platforms, repurpose clips, drive traffic.

**Responsibilities:**
- Extract 30-60s clips from full videos (best moments)
- Reformat for TikTok/Instagram (9:16 vertical)
- Generate social captions (hook + context + CTA)
- Post to platforms (TikTok, Instagram, LinkedIn, Reddit, Twitter)
- Cross-link to YouTube (drive traffic to full video)
- Engage with social comments (respond to questions)

**Autonomous Capabilities:**
- Clip extraction (detect high-engagement moments via transcript sentiment)
- Reformat video (crop to 9:16, add captions)
- Generate captions (platform-specific: TikTok = trending sounds, LinkedIn = professional tone)
- Post via APIs (TikTok API, Instagram Graph API, Reddit API, Twitter API)
- Schedule posts (stagger across platforms)

**Human-in-Loop Triggers:**
- First 10 social posts (YOU approve tone + strategy)
- Platform policy violation (post removed, account flagged)
- Negative engagement (comments overwhelmingly negative)

**Success Metrics:**
- Clips generated per video (target: 3 per full video)
- Post success rate (> 95%)
- Traffic driven to YouTube (> 10% of video views from social)
- Cross-platform growth (TikTok 100K, Instagram 50K by Month 6)

**Tools:**
- FFmpeg (clip extraction, reformatting)
- Platform APIs (TikTok, Instagram, Reddit, Twitter)
- Claude API (generate captions)
- Supabase (log social posts in `social_posts` table)

**File:** `/agents/engagement/social_amplifier_agent.py`

---

## Agent Coordination & Orchestration

### Sequential Workflows (Phase 1: Orchestration)

**Video Production Pipeline:**
```
Master Curriculum (select topic)
    ↓
Content Strategy (keyword research, outline)
    ↓
Scriptwriter (generate script)
    ↓
SEO Agent (optimize metadata)
    ↓
Thumbnail Agent (generate thumbnail)
    ↓
Voice Production (generate narration)
    ↓
Video Assembly (combine into video)
    ↓
Publishing Strategy (schedule upload)
    ↓
YouTube Uploader (execute upload)
    ↓
Social Amplifier (extract clips, post to social)
```

**Knowledge Base Pipeline:**
```
Research Agent (ingest sources)
    ↓
Atom Builder (structure as atoms)
    ↓
Quality Checker (validate accuracy)
    ↓
Atom Librarian (organize into curriculum)
    ↓
Master Curriculum (update roadmap)
```

### Parallel Workflows (Phase 2: Concurrency)

**Daily Operations (all run simultaneously):**
- Research Agent (scrape new sources)
- Community Agent (respond to comments)
- Analytics Agent (fetch metrics)
- Quality Checker (validate new atoms)
- AI CEO (monitor KPIs)
- AI Chief of Staff (track issue progress)

**Event-Driven Triggers:**
- New video published → Social Amplifier extracts clips
- Low CTR detected (< 2% after 48 hours) → SEO Agent optimizes metadata
- Comment question asked → Community Agent generates response
- Knowledge gap detected → Research Agent prioritizes topic

### Human-in-Loop Gates

**Approval Required (Tier 1: High-Stakes):**
- Videos 1-20 (foundation)
- First 20 comment responses (establish tone)
- First 10 knowledge atoms (set quality standard)
- Brand changes (logo, channel name)
- B2B contracts (corporate training, licensing)

**Sampling Required (Tier 2: Medium-Stakes):**
- Videos 21-50 (every 3rd video)
- Comment responses 21-50 (every 5th response)
- Social posts first 30 days (daily review)
- Thumbnail changes (A/B test results)

**Autonomous (Tier 3: Low-Stakes):**
- Videos 51+ (exception flagging only)
- Comment responses 51+ (toxicity/complex escalation only)
- Social posts after 30 days (policy violation escalation only)
- Metadata optimizations (A/B tests, tag updates)

---

## Agent Communication Protocol

### Inter-Agent Messaging (Supabase `agent_messages` table)

**Schema:**
```sql
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    message_type TEXT NOT NULL, -- 'task', 'notification', 'error', 'query'
    payload JSONB NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);
```

**Example Messages:**

```json
// Master Curriculum → Content Strategy
{
  "from_agent": "master_curriculum_agent",
  "to_agent": "content_strategy_agent",
  "message_type": "task",
  "payload": {
    "task": "plan_video",
    "topic": "ohms_law",
    "atom_ids": ["plc:generic:ohms-law", "plc:generic:voltage-current-resistance"],
    "priority": "high",
    "deadline": "2025-12-12T00:00:00Z"
  }
}

// Quality Checker → Atom Builder (error)
{
  "from_agent": "quality_checker_agent",
  "to_agent": "atom_builder_agent",
  "message_type": "error",
  "payload": {
    "error": "citation_invalid",
    "atom_id": "plc:ab:timer-on-delay",
    "details": "Source URL returns 404",
    "recommendation": "Re-scrape source or find alternative citation"
  }
}

// Analytics Agent → AI CEO (notification)
{
  "from_agent": "analytics_agent",
  "to_agent": "ai_ceo_agent",
  "message_type": "notification",
  "payload": {
    "alert": "negative_trend",
    "metric": "avg_view_duration",
    "change": "-22%",
    "period": "last_7_days",
    "recommendation": "Review recent videos for pacing issues"
  }
}
```

### Event Bus (Supabase Realtime)

**Publish-Subscribe Pattern:**
- Agents subscribe to events (e.g., `video_published`, `atom_created`, `comment_posted`)
- Agents publish events when tasks complete
- Decouples agents (no direct dependencies)

**Example Events:**

```python
# YouTube Uploader publishes event
supabase.channel('agent_events').send({
    'type': 'broadcast',
    'event': 'video_published',
    'payload': {
        'video_id': 'xyz123',
        'title': 'Ohm\'s Law Explained',
        'url': 'https://youtube.com/watch?v=xyz123',
        'published_at': '2025-12-10T14:30:00Z'
    }
})

# Social Amplifier subscribes and reacts
supabase.channel('agent_events').on_broadcast(
    event='video_published',
    callback=lambda payload: extract_clips_and_post(payload['video_id'])
).subscribe()
```

---

## Agent Monitoring & Health Checks

### Heartbeat System (Supabase `agent_status` table)

**Schema:**
```sql
CREATE TABLE agent_status (
    agent_name TEXT PRIMARY KEY,
    status TEXT NOT NULL, -- 'running', 'idle', 'error', 'stopped'
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    tasks_completed_today INT DEFAULT 0,
    tasks_failed_today INT DEFAULT 0,
    current_task TEXT,
    error_message TEXT
);
```

**Health Check Rules:**
- Agent sends heartbeat every 5 minutes
- AI Chief of Staff monitors heartbeat table
- Alert if heartbeat not received in 10 minutes
- Alert if error status persists > 30 minutes

### Performance Metrics (Supabase `agent_metrics` table)

**Schema:**
```sql
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value FLOAT NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);
```

**Example Metrics:**
- `scriptwriter_agent.scripts_generated_per_day`
- `youtube_uploader_agent.upload_success_rate`
- `community_agent.response_time_seconds`
- `analytics_agent.insight_count_per_report`

---

## Agent Development Roadmap

### Week 1 (Foundation)
- ✅ AI CEO Agent (basic KPI tracking)
- ✅ AI Chief of Staff Agent (GitHub issue management)
- ⏳ Research Agent (Issue #47)
- ⏳ Atom Builder Agent (partial, needs Quality Checker integration)

### Week 2-3 (Content Pipeline)
- ⏳ Scriptwriter Agent (Issue #48)
- Master Curriculum Agent
- Content Strategy Agent
- SEO Agent

### Week 4 (Media Production)
- Voice Production Agent
- Video Assembly Agent
- Thumbnail Agent

### Week 5 (Publishing)
- Publishing Strategy Agent
- YouTube Uploader Agent

### Week 6 (Engagement)
- Community Agent
- Analytics Agent
- Social Amplifier Agent

### Week 7 (Knowledge Base Completion)
- Quality Checker Agent
- Atom Librarian Agent

### Week 8 (Polish & Integration)
- Inter-agent communication (event bus)
- Monitoring dashboard
- Human-in-loop UI (approval queue)

---

## Tools & Infrastructure

### Agent Execution Environment
- **Python 3.10+** (all agents pure Python)
- **APScheduler** (task scheduling, cron-like)
- **Docker** (optional, for isolated agent execution)
- **Supabase** (database, realtime, storage)

### Agent Communication
- **Supabase Realtime** (pub/sub event bus)
- **Supabase `agent_messages` table** (task queue)
- **Redis** (optional, for high-frequency messaging)

### LLM & AI APIs
- **Claude API** (agent intelligence, script generation, analysis)
- **OpenAI API** (embeddings, Whisper for captions)
- **ElevenLabs API** (voice cloning, TTS)
- **DALLE / Canva API** (thumbnail generation)

### Media Processing
- **FFmpeg** (video rendering, clip extraction)
- **MoviePy** (video assembly, timeline sync)
- **Pydub** (audio processing)
- **Pillow** (image processing, thumbnails)

### Platform APIs
- **YouTube Data API** (upload, metadata, analytics)
- **YouTube Analytics API** (metrics)
- **TikTok API** (post videos)
- **Instagram Graph API** (post reels)
- **Reddit API** (post links, comments)
- **Twitter API** (post tweets)

---

## Success Criteria

### Week 8 (Agent System Complete)
- ✅ All 18 agents implemented
- ✅ Video production pipeline functional (topic → published video)
- ✅ Knowledge base pipeline functional (source → validated atom)
- ✅ Human-in-loop approval UI functional
- ✅ Monitoring dashboard functional

### Month 3 (Autonomous Operations)
- ✅ Agents produce 80% autonomously (you review exceptions only)
- ✅ 30+ videos published
- ✅ 100+ knowledge atoms
- ✅ YouTube Partner Program active

### Month 6 (Scale Achieved)
- ✅ Agents fully autonomous (exception handling only)
- ✅ 60+ videos published
- ✅ 200+ knowledge atoms
- ✅ Multi-platform presence (TikTok, Instagram, LinkedIn)
- ✅ First B2B inquiry

---

## Next Steps

1. ✅ Read this document (you're here)
2. Complete Issue #47: Build Research Agent
3. Complete Issue #48: Build Scriptwriter Agent
4. Implement remaining agents (Weeks 2-7)
5. Integrate inter-agent communication (event bus)
6. Build monitoring dashboard (Week 8)
7. Launch full autonomous pipeline (Month 3)

**The 18-agent system is your workforce. You're the architect and strategist.**
