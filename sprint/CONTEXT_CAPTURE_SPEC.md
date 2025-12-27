# INTELLIGENT CONTEXT CAPTURE & MANUAL RETRIEVAL

## Feature Overview

**Problem:** Technicians describe issues, but we only capture surface-level info. We're missing opportunities to proactively provide relevant documentation.

**Solution:** On every Telegram message, extract rich context about:
- Specific component (e.g., "VFD on Panel 3")
- Component family (e.g., "Variable Frequency Drives")
- Manufacturer/brand (e.g., "Allen-Bradley", "Siemens")
- Equipment category (e.g., "Motor Controls", "PLCs", "Sensors")
- Symptom/fault type (e.g., "fault code", "won't start", "overheating")
- Work context (e.g., "troubleshooting", "installation", "maintenance")

Then **automatically search** the knowledge base for relevant:
- User manuals
- Troubleshooting guides
- Fault code references
- Wiring diagrams
- Parts lists

---

## User Experience (Before vs After)

### BEFORE (Current)
```
Tech: "The PowerFlex 525 is showing fault F004"

Bot: "I understand you're having an issue with a VFD fault code. 
     What would you like to do?
     1. Create a work order
     2. Get troubleshooting help"
```

### AFTER (With This Feature)
```
Tech: "The PowerFlex 525 is showing fault F004"

Bot: "🔧 PowerFlex 525 - Fault F004 (Undervoltage)

     📖 From Allen-Bradley PowerFlex 520 Series Manual:
     
     **F004 - DC Bus Undervoltage**
     • Check incoming power voltage
     • Verify DC bus capacitor health
     • Check for loose connections on input terminals
     
     📄 Related docs I found:
     • PowerFlex 520 Troubleshooting Guide (p.47)
     • PowerFlex Fault Codes Quick Reference
     
     ⚠️ SAFETY: De-energize before inspecting terminals
     
     Want me to create a work order for this?"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TELEGRAM MESSAGE INTAKE                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTEXT EXTRACTOR (Claude)                     │
│                                                                  │
│  Input: "The PowerFlex 525 is showing fault F004"               │
│                                                                  │
│  Extracts:                                                       │
│  {                                                               │
│    "component": "PowerFlex 525",                                │
│    "component_family": "Variable Frequency Drive",              │
│    "manufacturer": "Allen-Bradley",                             │
│    "category": "Motor Controls",                                │
│    "issue_type": "fault_code",                                  │
│    "fault_code": "F004",                                        │
│    "symptoms": ["undervoltage"],                                │
│    "work_context": "troubleshooting",                           │
│    "urgency": "medium"                                          │
│  }                                                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE BASE SEARCH                         │
│                                                                  │
│  Search queries generated:                                       │
│  1. "PowerFlex 525 fault F004"                                  │
│  2. "Allen-Bradley VFD undervoltage"                            │
│  3. "PowerFlex 520 series troubleshooting"                      │
│  4. "VFD fault codes"                                           │
│                                                                  │
│  Sources searched:                                               │
│  • Uploaded prints (ChromaDB)                                   │
│  • PDF manual library (if exists)                               │
│  • Knowledge atoms (existing KB)                                │
│  • OEM documentation index                                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESPONSE SYNTHESIZER                          │
│                                                                  │
│  Combines:                                                       │
│  • Direct answer (from manuals)                                 │
│  • Troubleshooting steps                                        │
│  • Related document links                                       │
│  • Safety warnings                                              │
│  • Work order prompt                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Taxonomy

### Equipment Categories
```yaml
Motor Controls:
  - Variable Frequency Drives (VFD)
  - Soft Starters
  - Motor Contactors
  - Overload Relays
  
PLCs & Controllers:
  - Programmable Logic Controllers
  - PACs (Programmable Automation Controllers)
  - HMIs (Human Machine Interfaces)
  - I/O Modules
  
Sensors & Instrumentation:
  - Proximity Sensors
  - Photoelectric Sensors
  - Pressure Transmitters
  - Temperature Sensors
  - Level Sensors
  - Flow Meters
  
Power Distribution:
  - Circuit Breakers
  - Disconnects
  - Transformers
  - Power Supplies
  - UPS Systems
  
Pneumatics:
  - Solenoid Valves
  - Air Cylinders
  - FRLs (Filter/Regulator/Lubricator)
  - Pressure Regulators
  
Hydraulics:
  - Hydraulic Pumps
  - Directional Valves
  - Pressure Relief Valves
  - Hydraulic Cylinders
  
Safety:
  - E-Stops
  - Light Curtains
  - Safety Relays
  - Interlock Switches
```

### Major Manufacturers
```yaml
Allen-Bradley/Rockwell:
  - PowerFlex (VFDs)
  - CompactLogix/ControlLogix (PLCs)
  - PanelView (HMIs)
  
Siemens:
  - SINAMICS (VFDs)
  - S7-1200/1500 (PLCs)
  - SIMATIC HMI
  
ABB:
  - ACS (VFDs)
  - AC500 (PLCs)
  
Schneider Electric:
  - Altivar (VFDs)
  - Modicon (PLCs)
  - Magelis (HMIs)
  
Mitsubishi:
  - FR-E/FR-A (VFDs)
  - MELSEC (PLCs)
  
Yaskawa:
  - V1000/A1000 (VFDs)
  
Omron:
  - MX2/RX (VFDs)
  - CJ/NJ (PLCs)
  
Festo:
  - Pneumatic components
  
SMC:
  - Pneumatic components
  
Banner Engineering:
  - Sensors
  
Keyence:
  - Sensors, Vision
  
IFM:
  - Sensors
```

---

## Data Models

### EquipmentContext
```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class IssueType(Enum):
    FAULT_CODE = "fault_code"
    WONT_START = "wont_start"
    INTERMITTENT = "intermittent"
    NOISE_VIBRATION = "noise_vibration"
    OVERHEATING = "overheating"
    COMMUNICATION = "communication"
    CALIBRATION = "calibration"
    PHYSICAL_DAMAGE = "physical_damage"
    UNKNOWN = "unknown"

class WorkContext(Enum):
    TROUBLESHOOTING = "troubleshooting"
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    REPLACEMENT = "replacement"
    PROGRAMMING = "programming"
    COMMISSIONING = "commissioning"
    INSPECTION = "inspection"

@dataclass
class EquipmentContext:
    """Rich context extracted from user message."""
    
    # Component identification
    component_name: str                    # "PowerFlex 525"
    component_family: str                  # "Variable Frequency Drive"
    manufacturer: Optional[str]            # "Allen-Bradley"
    model_number: Optional[str]            # "25B-D030N114"
    category: str                          # "Motor Controls"
    
    # Issue details
    issue_type: IssueType
    fault_code: Optional[str]              # "F004"
    symptoms: List[str]                    # ["undervoltage", "trips randomly"]
    
    # Work context
    work_context: WorkContext
    location: Optional[str]                # "Panel 3", "Line 2"
    urgency: str                           # "low", "medium", "high", "critical"
    
    # Search hints
    search_keywords: List[str]             # Generated keywords for KB search
    manual_search_queries: List[str]       # Specific queries for manual lookup
    
    # Confidence
    confidence: float                      # 0.0 - 1.0
    needs_clarification: bool
    clarification_prompt: Optional[str]
```

### ManualReference
```python
@dataclass
class ManualReference:
    """Reference to a found manual/document."""
    
    title: str                             # "PowerFlex 520 User Manual"
    manufacturer: str
    document_type: str                     # "user_manual", "quick_start", "troubleshooting"
    relevant_section: Optional[str]        # "Chapter 7: Fault Codes"
    page_numbers: Optional[str]            # "47-52"
    relevance_score: float
    snippet: str                           # Relevant excerpt
    source_url: Optional[str]              # Link to PDF or online doc
    local_path: Optional[str]              # Path in our storage
```

---

## Implementation Plan

### Phase 1: Context Extractor (Day 1-2)

**Task 1.1: Equipment Taxonomy Database**
Create `agent_factory/knowledge/equipment_taxonomy.py`:
- Component families
- Manufacturer patterns
- Model number regex patterns
- Keyword mappings

**Task 1.2: Context Extraction Prompt**
Create Claude prompt that extracts structured context:
```python
CONTEXT_EXTRACTION_PROMPT = """
Analyze this maintenance technician's message and extract equipment context.

Message: "{message}"

Extract:
1. Component name (specific model if mentioned)
2. Component family (VFD, PLC, sensor, etc.)
3. Manufacturer (if identifiable)
4. Category (Motor Controls, PLCs, Sensors, etc.)
5. Issue type (fault_code, wont_start, etc.)
6. Fault code (if mentioned)
7. Symptoms described
8. Work context (troubleshooting, maintenance, etc.)
9. Location (if mentioned)
10. Urgency level

Return JSON format:
{json_schema}
"""
```

**Task 1.3: Context Extractor Class**
Create `agent_factory/intake/context_extractor.py`:
```python
class ContextExtractor:
    async def extract(self, message: str, user_history: List = None) -> EquipmentContext
    def _enhance_with_taxonomy(self, context: EquipmentContext) -> EquipmentContext
    def _generate_search_queries(self, context: EquipmentContext) -> List[str]
```

### Phase 2: Manual Library (Day 2-3)

**Task 2.1: PDF Manual Storage Schema**
```sql
CREATE TABLE equipment_manuals (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    manufacturer VARCHAR(255),
    component_family VARCHAR(255),
    model_patterns TEXT[],           -- Regex patterns for matching
    document_type VARCHAR(100),
    file_path VARCHAR(512),
    file_url VARCHAR(512),
    page_count INTEGER,
    indexed BOOLEAN DEFAULT FALSE,
    index_collection VARCHAR(255),   -- ChromaDB collection name
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE manual_sections (
    id UUID PRIMARY KEY,
    manual_id UUID REFERENCES equipment_manuals(id),
    section_title VARCHAR(500),
    page_start INTEGER,
    page_end INTEGER,
    section_type VARCHAR(100),       -- 'fault_codes', 'wiring', 'specs', etc.
    keywords TEXT[]
);
```

**Task 2.2: Manual Indexer**
Create `agent_factory/knowledge/manual_indexer.py`:
- Ingest PDF manuals
- Chunk by section (TOC-aware)
- Extract fault code tables
- Vectorize and store

**Task 2.3: Manual Search**
Create `agent_factory/knowledge/manual_search.py`:
```python
class ManualSearch:
    async def search(self, context: EquipmentContext) -> List[ManualReference]
    async def search_fault_code(self, manufacturer: str, model: str, fault_code: str) -> ManualReference
    async def search_by_symptom(self, component_family: str, symptoms: List[str]) -> List[ManualReference]
```

### Phase 3: Intelligent Response (Day 3-4)

**Task 3.1: Response Synthesizer**
Create `agent_factory/intake/response_synthesizer.py`:
```python
class ResponseSynthesizer:
    async def synthesize(
        self,
        context: EquipmentContext,
        manual_results: List[ManualReference],
        kb_results: List[dict]
    ) -> str
```

**Task 3.2: Telegram Integration**
Update intake handler to:
1. Extract context on every message
2. Search knowledge bases
3. Synthesize proactive response
4. Include document references

### Phase 4: Continuous Learning (Day 4-5)

**Task 4.1: Context Logging**
Log every extracted context for:
- Improving extraction accuracy
- Identifying common issues
- Finding KB gaps

**Task 4.2: Manual Gap Detection**
When context extracted but no manual found:
- Log the gap
- Suggest manual acquisition
- Track frequency

---

## Database Schema Additions

```sql
-- Context extraction log
CREATE TABLE context_extractions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES rivet_users(id),
    message_text TEXT,
    extracted_context JSONB,
    confidence FLOAT,
    manuals_found INTEGER,
    kb_results_found INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Manual gaps (what we need but don't have)
CREATE TABLE manual_gaps (
    id UUID PRIMARY KEY,
    manufacturer VARCHAR(255),
    component_family VARCHAR(255),
    model_pattern VARCHAR(255),
    request_count INTEGER DEFAULT 1,
    first_requested TIMESTAMP DEFAULT NOW(),
    last_requested TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_manual_id UUID REFERENCES equipment_manuals(id)
);

CREATE INDEX idx_manual_gaps_manufacturer ON manual_gaps(manufacturer);
CREATE INDEX idx_manual_gaps_family ON manual_gaps(component_family);
```

---

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/upload_manual` | Upload a PDF manual to the library |
| `/find_manual <query>` | Search for a manual |
| `/manual_gaps` | Show what manuals are most requested but missing |
| `/my_equipment` | Show equipment you've asked about |

---

## Integration Points

### With Existing Orchestrator
```python
# In orchestrator.py, before routing:
context = await context_extractor.extract(message)

# Enrich the intent with equipment context
intent.equipment_context = context

# Search for relevant docs
manual_results = await manual_search.search(context)
kb_results = await kb_search.search(context.search_keywords)

# Pass to response synthesizer
response = await synthesizer.synthesize(context, manual_results, kb_results)
```

### With Work Order Creation
```python
# When creating work order, include context:
work_order = {
    "title": f"{context.component_name} - {context.issue_type.value}",
    "description": original_message,
    "equipment_family": context.component_family,
    "manufacturer": context.manufacturer,
    "fault_code": context.fault_code,
    "related_manuals": [m.title for m in manual_results]
}
```

### With Print System (from electrical-prints-spec)
```python
# If user has uploaded prints for this equipment:
user_prints = await db.get_prints_by_component_family(
    user_id, 
    context.component_family
)

# Include in search
if user_prints:
    print_results = await retriever.retrieve(
        user_id, 
        machine_id,
        " ".join(context.search_keywords)
    )
```

---

## Sample Prompts for Context Extraction

### Basic Extraction
```
User: "PowerFlex is faulting"

Extracted:
{
    "component_name": "PowerFlex",
    "component_family": "Variable Frequency Drive",
    "manufacturer": "Allen-Bradley",
    "category": "Motor Controls",
    "issue_type": "fault_code",
    "confidence": 0.7,
    "needs_clarification": true,
    "clarification_prompt": "What fault code is displaying? (e.g., F001, F004)"
}
```

### Rich Extraction
```
User: "The Siemens S7-1500 on line 3 is showing SF light and won't communicate with the HMI"

Extracted:
{
    "component_name": "S7-1500",
    "component_family": "Programmable Logic Controller",
    "manufacturer": "Siemens",
    "model_number": null,
    "category": "PLCs & Controllers",
    "issue_type": "communication",
    "fault_code": null,
    "symptoms": ["SF light on", "no HMI communication"],
    "work_context": "troubleshooting",
    "location": "Line 3",
    "urgency": "high",
    "search_keywords": ["S7-1500", "SF fault", "HMI communication", "Siemens PLC"],
    "confidence": 0.95,
    "needs_clarification": false
}
```

---

## File Structure

```
agent_factory/
├── intake/
│   ├── __init__.py
│   ├── context_extractor.py      # Main extraction logic
│   ├── response_synthesizer.py   # Combine results into response
│   └── models.py                 # EquipmentContext, ManualReference
├── knowledge/
│   ├── __init__.py
│   ├── equipment_taxonomy.py     # Categories, manufacturers, patterns
│   ├── manual_indexer.py         # PDF ingestion for manuals
│   ├── manual_search.py          # Search indexed manuals
│   └── gap_tracker.py            # Track missing manuals
└── integrations/telegram/
    └── intake_handler.py         # Updated message handler
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Context extraction accuracy | >85% |
| Manual hit rate (when relevant manual exists) | >90% |
| Response includes relevant doc | >70% of queries |
| User clicks provided doc link | >40% |
| Time to first relevant info | <3 seconds |

---

## Sprint Timeline

| Day | Focus |
|-----|-------|
| 1 | Equipment taxonomy + Context extractor |
| 2 | Manual storage schema + PDF indexer |
| 3 | Manual search + Response synthesizer |
| 4 | Telegram integration + Testing |
| 5 | Gap tracking + Polish |

---

## Dependencies

```bash
pip install pdfplumber sentence-transformers chromadb
```

Uses existing:
- Claude API (extraction + synthesis)
- ChromaDB (vector storage)
- Neon PostgreSQL (metadata)
- Telegram bot framework
