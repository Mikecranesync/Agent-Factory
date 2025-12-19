# Agent Factory Roadmap Timeline

**Diagram Type:** Gantt Chart
**Purpose:** Feature roadmap from Backlog.md with milestones and delivery phases
**Update When:** Task completed (mark `done`), major milestone reached, timeline changes

## Diagram

```mermaid
gantt
    title Agent Factory Roadmap (2025-2026)
    dateFormat YYYY-MM-DD

    section SCAFFOLD Phase 1 (Complete)
    Core Orchestrator (task-1) :done, 2025-12-15, 2025-12-18
    Backlog Parser (task-scaffold-backlog-parser) :done, 2025-12-18, 2025-12-19

    section SCAFFOLD Phase 2
    Context Assembler (CLAUDE.md + snapshot) :crit, 2025-12-20, 2025-12-27
    Git Worktree Manager :crit, 2025-12-20, 2025-12-27
    PR Creation & Auto-Approval :2025-12-27, 2026-01-03
    Backlog Status Sync :2026-01-03, 2026-01-10
    Structured Logging :2026-01-10, 2026-01-17

    section Validation Tasks
    Knowledge Base (24 blog posts) :2025-12-27, 2026-01-10
    Task Parsing (100+ tasks) :2026-01-03, 2026-01-10
    Video Extraction (24 clips) :2026-01-10, 2026-01-17
    YouTube API Integration :2026-01-17, 2026-01-24

    section RIVET Pro
    Phase 6: Logging :2026-01-17, 2026-02-07
    Phase 7: API/Webhooks :2026-02-07, 2026-02-28

    section PLC Tutor
    Multi-Agent Orchestration :crit, 2026-01-10, 2026-01-31
    YouTube Automation Pipeline :2026-01-24, 2026-02-14
    Voice Clone (ElevenLabs) :2026-02-07, 2026-02-21
    A-to-Z Curriculum Roadmap :2026-02-14, 2026-03-07

    section Diagram System
    Generate Initial Diagrams (task-29) :active, 2025-12-19, 2025-12-20
    PR Template & Checklist :2025-12-20, 2025-12-21
    CI/CD Validation :2025-12-21, 2025-12-23
    SCAFFOLD Integration :2025-12-23, 2025-12-27
    User Documentation :2025-12-27, 2026-01-03
```

## Milestones

### ✅ SCAFFOLD Phase 1 Complete (Dec 19, 2025)
- Core orchestrator implemented (task-1)
- Backlog parser with MCP integration (task-scaffold-backlog-parser)
- 26 unit tests passing
- Foundation for autonomous development established

### 🎯 SCAFFOLD Phase 2 (Dec 20 - Jan 17, 2026)
- **Critical Path**: Context Assembler + Worktree Manager (enables autonomous code generation)
- **Follow-on**: PR creation, Backlog sync, structured logging
- **Goal**: Fully autonomous development loop operational

### 🎯 Diagram System (Dec 19 - Jan 3, 2026)
- **Active**: Generate initial diagrams (task-29)
- **Next**: PR template with mandatory checklist
- **Follow-on**: CI/CD validation, SCAFFOLD integration, user docs
- **Goal**: Living documentation synchronized with code

### 🎯 RIVET Pro (Jan 17 - Feb 28, 2026)
- **Phase 6**: Structured logging and observability
- **Phase 7**: REST API + webhook integrations
- **Goal**: Production-ready industrial maintenance platform

### 🎯 PLC Tutor (Jan 10 - Mar 7, 2026)
- **Critical**: Multi-agent orchestration (18 agents)
- **Content**: YouTube automation + voice clone
- **Curriculum**: A-to-Z roadmap (electricity → AI automation)
- **Goal**: Autonomous educational content generation

## Timeline Summary

- **Week 1 (Dec 15-19)**: SCAFFOLD Phase 1 ✅
- **Week 2-5 (Dec 20 - Jan 17)**: SCAFFOLD Phase 2 + Diagram System
- **Week 6-9 (Jan 17 - Feb 14)**: RIVET Pro Phase 6-7 + PLC Tutor kickoff
- **Week 10-13 (Feb 14 - Mar 7)**: PLC Tutor content pipeline + curriculum

## Dependencies

**SCAFFOLD Phase 2** depends on:
- Phase 1 complete ✅
- Backlog parser operational ✅
- Git worktrees available ✅

**Diagram System** depends on:
- Repository structure stable (ongoing)
- PR template enforcement (Dec 20)
- CI/CD validation (Dec 21)

**RIVET Pro Phase 6-7** depends on:
- Knowledge base seeded (validation tasks)
- Agent orchestration (SCAFFOLD Phase 2)
- Database schema stable (Q1 2026)

**PLC Tutor** depends on:
- 18-agent system design complete ✅
- YouTube-Wiki strategy approved ✅
- Voice clone ready (ElevenLabs setup)
- Content roadmap A-to-Z complete ✅

## Related Diagrams

- See `01-execution-flow.md` for SCAFFOLD workflow
- See `02-architecture.md` for module dependencies
- See `06-knowledge-map.md` for strategic priorities
