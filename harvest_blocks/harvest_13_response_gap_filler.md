# HARVEST BLOCK 13: Response Gap Filler

**Priority**: HIGH
**Size**: 30.5KB (876 lines)
**Source**: `agent_factory/tools/response_gap_filler.py`
**Target**: `rivet/tools/response_gap_filler.py`

---

## Overview

Autonomous gap detection and KB enrichment - automatically triggers research when knowledge base cannot answer queries, then inserts new atoms to fill gaps.

### What This Adds

- **4-case gap detection logic**: NO_MATCH, UNKNOWN_MANUFACTURER, MISSING_FAULT_CODE, UNKNOWN_MODEL
- **Entity extraction**: Manufacturer (25 known), equipment type (10 types), fault codes (4 patterns), model numbers (2 patterns)
- **Automatic research orchestration**: Builds research task → executes → parses results → inserts atoms
- **Approval workflow**: Optional pending atoms for admin review before insertion
- **Batch atom insertion**: With failure tracking and retry logic
- **OpenAI embeddings**: Async embedding generation for vector search
- **Pydantic models**: KnowledgeGap, FilledGap, AtomCandidate with validation

### Key Features

```python
from rivet.tools.response_gap_filler import KnowledgeGapFiller, ResponseGapDetector
from rivet.core.database_manager import DatabaseManager

# Initialize filler
db = DatabaseManager()
filler = KnowledgeGapFiller(
    kb_client=db.get_client(),
    auto_insert=True,
    require_approval=False  # True = manual approval
)

# Detect and fill gaps (convenience method)
filled = await filler.detect_and_fill(
    query="How to fix Siemens S7-1200 fault code F001?",
    search_results=[],  # Empty = no KB matches
    response_confidence=0.3  # Low confidence
)

# Or detect then fill separately
detector = ResponseGapDetector(confidence_threshold=0.6)
gap = detector.detect(query, search_results, response_confidence)

if gap:
    print(f"Gap detected: {gap.gap_type} - {gap.description}")
    filled = await filler.fill_gap(gap)
    print(f"Created {len(filled.atoms_created)} atoms, confidence={filled.confidence:.0%}")
```

---

## Gap Detection Logic (4 Cases)

```python
# Case 1: NO_MATCH (no results at all)
# → Priority: HIGH
if len(search_results) == 0:
    gap_type = GapType.NO_MATCH

# Case 2: UNKNOWN_MANUFACTURER (low confidence + unknown manufacturer)
# → Priority: HIGH
elif response_confidence < 0.6 and manufacturer not in KNOWN_MANUFACTURERS:
    gap_type = GapType.UNKNOWN_MANUFACTURER

# Case 3: MISSING_FAULT_CODE (fault code query + poor match)
# → Priority: CRITICAL
elif fault_code and best_score < 0.7:
    gap_type = GapType.MISSING_FAULT_CODE

# Case 4: UNKNOWN_MODEL (unknown model + poor match)
# → Priority: MEDIUM
elif model and best_score < 0.6:
    gap_type = GapType.UNKNOWN_MODEL
```

---

## Entity Extraction

**Known Manufacturers** (25):
- Siemens, Allen-Bradley, Rockwell, Schneider, ABB, Mitsubishi
- Omron, Fanuc, Yaskawa, Danfoss, Lenze, SEW, Nord, WEG
- Nidec, Emerson, GE, Honeywell, Phoenix Contact, Wago
- Beckhoff, Keyence, Banner, Sick, IFM, Turck, Balluff

**Equipment Types** (10):
- VFD, PLC, HMI, Motor, Servo, Sensor, Relay, Contactor, Circuit Breaker

**Fault Code Patterns** (4):
```python
r'\b[Ff](?:ault)?[\s\-_]?(\d{1,4})\b'  # F001, Fault 123
r'\b[Ee](?:rror)?[\s\-_]?(\d{1,4})\b'  # E001, Error 123
r'\b[Aa](?:larm)?[\s\-_]?(\d{1,4})\b'  # A001, Alarm 123
r'\b([A-Z]{1,3}\d{3,5})\b'              # ABC123, AB1234
```

**Model Patterns** (2):
```python
r'\b([A-Z]{2,4}[\-\s]?\d{3,5}[A-Z]?)\b'  # S7-1200, AB-1756
r'\b(\d{4}[\-\s]?[A-Z]{1,3})\b'          # 1756-L8
```

---

## Dependencies

```bash
# Install required packages
poetry add langchain-openai

# Already installed from previous blocks
# - research_executor (ResearchExecutorTool)
# - database_manager (DatabaseManager)
```

## Environment Variables

```bash
OPENAI_API_KEY=sk-...  # For embeddings
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/tools/response_gap_filler.py rivet/tools/response_gap_filler.py`
2. Install: `poetry add langchain-openai`
3. Set environment: `export OPENAI_API_KEY=sk-...`
4. Validate: `python -c "from rivet.tools.response_gap_filler import KnowledgeGapFiller; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.tools.response_gap_filler import KnowledgeGapFiller, ResponseGapDetector; print('OK')"

# Test gap detection
python -c "
from rivet.tools.response_gap_filler import ResponseGapDetector

detector = ResponseGapDetector()
gap = detector.detect(
    query='Siemens S7-1200 fault F001',
    search_results=[],
    response_confidence=0.3
)
print(f'Gap: {gap.gap_type if gap else None}')
"
```

---

## Integration Notes

**RivetOrchestrator Integration** (Route B/C):
```python
# In orchestrator after low-confidence response
if response_confidence < 0.6:
    filled = await self.gap_filler.detect_and_fill(
        query=query,
        search_results=kb_results,
        response_confidence=response_confidence
    )

    if filled and filled.fill_successful:
        logger.info(f"Gap filled: {len(filled.atoms_created)} new atoms")
        # Optionally re-query KB with new atoms
```

**Approval Workflow**:
```python
# Initialize with approval required
filler = KnowledgeGapFiller(require_approval=True)

# Research runs, atoms stored in pending
filled = await filler.fill_gap(gap)

# Admin reviews pending atoms
pending = filler._pending_atoms
for atom_id, atom in pending.items():
    print(f"{atom.title}: {atom.confidence_score:.0%}")

# Approve and insert
approved_atoms = [pending["atom1"], pending["atom2"]]
created, updated, failures = await filler._insert_atoms(approved_atoms)
```

**Research Task Building**:
- UNKNOWN_MANUFACTURER → 4 queries (docs, manuals, fault codes, troubleshooting)
- MISSING_FAULT_CODE → 4 queries (meaning, causes, resolution, related codes)
- UNKNOWN_MODEL → 4 queries (specs, manual, fault codes, programming)
- Generic → 3 queries (documentation, procedures, issues)

---

## What This Enables

- ✅ Zero-downtime knowledge expansion (autonomous research)
- ✅ Manufacturer/model/fault code learning (entity extraction)
- ✅ Intelligent gap prioritization (CRITICAL → HIGH → MEDIUM)
- ✅ Approval workflow for quality control (optional)
- ✅ Batch atom insertion with retry logic
- ✅ Vector embeddings for semantic search (OpenAI)
- ✅ Research task customization per gap type
- ✅ Failure tracking and logging (insertion errors)

---

## Next Steps

After implementing HARVEST 13, proceed to **HARVEST 14: Knowledge Gap Detector** for proactive KB expansion and equipment tracking.

SEE FULL SOURCE: `agent_factory/tools/response_gap_filler.py` (876 lines - copy as-is)
