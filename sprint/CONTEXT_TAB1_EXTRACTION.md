# TAB 1: CONTEXT EXTRACTION + MANUAL LIBRARY
# Copy everything below into Claude Code CLI

You are Tab 1 in a 2-tab sprint to build Intelligent Context Capture & Manual Retrieval.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task

## YOUR IDENTITY
- Workstream: Context + Manuals
- Branch: context-extraction
- Focus: Extract equipment context from messages, build manual library, index PDFs

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b context-extraction
git push -u origin context-extraction
```

---

## PHASE 1: Equipment Taxonomy (Day 1)

### Task 1.1: Create Intake Module
```bash
mkdir -p agent_factory/intake
touch agent_factory/intake/__init__.py
```

### Task 1.2: Data Models
Create `agent_factory/intake/models.py`:
```python
"""Data models for intelligent context capture."""
from dataclasses import dataclass, field
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
    PERFORMANCE = "performance"
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
    
    # Original message
    raw_message: str
    
    # Component identification
    component_name: str = ""
    component_family: str = ""
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    category: str = ""
    
    # Issue details
    issue_type: IssueType = IssueType.UNKNOWN
    fault_code: Optional[str] = None
    symptoms: List[str] = field(default_factory=list)
    
    # Work context
    work_context: WorkContext = WorkContext.TROUBLESHOOTING
    location: Optional[str] = None
    urgency: str = "medium"
    
    # Search optimization
    search_keywords: List[str] = field(default_factory=list)
    manual_search_queries: List[str] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.0
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None


@dataclass
class ManualReference:
    """Reference to a found manual/document."""
    
    title: str
    manufacturer: str
    document_type: str  # "user_manual", "troubleshooting", "quick_start"
    relevant_section: Optional[str] = None
    page_numbers: Optional[str] = None
    relevance_score: float = 0.0
    snippet: str = ""
    source_path: Optional[str] = None
    manual_id: Optional[str] = None
```

### Task 1.3: Equipment Taxonomy
Create `agent_factory/intake/equipment_taxonomy.py`:
```python
"""Equipment taxonomy for intelligent context extraction."""

# Component families with aliases and manufacturer patterns
COMPONENT_FAMILIES = {
    "vfd": {
        "canonical": "Variable Frequency Drive",
        "aliases": ["VFD", "drive", "inverter", "AC drive", "frequency drive", "variable speed drive"],
        "category": "Motor Controls",
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["powerflex", "1336", "160", "22"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["sinamics", "micromaster", "g120", "g110"],
                "brand": "Siemens"
            },
            "abb": {
                "patterns": ["acs", "ach"],
                "brand": "ABB"
            },
            "yaskawa": {
                "patterns": ["v1000", "a1000", "j1000", "ga700"],
                "brand": "Yaskawa"
            },
            "danfoss": {
                "patterns": ["vlt", "fc"],
                "brand": "Danfoss"
            },
            "schneider": {
                "patterns": ["altivar", "atv"],
                "brand": "Schneider Electric"
            }
        }
    },
    "plc": {
        "canonical": "Programmable Logic Controller",
        "aliases": ["PLC", "controller", "processor", "CPU"],
        "category": "PLCs & Controllers",
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["controllogix", "compactlogix", "micrologix", "slc", "plc-5", "1756", "1769", "1766"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["s7-1500", "s7-1200", "s7-300", "s7-400", "logo"],
                "brand": "Siemens"
            },
            "mitsubishi": {
                "patterns": ["melsec", "fx", "q series", "iq-r"],
                "brand": "Mitsubishi"
            },
            "omron": {
                "patterns": ["cj", "nj", "nx", "cp1"],
                "brand": "Omron"
            }
        }
    },
    "hmi": {
        "canonical": "Human Machine Interface",
        "aliases": ["HMI", "touchscreen", "operator panel", "operator interface", "OIT"],
        "category": "PLCs & Controllers",
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["panelview", "2711"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["simatic", "comfort panel", "tp", "ktp"],
                "brand": "Siemens"
            }
        }
    },
    "motor": {
        "canonical": "Electric Motor",
        "aliases": ["motor", "induction motor", "servo", "servo motor"],
        "category": "Motors",
        "manufacturers": {}
    },
    "contactor": {
        "canonical": "Motor Contactor",
        "aliases": ["contactor", "starter", "motor starter"],
        "category": "Motor Controls",
        "manufacturers": {}
    },
    "sensor": {
        "canonical": "Sensor",
        "aliases": ["sensor", "proximity", "prox", "photoelectric", "photo eye", "limit switch"],
        "category": "Sensors & Instrumentation",
        "manufacturers": {
            "banner": {"patterns": ["q", "qs", "world-beam"], "brand": "Banner Engineering"},
            "keyence": {"patterns": ["lr", "lv", "il"], "brand": "Keyence"},
            "ifm": {"patterns": ["efector", "o5"], "brand": "IFM"},
            "omron": {"patterns": ["e2e", "e3"], "brand": "Omron"}
        }
    },
    "safety_relay": {
        "canonical": "Safety Relay",
        "aliases": ["safety relay", "guard relay", "e-stop relay"],
        "category": "Safety",
        "manufacturers": {
            "pilz": {"patterns": ["pnoz"], "brand": "Pilz"},
            "allen-bradley": {"patterns": ["guardmaster", "msr"], "brand": "Allen-Bradley"},
            "banner": {"patterns": ["sc"], "brand": "Banner"}
        }
    },
    "valve": {
        "canonical": "Solenoid Valve",
        "aliases": ["valve", "solenoid", "solenoid valve", "directional valve"],
        "category": "Pneumatics",
        "manufacturers": {
            "festo": {"patterns": ["vuvs", "mfh", "jmfh"], "brand": "Festo"},
            "smc": {"patterns": ["sy", "vq", "vf"], "brand": "SMC"}
        }
    }
}

# Issue type keywords
ISSUE_KEYWORDS = {
    IssueType.FAULT_CODE: ["fault", "error", "alarm", "code", "f0", "e0", "err"],
    IssueType.WONT_START: ["won't start", "wont start", "no start", "doesn't start", "dead"],
    IssueType.INTERMITTENT: ["intermittent", "sometimes", "random", "sporadic", "comes and goes"],
    IssueType.NOISE_VIBRATION: ["noise", "vibration", "grinding", "humming", "buzzing", "rattling"],
    IssueType.OVERHEATING: ["hot", "overheating", "temperature", "thermal", "burning"],
    IssueType.COMMUNICATION: ["communication", "network", "ethernet", "no connection", "offline", "lost comm"],
    IssueType.CALIBRATION: ["calibration", "drift", "accuracy", "offset", "scaling"],
    IssueType.PHYSICAL_DAMAGE: ["broken", "cracked", "damaged", "burnt", "melted"],
    IssueType.PERFORMANCE: ["slow", "weak", "reduced", "poor", "degraded"]
}

# Urgency keywords
URGENCY_KEYWORDS = {
    "critical": ["down", "stopped", "urgent", "emergency", "production stopped", "critical"],
    "high": ["asap", "high priority", "soon", "important"],
    "low": ["when you can", "no rush", "minor", "cosmetic"]
}

from enum import Enum
from .models import IssueType

def identify_component_family(text: str) -> tuple:
    """
    Identify component family from text.
    Returns: (family_key, canonical_name, category)
    """
    text_lower = text.lower()
    
    for family_key, family_data in COMPONENT_FAMILIES.items():
        # Check aliases
        for alias in family_data["aliases"]:
            if alias.lower() in text_lower:
                return (family_key, family_data["canonical"], family_data["category"])
    
    return (None, None, None)

def identify_manufacturer(text: str, family_key: str = None) -> tuple:
    """
    Identify manufacturer from text.
    Returns: (manufacturer_key, brand_name)
    """
    text_lower = text.lower()
    
    families_to_check = [COMPONENT_FAMILIES[family_key]] if family_key else COMPONENT_FAMILIES.values()
    
    for family_data in families_to_check:
        for mfr_key, mfr_data in family_data.get("manufacturers", {}).items():
            for pattern in mfr_data["patterns"]:
                if pattern.lower() in text_lower:
                    return (mfr_key, mfr_data["brand"])
    
    # Check direct brand mentions
    brand_patterns = {
        "allen-bradley": ["allen-bradley", "allen bradley", "rockwell", "ab"],
        "siemens": ["siemens"],
        "abb": ["abb"],
        "schneider": ["schneider", "square d"],
        "mitsubishi": ["mitsubishi"],
        "omron": ["omron"],
        "yaskawa": ["yaskawa"],
        "festo": ["festo"],
        "smc": ["smc"]
    }
    
    for mfr_key, patterns in brand_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                return (mfr_key, patterns[0].title())
    
    return (None, None)

def identify_issue_type(text: str) -> IssueType:
    """Identify the type of issue from text."""
    text_lower = text.lower()
    
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return issue_type
    
    return IssueType.UNKNOWN

def identify_urgency(text: str) -> str:
    """Identify urgency level from text."""
    text_lower = text.lower()
    
    for urgency, keywords in URGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return urgency
    
    return "medium"

def extract_fault_code(text: str) -> str:
    """Extract fault code from text."""
    import re
    
    # Common fault code patterns
    patterns = [
        r'\b[fF]\d{1,4}\b',           # F001, F1, f004
        r'\b[eE]rr?\d{1,4}\b',        # E01, Err5, err001
        r'\b[aA]larm\s*\d{1,4}\b',    # Alarm 5, alarm001
        r'\bfault\s*code\s*(\d+)\b',  # fault code 5
        r'\b\d{1,2}[-\.]\d{1,2}\b',   # 1-5, 2.3 (some formats)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).upper()
    
    return None
```

---

## PHASE 2: Context Extractor (Day 1-2)

### Task 2.1: Context Extractor
Create `agent_factory/intake/context_extractor.py`:
```python
"""Extract rich equipment context from user messages."""
import anthropic
import json
import logging
from typing import Optional, List
import re

from .models import EquipmentContext, IssueType, WorkContext
from .equipment_taxonomy import (
    identify_component_family,
    identify_manufacturer,
    identify_issue_type,
    identify_urgency,
    extract_fault_code
)

logger = logging.getLogger(__name__)

class ContextExtractor:
    """Extract equipment context from technician messages."""
    
    EXTRACTION_PROMPT = '''Analyze this maintenance technician's message and extract equipment context.

Message: "{message}"

Extract the following information in JSON format:
{{
    "component_name": "specific model or component name mentioned",
    "component_family": "general type (VFD, PLC, sensor, motor, etc.)",
    "manufacturer": "brand name if identifiable",
    "model_number": "specific model number if mentioned",
    "category": "Motor Controls, PLCs, Sensors, Safety, Pneumatics, etc.",
    "issue_type": "fault_code|wont_start|intermittent|noise_vibration|overheating|communication|calibration|physical_damage|performance|unknown",
    "fault_code": "the specific fault/error code if mentioned",
    "symptoms": ["list", "of", "symptoms"],
    "work_context": "troubleshooting|installation|maintenance|replacement|programming|commissioning|inspection",
    "location": "where the equipment is located if mentioned",
    "urgency": "critical|high|medium|low",
    "confidence": 0.0-1.0,
    "needs_clarification": true/false,
    "clarification_prompt": "question to ask if needs clarification"
}}

Rules:
1. Be specific about component names (e.g., "PowerFlex 525" not just "VFD")
2. Identify manufacturer from model names (PowerFlex = Allen-Bradley)
3. Extract exact fault codes in original format
4. List all symptoms mentioned
5. Set needs_clarification=true if critical info is missing
6. Generate a helpful clarification question if needed

Return ONLY valid JSON, no other text.'''

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def extract(self, message: str, user_history: List[dict] = None) -> EquipmentContext:
        """
        Extract equipment context from message.
        
        Uses Claude for rich extraction, enhanced by taxonomy patterns.
        """
        # Start with rule-based extraction
        context = self._rule_based_extract(message)
        
        # Enhance with Claude
        try:
            claude_context = await self._claude_extract(message)
            context = self._merge_contexts(context, claude_context)
        except Exception as e:
            logger.warning(f"Claude extraction failed: {e}, using rule-based only")
        
        # Generate search queries
        context.search_keywords = self._generate_search_keywords(context)
        context.manual_search_queries = self._generate_manual_queries(context)
        
        return context
    
    def _rule_based_extract(self, message: str) -> EquipmentContext:
        """Fast rule-based extraction using taxonomy."""
        family_key, family_name, category = identify_component_family(message)
        mfr_key, mfr_name = identify_manufacturer(message, family_key)
        issue_type = identify_issue_type(message)
        urgency = identify_urgency(message)
        fault_code = extract_fault_code(message)
        
        return EquipmentContext(
            raw_message=message,
            component_family=family_name or "",
            category=category or "",
            manufacturer=mfr_name,
            issue_type=issue_type,
            urgency=urgency,
            fault_code=fault_code,
            confidence=0.5 if family_name else 0.2
        )
    
    async def _claude_extract(self, message: str) -> dict:
        """Use Claude for rich context extraction."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": self.EXTRACTION_PROMPT.format(message=message)
            }]
        )
        
        # Parse JSON response
        text = response.content[0].text.strip()
        
        # Handle markdown code blocks
        if text.startswith("```"):
            text = re.sub(r'^```json?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        return json.loads(text)
    
    def _merge_contexts(self, rule_ctx: EquipmentContext, claude_data: dict) -> EquipmentContext:
        """Merge rule-based and Claude extractions."""
        # Prefer Claude's extractions, fall back to rule-based
        rule_ctx.component_name = claude_data.get("component_name") or rule_ctx.component_name
        rule_ctx.component_family = claude_data.get("component_family") or rule_ctx.component_family
        rule_ctx.manufacturer = claude_data.get("manufacturer") or rule_ctx.manufacturer
        rule_ctx.model_number = claude_data.get("model_number")
        rule_ctx.category = claude_data.get("category") or rule_ctx.category
        
        # Issue details
        issue_str = claude_data.get("issue_type", "unknown")
        try:
            rule_ctx.issue_type = IssueType(issue_str)
        except ValueError:
            pass
        
        rule_ctx.fault_code = claude_data.get("fault_code") or rule_ctx.fault_code
        rule_ctx.symptoms = claude_data.get("symptoms", [])
        
        # Work context
        work_str = claude_data.get("work_context", "troubleshooting")
        try:
            rule_ctx.work_context = WorkContext(work_str)
        except ValueError:
            pass
        
        rule_ctx.location = claude_data.get("location")
        rule_ctx.urgency = claude_data.get("urgency") or rule_ctx.urgency
        
        # Confidence
        rule_ctx.confidence = claude_data.get("confidence", 0.7)
        rule_ctx.needs_clarification = claude_data.get("needs_clarification", False)
        rule_ctx.clarification_prompt = claude_data.get("clarification_prompt")
        
        return rule_ctx
    
    def _generate_search_keywords(self, ctx: EquipmentContext) -> List[str]:
        """Generate keywords for knowledge base search."""
        keywords = []
        
        if ctx.component_name:
            keywords.append(ctx.component_name)
        if ctx.component_family:
            keywords.append(ctx.component_family)
        if ctx.manufacturer:
            keywords.append(ctx.manufacturer)
        if ctx.model_number:
            keywords.append(ctx.model_number)
        if ctx.fault_code:
            keywords.append(f"fault {ctx.fault_code}")
        
        keywords.extend(ctx.symptoms[:3])
        
        return list(set(keywords))
    
    def _generate_manual_queries(self, ctx: EquipmentContext) -> List[str]:
        """Generate specific queries for manual search."""
        queries = []
        
        # Specific fault code query
        if ctx.fault_code and ctx.component_name:
            queries.append(f"{ctx.component_name} {ctx.fault_code}")
        
        # Model + issue type
        if ctx.component_name and ctx.issue_type != IssueType.UNKNOWN:
            queries.append(f"{ctx.component_name} {ctx.issue_type.value.replace('_', ' ')}")
        
        # Manufacturer + family + troubleshooting
        if ctx.manufacturer and ctx.component_family:
            queries.append(f"{ctx.manufacturer} {ctx.component_family} troubleshooting")
        
        # Generic component family query
        if ctx.component_family:
            queries.append(f"{ctx.component_family} manual")
        
        return queries
```

---

## PHASE 3: Manual Library (Day 2-3)

### Task 3.1: Database Migration
Create `migrations/003_create_manuals_tables.sql`:
```sql
-- Equipment manuals library
CREATE TABLE IF NOT EXISTS equipment_manuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    manufacturer VARCHAR(255),
    component_family VARCHAR(255),
    model_patterns TEXT[],
    document_type VARCHAR(100) DEFAULT 'user_manual',
    file_path VARCHAR(512),
    file_url VARCHAR(512),
    page_count INTEGER,
    indexed BOOLEAN DEFAULT FALSE,
    collection_name VARCHAR(255),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP
);

-- Manual sections for targeted retrieval
CREATE TABLE IF NOT EXISTS manual_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manual_id UUID REFERENCES equipment_manuals(id) ON DELETE CASCADE,
    section_title VARCHAR(500),
    section_type VARCHAR(100),
    page_start INTEGER,
    page_end INTEGER,
    keywords TEXT[],
    content_preview TEXT
);

-- Track context extractions
CREATE TABLE IF NOT EXISTS context_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    telegram_id BIGINT,
    message_text TEXT,
    extracted_context JSONB,
    confidence FLOAT,
    manuals_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track missing manuals (gaps)
CREATE TABLE IF NOT EXISTS manual_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manufacturer VARCHAR(255),
    component_family VARCHAR(255),
    model_pattern VARCHAR(255),
    request_count INTEGER DEFAULT 1,
    first_requested TIMESTAMP DEFAULT NOW(),
    last_requested TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_manual_id UUID REFERENCES equipment_manuals(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_manuals_manufacturer ON equipment_manuals(manufacturer);
CREATE INDEX IF NOT EXISTS idx_manuals_family ON equipment_manuals(component_family);
CREATE INDEX IF NOT EXISTS idx_manual_sections_manual ON manual_sections(manual_id);
CREATE INDEX IF NOT EXISTS idx_context_user ON context_extractions(user_id);
CREATE INDEX IF NOT EXISTS idx_gaps_manufacturer ON manual_gaps(manufacturer);
```

### Task 3.2: Manual Indexer
Create `agent_factory/knowledge/manual_indexer.py`:
```python
"""Index PDF manuals for search."""
import pdfplumber
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict
import logging
import os
import re

logger = logging.getLogger(__name__)

class ManualIndexer:
    """Index PDF manuals into ChromaDB for semantic search."""
    
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        # Collection for all manuals
        self.collection = self.client.get_or_create_collection(
            name="equipment_manuals",
            metadata={"description": "OEM equipment manuals and documentation"}
        )
    
    def index_manual(
        self,
        pdf_path: Path,
        manual_id: str,
        title: str,
        manufacturer: str,
        component_family: str
    ) -> Dict:
        """
        Index a PDF manual.
        
        Returns: {"success": bool, "chunk_count": int, "sections": [...]}
        """
        logger.info(f"Indexing manual: {title}")
        
        try:
            # Extract text from PDF
            pages = self._extract_pdf(pdf_path)
            
            # Identify sections (TOC-aware)
            sections = self._identify_sections(pages)
            
            # Chunk content
            chunks = self._chunk_pages(pages, manual_id, title, manufacturer, component_family)
            
            # Embed and store
            if chunks:
                texts = [c["text"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                ids = [c["id"] for c in chunks]
                
                embeddings = self.embedder.encode(texts).tolist()
                
                self.collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.info(f"Indexed {len(chunks)} chunks from {title}")
            
            return {
                "success": True,
                "chunk_count": len(chunks),
                "page_count": len(pages),
                "sections": sections
            }
            
        except Exception as e:
            logger.error(f"Failed to index {title}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract text from PDF pages."""
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                tables = page.extract_tables()
                
                # Convert tables to text
                table_text = ""
                for table in tables:
                    for row in table:
                        table_text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                
                pages.append({
                    "page_num": i + 1,
                    "text": text,
                    "table_text": table_text
                })
        
        return pages
    
    def _identify_sections(self, pages: List[Dict]) -> List[Dict]:
        """Identify document sections from page content."""
        sections = []
        
        # Common section patterns in manuals
        section_patterns = [
            (r"(?i)chapter\s+\d+[:\.]?\s*(.+)", "chapter"),
            (r"(?i)section\s+\d+[:\.]?\s*(.+)", "section"),
            (r"(?i)(\d+\.?\s+)?fault\s+codes?", "fault_codes"),
            (r"(?i)(\d+\.?\s+)?troubleshoot", "troubleshooting"),
            (r"(?i)(\d+\.?\s+)?specifications?", "specifications"),
            (r"(?i)(\d+\.?\s+)?wiring", "wiring"),
            (r"(?i)(\d+\.?\s+)?installation", "installation"),
            (r"(?i)(\d+\.?\s+)?maintenance", "maintenance"),
            (r"(?i)(\d+\.?\s+)?parameter", "parameters"),
        ]
        
        current_section = None
        
        for page in pages:
            for pattern, section_type in section_patterns:
                match = re.search(pattern, page["text"][:500])  # Check first 500 chars
                if match:
                    if current_section:
                        current_section["page_end"] = page["page_num"] - 1
                        sections.append(current_section)
                    
                    current_section = {
                        "title": match.group(0).strip(),
                        "type": section_type,
                        "page_start": page["page_num"],
                        "page_end": None
                    }
                    break
        
        if current_section:
            current_section["page_end"] = pages[-1]["page_num"]
            sections.append(current_section)
        
        return sections
    
    def _chunk_pages(
        self,
        pages: List[Dict],
        manual_id: str,
        title: str,
        manufacturer: str,
        component_family: str
    ) -> List[Dict]:
        """Chunk pages for vector storage."""
        chunks = []
        chunk_size = 500
        overlap = 100
        
        for page in pages:
            full_text = page["text"] + "\n" + page["table_text"]
            
            # Split into chunks
            words = full_text.split()
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                if len(chunk_words) < 50:  # Skip tiny chunks
                    continue
                
                chunk_text = " ".join(chunk_words)
                chunk_id = f"{manual_id}_p{page['page_num']}_{i}"
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "manual_id": manual_id,
                        "title": title,
                        "manufacturer": manufacturer,
                        "component_family": component_family,
                        "page_num": page["page_num"],
                        "chunk_index": len(chunks)
                    }
                })
        
        return chunks
```

### Task 3.3: Manual Search
Create `agent_factory/knowledge/manual_search.py`:
```python
"""Search indexed manuals."""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import os
import logging

from agent_factory.intake.models import EquipmentContext, ManualReference

logger = logging.getLogger(__name__)

class ManualSearch:
    """Search equipment manuals for relevant content."""
    
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        try:
            self.collection = self.client.get_collection("equipment_manuals")
        except Exception:
            self.collection = None
            logger.warning("equipment_manuals collection not found")
    
    async def search(
        self,
        context: EquipmentContext,
        top_k: int = 5
    ) -> List[ManualReference]:
        """
        Search for relevant manual content based on equipment context.
        """
        if not self.collection:
            return []
        
        results = []
        seen_manuals = set()
        
        # Search with each generated query
        for query in context.manual_search_queries[:3]:
            query_results = await self._search_query(query, top_k=3)
            
            for r in query_results:
                manual_id = r.get("manual_id")
                if manual_id not in seen_manuals:
                    seen_manuals.add(manual_id)
                    results.append(r)
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:top_k]
    
    async def search_fault_code(
        self,
        manufacturer: str,
        model: str,
        fault_code: str
    ) -> Optional[ManualReference]:
        """Search specifically for fault code information."""
        if not self.collection:
            return None
        
        query = f"{manufacturer} {model} fault {fault_code} troubleshooting"
        results = await self._search_query(query, top_k=3)
        
        # Filter for fault code mentions
        for r in results:
            if fault_code.lower() in r.snippet.lower():
                return r
        
        return results[0] if results else None
    
    async def _search_query(self, query: str, top_k: int = 5) -> List[ManualReference]:
        """Execute a single search query."""
        query_embedding = self.embedder.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        references = []
        
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            score = 1 / (1 + distance)
            
            references.append(ManualReference(
                title=metadata.get("title", "Unknown"),
                manufacturer=metadata.get("manufacturer", ""),
                document_type="user_manual",
                relevant_section=None,
                page_numbers=str(metadata.get("page_num", "")),
                relevance_score=score,
                snippet=doc[:300] + "..." if len(doc) > 300 else doc,
                manual_id=metadata.get("manual_id")
            ))
        
        return references
```

---

## PHASE 4: Database Methods (Day 3)

### Task 4.1: Add to database.py
Add these methods to `agent_factory/rivet_pro/database.py`:
```python
# Manual library methods
async def create_manual(self, title: str, manufacturer: str, component_family: str,
                       file_path: str, document_type: str = "user_manual") -> dict:
    query = """
        INSERT INTO equipment_manuals (title, manufacturer, component_family, file_path, document_type)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow(query, title, manufacturer, component_family, file_path, document_type)
        return dict(row)

async def update_manual_indexed(self, manual_id: str, collection_name: str, page_count: int) -> bool:
    query = """
        UPDATE equipment_manuals 
        SET indexed = TRUE, collection_name = $2, page_count = $3, indexed_at = NOW()
        WHERE id = $1
    """
    async with self.pool.acquire() as conn:
        await conn.execute(query, manual_id, collection_name, page_count)
        return True

async def search_manuals_by_family(self, component_family: str) -> List[dict]:
    query = """
        SELECT * FROM equipment_manuals 
        WHERE component_family ILIKE $1 AND indexed = TRUE
    """
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(query, f"%{component_family}%")
        return [dict(r) for r in rows]

async def log_context_extraction(self, user_id: str, telegram_id: int, message: str,
                                 context: dict, confidence: float, manuals_found: int) -> dict:
    query = """
        INSERT INTO context_extractions (user_id, telegram_id, message_text, extracted_context, confidence, manuals_found)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """
    import json
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow(query, user_id, telegram_id, message, json.dumps(context), confidence, manuals_found)
        return dict(row)

async def log_manual_gap(self, manufacturer: str, component_family: str, model_pattern: str) -> dict:
    query = """
        INSERT INTO manual_gaps (manufacturer, component_family, model_pattern)
        VALUES ($1, $2, $3)
        ON CONFLICT (manufacturer, component_family) 
        DO UPDATE SET request_count = manual_gaps.request_count + 1, last_requested = NOW()
        RETURNING *
    """
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow(query, manufacturer, component_family, model_pattern)
        return dict(row)

async def get_top_manual_gaps(self, limit: int = 10) -> List[dict]:
    query = """
        SELECT * FROM manual_gaps 
        WHERE resolved = FALSE
        ORDER BY request_count DESC
        LIMIT $1
    """
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(query, limit)
        return [dict(r) for r in rows]
```

---

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "context-extraction: [component] description"
git push origin context-extraction
```

## SUCCESS CRITERIA
- [ ] Equipment taxonomy covers major manufacturers
- [ ] Context extractor identifies component, manufacturer, issue type
- [ ] Fault codes are extracted correctly
- [ ] Manual indexer processes PDFs
- [ ] Manual search returns relevant results
- [ ] Database stores context extractions

## START NOW
Begin with Task 1.1 - Create intake module structure.
