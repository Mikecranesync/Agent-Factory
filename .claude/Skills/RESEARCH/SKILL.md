# RESEARCH Skill

## Purpose
Multi-source knowledge acquisition and validation workflows for all Agent Factory products (PLC Tutor, RIVET, SCAFFOLD).

## Status
✅ Active - Supports all products

## Core Capabilities

### 1. Web Research
- Perplexity-style multi-source research with citations
- Reddit mining for trending topics and questions
- Stack Overflow scraping for technical Q&A
- Forum monitoring (HVAC-Talk, PLCs.net, etc.)

### 2. PDF Ingestion
- Extract text from vendor manuals (Rockwell, Siemens, Mitsubishi, Omron)
- Preserve structure (sections, tables, diagrams)
- Detect and skip duplicate sources via URL hashing
- Convert to knowledge atoms with citations

### 3. YouTube Transcripts
- Fetch transcripts via YouTube Data API
- Extract educational content from PLC tutorial videos
- Identify high-quality instructors (ControlLogicETC, RealPars)
- Convert transcripts to atoms with video timestamps

### 4. Quality Validation
- 5-dimension scoring: completeness, clarity, accuracy, safety, citations
- Cross-reference against official documentation
- Safety compliance checking (NFPA, OSHA, ANSI)
- Perplexity-style footnote citations

## Architecture

### Research Workflows

#### A. Single-Source Research
```python
from agents.research.research_agent import ResearchAgent

agent = ResearchAgent()

# Scrape single URL
result = agent.scrape_url("https://example.com/manual.pdf")

# Extract YouTube transcript
result = agent.fetch_youtube_transcript("https://youtube.com/watch?v=...")

# Process Reddit thread
result = agent.scrape_reddit_thread("https://reddit.com/r/PLC/comments/...")
```

#### B. Multi-Source Research
```python
from agent_factory.workflows.ingestion_chain import IngestionPipeline

pipeline = IngestionPipeline()

# 7-stage pipeline: Acquisition → Extraction → Chunking → Generation → Validation → Embedding → Storage
result = pipeline.ingest_source(
    url="https://example.com/manual.pdf",
    source_type="pdf"
)

# Performance: 600 atoms/hour (parallel), $0.18/1000 sources
```

### Citation Format (Perplexity-Style)

All atoms use standardized inline citations with footer references:

```markdown
The ControlLogix scan cycle consists of three phases[^1]:
1. Input scan - read all input modules
2. Program scan - execute ladder logic
3. Output scan - write to output modules

The typical scan time is 10-50ms depending on program complexity[^2].

[^1]: Allen-Bradley ControlLogix Programming Manual, Chapter 2, pp. 15-18
[^2]: Rockwell Automation Technical Note 12345, "Optimizing Scan Time"
```

**Citation Rules**:
- Inline: Use `[^1][^2]` for multiple sources on same claim
- Footer: Full source details with URL (if available)
- Timestamp: Include for YouTube/video sources (`[^3]: Video at 4:23`)
- Page numbers: Include for PDF sources (`pp. 15-18`)

## Ingestion Pipeline (7 Stages)

### Implementation
**Location**: `agent_factory/workflows/ingestion_chain.py`
**Framework**: LangGraph StateGraph
**Performance**: 600 atoms/hour (parallel), 60 atoms/hour (sequential)

### Stage 1: Source Acquisition
- Download PDFs to `data/sources/pdfs/`
- Fetch YouTube transcripts via API
- Scrape web pages (BeautifulSoup)
- Deduplication: Hash URL → skip if already processed

### Stage 2: Content Extraction
- Parse text from PDFs (PyPDF2, pdfplumber)
- Extract HTML content (BeautifulSoup, Readability)
- Preserve structure (headings, lists, tables)
- Identify content types (procedure, concept, troubleshooting)

### Stage 3: Semantic Chunking
- Split into 200-400 word coherent chunks
- Use RecursiveCharacterTextSplitter (LangChain)
- Preserve context (include section headings)
- Overlap 50 words between chunks

### Stage 4: Atom Generation
- LLM extraction (GPT-4 or DeepSeek via LLMRouter)
- Convert chunks → structured Pydantic models (PLCAtom, RIVETAtom)
- Extract metadata (vendor, platform, difficulty)
- Generate citations from source metadata

### Stage 5: Quality Validation
- 5-dimension scoring (0.0-1.0 each):
  - **Completeness**: All required fields present?
  - **Clarity**: Understandable to target audience?
  - **Accuracy**: Cross-check with known facts?
  - **Safety**: Proper LOTO/PPE warnings?
  - **Citations**: Valid, traceable sources?
- Threshold: Total score ≥4.0 to pass

### Stage 6: Embedding Generation
- OpenAI `text-embedding-3-small` (1536 dimensions)
- Cost: $0.02 per 1M tokens
- Batch processing: 100 atoms at a time
- Store embeddings for semantic search

### Stage 7: Storage & Indexing
- Save to Supabase `knowledge_atoms` table
- Deduplication: Hash content → skip if exists
- Update `source_fingerprints` table
- Create pgvector index for semantic search

## Agents

### ResearchAgent
**Location**: `agents/research/research_agent.py`

**Responsibilities**:
- Web scraping (BeautifulSoup, Selenium)
- YouTube transcript extraction (YouTube Data API)
- PDF text extraction (PyPDF2, pdfplumber)
- Reddit/forum monitoring (PRAW, requests)

**Schedule**: On-demand (triggered by orchestrator)

**Output**: Raw research data in Supabase `research_sources` table

### AtomBuilderAgent
**Location**: `agents/research/atom_builder_agent.py`

**Responsibilities**:
- Convert raw data → structured Pydantic models
- Extract metadata (vendor, platform, difficulty)
- Generate citations from source metadata
- Validate schema compliance

**Schedule**: After ResearchAgent completes

**Output**: Structured atoms in Supabase `knowledge_atoms` table

### QualityCheckerAgent
**Location**: `agents/knowledge/quality_checker_agent.py`

**Responsibilities**:
- 5-dimension scoring (completeness, clarity, accuracy, safety, citations)
- Safety compliance validation (NFPA, OSHA, ANSI)
- Citation verification (check URLs, page numbers)
- Flag low-quality atoms for human review

**Schedule**: After AtomBuilderAgent completes

**Output**: Quality scores in Supabase, flagged atoms in `review_queue`

### CitationValidatorAgent
**Location**: `agents/knowledge/citation_validator_agent.py`

**Responsibilities**:
- Validate citation URLs (HTTP status check)
- Check citation format (Perplexity-style)
- Cross-reference claims against sources
- Detect hallucinated citations

**Schedule**: After QualityCheckerAgent completes

**Output**: Citation validation results in Supabase

## Commands

### Skill Loading
```bash
Skill("RESEARCH")  # Load this skill context
```

### Research Commands
```bash
# Single-source research
research-url "https://example.com/manual.pdf"

# Multi-source research (topic query)
research-topic "PLC motor control patterns"

# Reddit mining
research-reddit "r/PLC" --days 7

# YouTube transcript extraction
research-youtube "https://youtube.com/watch?v=..."

# Validate atom citations
validate-citations atom-123
```

### Pipeline Commands
```bash
# Run full ingestion pipeline
poetry run python agent_factory/workflows/ingestion_chain.py \
  --url "https://example.com/manual.pdf" \
  --source-type pdf

# Batch ingestion (multiple URLs)
poetry run python scripts/knowledge/batch_ingest.py \
  --urls-file data/seed_urls.txt

# Generate embeddings for existing atoms
poetry run python scripts/knowledge/generate_embeddings.py

# Upload embeddings to Supabase
poetry run python scripts/knowledge/upload_embeddings.py
```

### Validation Commands
```bash
# Test ResearchAgent
poetry run python -c "from agents.research.research_agent import ResearchAgent; print('OK')"

# Test ingestion pipeline
poetry run python agent_factory/workflows/ingestion_chain.py --test

# Validate atom schema
poetry run python -c "from core.models import PLCAtom; print('Schema OK')"
```

## Data Models

### LearningObject (Base Schema)
```python
from core.models import LearningObject

obj = LearningObject(
    atom_id="base:example:atom-001",
    type="concept",
    title="Example Concept",
    summary="Brief description...",
    content="Full content...",
    difficulty="beginner",
    educational_level=EducationalLevel.INTERMEDIATE,
    prereqs=["base:example:prereq-001"],
    source="Example Manual, Chapter 1",
    citations=[
        "[^1]: Example Manual, pp. 10-15",
        "[^2]: https://example.com/doc"
    ],
    last_reviewed_at="2025-12-22",
    safety_level="info",
    status=Status.PUBLISHED
)
```

### PLCAtom (PLC Tutor)
```python
from core.models import PLCAtom

atom = PLCAtom(
    atom_id="plc:ab:motor-start",
    type="pattern",
    vendor="allen_bradley",
    platform="control_logix",
    title="Basic Motor Start Circuit",
    # ... (see PLC_TUTOR skill for full example)
)
```

### RIVETAtom (RIVET Industrial)
```python
from core.models import RIVETAtom

atom = RIVETAtom(
    atom_id="rivet:hvac:compressor-noise",
    type="troubleshooting",
    equipment_class="HVAC",
    symptom="Loud rattling noise...",
    # ... (see RIVET_INDUSTRIAL skill for full example)
)
```

## Integration Points

### With PLC_TUTOR
- ResearchAgent scrapes PLC manuals and YouTube tutorials
- AtomBuilderAgent creates PLCAtoms
- QualityCheckerAgent validates safety compliance
- ScriptwriterAgent uses atoms to generate video scripts

### With RIVET_INDUSTRIAL
- ResearchAgent monitors Reddit/Stack Overflow for questions
- AtomBuilderAgent creates RIVETAtoms from solved problems
- QualityCheckerAgent validates NFPA/OSHA compliance
- KnowledgeAnswerer queries atoms to generate answers

### With SCAFFOLD
- ResearchAgent scrapes documentation for code generation
- AtomBuilderAgent creates code pattern atoms
- QualityCheckerAgent validates code quality
- PRCreator uses atoms to generate implementation plans

## Key Files & Directories

```
agents/research/
├── research_agent.py           # Web/PDF/YouTube scraping
├── atom_builder_agent.py       # Raw data → Pydantic models
└── atom_librarian_agent.py     # Organize atoms, build prereq chains

agents/knowledge/
├── quality_checker_agent.py    # 5-dimension validation
└── citation_validator_agent.py # Citation verification

agent_factory/workflows/
└── ingestion_chain.py          # 7-stage LangGraph pipeline

scripts/knowledge/
├── batch_ingest.py             # Batch URL ingestion
├── generate_embeddings.py      # OpenAI embeddings
├── upload_embeddings.py        # Supabase ingestion
└── validate_atoms.py           # Schema validation

core/
└── models.py                   # LearningObject, PLCAtom, RIVETAtom

docs/architecture/
└── ATOM_SPEC_UNIVERSAL.md      # IEEE LOM-based schema
```

## Quality Metrics

### Ingestion Performance
- **Sequential**: 60 atoms/hour
- **Parallel (10 workers)**: 600 atoms/hour
- **Cost**: $0.18 per 1,000 sources processed

### Validation Metrics
- **Pass Rate**: >90% (after pipeline tuning)
- **False Positive**: <5% (atoms flagged but actually good)
- **False Negative**: <2% (bad atoms passing validation)

### Citation Quality
- **Valid URLs**: >95% (HTTP 200 status)
- **Format Compliance**: >98% (Perplexity-style)
- **Source Traceability**: 100% (every atom has ≥1 citation)

## References

- **Ingestion Pipeline**: `agent_factory/workflows/ingestion_chain.py`
- **Atom Schema**: `docs/architecture/ATOM_SPEC_UNIVERSAL.md`
- **Agent Specs**: `docs/architecture/AGENT_ORGANIZATION.md`
- **Batch Scripts**: `scripts/knowledge/`

---

**Note**: RESEARCH skill is active and supports all products (PLC Tutor, RIVET, SCAFFOLD).
