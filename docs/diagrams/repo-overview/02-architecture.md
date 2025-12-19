# Agent Factory Architecture

**Diagram Type:** Module Dependency Graph
**Purpose:** High-level system architecture showing module relationships and integration points
**Update When:** New module/package added, dependencies change, integration points added

## Diagram

```mermaid
graph TD
    subgraph Core["Core Infrastructure"]
        AF[AgentFactory<br/>multi-LLM orchestration]
        DB[DatabaseManager<br/>PostgreSQL + Supabase]
        MEM[MemoryStorage<br/>pgvector search]
        SET[SettingsService<br/>runtime config]
    end

    subgraph SCAFFOLD["SCAFFOLD Platform"]
        ORCH[ScaffoldOrchestrator<br/>autonomous dev loop]
        FETCH[TaskFetcher<br/>Backlog.md parser]
        ROUTE[TaskRouter<br/>handler routing]
        SESS[SessionManager<br/>worktree + safety]
        RES[ResultProcessor<br/>PR creation]
    end

    subgraph RIVET["RIVET Pro"]
        RORCH[RivetOrchestrator<br/>4-route system]
        INT[IntentDetector<br/>query classification]
        CONF[ConfidenceScorer<br/>KB coverage]
        SME[SME Agents<br/>vendor specialists]
    end

    subgraph Workflows["LangGraph Workflows"]
        ING[IngestionChain<br/>7-stage pipeline]
        GRAPH[GraphOrchestrator<br/>multi-agent coord]
        COLLAB[CollaborationPatterns<br/>agent teams]
    end

    subgraph Agents["Agent Teams"]
        EXEC[Executive<br/>CEO, COS]
        RES_A[Research<br/>scraping, atoms]
        CONT[Content<br/>curriculum, scripts]
        MEDIA[Media<br/>voice, video]
        ENG[Engagement<br/>analytics, social]
    end

    %% Core dependencies
    ORCH --> AF
    ORCH --> DB
    FETCH --> ORCH
    ROUTE --> ORCH
    SESS --> ORCH
    RES --> ORCH

    RORCH --> AF
    RORCH --> MEM
    INT --> RORCH
    CONF --> RORCH
    SME --> RORCH

    ING --> DB
    ING --> MEM
    GRAPH --> Workflows
    COLLAB --> Workflows

    Agents --> AF
    Agents --> Workflows

    AF --> SET
    DB --> MEM
    MEM --> SET

    style SCAFFOLD fill:#e1f5ff
    style RIVET fill:#fff3e0
    style Workflows fill:#f3e5f5
    style Agents fill:#e8f5e9
    style Core fill:#fce4ec
```

## Module Descriptions

### Core Infrastructure

- **AgentFactory**: Multi-LLM orchestration layer (Claude, GPT-4, Gemini)
- **DatabaseManager**: Multi-provider PostgreSQL (Neon, Supabase, Railway)
- **MemoryStorage**: pgvector semantic search + hybrid retrieval
- **SettingsService**: Runtime configuration (database-backed, .env fallback)

### SCAFFOLD Platform

- **ScaffoldOrchestrator**: Autonomous development loop coordinator
- **TaskFetcher**: Backlog.md parser with dependency resolution
- **TaskRouter**: Route tasks to handlers (claude-code, manual)
- **SessionManager**: Worktree allocation + safety monitoring
- **ResultProcessor**: PR creation + Backlog.md synchronization

### RIVET Pro

- **RivetOrchestrator**: 4-route industrial maintenance routing
- **IntentDetector**: Query classification (vendor, category, complexity)
- **ConfidenceScorer**: Knowledge base coverage analysis
- **SME Agents**: Vendor-specific specialists (Rockwell, Siemens, etc.)

### LangGraph Workflows

- **IngestionChain**: 7-stage pipeline (Source → Atoms → Validation → Storage)
- **GraphOrchestrator**: Multi-agent workflow coordination
- **CollaborationPatterns**: Agent team patterns (research, content, media)

### Agent Teams

- **Executive**: AI CEO, Chief of Staff (strategy, KPIs)
- **Research**: Research Agent, Atom Builder, Quality Checker
- **Content**: Curriculum Designer, Scriptwriter, SEO Agent
- **Media**: Voice Production, Video Assembly, YouTube Uploader
- **Engagement**: Analytics Agent, Community Manager, Social Amplifier

## External Dependencies

- **MCP Servers**: Backlog.md, GitHub, Playwright, Memory
- **Supabase**: PostgreSQL 16 + pgvector + Auth
- **Neon/Railway**: Alternative database providers
- **VPS (Hostinger)**: 24/7 knowledge base ingestion (Redis queue + Ollama)
- **ElevenLabs**: Voice clone for autonomous narration
- **LangChain/LangGraph**: Workflow orchestration

## Related Diagrams

- See `01-execution-flow.md` for SCAFFOLD workflow
- See `03-orchestrator-states.md` for state machine
- See `05-data-model.md` for entity relationships
