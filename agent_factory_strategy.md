# Agent Factory & Industrial Skills Hub: Complete Strategy

## Vision

Build an **autonomous knowledge-creation and content-distribution system** powered by AI agents that:
1. Learn PLC/industrial automation from scratch using closed-loop simulation (Factory I/O).
2. Automatically build a comprehensive knowledge base (KB) organized as structured learning atoms.
3. Generate YouTube content (long-form videos, shorts, lessons) continuously, with minimal manual effort.
4. Monetize via education/courses while the learning loop matures.

You are the architect and final reviewer. The system runs 24/7, generating content and revenue while you focus on core innovation.

---

## Core System Architecture

### Three Parallel Agents (Pure Python)

#### 1. **Learning Agent (Inner Loop)**
- **Goal:** Become an expert PLC/automation engineer via iterative practice.
- **Process:**
  - Read PLC concepts from KB atoms.
  - Generate ladder logic / Structured Text (ST) code for tasks.
  - Run simulations in Factory I/O, log successes/failures.
  - Refine atoms based on what fails; update KB.
- **Output:** Structured logs, code versions, final "lesson learned" summaries.

#### 2. **Content/Media Agent (Outer Loop)**
- **Goal:** Convert everything the learning agent does into marketable content.
- **Process:**
  - Consume artifacts from learning agent (task specs, sim results, code history, KB updates).
  - Draft scripts: "How the AI learned start/stop circuits in 3 attempts."
  - Generate lesson outlines, quizzes, lab exercises.
  - Produce social posts, thumbnails, and metadata.
- **Output:** Video scripts, course modules, KB articles, YouTube metadata.

#### 3. **Digital Clone / Uploader Agent**
- **Goal:** Turn scripts into published videos with no human recording.
- **Process:**
  - Take video scripts from content agent.
  - Generate audio using voice cloning (ElevenLabs, etc., trained on short samples of your voice).
  - Assemble video: narration + Factory I/O footage / simulations / diagrams.
  - Upload to YouTube using YouTube Data API.
  - Schedule posts and manage playlists.
- **Output:** Published videos on Industrial Skills Hub channel.

---

## Knowledge Base: Atoms & Schema

### Core Data Structures (Pydantic models)

**Learning Object** (base class from IEEE LOM / LRMI standards):
```
- id, identifiers, title, description
- created_at, updated_at, version
- authors, source_urls
- educational_level (intro/intermediate/advanced)
- learning_resource_type (explanation, example, exercise, simulation, etc.)
- typical_learning_time_minutes
- intended_audience (student, technician, engineer, manager)
- alignments (teaches X, requires Y, assesses Z)
- relations (isPartOf, hasPart, requires, isVersionOf, references, simulates)
```

**PLCAtom** (specialized for industrial/PLC content):
```
- Inherits from LearningObject
- domain (electricity, plc, drives, safety, ai_agent)
- vendor (siemens, allen_bradley, generic)
- plc_language (ladder, stl, fbd, scl)
- code_snippet (canonical example code)
- io_signals (tags involved)
- hazards (safety warnings)
- quiz_question_ids (assessment hooks)
```

**Module & Course** (curriculum structure):
```
Module:
  - id, title, description
  - atom_ids (ordered list)
  - level

Course:
  - id, title, description
  - module_ids (ordered)
  - estimated_hours
```

### Why This Schema

- **Industry-standard:** Aligns with IEEE Learning Object Metadata, IMS, LRMI/OER Schema; proven for educational KB systems.
- **Captures everything:** Metadata, educational attributes, graph structure (prerequisites, relationships), code snippets, hazards, assessments.
- **Queryable:** Agents can traverse prerequisites, build curriculum paths, and generate content from any atom.
- **Extensible:** Add fields (difficulty scores, learner feedback, reliability metrics) as the system matures.

---

## Video/Content Pipeline

### VideoScript (from PLCAtom)
```
- id, title, description
- outline (bullet sections)
- script_text (full narration for TTS)
- atom_ids (which atoms this teaches)
- level, duration_minutes
```

### UploadJob (ready for YouTube)
```
- id, channel ("industrial_skills_hub")
- video_script_id
- media (audio_path, video_path, thumbnail_path)
- youtube_title, youtube_description
- tags, playlist_ids
- visibility, scheduled_time
```

### Workflow

1. Learning agent runs → produces artifact (code, sim result, lesson learned).
2. Content agent consumes → drafts VideoScript.
3. Media agent processes:
   - Script → TTS (voice-cloned audio).
   - Audio + Factory I/O footage / diagrams → video (MoviePy, FFmpeg).
   - Generate thumbnail, title, description, tags.
4. Uploader agent → push UploadJob to YouTube API.
5. Scheduler maintains cadence (daily, weekly, etc.).

---

## Implementation Stack

- **Language:** Python (pure code, no n8n).
- **Framework:** Claude Code CLI for rapid iteration.
- **Agents:** Pydantic models, LLM calls (Claude API).
- **KB Storage:** Vector DB (e.g., Pinecone, Weaviate) + relational schema for atoms and relations.
- **Video Generation:**
  - TTS: ElevenLabs (voice cloning), Synthesia, or HeyGen (if avatar needed).
  - Video assembly: MoviePy, FFmpeg, Shotstack.
  - Stock/sim footage: Factory I/O exports, stock clips.
- **YouTube API:** google-auth-oauthlib, google-api-python-client.
- **Scheduling:** APScheduler or cron.

### Module Layout (in Agent-Factory repo)

```
agent_factory/
├── models.py                    # All Pydantic schemas
├── kb/
│   ├── atom_store.py            # Vector DB + relational storage
│   ├── atom_scraper.py          # Ingest manuals, standards
│   └── atoms/                   # JSON/YAML atom definitions
├── agents/
│   ├── learning_agent.py        # Factory I/O loop, code gen
│   ├── content_agent.py         # Script gen, curriculum
│   └── uploader_agent.py        # YouTube API, scheduling
├── media/
│   ├── tts.py                   # Voice cloning
│   ├── video.py                 # Assembly (MoviePy, FFmpeg)
│   └── assets.py                # Thumbnail gen, stock footage
├── publish/
│   ├── youtube.py               # YouTube Data API wrapper
│   └── scheduler.py             # APScheduler runner
└── runner.py                    # Main entrypoint
```

---

## Launch Strategy: Industrial Skills Hub

### Phase 1: Build KB & Prove the Loop (Weeks 1-4)

- Set up models.py and basic atom store.
- Manually create 10-15 foundational atoms (electricity basics, voltage/current, resistance, Ohm's Law, etc.).
- Run learning agent on simple Factory I/O tasks.
- Verify learning agent can generate ladder + ST code and improve via feedback.
- Manually review and publish 2-3 proof-of-concept videos to the channel.

### Phase 2: Automate Content Gen (Weeks 5-8)

- Build content agent to draft scripts from atoms.
- Wire TTS + simple video renderer (screen recordings + narration).
- Publish 1-2 videos per week via uploader agent.
- Gather YouTube analytics and feedback.

### Phase 3: Scale to Courses (Weeks 9-12)

- Expand KB to 50+ atoms covering intro → intermediate.
- Organize into modules and courses (basic electricity, PLC fundamentals, etc.).
- Generate course playlists on YouTube.
- Launch optional free tier (public videos) + premium tier (course bundles, interactive tutor).

### Phase 4: Monetize & Iterate (Month 3+)

- Sell structured courses (Gumroad, Teachable, or direct).
- Offer premium access to tutor/advisor (agent + human review).
- Optimize based on watch time, completion, and learner feedback.
- Expand to drives, safety, AI automation topics.

---

## Content Roadmap: Electricity → Advanced AI

### Track 1: Foundational Theory
- Electricity basics (voltage, current, resistance, Ohm's Law, power).
- Sensors, actuators, motors, relays, safety.
- ~20 atoms, ~10 videos.

### Track 2: PLC Fundamentals
- Ladder logic basics, timers, counters, interlocks.
- Structured Text intro, conversion (ladder ↔ ST).
- Siemens vs. Allen-Bradley differences.
- ~30 atoms, ~15 videos.

### Track 3: Advanced & AI
- Complex state machines, motion control, data manipulation.
- "Watch the AI learn" episodes: how your agent designed circuits, what it tried, how it failed and improved.
- AI + PLC fusion: how agents can generate and test code autonomously.
- ~20+ atoms, ongoing.

**Why ladder ↔ ST conversion matters:**
- Industry reality: electricians need ladder for troubleshooting; complex logic requires ST.
- Your agents should canonicalize in ST (cleaner for codegen) but always export ladder for human techs.
- Teaching both is industry standard and matches how RealPars, AutomationDirect, and others structure courses.

---

## Revenue Model

### Free Tier
- YouTube channel (ads, organic growth, SEO).
- Core lessons (electricity basics, PLC fundamentals).
- Blog posts and KB articles.

### Paid Tier
- Structured courses: "Electricity Fundamentals to PLC Expert" ($99–$299).
- Lab kits: Factory I/O project templates, sim scenarios.
- Interactive tutor: chat with the agent over lessons, personalized exercises.
- "AI Agent Showcase": premium features where you can submit tasks and watch the AI generate + test PLC code live.

### B2B (Later)
- Licensed content for corporate training.
- API access to the KB + agent (other automation schools license your atoms + agents).
- White-label tutor for integrators and training vendors.

---

## Why This Works for You

1. **Leverage your constraints:** No time to record videos → use voice clone + automation.
2. **Reuse everything:** KB building = curriculum building = content generation. No redundant effort.
3. **Prove the model fast:** Start monetizing (YouTube ads, courses) in weeks, not months.
4. **Future-proof:** As the learning agent matures, it becomes a **product** (tutor/advisor), not just a knowledge source.
5. **Scalable:** One atom can become a video, a quiz, a course module, a social post, and a API training example. Agents multiply your output.

---

## Next Steps for Claude Code CLI

1. **Create `models.py`** with all Pydantic schemas (LearningObject, PLCAtom, Module, Course, VideoScript, UploadJob).
2. **Scaffold `kb/atom_store.py`** with a minimal in-memory store and vector DB adapter stubs.
3. **Build `agents/content_agent.py`** to take a PLCAtom and draft a VideoScript using Claude API.
4. **Implement `publish/youtube.py`** wrapper around YouTube Data API (OAuth, upload, set metadata).
5. **Create `runner.py`** to orchestrate: pull atoms → generate scripts → render video → upload.

Each module is testable in isolation; iterate with Claude Code CLI as you refine the schema and agent logic.

---

## Key Metrics to Track

- **KB:** Number of atoms, coverage (intro/intermediate/advanced), prerequisite chains.
- **Content:** Videos published per week, average watch time, completion rate.
- **Revenue:** YouTube ad revenue, course enrollment, customer LTV.
- **Learning loop:** Agent success rate (% of sim tasks solved), code quality (test pass rate).

---

## Resources & References

- IEEE Learning Object Metadata (LOM) standard: [web:655][web:664][web:667]
- LRMI / OER Schema: [web:663][web:668]
- Python YouTube automation repos: [web:634][web:627]
- YouTube Data API (Python): [web:644][web:639][web:647]
- Ladder vs. Structured Text in industry: [web:669][web:674][web:680]
