# Claude CLI Prompt: Diagnose and Fix RivetCEO Bot Performance Issues

## Current Situation

The RivetCEO Telegram bot is live but has critical issues. Here's actual production output:

```
TRACE [7577921b]
==============================
ROUTING
  Route: C_research
  Confidence: 54%
  KB Coverage: low
  KB Atoms: 0

TIMING
  routing: 36237ms   ← 36 SECONDS (CRITICAL)
  TOTAL: 37501ms

[INGESTION_TRIGGER]
Equipment: unknown    ← NOT EXTRACTING
Priority: LOW
Search terms: 0       ← NOT GENERATING
Status: Queued for research
```

And with a photo:
```
TRACE [b2ca9561]
==============================
PHOTO OCR
  Manufacturer: Fuji Electric
  Model: FRN004C2S-4U   ← OCR WORKS!
  Fault Code: 

ROUTING
  Route: C_research
  Confidence: 54%
  KB Coverage: low
  KB Atoms: 0           ← BUT KB IS EMPTY

TIMING
  ocr: 6908ms
  routing: 36503ms      ← STILL 36 SECONDS
  TOTAL: 45643ms
```

## Critical Issues to Fix (Priority Order)

### Issue 1: 36-Second Routing Latency (CRITICAL)

**Symptoms:**
- Every query takes 36+ seconds
- `routing: 36237ms` consistently
- Users will abandon the bot

**Likely Causes:**
1. LLM API timeout + retry (Groq has 30s timeout?)
2. Synchronous blocking call that should be async
3. Embedding generation bottleneck
4. Database query without index
5. Waiting for multiple sequential API calls that should be parallel

**Diagnostic Task:**
Add granular timing around each step in the routing pipeline:

```python
# Add timing instrumentation like this:
import time

async def route_query(self, query, user_id):
    timings = {}
    
    # Step 1: Intent extraction
    t0 = time.time()
    intent = await self.extract_intent(query)
    timings["intent_extraction"] = (time.time() - t0) * 1000
    
    # Step 2: KB search
    t0 = time.time()
    kb_results = await self.search_kb(query)
    timings["kb_search"] = (time.time() - t0) * 1000
    
    # Step 3: Coverage evaluation
    t0 = time.time()
    coverage = await self.evaluate_coverage(kb_results)
    timings["coverage_eval"] = (time.time() - t0) * 1000
    
    # Step 4: LLM call
    t0 = time.time()
    response = await self.generate_response(query, kb_results)
    timings["llm_call"] = (time.time() - t0) * 1000
    
    # Step 5: Gap detection
    t0 = time.time()
    gap = self.detect_gap(query, intent)
    timings["gap_detection"] = (time.time() - t0) * 1000
    
    print(f"TIMING BREAKDOWN: {timings}")
    # Find which step is taking 30+ seconds
```

**Fix Approaches:**

If LLM is slow:
```python
# Check Groq timeout settings
# Default might be too high, causing retries

# Option A: Reduce timeout and fail fast
client = Groq(timeout=10.0)  # 10 second timeout

# Option B: Use async properly
response = await asyncio.wait_for(
    self.llm.acomplete(prompt),
    timeout=15.0
)

# Option C: Check if you're accidentally using sync client
# BAD: response = client.chat.completions.create(...)  # BLOCKS
# GOOD: response = await client.chat.completions.acreate(...)
```

If DB is slow:
```python
# Add these indexes if missing
# CREATE INDEX idx_atoms_embedding ON knowledge_atoms USING ivfflat (embedding vector_cosine_ops);
# CREATE INDEX idx_atoms_manufacturer ON knowledge_atoms(manufacturer);
# CREATE INDEX idx_atoms_equipment ON knowledge_atoms(equipment_type);

# Check if you're doing N+1 queries
# BAD: for atom in atoms: await db.fetch_related(atom)
# GOOD: await db.fetch_all_with_related(atom_ids)
```

If sequential calls should be parallel:
```python
# BAD (sequential - adds up)
intent = await extract_intent(query)
kb_results = await search_kb(query)
coverage = await evaluate_coverage(query)

# GOOD (parallel where possible)
intent_task = asyncio.create_task(extract_intent(query))
kb_task = asyncio.create_task(search_kb(query))

intent, kb_results = await asyncio.gather(intent_task, kb_task)
coverage = await evaluate_coverage(kb_results)  # This one needs kb_results
```

---

### Issue 2: KB Has Zero Atoms

**Symptoms:**
- `KB Atoms: 0` on every query
- Every query hits Route C
- Bot is "flying blind" with no knowledge

**Diagnostic Task:**
```python
# Check what's actually in the KB
async def diagnose_kb():
    # Count atoms
    count = await db.fetchval("SELECT COUNT(*) FROM knowledge_atoms")
    print(f"Total atoms: {count}")
    
    # If count > 0, check why search returns nothing
    if count > 0:
        # Test vector search directly
        test_query = "contactor troubleshooting"
        embedding = await generate_embedding(test_query)
        
        results = await db.fetch("""
            SELECT id, title, content, 
                   1 - (embedding <=> $1) as similarity
            FROM knowledge_atoms
            ORDER BY embedding <=> $1
            LIMIT 5
        """, embedding)
        
        print(f"Search results: {results}")
        
        # Check if embeddings exist
        null_embeddings = await db.fetchval(
            "SELECT COUNT(*) FROM knowledge_atoms WHERE embedding IS NULL"
        )
        print(f"Atoms missing embeddings: {null_embeddings}")
```

**Fix - Seed the KB:**

Create a script to ingest foundational content:

```python
# scripts/seed_kb.py
"""Seed KB with foundational industrial maintenance content"""

SEED_CONTENT = [
    {
        "title": "Contactor Basics and Troubleshooting",
        "equipment_type": "contactor",
        "content": """
        A contactor is an electrically controlled switch used for switching power circuits.
        
        Common Issues:
        - Chattering: Check coil voltage, should be within 85-110% of rated voltage
        - Welded contacts: Caused by overcurrent, check load and overload settings
        - No pickup: Check control circuit, coil resistance, mechanical binding
        - Overheating: Check for loose connections, oversized load
        
        Troubleshooting Steps:
        1. Verify control voltage at coil terminals (A1, A2)
        2. Check main contacts for pitting or welding
        3. Measure coil resistance (compare to nameplate)
        4. Inspect auxiliary contacts
        5. Check mechanical operation manually (with power off)
        
        The red component between A1 and A2 is typically a surge suppressor 
        or RC snubber circuit that protects the coil from voltage spikes.
        """,
        "manufacturer": "generic",
        "tags": ["contactor", "troubleshooting", "basics"]
    },
    {
        "title": "VFD General Troubleshooting Guide",
        "equipment_type": "vfd",
        "content": """
        Variable Frequency Drives (VFDs) control motor speed by varying frequency.
        
        Common Fault Categories:
        - Overcurrent (OC): Check motor, wiring, parameters
        - Overvoltage (OV): Check regen, decel time, braking resistor
        - Undervoltage (UV): Check input power supply
        - Ground fault (GF): Check motor insulation, cable condition
        - Overtemperature (OH): Check ambient temp, fan operation, load
        
        General Troubleshooting:
        1. Record fault code before resetting
        2. Check input voltage (all three phases)
        3. Measure motor insulation (megger test)
        4. Verify parameter settings match motor nameplate
        5. Check for proper ventilation and cooling
        6. Inspect DC bus capacitors for bulging
        """,
        "manufacturer": "generic",
        "tags": ["vfd", "drive", "troubleshooting"]
    },
    {
        "title": "Fuji Electric FRENIC-Mini VFD Series",
        "equipment_type": "vfd",
        "manufacturer": "fuji",
        "content": """
        Fuji FRENIC-Mini (FRN-C2S series) compact VFD troubleshooting.
        
        Model number breakdown: FRN004C2S-4U
        - FRN = Fuji product code
        - 004 = 0.4kW (0.5HP)
        - C2S = FRENIC-Mini series
        - 4 = 400V class
        - U = US market
        
        Common fault codes:
        - Er1: Overcurrent during acceleration
        - Er2: Overcurrent during deceleration  
        - Er3: Overcurrent at constant speed
        - Er4: Overvoltage during acceleration
        - Er5: Overvoltage during deceleration
        - Er7: Overvoltage at constant speed
        - Er8: EEPROM error
        - Er9: Undervoltage
        
        Parameter access: Press FUNC key, use UP/DOWN to navigate
        Factory reset: Set parameter H03 to 1
        """,
        "manufacturer": "fuji",
        "model_pattern": "FRN%C2S%",
        "tags": ["vfd", "fuji", "frenic-mini", "fault-codes"]
    },
    # Add more seed content...
]

async def seed_kb():
    for item in SEED_CONTENT:
        # Generate embedding
        embedding = await generate_embedding(item["content"])
        
        # Insert atom
        await db.execute("""
            INSERT INTO knowledge_atoms 
            (title, content, equipment_type, manufacturer, tags, embedding)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, item["title"], item["content"], item["equipment_type"],
            item.get("manufacturer"), item.get("tags"), embedding)
        
        print(f"Seeded: {item['title']}")
    
    print(f"KB seeded with {len(SEED_CONTENT)} atoms")
```

---

### Issue 3: Gap Detector Not Extracting Equipment/Search Terms

**Symptoms:**
```
Equipment: unknown
Search terms: 0
```

Even when the user asks about "contactor" or OCR detects "Fuji Electric FRN004C2S-4U"

**Diagnostic Task:**
```python
# Test gap detector directly
from agent_factory.core.gap_detector import GapDetector

detector = GapDetector()

test_queries = [
    "What does a contactor do?",
    "How do I reset a Siemens S7-1200?",
    "My Allen-Bradley PowerFlex 525 shows fault code F064",
]

for query in test_queries:
    result = detector.analyze_query(query)
    print(f"Query: {query}")
    print(f"Result: {result}")
    print()
```

**Fix - Improve Gap Detector:**

```python
# agent_factory/core/gap_detector.py
"""
Gap detector that extracts equipment info and generates search terms
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Known equipment patterns
EQUIPMENT_PATTERNS = {
    "vfd": r"\b(vfd|drive|inverter|variable frequency|frn\d+|powerflex|micromaster|g120|fr-[a-z])\b",
    "plc": r"\b(plc|s7-\d+|controllogix|compactlogix|micrologix|fx\d+|q\s?series)\b",
    "contactor": r"\b(contactor|relay|starter|100-c|lc1d|3rt\d+)\b",
    "motor": r"\b(motor|servo|stepper|1la\d+|1le\d+|sgm)\b",
    "hmi": r"\b(hmi|panelview|ktp\d+|got\d+|touch\s?panel)\b",
    "sensor": r"\b(sensor|proximity|photoelectric|e3z|e2e|ultrasonic)\b",
}

# Known manufacturers
MANUFACTURER_PATTERNS = {
    "siemens": r"\b(siemens|simatic|micromaster|g120|s7-|1la|1le|sinumerik)\b",
    "allen-bradley": r"\b(allen.?bradley|rockwell|powerflex|controllogix|compactlogix|panelview|ab\s)\b",
    "mitsubishi": r"\b(mitsubishi|melsec|fx\d+|q\s?series|got|fr-[a-z])\b",
    "fuji": r"\b(fuji|frenic|frn\d+)\b",
    "schneider": r"\b(schneider|telemecanique|altivar|modicon|lc1d)\b",
    "abb": r"\b(abb|acs\d+|ach\d+|3aua)\b",
    "omron": r"\b(omron|sysmac|cp1|cj\d|e3z|e2e)\b",
    "yaskawa": r"\b(yaskawa|varispeed|sgm|sigma)\b",
}

# Model number patterns (generic)
MODEL_PATTERNS = [
    r"\b([A-Z]{2,4}[-]?\d{3,}[A-Z0-9\-]*)\b",  # FRN004C2S-4U, 100-C09D10
    r"\b(\d{4,}[-]?[A-Z]+[-]?\d*)\b",           # 1756-L71, 6ES7-315
    r"\b([A-Z]\d{1,2}[-]?[A-Z]{2,}\d+)\b",      # S7-1200, Q03UDECPU
]


@dataclass
class GapAnalysis:
    gap_detected: bool = False
    equipment_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    search_terms: List[str] = field(default_factory=list)
    priority: str = "LOW"
    should_ingest: bool = False


class GapDetector:
    """Analyzes queries to extract equipment info and generate search terms"""
    
    def analyze_query(
        self, 
        query: str, 
        ocr_context: dict = None
    ) -> GapAnalysis:
        """
        Analyze a query for knowledge gaps and extract equipment info.
        
        Args:
            query: User's query text
            ocr_context: Optional context from OCR (manufacturer, model, etc.)
            
        Returns:
            GapAnalysis with extracted info and search terms
        """
        result = GapAnalysis()
        query_lower = query.lower()
        
        # First, use OCR context if available (most reliable)
        if ocr_context:
            result.manufacturer = ocr_context.get("manufacturer")
            result.model_number = ocr_context.get("model_number")
            result.equipment_type = ocr_context.get("equipment_type")
            result.priority = "HIGH"  # OCR data is high value
        
        # Extract equipment type from query
        if not result.equipment_type:
            for equip_type, pattern in EQUIPMENT_PATTERNS.items():
                if re.search(pattern, query_lower):
                    result.equipment_type = equip_type
                    break
        
        # Extract manufacturer from query
        if not result.manufacturer:
            for manufacturer, pattern in MANUFACTURER_PATTERNS.items():
                if re.search(pattern, query_lower):
                    result.manufacturer = manufacturer
                    break
        
        # Extract model number from query
        if not result.model_number:
            for pattern in MODEL_PATTERNS:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    result.model_number = match.group(1)
                    break
        
        # Generate search terms
        result.search_terms = self._generate_search_terms(result, query)
        
        # Determine if this is a gap worth ingesting
        result.gap_detected = True  # We're in Route C, so there's a gap
        result.should_ingest = len(result.search_terms) > 0
        
        # Set priority based on specificity
        if result.model_number and result.manufacturer:
            result.priority = "HIGH"
        elif result.manufacturer or result.equipment_type:
            result.priority = "MEDIUM"
        else:
            result.priority = "LOW"
        
        return result
    
    def _generate_search_terms(self, analysis: GapAnalysis, query: str) -> List[str]:
        """Generate search terms for ingestion pipeline"""
        terms = []
        
        # Specific model search (highest value)
        if analysis.manufacturer and analysis.model_number:
            terms.append(f"{analysis.manufacturer} {analysis.model_number} manual pdf")
            terms.append(f"{analysis.manufacturer} {analysis.model_number} troubleshooting")
            terms.append(f"{analysis.manufacturer} {analysis.model_number} fault codes")
        
        # Manufacturer + equipment type
        elif analysis.manufacturer and analysis.equipment_type:
            terms.append(f"{analysis.manufacturer} {analysis.equipment_type} troubleshooting guide")
            terms.append(f"{analysis.manufacturer} {analysis.equipment_type} manual")
        
        # Just equipment type
        elif analysis.equipment_type:
            terms.append(f"{analysis.equipment_type} troubleshooting guide")
            terms.append(f"{analysis.equipment_type} basics maintenance")
        
        # Extract key terms from query as fallback
        if not terms:
            # Remove common words and extract meaningful terms
            stopwords = {"what", "how", "does", "do", "is", "the", "a", "an", "to", "this", "that", "it"}
            words = [w for w in query.lower().split() if w not in stopwords and len(w) > 2]
            if words:
                terms.append(" ".join(words[:4]) + " troubleshooting")
        
        return terms[:5]  # Limit to 5 search terms


# Integration with orchestrator
def integrate_gap_detector_with_ocr(query: str, ocr_context: dict = None):
    """
    Called from Route C to analyze gap and trigger ingestion.
    
    This is how OCR data should flow into gap detection:
    """
    detector = GapDetector()
    
    # Pass OCR context to gap detector
    gap_analysis = detector.analyze_query(query, ocr_context=ocr_context)
    
    # Build ingestion trigger
    trigger = {
        "equipment": gap_analysis.equipment_type or "unknown",
        "manufacturer": gap_analysis.manufacturer,
        "model_number": gap_analysis.model_number,
        "priority": gap_analysis.priority,
        "search_terms": gap_analysis.search_terms,
        "should_ingest": gap_analysis.should_ingest,
    }
    
    return trigger
```

---

### Issue 4: OCR Data Not Flowing to Gap Detector

**Symptoms:**
- OCR extracts `Manufacturer: Fuji Electric, Model: FRN004C2S-4U`
- But ingestion trigger shows `Equipment: unknown, Search terms: 0`

**The Problem:**
OCR results aren't being passed to the gap detector.

**Fix - Wire OCR to Gap Detector:**

```python
# In orchestrator.py - Route C handler

async def _route_c_no_coverage(self, request, kb_decision, user_id):
    """
    No coverage route - needs to pass OCR context to gap detector
    """
    
    # Get OCR context if available (from photo analysis)
    ocr_context = request.metadata.get("ocr_context")
    
    # Build OCR dict for gap detector
    ocr_data = None
    if ocr_context:
        ocr_data = {
            "manufacturer": ocr_context.get("manufacturer"),
            "model_number": ocr_context.get("model_number"),
            "equipment_type": ocr_context.get("equipment_type"),
            "serial_number": ocr_context.get("serial_number"),
        }
    
    # LLM fallback response
    llm_response = await self._llm_fallback(request.text, ocr_context)
    
    # Gap detection WITH OCR context
    gap_analysis = self.gap_detector.analyze_query(
        query=request.text,
        ocr_context=ocr_data  # ← THIS WAS MISSING
    )
    
    # Log gap
    gap_id = None
    if gap_analysis.should_ingest:
        gap_id = await self.db.log_gap(
            query=request.text,
            equipment=gap_analysis.equipment_type,
            manufacturer=gap_analysis.manufacturer,
            model_number=gap_analysis.model_number,
            search_terms=gap_analysis.search_terms,
            user_id=user_id
        )
        
        # Queue ingestion job
        await self._queue_ingestion_job({
            "gap_id": gap_id,
            "manufacturer": gap_analysis.manufacturer,
            "model_number": gap_analysis.model_number,
            "search_terms": gap_analysis.search_terms,
            "priority": gap_analysis.priority,
        })
    
    # Build trace output
    trace_data = {
        "equipment": gap_analysis.equipment_type or "unknown",
        "manufacturer": gap_analysis.manufacturer,
        "model_number": gap_analysis.model_number,
        "priority": gap_analysis.priority,
        "search_terms": len(gap_analysis.search_terms),
    }
    
    return {
        "text": llm_response["text"],
        "source": "llm_fallback",
        "gap_analysis": trace_data,
        "gap_id": gap_id,
    }
```

---

## Testing Checklist

After implementing fixes, validate each issue:

### Test 1: Latency
```bash
# Send a query and check timing breakdown
# Target: < 5 seconds total

# Expected output:
TIMING BREAKDOWN:
  intent_extraction: 150ms
  kb_search: 200ms
  coverage_eval: 50ms
  llm_call: 2500ms
  gap_detection: 10ms
  TOTAL: 2910ms
```

### Test 2: KB Search
```bash
# Query something that should be in seeded KB
User: "What does a contactor do?"

# Expected output:
ROUTING
  Route: A or B (NOT C!)
  KB Atoms: 1+
  Confidence: 70%+
```

### Test 3: Gap Detection
```bash
# Query with specific equipment
User: "How do I reset an Allen-Bradley PowerFlex 525?"

# Expected output:
[INGESTION_TRIGGER]
Equipment: vfd
Manufacturer: allen-bradley
Model: PowerFlex 525
Priority: HIGH
Search terms: 3
  - allen-bradley PowerFlex 525 manual pdf
  - allen-bradley PowerFlex 525 troubleshooting
  - allen-bradley PowerFlex 525 fault codes
```

### Test 4: OCR → Gap Flow
```bash
# Send photo of equipment
# Expected output:
PHOTO OCR
  Manufacturer: Fuji Electric
  Model: FRN004C2S-4U

[INGESTION_TRIGGER]
Equipment: vfd
Manufacturer: Fuji Electric  ← Should match OCR
Model: FRN004C2S-4U          ← Should match OCR
Priority: HIGH
Search terms: 3
  - Fuji Electric FRN004C2S-4U manual pdf
  - Fuji Electric FRN004C2S-4U fault codes
  - Fuji FRENIC-Mini troubleshooting
```

---

## Deliverables

1. **Timing instrumentation** in routing pipeline to identify bottleneck
2. **Fix for latency** (async, parallel calls, or timeout adjustment)
3. **KB seeding script** with foundational content
4. **Improved GapDetector** class with regex patterns
5. **Wiring fix** to pass OCR context to gap detector
6. **Test results** showing improvements

## Priority Order

1. 🔴 Fix latency (users are waiting 36+ seconds)
2. 🔴 Seed KB (bot has zero knowledge)
3. 🟠 Fix gap detector extraction
4. 🟠 Wire OCR → gap detector
5. 🟡 Validate with tests

Start with the timing instrumentation to find where those 36 seconds are going. That's blocking everything else.
