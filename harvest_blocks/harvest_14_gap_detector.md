# HARVEST BLOCK 14: Knowledge Gap Detector

**Priority**: HIGH
**Size**: 19.2KB (559 lines)
**Source**: `agent_factory/core/gap_detector.py`
**Target**: `rivet/core/gap_detector.py`

---

## Overview

Knowledge gap detection and analysis - identifies equipment, calculates priority, generates search terms, and triggers ingestion pipeline for autonomous KB expansion.

### What This Adds

- **Equipment identifier extraction**: 3 regex patterns (S7-1200, 1756-L83E, F0003)
- **Priority calculation**: Safety keywords → HIGH, fault/error → HIGH, troubleshooting → MEDIUM
- **Search term generation**: 10 queries (equipment + manual, vendor + equipment, fault codes, manufacturer sites)
- **Source prioritization**: 6 sources (manufacturer website first, then manualslib, service bulletins, etc.)
- **ULTRA-AGGRESSIVE MODE**: Logs every interaction for immediate research (fire-and-forget)
- **Ingestion trigger**: Structured JSON for research pipeline
- **Graceful degradation**: Works without ULTRA-AGGRESSIVE dependencies

### Key Features

```python
from rivet.core.gap_detector import GapDetector, GapPriority, IngestionSource
from rivet.routers.kb_evaluator import KBCoverageEvaluator
from rivet.schemas.routing import CoverageLevel

# Initialize detector
kb_evaluator = KBCoverageEvaluator()
detector = GapDetector(kb_evaluator)

# Analyze query and generate ingestion trigger
trigger = detector.analyze_query(
    request=request,
    intent=intent,
    kb_coverage=CoverageLevel.NONE  # or THIN
)

if trigger:
    print(f"Priority: {trigger['priority']}")
    print(f"Equipment: {trigger['equipment_identified']}")
    print(f"Search terms: {trigger['search_terms']}")
    print(f"Sources: {trigger['sources_to_try']}")

# Format for display
display = detector.format_trigger_for_display(trigger)
# Returns: [INGESTION_TRIGGER] ... [/INGESTION_TRIGGER]

# ULTRA-AGGRESSIVE MODE (logs every interaction)
gap_id = await detector.detect_and_log_gap_aggressive(
    request=request,
    intent=intent,
    kb_coverage=kb_coverage,
    atoms_found=atom_count,
    confidence=routing_confidence
)
# Returns: gap_id (int) if logged, None if failed
```

---

## Equipment Identifier Extraction (3 Patterns)

```python
MODEL_NUMBER_PATTERNS = [
    r'\b[A-Z]{1,3}[-\s]?\d{3,6}[A-Z]?\b',  # S7-1200, G120C
    r'\b\d{4}[-/]\d{2,4}\b',                # 1756-L83E
    r'\b[A-Z]\d{2,4}[A-Z]{0,2}\b',         # F0003, E123
]

# Example extractions:
"Siemens S7-1200 CPU fault" → ["S7-1200"]
"Allen Bradley 1756-L83E error" → ["1756-L83E"]
"VFD fault code F0003" → ["F0003"]
```

---

## Priority Calculation

```python
# HIGH: Safety-related keywords
SAFETY_KEYWORDS = [
    'safety', 'lockout', 'tagout', 'loto', 'emergency stop', 'e-stop',
    'fail-safe', 'safety rated', 'sil', 'category'
]

# HIGH: Fault/error keywords
if 'fault' or 'error' or 'alarm' or 'trip' in query:
    priority = GapPriority.HIGH

# MEDIUM: Troubleshooting keywords
if 'troubleshoot' or 'diagnose' or 'fix' or 'repair' in query:
    priority = GapPriority.MEDIUM

# MEDIUM: Specific vendor queries (non-generic)
if intent.vendor != VendorType.GENERIC:
    priority = GapPriority.MEDIUM

# LOW: General questions
else:
    priority = GapPriority.LOW
```

---

## Search Term Generation (10 Queries)

```python
# Equipment ID + manual
f'"{equipment_id}" manual filetype:pdf'
f'"{equipment_id}" troubleshooting guide'

# Vendor + equipment type
f'{vendor_name} {equipment_type} manual filetype:pdf'
f'{vendor_name} {equipment_type} service bulletin'

# Fault code searches
f'{equipment_id} {fault_code} fault code'

# Manufacturer websites (Siemens, Rockwell)
'site:siemens.com technical documentation'
'site:rockwellautomation.com literature library'

# Example output (10 terms):
[
    '"S7-1200" manual filetype:pdf',
    '"S7-1200" troubleshooting guide',
    'siemens plc manual filetype:pdf',
    'siemens plc service bulletin',
    'S7-1200 F0003 fault code',
    'site:siemens.com technical documentation'
]
```

---

## Source Prioritization (6 Sources)

```python
class IngestionSource(str, Enum):
    MANUFACTURER_WEBSITE = "manufacturer_website"    # Always first
    MANUALSLIB = "manualslib"                        # Always second
    SERVICE_BULLETINS = "service_bulletins"          # HIGH priority only
    TECHNICAL_STANDARDS = "technical_standards"       # Safety queries only
    INDUSTRY_FORUMS = "industry_forums"              # MEDIUM/LOW priority
    PARTS_DIAGRAMS = "parts_diagrams"                # (not used in current logic)

# Ordering example (HIGH priority, safety equipment):
[MANUFACTURER_WEBSITE, MANUALSLIB, SERVICE_BULLETINS, TECHNICAL_STANDARDS]
```

---

## ULTRA-AGGRESSIVE MODE

**Fire-and-forget logging on EVERY interaction** (not just NONE/THIN coverage):

```python
# In RivetOrchestrator after routing
asyncio.create_task(
    self.gap_detector.detect_and_log_gap_aggressive(
        request=request,
        intent=intent,
        kb_coverage=kb_coverage,
        atoms_found=len(kb_results),
        confidence=routing_confidence
    )
)
# Non-blocking - runs in background, doesn't slow down response
```

**Weakness Type Mapping**:
- `NO_KNOWLEDGE`: 0 atoms found (CoverageLevel.NONE)
- `INSUFFICIENT_KNOWLEDGE`: <3 atoms found (CoverageLevel.THIN)
- `LOW_QUALITY_RESPONSES`: Low confidence despite atoms
- `EDGE_CASE_SCENARIOS`: Specific equipment/vendor not covered

**Priority Score** (0-100):
- NONE coverage + 0 atoms = 100 (CRITICAL)
- NONE coverage + fault code = 95 (CRITICAL)
- THIN coverage + low confidence = 70-80 (HIGH)
- STRONG coverage + low confidence = 50-60 (MEDIUM)

---

## Dependencies

```bash
# Already installed from previous blocks
# - kb_evaluator (KBCoverageEvaluator)
# - rivet_pro.models (RivetRequest, RivetIntent)
# - schemas.routing (CoverageLevel)

# Optional (for ULTRA-AGGRESSIVE MODE):
# - phoenix_trace_analyzer (WeaknessType, WeaknessSignal)
# - kb_gap_logger (KBGapLogger)
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/core/gap_detector.py rivet/core/gap_detector.py`
2. Dependencies already installed
3. Validate: `python -c "from rivet.core.gap_detector import GapDetector; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.core.gap_detector import GapDetector, GapPriority, IngestionSource; print('OK')"

# Test equipment extraction
python -c "
from rivet.core.gap_detector import GapDetector
from rivet.routers.kb_evaluator import KBCoverageEvaluator

detector = GapDetector(KBCoverageEvaluator())
ids = detector._extract_equipment_identifiers('Siemens S7-1200 fault F0003')
print(f'Equipment IDs: {ids}')
"
```

---

## Integration Notes

**RivetOrchestrator Integration**:
```python
# After KB evaluator determines NONE/THIN coverage
if kb_coverage in [CoverageLevel.NONE, CoverageLevel.THIN]:
    trigger = self.gap_detector.analyze_query(request, intent, kb_coverage)

    if trigger:
        # Log trigger to ingestion queue
        await self._queue_ingestion_trigger(trigger)

        # Display to user (optional)
        response_text += self.gap_detector.format_trigger_for_display(trigger)
```

**ULTRA-AGGRESSIVE MODE** (fire-and-forget):
```python
# After routing decision made
asyncio.create_task(
    self.gap_detector.detect_and_log_gap_aggressive(
        request, intent, kb_coverage, len(kb_results), confidence
    )
)
# Non-blocking - logs in background
```

**Ingestion Trigger Structure**:
```json
{
  "trigger": "knowledge_gap",
  "query_text": "Siemens S7-1200 fault F0003...",
  "equipment_identified": "S7-1200, F0003",
  "vendor": "siemens",
  "equipment_type": "plc",
  "symptom": "fault code displayed",
  "search_terms": [...10 search queries...],
  "priority": "high",
  "sources_to_try": ["manufacturer_website", "manualslib", ...],
  "timestamp": "2025-01-03T12:34:56Z",
  "kb_coverage": "none"
}
```

---

## What This Enables

- ✅ Proactive KB expansion (automatic ingestion triggers)
- ✅ Equipment tracking (model numbers, part numbers extracted)
- ✅ Safety-aware prioritization (HIGH priority for safety keywords)
- ✅ Intelligent search term generation (10 queries per trigger)
- ✅ Source prioritization (manufacturer first, then manualslib)
- ✅ ULTRA-AGGRESSIVE MODE (logs every interaction, triggers research)
- ✅ Fire-and-forget async logging (non-blocking)
- ✅ Graceful degradation (works without optional dependencies)

---

## Next Steps

After implementing HARVEST 14, proceed to **HARVEST 15: RivetOrchestrator (MASTER)** for 4-route query routing orchestration.

SEE FULL SOURCE: `agent_factory/core/gap_detector.py` (559 lines - copy as-is)
