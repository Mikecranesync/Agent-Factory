# Agent Tracing Integration Pattern

## Overview

This document shows how to integrate `SyncAgentTracer` into existing knowledge agents for full traceability.

## Pattern: Wrap Main Entry Point

For each agent, wrap the main entry point method with `SyncAgentTracer`:

### Before:
```python
class QualityCheckerAgent:
    def validate_atom(self, atom_id: str) -> ValidationResult:
        # Fetch atom
        atom = self.db.execute_query(...)

        # Run 6-stage validation
        completeness_pass, missing = self.check_completeness(atom)
        # ... more checks ...

        return ValidationResult(...)
```

### After:
```python
from agent_factory.observability.agent_tracer import SyncAgentTracer

class QualityCheckerAgent:
    def __init__(self, db):
        self.db = db
        self.session_id = None  # Set by pipeline

    def validate_atom(self, atom_id: str) -> ValidationResult:
        # If session_id not set, skip tracing (backward compatible)
        if not self.session_id:
            return self._validate_atom_impl(atom_id)

        # Trace execution
        with SyncAgentTracer(self.session_id, "QualityChecker", self.db) as tracer:
            result = self._validate_atom_impl(atom_id)

            # Record metrics
            tracer.metadata["atoms_validated"] = 1
            tracer.metadata["quality_score"] = result.overall_score

            return result

    def _validate_atom_impl(self, atom_id: str) -> ValidationResult:
        """Original implementation (unchanged)."""
        atom = self.db.execute_query(...)
        completeness_pass, missing = self.check_completeness(atom)
        # ... validation logic ...
        return ValidationResult(...)
```

## Integration Points for Each Agent

### 1. AtomBuilder (`agents/knowledge/atom_builder_from_pdf.py`)

**Main method:** `process_pdf_extraction(json_path, output_dir)`

**Integration:**
```python
def process_pdf_extraction(self, json_path: Path, output_dir: Optional[Path] = None) -> List[KnowledgeAtom]:
    if not self.session_id:
        return self._process_pdf_extraction_impl(json_path, output_dir)

    with SyncAgentTracer(self.session_id, "AtomBuilder", self.db) as tracer:
        atoms = self._process_pdf_extraction_impl(json_path, output_dir)

        # Record metrics
        tracer.metadata["atoms_created"] = len(atoms)
        tracer.metadata["source_file"] = str(json_path)

        return atoms
```

**Metrics to capture:**
- `atoms_created`: Number of atoms generated
- `source_file`: PDF filename
- `avg_content_length`: Average atom content length

---

### 2. CitationValidator (`agents/knowledge/citation_validator_agent.py`)

**Main method:** `validate_citations(atom_id)`

**Integration:**
```python
def validate_citations(self, atom_id: str) -> CitationValidationResult:
    if not self.session_id:
        return self._validate_citations_impl(atom_id)

    with SyncAgentTracer(self.session_id, "CitationValidator", self.db) as tracer:
        result = self._validate_citations_impl(atom_id)

        # Record metrics
        tracer.metadata["citations_checked"] = result.total_citations
        tracer.metadata["citations_valid"] = result.valid_citations
        tracer.metadata["url_health_checks"] = result.urls_checked

        return result
```

**Metrics to capture:**
- `citations_checked`: Total citations validated
- `citations_valid`: Number of valid citations
- `url_health_checks`: URLs checked for availability
- `broken_links`: Number of 404s found

---

### 3. QualityChecker (`agents/knowledge/quality_checker_agent.py`)

**Main method:** `validate_atom(atom_id)`

**Integration:**
```python
def validate_atom(self, atom_id: str) -> ValidationResult:
    if not self.session_id:
        return self._validate_atom_impl(atom_id)

    with SyncAgentTracer(self.session_id, "QualityChecker", self.db) as tracer:
        result = self._validate_atom_impl(atom_id)

        # Record metrics
        tracer.metadata["quality_score"] = result.overall_score
        tracer.metadata["stage_1_completeness"] = result.completeness_pass
        tracer.metadata["stage_2_accuracy"] = result.accuracy_pass
        tracer.metadata["stage_3_clarity"] = result.clarity_pass
        tracer.metadata["stage_4_safety"] = result.safety_pass
        tracer.metadata["stage_5_citations"] = result.citation_pass
        tracer.metadata["stage_6_examples"] = result.examples_pass

        return result
```

**Metrics to capture:**
- `quality_score`: Overall score (0.0-1.0)
- `stage_X_pass`: Boolean for each of 6 stages
- `issues_found`: Total issues detected
- `flagged_for_review`: Boolean if human review needed

---

### 4. GeminiJudge (`agent_factory/judges/gemini_judge.py`)

**Main method:** `evaluate_atom(atom)` or `judge_quality(atom)`

**Integration:**
```python
def evaluate_atom(self, atom: Dict[str, Any]) -> JudgeResult:
    if not self.session_id:
        return self._evaluate_atom_impl(atom)

    with SyncAgentTracer(self.session_id, "GeminiJudge", self.db) as tracer:
        result = self._evaluate_atom_impl(atom)

        # Record LLM call metrics
        tracer.record_llm_call(
            tokens_used=result.tokens_used,
            cost_usd=result.cost_usd
        )

        # Record quality metrics
        tracer.metadata["quality_score"] = result.quality_score
        tracer.metadata["product_angle"] = result.product_angle
        tracer.metadata["confidence"] = result.confidence

        return result
```

**Metrics to capture:**
- `tokens_used`: LLM tokens consumed
- `cost_usd`: API cost
- `quality_score`: Judge's quality rating (1-5)
- `product_angle`: Product discovery signal
- `llm_model`: Model used (e.g., "gemini-1.5-flash")

---

## Pipeline Usage

When the ingestion pipeline calls agents, it sets the session_id first:

```python
class IngestionPipeline:
    async def ingest_source(self, url: str) -> Dict:
        # Create session
        session_id = await self._create_session(url)

        # Stage 4: Atom Generation
        atom_builder = AtomBuilderFromPDF(db)
        atom_builder.session_id = session_id  # Set session for tracing
        atoms = atom_builder.process_pdf_extraction(json_path)

        # Stage 5: Quality Validation
        quality_checker = QualityCheckerAgent(db)
        quality_checker.session_id = session_id  # Set session for tracing
        for atom in atoms:
            result = quality_checker.validate_atom(atom.atom_id)

        # Traces automatically written to agent_traces table
```

## Benefits

1. **Backward Compatible:** If `session_id` not set, tracing is skipped
2. **Zero Boilerplate:** Agent code stays clean, tracing handled in wrapper
3. **Automatic Metrics:** Duration, success, errors captured automatically
4. **Custom Metadata:** Each agent can record domain-specific metrics

## Implementation Checklist

For each agent file:
- [ ] Import `SyncAgentTracer` at top
- [ ] Add `self.session_id = None` to `__init__`
- [ ] Rename main method to `_method_impl` (private)
- [ ] Create new public method with tracing wrapper
- [ ] Add `tracer.metadata["key"] = value` for custom metrics

## Testing

```python
# Test with tracing enabled
db = DatabaseManager()
session_id = "test-session-123"

agent = QualityCheckerAgent(db)
agent.session_id = session_id

result = agent.validate_atom("atom-456")

# Verify trace written
traces = db.execute_query(
    "SELECT * FROM agent_traces WHERE session_id = $1",
    (session_id,)
)
assert len(traces) == 1
assert traces[0]["agent_name"] == "QualityChecker"
```

## Next Steps

1. Apply pattern to all 4 agents (AtomBuilder, Citation, Quality, Judge)
2. Test individually with mock session_id
3. Integrate into IngestionPipeline (Week 1 Day 5)
4. Verify full traceability: atom → session → agents (Week 1 Day 7)
